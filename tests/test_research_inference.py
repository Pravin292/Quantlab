import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from quantlab.research import inference as inf


def test_holm_known_example():
    p = [0.01, 0.04, 0.03, 0.005]
    # sorted: .005*4=.02, .01*3=.03, .03*2=.06, .04*1=.04 -> made monotone: .02,.03,.06,.06
    assert inf.holm(p) == pytest.approx([0.03, 0.06, 0.06, 0.02])


def test_holm_never_exceeds_one_and_is_at_least_raw_p():
    p = np.array([0.2, 0.5, 0.9])
    adj = inf.holm(p)
    assert (adj >= p).all() and (adj <= 1).all()


def test_bh_known_example_and_less_strict_than_holm():
    p = [0.01, 0.02, 0.03, 0.04, 0.05]
    assert inf.benjamini_hochberg(p) == pytest.approx([0.05] * 5)
    q = [0.001, 0.008, 0.039, 0.041, 0.6]
    assert (inf.benjamini_hochberg(q) <= inf.holm(q) + 1e-12).all()


def test_bonferroni_reference_values_are_not_holm_thresholds():
    assert inf.bonferroni_reference(0.05, 8) == pytest.approx(0.00625)
    assert inf.bonferroni_reference(0.05, 14) == pytest.approx(0.05 / 14)
    # Holm compares the SMALLEST p to alpha/m, the next to alpha/(m-1), ...:
    # p = (0.006, 0.02) in a family of 2 -> Bonferroni 0.025 rejects both; Holm rejects both
    # p = (0.02, 0.04): Bonferroni(0.025) rejects one; Holm adjusted (0.04, 0.04) rejects none at... 0.05 both
    adj = inf.holm([0.02, 0.04])
    assert adj == pytest.approx([0.04, 0.04])


def _data(seed=0, n_days=40, per_day=25, beta=0.5):
    rng = np.random.default_rng(seed)
    days = np.repeat(np.arange(n_days), per_day)
    x = rng.normal(size=len(days))
    shock = np.repeat(rng.normal(size=n_days), per_day)          # day-level shared noise
    y = beta * x + shock + rng.normal(size=len(days))
    X = np.column_stack([np.ones(len(days)), x])
    return y, X, days


def test_ols_cluster_matches_statsmodels():
    y, X, g = _data()
    mine = inf.ols_cluster(y, X, g)
    codes = pd.factorize(g)[0]
    ref = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": codes})
    assert mine["beta"] == pytest.approx(ref.params)
    assert mine["se"] == pytest.approx(ref.bse)


def test_clustered_se_larger_than_naive_when_days_share_noise():
    y, X, g = _data()
    naive = sm.OLS(y, X).fit().bse
    assert inf.ols_cluster(y, X, g)["se"][0] > naive[0]          # the intercept feels the day shocks


def test_wild_cluster_p_small_for_real_effect_and_large_for_none():
    rng = np.random.default_rng(1)
    y, X, g = _data(beta=0.6)
    assert inf.wild_cluster_p(y, X, g, 1, 399, rng) < 0.02
    y0, X0, g0 = _data(seed=3, beta=0.0)
    assert inf.wild_cluster_p(y0, X0, g0, 1, 399, rng) > 0.05


def test_demean_within_group_means_are_zero():
    df = pd.DataFrame({"a": [1.0, 3.0, 10.0, 20.0], "g": ["x", "x", "y", "y"]})
    out = inf.demean_within(df, ["a"], "g")
    assert out["a"].tolist() == [-1.0, 1.0, -5.0, 5.0]


def test_resample_days_shapes_and_blocks():
    rng = np.random.default_rng(0)
    assert inf.resample_days(30, 7, rng).shape == (7, 30)
    b = inf.resample_days(30, 5, rng, block=3)
    assert b.shape == (5, 30)
    assert (np.diff(b[:, :3], axis=1) == 1).all()                # consecutive days inside a block


def test_demean_two_way_removes_both_sets_of_group_means():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"a": rng.normal(size=60), "g1": np.tile(np.arange(6), 10),
                       "g2": np.repeat(np.arange(10), 6)})
    out = inf.demean_two_way(df, ["a"], "g1", "g2")
    assert out.groupby("g1")["a"].mean().abs().max() < 1e-8
    assert out.groupby("g2")["a"].mean().abs().max() < 1e-8
