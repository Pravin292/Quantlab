"""Write the complete registry of pre-specified tests (confirmatory + exploratory)
BEFORE any real-outcome result exists, so nothing can be added after seeing results.

Output: docs/07_test_registry.csv   (refuses to overwrite an existing file)
Columns: id, hypothesis, class, holm_or_bh_family, market_or_stock, description
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "07_test_registry.csv"
MARKETS = ["NSE", "US"]
STOCKS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "AAPL", "MSFT", "NVDA"]
rows = []


def add(h, cls, fam, where, desc):
    rows.append({"id": f"{h}-{cls[0].upper()}{sum(1 for r in rows if r['hypothesis'] == h and r['class'] == cls) + 1:03d}",
                 "hypothesis": h, "class": cls, "family": fam, "market_or_stock": where, "description": desc})


# ------------------------------------------------------------ CONFIRMATORY (14)
for mk in MARKETS:
    add("H1", "confirmatory", "F1_H1_omnibus", mk, "Friedman test, ln per-bar volatility, open/middle/close, market-level panel")
for mk in MARKETS:
    for a, b in [("open", "middle"), ("close", "middle"), ("open", "close")]:
        add("H1", "post-hoc", f"F2_H1_posthoc_{mk}", mk, f"Wilcoxon signed-rank {a} vs {b} (interpreted only if {mk} omnibus passes Holm)")
for mk in MARKETS:
    add("H2", "confirmatory", "F3_H2_primary", mk, "return continuation g_open, k=3, event regression (wild cluster bootstrap p)")
    add("H2", "confirmatory", "F3_H2_primary", mk, "forward volatility y_fv_open, k=3, event regression (wild cluster bootstrap p)")
for mk in MARKETS:
    add("H3", "confirmatory", "F4_H3_primary", mk, "clustered Wald test, autocorrelations at lags 1-6 jointly zero")

# ------------------------------------------------------------ EXPLORATORY (BH within hypothesis)
# H1 (19)
for s in STOCKS:
    add("H1", "exploratory", "BH_H1", s, "per-stock Friedman test")
for variant in ["all bars, no subsampling", "mean |r| measure", "drop the 3 highest-volatility days", "first 5 bars of open period excluded"]:
    for mk in MARKETS:
        add("H1", "exploratory", "BH_H1", mk, f"market-level Friedman, sensitivity: {variant}")
add("H1", "exploratory", "BH_H1", "NSE", "market-level Friedman, sensitivity: 15:10 bar excluded from close period")
for mk in MARKETS:
    for half in ["first half of days", "second half of days"]:
        add("H1", "exploratory", "BH_H1", mk, f"market-level Friedman, stability: {half}")
# H2 (56)
for mk in MARKETS:
    for out in ["return continuation", "forward volatility"]:
        add("H2", "exploratory", "BH_H2", mk, f"{out}: baseline L=20 instead of 10")
        add("H2", "exploratory", "BH_H2", mk, f"{out}: entry at event close (optimistic), k=3")
        add("H2", "exploratory", "BH_H2", mk, f"{out}: delayed entry O(t+2), k=3")
        add("H2", "exploratory", "BH_H2", mk, f"{out}: continuous ln(volume ratio) instead of event dummy")
        add("H2", "exploratory", "BH_H2", mk, f"{out}: de-clustered events (skip events within k bars of an earlier one)")
        add("H2", "exploratory", "BH_H2", mk, f"{out}: top 1% of |outcome| dropped (sensitivity only)")
        add("H2", "exploratory", "BH_H2", mk, f"{out}: matched comparison (same stock and slot, similar |z|)")
        for k in (1, 6):
            add("H2", "exploratory", "BH_H2", mk, f"{out}: horizon k={k}")
        for half in ["first half of days", "second half of days"]:
            add("H2", "exploratory", "BH_H2", mk, f"{out}: stability, {half}")
for s in STOCKS:
    for out in ["return continuation", "forward volatility"]:
        add("H2", "exploratory", "BH_H2", s, f"{out}: per-stock regression")
# H3 (56)
for mk in MARKETS:
    for k in range(1, 7):
        add("H3", "exploratory", "BH_H3", mk, f"autocorrelation at lag {k} (clustered z)")
    for q in (2, 3, 6, 12):
        add("H3", "exploratory", "BH_H3", mk, f"variance ratio VR({q}) (day-block bootstrap p)")
    for k in (1, 3, 6):
        add("H3", "exploratory", "BH_H3", mk, f"predictive regression, past {k} bars -> next {k} bars")
        add("H3", "exploratory", "BH_H3", mk, f"predictive regression k={k}: extra slope for large moves |z|>1.5")
    add("H3", "exploratory", "BH_H3", mk, "day-level: first-30-minute return vs last-30-minute return (Spearman)")
    for variant in ["no demeaning", "single overall mean"]:
        add("H3", "exploratory", "BH_H3", mk, f"omnibus Wald, sensitivity: {variant}")
    add("H3", "exploratory", "BH_H3", mk, "omnibus Wald, sensitivity: z winsorised at +/-4")
    for half in ["first half of days", "second half of days"]:
        add("H3", "exploratory", "BH_H3", mk, f"omnibus Wald, stability: {half}")
for s in STOCKS:
    add("H3", "exploratory", "BH_H3", s, "per-stock omnibus Wald")
    add("H3", "exploratory", "BH_H3", s, "day-level first-30 vs last-30 minute return (Spearman)")


def main():
    if OUT.exists():
        sys.exit(f"{OUT} exists; not overwriting.")
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print(Counter((r["hypothesis"], r["class"]) for r in rows), len(rows))
    print(Counter(r["family"] for r in rows if r["class"] != "exploratory"))


if __name__ == "__main__":
    main()
