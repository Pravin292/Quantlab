"""Unit tests for the Stage 0 H1 calibration candidates (src/quantlab/research/h1_calibration.py). Synthetic data only."""
import numpy as np
import pytest

from quantlab.calendars import NSE
from quantlab.research import direct_sim as ds, h1_calibration as hc, dependence as dep
from quantlab.research.h1_rms2 import bootstrap_t

IDX = ds.used_slot_index(NSE)
PROFILE_E = dep.shaped_profile(NSE, 2.0, 2.0, 2.0, 2.0)
PROFILE_E_UNEQUAL = dep.shaped_profile(NSE, 2.0, 2.0, 2.0, 2.0, mult=1.4)       # open and close volatility x1.4


def world(seed, n_days=59, df=1000.0, profile=PROFILE_E, stocks=3):
    rng = np.random.default_rng(seed)
    r2 = ds.simulate_returns_sq(NSE, stocks, n_days, rng, profile=profile, df=df, day_vol_sd=0.3)
    return hc.to_used(r2, IDX)


def test_max_abs_t_matches_existing_bootstrap_t_statistic():
    r2, groups = world(1)
    M = hc.market_matrix_from_r2(r2, groups)
    ref = bootstrap_t(M, np.random.default_rng(0), "rom", B=19)
    assert hc.max_abs_t(M) == pytest.approx(np.abs(ref["t"]).max(), rel=1e-12)


def test_matrix_from_r2_equals_direct_period_matrix():
    rng = np.random.default_rng(2)
    full = ds.simulate_returns_sq(NSE, 3, 20, rng, profile=PROFILE_E, df=6.0)
    r2, groups = hc.to_used(full, IDX)
    assert np.allclose(hc.market_matrix_from_r2(r2, groups), ds.period_matrix(full, IDX))


def test_groups_partition_the_used_slots():
    r2, groups = world(3, n_days=5)
    allg = np.concatenate(groups)
    assert sorted(allg) == list(range(r2.shape[2])) and len(set(allg)) == len(allg)


def test_fit_recovers_the_slot_shape_with_many_gaussian_days():
    r2, groups = world(4, n_days=1500, df=1000.0)
    model = hc.fit_bar_model(r2, groups)
    true = np.concatenate([PROFILE_E[i] ** 2 for i in IDX])
    true_shape = np.empty_like(true)
    for gp in groups:
        true_shape[gp] = true[gp] / true[gp].mean()
    assert np.max(np.abs(model.shape / true_shape - 1)) < 0.06


def test_standardised_shocks_have_period_mean_one():
    r2, groups = world(5, df=4.0)
    model = hc.fit_bar_model(r2, groups)
    for gp in groups:
        assert np.mean(model.e2[:, :, gp]) == pytest.approx(1.0, abs=1e-9)


def test_null_world_has_equal_period_means_even_when_the_data_do_not():
    r2, groups = world(6, n_days=200, df=1000.0, profile=PROFILE_E_UNEQUAL)
    M = hc.market_matrix_from_r2(r2, groups)
    assert M[:, 0].mean() / M[:, 1].mean() > 1.5                               # the data violate the null
    Ms = hc.null_world_matrices(hc.fit_bar_model(r2, groups), 200, 300, np.random.default_rng(7))
    col = Ms.mean(axis=(0, 1))
    assert np.max(col) / np.min(col) == pytest.approx(1.0, abs=0.03)           # the artificial worlds do not


def test_null_world_shape_and_determinism():
    r2, groups = world(8, n_days=30, df=5.0)
    model = hc.fit_bar_model(r2, groups)
    a = hc.null_world_matrices(model, 30, 50, np.random.default_rng(9))
    b = hc.null_world_matrices(model, 30, 50, np.random.default_rng(9))
    assert a.shape == (50, 30, 3) and np.array_equal(a, b)
    assert np.all(a > 0)


def test_null_world_refuses_missing_shocks():
    r2, groups = world(10, n_days=10)
    model = hc.fit_bar_model(r2, groups)
    model.e2[0, 0, 0] = np.nan
    with pytest.raises(ValueError):
        hc.null_world_matrices(model, 10, 5, np.random.default_rng(0))


