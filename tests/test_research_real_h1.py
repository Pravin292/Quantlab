"""Tests for the real-data H1 runner logic (docs/30). Constructed deterministic arrays only: no real data, no random numbers.
Implementation checks only, not statistical validation."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from quantlab.research import h1_calibration as hc                      # noqa: E402
from quantlab.research import real_h1 as rh                             # noqa: E402

GROUPS = [np.arange(0, 3), np.arange(3, 8), np.arange(8, 10)]           # 10 used slots: open 3, middle 5, close 2


def build(days=62, open_level=2.0, mid_level=1.0, close_level=2.0, stocks=3):
    d = np.arange(days)[None, :, None]
    s = np.arange(stocks)[:, None, None]
    k = np.arange(10)[None, None, :]
    lvl = np.where(k < 3, open_level, np.where(k < 8, mid_level, close_level))
    return lvl * (1.0 + 0.3 * np.sin(1.0 + 0.7 * d + 0.9 * s + 0.31 * k) ** 2)


def test_crit_is_the_frozen_n59_value():
    t = pd.read_csv(ROOT / "outputs/milestone4/h1_calibration/stage2/c3_training/c3_critical_values.csv")
    assert abs(float(t.loc[t.n_days == 59, "c3_crit"].iloc[0]) - 3.298658000460969) < 1e-12


def test_first_59_complete_sessions_are_selected_in_order():
    r2 = build()
    r2[1, 4, 2] = np.nan          # session 4 incomplete for stock 1
    r2[0, 10, :] = np.nan         # session 10 incomplete for stock 0
    dates = [f"d{i:02d}" for i in range(r2.shape[1])]
    out = rh.analyse_market(r2, GROUPS, dates, crit=3.298658)
    assert out["status"] == "TESTED" and out["usable_market_sessions"] == 60
    assert out["selected_positions"] == [i for i in range(62) if i not in (4, 10)][:59]
    assert out["first_date"] == "d00" and out["last_date"] == "d60"


def test_fewer_than_n_usable_sessions_is_not_testable_and_computes_nothing():
    r2 = build(days=60)
    for i in (0, 5):
        r2[2, i, 0] = np.nan
    out = rh.analyse_market(r2, GROUPS, list(range(60)), crit=3.298658)
    assert out["usable_market_sessions"] == 58 and out["status"] == "NOT_TESTABLE"
    assert out["T"] is None and out["reject"] is None and out["theta"] is None


def test_statistic_equals_direct_computation_and_decision_rule():
    r2 = build()
    dates = list(range(62))
    sel = np.arange(59)
    M = hc.market_matrix_from_r2(r2[:, sel, :], GROUPS)
    T = float(hc.max_abs_t(M))
    out = rh.analyse_market(r2, GROUPS, dates, crit=T - 1e-9)
    assert abs(out["T"] - T) < 1e-12 and out["reject"] is True
    out2 = rh.analyse_market(r2, GROUPS, dates, crit=T + 1e-9)
    assert out2["reject"] is False
    assert abs(max(abs(a / b) for a, b in zip(out["theta"], out["se"])) - T) < 1e-12


def test_equal_levels_give_small_statistic_and_unequal_levels_a_large_one():
    eq = rh.analyse_market(build(open_level=1.0, mid_level=1.0, close_level=1.0), GROUPS, list(range(62)), crit=3.298658)
    ne = rh.analyse_market(build(open_level=3.0, mid_level=1.0, close_level=2.0), GROUPS, list(range(62)), crit=3.298658)
    assert eq["T"] < ne["T"] and ne["reject"] is True
