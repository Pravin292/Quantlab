"""H1 calibration candidates, STAGE 0 (new, isolated; no existing module is changed).   ALL USED ON SIMULATED DATA ONLY.

The estimand is unchanged (day-weighted pooled variance ratio of the open, middle and close periods). The test statistic
is also unchanged: T = max over the three pairwise contrasts of |t|, with t = ln(mean_a / mean_b) divided by its
influence-function standard error (the "rom" statistic of h1_rms2). What differs between the candidates is only where
the critical value for T comes from.

  C1  null-imposed model-based bootstrap with empirical bar-level shocks
        fit a scale model to the bar-level squared returns,  r2[s,d,j] = v2[j] * g[s,d] * e2[s,d,j],
        v2 = slot scale profile, g = robust (median-based) day scale, e2 = standardised squared shock;
        build artificial datasets in which the period variances are EQUAL (the null) by rescaling the slot profile inside
        each period, and drawing shocks (jointly over stocks) from the empirical shocks of the SAME period and day scales
        from the observed day scales; the decision uses the Monte-Carlo p-value p = (1 + #{T* >= T}) / (R + 1) <= alpha (R + 1 should make alpha*(R+1)
        an integer, e.g. R = 499); the 1-alpha quantile of T* is returned as `crit` for diagnostics.
  C2  fast double bootstrap-t (Davidson & MacKinnon 2007 form; formula recalled from memory, to be checked in Stage 0)
  C3  a fixed critical value supplied by the caller (benchmark / fallback)

Shock draws keep the three stocks of one (day, slot) together, so cross-stock dependence of shocks is preserved; day
scales are drawn iid across days (day-to-day persistence is NOT reproduced; a documented limitation).
Missing bars are not supported by the resampler (it needs finite shocks); `fit_bar_model` itself tolerates NaN so that it
can be used for descriptive work on real data.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .h1_rms import CONTRAST_IDX
from .h1_rms2 import _influence, _se_blocks
from .inference import resample_days

ALPHA = 0.05


# ---------------------------------------------------------------------------------------------------- seeds
def child_seeds(master: int, n: int) -> list[np.random.SeedSequence]:
    """n independent child seed sequences of one master seed. Pass each directly to np.random.default_rng, which keeps
    the full 128-bit entropy (M4b truncated each child to one 32-bit integer, which allowed harmless coincidences)."""
    return list(np.random.SeedSequence(master).spawn(n))


# ---------------------------------------------------------------------------------------------------- statistic
def _parts(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Estimates and standard errors of the three log ratios; X is (n,3) or (B,n,3); returns arrays (...,3)."""
    th, se = [], []
    for a, b in CONTRAST_IDX:
        t_, u = _influence(X, a, b, "rom")
        th.append(t_)
        se.append(_se_blocks(u, 1))
    return np.stack(th, axis=-1), np.stack(se, axis=-1)


def max_abs_t(X: np.ndarray) -> np.ndarray:
    """T = max_c |theta_c / se_c| for X of shape (n,3) or (B,n,3)."""
    th, se = _parts(X)
    return np.abs(th / se).max(axis=-1)


def market_matrix_from_r2(r2_used: np.ndarray, groups: list[np.ndarray]) -> np.ndarray:
    """(days, 3) matrix of period mean squares averaged over stocks; r2_used is (stocks, days, used slots)."""
    return np.stack([np.nanmean(r2_used[:, :, g], axis=2) for g in groups], axis=-1).mean(axis=0)


def to_used(r2: np.ndarray, idx: list[np.ndarray]) -> tuple[np.ndarray, list[np.ndarray]]:
    """Restrict a (stocks, days, all slots) array to the slots H1 uses; returns the array and the three period groups
    as positions inside the restricted array."""
    order = np.concatenate(idx)
    groups, start = [], 0
    for i in idx:
        groups.append(np.arange(start, start + len(i)))
        start += len(i)
    return r2[:, :, order], groups


# ---------------------------------------------------------------------------------------------------- C1
@dataclass
class BarModel:
    v2: np.ndarray            # slot scale profile (K,), mean 1
    g: np.ndarray             # day scales (S, D)
    e2: np.ndarray            # standardised squared shocks (S, D, K), rescaled to mean 1 inside each period
    groups: list[np.ndarray]
    shape: np.ndarray         # slot shape relative to its own period mean (K,)


