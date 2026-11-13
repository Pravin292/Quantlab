"""H1 calibration, STAGE 4 helpers: the six alternative processes a-f of the frozen v1.1 specification (A4). SIMULATED DATA ONLY. New file; nothing frozen is changed.

Parameters come from `outputs/milestone4/h1_calibration/frozen_spec_v1_1/alt_dgp_parameters.json` (process e as approved: a Gaussian scale mixture):
  a  intraday volatility clustering: h_0 ~ N(0, 0.25^2); h_j = 0.9 h_(j-1) + sqrt(1-0.9^2) * 0.25 * eta_j; r = profile * e^f * e^(h - 0.25^2) * eps, eps ~ t6 (unit variance)
  b  jumps: r = profile * e^f * (0.96194 * eps + J), eps ~ t10 (unit variance), per bar and stock J = +-U(4,8) with probability 0.002
  c  period-specific tails: eps ~ t4 in open and close slots, t8 in middle slots (unit variance)
  d  stock-specific tails: eps ~ t3, t5, t8 for stock 1, 2, 3 (unit variance)
  e  heavy-tailed day factor: f ~ N(0, 0.25355^2) w.p. 0.95, N(0, 0.76064^2) w.p. 0.05; eps ~ t8 (unit variance)
  f  Laplace shocks: eps ~ Laplace(scale 1/sqrt(2)) (unit variance)
Common: 3 stocks, shape E (market specific), day factor f ~ N(0, 0.3^2) independent across stocks unless stated (a, b, c, d, f), H0 true by construction.
`profile` is the frozen M4b profile (equal RMS per period over the used slots), supplied by the caller.
"""
from __future__ import annotations

import math

import numpy as np

from ..calendars import expected_slots
from ..eda.masks import assign_period
from .dependence import day_factors
from .h1_calibration_v11 import (E_LARGE_SD, E_MIX_WEIGHT, E_SMALL_SD, JUMP_HIGH, JUMP_LOW, JUMP_P, PHI_A, SHOCK_SCALE_B, SIGMA_A, t_unit_scale)

PROCESSES = ["a_intraday_volatility_clustering", "b_jumps", "c_period_specific_tails", "d_stock_specific_tails", "e_heavy_tailed_day_factor", "f_laplace_shocks"]
DAY_SD = 0.3


def _t(df: float, size, rng: np.random.Generator) -> np.ndarray:
    """Student-t(df) draws scaled to unit variance."""
    return rng.standard_t(df, size) * t_unit_scale(df)


def slot_periods(market) -> np.ndarray:
    """Period name ('open', 'middle', 'close') of every slot of the session (same assignment as the M4b generator)."""
    return assign_period(expected_slots(market, "2026-08-03"), market).to_numpy()


def alt_components(process: str, market, n_stocks: int, n_days: int, rng: np.random.Generator) -> dict:
    """The random ingredients of one alternative process: day factor f (stocks, days), shocks eps (stocks, days, slots), and where used the
    log-volatility h and the jump term J. Exposed separately so each ingredient can be tested; `simulate_alt_returns` only combines them."""
    n = market.bars_per_day
    shape = (n_stocks, n_days, n)
    if process == "e_heavy_tailed_day_factor":                                              # day factor: scale mixture, independent across stocks and days
        big = rng.random((n_stocks, n_days)) < E_MIX_WEIGHT
        f = np.where(big, E_LARGE_SD, E_SMALL_SD) * rng.standard_normal((n_stocks, n_days))
    else:
        f = day_factors(n_days, n_stocks, DAY_SD, 0.0, 0.0, rng)
    out = {"f": f, "h": None, "jump": None}
    if process == "a_intraday_volatility_clustering":
        eta = rng.standard_normal(shape)
        h = np.empty(shape)
        h[:, :, 0] = SIGMA_A * rng.standard_normal((n_stocks, n_days))                      # stationary start
        for j in range(1, n):
            h[:, :, j] = PHI_A * h[:, :, j - 1] + math.sqrt(1 - PHI_A ** 2) * SIGMA_A * eta[:, :, j]
        out.update(h=h, eps=_t(6, shape, rng))
    elif process == "b_jumps":
        out["jump"] = np.where(rng.random(shape) < JUMP_P, rng.choice([-1.0, 1.0], shape) * rng.uniform(JUMP_LOW, JUMP_HIGH, shape), 0.0)
        out["eps"] = _t(10, shape, rng)
    elif process == "c_period_specific_tails":
        per = slot_periods(market)
        out["eps"] = np.where((per == "middle")[None, None, :], _t(8, shape, rng), _t(4, shape, rng))
    elif process == "d_stock_specific_tails":
        out["eps"] = np.stack([_t(df, shape[1:], rng) for df in (3, 5, 8)[:n_stocks]])
    elif process == "e_heavy_tailed_day_factor":
        out["eps"] = _t(8, shape, rng)
    elif process == "f_laplace_shocks":
        out["eps"] = rng.laplace(0.0, 1 / math.sqrt(2), shape)
    else:
        raise KeyError(process)
    return out


def simulate_alt_returns(process: str, market, n_stocks: int, n_days: int, rng: np.random.Generator, profile: np.ndarray) -> np.ndarray:
    """SIGNED returns (stocks, days, slots) of one alternative process under H0 (profile * e^f * [process-specific factor] * shock)."""
    c = alt_components(process, market, n_stocks, n_days, rng)
    base = np.asarray(profile)[None, None, :] * np.exp(c["f"])[:, :, None]
    if process == "a_intraday_volatility_clustering":
        return base * np.exp(c["h"] - SIGMA_A ** 2) * c["eps"]
    if process == "b_jumps":
        return base * (SHOCK_SCALE_B * c["eps"] + c["jump"])
    return base * c["eps"]


def simulate_alt_returns_sq(process: str, market, n_stocks: int, n_days: int, rng: np.random.Generator, profile: np.ndarray) -> np.ndarray:
    """Squared returns (stocks, days, slots) of one alternative process (what the H1 market matrix needs)."""
    r = simulate_alt_returns(process, market, n_stocks, n_days, rng, profile)
    return r * r
