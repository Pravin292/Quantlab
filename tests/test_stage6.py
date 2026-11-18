"""Tests for the Stage 6 helpers (docs/42). Constructed or tiny seeded inputs only: no real data, no long simulations.
Implementation checks, not statistical validation."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))
from quantlab.research import h1_calibration as hc, h1_stage3 as s3, stage6 as s6   # noqa: E402
import run_h1_next as nx                                                          # noqa: E402


def test_cell_grids_have_the_registered_size():
    a, b = s6.size_cells(), s6.power_cells()
    assert len(a) == 96 and len(b) == 120
    assert list(a["row"]) == list(range(96)) and list(b["row"]) == list(range(120))
    assert a.groupby("gated").size().to_dict() == {False: 32, True: 64}            # S4 and S5 are never gated
    assert set(a.loc[~a["gated"], "level"]) == {"S4_one_and_half_x", "S5_illustrative"}
    assert set(b["n_days"]) == {59, 90, 125, 180, 250}


def test_dependence_levels_match_the_earlier_registered_values():
    for mk in ("NSE", "US"):
        assert s6.dependence_for("S1_validated", mk) == nx.EMP_DEP[mk]
    assert {"ret_corr": 0.5, "share": 0.7, "phi": 0.7} == s6.dependence_for("S5_illustrative", "US") == {k: nx.ILLUSTRATIVE_DEP[k] for k in ("ret_corr", "share", "phi")}
    assert s6.dependence_for("S0_none", "NSE") == {"ret_corr": 0.0, "share": 0.0, "phi": 0.0}


def test_stress_levels_increase_in_strength():
    for k in ("phi", "share", "ret_corr"):
        v = [s6.dependence_for(lv, "US")[k] for lv in ("S2_fresh_point", "S3_fresh_upper")]
        assert v[0] < v[1]


def test_seeds_are_new_and_distinct_from_every_earlier_master():
    earlier = set(s3.all_registered_masters().values()) | {20261206, 20261207, 20261208, 20261215}
    assert not (set(s6.MASTER.values()) & earlier)
    assert len(set(s6.MASTER.values())) == 3
    assert s6.size_seed(3, 7, "data").entropy == 20261401 and s6.size_seed(3, 7, "data").spawn_key == (3, 7, 0)
    assert s6.size_seed(3, 7, "baseline").spawn_key == (3, 7, 1) and s6.power_seed(4, 9).spawn_key == (4, 9)
    a = np.random.default_rng(s6.size_seed(0, 0, "data")).random(3)
    assert np.array_equal(a, np.random.default_rng(s6.size_seed(0, 0, "data")).random(3))
    assert not np.array_equal(a, np.random.default_rng(s6.size_seed(0, 1, "data")).random(3))


def test_size_status_uses_the_frozen_limits():
    assert s6.size_status(1375, 25000, "T6")["status"].startswith("PASS")            # exactly 5.5%: tier A limit
    assert s6.size_status(1376, 25000, "T6")["status"].startswith("FAIL")
    assert s6.size_status(1500, 25000, "T4")["status"].startswith("PASS")            # exactly 6.0%: tier B limit
    assert s6.size_status(1501, 25000, "T4")["status"].startswith("FAIL")
    assert s6.size_status(100, 25000, "T4")["status"] == "PASS"                      # far below: clear pass


def test_part_a_outcome_ignores_reported_cells():
    df = pd.DataFrame({"gated": [True, True, False], "status": ["PASS", "PASS", "REPORTED_FAIL"]})
    assert s6.part_a_outcome(df) == "STRESS_PASS"
    for st, want in (("PASS_AMBIGUOUS", "STRESS_MARGINAL"), ("FAIL_AMBIGUOUS", "STRESS_BOUNDARY"), ("FAIL", "STRESS_FAIL")):
        assert s6.part_a_outcome(pd.DataFrame({"gated": [True, True], "status": ["PASS", st]})) == want


def test_min_detectable_effect_rules():
    m = [1.05, 1.1, 1.2, 1.3, 1.5, 2.0]
    assert s6.min_detectable(m, [0.9, 0.95, 1, 1, 1, 1]) == {"value": 1.05, "kind": "at_or_below_first"}
    assert s6.min_detectable(m, [0.1, 0.2, 0.3, 0.4, 0.5, 0.6])["kind"] == "not_reached"
    r = s6.min_detectable(m, [0.1, 0.2, 0.5, 0.7, 0.9, 1.0])                          # crosses 0.80 between 1.3 (0.7) and 1.5 (0.9)
    assert r["kind"] == "interpolated" and 1.3 < r["value"] < 1.5
    assert r["value"] == pytest.approx(np.exp(np.log(1.3) + 0.5 * (np.log(1.5) - np.log(1.3))))
    assert s6.min_detectable(m[::-1], [1.0, 0.9, 0.7, 0.5, 0.2, 0.1]) == s6.min_detectable(m, [0.1, 0.2, 0.5, 0.7, 0.9, 1.0])   # grid order does not matter


def test_permute_slots_keeps_values_and_is_common_across_stocks():
    rng = np.random.default_rng(1)
    x = rng.random((3, 5, 12))
    p = s6.permute_slots(x, np.random.default_rng(2))
    assert p.shape == x.shape
    for d in range(5):
        for s in range(3):
            assert sorted(p[s, d]) == sorted(x[s, d])                                  # same values, new order
    assert not np.array_equal(p, x)
    assert np.array_equal(s6.permute_slots(x, np.random.default_rng(2)), p)           # same seed, same permutation


def test_permutation_is_the_same_for_all_stocks_of_a_session():
    x = np.tile(np.arange(10.0), (3, 4, 1)) * np.array([1.0, 10.0, 100.0])[:, None, None]
    p = s6.permute_slots(x, np.random.default_rng(5))
    assert np.allclose(p[1], p[0] * 10) and np.allclose(p[2], p[0] * 100)


def test_placebo_statistics_and_summary_on_equal_variance_data():
    rng = np.random.default_rng(7)
    r2 = rng.standard_normal((3, 40, 75)) ** 2                                         # equal variance in every slot
    groups = [np.arange(0, 9), np.arange(9, 63), np.arange(63, 72)]
    T = s6.placebo_statistics(r2, groups, np.random.default_rng(8), n_rep=60)
    assert T.shape == (60,) and np.isfinite(T).all()
    assert T[0] == float(hc.max_abs_t(hc.market_matrix_from_r2(s6.permute_slots(r2, np.random.default_rng(8)), groups)))
    s = s6.placebo_summary(T, crit=2.0)
    assert s["n_rep"] == 60 and s["n_reject"] == int((T > 2.0).sum()) and s["wilson_low"] <= s["rate"] <= s["wilson_high"]


def test_placebo_refuses_incomplete_sessions():
    r2 = np.ones((3, 5, 10))
    r2[0, 0, 0] = np.nan
    with pytest.raises(ValueError):
        s6.placebo_statistics(r2, [np.arange(3), np.arange(3, 7), np.arange(7, 10)], np.random.default_rng(1), n_rep=2)


def test_runners_do_not_import_real_market_data_in_parts_a_and_b():
    for name in ("stage6_run_size.py", "stage6_run_power.py"):
        text = (ROOT / "scripts" / "milestone4" / name).read_text()
        assert "load_tables" not in text and "data/clean" not in text
