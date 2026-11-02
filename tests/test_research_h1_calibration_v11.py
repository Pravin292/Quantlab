"""Unit tests for the spec v1.1 additions (src/quantlab/research/h1_calibration_v11.py). Synthetic data only.

These tests check that the CODE does what its docstrings say. They are NOT evidence that the corrected C2 (or any procedure) is
statistically valid; the formula itself is UNVERIFIED and validity is judged only by the pre-specified simulation stages.
"""
import hashlib
import math
from pathlib import Path

import numpy as np
import pytest

from quantlab.research import h1_calibration as hc, h1_calibration_v11 as v11

ROOT = Path(__file__).resolve().parents[1]


# ------------------------------------------------------------------------------------------------ A1
def test_fdb_p_value_hand_computed():
    Tstar = np.array([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0])
    T2 = np.arange(1.0, 11.0)                                   # quantile(T2, 1 - p1) is easy to compute by hand
    p1, p = v11.fdb_p_value(3.2, Tstar, T2)                     # T* >= 3.2 for 3.5, 4.0, 4.5, 5.0 -> p1 = 0.4
    assert p1 == pytest.approx(0.4)
    q = np.quantile(T2, 0.6)                                    # = 6.4
    assert q == pytest.approx(6.4)
    assert p == pytest.approx(np.mean(Tstar > 6.4))             # = 0.0, since no first-level T* exceeds 6.4


def test_fdb_p_value_uses_first_level_statistics_not_second_level():
    # when the second level is shifted up, the corrected p must change; the v1 formula (T2 vs quantile of T2) would not
    Tstar = np.linspace(0.1, 5.0, 100)
    T2_low, T2_high = np.linspace(0.1, 5.0, 100), np.linspace(0.1, 8.0, 100)
    _, p_low = v11.fdb_p_value(2.0, Tstar, T2_low)
    _, p_high = v11.fdb_p_value(2.0, Tstar, T2_high)
    assert p_high < p_low


def test_fdb_p_value_edges_p1_zero_and_one():
    Tstar, T2 = np.array([1.0, 2.0, 3.0]), np.array([0.5, 1.5, 2.5])
    p1, p = v11.fdb_p_value(10.0, Tstar, T2)                    # nothing >= T: p1 = 0, quantile(T2, 1) = max(T2)
    assert p1 == 0.0 and p == 0.0 + np.mean(Tstar > 2.5)
    p1, p = v11.fdb_p_value(-1.0, Tstar, T2)                    # everything >= T: p1 = 1, quantile(T2, 0) = min(T2)
    assert p1 == 1.0 and p == np.mean(Tstar > 0.5)


def test_fdb_like_test_matches_v1_random_draws_but_not_its_p_value():
    rng = np.random.default_rng(31)
    diffs = []
    for i in range(30):
        M = rng.gamma(2.0, 1.0, (59, 3))
        old = hc.fast_double_bootstrap(M, np.random.default_rng(i), B=199)
        new = v11.fdb_like_test(M, np.random.default_rng(i), B=199)
        assert new["T"] == old["T"] and new["p_first"] == old["p_first"]          # same draws, same first level
        assert old["p_fdb"] == pytest.approx(old["p_first"], abs=0.01)             # documents the v1 defect
        diffs.append(abs(new["p_fdb"] - new["p_first"]))
    assert np.mean(diffs) > 0.005                                                   # the corrected p-value is a different quantity


def test_fdb_like_test_is_deterministic_labelled_unverified_and_detects_a_huge_effect():
    rng = np.random.default_rng(32)
    M = rng.gamma(2.0, 1.0, (59, 3))
    out = v11.fdb_like_test(M, np.random.default_rng(5), B=199)
    assert out == v11.fdb_like_test(M, np.random.default_rng(5), B=199)
    assert "UNVERIFIED" in out["label"] and 0 <= out["p_fdb"] <= 1
    M2 = M.copy()
    M2[:, 0] *= 6.0
    assert v11.fdb_like_test(M2, np.random.default_rng(6), B=199)["reject"]


# ------------------------------------------------------------------------------------------------ A2 / A3
def test_wilson_interval_known_value_and_contains_estimate():
    L, U = v11.wilson_interval(np.array([1250, 100, 0]), 25_000)
    assert 0.0472 < L[0] < 0.0475 and 0.0525 < U[0] < 0.0528                        # p-hat 0.05, half-width about 0.27 points
    assert (L <= np.array([1250, 100, 0]) / 25_000).all() and (U >= np.array([1250, 100, 0]) / 25_000).all()


def test_gate_point_rule_boundaries_tier_a_and_b():
    n = 25_000
    assert v11.gate_pass(int(0.045 * n), n, "A") and v11.gate_pass(int(0.055 * n), n, "A")
    assert not v11.gate_pass(int(0.0446 * n), n, "A") and not v11.gate_pass(int(0.0555 * n), n, "A")
    assert v11.gate_pass(int(0.040 * n), n, "B") and v11.gate_pass(int(0.060 * n), n, "B")
    assert not v11.gate_pass(int(0.0605 * n), n, "B")


