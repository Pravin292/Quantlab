"""Alternative H1 inference candidates that KEEP the RMS estimand.   (M4b diagnostics; not frozen)

All take the days x 3 matrix M of period mean squares (average over stocks) and test that the three
period variances are equal, using the same three pairwise contrasts as h1_rms2. The target is unchanged:
the day-weighted pooled variance ratio. Nothing here trims, winsorises or subsamples the data.

  bootstrap_t_jackknife   bootstrap-t for ln(mean_a/mean_b) with a DELETE-ONE JACKKNIFE standard error inside every
                          resample (instead of the delta-method SE of h1_rms2). Accounts for the non-linearity of
                          the ratio; costs O(B*n).
  wild_bootstrap_t        wild bootstrap-t for the LINEAR contrasts E[ms_a - ms_b] = 0 with the null imposed: the
                          day-level contrasts are multiplied by random weights (Rademacher, or Mammen which also
                          matches skewness). Same weight for all three contrasts in a resample keeps their dependence.
                          Handles day-to-day heteroskedasticity; Rademacher is exact only for symmetric contrasts.
  empirical_likelihood_diff  Owen's empirical likelihood test of each linear contrast = 0, chi-square(1) calibrated
                          at alpha/3 (Bonferroni). Data-driven shape of the interval; known to under-cover with
                          heavy tails and small n; returns 'reject' when 0 lies outside the convex hull.
Multiplicity: the bootstrap versions use one critical value for max |t| over the three contrasts.
"""
from __future__ import annotations

import numpy as np
from scipy import optimize, stats

from .h1_rms import CONTRAST_IDX
from .inference import resample_days

ALPHA = 0.05


def _log_ratio_of_means(X: np.ndarray, a: int, b: int):
    return np.log(X[..., a].mean(axis=-1) / X[..., b].mean(axis=-1))


def _jackknife_se(X: np.ndarray, a: int, b: int) -> np.ndarray:
    """Delete-one jackknife SE of ln(mean_a/mean_b). X: (n,3) or (B,n,3)."""
    n = X.shape[-2]
    S = X.sum(axis=-2, keepdims=True)
    loo = (S - X) / (n - 1)
    th = np.log(loo[..., a] / loo[..., b])
    return np.sqrt((n - 1) / n * ((th - th.mean(axis=-1, keepdims=True)) ** 2).sum(axis=-1))


def bootstrap_t_jackknife(M: np.ndarray, rng: np.random.Generator, B: int = 999, alpha: float = ALPHA) -> dict:
    n = len(M)
    Xb = M[resample_days(n, B, rng)]
    ts, tstar = [], []
    for a, b in CONTRAST_IDX:
        th = float(_log_ratio_of_means(M, a, b))
        ts.append(th / float(_jackknife_se(M, a, b)))
        tstar.append((_log_ratio_of_means(Xb, a, b) - th) / _jackknife_se(Xb, a, b))
    ts, tstar = np.abs(np.array(ts)), np.abs(np.stack(tstar, axis=1))
    crit_max = float(np.quantile(tstar.max(axis=1), 1 - alpha))
    crit_c = np.quantile(tstar, 1 - alpha / 3, axis=0)
    return {"reject_max": bool(ts.max() > crit_max), "reject_bonf": bool((ts > crit_c).any()), "t": ts, "crit_max": crit_max}


def _mammen(rng, B, n):
    s5 = np.sqrt(5.0)
    lo, hi = -(s5 - 1) / 2, (s5 + 1) / 2
    p_lo = (s5 + 1) / (2 * s5)
    return np.where(rng.random((B, n)) < p_lo, lo, hi)


def wild_bootstrap_t(M: np.ndarray, rng: np.random.Generator, B: int = 1999, weights: str = "mammen",
                     alpha: float = ALPHA) -> dict:
    n = len(M)
    D = np.stack([M[:, a] - M[:, b] for a, b in CONTRAST_IDX], axis=1)             # n x 3
    t = np.abs(D.mean(axis=0) / (D.std(axis=0, ddof=1) / np.sqrt(n)))
    w = (rng.integers(0, 2, (B, n)) * 2.0 - 1.0) if weights == "rademacher" else _mammen(rng, B, n)
    Db = w[:, :, None] * D[None]
    tb = np.abs(Db.mean(axis=1) / (Db.std(axis=1, ddof=1) / np.sqrt(n)))
    crit_max = float(np.quantile(tb.max(axis=1), 1 - alpha))
    crit_c = np.quantile(tb, 1 - alpha / 3, axis=0)
    return {"reject_max": bool(t.max() > crit_max), "reject_bonf": bool((t > crit_c).any()), "t": t, "crit_max": crit_max}


def el_statistic(d: np.ndarray) -> float:
    """-2 log empirical likelihood ratio for H0: mean(d) = 0 (inf if 0 is outside the convex hull)."""
    d = np.asarray(d, float)
    d = d / np.abs(d).max()
    if d.min() >= 0 or d.max() <= 0:
        return float("inf")
    eps = 1e-10
    lo, hi = -1 / d.max() + eps, -1 / d.min() - eps
    g = lambda lam: np.sum(d / (1 + lam * d))
    lam = optimize.brentq(g, lo, hi, xtol=1e-12, maxiter=200)
    return float(2 * np.sum(np.log1p(lam * d)))


def empirical_likelihood_diff(M: np.ndarray, alpha: float = ALPHA) -> dict:
    stats_ = np.array([el_statistic(M[:, a] - M[:, b]) for a, b in CONTRAST_IDX])
    crit = stats.chi2.ppf(1 - alpha / 3, 1)
    return {"reject_bonf": bool((stats_ > crit).any()), "stat": stats_, "crit": float(crit)}
