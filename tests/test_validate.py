"""One or more tests per validation rule, run for BOTH NSE and US (via fixtures)."""
import numpy as np
import pandas as pd
import pytest

from quantlab.calendars import NSE, US
from quantlab.validate import validate

from conftest import make_day


def flags_of(df, market, **kw):
    return validate(df, market, **kw)


def test_clean_day_has_no_flags(clean_frame):
    market, df = clean_frame
    res = validate(df, market)
    assert len(df) == market.bars_per_day            # 75 for NSE, 78 for US
    assert sum(res.counts().values()) == 0
    assert len(res.missing_slots) == 0


# ---- missing candles (rows that do not exist at all) ----
def test_missing_candle_is_reported(clean_frame):
    market, df = clean_frame
    removed = df.index[10]
    res = validate(df.drop(removed), market)
    assert list(res.missing_slots) == [removed]


def test_missing_candles_checked_per_day(market_day):
    market, day = market_day
    d2 = (pd.Timestamp(day) + pd.Timedelta(days=1)).date()
    df = pd.concat([make_day(market, day), make_day(market, d2)])
    gone = df.index[[3, market.bars_per_day + 5]]
    res = validate(df.drop(gone), market)
    assert list(res.missing_slots) == list(gone)


# ---- empty (NaN) candles ----
def test_nan_prices_flagged(clean_frame):
    market, df = clean_frame
    df.iloc[5, df.columns.get_loc("close")] = np.nan
    assert validate(df, market).counts()["missing_ohlc"] == 1


def test_nan_volume_flagged_separately(clean_frame):
    market, df = clean_frame
    df.iloc[5, df.columns.get_loc("volume")] = np.nan
    c = validate(df, market).counts()
    assert c["missing_volume"] == 1 and c["missing_ohlc"] == 0


# ---- zero volume ----
def test_zero_volume_flagged(clean_frame):
    market, df = clean_frame
    df.iloc[20, df.columns.get_loc("volume")] = 0
    assert validate(df, market).counts()["zero_volume"] == 1


def test_nan_row_is_not_also_zero_volume(clean_frame):
    market, df = clean_frame
    df.iloc[7, :] = np.nan
    c = validate(df, market).counts()
    assert c["missing_ohlc"] == 1 and c["zero_volume"] == 0


# ---- duplicates ----
def test_duplicate_timestamps_flagged(clean_frame):
    market, df = clean_frame
    df = pd.concat([df, df.iloc[[4]]])
    assert validate(df, market).counts()["duplicate_timestamp"] == 2  # both copies


# ---- invalid OHLC ----
@pytest.mark.parametrize("col,value", [
    ("high", 50.0),     # high below open/close
    ("low", 500.0),     # low above open/close
    ("close", -1.0),    # negative price
    ("open", 0.0),      # zero price
    ("volume", -5.0),   # negative volume
])
def test_invalid_ohlc_flagged(clean_frame, col, value):
    market, df = clean_frame
    df.iloc[3, df.columns.get_loc(col)] = value
    assert validate(df, market).counts()["invalid_ohlc"] == 1


def test_high_below_low_flagged(clean_frame):
    market, df = clean_frame
    df.iloc[3, df.columns.get_loc("high")] = df.iloc[3]["low"] - 1
    assert validate(df, market).counts()["invalid_ohlc"] == 1


# ---- timezone handling ----
def test_naive_timestamps_rejected(clean_frame):
    market, df = clean_frame
    df.index = df.index.tz_localize(None)
    with pytest.raises(ValueError, match="naive"):
        validate(df, market)


def test_wrong_timezone_rejected(clean_frame):
    market, df = clean_frame
    df.index = df.index.tz_convert("UTC")
    with pytest.raises(ValueError, match="expected"):
        validate(df, market)


def test_same_instant_in_other_zone_is_a_different_wallclock():
    """US data labelled with the NSE zone would look badly out of session."""
    df = make_day(US, "2026-10-13")
    df.index = df.index.tz_convert("Asia/Kolkata")
    res = validate(df, NSE)
    assert res.counts()["unexpected_session_bar"] > 0


def test_us_daylight_saving_week_keeps_wallclock_slots():
    """After the US clocks change (2026-11-02) 09:30 local is still the first bar."""
    for day in ["2026-10-30", "2026-11-02"]:
        res = validate(make_day(US, day), US)
        assert sum(res.counts().values()) == 0 and len(res.missing_slots) == 0


# ---- unexpected session bars ----
def test_us_1600_bar_is_unexpected():
    df = make_day(US, "2026-10-13")
    extra = df.iloc[[-1]].copy()
    extra.index = extra.index + pd.Timedelta(minutes=5)       # 16:00
    res = validate(pd.concat([df, extra]), US)
    assert res.counts()["unexpected_session_bar"] == 1


def test_premarket_and_offgrid_bars_unexpected(clean_frame):
    market, df = clean_frame
    pre = df.iloc[[0]].copy(); pre.index = pre.index - pd.Timedelta(minutes=5)
    off = df.iloc[[1]].copy(); off.index = off.index + pd.Timedelta(minutes=2)
    res = validate(pd.concat([pre, off, df]).sort_index(), market)
    assert res.counts()["unexpected_session_bar"] == 2


def test_nse_bar_at_1530_is_unexpected():
    df = make_day(NSE, "2026-10-12")
    extra = df.iloc[[-1]].copy(); extra.index = extra.index + pd.Timedelta(minutes=5)
    assert validate(pd.concat([df, extra]), NSE).counts()["unexpected_session_bar"] == 1


# ---- bar still forming ----
def test_forming_bar_flagged_and_not_counted_as_missing():
    df = make_day(NSE, "2026-10-12").iloc[:19]               # 09:15 .. 10:40
    as_of = df.index[-1] + pd.Timedelta(minutes=2)           # last bar unfinished
    res = validate(df, NSE, as_of=as_of)
    assert res.counts()["forming_bar"] == 1
    assert len(res.missing_slots) == 0


# ---- NSE-only known quirks ----
def test_nse_opening_zero_volume_quirk():
    df = make_day(NSE, "2026-10-12")
    df.iloc[0, df.columns.get_loc("volume")] = 0
    c = validate(df, NSE).counts()
    assert c["nse_open_zero_volume"] == 1 and c["zero_volume"] == 1


def test_same_pattern_in_us_is_not_an_nse_quirk():
    df = make_day(US, "2026-10-13")
    df.iloc[0, df.columns.get_loc("volume")] = 0
    c = validate(df, US).counts()
    assert c["nse_open_zero_volume"] == 0 and c["zero_volume"] == 1


def test_nse_closing_window_empty_bars():
    df = make_day(NSE, "2026-10-12")
    df.iloc[-2:, :] = np.nan                                 # 15:20 and 15:25
    c = validate(df, NSE).counts()
    assert c["nse_close_window_empty"] == 2 and c["missing_ohlc"] == 2


def test_empty_midday_bar_is_not_a_closing_quirk():
    df = make_day(NSE, "2026-10-12")
    df.iloc[30, :] = np.nan
    assert validate(df, NSE).counts()["nse_close_window_empty"] == 0
