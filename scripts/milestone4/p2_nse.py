"""P2 zero-cost NSE check (docs/33 section 7): ONE Yahoo pull for the three NSE stocks, cleaning into data/clean_p2, then the frozen C3 test
(same rules as docs/30) only if 59 usable complete sessions exist. No cost, no account, no random numbers.
  pull   one request per symbol (3 requests), write-once marker data/p2_nse_pull.done
  clean  parse/validate/clean the three new raw files into data/clean_p2 (data/clean is never touched)
  run    session counts first; T only if >= 59; output outputs/milestone4/p2_nse/ (write-once, aggregates only)"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))

from quantlab.calendars import NSE, market_for_symbol                           # noqa: E402
from quantlab.clean import clean, write_clean                                    # noqa: E402
from quantlab.ingest import fetch_yahoo_raw, save_raw_snapshot, sha256_of_file   # noqa: E402
from quantlab.parse import parse_yahoo_json                                      # noqa: E402
from quantlab.research import direct_sim as ds, h1_calibration as hc, real_h1 as rh   # noqa: E402
from quantlab.research.panel import load_tables                                  # noqa: E402
import real_h1_run as r1                                                         # noqa: E402

SYMS = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
RAW, CLEAN = ROOT / "data" / "raw", ROOT / "data" / "clean_p2"
MARK = ROOT / "data" / "p2_nse_pull.done"
OUT = ROOT / "outputs" / "milestone4" / "p2_nse"
MANIFEST = ROOT / "outputs" / "milestone4" / "frozen_p2_inputs.sha256"
C3_CSV = ROOT / "outputs" / "milestone4" / "h1_calibration" / "stage2" / "c3_training" / "c3_critical_values.csv"


def pull():
    if MARK.exists():
        sys.exit("single-pull rule: data/p2_nse_pull.done exists.")
    if r1.verify(MANIFEST):
        sys.exit("freeze manifest mismatch: stop.")
    saved = []
    for s in SYMS:
        raw = fetch_yahoo_raw(s, "5m", "60d")
        p = save_raw_snapshot(raw, source="yahoo", symbol=s, interval="5m", rng="60d", raw_dir=RAW, manifest_path=ROOT / "data" / "manifest.csv")
        saved.append(str(p.relative_to(ROOT)))
        print("saved", saved[-1], flush=True)
    MARK.write_text(json.dumps(saved, indent=1))


def clean_new():
    CLEAN.mkdir(exist_ok=True)
    for rel in json.loads(MARK.read_text()):
        raw_path = ROOT / rel
        bars, meta = parse_yahoo_json(raw_path.read_bytes())
        market = market_for_symbol(meta["symbol"])
        as_of = pd.Timestamp(raw_path.name.split("_")[0]).tz_convert(market.tz)
        out, result = clean(bars, market, as_of=as_of)
        sha = sha256_of_file(raw_path)
        target = CLEAN / f"{meta['symbol']}_{raw_path.stem}.parquet"
        write_clean(out, target, raw_sha256=sha)
        print(meta["symbol"], "usable bars", int(out.usable.sum()), flush=True)


def run():
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit("single-run rule: output exists.")
    if r1.verify(MANIFEST):
        sys.exit("freeze manifest mismatch: stop.")
    crit = float(pd.read_csv(C3_CSV).query("n_days == 59").c3_crit.iloc[0])
    tabs = load_tables(CLEAN)
    idx = ds.used_slot_index(NSE)
    full, syms, dates = r1.real_array(tabs, NSE)
    r2, groups = hc.to_used(full, idx)
    print(syms, rh.usable_counts(r2, dates), flush=True)
    res = rh.analyse_market(r2, groups, dates, crit)
    print(res["status"], res["T"], res["reject"], flush=True)
    OUT.mkdir(parents=True)
    row = {"market": "NSE", "symbols": ",".join(syms), "dates_in_sample": len(dates), "usable_market_sessions": res["usable_market_sessions"],
           "usable_per_stock": str(res["usable_per_stock"]), "n_required": 59, "status": res["status"], "T": res["T"], "crit": crit,
           "reject": res["reject"], "first_date": res["first_date"], "last_date": res["last_date"]}
    if res["status"] == "TESTED":
        for k, (a, b) in enumerate(res["contrasts"]):
            row[f"log_ratio_{r1.MAIN[a]}_{r1.MAIN[b]}"] = res["theta"][k]
            row[f"se_{r1.MAIN[a]}_{r1.MAIN[b]}"] = res["se"][k]
    pd.DataFrame([row]).to_csv(OUT / "p2_nse_results.csv", index=False)
    (OUT / "p2_nse_metadata.json").write_text(json.dumps({"crit_n59": crit, "data_files": {p.name: r1.sha(p) for p in sorted(CLEAN.glob("*.parquet"))}}, indent=2))


if __name__ == "__main__":
    {"pull": pull, "clean": clean_new, "run": run}[sys.argv[1]]()
