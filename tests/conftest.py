"""Shared helpers: tiny hand-made data, so tests need no internet and no files."""
import json

import numpy as np
import pandas as pd
import pytest

from quantlab.calendars import NSE, US, expected_slots

NSE_DAY = "2026-10-12"   # a Monday
US_DAY = "2026-10-13"    # a Tuesday


def make_day(market, day, price=100.0, volume=1000.0) -> pd.DataFrame:
    """One perfectly clean trading day: every expected bar, valid prices."""
    idx = expected_slots(market, day)
    n = len(idx)
    close = price + np.arange(n) * 0.01
    df = pd.DataFrame({"open": close - 0.005, "high": close + 0.05,
                       "low": close - 0.05, "close": close,
                       "volume": np.full(n, volume)}, index=idx)
    df.index.name = "bar_start"
    return df


@pytest.fixture(params=[(NSE, NSE_DAY), (US, US_DAY)], ids=["NSE", "US"])
def market_day(request):
    return request.param


@pytest.fixture
def clean_frame(market_day):
    market, day = market_day
    return market, make_day(market, day)


def yahoo_json(timestamps, quote, tz="Asia/Kolkata") -> bytes:
    """Build a minimal Yahoo-style JSON payload."""
    return json.dumps({"chart": {"result": [{
        "meta": {"symbol": "TEST", "exchangeTimezoneName": tz},
        "timestamp": timestamps,
        "indicators": {"quote": [quote]}}], "error": None}}).encode()
