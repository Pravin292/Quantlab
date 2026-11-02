"""SIMULATED market data for testing and calibrating the research procedures.

Everything produced here is synthetic. It is used ONLY to check that our
statistical procedures behave as designed (correct false-positive rate under a
known null; ability to detect an effect of known size). It is never presented
as market data and never mixed with the real samples.

The simulator reproduces the structure of the real pipeline end to end: it
creates raw 5-minute bars on the real exchange calendar (time zones, 75/78
slots), then runs them through `clean()` and `build_bar_table()`, so the
research code sees exactly the same table layout as for real data.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..calendars import Market, expected_slots
from ..clean import clean
from ..eda.masks import PERIODS, assign_period, build_bar_table
from .h2_volume import K_DEFAULT, L_DEFAULT, MIN_VALID, THR_DEFAULT
from .panel import past_baseline


def trading_dates(n_days: int, start: str = "2026-08-03") -> list:
    return list(pd.bdate_range(start, periods=n_days).date)


def _profile(n: int, edge_boost: float) -> np.ndarray:
    """U-shaped profile over the session: 1 in the middle, 1+edge_boost at both ends."""
    j = np.arange(n)
    return 1 + edge_boost * (np.exp(-j / 6.0) + np.exp(-(n - 1 - j) / 6.0))


def simulate_raw(market: Market, n_days: int, rng: np.random.Generator, *,
                 rho: float = 0.0, df: float = 4.0, base_vol: float = 0.0012,
                 day_vol_sd: float = 0.25, vol_edge_boost: float = 0.0,
                 period_mult: dict | None = None,
                 volume_day_loading: float = 0.0, volume_edge_boost: float = 1.0,
                 slot_vol: np.ndarray | None = None,
                 intraday_regime_sd: float = 0.0, intraday_regime_phi: float = 0.97,
                 volume_intraday_loading: float = 0.0,
                 fwd_vol_mult: float = 1.0, continuation: float = 0.0,
                 k: int = K_DEFAULT, L: int = L_DEFAULT, thr: float = THR_DEFAULT,
                 missing_prob: float = 0.0, nse_feed_quirks: bool = False,
                 start: str = "2026-08-03",
                 day_factor: np.ndarray | None = None,
                 common_z: np.ndarray | None = None, shock_corr: float = 0.0) -> pd.DataFrame:
    """Synthetic raw OHLCV bars (tz-aware index) for n_days.

    rho              within-day AR(1) coefficient of standardised returns
    period_mult      e.g. {"open": 1.8, "close": 1.3} multiplies volatility by period
    volume_day_loading  how strongly volume shares the day's volatility factor
    slot_vol         optional explicit per-slot volatility profile (overrides base_vol/boost/period_mult)
    intraday_regime_sd/phi  a slowly moving volatility regime INSIDE the day (AR(1) over the slots)
    volume_intraday_loading how strongly volume shares that intraday regime
    day_factor       optional (n_days,) array that REPLACES the independently drawn day factor (used to
                     build cross-stock / across-day dependence; see dependence.py). Default None = unchanged.
    common_z, shock_corr  optional (n_days, n) Gaussian shocks shared by all stocks and their weight:
                     the Gaussian part of each stock's shock is sqrt(c)*common_z + sqrt(1-c)*own, then divided
                     by an independent chi-square mixing variable so each stock's marginal stays Student-t(df).
                     Default None = unchanged (identical random draws as before).
    fwd_vol_mult     volatility multiplier applied to the k bars after a volume
                     event (a TRUE forward-volatility effect of known size)
    continuation     drift (in units of volatility) added after an event, in the
                     direction of the event candle (a TRUE continuation effect)
    """
    n = market.bars_per_day
    dates = trading_dates(n_days, start)
    explicit_slot_vol = slot_vol
    slot_vol = base_vol * _profile(n, vol_edge_boost)
    if period_mult:
        idx0 = expected_slots(market, dates[0])
        periods = assign_period(idx0, market).to_numpy()
        for name, mult in period_mult.items():
            slot_vol = np.where(periods == name, slot_vol * mult, slot_vol)
    if explicit_slot_vol is not None:
        slot_vol = np.asarray(explicit_slot_vol, float)
    f = rng.normal(0, day_vol_sd, n_days)                           # day-level volatility factor
    if day_factor is not None:
        f = np.asarray(day_factor, float)
    g = np.zeros((n_days, n))                                       # intraday volatility regime
    if intraday_regime_sd > 0:
        g[:, 0] = rng.normal(0, intraday_regime_sd, n_days)
        for s_ in range(1, n):
            g[:, s_] = (intraday_regime_phi * g[:, s_ - 1]
                        + np.sqrt(1 - intraday_regime_phi ** 2) * intraday_regime_sd * rng.normal(size=n_days))
    vslot = 1000.0 * _profile(n, volume_edge_boost)
    V = vslot[None, :] * np.exp(volume_day_loading * f[:, None] + volume_intraday_loading * g
                                + 0.5 * rng.normal(size=(n_days, n)))
    base = past_baseline(V, L, MIN_VALID)
    with np.errstate(invalid="ignore", divide="ignore"):
        event = np.nan_to_num(V / base, nan=0.0) >= thr

    scale = np.sqrt((df - 2) / df)
    O = np.zeros((n_days, n)); C = np.zeros((n_days, n))
    for d in range(n_days):
        if common_z is None:
            eps = rng.standard_t(df, n) * scale
        else:
            zg = np.sqrt(shock_corr) * common_z[d] + np.sqrt(1 - shock_corr) * rng.standard_normal(n)
            eps = zg / np.sqrt(rng.chisquare(df, n) / df) * scale
        z_prev, prev_close = 0.0, 100.0
        r = np.zeros(n)
        boost = np.ones(n)
        drift = np.zeros(n)
        for s in range(n):
            z = rho * z_prev + np.sqrt(1 - rho ** 2) * eps[s]
            vol_s = slot_vol[s] * np.exp(f[d] + g[d, s]) * boost[s]
            r[s] = vol_s * z + drift[s] * vol_s
            z_prev = z
            if event[d, s]:                                         # effects start AFTER the event candle
                hi = min(n, s + 1 + k)
                boost[s + 1:hi] *= fwd_vol_mult
                drift[s + 1:hi] += continuation * np.sign(r[s])
            gap, intra = 0.3 * r[s], 0.7 * r[s]
            O[d, s] = prev_close * np.exp(gap)
            C[d, s] = O[d, s] * np.exp(intra)
            prev_close = C[d, s]
    frames = []
    for d, day in enumerate(dates):
        idx = expected_slots(market, day)
        hi_p = np.maximum(O[d], C[d]) * 1.0002
        lo_p = np.minimum(O[d], C[d]) * 0.9998
        frames.append(pd.DataFrame({"open": O[d], "high": hi_p, "low": lo_p, "close": C[d],
                                    "volume": np.round(V[d])}, index=idx))
    raw = pd.concat(frames)
    if missing_prob:
        gone = rng.random(len(raw)) < missing_prob
        raw.loc[gone, :] = np.nan
    if nse_feed_quirks and market.name == "NSE":
        pos = np.tile(np.arange(n), n_days)
        raw.loc[pos == n - 2, :] = np.nan                           # 15:20 always empty
        raw.loc[(pos == n - 1) & (rng.random(len(raw)) < 0.78), :] = np.nan   # 15:25 mostly empty
        raw.loc[pos == 0, "volume"] = 0.0                           # opening-bar volume missing
    raw.index.name = "bar_start"
    return raw


def simulate_table(market: Market, symbol: str, n_days: int, rng: np.random.Generator, **kw) -> pd.DataFrame:
    """Synthetic data pushed through the REAL clean() and build_bar_table()."""
    raw = simulate_raw(market, n_days, rng, **kw)
    annotated, _ = clean(raw, market)
    return build_bar_table(annotated, market, symbol)
