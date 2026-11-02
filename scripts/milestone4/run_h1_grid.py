"""M4b: sensitivity of ALL H1 candidates to tail heaviness x within-period variance inequality (59 days).  ALL SIMULATED.
Grid: tails G, T10, T6, T4 x shapes flat, E (estimated), D5 (extreme), R2; 5000 simulations per cell; same methods as h1_cand.
Output: outputs/milestone4/m4b/h1_grid/    Usage: python scripts/milestone4/run_h1_grid.py [--quick]
"""
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))
import run_h1_inference as ri                                                  # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "m4b" / "h1_grid"
SEED = 20261073


def main():
    q = "--quick" in sys.argv
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files.")
    OUT.mkdir(parents=True, exist_ok=True)
    n = 8 if q else 5000
    seeds = iter(np.random.SeedSequence(SEED).spawn(1_000_000))
    nxt = lambda: int(next(seeds).generate_state(1)[0])
    names = [f"{t} {s}" for t in ("G", "T10", "T6", "T4") for s in ("flat", "E", "D5", "R2")]
    rows, sims, t0 = [], [], time.time()
    with ProcessPoolExecutor() as pool:
        for mk in ("NSE", "US"):
            for nm in names:
                spec = ri.parse(nm, mk, 59)
                df = pd.DataFrame(list(pool.map(ri.sim_cand, [(nxt(), mk, spec) for _ in range(n)], chunksize=16)))
                df.insert(0, "scenario", nm); df.insert(1, "market", mk); df.insert(2, "n_days", 59)
                sims.append(df)
                for c in [c for c in df.columns if c.endswith("|max") or c.endswith("|bonf")]:
                    k, N = int(df[c].sum()), len(df)
                    lo, hi = ri.wilson(k, N)
                    rows.append({"scenario": nm, "market": mk, "n_days": 59, "method": c.split("|")[0], "rule": c.split("|")[1], "n_sims": N,
                                 "rejection_rate": k / N, "ci95_low": lo, "ci95_high": hi})
                print(mk, nm, f"done {time.time() - t0:.0f}s", flush=True)
    pd.concat(sims).to_parquet(OUT / "h1_grid_per_simulation.parquet", index=False)
    pd.DataFrame(rows).to_csv(OUT / "h1_grid_size.csv", index=False)
    pd.Series({"master_seed": SEED, "quick": q, "n_sims_per_cell": n, "note": "ALL DATA SIMULATED"}).to_csv(OUT / "run_metadata.csv", header=["value"])
    print("COMPLETE", flush=True)


if __name__ == "__main__":
    main()
