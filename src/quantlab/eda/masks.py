"""EDA building blocks: which bars may be used, for what, and why not.

Takes an annotated bar table from `quantlab.clean` and produces a "bar table"
with one row per candle, containing:

  period        session period of the candle (see PERIODS)
  slot          bar start time as "HH:MM" (exchange local time)
  mins_since_open
  ret           close-to-close 5-minute log return -- MAIN analysis, only for
                bars where status == "ok"
  ret_closing   same calculation, but only for NSE closing-window bars
                (15:15-15:25), kept apart because that data is unreliable
  ret_oc        open-to-close log return of the FIRST candle of the session
                (09:15 NSE / 09:30 US), a separate analysis
  status        why a bar is (not) used for returns -- exactly one reason
  volume_status why a bar is (not) used for volume statistics

Nothing is deleted or filled: every candle keeps a row and a reason.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..calendars import BAR_MINUTES, Market

# ---------------------------------------------------------------------------
# Period definitions: HALF-OPEN intervals [start, end) in minutes after local
# midnight, applied to the bar START time. Half-open means a bar starting
# exactly on a boundary belongs to the LATER period only, so no candle is
# counted twice, and the intervals touch end-to-start so none is omitted.
# ---------------------------------------------------------------------------
CLOSING_WINDOW = "closing_window_unreliable"
PERIODS: dict[str, list[tuple[str, int, int]]] = {
    "NSE": [("open", 9 * 60 + 15, 10 * 60),            # 09:15-09:55  (9 bars)
            ("middle", 10 * 60, 14 * 60 + 30),         # 10:00-14:25 (54 bars)
            ("close", 14 * 60 + 30, 15 * 60 + 15),     # 14:30-15:10  (9 bars)
            (CLOSING_WINDOW, 15 * 60 + 15, 15 * 60 + 30)],  # 15:15-15:25 (3 bars)
    "US": [("open", 9 * 60 + 30, 10 * 60 + 30),        # 09:30-10:25 (12 bars)
           ("middle", 10 * 60 + 30, 15 * 60),          # 10:30-14:55 (54 bars)
           ("close", 15 * 60, 16 * 60)],               # 15:00-15:55 (12 bars)
}
MAIN_PERIODS = ["open", "middle", "close"]


def assign_period(index: pd.DatetimeIndex, market: Market) -> pd.Series:
    """Label each bar start time with its period, or 'outside_session'."""
    minute_of_day = index.hour * 60 + index.minute
    labels = np.full(len(index), "outside_session", dtype=object)
    for name, start, end in PERIODS[market.name]:
        labels[(minute_of_day >= start) & (minute_of_day < end)] = name
    return pd.Series(labels, index=index, name="period")


def _unusable_reason(df: pd.DataFrame) -> pd.Series:
    """First applicable reason a bar is unusable (precedence = list order)."""
    reason = pd.Series("", index=df.index, dtype=object)
    for flag in ["forming_bar", "missing_ohlc", "invalid_ohlc",
                 "unexpected_session_bar", "duplicate_timestamp"]:
        todo = (reason == "") & df[flag]
        reason[todo] = f"excluded_{flag}"
    return reason


def build_bar_table(df: pd.DataFrame, market: Market, symbol: str) -> pd.DataFrame:
    """Turn an annotated clean table into the EDA bar table."""
    df = df.sort_index()
    idx = df.index
    t = pd.DataFrame(index=idx)
    t["symbol"] = symbol
    t["market"] = market.name
    t["date"] = idx.date
    t["slot"] = idx.strftime("%H:%M")
    t["mins_since_open"] = idx.hour * 60 + idx.minute - market.open_minutes
    t["period"] = assign_period(idx, market)
    for c in ["open", "high", "low", "close", "volume", "usable", "volume_reliable"]:
        t[c] = df[c]

    # ---- return status: exactly one reason per bar (first match wins) ----
    gap = pd.Series(idx, index=idx).diff()
    consecutive = gap == pd.Timedelta(minutes=BAR_MINUTES)   # previous bar is 5 min earlier
    prev_usable = df["usable"].shift(1, fill_value=False).astype(bool)
    closing = t["period"] == CLOSING_WINDOW
    first_bar = t["mins_since_open"] == 0

    status = _unusable_reason(df)
    for label, cond in [("nse_closing_window", closing),
                        ("first_bar_of_day", first_bar),
                        ("gap_or_previous_bar_unusable", ~(consecutive & prev_usable))]:
        todo = (status == "") & cond
        status[todo] = label
    status[status == ""] = "ok"
    t["status"] = status

    # ---- returns ----
    # Only unflagged, consecutive bars get a log return: ln(close_t / close_{t-1}).
    log_ret = np.log(df["close"] / df["close"].shift(1))
    # Closing-window bars get a return only if they also satisfy the usual rules.
    closing_ok = closing & df["usable"] & consecutive & prev_usable
    t["ret"] = log_ret.where(status == "ok")
    t["ret_closing"] = log_ret.where(closing_ok)
    # Opening candle: its own open-to-close move, kept separate from `ret`.
    t["ret_oc"] = np.log(df["close"] / df["open"]).where(first_bar & df["usable"])

    # ---- volume status ----
    vstat = pd.Series("ok", index=idx, dtype=object)
    vstat[~df["volume_reliable"]] = "excluded_zero_missing_or_flagged_volume"
    if market.name == "NSE":
        vstat[first_bar] = "excluded_nse_0915_volume"      # reliability unproven
    vstat[closing] = "excluded_nse_closing_window"
    vstat[~df["usable"]] = "excluded_unusable_bar"
    t["volume_status"] = vstat
    t["volume_ok"] = vstat == "ok"
    return t


def exclusion_summary(table: pd.DataFrame) -> pd.DataFrame:
    """Counts of every status, so no exclusion is silent."""
    out = []
    for col in ["status", "volume_status"]:
        c = table[col].value_counts().rename_axis("reason").reset_index(name="n_bars")
        c.insert(0, "analysis", "returns" if col == "status" else "volume")
        out.append(c)
    res = pd.concat(out, ignore_index=True)
    res.insert(0, "symbol", table["symbol"].iloc[0] if len(table) else "")
    res["share"] = res["n_bars"] / max(len(table), 1)
    return res
