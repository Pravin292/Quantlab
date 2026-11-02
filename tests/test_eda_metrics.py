"""EDA metrics checked against hand-computed answers."""
import numpy as np
import pandas as pd
import pytest
from scipy import stats

from quantlab.eda import metrics as m


def tbl(rows):
    """rows: list of dicts -> bar-table-like frame with sensible defaults."""
    base = {"symbol": "X", "status": "ok", "period": "middle", "slot": "10:00",
            "ret": np.nan, "ret_oc": np.nan, "ret_closing": np.nan, "volume": 100.0,
            "volume_ok": True, "volume_status": "ok", "mins_since_open": 45}
    return pd.DataFrame([{**base, **r} for r in rows])


def test_distribution_stats_known_values():
    x = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, np.nan])      # NaN ignored
    d = m.distribution_stats(x)
    assert d["n"] == 5 and d["mean"] == 3.0
    assert d["std"] == pytest.approx(np.sqrt(2.5))
    assert d["skew"] == pytest.approx(0.0)
    assert d["excess_kurtosis"] == pytest.approx(-1.2)     # known for 1..5, unbiased
    assert d["min"] == 1.0 and d["max"] == 5.0


def test_too_few_observations_give_nan_not_a_number():
    d = m.distribution_stats(pd.Series([0.1, 0.2]))
    assert d["n"] == 2 and np.isnan(d["std"])


def test_main_returns_uses_only_ok_status():
    t = tbl([{"ret": 0.01}, {"ret": 0.5, "status": "excluded_forming_bar"},
             {"ret": 0.5, "status": "nse_closing_window"}])
    assert len(m.main_returns(t)) == 1


def test_mean_by_slot_and_t_interval():
    t = tbl([{"ret": r} for r in [0.01, -0.01, 0.01, -0.01, 0.0]])  # mean 0, n=5
    r = m.mean_by_slot(t).iloc[0]
    sd = np.std([0.01, -0.01, 0.01, -0.01, 0.0], ddof=1)
    assert r["n"] == 5 and r["mean"] == pytest.approx(0.0)
    assert r["se"] == pytest.approx(sd / np.sqrt(5))
    assert r["ci_high"] == pytest.approx(stats.t.ppf(0.975, 4) * sd / np.sqrt(5))
    assert not r["ci_excludes_zero"]


def test_ci_excludes_zero_when_clearly_positive():
    t = tbl([{"ret": r} for r in [0.010, 0.011, 0.009, 0.010, 0.012]])
    assert m.mean_by_slot(t).iloc[0]["ci_excludes_zero"]


def test_slots_with_too_few_days_are_nan():
    t = tbl([{"ret": 0.01}, {"ret": 0.02}])
    r = m.mean_by_slot(t).iloc[0]
    assert r["n"] == 2 and np.isnan(r["ci_low"]) and not r["ci_excludes_zero"]


def test_volatility_by_slot_is_sample_std():
    t = tbl([{"ret": r, "slot": s} for s in ["10:00", "10:05"]
             for r in [0.01, -0.01, 0.01, -0.01, 0.02]])
    v = m.volatility_by_slot(t).set_index("slot")
    exp = np.std([0.01, -0.01, 0.01, -0.01, 0.02], ddof=1)
    assert v.loc["10:00", "std"] == pytest.approx(exp)
    assert v.loc["10:00", "std_bps"] == pytest.approx(exp * 1e4)
    assert v.loc["10:05", "n"] == 5


def test_volatility_by_period_pools_and_ignores_closing_window():
    rets = [0.01, -0.01, 0.01, -0.01, 0.01]
    t = tbl([{"ret": r, "period": "open"} for r in rets]
            + [{"ret": 0.02 * r / 0.01, "period": "close"} for r in rets]
            + [{"ret": 0.5, "period": "closing_window_unreliable"}] * 5)
    v = m.volatility_by_period(t).set_index("period")
    assert list(v.index) == ["open", "close"]
    assert v.loc["close", "std"] == pytest.approx(2 * v.loc["open", "std"])


def test_standardisation_and_tail_counts():
    rng = np.random.default_rng(0)
    base = rng.normal(0, 0.01, 200)
    base[0] = 0.5                                         # one huge outlier
    t = tbl([{"ret": r} for r in base])
    z = m.add_standardised(t)["z"]
    assert z.abs().max() == z.iloc[0].__abs__()          # outlier stays, largest |z|
    assert len(z.dropna()) == 200                         # nothing removed
    ts = m.tail_stats(z)
    assert ts["n_beyond"] >= 1
    assert ts["expected_share_if_normal"] == pytest.approx(0.0026998, abs=1e-6)


