"""SYNTHETIC cross-stock and across-day dependence for calibration experiments.   ALL DATA SIMULATED.

Earlier simulations drew every stock independently and every day independently. Real stocks in one
market move together, and volatility is persistent across days. This module builds a market of
`n_stocks` synthetic stocks with:

  day-level log-volatility   L[s,d] = sd * ( sqrt(share) * F[d] + sqrt(1-share) * E[s,d] )
      F and every E[s] are independent unit-variance AR(1) series with coefficient `phi`.
      So each stock has day-vol sd `sd` and lag-1 autocorrelation `phi`; two stocks have correlation `share`.
  return shocks              Gaussian part  sqrt(c) * Z[d,slot] + sqrt(1-c) * own,  then Student-t mixing
      so each stock's returns keep t(df) marginals and two stocks have (Gaussian-core) correlation `c`.

What is and is not claimed: these are modelling devices. Parameter values are either estimated
descriptively from the cleaned sample (see scripts/milestone4/describe_next_round.py; imprecise with
~59 days) or are illustrative stress values. The t-mixing gives no tail dependence beyond what the
shared Gaussian core and the shared day factor imply.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..calendars import Market, expected_slots
from ..clean import clean
from ..eda.masks import assign_period, build_bar_table
from .nulls import simulate_raw


def ar1_unit(n_days: int, phi: float, rng: np.random.Generator, size: int | None = None) -> np.ndarray:
    """Stationary unit-variance AR(1) series (rows = independent series)."""
    k = 1 if size is None else size
    x = np.zeros((k, n_days))
    x[:, 0] = rng.standard_normal(k)
    for d in range(1, n_days):
        x[:, d] = phi * x[:, d - 1] + np.sqrt(1 - phi ** 2) * rng.standard_normal(k)
    return x[0] if size is None else x


def core_corr_for_pearson(rho: float, df: float) -> float:
    """Gaussian-core correlation that yields Pearson correlation `rho` between two t(df) returns that share
    the Gaussian core but have independent chi-square mixing (the mixing shrinks the Pearson correlation by
    E[s]^2 / E[s^2], s = sqrt(df/chi2_df))."""
    from math import exp, lgamma, sqrt
    es = sqrt(df / 2) * exp(lgamma((df - 1) / 2) - lgamma(df / 2))
    return rho / (es ** 2 / (df / (df - 2)))


def day_factors(n_days: int, n_stocks: int, sd: float, share: float, phi: float,
                rng: np.random.Generator) -> np.ndarray:
    """(n_stocks, n_days) day log-volatility factors with marginal sd `sd`, lag-1 autocorrelation `phi`,
    cross-stock correlation `share`."""
    F = ar1_unit(n_days, phi, rng)
    E = ar1_unit(n_days, phi, rng, size=n_stocks)
    return sd * (np.sqrt(share) * F[None, :] + np.sqrt(1 - share) * E)


def simulate_market_tables(market: Market, n_stocks: int, n_days: int, rng: np.random.Generator, *,
                           day_vol_sd: float = 0.3, day_share: float = 0.0, day_phi: float = 0.0,
                           ret_corr: float = 0.0, nse_feed_quirks: bool = False, **kw) -> list[pd.DataFrame]:
    """Bar tables for `n_stocks` dependent synthetic stocks pushed through the real clean()/build_bar_table()."""
    n = market.bars_per_day
    F = day_factors(n_days, n_stocks, day_vol_sd, day_share, day_phi, rng)
    common = rng.standard_normal((n_days, n)) if ret_corr > 0 else None
    tables = []
    for i in range(n_stocks):
        raw = simulate_raw(market, n_days, rng, day_vol_sd=day_vol_sd, day_factor=F[i], common_z=common,
                           shock_corr=ret_corr, nse_feed_quirks=nse_feed_quirks, **kw)
        annotated, _ = clean(raw, market)
        tables.append(build_bar_table(annotated, market, f"S{i}"))
    return tables


def shaped_profile(market: Market, open_amp: float, open_tau: float, close_amp: float, close_tau: float,
                   mult: float = 1.0, v: float = 0.0012) -> np.ndarray:
    """Slot volatility profile: decaying open (1 + a*exp(-j/tau) from the session start), rising close
    (mirror image), flat middle. Each period is rescaled to the SAME RMS over the slots H1 uses (so the
    RMS null is true), then open and close are multiplied by `mult` (mult=1 for nulls)."""
    n = market.bars_per_day
    periods = assign_period(expected_slots(market, "2026-08-03"), market).to_numpy()
    prof = np.ones(n)
    for name, amp, tau in (("open", open_amp, open_tau), ("close", close_amp, close_tau)):
        idx = np.where(periods == name)[0]
        j = np.arange(len(idx))
        prof[idx] = 1 + amp * np.exp(-(j if name == "open" else j[::-1]) / tau)
    for name in ("open", "middle", "close"):
        u = np.where(periods == name)[0]
        u = u[u > 0]                                      # the session's first candle has no close-to-close return
        prof[u] = prof[u] / np.sqrt(np.mean(prof[u] ** 2))
        if name in ("open", "close"):
            prof[u] = prof[u] * mult
    prof[0] = prof[1]
    return prof * v
