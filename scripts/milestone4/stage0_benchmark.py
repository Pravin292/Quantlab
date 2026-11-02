"""H1 calibration, STAGE 0: compute benchmark ONLY. Measures run time of each candidate on a few simulated null datasets.
These runs are NOT calibration results (n is tiny; no rejection rates are recorded or interpreted).  ALL DATA SIMULATED.
Output (new folder): outputs/milestone4/h1_calibration/stage0/benchmark/
"""
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from quantlab.calendars import NSE                                         # noqa: E402
from quantlab.research import direct_sim as ds, dependence as dep, h1_calibration as hc  # noqa: E402
from quantlab.research.h1_rms2 import bootstrap_t                          # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "h1_calibration" / "stage0" / "benchmark"
IDX = ds.used_slot_index(NSE)
PROFILE = dep.shaped_profile(NSE, 2.0, 2.0, 2.0, 2.0)
SEED = 20261100
N_SIM = 20


def data(seed, n_days, df=4.0):
    rng = np.random.default_rng(seed)
    r2 = ds.simulate_returns_sq(NSE, 3, n_days, rng, profile=PROFILE, df=df, day_vol_sd=0.3)
    return hc.to_used(r2, IDX)


def timed(fn, reps):
    ts = []
    for i in range(reps):
        t0 = time.perf_counter()
        fn(i)
        ts.append(time.perf_counter() - t0)
    return float(np.median(ts)), float(np.min(ts)), float(np.max(ts))


def one_c1(args):
    seed, n_days, R = args
    r2, g = data(seed, n_days)
    return hc.c1_test(r2, g, np.random.default_rng(seed), R=R)["crit"]


def main():
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files.")
    OUT.mkdir(parents=True, exist_ok=True)
    kids = hc.child_seeds(SEED, 100000)
    rows = []
    for n_days in (59, 125, 250):
        pre = [data(kids[i], n_days) for i in range(N_SIM)]
        mats = [hc.market_matrix_from_r2(r, g) for r, g in pre]
        cfg = {
            "generate data (fast generator)": lambda i: data(kids[1000 + i], n_days),
            "base bootstrap-t, B=999 (M4b method)": lambda i: bootstrap_t(mats[i], np.random.default_rng(kids[2000 + i]), "rom", B=999),
            "C2 fast double bootstrap, B=999": lambda i: hc.fast_double_bootstrap(mats[i], np.random.default_rng(kids[3000 + i]), B=999),
            "C3 fixed critical value": lambda i: hc.c3_test(mats[i], 3.2),
            "C1 fit only": lambda i: hc.fit_bar_model(*pre[i]),
        }
        for R in (199, 499, 999):
            cfg[f"C1 full test, R={R}"] = (lambda R: lambda i: hc.c1_test(*pre[i], np.random.default_rng(kids[4000 + i]), R=R))(R)
        for name, fn in cfg.items():
            med, lo, hi = timed(fn, N_SIM)
            rows.append({"n_days": n_days, "task": name, "reps": N_SIM, "median_s": med, "min_s": lo, "max_s": hi})
            print(n_days, name, f"{med:.4f}s", flush=True)
    single = pd.DataFrame(rows)
    single.to_csv(OUT / "single_core_timing.csv", index=False)

    # parallel scaling: 64 C1 tests at 59 days, R = 499, on all cores vs one core
    jobs = [(kids[9000 + i], 59, 499) for i in range(64)]
    t0 = time.perf_counter()
    for a in jobs[:8]:
        one_c1(a)
    t_one = (time.perf_counter() - t0) / 8
    t0 = time.perf_counter()
    with ProcessPoolExecutor() as pool:
        crits = list(pool.map(one_c1, jobs, chunksize=2))
    t_par = (time.perf_counter() - t0) / len(jobs)
    par = pd.DataFrame([{"task": "C1 R=499, 59 days", "single_core_s_per_test": t_one, "all_cores_wall_s_per_test": t_par,
                         "speedup": t_one / t_par, "n_tests": len(jobs)}])
    par.to_csv(OUT / "parallel_scaling.csv", index=False)
    print(par.to_string(), flush=True)

    # plumbing indicator ONLY (40 datasets; not evidence): spread of the C1 critical value vs the bootstrap-t critical value
    cb, cc = [], []
    for i in range(40):
        r2, g = data(kids[20000 + i], 59)
        M = hc.market_matrix_from_r2(r2, g)
        cb.append(bootstrap_t(M, np.random.default_rng(kids[21000 + i]), "rom", B=499)["crit_max"])
        cc.append(hc.c1_test(r2, g, np.random.default_rng(kids[22000 + i]), R=499)["crit"])
    pd.DataFrame([{"what": "PLUMBING INDICATOR ONLY (40 datasets, NSE T4 E-like shape, 59 days)",
                   "bootstrap_t_crit_mean": np.mean(cb), "bootstrap_t_crit_cv": np.std(cb) / np.mean(cb),
                   "c1_crit_mean": np.mean(cc), "c1_crit_cv": np.std(cc) / np.mean(cc)}]).to_csv(OUT / "plumbing_indicator_crit_spread.csv", index=False)
    pd.Series({"python": platform.python_version(), "numpy": np.__version__, "machine": platform.platform(),
               "cpu_count": __import__("os").cpu_count(), "master_seed": SEED,
               "note": "timing only; no rejection rates recorded; ALL DATA SIMULATED"}).to_csv(OUT / "run_metadata.csv", header=["value"])
    print("COMPLETE", flush=True)


if __name__ == "__main__":
    main()
