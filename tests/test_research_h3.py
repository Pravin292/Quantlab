import numpy as np
import pytest

from quantlab.calendars import NSE, US
from quantlab.research import h3_serial as h3
from quantlab.research.nulls import simulate_table

from research_helpers import bars_table


def brute_force_sums(Z, kmax):
    """Slow, obviously-correct reference: loop day by day, pair only inside a day."""
    nd, ns = Z.shape
    N = np.zeros((nd, kmax)); n = np.zeros((nd, kmax))
    for d in range(nd):
        for k in range(1, kmax + 1):
            for s in range(k, ns):
                a, b = Z[d, s], Z[d, s - k]
                if not (np.isnan(a) or np.isnan(b)):
                    N[d, k - 1] += a * b
                    n[d, k - 1] += 1
    return N, n


def test_day_sums_match_brute_force_with_gaps():
    rng = np.random.default_rng(0)
    Z = rng.normal(size=(7, 20))
    Z[rng.random(Z.shape) < 0.15] = np.nan
    N, n, D, m = h3.day_sums(Z, 4)
    N2, n2 = brute_force_sums(Z, 4)
    assert np.allclose(N, N2) and np.allclose(n, n2)


def test_pair_counts_are_exactly_n_minus_k_per_day_and_never_cross_days():
    Z = np.ones((3, 10))
    N, n, D, m = h3.day_sums(Z, 3)
    assert (n == np.array([9, 8, 7]) * np.ones((3, 1))).all()       # 10-k pairs per day, 3 days
    # a huge value at the END of day 1 and the START of day 2 must never be multiplied together
    Z2 = np.zeros((2, 10)); Z2[0, -1] = 100.0; Z2[1, 0] = 100.0
    N2, *_ = h3.day_sums(Z2, 3)
    assert N2.sum() == 0.0


def test_one_missing_bar_removes_exactly_the_pairs_that_use_it():
    Z = np.ones((1, 10)); Z[0, 4] = np.nan
    _, n, _, _ = h3.day_sums(Z, 2)
    assert n[0].tolist() == [9 - 2, 8 - 2]                           # lag1 loses 2 pairs, lag2 loses 2


def test_estimator_exact_on_alternating_series():
    Z = np.tile(np.array([1.0, -1.0] * 10), (5, 1))                  # perfect reversal
    N, n, D, m = h3.day_sums(Z, 3)
    rho = h3.rho_from_sums(N, n, D, m)
    assert rho == pytest.approx([-1.0, 1.0, -1.0])


def test_zscore_has_zero_mean_and_unit_sd_per_slot_and_respects_demean_options():
    t = simulate_table(US, "S", 40, np.random.default_rng(0))
    Z, _ = h3.zscore_matrix(t)
    has_data = (~np.isnan(Z)).sum(axis=0) >= 5          # the opening candle has no close-to-close return
    assert has_data.sum() == US.bars_per_day - 1
    assert np.nanmean(Z[:, has_data], axis=0) == pytest.approx(0.0, abs=1e-12)
    assert np.nanstd(Z[:, has_data], axis=0, ddof=1) == pytest.approx(1.0)


def test_slot_demeaning_removes_a_spurious_autocorrelation_caused_by_drift():
    rng = np.random.default_rng(1)
    drift = np.where(np.arange(30) % 2 == 0, 1.0, -1.0) * 0.8        # slot-specific mean pattern
    Z = rng.normal(size=(60, 30)) + drift
    N, n, D, m = h3.day_sums(Z, 1)
    raw = h3.rho_from_sums(N, n, D, m)[0]
    Zc = Z - np.nanmean(Z, axis=0)
    N, n, D, m = h3.day_sums(Zc, 1)
    centred = h3.rho_from_sums(N, n, D, m)[0]
    assert raw < -0.3 and abs(centred) < 0.05


def test_variance_ratio_known_cases():
    alt = np.tile(np.array([1.0, -1.0] * 20), (5, 1))
    assert h3.variance_ratio(alt, 2) == pytest.approx(0.0)           # perfect reversal
    rng = np.random.default_rng(0)
    assert h3.variance_ratio(rng.normal(size=(200, 60)), 6) == pytest.approx(1.0, abs=0.06)
    trend = np.cumsum(np.ones((5, 40)), axis=1)                       # perfectly persistent
    assert h3.variance_ratio(np.ones((5, 40)), 4) == pytest.approx(4.0)


# ---------- the estimator validated on simulated data with KNOWN autocorrelation ----------
@pytest.mark.parametrize("rho", [-0.10, 0.0, 0.10])
def test_estimator_recovers_known_rho_on_simulated_market_calendar(rho):
    rng = np.random.default_rng(10)
    est = []
    for _ in range(8):
        t = simulate_table(NSE, "S", 59, rng, rho=rho, nse_feed_quirks=True, df=4, day_vol_sd=0.3,
                           vol_edge_boost=1.0)
        Z, d = h3.zscore_matrix(t)
        est.append(h3.omnibus_autocorr([(Z, d)])["rho"][0])
    assert np.mean(est) == pytest.approx(rho, abs=0.02)


def test_wald_rejects_when_autocorrelation_is_real_and_accepts_when_absent():
    rng = np.random.default_rng(11)
    real = simulate_table(US, "S", 59, rng, rho=0.25)
    null = simulate_table(US, "S", 59, rng, rho=0.0)
    assert h3.omnibus_autocorr([h3.zscore_matrix(real)])["p"] < 1e-6
    assert h3.omnibus_autocorr([h3.zscore_matrix(null)])["p"] > 0.01


def test_bootstrap_crosscheck_agrees_in_direction():
    rng = np.random.default_rng(12)
    real = simulate_table(US, "S", 59, rng, rho=0.25)
    out = h3.omnibus_autocorr_bootstrap([h3.zscore_matrix(real)], rng, B=199)
    assert out["p_boot"] < 0.05


def test_cluster_by_calendar_day_pools_stocks():
    rng = np.random.default_rng(13)
    tabs = [simulate_table(US, f"S{i}", 59, rng, rho=0.0) for i in range(3)]
    res = h3.omnibus_autocorr([h3.zscore_matrix(t) for t in tabs])
    assert res["n_clusters"] == 59                                   # clusters = days, not stock-days
