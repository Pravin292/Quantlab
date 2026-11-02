"""H1 calibration, STAGE 2, step E3: C3 TRAINING RUN ONLY (no baseline, no C1, no C2, no development data).   ALL DATA SIMULATED, NULL ONLY.

Simulates the 68 gated development cells (25,000 datasets each = 1,700,000) with master seed 20261202, computes the statistic T = max |t| of each
dataset, and builds the C3 critical-value table: crit_n = maximum over the cells of size n of the 0.95 quantile of T (no margin).
Then FREEZES the table (C3_TABLE.sha256).  Stops there: the main development run (E4) is a separate, separately approved step.
Safety: all frozen manifests and the Stage 2 input manifest must verify; the output folder must be empty; at least 2 GiB of disk must be free.
Output: outputs/milestone4/h1_calibration/stage2/c3_training/
Usage : python scripts/milestone4/stage2_run_c3_training.py            (the real run)
        python scripts/milestone4/stage2_run_c3_training.py --smoke --out <scratch folder>   (40 simulations per cell; NOT results)
"""
import argparse
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
from quantlab.research import h1_calibration_v11 as v11, h1_stage2 as s2   # noqa: E402

OUT = sc.BASE / "stage2" / "c3_training"
C3_CELLS = sc.BASE / "stage2_plan" / "stage2_c3_training_cells.csv"
CHUNK = 1000
_PLAN = None


def _init():
    """Worker start-up: load the development plan once."""
    global _PLAN
    _PLAN = sc.load_plan()


