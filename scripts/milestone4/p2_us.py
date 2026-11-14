"""P2 zero-cost fresh US check (docs/33 sections 7 and 8): ONE Alpaca free-plan pull (feed=sip) of AAPL, MSFT, NVDA 5-minute bars for
2026-04-13..2026-08-05 (all before the tested sample), then the frozen C3 test (same rules as docs/30) on the first 59 usable complete sessions.
Keys are read from the environment (ALPACA_KEY_ID, ALPACA_SECRET_KEY) and are never stored or printed. Free plan only: no paid call exists here.
  pull | clean | run   (pull is write-once via data/p2_us_pull.done; run is write-once)"""
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))

from quantlab.calendars import US, expected_slots                                # noqa: E402
from quantlab.clean import clean, write_clean                                     # noqa: E402
from quantlab.research import direct_sim as ds, h1_calibration as hc, real_h1 as rh   # noqa: E402
from quantlab.research.panel import load_tables                                   # noqa: E402
import real_h1_run as r1                                                          # noqa: E402

SYMS = ["AAPL", "MSFT", "NVDA"]
START, END = "2026-04-13", "2026-08-05"                  # inclusive calendar window, fixed before any fetch
US_HOLIDAYS = {"2026-05-25", "2026-06-19", "2026-07-03"}   # Memorial Day, Juneteenth, Independence Day (observed)
RAW, CLEAN = ROOT / "data" / "raw" / "alpaca", ROOT / "data" / "clean_p2_us"
MARK = ROOT / "data" / "p2_us_pull.done"
OUT = ROOT / "outputs" / "milestone4" / "p2_us"
MANIFEST = ROOT / "outputs" / "milestone4" / "frozen_p2_us_inputs.sha256"
C3_CSV = ROOT / "outputs" / "milestone4" / "h1_calibration" / "stage2" / "c3_training" / "c3_critical_values.csv"


def scheduled_sessions():
    d = pd.bdate_range(START, END)
    return [x.strftime("%Y-%m-%d") for x in d if x.strftime("%Y-%m-%d") not in US_HOLIDAYS]


def alpaca_json_to_bars(payload, symbol):
    """Alpaca bars (UTC bar-start times) -> the table the project's cleaner expects (exchange time, bar START)."""
    rows = payload["bars"].get(symbol, [])
    idx = pd.to_datetime([b["t"] for b in rows], utc=True).tz_convert(US.tz)
    bars = pd.DataFrame({"open": [b["o"] for b in rows], "high": [b["h"] for b in rows], "low": [b["l"] for b in rows],
                         "close": [b["c"] for b in rows], "volume": [float(b["v"]) for b in rows]}, index=idx, dtype="float64")
    bars.index.name = "bar_start"
    return bars


def fetch_symbol(symbol):
    key, sec = os.environ.get("ALPACA_KEY_ID"), os.environ.get("ALPACA_SECRET_KEY")
    if not key or not sec:
        sys.exit("set ALPACA_KEY_ID and ALPACA_SECRET_KEY in your terminal (free plan keys); they are never stored.")
    bars, token = [], None
    while True:
        q = {"symbols": symbol, "timeframe": "5Min", "start": f"{START}T00:00:00Z", "end": "2026-08-06T00:00:00Z", "limit": 10000,
             "adjustment": "raw", "feed": "sip", "sort": "asc"}
        if token:
            q["page_token"] = token
        req = urllib.request.Request("https://data.alpaca.markets/v2/stocks/bars?" + urllib.parse.urlencode(q),
                                     headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": sec})
        with urllib.request.urlopen(req, timeout=60) as r:
            page = json.load(r)
        bars += page.get("bars", {}).get(symbol, [])
        token = page.get("next_page_token")
        if not token:
            return {"bars": {symbol: bars}}


def pull():
    if MARK.exists():
        sys.exit("single-pull rule: data/p2_us_pull.done exists.")
    if r1.verify(MANIFEST):
        sys.exit("freeze manifest mismatch: stop.")
    RAW.mkdir(parents=True, exist_ok=True)
    saved = []
    for s in SYMS:
        blob = json.dumps(fetch_symbol(s)).encode()
        p = RAW / f"{s}_5m_{START}_{END}_{hashlib.sha256(blob).hexdigest()[:12]}.json"
        p.write_bytes(blob)
        saved.append(str(p.relative_to(ROOT)))
        print("saved", saved[-1], flush=True)
    MARK.write_text(json.dumps(saved, indent=1))


def clean_new():
    CLEAN.mkdir(exist_ok=True)
    for rel in json.loads(MARK.read_text()):
        raw_path = ROOT / rel
        sym = raw_path.name.split("_")[0]
        bars = alpaca_json_to_bars(json.loads(raw_path.read_bytes()), sym)
        out, _ = clean(bars, US, as_of=pd.Timestamp("2026-08-06", tz=US.tz))
        write_clean(out, CLEAN / f"{sym}_{raw_path.stem}.parquet", raw_sha256=r1.sha(raw_path))
        print(sym, "usable bars", int(out.usable.sum()), flush=True)


def run():
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit("single-run rule: output exists.")
    if r1.verify(MANIFEST):
        sys.exit("freeze manifest mismatch: stop.")
    crit = float(pd.read_csv(C3_CSV).query("n_days == 59").c3_crit.iloc[0])
    tabs = load_tables(CLEAN)
    full, syms, _ = r1.real_array(tabs, US)
    # Re-index on the frozen scheduled-session list: a scheduled date with no data is an unusable session, never dropped.
    dates_data = sorted(set().union(*[set(tabs[s]["date"]) for s in syms]))
    sched = scheduled_sessions()
    pos = {str(d): i for i, d in enumerate(dates_data)}
    arr = np.full((len(syms), len(sched), full.shape[2]), np.nan)
    for j, d in enumerate(sched):
        if d in pos:
            arr[:, j, :] = full[:, pos[d], :]
    r2, groups = hc.to_used(arr, ds.used_slot_index(US))
    res = rh.analyse_market(r2, groups, sched, crit)
    print(syms, {k: res[k] for k in ("dates_in_sample", "usable_per_stock", "usable_market_sessions")}, res["status"], res["T"], res["reject"], flush=True)
    OUT.mkdir(parents=True)
    row = {"market": "US", "symbols": ",".join(syms), "dates_in_sample": len(sched), "usable_market_sessions": res["usable_market_sessions"],
           "usable_per_stock": str(res["usable_per_stock"]), "n_required": 59, "status": res["status"], "T": res["T"], "crit": crit,
           "reject": res["reject"], "first_date": res["first_date"], "last_date": res["last_date"]}
    if res["status"] == "TESTED":
        for k, (a, b) in enumerate(res["contrasts"]):
            row[f"log_ratio_{r1.MAIN[a]}_{r1.MAIN[b]}"] = res["theta"][k]
            row[f"se_{r1.MAIN[a]}_{r1.MAIN[b]}"] = res["se"][k]
    pd.DataFrame([row]).to_csv(OUT / "p2_us_results.csv", index=False)
    (OUT / "p2_us_metadata.json").write_text(json.dumps({"crit_n59": crit, "data_files": {p.name: r1.sha(p) for p in sorted(CLEAN.glob("*.parquet"))}}, indent=2))


if __name__ == "__main__":
    {"pull": pull, "clean": clean_new, "run": run}[sys.argv[1]]()
