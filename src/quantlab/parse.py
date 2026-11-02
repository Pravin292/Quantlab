"""Turn a raw Yahoo JSON snapshot into a table. NO cleaning happens here:
empty (NaN) bars, zero volumes and odd timestamps are all kept as received."""
from __future__ import annotations

import json

import pandas as pd

COLUMNS = ["open", "high", "low", "close", "volume"]


def parse_yahoo_json(raw: bytes | str) -> tuple[pd.DataFrame, dict]:
    """Return (bars, meta). `bars` is indexed by bar START time, in the
    exchange's own time zone (taken from Yahoo's metadata)."""
    payload = json.loads(raw)
    chart = payload.get("chart", {})
    if chart.get("error"):
        raise ValueError(f"Yahoo returned an error: {chart['error']}")
    result = chart.get("result")
    if not result:
        raise ValueError("Yahoo response has no result")
    result = result[0]
    if "timestamp" not in result:
        raise ValueError("Yahoo response has no timestamps (no data)")

    meta = result["meta"]
    tz = meta["exchangeTimezoneName"]
    quote = result["indicators"]["quote"][0]

    # Epoch seconds are in UTC; convert to the exchange's local time.
    index = pd.to_datetime(result["timestamp"], unit="s", utc=True).tz_convert(tz)
    # Missing values arrive as null -> NaN; we deliberately keep them.
    bars = pd.DataFrame({c: pd.array(quote[c], dtype="float64") for c in COLUMNS},
                        index=index)
    bars.index.name = "bar_start"
    return bars, meta
