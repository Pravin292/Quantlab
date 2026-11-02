"""Statistical inference helpers shared by H1, H2 and H3.

The unit of independent evidence is the TRADING DAY. Bars within a day are
dependent, so everything here either works on one number per day or clusters
(groups) observations by day.

Contents
--------
holm, benjamini_hochberg   multiple-testing corrections
bonferroni_reference       the plain alpha/m reference threshold (NOT Holm's
                           sequential thresholds; see docs/07)
ols_cluster                OLS with day-clustered standard errors (CR1)
wild_cluster_p             wild cluster bootstrap p-value (null imposed)
demean_within              absorb fixed effects (e.g. stock x slot)
resample_days, percentile_ci   day-block bootstrap helpers
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


# ---------------------------------------------------------------- p-values
def holm(p) -> np.ndarray:
    """Holm step-down adjusted p-values (controls family-wise error)."""
    p = np.asarray(p, float)
    m = len(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(np.argsort(p)):
        running = max(running, (m - rank) * p[i])      # enforce monotonicity
        adj[i] = min(1.0, running)
    return adj


def benjamini_hochberg(p) -> np.ndarray:
    """BH adjusted p-values (q-values; controls false discovery rate)."""
    p = np.asarray(p, float)
    m = len(p)
    order = np.argsort(p)[::-1]                         # largest first
    adj = np.empty(m)
    running = 1.0
    for k, i in enumerate(order):
        rank = m - k
        running = min(running, p[i] * m / rank)
        adj[i] = running
    return adj


def bonferroni_reference(alpha: float, m: int) -> float:
    """alpha / m. A reference threshold only; Holm's actual thresholds are
    alpha/m, alpha/(m-1), ... applied to the sorted p-values."""
    return alpha / m


# ---------------------------------------------------------- clustered OLS
def _cluster_codes(groups):
    codes, uniq = pd.factorize(pd.Series(groups))
    return codes, len(uniq)


def ols_cluster(y, X, groups) -> dict:
    """OLS with cluster-robust (CR1) standard errors.

    Small-sample factor G/(G-1) * (n-1)/(n-k), the same as statsmodels'
    cov_type="cluster" default. p-values use a t distribution with G-1
    degrees of freedom because the number of clusters (days) is small."""
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    n, k = X.shape
    codes, G = _cluster_codes(groups)
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ X.T @ y
    u = y - X @ beta
    scores = np.zeros((G, k))
    np.add.at(scores, codes, X * u[:, None])
    c = G / (G - 1) * (n - 1) / (n - k)
    cov = c * xtx_inv @ (scores.T @ scores) @ xtx_inv
    se = np.sqrt(np.diag(cov))
    t = beta / se
    p = 2 * stats.t.sf(np.abs(t), G - 1)
    return {"beta": beta, "se": se, "t": t, "p": p, "n": n, "n_clusters": G, "cov": cov}


def wild_cluster_p(y, X, groups, j: int, B: int, rng: np.random.Generator) -> float:
    """Wild cluster bootstrap p-value for coefficient j (WCR, Rademacher weights).

    The model is re-fitted WITHOUT column j (imposing H0: beta_j = 0); its
    residuals are flipped in sign cluster-by-cluster, and the clustered t
    statistic for beta_j is recomputed on the full model. Recommended when the
    number of clusters is small, as it is here (about 50-60 days)."""
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    n, k = X.shape
    codes, G = _cluster_codes(groups)
    onehot = np.zeros((n, G))
    onehot[np.arange(n), codes] = 1.0
    c = G / (G - 1) * (n - 1) / (n - k)
    xtx_inv = np.linalg.inv(X.T @ X)
    proj = xtx_inv @ X.T

    def t_stat(yv):
        beta = proj @ yv
        u = yv - X @ beta
        scores = onehot.T @ (X * u[:, None])
        cov = c * xtx_inv @ (scores.T @ scores) @ xtx_inv
        return beta[j] / np.sqrt(cov[j, j])

    t0 = t_stat(y)
    Xr = np.delete(X, j, axis=1)
    if Xr.shape[1]:
        fitted_r = Xr @ np.linalg.lstsq(Xr, y, rcond=None)[0]
    else:
        fitted_r = np.zeros(n)
    resid_r = y - fitted_r
    hits = 0
    for _ in range(B):
        w = rng.choice([-1.0, 1.0], size=G)[codes]
        if abs(t_stat(fitted_r + resid_r * w)) >= abs(t0):
            hits += 1
    return (hits + 1) / (B + 1)          # +1 keeps p away from exactly 0


def demean_within(df: pd.DataFrame, cols, by) -> pd.DataFrame:
    """Subtract group means (absorbs fixed effects, Frisch-Waugh-Lovell)."""
    out = df.copy()
    out[list(cols)] = df[list(cols)] - df.groupby(by)[list(cols)].transform("mean")
    return out


def demean_two_way(df: pd.DataFrame, cols, by1, by2, tol: float = 1e-10, max_iter: int = 200) -> pd.DataFrame:
    """Absorb TWO sets of fixed effects (e.g. stock x slot and stock x day) by
    alternately removing each set's group means until nothing changes."""
    out = df.copy()
    cols = list(cols)
    for _ in range(max_iter):
        before = out[cols].to_numpy().copy()
        out[cols] = out[cols] - out.groupby(by1)[cols].transform("mean")
        out[cols] = out[cols] - out.groupby(by2)[cols].transform("mean")
        if np.abs(out[cols].to_numpy() - before).max() < tol:
            break
    return out


# ------------------------------------------------------ day-block bootstrap
def resample_days(n_days: int, B: int, rng: np.random.Generator, block: int = 1) -> np.ndarray:
    """Index matrix (B x n_days) of days drawn with replacement.
    block > 1 resamples runs of consecutive days (for day-to-day dependence)."""
    if block == 1:
        return rng.integers(0, n_days, size=(B, n_days))
    n_blocks = int(np.ceil(n_days / block))
    starts = rng.integers(0, n_days - block + 1, size=(B, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(B, -1)
    return idx[:, :n_days]


def percentile_ci(values, level: float = 0.95) -> tuple[float, float]:
    lo = (1 - level) / 2
    return tuple(np.nanquantile(values, [lo, 1 - lo]))
