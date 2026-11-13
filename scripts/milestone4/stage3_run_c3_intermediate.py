"""H1 calibration, STAGE 3 prerequisite: train the C3 critical values for 90 and 180 days (spec v1.1, addendum A5). Statistic T only; no candidate is evaluated.
24 cells (12 per size: tails G, T6, T4 x shapes E, D5 x NSE, US) x 25,000 = 600,000 simulations, seed 20261209, SeedSequence(20261209, spawn_key=(row, i)).
crit_n = maximum over the 12 cells of the 0.95 quantile of T (no margin). The table is FROZEN (hashed) before the validation run.   ALL DATA SIMULATED.
Output: outputs/milestone4/h1_calibration/stage3/c3_intermediate/     Usage: python scripts/milestone4/stage3_run_c3_intermediate.py   (--smoke --out <scratch> for plumbing)
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
from quantlab.research import h1_stage2 as s2, h1_stage3 as s3             # noqa: E402

OUT = c3c.S3 / "c3_intermediate"
CHUNK = 1000
_CELLS = None


def _init():
    """Worker start-up: load the 24 training cells."""
    global _CELLS
    _CELLS = pd.read_csv(c3c.C3_INTERMEDIATE_CELLS, keep_default_na=False)


def work(job):
    """Simulations [start, stop) of one training cell."""
    row, start, stop = job
    setup = c3c.cell_setup({k: _CELLS.loc[row, k] for k in _CELLS.columns})
    return row, [(i, c3c.statistic_only(setup, np.random.default_rng(s3.c3i_seed(row, i)))) for i in range(start, stop)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = Path(a.out) if a.out else OUT
    if a.smoke and (a.out is None or Path(a.out).resolve() == OUT.resolve()):
        sys.exit("--smoke needs --out pointing to a scratch folder")
    checks = c3c.verify_all(stage3_inputs=not a.smoke)
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} already has files.")
    out.mkdir(parents=True, exist_ok=True)
    cells = pd.read_csv(c3c.C3_INTERMEDIATE_CELLS, keep_default_na=False)
    assert len(cells) == 24 and int(cells.n_sims.sum()) == 600_000 and sorted(cells.n_days.unique()) == [90, 180]
    t0, done = time.perf_counter(), 0
    rows = []
    with ProcessPoolExecutor(initializer=_init) as pool:
        for row, c in cells.iterrows():
            n = 40 if a.smoke else int(c["n_sims"])
            res = [r for _, part in pool.map(work, [(row, s, min(s + CHUNK, n)) for s in range(0, n, CHUNK)]) for r in part]
            d = pd.DataFrame(res, columns=["sim", "T"]).sort_values("sim")
            d["valid"] = np.isfinite(d["T"])
            assert d["sim"].tolist() == list(range(n))
            d.to_parquet(out / f"cell_{row:02d}.parquet", index=False)
            v = d[d["valid"]]
            rows.append({"row": row, "tail": c["tail"], "shape": c["shape"], "market": c["market"], "n_days": int(c["n_days"]), "n_run": n, "n_failed": int((~d.valid).sum()),
                         "q95": s2.c3_cell_quantiles(v["T"]), "q95_se_bootstrap": s2.quantile_se(v["T"].to_numpy())})
            done += n
            print(f"row {row:02d} {c['tail']:>3} {c['shape']:>3} {c['market']:>3} {int(c['n_days'])}d n={n} failed={rows[-1]['n_failed']} q95={rows[-1]['q95']:.4f} done={done} elapsed={time.perf_counter() - t0:.0f}s", flush=True)
    res = pd.DataFrame(rows)
    res.to_csv(out / "c3_intermediate_cell_results.csv", index=False)
    table = res.groupby("n_days").apply(lambda g: pd.Series({"c3_crit": g.q95.max(), "source_row": int(g.loc[g.q95.idxmax(), "row"]), "n_cells": len(g)}), include_groups=False).reset_index()
    table["source_row"] = table["source_row"].astype(int); table["n_cells"] = table["n_cells"].astype(int)
    table.to_csv(out / "c3_intermediate_values.csv", index=False)
    crit = [("24 cells x 25,000 simulations completed, unique ids", bool((res.n_run == (40 if a.smoke else 25_000)).all())),
            ("failure rate at most 0.1% in every cell", bool(((res.n_failed / res.n_run) <= 0.001).all())),
            ("one finite value for each of 90 and 180 days", bool(sorted(table.n_days) == [90, 180] and np.isfinite(table.c3_crit).all())),
            ("seed 20261209 distinct from every other registered master seed", bool(list(s3.all_registered_masters().values()).count(s3.MASTER["c3_intermediate"]) == 1))]            # appears exactly once in the registry
    pd.DataFrame([{"criterion": k, "met": m} for k, m in crit]).to_csv(out / "c3_intermediate_criteria.csv", index=False)
    after = c3c.verify_all(stage3_inputs=not a.smoke)
    rel = lambda p: p.relative_to(c3c.sc.ROOT) if p.is_relative_to(c3c.sc.ROOT) else p
    (out / "C3_INTERMEDIATE_TABLE.sha256").write_text("".join(f"{c3c.sha256(out / f)}  {rel(out / f)}\n" for f in ("c3_intermediate_values.csv", "c3_intermediate_cell_results.csv")))
    ru = resource.getrusage(resource.RUSAGE_CHILDREN)
    pd.Series({"master_seed": s3.MASTER["c3_intermediate"], "seed_rule": "SeedSequence(20261209, spawn_key=(row, i))", "cells": 24, "simulations": done, "failed": int(res.n_failed.sum()),
               "smoke": a.smoke, "wall_seconds": round(time.perf_counter() - t0, 1), "child_cpu_user_seconds": round(ru.ru_utime, 1), "max_child_rss_mb": round(ru.ru_maxrss / 2 ** 20, 1),
               "free_gib_before": checks["free_gib"], "free_gib_after": after["free_gib"], "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
               "manifests_verified": str({k: v for k, v in checks.items() if k != "free_gib"}), "note": "ALL DATA SIMULATED; C3 training only"}).to_csv(out / "run_metadata.csv", header=["value"])
    print(table.round(4).to_string(index=False)); print("COMPLETE", done, "simulations,", int(res.n_failed.sum()), "failed", flush=True)


if __name__ == "__main__":
    main()
