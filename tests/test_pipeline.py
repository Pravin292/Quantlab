"""Tests for parse, ingest (raw preservation) and clean."""
import hashlib
import os
import stat
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from quantlab.calendars import NSE, US, market_for_symbol
from quantlab.clean import clean, drop_exact_duplicates, write_clean
from quantlab.ingest import save_raw_snapshot
from quantlab.parse import parse_yahoo_json

from conftest import make_day, yahoo_json


# ---------------- parse ----------------
def test_parse_converts_to_exchange_timezone_and_keeps_nan():
    # 2026-10-12 03:45:00 UTC == 09:15 IST
    ts = [1791776700, 1791777000]
    raw = yahoo_json(ts, {"open": [1, None], "high": [2, None], "low": [1, None],
                          "close": [2, None], "volume": [0, None]})
    df, meta = parse_yahoo_json(raw)
    assert str(df.index.tz) == "Asia/Kolkata"
    assert df.index[0].strftime("%H:%M") == "09:15"
    assert df.iloc[1].isna().all()               # NaN kept, not dropped or filled
    assert len(df) == 2 and meta["symbol"] == "TEST"


def test_parse_us_timezone():
    # 2026-10-13 13:30 UTC == 09:30 EDT
    raw = yahoo_json([1791898200], {"open": [1], "high": [2], "low": [1],
                                    "close": [2], "volume": [5]},
                     tz="America/New_York")
    df, _ = parse_yahoo_json(raw)
    assert df.index[0].strftime("%H:%M") == "09:30"


def test_parse_error_payload_raises():
    bad = b'{"chart": {"result": null, "error": {"code": "X"}}}'
    with pytest.raises(ValueError):
        parse_yahoo_json(bad)


def test_market_for_symbol():
    assert market_for_symbol("TCS.NS") is NSE
    assert market_for_symbol("AAPL") is US


# ---------------- ingest: raw preservation ----------------
def _snap(tmp_path, raw, when):
    return save_raw_snapshot(raw, source="yahoo", symbol="TCS.NS", interval="5m",
                             rng="60d", raw_dir=tmp_path / "raw",
                             manifest_path=tmp_path / "manifest.csv", now=when)


def test_snapshot_is_exact_bytes_readonly_and_in_manifest(tmp_path):
    raw = b'{"hello": "world"}'
    when = datetime(2026, 10, 30, 5, 0, tzinfo=timezone.utc)
    path = _snap(tmp_path, raw, when)
    assert path.read_bytes() == raw
    assert (path.stat().st_mode & 0o222) == 0        # no write permission for anyone
    sha = hashlib.sha256(raw).hexdigest()
    assert sha[:12] in path.name and "20261030T050000Z" in path.name
    manifest = pd.read_csv(tmp_path / "manifest.csv")
    assert manifest.loc[0, "sha256"] == sha and len(manifest) == 1


def test_snapshot_never_overwrites(tmp_path):
    when = datetime(2026, 10, 30, 5, 0, tzinfo=timezone.utc)
    _snap(tmp_path, b"abc", when)
    with pytest.raises(FileExistsError):
        _snap(tmp_path, b"abc", when)            # same bytes, same second


def test_two_pulls_make_two_files(tmp_path):
    p1 = _snap(tmp_path, b"abc", datetime(2026, 10, 30, 5, 0, tzinfo=timezone.utc))
    p2 = _snap(tmp_path, b"abd", datetime(2026, 10, 30, 6, 0, tzinfo=timezone.utc))
    assert p1 != p2 and p1.exists() and p2.exists()
    assert len(pd.read_csv(tmp_path / "manifest.csv")) == 2


# ---------------- clean ----------------
def test_clean_does_not_modify_input_or_drop_suspicious_rows(market_day):
    market, day = market_day
    df = make_day(market, day)
    df.iloc[3, :] = np.nan
    df.iloc[8, df.columns.get_loc("volume")] = 0
    before = df.copy()
    out, _ = clean(df, market)
    pd.testing.assert_frame_equal(df, before)    # input untouched
    assert len(out) == len(df)                   # nothing deleted
    assert out.iloc[3][["open", "close"]].isna().all()   # nothing filled


def test_clean_labels_usable_and_volume_reliable():
    df = make_day(NSE, "2026-10-12")
    df.iloc[0, df.columns.get_loc("volume")] = 0     # NSE opening quirk
    df.iloc[-1, :] = np.nan                          # empty closing bar
    out, _ = clean(df, NSE)
    first, last, mid = out.iloc[0], out.iloc[-1], out.iloc[10]
    assert first.usable and not first.volume_reliable    # price ok, volume not
    assert not last.usable and not last.volume_reliable
    assert mid.usable and mid.volume_reliable


def test_clean_marks_us_1600_bar_unusable_but_keeps_it():
    df = make_day(US, "2026-10-13")
    extra = df.iloc[[-1]].copy(); extra.index = extra.index + pd.Timedelta(minutes=5)
    out, _ = clean(pd.concat([df, extra]), US)
    assert len(out) == 79 and not out.iloc[-1].usable


def test_exact_duplicates_removed_conflicting_duplicates_raise():
    df = make_day(NSE, "2026-10-12")
    same = pd.concat([df, df.iloc[[2]]])
    assert len(drop_exact_duplicates(same)) == len(df)

    conflict = df.iloc[[2]].copy(); conflict["close"] += 1
    with pytest.raises(ValueError, match="conflicting"):
        drop_exact_duplicates(pd.concat([df, conflict]))


def test_clean_sorts_by_time():
    df = make_day(US, "2026-10-13").iloc[::-1]
    out, _ = clean(df, US)
    assert out.index.is_monotonic_increasing


def test_write_clean_roundtrip_and_no_overwrite(tmp_path):
    out, _ = clean(make_day(NSE, "2026-10-12"), NSE)
    path = write_clean(out, tmp_path / "x.parquet", raw_sha256="abc")
    back = pd.read_parquet(path)
    assert len(back) == 75 and str(back.index.tz) == "Asia/Kolkata"
    with pytest.raises(FileExistsError):
        write_clean(out, path, raw_sha256="abc")
