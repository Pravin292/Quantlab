"""Compare the revision snapshot with the original research snapshot (both read-only).

Only bars that were already COMPLETE when the original was pulled are compared,
so ordinary new data arriving later is not mistaken for a revision. Cleaning is
done in memory for the flag comparison; nothing is written to data/clean/.

Outputs (new folder): outputs/milestone4/revision/
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from quantlab.calendars import BAR_MINUTES, market_for_symbol          # noqa: E402
from quantlab.clean import clean                                        # noqa: E402
from quantlab.ingest import sha256_of_file                              # noqa: E402
from quantlab.parse import parse_yahoo_json                             # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "revision"
SYMBOLS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "AAPL", "MSFT", "NVDA"]
COLS = ["open", "high", "low", "close", "volume"]


def load(path: Path, symbol: str):
    market = market_for_symbol(symbol)
    bars, _ = parse_yahoo_json(path.read_bytes())
    as_of = pd.Timestamp(path.name.split("_")[0]).tz_convert(market.tz)
    annotated, _ = clean(bars, market, as_of=as_of)
    return annotated, as_of, market


def differs(a: pd.Series, b: pd.Series) -> pd.Series:
    """True where values differ; two NaNs count as equal."""
    both_nan = a.isna() & b.isna()
    return ~both_nan & ~np.isclose(a.fillna(-1e18), b.fillna(-1e18), rtol=1e-9, atol=0)


def main():
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files; move them yourself first.")
    OUT.mkdir(parents=True, exist_ok=True)
    rows, by_slot, files = [], [], []
    for sym in SYMBOLS:
        orig = next((ROOT / "data" / "raw" / "yahoo" / sym).glob("*.json"))
        rev = next((ROOT / "data" / "raw_revision" / "yahoo" / sym).glob("*.json"))
        files.append({"symbol": sym, "original": str(orig.relative_to(ROOT)), "original_sha256": sha256_of_file(orig),
                      "revision": str(rev.relative_to(ROOT)), "revision_sha256": sha256_of_file(rev)})
        a, as_of_a, market = load(orig, sym)
        b, as_of_b, _ = load(rev, sym)
        complete = a.index[(a.index + pd.Timedelta(minutes=BAR_MINUTES)) <= as_of_a]
        common = complete.intersection(b.index)
        A, Bv = a.loc[common], b.loc[common]
        price_diff = pd.concat([differs(A[c], Bv[c]) for c in ["open", "high", "low", "close"]], axis=1).any(axis=1)
        vol_diff = differs(A["volume"], Bv["volume"])
        empty_a, empty_b = A[["open", "high", "low", "close"]].isna().any(axis=1), Bv[["open", "high", "low", "close"]].isna().any(axis=1)
        zero_a, zero_b = (A["volume"] == 0), (Bv["volume"] == 0)
        rows.append({
            "symbol": sym, "gap_minutes_between_pulls": round((as_of_b - as_of_a).total_seconds() / 60),
            "bars_complete_in_original": len(complete), "of_which_still_present": len(common),
            "bars_dropped_from_window_start": len(complete) - len(common),
            "share_price_changed": price_diff.mean(), "n_price_changed": int(price_diff.sum()),
            "share_volume_changed": vol_diff.mean(), "n_volume_changed": int(vol_diff.sum()),
            "n_empty_became_filled": int((empty_a & ~empty_b).sum()), "n_filled_became_empty": int((~empty_a & empty_b).sum()),
            "n_zero_became_nonzero": int((zero_a & ~zero_b & ~empty_b).sum()),
            "n_nonzero_became_zero": int((~zero_a & zero_b & ~empty_a).sum()),
            "share_usable_flag_changed": (A["usable"] != Bv["usable"]).mean(),
            "share_volume_reliable_flag_changed": (A["volume_reliable"] != Bv["volume_reliable"]).mean(),
            "n_dates_with_any_change": len(set(common[(price_diff | vol_diff).to_numpy()].date)),
        })
        t = pd.DataFrame({"slot": common.strftime("%H:%M"), "price": price_diff.to_numpy(), "volume": vol_diff.to_numpy()})
        g = t.groupby("slot").mean().reset_index()
        g.insert(0, "symbol", sym)
        by_slot.append(g[(g.price > 0) | (g.volume > 0)])
    pd.DataFrame(files).to_csv(OUT / "snapshot_files.csv", index=False)
    summary = pd.DataFrame(rows)
    summary.to_csv(OUT / "revision_summary.csv", index=False)
    pd.concat(by_slot).to_csv(OUT / "revision_by_slot.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(summary.round(4).T.to_string())


if __name__ == "__main__":
    main()
