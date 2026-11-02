"""H1 calibration, STAGE 0: parallel-scaling benchmark (timing only; simulated data). The first benchmark's 64-test batch was too
small (process start-up dominated), so this repeats the measurement with 960 tests after a warm-up."""
import sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))
import stage0_benchmark as sb                                                   # noqa: E402
from quantlab.research import h1_calibration as hc                              # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "h1_calibration" / "stage0" / "benchmark"

if __name__ == "__main__":
    kids = hc.child_seeds(20261101, 5000)
    rows = []
    for n_days, R, n in ((59, 499, 960), (250, 499, 240)):
        jobs = [(kids[i], n_days, R) for i in range(n)]
        t0 = time.perf_counter()
        for a in jobs[:6]:
            sb.one_c1(a)
        t_one = (time.perf_counter() - t0) / 6
        with ProcessPoolExecutor() as pool:
            list(pool.map(sb.one_c1, jobs[:32]))                                    # warm-up
            t0 = time.perf_counter()
            list(pool.map(sb.one_c1, jobs, chunksize=8))
            t_par = (time.perf_counter() - t0) / n
        rows.append({"task": f"C1 R={R}, {n_days} days", "tests": n, "single_core_s_per_test": t_one,
                     "all_cores_wall_s_per_test": t_par, "speedup": t_one / t_par})
        print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(OUT / "parallel_scaling_large_batch.csv", index=False)
