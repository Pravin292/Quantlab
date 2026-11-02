"""ONE manual snapshot, taken only to measure how much Yahoo revises its history.

* Saved in a SEPARATE folder (data/raw_revision/) with a SEPARATE manifest
  (data/manifest_revision.csv). The original data/raw/, data/manifest.csv and
  data/clean/ are not touched.
* Not processed into data/clean/ and not part of the research sample.
* One request per stock (6 total). Run it by hand once; nothing here repeats.

Usage:  python scripts/milestone4/pull_revision_snapshot.py --confirm
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from quantlab.ingest import fetch_yahoo_raw, save_raw_snapshot   # noqa: E402

SYMBOLS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "AAPL", "MSFT", "NVDA"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true")
    if not ap.parse_args().confirm:
        sys.exit("Refusing to download without --confirm (6 requests, revision-sensitivity snapshot).")
    raw_dir = ROOT / "data" / "raw_revision"
    manifest = ROOT / "data" / "manifest_revision.csv"
    print("REVISION-SENSITIVITY SNAPSHOT (not part of the research sample)")
    for sym in SYMBOLS:
        raw = fetch_yahoo_raw(sym, "5m", "60d")
        path = save_raw_snapshot(raw, source="yahoo", symbol=sym, interval="5m", rng="60d",
                                 raw_dir=raw_dir, manifest_path=manifest)
        print("saved", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
