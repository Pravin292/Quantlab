"""EDA masks, return status and period assignment, on small hand-made data
whose correct answers are known in advance."""
import numpy as np
import pandas as pd
import pytest

from quantlab.calendars import NSE, US, expected_slots
from quantlab.clean import clean
from quantlab.eda.masks import (CLOSING_WINDOW, assign_period, build_bar_table,
                                exclusion_summary)

from conftest import NSE_DAY, US_DAY, make_day


def table(df, market, **kw):
    out, _ = clean(df, market, **kw)
    return build_bar_table(out, market, "TEST")


def set_closes(df, closes):
    """Replace prices by a chosen close series (open = previous close)."""
    df = df.copy()
    df["close"] = closes
    df["open"] = df["close"]
    df["high"] = df["close"] + 0.01
    df["low"] = df["close"] - 0.01
    return df


# ---------------- period assignment ----------------
EXPECTED_COUNTS = {"NSE": {"open": 9, "middle": 54, "close": 9, CLOSING_WINDOW: 3},
                   "US": {"open": 12, "middle": 54, "close": 12}}


def test_every_slot_in_exactly_one_period_with_expected_counts(market_day):
    market, day = market_day
    periods = assign_period(expected_slots(market, day), market)
    assert (periods != "outside_session").all()               # none omitted
    assert periods.value_counts().to_dict() == EXPECTED_COUNTS[market.name]
    assert len(periods) == market.bars_per_day                # none counted twice


@pytest.mark.parametrize("hhmm,expected", [
    ("09:15", "open"), ("09:55", "open"), ("10:00", "middle"),
    ("14:25", "middle"), ("14:30", "close"), ("15:10", "close"),
    ("15:15", CLOSING_WINDOW), ("15:25", CLOSING_WINDOW)])
def test_nse_boundaries(hhmm, expected):
    idx = expected_slots(NSE, NSE_DAY)
    period = assign_period(idx, NSE)
    assert period[idx[[t.strftime("%H:%M") == hhmm for t in idx]][0]] == expected


@pytest.mark.parametrize("hhmm,expected", [
    ("09:30", "open"), ("10:25", "open"), ("10:30", "middle"),
    ("14:55", "middle"), ("15:00", "close"), ("15:55", "close")])
def test_us_boundaries(hhmm, expected):
    idx = expected_slots(US, US_DAY)
    period = assign_period(idx, US)
    assert period[idx[[t.strftime("%H:%M") == hhmm for t in idx]][0]] == expected


def test_bars_outside_the_session_get_outside_label():
    idx = expected_slots(US, US_DAY)
    odd = pd.DatetimeIndex([idx[0] - pd.Timedelta(minutes=5),
                            idx[-1] + pd.Timedelta(minutes=5)])
    assert (assign_period(odd, US) == "outside_session").all()   # 09:25 and 16:00


# ---------------- returns ----------------
def test_return_is_log_close_to_close(clean_frame):
    market, df = clean_frame
    closes = 100 * 1.01 ** np.arange(len(df))
    t = table(set_closes(df, closes), market)
    ok = t[t["status"] == "ok"]["ret"]      # NSE closing-window bars are excluded by design
    assert len(ok) == market.bars_per_day - 1 - (3 if market.name == "NSE" else 0)
    assert ok.round(10).eq(round(np.log(1.01), 10)).all()


def test_first_bar_has_no_close_to_close_return_but_has_open_to_close(clean_frame):
    market, df = clean_frame
    df = df.copy()
    df.iloc[0, df.columns.get_loc("open")] = 100.0
    df.iloc[0, df.columns.get_loc("close")] = 101.0
    df.iloc[0, df.columns.get_loc("high")] = 101.5
    df.iloc[0, df.columns.get_loc("low")] = 99.5
    t = table(df, market)
    assert np.isnan(t["ret"].iloc[0])
    assert t["status"].iloc[0] == "first_bar_of_day"
    assert t["ret_oc"].iloc[0] == pytest.approx(np.log(101 / 100))
    assert t["ret_oc"].iloc[1:].isna().all()           # only the opening candle


def test_no_overnight_return_between_days(market_day):
    market, day = market_day
    d2 = (pd.Timestamp(day) + pd.Timedelta(days=1)).date()
    df = pd.concat([make_day(market, day, price=100), make_day(market, d2, price=150)])
    t = table(df, market)
    day2_first = t[t["date"] == d2].iloc[0]
    assert day2_first["status"] == "first_bar_of_day" and np.isnan(day2_first["ret"])
    assert t["ret"].abs().max() < 0.01                 # no jump of ln(150/100) appears