def work(job):
    """Simulations [start, stop) of one training cell: returns (sim index, T, valid) tuples."""
    row, start, stop = job
    cell = {k: _PLAN.loc[row, k] for k in _PLAN.columns}
    setup = sc.cell_setup(cell)
    res = []
    for i in range(start, stop):
        t = sc.statistic_only(setup, np.random.default_rng(s2.c3_seed(row, i)))
        res.append((i, t, bool(np.isfinite(t))))
    return row, res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = Path(a.out) if a.out else OUT
    if a.smoke and (a.out is None or Path(a.out).resolve() == OUT.resolve()):
        sys.exit("--smoke needs --out pointing to a scratch folder")
    checks = sc.verify_all(require_stage2_inputs=not a.smoke)
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} already has files.")
    out.mkdir(parents=True, exist_ok=True)
    cells = pd.read_csv(C3_CELLS, keep_default_na=False)
    assert len(cells) == 68 and int(cells.n_sims.sum()) == 1_700_000 and (cells.seed_master == s2.MASTER["c3_training"]).all()
    n_per = 40 if a.smoke else None
    t0, wall0 = time.perf_counter(), time.time()
    done = 0
    with ProcessPoolExecutor(initializer=_init) as pool:
        for _, c in cells.iterrows():
            row, n = int(c["dev_row"]), (n_per or int(c["n_sims"]))
            jobs = [(row, s, min(s + CHUNK, n)) for s in range(0, n, CHUNK)]
            recs = [r for _, part in pool.map(work, jobs) for r in part]
            d = pd.DataFrame(recs, columns=["sim", "T", "valid"]).sort_values("sim")
            assert len(d) == n and d["sim"].tolist() == list(range(n)), f"cell {row}: wrong simulation count"
            d.to_parquet(out / f"cell_{row:02d}.parquet", index=False)
            done += n
            print(f"dev_row {row:02d} {c['tail']:>3} {c['shape']:>4} {c['market']:>3} n_days={c['n_days']:>3} dep={c['dependence']:>9} sd={c['day_vol_sd']} n={n} "
                  f"failed={int((~d.valid).sum())} q95={s2.c3_cell_quantiles(d['T']):.4f} total={done} elapsed={time.perf_counter() - t0:.0f}s", flush=True)

    # ---- per-cell results and the table
    rows = []
    for _, c in cells.iterrows():
        d = pd.read_parquet(out / f"cell_{int(c['dev_row']):02d}.parquet")
        v = d[d["valid"]]
        rows.append({**{k: c[k] for k in ("dev_row", "tail", "shape", "market", "n_days", "dependence", "day_vol_sd", "tier")},
                     "n_planned": int(c["n_sims"]) if not a.smoke else n_per, "n_run": len(d), "n_failed": int((~d["valid"]).sum()), "n_valid": len(v),
                     "fail_rate": float((~d["valid"]).mean()), "q95": s2.c3_cell_quantiles(v["T"]), "q95_se_bootstrap": s2.quantile_se(v["T"].to_numpy()),
                     "T_mean": float(v["T"].mean()), "T_max": float(v["T"].max())})
    res = pd.DataFrame(rows)
    table = s2.c3_table(res)
    crit = table.set_index("n_days")["c3_crit"]
    # in-sample check ONLY (the same data the table was built from): upper-limit statuses of C3 on its own training data
    ins = []
    for _, r in res.iterrows():
        v = pd.read_parquet(out / f"cell_{int(r['dev_row']):02d}.parquet")
        v = v[v["valid"]]
        k = int((v["T"] > crit[int(r["n_days"])]).sum())
        cl = v11.classify_cell(k, len(v), r["tier"], c3_mode=True)
        ins.append({"c3_crit_used": float(crit[int(r["n_days"])]), "in_sample_rejections": k, "in_sample_rate": cl["p_hat"], "in_sample_wilson_low": cl["wilson_low"],
                    "in_sample_wilson_high": cl["wilson_high"], "in_sample_status_c3_upper_only": cl["status"],
                    "q95_gap_to_crit_in_se": float((crit[int(r["n_days"])] - r["q95"]) / r["q95_se_bootstrap"])})
    res = pd.concat([res, pd.DataFrame(ins)], axis=1)
    res.to_csv(out / "c3_training_cell_results.csv", index=False)
    table.to_csv(out / "c3_critical_values.csv", index=False)

    # ---- predefined criteria for the training run
    seeds_ok = s2.MASTER["c3_training"] not in [v for k, v in s2.RESERVED_MASTERS.items() if k != "c3_training"]
    crit_list = [
        ("all 68 cells x planned simulations completed, simulation indices unique", bool((res.n_run == res.n_planned).all() and len(res) == 68)),
        ("numerical failure rate <= 0.1% in every cell (D6)", bool((res.fail_rate <= s2.FAIL_RATE_LIMIT + 1e-15).all())),
        ("one finite critical value for each of the sample sizes 59, 125, 250", bool(sorted(table.n_days) == [59, 125, 250] and np.isfinite(table.c3_crit).all())),
        ("training seed 20261202 distinct from every other registered master seed", bool(seeds_ok)),
        ("in-sample C3 rate within the upper limit in every cell (5.5% tier A, 6.0% tier B; uninformative about validity: same data)",
         bool(res["in_sample_status_c3_upper_only"].str.startswith("PASS").all())),
        ("frozen v1, v1.1, Stage 1 and Stage 2 input manifests verified before the run", True),
    ]
    pd.DataFrame([{"criterion": c, "met": m} for c, m in crit_list]).to_csv(out / "c3_training_criteria.csv", index=False)

    # ---- freeze the table and record resources
    verify = sc.verify_all(require_stage2_inputs=not a.smoke)          # re-verify after the run
    (out / "C3_TABLE.sha256").write_text("".join(f"{sc.sha256(out / f)}  {(out / f).relative_to(sc.ROOT) if (out / f).is_relative_to(sc.ROOT) else (out / f)}\n"
                                                    for f in ("c3_critical_values.csv", "c3_training_cell_results.csv")))
    ru = resource.getrusage(resource.RUSAGE_CHILDREN)
    size = sum(f.stat().st_size for f in out.glob("*"))
    pd.Series({"master_seed": s2.MASTER["c3_training"], "seed_rule": "SeedSequence(20261202, spawn_key=(dev_row, i))", "cells": len(cells),
               "simulations": done, "failed_simulations": int(res.n_failed.sum()), "smoke": a.smoke, "wall_seconds": round(time.perf_counter() - t0, 1),
               "started_unix": round(wall0), "child_cpu_user_seconds": round(ru.ru_utime, 1), "child_cpu_system_seconds": round(ru.ru_stime, 1),
               "max_child_rss_mb": round(ru.ru_maxrss / 2 ** 20, 1), "output_mb": round(size / 2 ** 20, 1), "logical_cpus": __import__("os").cpu_count(),
               "free_gib_before": checks["free_gib"], "free_gib_after": verify["free_gib"], "python": platform.python_version(), "numpy": np.__version__,
               "pandas": pd.__version__, "machine": platform.platform(), "manifests_verified_before": str({k: v for k, v in checks.items() if k != "free_gib"}),
               "manifests_verified_after": str({k: v for k, v in verify.items() if k != "free_gib"}),
               "note": "ALL DATA SIMULATED, NULL ONLY; C3 training only; no baseline, C1 or C2 was run"}).to_csv(out / "run_metadata.csv", header=["value"])
    print(table.round(4).to_string(index=False))
    print("COMPLETE", done, "simulations,", int(res.n_failed.sum()), "failed", flush=True)


if __name__ == "__main__":
    main()
