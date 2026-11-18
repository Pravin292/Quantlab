"""STAGE 6 part B (docs/42): power curve of the frozen C3 (H1 true: open and close volatility = mult x middle). 120 cells x 10,000 simulations, shape R2, tail T4, five sample sizes
(all with frozen C3 values), two dependence levels. Diagnostic only; nothing is gated or selected. Master seed 20261402. Write-once output: outputs/milestone4/stage6/part_b/."""
import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage6_common as sc6                                                # noqa: E402
import stage3_common as c3c                                                # noqa: E402
from quantlab.research import h1_calibration_v11 as v11, stage6 as s6       # noqa: E402

CELLS = s6.power_cells()
CHUNK = 1000


def work(job):
    row, start, stop = job
    cell = CELLS.iloc[row].to_dict()
    setup, crit = sc6.cell_setup(cell, mult=cell["mult"]), sc6.c3_crit(cell["n_days"])
    return [{"row": row, "sim": i, "T": c3c.statistic_only(setup, np.random.default_rng(s6.power_seed(row, i)))} for i in range(start, stop)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--n", type=int, default=s6.N_SIMS_POWER)
    a = ap.parse_args()
    out = Path(a.out) if a.out else sc6.OUT / "part_b"
    if a.smoke and (a.out is None or out.resolve() == (sc6.OUT / "part_b").resolve()):
        sys.exit("--smoke needs --out (scratch)")
    n = a.n if a.smoke else s6.N_SIMS_POWER
    sc6.verify_all(smoke=a.smoke)
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} already has files: single-run rule.")
    out.mkdir(parents=True, exist_ok=True)
    t0, rows = time.perf_counter(), []
    with ProcessPoolExecutor() as pool:
        for row in range(len(CELLS)):
            c = CELLS.iloc[row]
            T = np.array([r["T"] for part in pool.map(work, [(row, s, min(s + CHUNK, n)) for s in range(0, n, CHUNK)]) for r in part])
            crit = sc6.c3_crit(c["n_days"])
            valid = np.isfinite(T)
            k, nn = int((T[valid] > crit).sum()), int(valid.sum())
            lo, hi = (float(x) for x in v11.wilson_interval(k, nn))
            rows.append({**c.to_dict(), "n_sims": n, "n_valid": nn, "n_failed": n - nn, "crit": crit, "k_reject": k, "power": k / nn, "wilson_low": lo, "wilson_high": hi})
            print(f"cell {row:03d} {c.market} n={c.n_days} {c.level} x{c.mult}: power={k / nn:.4f} elapsed={time.perf_counter() - t0:.0f}s", flush=True)
    res = pd.DataFrame(rows)
    res.to_csv(out / "power_by_cell.csv", index=False)
    mde = []
    for (mk, nd, lv), g in res.groupby(["market", "n_days", "level"], sort=False):
        m = s6.min_detectable(g["mult"], g["power"])
        mde.append({"market": mk, "n_days": nd, "level": lv, "min_detectable_mult": m["value"], "kind": m["kind"], "power_target": s6.POWER_TARGET})
    pd.DataFrame(mde).to_csv(out / "min_detectable_effect.csv", index=False)
    pd.Series({"master_seed": s6.MASTER["power"], "n_per_cell": n, "smoke": a.smoke, "wall_seconds": round(time.perf_counter() - t0, 1),
               "note": "ALL DATA SIMULATED; diagnostic only; no gate"}).to_csv(out / "run_metadata.csv", header=["value"])
    print("COMPLETE")


if __name__ == "__main__":
    main()
