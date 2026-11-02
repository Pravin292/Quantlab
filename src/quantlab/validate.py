"""Validation: look at the data and REPORT problems. Nothing is changed here.

Each rule produces a True/False column ("flag") with one value per input row.
Rules are documented in docs/05_validation_rules.md.

Flag columns
------------
duplicate_timestamp     the same bar start time appears more than once
missing_ohlc            open/high/low/close contains an empty (NaN) value
missing_volume          prices exist but volume is empty
zero_volume             prices exist and volume is exactly 0
invalid_ohlc            impossible prices (high < low, high < open/close,
                        low > open/close, price <= 0, volume < 0)
unexpected_session_bar  bar is outside the trading session or not on the
                        5-minute grid (e.g. a 16:00 bar in the US)
forming_bar             bar had not finished at `as_of` (only if as_of given)
nse_open_zero_volume    NSE only: 09:15 bar with real prices but volume 0
nse_close_window_empty  NSE only: empty bar at 15:15 or later

The last two are KNOWN QUIRKS of the Yahoo NSE feed (docs/04). They are
flagged so later code can avoid them; they are never filled or deleted.

Missing candles (slots that do not exist as rows at all) are reported
separately in `missing_slots`.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .calendars import BAR_MINUTES, Market, expected_slots

FLAG_COLUMNS = [
    "duplicate_timestamp", "missing_ohlc", "missing_volume", "zero_volume",
    "invalid_ohlc", "unexpected_session_bar", "forming_bar",
    "nse_open_zero_volume", "nse_close_window_empty",
]
PRICE_COLUMNS = ["open", "high", "low", "close"]


@dataclass
class ValidationResult:
    market: Market
    flags: pd.DataFrame           # same rows as the input, one bool column per flag
    missing_slots: pd.DatetimeIndex
    n_rows: int
    n_days: int

    def counts(self) -> dict[str, int]:
        return {c: int(self.flags[c].sum()) for c in FLAG_COLUMNS}

    def to_text(self) -> str:
        lines = [f"Market: {self.market.name}   rows: {self.n_rows}   "
                 f"days: {self.n_days}   expected bars/day: {self.market.bars_per_day}"]
        for name, n in self.counts().items():
            lines.append(f"  {name:<24}{n:>6}")
        lines.append(f"  {'missing_slots':<24}{len(self.missing_slots):>6}")
        return "\n".join(lines)


def check_timezone(index: pd.Index, market: Market) -> None:
    """Fail loudly if timestamps are naive or in the wrong zone. Mixing
    zones is a classic way to silently corrupt intraday research."""
    if not isinstance(index, pd.DatetimeIndex):
        raise ValueError("index must be a DatetimeIndex")
    if index.tz is None:
        raise ValueError("timestamps are timezone-naive; expected "
                         f"{market.tz}")
    if str(index.tz) != market.tz:
        raise ValueError(f"timestamps are in {index.tz}, expected {market.tz}")


def validate(df: pd.DataFrame, market: Market,
             as_of: pd.Timestamp | None = None) -> ValidationResult:
    """Run every rule on `df` (bars indexed by bar start time)."""
    check_timezone(df.index, market)
    if as_of is not None and as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")

    idx = df.index
    flags = pd.DataFrame(index=idx)

    flags["duplicate_timestamp"] = idx.duplicated(keep=False)

    prices_missing = df[PRICE_COLUMNS].isna().any(axis=1)
    flags["missing_ohlc"] = prices_missing
    flags["missing_volume"] = df["volume"].isna() & ~prices_missing
    flags["zero_volume"] = (df["volume"] == 0) & ~prices_missing

    # Only judge price logic on rows where all four prices exist.
    o, h, low, c = (df[k] for k in PRICE_COLUMNS)
    bad_logic = (h < low) | (h < o) | (h < c) | (low > o) | (low > c)
    non_positive = (df[PRICE_COLUMNS] <= 0).any(axis=1) | (df["volume"] < 0)
    flags["invalid_ohlc"] = (bad_logic | non_positive) & ~prices_missing

    # Minutes since the session opened, in exchange-local wall-clock time.
    minute_of_day = idx.hour * 60 + idx.minute
    since_open = pd.Series(minute_of_day - market.open_minutes, index=idx)
    in_session = (since_open >= 0) & (since_open < market.close_minutes - market.open_minutes)
    on_grid = (since_open % BAR_MINUTES == 0) & (idx.second == 0)
    flags["unexpected_session_bar"] = ~(in_session & on_grid)

    if as_of is not None:
        flags["forming_bar"] = (idx + pd.Timedelta(minutes=BAR_MINUTES)) > as_of
    else:
        flags["forming_bar"] = False

    if market.name == "NSE":
        flags["nse_open_zero_volume"] = (
            (minute_of_day == market.open_minutes) & flags["zero_volume"])
        flags["nse_close_window_empty"] = (
            (minute_of_day >= market.close_minutes - 15) & prices_missing)
    else:
        flags["nse_open_zero_volume"] = False
        flags["nse_close_window_empty"] = False

    flags = flags[FLAG_COLUMNS].astype(bool)
    return ValidationResult(market, flags, find_missing_slots(idx, market, as_of),
                            len(df), len(set(idx.date)))


def find_missing_slots(idx: pd.DatetimeIndex, market: Market,
                       as_of: pd.Timestamp | None = None) -> pd.DatetimeIndex:
    """Expected bar times that have NO row at all, for every day present."""
    missing = []
    for day in sorted(set(idx.date)):
        slots = expected_slots(market, day)
        if as_of is not None:   # don't expect bars that hadn't finished yet
            slots = slots[(slots + pd.Timedelta(minutes=BAR_MINUTES)) <= as_of]
        missing.append(slots.difference(idx))
    if not missing:
        return pd.DatetimeIndex([], tz=market.tz)
    out = missing[0]
    for m in missing[1:]:
        out = out.append(m)
    return out
