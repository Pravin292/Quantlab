"""STAGE 6 part A (docs/42): size of the frozen C3 under dependence. 96 cells x 25,000 simulations (H0 true), C3 at its frozen critical value + the old bootstrap-t as a reference
on the same datasets. Gated cells = dependence levels S0-S3; S4 and S5 are reported, never gated. Master seed 20261401. Write-once output: outputs/milestone4/stage6/part_a/.
--smoke runs a few simulations into a scratch folder and skips the Stage 6 manifest check."""
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
from quantlab.research import stage6 as s6                                  # noqa: E402

CELLS = s6.size_cells()
CHUNK = 500


def work(job):
    """Simulations [start, stop) of one cell."""
    row, start, stop = job
    cell = CELLS.iloc[row].to_dict()
    setup, crit = sc6.cell_setup(cell), sc6.c3_crit(cell["n_days"])
    out = []
    for i in range(start, stop):
        r = c3c.simulate_one(setup, lambda k, i=i: s6.size_seed(row, i, k), crit)
        out.append({"row": row, "sim": i, "T": r["T"], "valid_c3": r["valid_c3"], "reject_c3": r["reject_c3"], "valid_base": r["valid_base"], "reject_base": r["reject_base"]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--n", type=int, default=s6.N_SIMS_SIZE)
    a = ap.parse_args()
    out = Path(a.out) if a.out else sc6.OUT / "part_a"
    if a.smoke and (a.out is None or out.resolve() == (sc6.OUT / "part_a").resolve()):
        sys.exit("--smoke needs --out (scratch)")
    n = a.n if a.smoke else s6.N_SIMS_SIZE
    sc6.verify_all(smoke=a.smoke)
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} already has files: single-run rule.")
    (out / "cells").mkdir(parents=True, exist_ok=True)
    t0, rows = time.perf_counter(), []
    with ProcessPoolExecutor() as pool:
        for row in range(len(CELLS)):
            c = CELLS.iloc[row]
            d = pd.DataFrame([r for part in pool.map(work, [(row, s, min(s + CHUNK, n)) for s in range(0, n, CHUNK)]) for r in part]).sort_values("sim")
            d.to_parquet(out / "cells" / f"cell_{row:02d}.parquet", index=False)
            v = d[d.valid_c3]
            k, nn = int(v.reject_c3.sum()), len(v)
            st = s6.size_status(k, nn, c["tail"])
            vb = d[d.valid_base]
            rows.append({**c.to_dict(), "n_sims": n, "n_valid_c3": nn, "n_failed_c3": len(d) - nn, "k_c3": k, "rate_c3": st["p_hat"], "wilson_low": st["wilson_low"],
                         "wilson_high": st["wilson_high"], "status": st["status"] if c["gated"] else "REPORTED_" + st["status"],
                         "rate_base": float(vb.reject_base.mean()) if len(vb) else float("nan"), "n_valid_base": len(vb)})
            print(f"cell {row:02d} {c['market']} {c['shape']} {c['tail']} n={c['n_days']} {c['level']}: c3={st['p_hat']:.4f} {st['status']} base={rows[-1]['rate_base']:.4f} elapsed={time.perf_counter() - t0:.0f}s", flush=True)
    res = pd.DataFrame(rows)
    res.to_csv(out / "size_by_cell.csv", index=False)
    gated = res[res.gated].assign(status=lambda x: x.status)
    pd.DataFrame([{"outcome": s6.part_a_outcome(gated), "gated_cells": len(gated), "n_PASS": int((gated.status == "PASS").sum()), "n_PASS_AMBIGUOUS": int((gated.status == "PASS_AMBIGUOUS").sum()),
                   "n_FAIL_AMBIGUOUS": int((gated.status == "FAIL_AMBIGUOUS").sum()), "n_FAIL": int((gated.status == "FAIL").sum()),
                   "highest_gated_rate": float(gated.rate_c3.max()), "highest_reported_rate": float(res[~res.gated].rate_c3.max())}]).to_csv(out / "part_a_outcome.csv", index=False)
    pd.Series({"master_seed": s6.MASTER["size"], "n_per_cell": n, "smoke": a.smoke, "wall_seconds": round(time.perf_counter() - t0, 1),
               "note": "ALL DATA SIMULATED"}).to_csv(out / "run_metadata.csv", header=["value"])
    print("COMPLETE", s6.part_a_outcome(gated))


if __name__ == "__main__":
    main()
