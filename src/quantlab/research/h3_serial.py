"""H3: do 5-minute returns show momentum (positive serial dependence) or
mean reversion (negative)?

Standardised, demeaned return (per stock and slot, full-sample => inference only):
    z_t = (r_t - mu_slot) / sigma_slot          sigma uses ddof = 1, needs >= 5 days

Lag-k autocorrelation (all pairs inside ONE day, exactly k bars apart):
    rho_k = [ (1/n_k) * sum z_t z_{t-k} ]  /  [ (1/n) * sum z_t^2 ]

* Matrices have one row per day, so a lag never reaches into another day.
* A pair needs BOTH returns to exist (missing bars, forming bars and the NSE
  closing window are NaN), so gaps simply remove the affected pairs.
* The 6 autocorrelations are tested jointly with a Wald test whose covariance
  clusters by calendar day (stocks of one market on the same day share a
  cluster). Reference distribution: F(K, G-K) after a Hotelling-type scaling,
  because there are only G ~ 59 clusters.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy import stats

from .panel import to_matrix

MIN_OBS = 5
KMAX = 6


def zscore_matrix(table: pd.DataFrame, min_obs: int = MIN_OBS, demean: str = "slot"):
    """days x slots matrix of standardised returns. demean in {"slot","overall","none"}."""
    m = table["market"].iloc[0]
    R, dates = to_matrix(table, "ret", m)
    count = (~np.isnan(R)).sum(axis=0)
    with np.errstate(invalid="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)      # empty slots (e.g. the opening candle) give NaN
        if demean == "slot":
            mu = np.nanmean(R, axis=0)
        elif demean == "overall":
            mu = np.full(R.shape[1], np.nanmean(R))
        elif demean == "none":
            mu = np.zeros(R.shape[1])
        else:
            raise ValueError(demean)
        sd = np.nanstd(R - mu, axis=0, ddof=1)
    sd = np.where(count >= min_obs, sd, np.nan)
    return (R - mu) / sd, dates


def day_sums(Z: np.ndarray, kmax: int = KMAX):
    """Per-day sufficient statistics: cross-product sums N[d,k], pair counts n[d,k],
    squared sums D[d] and counts m[d]. Lag k pairs are columns (s, s-k) of the SAME row."""
    nd = Z.shape[0]
    N = np.zeros((nd, kmax))
    n = np.zeros((nd, kmax))
    for k in range(1, kmax + 1):
        prod = Z[:, k:] * Z[:, :-k]
        N[:, k - 1] = np.nansum(prod, axis=1)
        n[:, k - 1] = (~np.isnan(prod)).sum(axis=1)
    D = np.nansum(Z ** 2, axis=1)
    m = (~np.isnan(Z)).sum(axis=1)
    return N, n, D, m


def pooled_day_sums(Zs: list, kmax: int = KMAX):
    """Add the per-day sums of several stocks that share calendar dates.
    `Zs` is a list of (Z, dates). Clusters are calendar days."""
    all_dates = sorted(set().union(*[set(d) for _, d in Zs]))
    pos = {d: i for i, d in enumerate(all_dates)}
    N = np.zeros((len(all_dates), kmax)); n = np.zeros_like(N)
    D = np.zeros(len(all_dates)); m = np.zeros(len(all_dates))
    for Z, dates in Zs:
        a, b, c, d = day_sums(Z, kmax)
        idx = [pos[x] for x in dates]
        N[idx] += a; n[idx] += b; D[idx] += c; m[idx] += d
    return N, n, D, m, all_dates


def rho_from_sums(N, n, D, m):
    A = N.sum(axis=0) / n.sum(axis=0)
    Bv = D.sum() / m.sum()
    return A / Bv


def rho_and_cov(N, n, D, m):
    """rho_k and its day-clustered covariance via a ratio (delta-method) linearisation."""
    keep = (m > 0)
    N, n, D, m = N[keep], n[keep], D[keep], m[keep]
    G = len(m)
    A = N.sum(axis=0) / n.sum(axis=0)
    Bv = D.sum() / m.sum()
    rho = A / Bv
    # influence of each day on rho_k
    psi = ((N - A * n) / n.sum(axis=0)) / Bv - rho * ((D - Bv * m) / m.sum())[:, None] / Bv
    cov = G / (G - 1) * psi.T @ psi
    return rho, cov, G


def wald_test(rho, cov, G: int) -> dict:
    K = len(rho)
    W = float(rho @ np.linalg.solve(cov, rho))
    F = W * (G - K) / (K * (G - 1))              # Hotelling-type small-sample scaling
    p = float(stats.f.sf(F, K, G - K))
    return {"wald": W, "F": F, "p": p, "df1": K, "df2": G - K}


def omnibus_autocorr(Zs: list, kmax: int = KMAX) -> dict:
    """Primary H3 test for one market: H0 rho_1 = ... = rho_kmax = 0."""
    N, n, D, m, dates = pooled_day_sums(Zs, kmax)
    rho, cov, G = rho_and_cov(N, n, D, m)
    out = wald_test(rho, cov, G)
    out.update(rho=rho, se=np.sqrt(np.diag(cov)), n_pairs=n.sum(axis=0), n_clusters=G)
    return out


def omnibus_autocorr_bootstrap(Zs: list, rng: np.random.Generator, B: int = 999, kmax: int = KMAX) -> dict:
    """Day-block bootstrap cross-check. Days are resampled whole; the statistic is
    centred at the full-sample estimate so it approximates the NULL distribution."""
    N, n, D, m, _ = pooled_day_sums(Zs, kmax)
    rho, cov, G = rho_and_cov(N, n, D, m)
    W = float(rho @ np.linalg.solve(cov, rho))
    exceed = 0
    done = 0
    for _ in range(B):
        idx = rng.integers(0, len(m), len(m))
        try:
            r_b, c_b, _ = rho_and_cov(N[idx], n[idx], D[idx], m[idx])
            d = r_b - rho
            W_b = float(d @ np.linalg.solve(c_b, d))
        except np.linalg.LinAlgError:
            continue
        done += 1
        exceed += W_b >= W
    return {"wald": W, "p_boot": (exceed + 1) / (done + 1), "B": done}


def variance_ratio_sums(Z: np.ndarray, q: int):
    """Per-day sums for VR(q): sums of squared q-bar returns (overlapping, inside a day)."""
    S = np.zeros_like(Z[:, q - 1:])
    valid = np.ones_like(S, dtype=bool)
    for i in range(q):
        part = Z[:, q - 1 - i: Z.shape[1] - i]
        S = S + np.nan_to_num(part)
        valid &= ~np.isnan(part)
    sq = np.where(valid, S ** 2, 0.0)
    return sq.sum(axis=1), valid.sum(axis=1), np.nansum(Z ** 2, axis=1), (~np.isnan(Z)).sum(axis=1)


def variance_ratio(Z: np.ndarray, q: int) -> float:
    """VR(q) = Var(q-bar return) / (q * Var(1-bar return)): >1 momentum, <1 reversion."""
    s, c, d, m = variance_ratio_sums(Z, q)
    return float((s.sum() / c.sum()) / (q * d.sum() / m.sum()))
