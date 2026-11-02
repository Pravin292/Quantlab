"""Bridge used to VALIDATE the fast generator (direct_sim.py) against the bar-level pipeline.   ALL SIMULATED.

`returns_to_table` turns a (days x slots) array of returns into raw 5-minute OHLCV bars exactly as
`nulls.simulate_raw` constructs them (open = previous close * exp(0.3 r), close = open * exp(0.7 r), previous
close reset to 100 each day, +/-0.02% high/low, NSE feed quirks), then pushes them through the REAL clean()
and build_bar_table(). Feeding the SAME returns to both routes lets us compare them exactly, which identical
seeds alone cannot do (the two generators consume random numbers differently).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..calendars import Market, expected_slots
from ..clean import clean
from ..eda.masks import build_bar_table
from .nulls import trading_dates


def returns_to_table(market: Market, r: np.ndarray, symbol: str, rng: np.random.Generator,
                     nse_feed_quirks: bool = False) -> pd.DataFrame:
    n_days, n = r.shape
    frames = []
    for d, day in enumerate(trading_dates(n_days)):
        O, C, prev = np.zeros(n), np.zeros(n), 100.0
        for s in range(n):
            O[s] = prev * np.exp(0.3 * r[d, s])
            C[s] = O[s] * np.exp(0.7 * r[d, s])
            prev = C[s]
        frames.append(pd.DataFrame({"open": O, "high": np.maximum(O, C) * 1.0002, "low": np.minimum(O, C) * 0.9998,
                                    "close": C, "volume": np.full(n, 1000.0)}, index=expected_slots(market, day)))
    raw = pd.concat(frames)
    if nse_feed_quirks and market.name == "NSE":
        pos = np.tile(np.arange(n), n_days)
        raw.loc[pos == n - 2, :] = np.nan
        raw.loc[(pos == n - 1) & (rng.random(len(raw)) < 0.78), :] = np.nan
        raw.loc[pos == 0, "volume"] = 0.0
    raw.index.name = "bar_start"
    annotated, _ = clean(raw, market)
    return build_bar_table(annotated, market, symbol)
