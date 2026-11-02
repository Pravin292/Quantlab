"""FAST synthetic generator of the H1 market matrix (days x [open, middle, close] of mean squared returns).  ALL SIMULATED.

For H1 only close-to-close returns of the three periods matter. In the bar-level simulator
(`nulls.simulate_raw` -> `clean` -> `build_bar_table`) a return is exactly  vol_slot * exp(day factor) * shock
(no intraday regime, AR term or missing bars in these scenarios), so the period mean square can be computed
directly. This module does that in a few array operations, which allows thousands of simulations per scenario.
It is only valid for those scenarios; equivalence with the bar-level simulator is checked statistically in
tests and in the M4b report (rejection rates of the same test in the same scenarios).

Dependence uses the same device as `dependence.py`: stock day factors with persistence `phi` and cross-stock
correlation `share`; shared Gaussian shock core with Student-t mixing (Pearson target `ret_corr`).
"""
from __future__ import annotations

import numpy as np

from ..calendars import Market, expected_slots
from ..eda.masks import assign_period
from .dependence import core_corr_for_pearson, day_factors

PERIOD_NAMES = ("open", "middle", "close")


def used_slot_index(market: Market) -> list[np.ndarray]:
    """Per period: slot positions whose close-to-close return is used by H1 (the session's first candle has none)."""
    periods = assign_period(expected_slots(market, "2026-08-03"), market).to_numpy()
    out = []
    for p in PERIOD_NAMES:
        idx = np.where(periods == p)[0]
        out.append(idx[idx > 0])
    return out


def simulate_returns_sq(market: Market, n_stocks: int, n_days: int, rng: np.random.Generator, *,
                        profile: np.ndarray, df: float = 4.0, day_vol_sd: float = 0.3,
                        share: float = 0.0, phi: float = 0.0, ret_corr: float = 0.0) -> np.ndarray:
    """Squared returns, shape (stocks, days, slots)."""
    n = market.bars_per_day
    f = day_factors(n_days, n_stocks, day_vol_sd, share, phi, rng)               # (S, D)
    scale = np.sqrt((df - 2) / df)
    if ret_corr > 0:
        c = core_corr_for_pearson(ret_corr, df)
        z = np.sqrt(c) * rng.standard_normal((1, n_days, n)) + np.sqrt(1 - c) * rng.standard_normal((n_stocks, n_days, n))
        eps = z / np.sqrt(rng.chisquare(df, (n_stocks, n_days, n)) / df) * scale
    else:
        eps = rng.standard_t(df, (n_stocks, n_days, n)) * scale
    r = np.asarray(profile)[None, None, :] * np.exp(f)[:, :, None] * eps
    return r * r


def period_matrix(r2: np.ndarray, idx: list[np.ndarray]) -> np.ndarray:
    """(days, 3) market matrix: period mean square averaged over stocks."""
    return np.stack([r2[:, :, i].mean(axis=-1) for i in idx], axis=-1).mean(axis=0)


def replace_extremes(r2: np.ndarray, idx: list[np.ndarray], k: int) -> np.ndarray:
    """DIAGNOSTIC ONLY (not an estimator): replace the k largest squared returns among the used bars by the median of
    the same stock and slot across days. Shows how much the test depends on a few extreme observations."""
    out = r2.copy()
    used = np.concatenate(idx)
    sub = out[:, :, used]
    med = np.median(sub, axis=1, keepdims=True)
    flat = sub.reshape(-1)
    top = np.argpartition(flat, -k)[-k:]
    s, d, u = np.unravel_index(top, sub.shape)
    sub[s, d, u] = med[s, 0, u]
    out[:, :, used] = sub
    return out


def simulate_market_matrix(market: Market, n_stocks: int, n_days: int, rng: np.random.Generator, **kw) -> np.ndarray:
    return period_matrix(simulate_returns_sq(market, n_stocks, n_days, rng, **kw), used_slot_index(market))