@pytest.mark.parametrize("n", [25_000, 50_000, 100_000])
@pytest.mark.parametrize("tier", ["A", "B", "ALT"])
def test_wilson_clause_and_ceiling_are_redundant_for_large_n(n, tier):
    # A3: exhaustive over every possible k; switching the extra clauses off never changes a decision
    k = np.arange(0, n + 1)
    full = v11.gate_pass(k, n, tier)
    point_only = v11.gate_pass(k, n, tier, use_wilson=False, use_ceiling=False)
    assert np.array_equal(full, point_only)


def test_wilson_clause_is_NOT_redundant_for_small_n():
    # documents WHY the clause is kept: with few valid simulations it does bind
    n = 1_000
    k = np.arange(0, n + 1)
    assert not np.array_equal(v11.gate_pass(k, n, "A"), v11.gate_pass(k, n, "A", use_wilson=False, use_ceiling=False))


def test_classify_cell_statuses():
    n = 25_000
    assert v11.classify_cell(1250, n, "A")["status"] == "PASS"                       # 5.0%: far from both bounds
    assert v11.classify_cell(int(0.055 * n) - 5, n, "A")["status"] == "PASS_AMBIGUOUS"
    assert v11.classify_cell(int(0.055 * n) + 20, n, "A")["status"] == "FAIL_AMBIGUOUS"
    assert v11.classify_cell(int(0.065 * n), n, "A")["status"] == "FAIL"
    low = v11.classify_cell(int(0.040 * n), n, "A")                                   # 4.0%: clearly below the 4.5% bound
    assert low["status"] == "FAIL" and not low["ambiguous"]


def test_classify_cell_c3_mode_uses_upper_bound_only():
    n = 25_000
    assert v11.classify_cell(int(0.030 * n), n, "A", c3_mode=True)["status"] == "PASS"   # very conservative C3 is fine
    assert v11.classify_cell(int(0.060 * n), n, "A", c3_mode=True)["status"] == "FAIL"


def _cells(*statuses):
    return [{"status": s} for s in statuses]


def test_classify_candidate_precedence():
    assert v11.classify_candidate(_cells("PASS", "PASS")) == "PASS_CLEAR"
    assert v11.classify_candidate(_cells("PASS", "PASS_AMBIGUOUS")) == "MARGINAL_NOT_DEMONSTRATED"
    assert v11.classify_candidate(_cells("PASS", "FAIL_AMBIGUOUS", "PASS_AMBIGUOUS")) == "FAIL_BOUNDARY_ONLY"
    assert v11.classify_candidate(_cells("PASS_AMBIGUOUS", "FAIL_AMBIGUOUS", "FAIL")) == "FAIL"


# ------------------------------------------------------------------------------------------------ A4
@pytest.mark.parametrize("name", ["a_intraday_volatility_clustering", "b_jumps", "e_heavy_tailed_day_factor", "f_laplace_shocks"])
def test_alternative_process_shock_part_has_unit_second_moment(name):
    assert v11.alt_dgp_second_moment_factor(name) == pytest.approx(1.0, abs=1e-9)


def test_jump_constants():
    assert v11.E_JUMP_SQ == pytest.approx(37.3333, abs=1e-3)
    assert v11.JUMP_VAR_SHARE == pytest.approx(0.07467, abs=1e-5)
    assert v11.SHOCK_SCALE_B == pytest.approx(0.9619, abs=1e-4)


def test_t_unit_scale_gives_unit_variance():
    from scipy import stats
    for df in (3, 4, 5, 6, 8, 10):
        assert stats.t(df).var() * v11.t_unit_scale(df) ** 2 == pytest.approx(1.0)


def test_process_e_mixture_has_target_sd_and_finite_second_moment():
    var = (1 - v11.E_MIX_WEIGHT) * v11.E_SMALL_SD ** 2 + v11.E_MIX_WEIGHT * v11.E_LARGE_SD ** 2
    assert math.sqrt(var) == pytest.approx(0.3)
    assert math.isfinite(v11.day_factor_second_moment_e()) and v11.day_factor_second_moment_e() > 1.0
    assert "DEVIATION_FROM_V1_WORDING" in v11.ALT_DGP_PARAMETERS["e_heavy_tailed_day_factor"]


def test_process_a_log_volatility_is_stationary_with_target_sd():
    rng = np.random.default_rng(41)
    n_paths, n_steps = 20_000, 60
    h = rng.normal(0, v11.SIGMA_A, n_paths)
    last = h
    for _ in range(n_steps):
        last = v11.PHI_A * last + math.sqrt(1 - v11.PHI_A ** 2) * v11.SIGMA_A * rng.standard_normal(n_paths)
    assert np.std(last) == pytest.approx(v11.SIGMA_A, rel=0.03)                       # the recursion keeps the stationary sd


# ------------------------------------------------------------------------------------------------ A5 / guards
def test_c3_intermediate_spec_is_consistent_and_seed_is_new():
    c = v11.C3_TRAINING_INTERMEDIATE
    assert c["sample_sizes_days"] == [90, 180] and c["sims_per_cell"] == 25_000
    assert c["seed"] not in (20261201, 20261202, 20261203, 20261204, 20261205, 20261206, 20261207, 20261208)


def test_frozen_v1_files_are_unchanged():
    manifest = ROOT / "outputs/milestone4/h1_calibration/frozen_spec/FROZEN_v1.sha256"
    lines = [ln.split("  ", 1) for ln in manifest.read_text().splitlines() if ln.strip()]
    assert len(lines) == 23
    for digest, rel in lines:
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest, rel