def test_fit_tolerates_missing_bars():
    r2, groups = world(11, n_days=40)
    r2 = r2.copy()
    r2[0, 3, 5] = np.nan
    r2[1, 7, :4] = np.nan
    model = hc.fit_bar_model(r2, groups)
    assert np.all(np.isfinite(model.v2)) and np.all(np.isfinite(model.g))


def test_c1_critical_value_matches_a_large_independent_null_in_a_gaussian_world():
    r2, groups = world(12, n_days=59, df=1000.0)
    got = hc.c1_test(r2, groups, np.random.default_rng(13), R=1500)["crit"]
    rng = np.random.default_rng(14)
    Ts = [hc.max_abs_t(hc.market_matrix_from_r2(*world(int(rng.integers(1e9)), df=1000.0))) for _ in range(1500)]
    assert got == pytest.approx(np.quantile(Ts, 0.95), rel=0.08)


def test_c1_is_deterministic_and_rejects_a_clear_violation():
    r2, groups = world(15, n_days=59, df=1000.0, profile=dep.shaped_profile(NSE, 2.0, 2.0, 2.0, 2.0, mult=1.8))
    a = hc.c1_test(r2, groups, np.random.default_rng(16), R=299)
    b = hc.c1_test(r2, groups, np.random.default_rng(16), R=299)
    assert a == b and a["reject"]


def test_c1_does_not_reject_a_null_world_most_of_the_time():
    rej = [hc.c1_test(*world(100 + i, df=1000.0), np.random.default_rng(i), R=199)["reject"] for i in range(60)]
    assert np.mean(rej) < 0.2                                                  # loose smoke bound (60 sims)


def test_fast_double_bootstrap_basic_properties():
    rng = np.random.default_rng(17)
    M = rng.gamma(2.0, 1.0, (59, 3))
    out = hc.fast_double_bootstrap(M, np.random.default_rng(18), B=399)
    assert 0 <= out["p_first"] <= 1 and 0 <= out["p_fdb"] <= 1
    assert out == hc.fast_double_bootstrap(M, np.random.default_rng(18), B=399)
    M2 = M.copy()
    M2[:, 0] *= 4.0
    assert hc.fast_double_bootstrap(M2, np.random.default_rng(19), B=399)["reject"]


def test_fast_double_bootstrap_edge_case_zero_first_level_p_rejects():
    rng = np.random.default_rng(23)
    M = np.column_stack([1.0 + 0.01 * rng.random(40), 9.0 + 0.01 * rng.random(40), 1.0 + 0.01 * rng.random(40)])
    out = hc.fast_double_bootstrap(M, np.random.default_rng(20), B=199)
    assert np.isfinite(out["T"]) and out["p_first"] == 0.0 and out["p_fdb"] == 0.0 and out["reject"]


def test_fast_double_bootstrap_is_roughly_calibrated_with_gaussian_data():
    rng = np.random.default_rng(21)
    rej = [hc.fast_double_bootstrap(rng.gamma(2.0, 1.0, (59, 3)), np.random.default_rng(i), B=199)["reject"] for i in range(200)]
    assert 0.01 < np.mean(rej) < 0.11                                          # loose smoke bound (200 sims)


def test_c3_rule_is_exactly_t_greater_than_crit():
    rng = np.random.default_rng(22)
    M = rng.gamma(2.0, 1.0, (59, 3))
    T = float(hc.max_abs_t(M))
    assert hc.c3_test(M, T - 1e-9)["reject"] and not hc.c3_test(M, T + 1e-9)["reject"]


def test_child_seeds_are_unique_and_full_width():
    kids = hc.child_seeds(123, 20000)
    states = {tuple(k.generate_state(4, np.uint64)) for k in kids}
    assert len(states) == 20000
    a = np.random.default_rng(kids[0]).random(3)
    assert np.array_equal(a, np.random.default_rng(hc.child_seeds(123, 20000)[0]).random(3))


def test_c1_p_value_is_consistent_with_the_decision():
    r2, groups = world(30, n_days=40, df=5.0)
    out = hc.c1_test(r2, groups, np.random.default_rng(31), R=99)
    assert out["p_mc"] * 100 == pytest.approx(round(out["p_mc"] * 100), abs=1e-9)          # multiple of 1/(R+1)
    assert out["reject"] == (out["p_mc"] <= 0.05)
