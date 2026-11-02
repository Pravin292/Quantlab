"""Verify planned vs actual simulation counts for M4b from the saved per-simulation files; check seed uniqueness (within a file
and across all M4b files), missing values in decision columns, and that the aborted early H2 start left no results.
The PLAN below is written independently of the runner scripts (from the task specification)."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "outputs" / "milestone4" / "m4b"
plan = {}
def add(part, file, rows):
    plan[part] = (file, rows)
nulls59 = ["G flat", "T4 flat", "G E", "T6 E", "T4 E", "T4 E nodayfactor", "T4 R2", "G D5", "T4 D5", "T4 E dep"]
pow59 = ["T4 E x1.1", "T4 E x1.2", "T4 E x1.3", "T4 flat x1.1", "T4 flat x1.2"]
diag = [f"{t} {s}" for t in ("G", "T10", "T6", "T4") for s in ("flat", "E", "D5")] + [f"T4 Etau{v}" for v in ("0.37", "1.0", "2.0", "4.0")] + ["T4 Eopen", "T4 Eclose", "T4 E nodayfactor", "T4 D5 nodayfactor"]
add("h1_diag", "h1_diag/h1_diag_per_simulation.parquet", {(s, m, 59): 8000 for s in diag for m in ("NSE", "US")})
add("h1_cand", "h1_cand/h1_cand_per_simulation.parquet", {**{(s, m, 59): 10000 for s in nulls59 for m in ("NSE", "US")}, **{(s, m, 59): 2000 for s in pow59 for m in ("NSE", "US")}})
add("h1_size", "h1_size/h1_size_per_simulation.parquet", {**{(s, m, nd): 5000 for nd in (125, 250) for s in ("T4 flat", "T4 E", "T4 D5", "T4 E dep", "G E") for m in ("NSE", "US")},
                                                       **{(s, m, nd): 1000 for nd in (125, 250) for s in ("T4 E x1.1", "T4 E x1.2") for m in ("NSE", "US")}})
add("h1_grid", "h1_grid/h1_grid_per_simulation.parquet", {(f"{t} {s}", m, 59): 5000 for t in ("G", "T10", "T6", "T4") for s in ("flat", "E", "D5", "R2") for m in ("NSE", "US")})
eff59 = ["null", "vol x0.90", "vol x1.05", "vol x1.10", "vol x1.25", "cont -0.10", "cont -0.05", "cont -0.02", "cont +0.02", "cont +0.05", "cont +0.10"]
add("h2_p59", "h2_p59/h2_p59_per_simulation.parquet", {(f"{e}|{dp}", m, 59): 120 for e in eff59 for dp in ("X0 independent", "X3 estimated dependence") for m in ("NSE", "US")})
add("h2_pbig", "h2_pbig/h2_pbig_per_simulation.parquet", {(f"{e}|X3 estimated dependence", m, nd): 80 for e in ("null", "vol x1.05", "vol x1.10", "cont +0.02", "cont +0.05") for nd in (125, 250) for m in ("NSE", "US")})
rows, allseeds = [], []
for part, (f, exp) in plan.items():
    p = B / f
    if not p.exists():
        rows.append({"part": part, "status": "MISSING FILE"}); continue
    d = pd.read_parquet(p)
    if part.startswith("h2"):
        d["scenario"] = d["effect"] + "|" + d["dependence"]
    got = d.groupby(["scenario", "market", "n_days"]).size().to_dict()
    mism = {k: (exp.get(k), got.get(k)) for k in set(exp) | set(got) if exp.get(k) != got.get(k)}
    dec = [c for c in d.columns if c.endswith(("|max", "|bonf", "|p_wild", "|p_t"))]
    allseeds.append(d["seed"].to_numpy())
    rows.append({"part": part, "status": "OK" if not mism else "MISMATCH", "planned_total": sum(exp.values()), "actual_total": len(d),
                 "cells_planned": len(exp), "cells_found": len(got), "cells_with_wrong_count": len(mism),
                 "unique_seeds_in_file": int(d["seed"].nunique()), "duplicate_seeds_in_file": int(len(d) - d["seed"].nunique()),
                 "missing_values_in_decision_columns": int(d[dec].isna().sum().sum()), "detail": str(list(mism.items())[:3])})
seeds = np.concatenate(allseeds) if allseeds else np.array([])
rows.append({"part": "ALL FILES", "status": "OK" if len(seeds) == len(np.unique(seeds)) else "DUPLICATE SEEDS ACROSS FILES",
             "actual_total": len(seeds), "unique_seeds_in_file": int(len(np.unique(seeds)))})
ab = B / "h2_p59_ABORTED_EARLY_START.log"
rows.append({"part": "aborted early H2 start", "status": "ZERO RESULTS" if ab.exists() and ab.stat().st_size == 0 else "CHECK", "detail": f"log bytes={ab.stat().st_size if ab.exists() else 'absent'}; its output folder was empty and removed"})
out = pd.DataFrame(rows)
(B / "verification").mkdir(exist_ok=True)
out.to_csv(B / "verification" / "planned_vs_actual_counts.csv", index=False)
pd.set_option("display.width", 250, "display.max_columns", 20)
print(out.drop(columns=["detail"], errors="ignore").to_string(index=False))
