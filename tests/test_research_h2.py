import numpy as np
import pandas as pd
import pytest

from quantlab.calendars import NSE, US
from quantlab.research import h2_volume as h2
from quantlab.research.panel import past_baseline

from research_helpers import bars_table

K = 3


def spike_table(market, spike_day=11, slot=20, spike=250.0, n_days=12, **kw):
    n = market.bars_per_day
    vols = np.full((n_days, n), 100.0)
    vols[spike_day, slot] = spike
    return bars_table(market, n_days=n_days, volumes=vols, **kw)


# ---------------- past-only baseline ----------------
def test_baseline_is_median_of_previous_days_only():
    M = np.arange(1, 6 * 4 + 1, dtype=float).reshape(6, 4)
    b = past_baseline(M, L=3, min_count=1, neighbors=0)
    assert np.isnan(b[:3]).all()
    assert b[3, 0] == np.median(M[0:3, 0])        # rows 0..2 only
    assert b[4, 2] == np.median(M[1:4, 2])


def test_changing_current_or_future_volume_never_changes_baseline_or_earlier_events():
    t = spike_table(US)
    f0 = h2.event_features(t)
    t2 = t.copy()
    mask = t2["date"] == sorted(set(t2["date"]))[11]        # rewrite the LAST day completely
    t2.loc[mask, "volume"] = 9999.0
    f1 = h2.event_features(t2)
    before = f0["date"] != sorted(set(t["date"]))[11]
    assert (f0.loc[before, "baseline"].fillna(-1) == f1.loc[before, "baseline"].fillna(-1)).all()
    assert (f0.loc[before, "event"] == f1.loc[before, "event"]).all()
    # and on the last day the baseline itself does not depend on that day's volume
    last = ~before
    assert (f0.loc[last, "baseline"].fillna(-1) == f1.loc[last, "baseline"].fillna(-1)).all()


# ---------------- event threshold ----------------
@pytest.mark.parametrize("vol,expected", [(199.0, 0.0), (200.0, 1.0), (250.0, 1.0)])
def test_threshold_is_at_least_2x(vol, expected):
    f = h2.event_features(spike_table(US, spike=vol))
    row = f[(f["slot_idx"] == 20) & (f["date"] == sorted(set(f["date"]))[11])].iloc[0]
    assert row["ratio"] == pytest.approx(vol / 100.0) and row["event"] == expected


def test_events_need_a_baseline_burn_in():
    f = h2.event_features(spike_table(US, spike_day=5, spike=500.0))
    assert f["event"].sum() == 0                              # day 5 < L=10: no baseline, no event


def test_nse_0915_volume_can_never_be_an_event():
    t = spike_table(NSE, slot=0, spike=900.0)
    f = h2.event_features(t)
    assert f["event"].sum() == 0


# ---------------- forward windows ----------------
def _row(f, day_i, slot, dates):
    return f[(f["date"] == dates[day_i]) & (f["slot_idx"] == slot)].iloc[0]


def test_window_needs_all_k_following_bars():
    t = spike_table(US, nan_rows=[(11, 22)])                  # bar t+2 empty
    f = h2.event_features(t)
    dates = sorted(set(t["date"]))
    assert _row(f, 11, 20, dates)["window_valid"] == 0.0
    assert _row(f, 11, 30, dates)["window_valid"] == 1.0


def test_window_cannot_run_past_the_end_of_the_day():
    f = h2.event_features(spike_table(US, slot=77))           # last bar of the day
    assert f["eligible"].sum() == 0
    f2 = h2.event_features(spike_table(US, slot=74))          # t+3 would be slot 77 -> still valid
    assert f2["eligible"].sum() == 1
    f3 = h2.event_features(spike_table(US, slot=75))          # t+3 would fall off the day
    assert f3["eligible"].sum() == 0


def test_nse_window_cannot_enter_the_closing_window():
    # slot 69 = 14:55 start? NSE slot j starts 09:15 + 5j; slot 71 = 15:10, slot 72 = 15:15.
    f_ok = h2.event_features(spike_table(NSE, slot=68))       # t+3 = slot 71 (15:10): allowed
    f_bad = h2.event_features(spike_table(NSE, slot=69))      # t+3 = slot 72 (15:15): closing window
    assert f_ok["eligible"].sum() == 1 and f_bad["eligible"].sum() == 0


# ---------------- outcome formulas with known numbers ----------------
def priced_table(market):
    """Event at slot 20 of the last day, hand-picked prices around it."""
    n_days, n = 12, market.bars_per_day
    closes = np.tile(100.0 + 0.0 * np.arange(n), (n_days, 1))
    opens = closes.copy()
    d, s = 11, 20
    closes[d, s] = 99.0
    opens[d, s + 1], closes[d, s + 1] = 100.0, 101.0           # O_{t+1}=100 (gap from 99), C_{t+1}=101
    opens[d, s + 2], closes[d, s + 2] = 101.0, 102.0
    opens[d, s + 3], closes[d, s + 3] = 102.0, 103.02
    opens[d, s] = 99.5
    opens[d, s + 4], closes[d, s + 4] = 103.02, 104.0
    return spike_table(market, closes=closes, opens=opens), d, s


