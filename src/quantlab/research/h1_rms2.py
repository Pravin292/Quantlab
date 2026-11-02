"""H1 calibration candidates, round 2 (diagnostics, not frozen).   Extends h1_rms.py; does not change it.

Adds, for the two leading RMS-preserving tests ("rom": ln of the ratio of period-average squared returns;
"diff": the linear contrast of period-average squared returns):
  * a SINGLE max-statistic bootstrap-t for the three contrasts (one critical value for max |t|),
    alongside the Bonferroni rule of round 1, from the same bootstrap draws;
  * a block-aware standard error (blocks of consecutive days) and block bootstrap, for volatility
    clustering across days; block = 1 reduces exactly to the iid-day case;
  * the raw ingredients (estimate, SE, t, critical values) so a failure can be diagnosed;
  * a day-level jackknife bias-corrected estimate of the log ratio.
Unit of resampling: the trading day. Input M is the days x 3 matrix of mean squares (average over stocks).
"""
from __future__ import annotations

import numpy as np

from .h1_rms import CONTRAST_IDX
from .inference import resample_days


def _se_blocks(u: np.ndarray, block: int) -> np.ndarray:
    """SE of the mean of u (last axis = days) using non-overlapping blocks of `block` consecutive days.
    block = 1 gives sd/sqrt(n) (ddof = 1)."""
    n = u.shape[-1]
    m = n // block
    ub = u[..., : m * block].reshape(*u.shape[:-1], m, block).sum(axis=-1)
    return np.sqrt(ub.var(axis=-1, ddof=1) * m) / (m * block)


def _influence(X: np.ndarray, a: int, b: int, kind: str) -> tuple[np.ndarray, np.ndarray]:
    """(estimate, per-day series whose mean-SE is the SE of the estimate). X is (n,3) or (B,n,3)."""
    ma, mb = X[..., a].mean(axis=-1, keepdims=True), X[..., b].mean(axis=-1, keepdims=True)
    if kind == "rom":
        return np.log(ma[..., 0] / mb[..., 0]), X[..., a] / ma - X[..., b] / mb
    if kind == "diff":
        return ma[..., 0] - mb[..., 0], X[..., a] - X[..., b]
    raise ValueError(kind)


def bootstrap_t(M: np.ndarray, rng: np.random.Generator, kind: str, B: int = 999, alpha: float = 0.05,
                block: int = 1) -> dict:
    """Bootstrap-t for the three pairwise contrasts. Returns both multiplicity rules:
       bonf  reject if any |t_c| exceeds the (1 - alpha/3) quantile of |t*_c| (round-1 rule)
       max   reject if max_c |t_c| exceeds the (1 - alpha) quantile of max_c |t*_c|  (single critical value)
    plus theta, se, t, per-contrast critical values, the jackknife bias-corrected log ratio (rom only)."""
    n = len(M)
    idx = resample_days(n, B, rng, block)
    Xb = M[idx]
    theta, se, t, tstar = [], [], [], []
    for a, b in CONTRAST_IDX:
        th, u = _influence(M, a, b, kind)
        s = _se_blocks(u, block)
        thb, ub = _influence(Xb, a, b, kind)
        sb = _se_blocks(ub, block)
        theta.append(float(th)); se.append(float(s)); t.append(float(th / s))
        tstar.append((thb - th) / sb)
    tstar = np.stack(tstar, axis=1)                                   # B x 3
    crit_c = np.quantile(np.abs(tstar), 1 - alpha / 3, axis=0)
    crit_max = float(np.quantile(np.abs(tstar).max(axis=1), 1 - alpha))
    t = np.array(t)
    out = {"theta": np.array(theta), "se": np.array(se), "t": t, "crit_bonf": crit_c, "crit_max": crit_max,
           "reject_bonf": bool((np.abs(t) > crit_c).any()), "reject_max": bool(np.abs(t).max() > crit_max)}
    if kind == "rom":
        tot = M.sum(axis=0)
        jk = []
        for (a, b), th in zip(CONTRAST_IDX, theta):
            loo = (tot[None, :] - M) / (n - 1)
            jk.append(n * th - (n - 1) * np.log(loo[:, a] / loo[:, b]).mean())
        out["theta_jk"] = np.array(jk)
    return out
