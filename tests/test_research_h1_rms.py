import numpy as np
import pytest

from quantlab.calendars import NSE
from quantlab.research import h1_rms

from test_research_h1 import table_with_period_vol


def test_mean_square_panel_is_exact():
    t = table_with_period_vol(NSE, 0.004, 0.002, 0.003)
    p = h1_rms.mean_square_panel(t, "NSE")
    assert np.allclose(p["open"], 0.004 ** 2) and np.allclose(p["middle"], 0.002 ** 2) and np.allclose(p["close"], 0.003 ** 2)


def test_jackknife_removes_most_of_ln_rms_bias():
    rng = np.random.default_rng(1)
    n, reps = 8, 20000
    x = rng.standard_normal((reps, n))
    raw = (0.5 * np.log((x ** 2).mean(axis=1))).mean()
    jk = np.mean([h1_rms.jackknife_ln_rms(r) for r in x[:4000]])
    assert abs(raw) > 0.05                  # the bias is real (true ln sigma = 0)
    assert abs(jk) < 0.4 * abs(raw)


def test_jackknife_returns_nan_instead_of_log_of_zero():
    assert np.isnan(h1_rms.jackknife_ln_rms(np.array([0.0, 0.0, 0.0, 0.01])))


@pytest.mark.parametrize("method", ["pct", "t", "bca", "diff"])
def test_tests_detect_a_large_difference_and_report_log_ratio(method):
    rng = np.random.default_rng(2)
    base = np.exp(rng.normal(0, 0.3, (59, 1)))
    M = base * rng.chisquare(5, (59, 3)) / 5 * np.array([2.0, 1.0, 1.0])     # open variance doubled
    r = h1_rms.rms_ratio_test(M, rng, method, B=199)
    assert r["reject"] and 0.4 < r["open_mid"] < 1.0                          # ln 2 = 0.69


@pytest.mark.parametrize("method", ["pct", "t", "bca", "diff"])
def test_tests_rarely_reject_when_variances_are_equal(method):
    rng = np.random.default_rng(3)
    rej = 0
    for _ in range(100):
        M = np.exp(rng.normal(0, 0.3, (59, 1))) * rng.chisquare(5, (59, 3)) / 5
        rej += h1_rms.rms_ratio_test(M, rng, method, B=199)["reject"]
    assert rej <= 15                        # nominal 5%; loose bound for 100 reps


def test_market_matrix_drops_incomplete_days():
    import pandas as pd
    a = pd.DataFrame([[1.0, 2, 3], [np.nan, 2, 3]], index=[0, 1], columns=["open", "middle", "close"])
    b = a.copy()
    assert h1_rms.market_matrix([a, b]).shape == (1, 3)
