"""QuantLab H1 tool: run the frozen C3 test on your own 5-minute bars.

    python -m quantlab.h1tool bars.csv                 # 59 sessions (default)
    python -m quantlab.h1tool bars.csv --sessions 125 --json result.json

INPUT  a CSV with the columns  symbol,timestamp,open,high,low,close,volume  (case does not matter).
       `timestamp` is the bar START time, either ISO 8601 with a UTC offset (2026-08-06T09:30:00-04:00) or exchange-local wall-clock time without an offset.
       Exactly three stocks of ONE market. Symbols ending in .NS are NSE (09:15-15:30 IST); anything else is a US stock (09:30-16:00 New York).
OUTPUT a plain-text report and, with --json, a machine-readable file: status, the statistic T, the frozen C3 critical value, the decision, the three volatility ratios
       with 95% intervals, data-quality counts and warnings. Exit code 0 = tested, 2 = not testable or outside the supported domain, 1 = unreadable input.

What the tool does NOT do: it never shortens a sample to fit (fewer usable complete sessions than requested = NOT_TESTABLE), never fills or deletes bars silently (the project's cleaner labels every
bar), and never claims more than the C3 evidence supports (see the `limitations` field). The C3 critical values are the frozen ones (docs/18, docs/20); a test checks they match the frozen files.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from .calendars import expected_slots, market_for_symbol
from .clean import clean
from .eda.masks import build_bar_table
from .research import direct_sim as ds, h1_calibration as hc, real_h1 as rh
from .research.h1_rms import CONTRAST_IDX

VERSION = "1.0"
# Frozen C3 critical values (outputs/milestone4/h1_calibration/stage2/c3_training and stage3/c3_intermediate). tests/test_h1tool.py checks them against the files.
C3_CRIT = {59: 3.298658000460969, 90: 2.946700601647945, 125: 2.880075520718791, 180: 2.8547272011404488, 250: 2.8160001315968115}
REQUIRED = ["symbol", "timestamp", "open", "high", "low", "close", "volume"]
MAIN = ["open", "middle", "close"]
N_STOCKS = 3
Z95 = 1.959964
LIMITATIONS = [
    "C3 was validated on SIMULATED markets with three stocks and a fixed set of session counts; its verdict is PARTIAL (safe and cautious there, not proven exact, not proven on real data).",
    "A rejection means volatility differs between at least two of open, middle and close. It does not say which period or why, and says nothing about trading or profit.",
    "C3 is cautious: a 'not rejected' result is weak evidence of equality, not proof of it.",
    "Only dependence levels inside the simulated range are covered by the evidence (see docs/41 and docs/43).",
    "Stocks that moved together unusually strongly, or markets other than NSE and US, are outside what was checked.",
]


def _parse_timestamps(s: pd.Series, tz: str) -> pd.DatetimeIndex:
    """Bar start times as exchange-local tz-aware timestamps. All-offset or all-naive input is accepted; a mixture is refused."""
    has_offset = s.astype(str).str.contains(r"(?:Z|[+-]\d{2}:?\d{2})$", regex=True)
    if has_offset.all():
        return pd.DatetimeIndex(pd.to_datetime(s, utc=True)).tz_convert(tz)
    if not has_offset.any():
        return pd.DatetimeIndex(pd.to_datetime(s)).tz_localize(tz)
    raise ValueError("timestamps mix values with and without a UTC offset; use one style")


def read_bars(path: str | Path) -> dict[str, pd.DataFrame]:
    """CSV -> {symbol: bars} with a tz-aware exchange-time index named bar_start and float64 open/high/low/close/volume."""
    df = pd.read_csv(path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"missing column(s): {', '.join(missing)}; required: {', '.join(REQUIRED)}")
    out = {}
    for sym, g in df.groupby(df["symbol"].astype(str).str.strip(), sort=True):
        market = market_for_symbol(sym)
        idx = _parse_timestamps(g["timestamp"], market.tz)
        bars = pd.DataFrame({c: pd.to_numeric(g[c], errors="coerce").to_numpy(dtype="float64") for c in ("open", "high", "low", "close", "volume")}, index=idx)
        bars.index.name = "bar_start"
        out[sym] = bars
    return out


def _real_array(tabs: dict[str, pd.DataFrame], market) -> tuple[np.ndarray, list[str], list]:
    """(stocks, days, all slots) squared returns of usable main-period bars; NaN elsewhere (same rule as the project's real-data tests)."""
    labels = list(expected_slots(market, "2026-08-03").strftime("%H:%M"))
    syms = sorted(tabs)
    dates = sorted(set().union(*[set(tabs[s]["date"]) for s in syms]))
    arr = np.full((len(syms), len(dates), len(labels)), np.nan)
    for i, s in enumerate(syms):
        t = tabs[s]
        t = t[(t["status"] == "ok") & t["period"].isin(MAIN) & np.isfinite(t["ret"])]
        di = pd.Index(dates).get_indexer(t["date"])
        si = pd.Index(labels).get_indexer(t["slot"])
        keep = (di >= 0) & (si >= 0)
        arr[i, di[keep], si[keep]] = t["ret"].to_numpy()[keep] ** 2
    return arr, syms, dates


def _unsupported(reason: str, **extra) -> dict:
    return {"tool_version": VERSION, "status": "NOT_SUPPORTED", "reason": reason, "limitations": LIMITATIONS, **extra}


def analyse(bars_by_symbol: dict[str, pd.DataFrame], sessions: int = 59) -> dict:
    """Run the cleaner and the frozen C3 test. Returns a JSON-ready dict."""
    if sessions not in C3_CRIT:
        return _unsupported(f"C3 has frozen critical values only for {sorted(C3_CRIT)} sessions; asked for {sessions}")
    syms = sorted(bars_by_symbol)
    markets = {market_for_symbol(s).name for s in syms}
    if len(markets) != 1:
        return _unsupported("the stocks belong to more than one market; give three stocks of one market", symbols=syms)
    if len(syms) != N_STOCKS:
        return _unsupported(f"C3 was calibrated for exactly {N_STOCKS} stocks of one market; got {len(syms)}", symbols=syms)
    market = market_for_symbol(syms[0])
    tabs, quality = {}, {}
    for s in syms:
        b = bars_by_symbol[s]
        as_of = b.index.max().normalize() + pd.Timedelta(days=1)
        annotated, result = clean(b, market, as_of=as_of)
        tabs[s] = build_bar_table(annotated, market, s)
        quality[s] = {"rows_read": int(len(b)), "exact_duplicates_removed": int(result.n_duplicates_removed), "status_counts": {k: int(v) for k, v in tabs[s]["status"].value_counts().items()}}
    full, order, dates = _real_array(tabs, market)
    r2, groups = hc.to_used(full, ds.used_slot_index(market))
    crit = C3_CRIT[sessions]
    res = rh.analyse_market(r2, groups, dates, crit, n=sessions)
    out = {"tool_version": VERSION, "status": res["status"], "market": market.name, "symbols": order, "sessions_requested": sessions, "dates_in_sample": res["dates_in_sample"],
           "usable_sessions_per_stock": dict(zip(order, res["usable_per_stock"])), "usable_market_sessions": res["usable_market_sessions"], "crit_C3": crit, "data_quality": quality,
           "limitations": LIMITATIONS, "warnings": []}
    if res["status"] != "TESTED":
        out["reading"] = (f"NOT TESTABLE: only {res['usable_market_sessions']} complete sessions are usable (all three stocks, every used 5-minute slot), but {sessions} are required. "
                          "The sample is never shortened to fit; no statistic was computed.")
        return out
    ratios = {}
    for k, (a, b) in enumerate(res["contrasts"]):
        th, se = res["theta"][k], res["se"][k]
        ratios[f"{MAIN[a]}_vs_{MAIN[b]}"] = {"log_ratio_of_mean_squares": th, "standard_error": se, "volatility_ratio": math.exp(th / 2),
                                            "ratio_low_95": math.exp((th - Z95 * se) / 2), "ratio_high_95": math.exp((th + Z95 * se) / 2), "t": th / se}
    out.update({"first_date": res["first_date"], "last_date": res["last_date"], "T": res["T"], "reject": res["reject"], "contrasts": ratios})
    if res["usable_market_sessions"] > sessions:
        out["warnings"].append(f"{res['usable_market_sessions']} usable sessions exist; only the FIRST {sessions} in date order were used (frozen rule).")
    out["reading"] = (f"REJECT: T = {res['T']:.3f} is above the C3 limit {crit:.3f}. Volatility is not equal across open, middle and close." if res["reject"]
                      else f"NOT REJECTED: T = {res['T']:.3f} is not above the C3 limit {crit:.3f}. No evidence of a difference (C3 is cautious, so this is weak evidence of equality).")
    return out


def format_report(r: dict) -> str:
    lines = [f"QuantLab H1 tool v{r['tool_version']}", f"status: {r['status']}"]
    if r["status"] == "NOT_SUPPORTED":
        lines += [f"reason: {r['reason']}"]
    else:
        lines += [f"market: {r['market']}   stocks: {', '.join(r['symbols'])}", f"sessions: {r['usable_market_sessions']} usable of {r['dates_in_sample']} dates; {r['sessions_requested']} requested"]
        if r["status"] == "TESTED":
            lines += [f"window: {r['first_date']} to {r['last_date']}", f"T = {r['T']:.4f}   C3 limit = {r['crit_C3']:.4f}   decision: {'REJECT' if r['reject'] else 'not rejected'}", "volatility ratios (RMS return, 95% interval):"]
            lines += [f"  {k.replace('_', ' '):18s} {v['volatility_ratio']:.2f}x  [{v['ratio_low_95']:.2f}, {v['ratio_high_95']:.2f}]" for k, v in r["contrasts"].items()]
        lines += [r["reading"]] + [f"warning: {w}" for w in r["warnings"]]
    lines += ["", "limitations:"] + [f"  - {t}" for t in r["limitations"]]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="quantlab.h1tool", description="Run the frozen C3 test of equal volatility in the open, middle and close on your own 5-minute bars.")
    ap.add_argument("csv", help="CSV with columns symbol,timestamp,open,high,low,close,volume")
    ap.add_argument("--sessions", type=int, default=59, choices=sorted(C3_CRIT), help="complete sessions to use (default 59)")
    ap.add_argument("--json", default=None, help="also write the result to this JSON file")
    a = ap.parse_args(argv)
    try:
        result = analyse(read_bars(a.csv), a.sessions)
    except (ValueError, OSError, pd.errors.ParserError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(format_report(result))
    if a.json:
        Path(a.json).write_text(json.dumps(result, indent=2, default=str))
    return 0 if result["status"] == "TESTED" else 2


if __name__ == "__main__":
    sys.exit(main())
