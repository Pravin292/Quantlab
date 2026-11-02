import numpy as np
import pytest

from quantlab.calendars import NSE, US
from quantlab.research import dependence as dep, direct_sim as ds, h1_rms, h1_robust as rb
from quantlab.research.nulls import simulate_table


def test_direct_matrix_matches_bar_level_simulator_in_mean_square_per_period():
    """Same profile, no regime/AR: the direct generator and the bar-level pipeline agree on period mean squares."""
    prof = dep.shaped_profile(NSE, 2.0, 2.0, 4.0, 0.4)
    rng = np.random.default_rng(1)
    tabs = [simulate_table(NSE, f"S{i}", 59, rng, df=4.0, day_vol_sd=0.0, slot_vol=prof, nse_feed_quirks=True) for i in range(3)]
    A = h1_rms.market_matrix([h1_rms.mean_square_panel(t, "NSE") for t in tabs]).mean(axis=0)
    rng = np.random.default_rng(2)
    B_ = np.mean([ds.simulate_market_matrix(NSE, 3, 59, rng, profile=prof, df=4.0, day_vol_sd=0.0).mean(axis=0) for _ in range(30)], axis=0)
    assert np.allclose(A / A[1], B_ / B_[1], rtol=0.25)          # heavy tails: loose tolerance
    assert np.allclose(B_ / B_[1], 1.0, rtol=0.12)               # periods have equal RMS by construction


def test_direct_period_means_equal_profile_squared_in_expectation_and_use_correct_slots():
    idx = ds.used_slot_index(NSE)
    assert [len(i) for i in idx] == [8, 54, 9] and all(i.min() >= 1 for i in idx)
    idx = ds.used_slot_index(US)
    assert [len(i) for i in idx] == [11, 54, 12]
    prof = np.full(NSE.bars_per_day, 0.002)
    rng = np.random.default_rng(3)
    M = np.mean([ds.simulate_market_matrix(NSE, 3, 59, rng, profile=prof, df=1000.0, day_vol_sd=0.0).mean(axis=0) for _ in range(40)], axis=0)
    assert np.allclose(M, 0.002 ** 2, rtol=0.03)


def test_direct_generator_cross_stock_correlation_and_extremes_replacement():
    rng = np.random.default_rng(4)
    prof = np.full(NSE.bars_per_day, 0.001)
    r2 = ds.simulate_returns_sq(NSE, 3, 200, rng, profile=prof, df=1000.0, day_vol_sd=0.0, ret_corr=0.4)
    r = np.sqrt(r2)
    assert r.shape == (3, 200, 75)
    idx = ds.used_slot_index(NSE)
    out = ds.replace_extremes(r2, idx, 3)
    used = np.concatenate(idx)
    assert out[:, :, used].max() < r2[:, :, used].max() and (out != r2).sum() == 3


@pytest.mark.parametrize("fn", [lambda M, r: rb.bootstrap_t_jackknife(M, r, 299),
                                lambda M, r: rb.wild_bootstrap_t(M, r, 299, "mammen"),
                                lambda M, r: rb.wild_bootstrap_t(M, r, 299, "rademacher")])
def test_robust_bootstrap_tests_detect_an_effect(fn):
    rng = np.random.default_rng(5)
    M = np.exp(rng.normal(0, 0.3, (59, 1))) * rng.chisquare(5, (59, 3)) / 5 * np.array([2.0, 1.0, 1.0])
    assert fn(M, rng)["reject_max"]


@pytest.mark.parametrize("fn", [lambda M, r: rb.bootstrap_t_jackknife(M, r, 199)["reject_max"],
                                lambda M, r: rb.wild_bootstrap_t(M, r, 199, "mammen")["reject_max"],
                                lambda M, r: rb.empirical_likelihood_diff(M)["reject_bonf"]])
def test_robust_tests_are_not_grossly_liberal_when_variances_are_equal(fn):
    rng = np.random.default_rng(6)
    rej = sum(fn(np.exp(rng.normal(0, 0.3, (59, 1))) * rng.chisquare(5, (59, 3)) / 5, rng) for _ in range(100))
    assert rej <= 16


def test_empirical_likelihood_statistic_properties():
    rng = np.random.default_rng(7)
    d = rng.normal(0, 1, 59)
    assert rb.el_statistic(d - d.mean()) < 1e-6                     # zero-mean sample -> statistic 0
    assert rb.el_statistic(np.abs(d) + 0.1) == float("inf")         # 0 outside convex hull
    big = [rb.el_statistic(rng.normal(0.5, 1, 59)) for _ in range(50)]
    assert np.median(big) > 3.84


def test_jackknife_se_matches_a_direct_loop():
    rng = np.random.default_rng(8)
    X = rng.chisquare(5, (30, 3))
    th = [np.log(np.delete(X, i, 0).mean(0)[0] / np.delete(X, i, 0).mean(0)[1]) for i in range(30)]
    se = np.sqrt(29 / 30 * np.sum((np.array(th) - np.mean(th)) ** 2))
    assert np.isclose(rb._jackknife_se(X, 0, 1), se)
