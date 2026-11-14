"""Offline tests for the fresh-US runner (docs/33 section 8): conversion and the frozen scheduled-session list. No network, no keys, no real data."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))
import p2_us                                                                # noqa: E402


def test_scheduled_sessions_exclude_weekends_and_holidays_and_end_before_the_tested_sample():
    s = p2_us.scheduled_sessions()
    assert s[0] == "2026-04-13" and s[-1] == "2026-08-05" and s[-1] < "2026-08-06"
    assert not {"2026-05-25", "2026-06-19", "2026-07-03"} & set(s)
    assert all(pd.Timestamp(d).weekday() < 5 for d in s) and len(s) >= 59 + 10


def test_alpaca_conversion_gives_exchange_time_bar_start_index():
    payload = {"bars": {"AAPL": [{"t": "2026-04-13T13:30:00Z", "o": 1, "h": 2, "l": 0.5, "c": 1.5, "v": 100},
                                  {"t": "2026-04-13T13:35:00Z", "o": 1.5, "h": 2, "l": 1, "c": 1.8, "v": 50}]}}
    b = p2_us.alpaca_json_to_bars(payload, "AAPL")
    assert str(b.index[0]) == "2026-04-13 09:30:00-04:00" and list(b.columns) == ["open", "high", "low", "close", "volume"]
    assert b.close.tolist() == [1.5, 1.8]
