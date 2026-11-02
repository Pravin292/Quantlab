import numpy as np
import pytest

from quantlab.research.tail_descriptives import hill_alpha, tail_summary


def test_hill_recovers_a_pareto_tail_index():
    rng = np.random.default_rng(0)
    x = (1 - rng.random(200_000)) ** (-1 / 3.0)                  # Pareto, alpha = 3
    assert hill_alpha(x, 4000) == pytest.approx(3.0, rel=0.05)


def test_hill_rejects_bad_k():
    with pytest.raises(ValueError):
        hill_alpha(np.arange(1.0, 11.0), 1)


def test_tail_summary_gaussian_kurtosis_and_exceedances():
    rng = np.random.default_rng(1)
    s = tail_summary(rng.standard_normal(400_000) ** 2)
    assert s["kurtosis"] == pytest.approx(3.0, abs=0.1)
    assert s["share_abs_z_gt_3_per_1000"] == pytest.approx(2.7, abs=0.4)


def test_tail_summary_ignores_nan_and_zero():
    e2 = np.array([np.nan, 0.0] + list(np.random.default_rng(2).random(500) + 0.1))
    assert tail_summary(e2)["n"] == 500
