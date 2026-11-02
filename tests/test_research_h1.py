import numpy as np
import pandas as pd
import pytest

from quantlab.calendars import NSE, US
from quantlab.research import h1_volatility as h1

from research_helpers import bars_table


def table_with_period_vol(market, a, b, c, n_days=6):
    """Every return in the open/middle/close period has magnitude a/b/c (alternating
    sign), so the per-bar volatility is exactly a, b, c."""
    n = market.bars_per_day
    from quantlab.eda.masks import assign_period
    from quantlab.calendars import expected_slots
    periods = assign_period(expected_slots(market, "2026-08-03"), market).to_numpy()
    mag = np.where(periods == "open", a, np.where(periods == "middle", b,
                   np.where(periods == "close", c, c)))
    sign = np.where(np.arange(n) % 2 == 0, 1.0, -1.0)
    r = mag * sign
    closes = 100 * np.exp(np.cumsum(r))
    return bars_table(market, n_days=n_days, closes=np.tile(closes, (n_days, 1)))


@pytest.mark.parametrize("market", [NSE, US], ids=["NSE", "US"])
def test_period_volatility_is_exact_and_logged(market):
    t = table_with_period_vol(market, 0.004, 0.002, 0.003)
    p = h1.period_panel(t, market.name)
    assert p["open"].round(8).eq(round(np.log(0.004), 8)).all()
    assert p["middle"].round(8).eq(round(np.log(0.002), 8)).all()
    assert p["close"].round(8).eq(round(np.log(0.003), 8)).all()


def test_nse_open_period_uses_8_returns_and_excludes_the_opening_candle():
    t = table_with_period_vol(NSE, 0.004, 0.002, 0.003, n_days=1)
    used = t[(t["status"] == "ok") & (t["period"] == "open")]
    assert len(used) == h1.EXPECTED_RETURNS["NSE"]["open"] == 8
    assert "09:15" not in used["slot"].tolist()


def test_us_expected_return_counts():
    t = table_with_period_vol(US, 0.004, 0.002, 0.003, n_days=1)
    counts = t[t["status"] == "ok"].groupby("period").size().to_dict()
    assert counts == h1.EXPECTED_RETURNS["US"]


def test_nse_closing_window_never_enters_the_close_period():
    t = table_with_period_vol(NSE, 0.004, 0.002, 0.003, n_days=1)
    used = t[(t["status"] == "ok") & (t["period"] == "close")]
    assert used["slot"].max() == "15:10"


def test_low_coverage_day_period_is_nan_not_estimated():
    # empty 6 of the 54 middle bars on day 0 (coverage 48/54 = 89% < 90%)
    t = table_with_period_vol(US, 0.004, 0.002, 0.003, n_days=3)
    t0 = bars_table(US, n_days=3, closes=np.tile(100 * np.exp(np.cumsum(np.where(np.arange(78) % 2 == 0, 0.002, -0.002))), (3, 1)),
                    nan_rows=[(0, s) for s in range(20, 26)])
    p = h1.period_panel(t0, "US")
    assert np.isnan(p["middle"].iloc[0]) and not np.isnan(p["middle"].iloc[1])


def test_market_panel_is_mean_of_logs_and_propagates_nan():
    a = pd.DataFrame({"open": [1.0, np.nan], "middle": [0.0, 0.0], "close": [0.0, 0.0]}, index=[1, 2])
    b = pd.DataFrame({"open": [3.0, 5.0], "middle": [0.0, 0.0], "close": [0.0, 0.0]}, index=[1, 2])
    m = h1.market_panel([a, b])
    assert m.loc[1, "open"] == 2.0 and np.isnan(m.loc[2, "open"])


def _panel(open_shift, n=40, seed=0):
    rng = np.random.default_rng(seed)
    base = rng.normal(0, 0.3, n)                   # day-level volatility, shared by all periods
    return pd.DataFrame({"open": base + open_shift + rng.normal(0, 0.1, n),
                         "middle": base + rng.normal(0, 0.1, n),
                         "close": base + rng.normal(0, 0.1, n)}, index=range(n))


def test_friedman_detects_a_period_difference_and_kendalls_w():
    res = h1.omnibus(_panel(0.7))
    assert res["p"] < 1e-6 and res["n_days"] == 40
    assert res["kendalls_w"] == pytest.approx(res["chi2"] / (40 * 2))
    assert h1.omnibus(_panel(0.0))["p"] > 0.01


def test_pairwise_recovers_known_ratio():
    rng = np.random.default_rng(0)
    out = h1.pairwise(_panel(np.log(2.0)), rng, B=500)
    row = out[out.contrast == "open-middle"].iloc[0]
    assert row["ratio"] == pytest.approx(2.0, rel=0.1)
    assert row["ci_low_ratio"] < 2.0 < row["ci_high_ratio"] * 1.15
    assert row["wilcoxon_p"] < 1e-6
    assert out[out.contrast == "close-middle"].iloc[0]["wilcoxon_p"] > 0.001


def test_difference_autocorrelation_runs():
    out = h1.difference_autocorrelation(_panel(0.5))
    assert set(out["contrast"]) == {"open-middle", "close-middle", "open-close"}


def test_equal_size_subsampling_removes_the_small_sample_bias_between_periods():
    """Regression test for a flaw found in the M4a calibration: with fat-tailed returns and
    EQUAL true volatility, ln(vol) from 8 open bars is biased lower than from 54 middle bars."""
    from quantlab.research.nulls import simulate_table
    rng = np.random.default_rng(3)
    tabs = [simulate_table(NSE, f"S{i}", 59, rng, df=4, day_vol_sd=0.0) for i in range(6)]
    full = pd.concat([h1.period_panel(t, "NSE", subsample=False) for t in tabs])
    sub = pd.concat([h1.period_panel(t, "NSE", subsample=True) for t in tabs])
    bias_full = (full["open"] - full["middle"]).mean()
    bias_sub = (sub["open"] - sub["middle"]).mean()
    assert bias_full < -0.04                      # the artefact exists with all bars
    assert abs(bias_sub) < 0.03 and abs(bias_sub) < abs(bias_full)


def test_subsampled_panel_is_reproducible():
    t = table_with_period_vol(US, 0.004, 0.002, 0.003)
    a = h1.period_panel(t, "US")
    b = h1.period_panel(t, "US")
    assert a.equals(b)
