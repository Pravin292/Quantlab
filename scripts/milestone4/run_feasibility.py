"""OUTCOME-BLIND H2 feasibility report.

Uses ONLY volume and candle availability. Every price column is removed from
the tables before anything is counted (research.h2_volume.feasibility ignores
them as well, and a unit test proves identical results with scrambled prices).
No forward return, forward volatility or event-candle return is computed or seen.

Parameters are the frozen ones: L = 10, threshold = 2.0x, k = 3. They are not relaxed.
Adequacy rule: at least 30 events on at least 15 distinct days, per market (pooled stocks).
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from quantlab.research import h2_volume as h2           # noqa: E402
from quantlab.research.panel import load_tables          # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "feasibility"


def main():
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files; move them yourself first.")
    OUT.mkdir(parents=True, exist_ok=True)
    tables = load_tables(ROOT / "data" / "clean")
    blind = {s: t[[c for c in t.columns if c not in h2.PRICE_COLUMNS]] for s, t in tables.items()}
    per_stock, event_dates = [], {}
    for sym, t in blind.items():
        assert not (set(t.columns) & h2.PRICE_COLUMNS)
        per_stock.append({"market": t["market"].iloc[0], **h2.feasibility(t)})
        f = h2.event_features(t)
        event_dates[sym] = set(f.loc[f["eligible"] == 1.0, "date"])
    ps = pd.DataFrame(per_stock)
    rows = []
    for mk, g in ps.groupby("market"):
        days = set().union(*[event_dates[s] for s in g["symbol"]])
        n_ev, n_use = int(g["n_events"].sum()), int(g["n_usable_events"].sum())
        rows.append({"market": mk, "stocks": len(g), "n_events": n_ev, "n_usable_events": n_use,
                     "n_usable_event_days": len(days),
                     "adequacy_rule": "usable events >= 30 and usable event days >= 15",
                     "adequacy": h2.adequacy(n_use, len(days))})
    ps.to_csv(OUT / "h2_feasibility_by_stock.csv", index=False)
    mk = pd.DataFrame(rows)
    mk.to_csv(OUT / "h2_feasibility_by_market.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(ps.to_string(index=False)); print(); print(mk.to_string(index=False))


if __name__ == "__main__":
    main()
