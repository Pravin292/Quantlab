"""H1 calibration, STAGE 3: LOCKED VALIDATION, RUN ONCE. Candidate = C3 (frozen critical values); the M4b baseline runs on the same datasets as a REFERENCE only.
No C1 (not selected), no C2. 96 frozen cells, 2,280,000 simulations; seeds SeedSequence(master, spawn_key=(val_row, i, stream)), master 20261204 (rows 0-75) and
20261205 (rows 76-95), stream 0 data, 1 baseline. NO retuning: if the result is unfavourable it is reported, the cells are not re-run.
Safety: all manifests, the Stage 3 input manifest and both frozen C3 tables must verify; >= 2 GiB free; refuses to start on a non-empty folder unless --resume,
and refuses to recompute a cell that is already complete.     Output: outputs/milestone4/h1_calibration/stage3/validation/
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
import stage3_common as c3c                                                # noqa: E402
from quantlab.research import h1_stage3 as s3                              # noqa: E402

OUT = c3c.S3 / "validation"
CHUNK = 250
_CELLS, _TAB2, _TAB3 = None, None, None


def _init(tab2, tab3):
    """Worker start-up: load the frozen grid and the two frozen C3 tables."""
    global _CELLS, _TAB2, _TAB3
    _CELLS, _TAB2, _TAB3 = c3c.load_validation_cells(), tab2, tab3


def work(job):
    """Simulations [start, stop) of one validation cell."""
    row, start, stop = job
    cell = {k: _CELLS.loc[row, k] for k in _CELLS.columns}
    setup = c3c.cell_setup(cell)
    crit = s3.c3_value(int(cell["n_days"]), _TAB2, _TAB3)
    return [{"val_row": row, "sim": i, **c3c.simulate_one(setup, lambda k, i=i: s3.val_seed(row, i, k), crit)} for i in range(start, stop)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--c3-table-59-250", default=None)
    ap.add_argument("--c3-table-90-180", default=None)
    ap.add_argument("--rows", default=None)
    ap.add_argument("--n", type=int, default=None)
    a = ap.parse_args()
    out = Path(a.out) if a.out else OUT
    if a.smoke and (a.out is None or Path(a.out).resolve() == OUT.resolve() or not (a.c3_table_59_250 and a.c3_table_90_180)):
        sys.exit("--smoke needs --out (scratch) and both --c3-table-* files")
    checks = c3c.verify_all(stage3_inputs=not a.smoke, c3_intermediate=not a.smoke)
    t2 = pd.read_csv(Path(a.c3_table_59_250) if a.smoke else c3c.STAGE2_C3_TABLE).set_index("n_days")["c3_crit"].to_dict()
    t3 = pd.read_csv(Path(a.c3_table_90_180) if a.smoke else c3c.C3I_TABLE).set_index("n_days")["c3_crit"].to_dict()
    assert set(t2) == {59, 125, 250} and set(t3) == {90, 180} and all(np.isfinite(list(t2.values()) + list(t3.values())))
    if out.exists() and any(out.iterdir()) and not a.resume:
        sys.exit(f"{out} already has files (use --resume only to continue an interrupted run).")
    out.mkdir(parents=True, exist_ok=True)
    cells = c3c.load_validation_cells()
    assert len(cells) == 96 and int(cells.n_sims.sum()) == 2_280_000
    rows = [int(x) for x in a.rows.split(",")] if a.rows else list(range(96))
    t0, wall0, done, skipped = time.perf_counter(), time.time(), 0, 0
    with ProcessPoolExecutor(initializer=_init, initargs=(t2, t3)) as pool:
        for row in rows:
            c = cells.loc[row]
            n = a.n if (a.smoke and a.n) else int(c["n_sims"])
            f = out / f"cell_{row:02d}.parquet"
            if f.exists():
                d = pd.read_parquet(f, columns=["sim"])
                if len(d) == n and d["sim"].tolist() == list(range(n)):
                    skipped += 1
                    continue
                sys.exit(f"{f.name} exists but is incomplete; stop and report (no automatic recomputation of a locked cell)")
            d = pd.DataFrame([r for part in pool.map(work, [(row, s, min(s + CHUNK, n)) for s in range(0, n, CHUNK)]) for r in part]).sort_values("sim")
            assert len(d) == n and d["sim"].tolist() == list(range(n)), f"cell {row}: wrong simulation count"
            tmp = out / f"cell_{row:02d}.tmp"
            d.to_parquet(tmp, index=False)
            tmp.rename(f)
            done += n
            print(f"cell {row:02d}/95 {c['tail']:>3} {c['shape']:>4} {c['market']:>3} n_days={int(c['n_days']):>3} dep={c['dependence']:>9} sd={c['day_vol_sd']} n={n} "
                  f"rej base={d.loc[d.valid_base, 'reject_base'].mean():.4f} c3={d.loc[d.valid_c3, 'reject_c3'].mean():.4f} failed b/c3={int((~d.valid_base).sum())}/{int((~d.valid_c3).sum())} "
                  f"done={done} elapsed={time.perf_counter() - t0:.0f}s", flush=True)
    ru = resource.getrusage(resource.RUSAGE_CHILDREN)
    pd.Series({"masters": f"{s3.MASTER['validation_cells']} (rows 0-75), {s3.MASTER['validation_intermediate']} (rows 76-95)", "seed_rule": "SeedSequence(master, spawn_key=(val_row, i, stream)); stream 0 data, 1 baseline",
               "cells_this_session": len(rows) - skipped, "cells_skipped_complete": skipped, "simulations_this_session": done, "c3_values": str({**t2, **t3}), "smoke": a.smoke,
               "wall_seconds_this_session": round(time.perf_counter() - t0, 1), "started_unix": round(wall0), "child_cpu_user_seconds": round(ru.ru_utime, 1), "max_child_rss_mb": round(ru.ru_maxrss / 2 ** 20, 1),
               "logical_cpus": os.cpu_count(), "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "machine": platform.platform(),
               "manifests_verified": str({k: v for k, v in checks.items() if k != "free_gib"}), "methods": "C3 (candidate, frozen values) + baseline B=999 (reference); no C1, no C2",
               "note": "ALL DATA SIMULATED, NULL ONLY; locked validation, run once"}).to_csv(out / f"run_metadata_{int(wall0)}.csv", header=["value"])
    print("COMPLETE", done, "simulations this session;", skipped, "cells already complete", flush=True)


if __name__ == "__main__":
    main()
