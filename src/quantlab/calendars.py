"""Market definitions: where and when each exchange trades.

Bar timestamps in QuantLab always mean the bar START time. A bar stamped
09:15 covers 09:15:00 up to (but not including) 09:20:00.

Limitation: we do NOT have an official holiday or early-close calendar yet.
A holiday simply has no data (it is not reported as "missing"), and an
early-close day will show its later slots as missing.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

BAR_MINUTES = 5


@dataclass(frozen=True)
class Market:
    name: str              # "NSE" or "US"
    tz: str                # exchange time zone (IANA name)
    open_minutes: int      # session open, minutes after local midnight
    close_minutes: int     # session close, minutes after local midnight

    @property
    def bars_per_day(self) -> int:
        return (self.close_minutes - self.open_minutes) // BAR_MINUTES


NSE = Market("NSE", "Asia/Kolkata", 9 * 60 + 15, 15 * 60 + 30)   # 75 bars
US = Market("US", "America/New_York", 9 * 60 + 30, 16 * 60)      # 78 bars


def market_for_symbol(symbol: str) -> Market:
    """Yahoo uses the '.NS' suffix for NSE stocks; everything else here is US."""
    return NSE if symbol.upper().endswith(".NS") else US


def expected_slots(market: Market, day) -> pd.DatetimeIndex:
    """All bar start times we expect on one local calendar day."""
    midnight = pd.Timestamp(day).normalize().tz_localize(None)
    start = midnight + pd.Timedelta(minutes=market.open_minutes)
    end = midnight + pd.Timedelta(minutes=market.close_minutes)
    naive = pd.date_range(start, end, freq=f"{BAR_MINUTES}min", inclusive="left")
    # Build the wall-clock times first, then attach the time zone.
    return naive.tz_localize(market.tz)
