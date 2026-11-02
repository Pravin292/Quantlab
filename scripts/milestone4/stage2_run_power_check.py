"""H1 calibration, STAGE 2, step E6: EARLY-WARNING POWER CHECK (decision D3).   WRITTEN IN E1; NOT RUN (it needs a separate instruction and only applies to
candidates that meet the calibration conditions of docs/17 section 10 A.1-A.5).   ALL DATA SIMULATED.  DIAGNOSTIC ONLY: it does not enter the advance
rule, does not rank candidates and is never validation.
Cells: T4, 59 days, no dependence, day-volatility 0.3, open/close variance multiplier mult:  flat x1.1, flat x1.2, E x1.2, both markets (6 cells x 5,000).
Methods on the SAME data: baseline, C1, C3 (frozen table).  Seed: master 20261212, SeedSequence(20261212, spawn_key=(power_cell, i, k)).
Only flag (v1 failure condition): candidate power < 70% of the baseline's at T4 flat x1.2.  Caveat: the baseline's size is distorted in the E cells.
Output: outputs/milestone4/h1_calibration/stage2/power_check/
"""
import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage2_common as sc                                                 # noqa: E402
from quantlab.research import h1_calibration_v11 as v11, h1_stage2 as s2   # noqa: E402

OUT = sc.BASE / "stage2" / "power_check"
C3_DIR = sc.BASE / "stage2" / "c3_training"
CELLS = [dict(power_cell=j, tail="T4", shape=sh, mult=m, market=mk, n_days=59, dependence="none", day_vol_sd=0.3)
         for j, (sh, m, mk) in enumerate([(sh, m, mk) for (sh, m) in (("flat", 1.1), ("flat", 1.2), ("E", 1.2)) for mk in ("NSE", "US")])]
CHUNK = 250
_CRIT = None


def _init(crit):
    """Worker start-up: frozen C3 critical value for 59 days."""
    global _CRIT
    _CRIT = crit


def work(job):
    """Simulations [start, stop) of one power cell."""
    j, start, stop = job
    cell = CELLS[j]
    setup = sc.cell_setup(cell, mult=cell["mult"])
    return [{"power_cell": j, "sim": i, **sc.simulate_all(setup, lambda k, i=i: s2.power_seed(j, i, k), _CRIT)} for i in range(start, stop)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--c3-table", default=None)
    ap.add_argument("--n", type=int, default=5000)
    a = ap.parse_args()
    out = Path(a.out) if a.out else OUT
    if a.smoke and (a.out is None or a.c3_table is None or Path(a.out).resolve() == OUT.resolve()):
        sys.exit("--smoke needs --out (scratch) and --c3-table")
    sc.verify_all(require_stage2_inputs=not a.smoke)
    if not a.smoke:
        sc.verify_manifest(C3_DIR / "C3_TABLE.sha256", 2)
        n = 5000
    else:
        n = a.n
    crit = float(pd.read_csv(Path(a.c3_table) if a.smoke else C3_DIR / "c3_critical_values.csv").set_index("n_days").loc[59, "c3_crit"])
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} already has files.")
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    summ = []
    with ProcessPoolExecutor(initializer=_init, initargs=(crit,)) as pool:
        for j, c in enumerate(CELLS):
            d = pd.DataFrame([r for part in pool.map(work, [(j, s, min(s + CHUNK, n)) for s in range(0, n, CHUNK)]) for r in part]).sort_values("sim")
            d.to_parquet(out / f"power_cell_{j}.parquet", index=False)
            for m in ("base", "c1", "c3"):
                v = d[d[f"valid_{m}"]]
                k, nn = int(v[f"reject_{m}"].sum()), len(v)
                lo, hi = (float(x) for x in v11.wilson_interval(k, nn))
                summ.append({"power_cell": j, "shape": c["shape"], "mult": c["mult"], "market": c["market"], "method": m, "n_valid": nn, "n_failed": len(d) - nn,
                             "power": k / nn, "wilson_low": lo, "wilson_high": hi})
            print(f"power cell {j} {c['shape']} x{c['mult']} {c['market']}: " + " ".join(f"{m}={d.loc[d[f'valid_{m}'], f'reject_{m}'].mean():.4f}" for m in ('base', 'c1', 'c3')) +
                  f" elapsed={time.perf_counter() - t0:.0f}s", flush=True)
    s = pd.DataFrame(summ)
    # paired difference and the single flag
    flags = []
    for j, c in enumerate(CELLS):
        b = s[(s.power_cell == j) & (s.method == "base")].iloc[0]
        for m in ("c1", "c3"):
            x = s[(s.power_cell == j) & (s.method == m)].iloc[0]
            ratio = x.power / b.power if b.power > 0 else float("nan")
            is_flag_cell = c["shape"] == "flat" and c["mult"] == 1.2
            flags.append({"power_cell": j, "shape": c["shape"], "mult": c["mult"], "market": c["market"], "method": m, "power_method": x.power, "power_baseline": b.power,
                          "ratio_to_baseline": ratio, "flag_cell": is_flag_cell, "power_collapse_flag": bool(is_flag_cell and ratio < 0.70),
                          "caveat": "" if c["shape"] == "flat" else "baseline size is distorted in E cells: ratio not a fair yardstick; no flag applies"})
    s.to_csv(out / "power_by_cell_method.csv", index=False)
    pd.DataFrame(flags).to_csv(out / "power_ratio_and_flag.csv", index=False)
    pd.Series({"master_seed": s2.MASTER["power_check"], "n_per_cell": n, "c3_crit_59": crit, "smoke": a.smoke, "wall_seconds": round(time.perf_counter() - t0, 1),
               "note": "ALL DATA SIMULATED; diagnostic only; not for selection or validation"}).to_csv(out / "run_metadata.csv", header=["value"])
    print("COMPLETE")


if __name__ == "__main__":
    main()