def test_standardisation_is_per_symbol_and_slot():
    a = [{"ret": r, "symbol": "A"} for r in [0.01, -0.01, 0.01, -0.01, 0.01]]
    b = [{"ret": r, "symbol": "B"} for r in [0.10, -0.10, 0.10, -0.10, 0.10]]
    z = m.add_standardised(tbl(a + b))
    za = z[z.symbol == "A"]["z"].abs().round(6).to_numpy()
    zb = z[z.symbol == "B"]["z"].abs().round(6).to_numpy()
    assert (za == zb).all()          # same shape of data -> same z despite 10x scale


def test_largest_moves_reports_without_removing():
    t = tbl([{"ret": r} for r in [0.01, -0.01, 0.01, -0.01, 0.2]])
    t.index = pd.date_range("2026-10-12 10:00", periods=5, freq="D", tz="Asia/Kolkata")
    out = m.largest_moves(m.add_standardised(t), n=2)
    assert len(out) == 2 and out.iloc[0]["ret"] == 0.2


def test_volume_profile_median_and_relative():
    rows = [{"volume": v, "slot": "10:00"} for v in [10, 20, 30, 40, 50]]
    rows += [{"volume": v, "slot": "10:05"} for v in [100, 200, 300, 400, 500]]
    rows += [{"volume": 9999, "slot": "10:05", "volume_ok": False,
              "volume_status": "excluded_zero_missing_or_flagged_volume"}] * 3
    p = m.volume_profile(tbl(rows)).set_index("slot")
    assert p.loc["10:00", "median_volume"] == 30 and p.loc["10:05", "median_volume"] == 300
    assert p.loc["10:05", "n"] == 5                       # excluded bars not counted
    assert p.loc["10:00", "relative_volume"] == pytest.approx(30 / 165)  # ref = median(30,300)


def test_opening_candle_stats_use_only_ret_oc():
    t = tbl([{"ret_oc": r, "ret": 0.9} for r in [0.01, 0.02, 0.03, 0.04, 0.05]])
    o = m.opening_candle_stats(t).iloc[0]
    assert o["mean"] == pytest.approx(0.03) and o["n"] == 5


def test_closing_window_stats_counts_empty_bars():
    w = "closing_window_unreliable"
    rows = [{"period": w, "slot": "15:20", "status": "excluded_missing_ohlc"}] * 3
    rows += [{"period": w, "slot": "15:20", "status": "nse_closing_window", "ret_closing": 0.001}] * 2
    r = m.closing_window_stats(tbl(rows)).iloc[0]
    assert (r["n_bars"], r["n_empty_or_excluded"], r["n_with_return"]) == (5, 3, 2)


def test_quality_categories():
    t = tbl([{}, {"status": "excluded_missing_ohlc"},
             {"volume_status": "excluded_zero_missing_or_flagged_volume"},
             {"status": "excluded_forming_bar"}])
    assert list(m.quality_category(t)) == ["ok", "empty_bar", "zero_or_missing_volume",
                                           "other_excluded"]


def test_quality_categories_for_nse_specific_exclusions():
    t = tbl([{"status": "nse_closing_window"},
             {"volume_status": "excluded_nse_0915_volume"},
             {"status": "excluded_missing_ohlc", "volume_status": "excluded_unusable_bar"}])
    assert list(m.quality_category(t)) == ["nse_closing_window_usable_but_excluded",
                                           "nse_0915_volume_excluded", "empty_bar"]


def test_mins_since_open_is_looked_up_per_symbol_not_per_clock_label():
    # "10:00" is 45 minutes after the NSE open but 30 after the US open.
    table = tbl([{"symbol": "N", "slot": "10:00", "mins_since_open": 45},
                 {"symbol": "U", "slot": "10:00", "mins_since_open": 30}])
    result = pd.DataFrame({"symbol": ["U", "N"], "slot": ["10:00", "10:00"], "x": [1, 2]})
    out = m.attach_mins_since_open(result, table).set_index("symbol")
    assert out.loc["U", "mins_since_open"] == 30 and out.loc["N", "mins_since_open"] == 45
