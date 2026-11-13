"""Real-data H1 test with frozen C3 (docs/30), run ONCE on data/clean. No random numbers, no simulation.
Step 1 writes the session counts; step 2 computes T only for markets with 59 usable complete sessions. Output is write-once:
outputs/milestone4/real_h1/ (aggregates only; no bar-level or raw data)."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from quantlab.calendars import NSE, US, expected_slots, market_for_symbol     # noqa: E402
from quantlab.research import direct_sim as ds, h1_calibration as hc, real_h1 as rh   # noqa: E402
from quantlab.research.panel import load_tables                               # noqa: E402

B = ROOT / "outputs" / "milestone4" / "h1_calibration"
OUT = ROOT / "outputs" / "milestone4" / "real_h1"
MANIFEST = ROOT / "outputs" / "milestone4" / "frozen_real_h1_inputs.sha256"
C3_CSV = B / "stage2" / "c3_training" / "c3_critical_values.csv"
MAIN = ["open", "middle", "close"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def verify(manifest):
    bad = 0
    for line in Path(manifest).read_text().splitlines():
        h, _, rel = line.partition("  ")
        if sha(ROOT / rel) != h:
            bad += 1
            print("MISMATCH", rel)
    return bad


def real_array(tabs, market):
    labels = list(expected_slots(market, "2026-08-03").strftime("%H:%M"))
    syms = sorted(s for s in tabs if market_for_symbol(s).name == market.name)
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


def main():
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files: single-run rule (docs/30 R6).")
    bad = verify(MANIFEST)
    for m in B.rglob("*.sha256"):
        pass
    if bad:
        sys.exit("frozen_real_h1_inputs.sha256 mismatch: stop.")
    c3 = pd.read_csv(C3_CSV)
    crit = float(c3.loc[c3.n_days == rh.N_SESSIONS, "c3_crit"].iloc[0])
    tabs = load_tables(ROOT / "data" / "clean")
    OUT.mkdir(parents=True, exist_ok=True)
    rows, meta = [], {"crit_n59": crit, "data_files": {p.name: sha(p) for p in sorted((ROOT / "data" / "clean").glob("*.parquet"))}}
    for market in (NSE, US):
        idx = ds.used_slot_index(market)
        full, syms, dates = real_array(tabs, market)
        r2, groups = hc.to_used(full, idx)
        counts = rh.usable_counts(r2, dates)
        print(market.name, syms, counts, flush=True)
        res = rh.analyse_market(r2, groups, dates, crit)
        meta[market.name] = {"symbols": syms, "used_slots": int(r2.shape[2]), **{k: v for k, v in res.items() if k not in ("theta", "se", "selected_positions")}}
        row = {"market": market.name, "symbols": ",".join(syms), "dates_in_sample": counts["dates_in_sample"], "usable_market_sessions": counts["usable_market_sessions"],
               "usable_per_stock": str(counts["usable_per_stock"]), "n_required": rh.N_SESSIONS, "status": res["status"], "T": res["T"], "crit": crit, "reject": res["reject"],
               "first_date": res["first_date"], "last_date": res["last_date"]}
        if res["status"] == "TESTED":
            for k, (a, b) in enumerate(res["contrasts"]):
                row[f"log_ratio_{MAIN[a]}_{MAIN[b]}"] = res["theta"][k]
                row[f"se_{MAIN[a]}_{MAIN[b]}"] = res["se"][k]
        rows.append(row)
        print(market.name, res["status"], res["T"], res["reject"], flush=True)
    pd.DataFrame(rows).to_csv(OUT / "real_h1_results.csv", index=False)
    (OUT / "real_h1_metadata.json").write_text(json.dumps(meta, indent=2, default=str))


if __name__ == "__main__":
    main()
