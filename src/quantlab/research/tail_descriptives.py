"""DESCRIPTIVE tail-weight summaries of standardised bar returns (H1 calibration, Stage 0). No hypothesis test.

`tail_summary` takes the standardised squared shocks e2 produced by h1_calibration.fit_bar_model (mean 1 within each period)
and returns scale-free summaries that can also be computed on simulated worlds with known tails, so that an observed value
can be read against a reference (the Hill estimator in particular is biased in samples of this size and must be read that way).
"""
from __future__ import annotations

import numpy as np


def hill_alpha(x: np.ndarray, k: int) -> float:
    """Hill estimator of the tail index of positive data from the k largest values."""
    x = np.sort(np.asarray(x, float))[::-1]
    if k < 2 or k >= len(x):
        raise ValueError("need 2 <= k < n")
    return float(1.0 / np.mean(np.log(x[:k] / x[k])))


def tail_summary(e2: np.ndarray, hill_fracs=(0.01, 0.02, 0.05, 0.10)) -> dict:
    """e2: any array of standardised squared shocks (NaN allowed). |z| = sqrt(e2)."""
    z = np.sqrt(np.asarray(e2, float).ravel())
    z = z[np.isfinite(z) & (z > 0)]
    n = len(z)
    out = {"n": n, "kurtosis": float(np.mean(z ** 4) / np.mean(z ** 2) ** 2), "max_abs_z": float(z.max())}
    for c in (3, 4, 5, 6):
        out[f"share_abs_z_gt_{c}_per_1000"] = float(1000 * np.mean(z > c))
    for f in hill_fracs:
        out[f"hill_alpha_top{int(round(100 * f))}pct"] = hill_alpha(z, max(2, int(f * n)))
    return out
