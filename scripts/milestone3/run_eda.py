"""Run the Milestone 3 EDA on the cleaned sample snapshots.

Reads  : data/clean/*.parquet (never modified) and the matching raw JSON in
         data/raw (only READ, to re-verify hashes and count duplicates).
Writes : outputs/milestone3/  (CSV tables + HTML charts). Refuses to run if
         that folder already has files, so earlier outputs are never replaced.

Run from the project root:  python scripts/milestone3/run_eda.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from quantlab.calendars import NSE, US, market_for_symbol          # noqa: E402
from quantlab.clean import clean                                    # noqa: E402
from quantlab.eda import metrics as m                               # noqa: E402
from quantlab.eda import plots                                      # noqa: E402
from quantlab.eda.masks import build_bar_table, exclusion_summary   # noqa: E402
from quantlab.ingest import sha256_of_file                          # noqa: E402
from quantlab.parse import parse_yahoo_json                         # noqa: E402

CLEAN_DIR, RAW_DIR = ROOT / "data" / "clean", ROOT / "data" / "raw" / "yahoo"
OUT = ROOT / "outputs" / "milestone3"
CORE = ["open", "high", "low", "close", "volume", "usable", "volume_reliable"]


def load_snapshot(parquet: Path):
    """Load one cleaned file, and re-derive it from the raw snapshot to prove
    it matches (and to count exact duplicate rows removed)."""
    symbol, _, stem = parquet.stem.partition("_")
    raw_path = RAW_DIR / symbol / f"{stem}.json"
    market = market_for_symbol(symbol)
    stored = pd.read_parquet(parquet)

    bars, _meta = parse_yahoo_json(raw_path.read_bytes())          # read-only use of raw
    as_of = pd.Timestamp(stem.split("_")[0]).tz_convert(market.tz)
    recomputed, result = clean(bars, market, as_of=as_of)
    same = stored[CORE].equals(recomputed[CORE])
    sha = sha256_of_file(raw_path)
    info = {"symbol": symbol, "market": market.name, "raw_file": str(raw_path.relative_to(ROOT)),
            "raw_sha256": sha, "sha_in_clean_file": stored.attrs.get("raw_sha256"),
            "sha_matches": sha == stored.attrs.get("raw_sha256"),
            "clean_matches_recomputed": bool(same), "rows": len(stored),
            "first_day": str(stored.index.min().date()), "last_day": str(stored.index.max().date()),
            "n_duplicates_removed": result.n_duplicates_removed}
    return symbol, market, stored, info


def per_symbol(fn, ok, by="slot"):
    parts = []
    for s, g in ok.groupby("symbol"):
        r = fn(g, by)
        r.insert(0, "symbol", s)
        parts.append(r)
    return m.attach_mins_since_open(pd.concat(parts, ignore_index=True), ok)


def main():
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files; move or delete them yourself first "
                 "(this script never overwrites outputs).")
    OUT.mkdir(parents=True, exist_ok=True)

    tables, infos, markets = {}, [], {}
    for p in sorted(CLEAN_DIR.glob("*.parquet")):
        sym, market, stored, info = load_snapshot(p)
        tables[sym] = build_bar_table(stored, market, sym)
        markets[sym] = market
        infos.append(info)
    snap = pd.DataFrame(infos)
    assert snap["sha_matches"].all() and snap["clean_matches_recomputed"].all(), \
        "a cleaned file does not match its raw snapshot -- stop and investigate"
    snap.to_csv(OUT / "snapshots.csv", index=False)

    full = pd.concat(tables.values())
    by_market = {mk: sorted(s for s in tables if markets[s].name == mk) for mk in ["NSE", "US"]}
    ok = m.add_standardised(m.main_returns(full))

    # ---- exclusions: every bar accounted for ----
    pd.concat([exclusion_summary(t) for t in tables.values()]).to_csv(OUT / "exclusions.csv", index=False)

    # ---- distribution, tails, outliers ----
    dist = pd.DataFrame([{"symbol": s, **m.distribution_stats(g["ret"])} for s, g in ok.groupby("symbol")])
    dist.to_csv(OUT / "return_distribution.csv", index=False)
    tails = pd.DataFrame([{"symbol": s, **m.tail_stats(g["z"])} for s, g in ok.groupby("symbol")])
    tails.to_csv(OUT / "tail_events.csv", index=False)
    moves = m.largest_moves(ok, 10)
    moves.to_csv(OUT / "largest_moves.csv", index=False)

    # ---- time of day ----
    mean_tbl = per_symbol(m.mean_by_slot, ok)
    mean_tbl.to_csv(OUT / "mean_return_by_slot.csv", index=False)
    ci = (mean_tbl.dropna(subset=["ci_low"]).groupby("symbol")
          .agg(n_slots=("slot", "count"), n_ci_excludes_zero=("ci_excludes_zero", "sum")).reset_index())
    ci["expected_by_chance_at_5pct"] = ci["n_slots"] * 0.05
    ci.to_csv(OUT / "mean_return_ci_summary.csv", index=False)

    vol_tbl = per_symbol(m.volatility_by_slot, ok)
    vol_tbl.to_csv(OUT / "volatility_by_slot.csv", index=False)
    per = []
    for s, g in ok.groupby("symbol"):
        r = m.volatility_by_period(g); r.insert(0, "symbol", s); per.append(r)
    pd.concat(per).to_csv(OUT / "volatility_by_period.csv", index=False)

    vp = m.volume_profile(full)
    vp = m.attach_mins_since_open(vp, full)
    vp.to_csv(OUT / "volume_profile.csv", index=False)

    # ---- separate analyses ----
    m.opening_candle_stats(full).to_csv(OUT / "opening_candle_open_to_close.csv", index=False)
    m.closing_window_stats(full).to_csv(OUT / "nse_closing_window.csv", index=False)
    qual = m.quality_by_slot(full)
    qual.to_csv(OUT / "data_quality_by_slot.csv", index=False)

    # ---- NSE vs US comparison (relative shapes) ----
    v = vol_tbl.copy()
    v["value"] = v["std_bps"] / v.groupby("symbol")["std_bps"].transform("median")
    v["market"] = v["symbol"].map(lambda s: markets[s].name)
    vol_rel = v.groupby(["market", "mins_since_open"], as_index=False)["value"].mean()
    p = vp.copy()
    p["value"] = p["relative_volume"]
    p["market"] = p["symbol"].map(lambda s: markets[s].name)
    vp_rel = p.groupby(["market", "mins_since_open"], as_index=False)["value"].mean()
    vol_rel.to_csv(OUT / "compare_volatility_relative.csv", index=False)
    vp_rel.to_csv(OUT / "compare_volume_relative.csv", index=False)

    # ---- charts ----
    def save(fig, name):
        fig.write_html(OUT / f"{name}.html", include_plotlyjs="directory")
    save(plots.returns_histogram(ok, by_market), "01_return_distributions")
    save(plots.qq_plot(ok, by_market), "02_qq_plots")
    for mk, mkt in [("NSE", NSE), ("US", US)]:
        syms = by_market[mk]
        save(plots.mean_return_by_slot(mean_tbl[mean_tbl.symbol.isin(syms)], mkt, syms), f"03_mean_return_{mk}")
        save(plots.volatility_by_slot(vol_tbl[vol_tbl.symbol.isin(syms)], mkt, syms), f"04_volatility_{mk}")
        save(plots.volume_profile(vp[vp.symbol.isin(syms)], mkt, syms), f"05_volume_{mk}")
        save(plots.quality_heatmap(full[full.symbol.isin(syms)], syms,
                                   m.quality_category(full[full.symbol.isin(syms)]), mkt), f"07_data_quality_{mk}")
    save(plots.market_comparison(vol_rel, vp_rel), "06_nse_vs_us")

    print("snapshots:\n", snap[["symbol", "rows", "first_day", "last_day", "n_duplicates_removed",
                                 "sha_matches", "clean_matches_recomputed"]].to_string(index=False))
    print("\nwrote", len(list(OUT.iterdir())), "files to", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
