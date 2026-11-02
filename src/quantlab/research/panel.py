"""Reshaping helpers: from the EDA bar table to day x slot matrices.

A matrix has one row per trading day and one column per 5-minute slot of the
session (75 for NSE, 78 for US). Because columns are fixed grid positions,
shifting along the columns can never reach into another day.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..calendars import BAR_MINUTES, market_for_symbol
from ..eda.masks import build_bar_table

WIDTH = {"NSE": 75, "US": 78}


def load_tables(clean_dir: Path) -> dict[str, pd.DataFrame]:
    """Read the cleaned Parquet files (read-only) into EDA bar tables."""
    out = {}
    for p in sorted(Path(clean_dir).glob("*.parquet")):
        symbol = p.stem.partition("_")[0]
        market = market_for_symbol(symbol)
        table = build_bar_table(pd.read_parquet(p), market, symbol)
        table.attrs["raw_sha256"] = pd.read_parquet(p).attrs.get("raw_sha256")
        out[symbol] = table
    return out


def to_matrix(table: pd.DataFrame, values, market_name: str):
    """Return (matrix[days, slots], dates). `values` is a column name or a Series
    aligned with `table`. Bars off the 5-minute grid (e.g. a live, unfinished
    bar stamped 12:02) are left out."""
    s = table[values] if isinstance(values, str) else values
    mins = table["mins_since_open"].to_numpy()
    slot = mins // BAR_MINUTES
    on_grid = (mins % BAR_MINUTES == 0) & (slot >= 0) & (slot < WIDTH[market_name])
    dates = np.array(sorted(set(table["date"])))
    day_pos = pd.Series(np.arange(len(dates)), index=dates)
    di = day_pos.loc[table["date"]].to_numpy()
    M = np.full((len(dates), WIDTH[market_name]), np.nan)
    vals = pd.to_numeric(s, errors="coerce").to_numpy(dtype=float)
    M[di[on_grid], slot[on_grid]] = vals[on_grid]
    return M, dates


def past_baseline(M: np.ndarray, L: int, min_count: int, neighbors: int = 1,
                  stat=np.nanmedian) -> np.ndarray:
    """For each (day i, slot s): a statistic of the same stock's values on the
    previous L trading days in slots s-neighbors..s+neighbors.

    ONLY earlier days are used (rows i-L .. i-1), so nothing from day i or
    later can leak in. NaN when fewer than `min_count` valid values."""
    nd, ns = M.shape
    out = np.full_like(M, np.nan)
    for i in range(L, nd):
        window = M[i - L:i]
        for s in range(ns):
            block = window[:, max(0, s - neighbors):s + neighbors + 1]
            vals = block[~np.isnan(block)]
            if vals.size >= min_count:
                out[i, s] = stat(vals)
    return out
