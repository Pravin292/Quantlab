"""Command-line runner for the data pipeline.

  pull-test  one LIMITED, clearly labelled test pull (one request per symbol).
             It is manual; nothing here schedules or repeats downloads.
  process    parse -> validate -> clean one saved raw snapshot, write Parquet
             and a text report to data/clean/. The raw file is only read.

Run from the project root with the project's virtual environment, e.g.
  python scripts/milestone2/run_pipeline.py pull-test --confirm
  python scripts/milestone2/run_pipeline.py process data/raw/yahoo/TCS.NS/<file>.json
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from quantlab.calendars import market_for_symbol        # noqa: E402
from quantlab.clean import clean, write_clean            # noqa: E402
from quantlab.ingest import (fetch_yahoo_raw, save_raw_snapshot,   # noqa: E402
                             sha256_of_file)
from quantlab.parse import parse_yahoo_json              # noqa: E402

TEST_SYMBOLS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "AAPL", "MSFT", "NVDA"]
RAW_DIR, CLEAN_DIR = ROOT / "data" / "raw", ROOT / "data" / "clean"
MANIFEST = ROOT / "data" / "manifest.csv"


def pull_test(confirm: bool) -> None:
    if not confirm:
        sys.exit("Refusing to download without --confirm (limited TEST pull, "
                 f"{len(TEST_SYMBOLS)} requests).")
    print("LIMITED TEST PULL from Yahoo (unofficial, personal-use source; "
          "not suitable for reliable long-term research).")
    for sym in TEST_SYMBOLS:
        raw = fetch_yahoo_raw(sym, "5m", "60d")
        path = save_raw_snapshot(raw, source="yahoo", symbol=sym, interval="5m",
                                 rng="60d", raw_dir=RAW_DIR, manifest_path=MANIFEST)
        print(f"saved {path.relative_to(ROOT)}")


def process(raw_path: Path) -> None:
    raw_path = Path(raw_path).resolve()
    bars, meta = parse_yahoo_json(raw_path.read_bytes())
    market = market_for_symbol(meta["symbol"])
    # Snapshot time = when we pulled it; bars that had not finished by then
    # are flagged as still forming.
    stamp = raw_path.name.split("_")[0]                      # 20261030T050000Z
    as_of = pd.Timestamp(stamp).tz_convert(market.tz)
    out, result = clean(bars, market, as_of=as_of)

    sha = sha256_of_file(raw_path)
    target = CLEAN_DIR / f"{meta['symbol']}_{raw_path.stem}.parquet"
    write_clean(out, target, raw_sha256=sha)
    report = f"Source: {raw_path.name}\nsha256: {sha}\n" + result.to_text()
    report += (f"\n  usable bars          {int(out.usable.sum()):>6}"
               f"\n  volume_reliable bars {int(out.volume_reliable.sum()):>6}\n")
    target.with_suffix(".report.txt").write_text(report)
    print(report)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull-test"); p.add_argument("--confirm", action="store_true")
    q = sub.add_parser("process"); q.add_argument("raw_path")
    a = ap.parse_args()
    pull_test(a.confirm) if a.cmd == "pull-test" else process(a.raw_path)
