"""H1 calibration, STAGE 2, step E4: MAIN DEVELOPMENT RUN.   WRITTEN IN E1; NOT RUN until the user gives a separate, explicit approval (after E3).
ALL DATA SIMULATED, NULL ONLY.  Applies the M4b baseline, C1 and C3 (frozen critical-value table) to the SAME dataset in every simulation of the 76
frozen development cells (1,780,000 simulations).  No C2 (D9).  Master seed 20261203; simulation i of cell row r uses
SeedSequence(20261203, spawn_key=(r, i, k)), k = 0 data, 1 baseline, 2 C1.  Every cell is run to completion: no early stopping (D8).
Resumable: one parquet per cell, written atomically; --resume skips completed cells whose row count and simulation indices are verified.
Safety: all manifests + the Stage 2 input manifest + the frozen C3 table must verify; at least 2 GiB free.
Output: outputs/milestone4/h1_calibration/stage2/development/
"""
import argparse
import os
import platform
import resource
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage2_common as sc                                                 # noqa: E402
from quantlab.research import h1_stage2 as s2                              # noqa: E402

OUT = sc.BASE / "stage2" / "development"
C3_DIR = sc.BASE / "stage2" / "c3_training"
CHUNK = 250
_PLAN, _CRIT = None, None


def _init(crit):
    """Worker start-up: load the plan and the frozen C3 critical values {n_days: crit}."""
    global _PLAN, _CRIT
    _PLAN, _CRIT = sc.load_plan(), crit


def work(job):
    """Simulations [start, stop) of one development cell; returns a list of per-simulation result rows."""
    row, start, stop = job
    cell = {k: _PLAN.loc[row, k] for k in _PLAN.columns}
    setup = sc.cell_setup(cell)
    crit = _CRIT[int(cell["n_days"])]
    rows = []
    for i in range(start, stop):
        r = sc.simulate_all(setup, lambda k, i=i: s2.dev_seed(row, i, k), crit)
        rows.append({"cell_row": row, "sim": i, **r})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--c3-table", default=None, help="smoke only: a scratch c3_critical_values.csv")
    ap.add_argument("--rows", default=None, help="smoke only: comma-separated dev_rows")
    ap.add_argument("--n", type=int, default=None, help="smoke only: simulations per cell")
    a = ap.parse_args()
    out = Path(a.out) if a.out else OUT
    if a.smoke and (a.out is None or Path(a.out).resolve() == OUT.resolve() or a.c3_table is None):
        sys.exit("--smoke needs --out (scratch) and --c3-table")
    checks = sc.verify_all(require_stage2_inputs=not a.smoke)
    if not a.smoke:
        sc.verify_manifest(C3_DIR / "C3_TABLE.sha256", 2)                  # the frozen C3 table must be unchanged
    c3_path = Path(a.c3_table) if a.smoke else C3_DIR / "c3_critical_values.csv"
    crit = pd.read_csv(c3_path).set_index("n_days")["c3_crit"].to_dict()
    assert set(crit) == {59, 125, 250} and all(np.isfinite(list(crit.values())))
    if out.exists() and any(out.iterdir()) and not a.resume:
        sys.exit(f"{out} already has files (use --resume to continue an interrupted run).")
    out.mkdir(parents=True, exist_ok=True)
    plan = sc.load_plan()
    rows = [int(x) for x in a.rows.split(",")] if a.rows else list(plan.dev_row)
    t0, wall0, done, skipped = time.perf_counter(), time.time(), 0, 0
    with ProcessPoolExecutor(initializer=_init, initargs=(crit,)) as pool:
        for row in rows:
            c = plan.loc[row]
            n = a.n if a.smoke and a.n else int(c["n_sims"])
            f = out / f"cell_{row:02d}.parquet"
            if f.exists():
                d = pd.read_parquet(f, columns=["sim"])
                if len(d) == n and d["sim"].tolist() == list(range(n)):
                    skipped += 1
                    continue
                f.unlink()                                                  # incomplete file: recompute this cell from scratch
            jobs = [(row, s, min(s + CHUNK, n)) for s in range(0, n, CHUNK)]
            d = pd.DataFrame([r for part in pool.map(work, jobs) for r in part]).sort_values("sim")
            assert len(d) == n and d["sim"].tolist() == list(range(n)), f"cell {row}: wrong simulation count"
            tmp = out / f"cell_{row:02d}.tmp"
            d.to_parquet(tmp, index=False)
            tmp.rename(f)                                                   # atomic: a cell file is either complete or absent
            done += n
            print(f"cell {row:02d}/75 {c['tail']:>3} {c['shape']:>4} {c['market']:>3} n_days={c['n_days']:>3} dep={c['dependence']:>9} sd={c['day_vol_sd']} n={n} "
                  f"rej base={d.loc[d.valid_base, 'reject_base'].mean():.4f} c1={d.loc[d.valid_c1, 'reject_c1'].mean():.4f} c3={d.loc[d.valid_c3, 'reject_c3'].mean():.4f} "
                  f"failed b/c1/c3={int((~d.valid_base).sum())}/{int((~d.valid_c1).sum())}/{int((~d.valid_c3).sum())} "
                  f"done={done} elapsed={time.perf_counter() - t0:.0f}s", flush=True)
    ru = resource.getrusage(resource.RUSAGE_CHILDREN)
    pd.Series({"master_seed": s2.MASTER["development"], "seed_rule": "SeedSequence(20261203, spawn_key=(dev_row, i, k)); k=0 data, 1 baseline, 2 C1",
               "cells_completed_this_session": len(rows) - skipped, "cells_skipped_already_complete": skipped, "simulations_this_session": done,
               "c3_crit": str(crit), "smoke": a.smoke, "wall_seconds_this_session": round(time.perf_counter() - t0, 1), "started_unix": round(wall0),
               "child_cpu_user_seconds": round(ru.ru_utime, 1), "max_child_rss_mb": round(ru.ru_maxrss / 2 ** 20, 1), "logical_cpus": os.cpu_count(),
               "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "machine": platform.platform(),
               "manifests_verified": str({k: v for k, v in checks.items() if k != "free_gib"}), "methods": "baseline (B=999), C1 (R=499), C3 (frozen table); no C2",
               "note": "ALL DATA SIMULATED, NULL ONLY"}).to_csv(out / f"run_metadata_{int(wall0)}.csv", header=["value"])
    print("COMPLETE", done, "simulations this session;", skipped, "cells already complete", flush=True)


if __name__ == "__main__":
    main()