def test_primary_outcomes_use_next_open_entry_and_open_to_close_first_candle():
    t, d, s = priced_table(US)
    f = h2.outcome_features(t, k=K)
    dates = sorted(set(t["date"]))
    r = _row(f, d, s, dates)
    r22, r23 = np.log(102 / 101), np.log(103.02 / 102)
    assert r["f_open"] == pytest.approx(np.log(103.02 / 100.0))              # enter at O_{t+1}
    assert r["f_close"] == pytest.approx(np.log(103.02 / 99.0))              # optimistic: enter at C_t
    assert r["gap"] == pytest.approx(np.log(100.0 / 99.0))
    fv_open = np.sqrt((np.log(101 / 100) ** 2 + r22 ** 2 + r23 ** 2) / 3)    # first candle open-to-close
    assert r["fv_open"] == pytest.approx(fv_open)
    r21_cc = np.log(101 / 99)                                                # close-to-close of the first candle
    fv_close = np.sqrt((r21_cc ** 2 + r22 ** 2 + r23 ** 2) / 3)
    assert r["fv_close"] == pytest.approx(fv_close)
    assert fv_open < fv_close                                                # the gap is excluded from exposure
    assert r["event"] == 1.0 and r["eligible"] == 1.0


def test_continuation_sign_follows_the_event_candle_direction():
    t, d, s = priced_table(US)            # r_t = ln(99/100) < 0 (event candle fell)
    f = h2.outcome_features(t, k=K)
    dates = sorted(set(t["date"]))
    r = _row(f, d, s, dates)
    assert r["f_open"] > 0 and r["g_open"] == pytest.approx(-r["f_open"])    # price rose => reversal => g < 0


def test_delay_shifts_entry_one_candle():
    t, d, s = priced_table(US)
    f = h2.outcome_features(t, k=K, delay=1)
    r = _row(f, d, s, sorted(set(t["date"])))
    assert r["f_open"] == pytest.approx(np.log(104.0 / 101.0))           # enter O_{t+2}, exit C_{t+4}
    assert r["fv_open"] == pytest.approx(np.sqrt((np.log(102 / 101) ** 2
                                                  + np.log(103.02 / 102) ** 2
                                                  + np.log(104 / 103.02) ** 2) / 3))


# ---------------- outcome-blind feasibility ----------------
def test_feasibility_is_identical_when_all_prices_are_scrambled():
    rng = np.random.default_rng(0)
    t = spike_table(US)
    a = h2.feasibility(t)
    t2 = t.copy()
    for c in ["open", "high", "low", "close", "ret", "ret_oc", "ret_closing"]:
        t2[c] = rng.normal(size=len(t2))
    assert h2.feasibility(t2) == a


def test_feasibility_never_touches_price_columns():
    t = spike_table(US)
    t = t.copy()
    for c in h2.PRICE_COLUMNS:
        if c in t.columns:
            t[c] = np.nan                    # if feasibility read prices this would break eligibility
    assert h2.feasibility(t)["n_events"] == 1


@pytest.mark.parametrize("n_ev,n_days,label", [(29, 20, "UNDERPOWERED"), (30, 15, "ADEQUATE"),
                                               (30, 14, "UNDERPOWERED"), (500, 40, "ADEQUATE")])
def test_adequacy_threshold(n_ev, n_days, label):
    assert h2.adequacy(n_ev, n_days) == label


# ---------------- regression and null device ----------------
def test_shuffle_volume_days_keeps_prices_and_each_slots_volume_multiset():
    from quantlab.research.nulls import simulate_table
    rng = np.random.default_rng(0)
    t = simulate_table(US, "S", 15, rng)
    s = h2.shuffle_volume_days(t, rng)
    assert (s["close"] == t["close"]).all()
    for slot in ["09:30", "12:00"]:
        a = np.sort(t.loc[t["slot"] == slot, "volume"].to_numpy())
        b = np.sort(s.loc[s["slot"] == slot, "volume"].to_numpy())
        assert (a == b).all()
    assert not (s["volume"].to_numpy() == t["volume"].to_numpy()).all()


def test_event_regression_detects_a_true_forward_volatility_effect():
    from quantlab.research.nulls import simulate_table
    rng = np.random.default_rng(5)
    tabs = [simulate_table(US, f"S{i}", 59, rng, fwd_vol_mult=2.5) for i in range(3)]
    feat = pd.concat([h2.outcome_features(t) for t in tabs])
    res = h2.event_regression(feat, "y_fv_open", 199, rng)
    assert res["beta"] > 0.2 and res["p_wild"] < 0.05 and res["adequacy"] == "ADEQUATE"