def test_empty_bar_excludes_itself_and_the_next_return_only(clean_frame):
    market, df = clean_frame
    df = df.copy()
    df.iloc[5, :] = np.nan
    t = table(df, market)
    assert t["status"].iloc[5] == "excluded_missing_ohlc"
    assert t["status"].iloc[6] == "gap_or_previous_bar_unusable"
    assert np.isnan(t["ret"].iloc[5]) and np.isnan(t["ret"].iloc[6])   # no 2-bar return
    assert t["status"].iloc[7] == "ok" and not np.isnan(t["ret"].iloc[7])


def test_absent_row_does_not_produce_a_two_bar_return(clean_frame):
    market, df = clean_frame
    t = table(df.drop(df.index[5]), market)
    row = t[t["slot"] == df.index[6].strftime("%H:%M")].iloc[0]
    assert row["status"] == "gap_or_previous_bar_unusable" and np.isnan(row["ret"])


def test_forming_bar_excluded_from_returns_and_volume():
    df = make_day(NSE, NSE_DAY).iloc[:19]
    as_of = df.index[-1] + pd.Timedelta(minutes=2)
    t = table(df, NSE, as_of=as_of)
    last = t.iloc[-1]
    assert last["status"] == "excluded_forming_bar" and np.isnan(last["ret"])
    assert last["volume_status"] == "excluded_unusable_bar"


def test_nse_closing_window_kept_separate():
    df = make_day(NSE, NSE_DAY)
    t = table(df, NSE)
    window = t[t["period"] == CLOSING_WINDOW]
    assert len(window) == 3
    assert (window["status"] == "nse_closing_window").all()
    assert window["ret"].isna().all()                    # not in the main results
    assert window["ret_closing"].notna().all()           # separate series
    assert t[t["slot"] == "15:10"]["status"].iloc[0] == "ok"


def test_closing_window_empty_bar_has_no_separate_return_either():
    df = make_day(NSE, NSE_DAY)
    df.iloc[-1, :] = np.nan                              # 15:25 empty
    t = table(df, NSE)
    assert t["status"].iloc[-1] == "excluded_missing_ohlc"
    assert t["ret_closing"].iloc[-1:].isna().all()


def test_us_has_no_closing_window():
    t = table(make_day(US, US_DAY), US)
    assert t["ret_closing"].isna().all()
    assert t["status"].value_counts().to_dict() == {"ok": 77, "first_bar_of_day": 1}


# ---------------- volume mask ----------------
def test_nse_0915_volume_excluded_even_when_nonzero():
    t = table(make_day(NSE, NSE_DAY, volume=500), NSE)
    assert t["volume_status"].iloc[0] == "excluded_nse_0915_volume"


def test_us_open_bar_volume_is_usable():
    t = table(make_day(US, US_DAY, volume=500), US)
    assert t["volume_status"].iloc[0] == "ok"


def test_zero_volume_and_closing_window_excluded_from_volume(market_day):
    market, day = market_day
    df = make_day(market, day)
    df.iloc[20, df.columns.get_loc("volume")] = 0
    t = table(df, market)
    assert t["volume_status"].iloc[20] == "excluded_zero_missing_or_flagged_volume"
    if market.name == "NSE":
        assert (t[t["period"] == CLOSING_WINDOW]["volume_status"]
                == "excluded_nse_closing_window").all()


# ---------------- time zones ----------------
def test_slots_are_exchange_local_time_across_us_dst_change():
    for day in ["2026-10-30", "2026-11-02"]:     # clocks change on 2026-11-01
        t = table(make_day(US, day), US)
        assert t["slot"].iloc[0] == "09:30" and t["slot"].iloc[-1] == "15:55"
        assert t["mins_since_open"].iloc[0] == 0


def test_nse_slots_are_ist():
    t = table(make_day(NSE, NSE_DAY), NSE)
    assert t["slot"].iloc[0] == "09:15" and t["slot"].iloc[-1] == "15:25"


# ---------------- accounting ----------------
def test_exclusion_summary_accounts_for_every_bar(market_day):
    market, day = market_day
    df = make_day(market, day)
    df.iloc[4, :] = np.nan
    t = table(df, market)
    s = exclusion_summary(t)
    for analysis in ["returns", "volume"]:
        assert s[s.analysis == analysis]["n_bars"].sum() == len(t)