def fit_bar_model(r2: np.ndarray, groups: list[np.ndarray], n_iter: int = 3) -> BarModel:
    """Alternate between a robust day scale g = median_j(r2 / v2) and a slot profile v2 = mean_{s,d}(r2 / g)."""
    S, D, K = r2.shape
    v2 = np.ones(K)
    g = np.ones((S, D))
    for _ in range(n_iter):
        g = np.nanmedian(r2 / v2, axis=2)
        g = np.where(np.isfinite(g) & (g > 0), g, np.nanmean(g[np.isfinite(g) & (g > 0)]))
        v2 = np.nanmean(r2 / g[:, :, None], axis=(0, 1))
        v2 = v2 / np.nanmean(v2)
    e2 = r2 / (v2[None, None, :] * g[:, :, None])
    shape = np.empty(K)
    for gp in groups:
        e2[:, :, gp] = e2[:, :, gp] / np.nanmean(e2[:, :, gp])
        shape[gp] = v2[gp] / v2[gp].mean()
    return BarModel(v2=v2, g=g, e2=e2, groups=groups, shape=shape)


def null_world_matrices(model: BarModel, n_days: int, R: int, rng: np.random.Generator, chunk: int = 100) -> np.ndarray:
    """R artificial (n_days, 3) market matrices in which the three period variances are equal in expectation."""
    S, D, _ = model.e2.shape
    if not np.isfinite(model.e2).all():
        raise ValueError("the shock resampler needs finite standardised shocks (no missing bars)")
    flats = [model.e2[:, :, gp].reshape(S, -1) for gp in model.groups]
    out = np.empty((R, n_days, 3))
    for lo in range(0, R, chunk):
        hi = min(R, lo + chunk)
        r = hi - lo
        gstar = model.g[:, rng.integers(0, D, (r, n_days))]                              # (S, r, n)
        for p, gp in enumerate(model.groups):
            idx = rng.integers(0, flats[p].shape[1], (r, n_days, len(gp)))
            E = flats[p][:, idx]                                                         # (S, r, n, |gp|)
            m = (E * model.shape[gp]).mean(axis=3)                                       # (S, r, n)
            out[lo:hi, :, p] = (m * gstar).mean(axis=0)
    return out


def c1_test(r2_used: np.ndarray, groups: list[np.ndarray], rng: np.random.Generator, R: int = 499,
            alpha: float = ALPHA) -> dict:
    M = market_matrix_from_r2(r2_used, groups)
    model = fit_bar_model(r2_used, groups)
    Tstar = max_abs_t(null_world_matrices(model, len(M), R, rng))
    crit = float(np.quantile(Tstar, 1 - alpha))
    T = float(max_abs_t(M))
    p_mc = float((1 + np.sum(Tstar >= T)) / (R + 1))          # Monte-Carlo p-value; exact if T behaves like one more draw
    return {"T": T, "crit": crit, "p_mc": p_mc, "reject": bool(p_mc <= alpha)}


# ---------------------------------------------------------------------------------------------------- C2
def fast_double_bootstrap(M: np.ndarray, rng: np.random.Generator, B: int = 999, alpha: float = ALPHA) -> dict:
    """Fast double bootstrap-t for T. First level: p1 = share of T* >= T. Second level (one inner resample per outer):
    adjusted p = share of T** above the (1 - p1) quantile of T**. Reject when the adjusted p <= alpha."""
    n = len(M)
    th, _ = _parts(M)
    T = float(max_abs_t(M))
    Xb = M[resample_days(n, B, rng)]                                                     # (B, n, 3)
    thb, seb = _parts(Xb)
    Tstar = np.abs((thb - th) / seb).max(axis=-1)
    idx2 = rng.integers(0, n, (B, n))
    X2 = np.take_along_axis(Xb, idx2[:, :, None], axis=1)
    th2, se2 = _parts(X2)
    T2 = np.abs((th2 - thb) / se2).max(axis=-1)
    p1 = float(np.mean(Tstar >= T))
    q = float(np.quantile(T2, 1 - p1))
    p2 = float(np.mean(T2 > q))
    return {"T": T, "p_first": p1, "p_fdb": p2, "reject": bool(p2 <= alpha)}


# ---------------------------------------------------------------------------------------------------- C3
def c3_test(M: np.ndarray, crit: float) -> dict:
    T = float(max_abs_t(M))
    return {"T": T, "crit": float(crit), "reject": bool(T > crit)}
