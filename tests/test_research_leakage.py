"""Look-ahead leakage tests for the H2 event definition and every control.

Decision time = the END of the event candle t (when its volume and close are final).
So any feature at (day D, slot s0) may depend on: all earlier days, and candles up to and
including s0 of day D. It must NOT change if prices or volumes after s0 (or on later days) change."""
import numpy as np
import pandas as pd
import pytest

from quantlab.calendars import US
from quantlab.research import h2_volume as h2
from quantlab.research.nulls import simulate_table

FEATURES = ["volume", "baseline", "ratio", "event", "c1", "c2", "c3", "c3_12", "c3_24", "c4"]
D_IDX, S0 = 15, 40


@pytest.fixture(scope="module")
def table():
    return simulate_table(US, "S", 22, np.random.default_rng(7), df=4, day_vol_sd=0.3,
                          volume_day_loading=0.8, intraday_regime_sd=0.2)


def _rows(f, dates, d_idx, upto_slot=None):
    day = dates[d_idx]
    if upto_slot is None:
        return f["date"] < day
    return (f["date"] == day) & (f["slot_idx"] <= upto_slot)


def _scramble_after(table, d_idx, s0, rng):
    dates = sorted(set(table["date"]))
    after = (table["date"] > dates[d_idx]) | ((table["date"] == dates[d_idx]) & (table["mins_since_open"] > 5 * s0))
    t = table.copy()
    n = int(after.sum())
    t.loc[after, "ret"] = rng.normal(0, 0.02, n)
    for c in ["open", "close"]:
        t.loc[after, c] = 100 * np.exp(rng.normal(0, 0.05, n))
    t.loc[after, "volume"] = rng.uniform(1, 50000, n)
    return t, dates


def test_features_at_decision_time_do_not_depend_on_anything_later(table):
    rng = np.random.default_rng(0)
    base = h2.outcome_features(table)
    t2, dates = _scramble_after(table, D_IDX, S0, rng)
    alt = h2.outcome_features(t2)
    for rows in (_rows(base, dates, D_IDX), _rows(base, dates, D_IDX, S0)):
        for col in FEATURES:
            np.testing.assert_array_equal(base.loc[rows, col].to_numpy(), alt.loc[rows, col].to_numpy(),
                                          err_msg=f"{col} changed when only FUTURE data was altered")


def test_forward_outcomes_DO_change_when_future_changes(table):
    """Sanity check that the test above is able to detect a change at all."""
    rng = np.random.default_rng(1)
    base = h2.outcome_features(table)
    t2, dates = _scramble_after(table, D_IDX, S0, rng)
    alt = h2.outcome_features(t2)
    rows = _rows(base, dates, D_IDX, S0)
    sel = rows & (base["slot_idx"] == S0 - 1)
    assert not np.array_equal(base.loc[sel, "f_open"].to_numpy(), alt.loc[sel, "f_open"].to_numpy())


def test_c3_includes_the_event_candle_but_not_the_next_one(table):
    base = h2.outcome_features(table)
    dates = sorted(set(table["date"]))
    t2 = table.copy()
    hit = (t2["date"] == dates[D_IDX]) & (t2["mins_since_open"] == 5 * S0)
    t2.loc[hit, "ret"] = 0.05                                    # change the event candle's own return
    alt = h2.outcome_features(t2)
    at = lambda f, s: f[(f["date"] == dates[D_IDX]) & (f["slot_idx"] == s)].iloc[0]
    assert at(alt, S0)["c3"] != at(base, S0)["c3"]               # candle t is known at decision time
    assert at(alt, S0 - 1)["c3"] == at(base, S0 - 1)["c3"] or (
        np.isnan(at(alt, S0 - 1)["c3"]) and np.isnan(at(base, S0 - 1)["c3"]))   # earlier decision unaffected


def test_c4_uses_only_earlier_days(table):
    base = h2.outcome_features(table)
    dates = sorted(set(table["date"]))
    today, prev = dates[D_IDX], dates[D_IDX - 1]

    def c4_at(t):
        f = h2.outcome_features(t)
        return f[f["date"] == today]["c4"].iloc[0]

    mod_today = table.copy()
    mod_today.loc[mod_today["date"] == today, "ret"] = 0.03       # change TODAY: c4 must not move
    assert c4_at(mod_today) == c4_at(table)
    mod_prev = table.copy()
    mod_prev.loc[mod_prev["date"] == prev, "ret"] = 0.03          # change YESTERDAY: c4 must move
    assert c4_at(mod_prev) != c4_at(table)


def test_baseline_never_uses_the_current_or_later_days(table):
    f = h2.outcome_features(table)
    dates = sorted(set(table["date"]))
    t2 = table.copy()
    t2.loc[t2["date"] >= dates[D_IDX], "volume"] = 123456.0
    alt = h2.outcome_features(t2)
    rows = f["date"] == dates[D_IDX]
    np.testing.assert_array_equal(f.loc[rows, "baseline"].to_numpy(), alt.loc[rows, "baseline"].to_numpy())


def test_simulator_options_behave():
    rng = np.random.default_rng(0)
    custom = np.full(US.bars_per_day, 0.001); custom[0] = 0.005
    t = simulate_table(US, "S", 40, rng, slot_vol=custom, df=30, day_vol_sd=0.0)
    sd_open = t.loc[t["slot"] == "09:30", "ret_oc"].std()          # first candle: 0.7 of its 0.005 move
    sd_later = t.loc[t["slot"] == "10:00", "ret"].std()
    assert sd_open > 2.5 * sd_later                               # explicit profile is honoured
    t = simulate_table(US, "S", 30, rng, intraday_regime_sd=0.4, intraday_regime_phi=0.97, day_vol_sd=0.0, df=30)
    r = t["ret"].abs().groupby(t["date"]).apply(lambda s: s.dropna().autocorr(1))
    assert r.mean() > 0.1                                         # |returns| cluster inside the day
