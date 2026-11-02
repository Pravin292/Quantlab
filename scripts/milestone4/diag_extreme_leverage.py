"""M4b Task A, factor 5: sensitivity to INDIVIDUAL EXTREME observations, without altering any data.   ALL SIMULATED.

The replace-the-largest-returns diagnostic in run_h1_inference.py (columns 'minus1', 'minus5') turned out to be confounded: under
heterogeneous shapes the largest squared returns sit in the high-variance period, so replacing them changes the true period
variances and the null is no longer true (even a Gaussian E cell then rejects 10-50%). It is reported but NOT used for attribution.
Instead: for every simulated dataset compute the LEVERAGE of its most influential day,
    leverage = max over periods of  max_d X[d,p] / sum_d X[d,p]
(the largest share any single day contributes to a period total of mean squares), and report the as-run rejection rate of
rom_t / diff_t (max rule, B=999) within leverage quartiles of the same scenario. Data are not modified.
Output: outputs/milestone4/m4b/h1_leverage/
"""
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))
from quantlab.research import direct_sim as ds, h1_rms2                    # noqa: E402
import run_h1_inference as ri                                              # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "m4b" / "h1_leverage"
SEED = 20261074


def sim(args):
    seed, mk, spec = args
    r2, rng = ri.gen(seed, mk, spec)
    M = ds.period_matrix(r2, ds.used_slot_index(ri.MARKETS[mk]))
    lev = float((M / M.sum(axis=0)).max())
    return {"seed": seed, "leverage": lev, "rom_t|max": h1_rms2.bootstrap_t(M, rng, "rom", B=999)["reject_max"],
            "diff_t|max": h1_rms2.bootstrap_t(M, rng, "diff", B=999)["reject_max"]}


def main():
    q = "--quick" in sys.argv
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files.")
    OUT.mkdir(parents=True, exist_ok=True)
    n = 40 if q else 20000
    seeds = iter(np.random.SeedSequence(SEED).spawn(1_000_000))
    nxt = lambda: int(next(seeds).generate_state(1)[0])
    rows, sims = [], []
    with ProcessPoolExecutor() as pool:
        for mk in ("NSE", "US"):
            for nm in ("G E", "T4 flat", "T4 E", "T4 D5"):
                spec = ri.parse(nm, mk, 59)
                df = pd.DataFrame(list(pool.map(sim, [(nxt(), mk, spec) for _ in range(n)], chunksize=32)))
                df.insert(0, "scenario", nm); df.insert(1, "market", mk)
                sims.append(df)
                df["q"] = pd.qcut(df["leverage"], 4, labels=["Q1 lowest", "Q2", "Q3", "Q4 highest"])
                for qn, g in df.groupby("q", observed=True):
                    for c in ("rom_t|max", "diff_t|max"):
                        k, N = int(g[c].sum()), len(g)
                        lo, hi = ri.wilson(k, N)
                        rows.append({"scenario": nm, "market": mk, "leverage_quartile": qn, "test": c.split("|")[0], "n_sims": N,
                                     "mean_leverage": g["leverage"].mean(), "rejection_rate": k / N, "ci95_low": lo, "ci95_high": hi})
                print(mk, nm, "done", flush=True)
    pd.concat(sims).to_parquet(OUT / "h1_leverage_per_simulation.parquet", index=False)
    pd.DataFrame(rows).to_csv(OUT / "h1_leverage_by_quartile.csv", index=False)
    pd.Series({"master_seed": SEED, "n_sims_per_cell": n, "note": "ALL DATA SIMULATED; data not modified"}).to_csv(OUT / "run_metadata.csv", header=["value"])
    print("COMPLETE")


if __name__ == "__main__":
    main()
