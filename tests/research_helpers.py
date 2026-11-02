"""Small hand-built bar tables for the research tests."""
import numpy as np
import pandas as pd

from quantlab.calendars import expected_slots
from quantlab.clean import clean
from quantlab.eda.masks import build_bar_table
from quantlab.research.nulls import trading_dates


def bars_table(market, symbol="T", n_days=12, volume=100.0, closes=None, opens=None,
               volumes=None, nan_rows=(), seed=0):
    """Table of n_days clean days. closes/opens/volumes: optional (n_days x n_slots)
    arrays; otherwise a gentle deterministic random walk and constant volume."""
    rng = np.random.default_rng(seed)
    n = market.bars_per_day
    if closes is None:
        closes = 100 * np.exp(np.cumsum(rng.normal(0, 0.0005, (n_days, n)), axis=1))
    closes = np.asarray(closes, float)
    if opens is None:
        opens = np.concatenate([np.full((n_days, 1), 100.0), closes[:, :-1]], axis=1)
    opens = np.asarray(opens, float)
    vols = np.full((n_days, n), volume) if volumes is None else np.asarray(volumes, float)
    frames = []
    for d, day in enumerate(trading_dates(n_days)):
        idx = expected_slots(market, day)
        frames.append(pd.DataFrame({
            "open": opens[d], "high": np.maximum(opens[d], closes[d]) + 0.01,
            "low": np.minimum(opens[d], closes[d]) - 0.01, "close": closes[d],
            "volume": vols[d]}, index=idx))
    raw = pd.concat(frames)
    raw.index.name = "bar_start"
    for r in nan_rows:                               # (day, slot) pairs made empty
        raw.iloc[r[0] * n + r[1], :] = np.nan
    annotated, _ = clean(raw, market)
    return build_bar_table(annotated, market, symbol)
