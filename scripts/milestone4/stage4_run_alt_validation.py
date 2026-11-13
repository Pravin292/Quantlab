"""H1 calibration, STAGE 4, part B: VALIDATION OF C3 ON THE SIX ALTERNATIVE PROCESSES (frozen: cells_alternative_dgps.csv, 12 cells x 25,000 = 300,000 simulations).
C3 (critical value 3.298658 for 59 days) is run UNCHANGED; the baseline bootstrap-t (B = 999) is a reference. Seeds SeedSequence(20261206, spawn_key=(cell_row, i, stream)),
stream 0 data, 1 baseline bootstrap. Refuses to run unless the null check passed. Run once; incomplete cells stop the run for a report (no automatic recomputation).
Output: outputs/milestone4/h1_calibration/stage4/alt_validation/
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
import stage4_common as c4                                                 # noqa: E402

OUT = c4.S4 / "alt_validation"
CHUNK = 250
_CELLS, _CRIT = None, None


def _init(crit):
    """Worker start-up."""
    global _CELLS, _CRIT
    _CELLS, _CRIT = pd.read_csv(c4.ALT_CELLS, keep_default_na=False), crit


def work(job):
    """Simulations [start, stop) of one alternative-process cell."""
    row, start, stop = job
    cell = {k: _CELLS.loc[row, k] for k in _CELLS.columns}
    setup = c4.alt_setup(cell)
    return [{"cell_row": row, "sim": i, **c4.simulate_alt_one(setup, cell["dgp"], lambda k, i=i: np.random.SeedSequence(c4.MASTER["alt"], spawn_key=(row, i, {"data": 0, "baseline": 1}[k])), _CRIT)}
            for i in range(start, stop)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--null-outcome", default=None)
    ap.add_argument("--rows", default=None)
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    out = Path(a.out) if a.out else OUT
    if a.smoke and (a.out is None or Path(a.out).resolve() == OUT.resolve() or a.null_outcome is None):
        sys.exit("--smoke needs --out (scratch) and --null-outcome")
    checks = c4.verify_all(stage4_inputs=not a.smoke)
    of = Path(a.null_outcome) if a.smoke else c4.S4 / "null_check" / "null_check_outcome.csv"
    if not of.exists() or not bool(pd.read_csv(of).iloc[-1]["met"]):
        sys.exit("the null check has not passed (or is missing): the alternative processes are not used")
    if out.exists() and any(out.iterdir()) and not a.resume:
        sys.exit(f"{out} already has files (use --resume only to continue an interrupted run).")
    out.mkdir(parents=True, exist_ok=True)
    cells = pd.read_csv(c4.ALT_CELLS, keep_default_na=False)
    assert len(cells) == 12 and int(cells.n_sims.sum()) == 300_000
    crit = c4.c3_value_59()
    rows = [int(x) for x in a.rows.split(",")] if a.rows else list(range(12))
    t0, wall0, done, skipped = time.perf_counter(), time.time(), 0, 0
    with ProcessPoolExecutor(initializer=_init, initargs=(crit,)) as pool:
        for row in rows:
            n = a.n if (a.smoke and a.n) else int(cells.loc[row, "n_sims"])
            f = out / f"cell_{row:02d}.parquet"
            if f.exists():
                d = pd.read_parquet(f, columns=["sim"])
                if len(d) == n and d["sim"].tolist() == list(range(n)):
                    skipped += 1
                    continue
                sys.exit(f"{f.name} exists but is incomplete; stop and report (no automatic recomputation)")
            d = pd.DataFrame([r for part in pool.map(work, [(row, s, min(s + CHUNK, n)) for s in range(0, n, CHUNK)]) for r in part]).sort_values("sim")
            assert len(d) == n and d["sim"].tolist() == list(range(n))
            tmp = out / f"cell_{row:02d}.tmp"; d.to_parquet(tmp, index=False); tmp.rename(f)
            done += n
            print(f"cell {row:02d}/11 {cells.loc[row, 'dgp'][:2]} {cells.loc[row, 'market']:>3} n={n} c3={d.loc[d.valid_c3, 'reject_c3'].mean():.4f} base={d.loc[d.valid_base, 'reject_base'].mean():.4f} "
                  f"failed b/c3={int((~d.valid_base).sum())}/{int((~d.valid_c3).sum())} done={done} elapsed={time.perf_counter() - t0:.0f}s", flush=True)
    ru = resource.getrusage(resource.RUSAGE_CHILDREN)
    pd.Series({"master_seed": c4.MASTER["alt"], "seed_rule": "SeedSequence(20261206, spawn_key=(cell_row, i, stream)); stream 0 data, 1 baseline", "c3_crit_59": crit, "cells_this_session": len(rows) - skipped,
               "simulations_this_session": done, "smoke": a.smoke, "wall_seconds": round(time.perf_counter() - t0, 1), "started_unix": round(wall0), "child_cpu_user_seconds": round(ru.ru_utime, 1),
               "logical_cpus": os.cpu_count(), "python": platform.python_version(), "numpy": np.__version__, "manifests_verified": str({k: v for k, v in checks.items() if k != "free_gib"}),
               "note": "ALL DATA SIMULATED, NULL ONLY; C3 unchanged; baseline is a reference"}).to_csv(out / f"run_metadata_{int(wall0)}.csv", header=["value"])
    print("COMPLETE", done, "simulations this session;", skipped, "cells already complete", flush=True)


if __name__ == "__main__":
    main()
