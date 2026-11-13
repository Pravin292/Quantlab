"""H1 calibration, STAGE 3: power cells (T4 flat x1.1 and x1.2, T4 E x1.2; both markets; 59 days; 5,000 simulations each = 30,000), baseline + C3 on the same data.
Per docs/13 these are reported ONLY AFTER CALIBRATION PASSES: this script refuses to run unless stage3/summary/stage3_candidate_outcome.csv says the C3 outcome is
PASS_CLEAR or MARGINAL_NOT_DEMONSTRATED (no FAIL, no FAIL_BOUNDARY_ONLY). Fresh master seed 20261213 (new, registered in docs/20). Never used for selection.
Flag (v1 failure condition 5): C3 power below 70% of the baseline's at T4 flat x1.2.    Output: outputs/milestone4/h1_calibration/stage3/power_check/
"""
import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage3_common as c3c                                                # noqa: E402
from quantlab.research import h1_calibration_v11 as v11, h1_stage3 as s3   # noqa: E402

OUT = c3c.S3 / "power_check"
CELLS = [dict(power_cell=j, tail="T4", shape=sh, mult=m, market=mk, n_days=59, dependence="none", day_vol_sd=0.3)
         for j, (sh, m, mk) in enumerate([(sh, m, mk) for (sh, m) in (("flat", 1.1), ("flat", 1.2), ("E", 1.2)) for mk in ("NSE", "US")])]
ALLOWED = ("PASS_CLEAR", "MARGINAL_NOT_DEMONSTRATED")
CHUNK = 250
_CRIT = None


def _init(crit):
    """Worker start-up: frozen C3 value for 59 days."""
    global _CRIT
    _CRIT = crit


def work(job):
    """Simulations [start, stop) of one power cell."""
    j, start, stop = job
    cell = CELLS[j]
    setup = c3c.cell_setup(cell, mult=cell["mult"])
    return [{"power_cell": j, "sim": i, **c3c.simulate_one(setup, lambda k, i=i: s3.power_seed(j, i, k), _CRIT)} for i in range(start, stop)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--outcome-file", default=None)
    ap.add_argument("--c3-table", default=None)
    ap.add_argument("--n", type=int, default=5000)
    a = ap.parse_args()
    out = Path(a.out) if a.out else OUT
    if a.smoke and (a.out is None or Path(a.out).resolve() == OUT.resolve() or not (a.outcome_file and a.c3_table)):
        sys.exit("--smoke needs --out (scratch), --outcome-file and --c3-table")
    c3c.verify_all(stage3_inputs=not a.smoke, c3_intermediate=not a.smoke)
    of = Path(a.outcome_file) if a.smoke else c3c.S3 / "summary" / "stage3_candidate_outcome.csv"
    if not of.exists():
        sys.exit("no Stage 3 candidate outcome file: summarise the validation first")
    oc = pd.read_csv(of, keep_default_na=False)
    outcome = oc[oc["method"] == "c3"]["v1_1_candidate_outcome"].iloc[0]
    if outcome not in ALLOWED:
        sys.exit(f"C3 calibration outcome is {outcome}: power cells are reported only after calibration passes (docs/13); not run")
    n = a.n if a.smoke else 5000
    crit = float(pd.read_csv(Path(a.c3_table) if a.smoke else c3c.STAGE2_C3_TABLE).set_index("n_days").loc[59, "c3_crit"])
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} already has files.")
    out.mkdir(parents=True, exist_ok=True)
    t0, summ = time.perf_counter(), []
    with ProcessPoolExecutor(initializer=_init, initargs=(crit,)) as pool:
        for j, c in enumerate(CELLS):
            d = pd.DataFrame([r for part in pool.map(work, [(j, s, min(s + CHUNK, n)) for s in range(0, n, CHUNK)]) for r in part]).sort_values("sim")
            d.to_parquet(out / f"power_cell_{j}.parquet", index=False)
            for m in ("base", "c3"):
                v = d[d[f"valid_{m}"]]
                k, nn = int(v[f"reject_{m}"].sum()), len(v)
                lo, hi = (float(x) for x in v11.wilson_interval(k, nn))
                summ.append({"power_cell": j, "shape": c["shape"], "mult": c["mult"], "market": c["market"], "method": m, "n_valid": nn, "n_failed": len(d) - nn, "power": k / nn, "wilson_low": lo, "wilson_high": hi})
            print(f"power cell {j} {c['shape']} x{c['mult']} {c['market']}: base={d.loc[d.valid_base, 'reject_base'].mean():.4f} c3={d.loc[d.valid_c3, 'reject_c3'].mean():.4f} elapsed={time.perf_counter() - t0:.0f}s", flush=True)
    s = pd.DataFrame(summ)
    flags = []
    for j, c in enumerate(CELLS):
        b = s[(s.power_cell == j) & (s.method == "base")].iloc[0]; x = s[(s.power_cell == j) & (s.method == "c3")].iloc[0]
        ratio = x.power / b.power if b.power > 0 else float("nan"); fc = c["shape"] == "flat" and c["mult"] == 1.2
        flags.append({"power_cell": j, "shape": c["shape"], "mult": c["mult"], "market": c["market"], "method": "c3", "power_method": x.power, "power_baseline": b.power, "ratio_to_baseline": ratio,
                      "flag_cell": fc, "power_collapse_flag": bool(fc and ratio < 0.70), "caveat": "" if c["shape"] == "flat" else "baseline size is distorted in E cells: ratio not a fair yardstick; no flag applies"})
    s.to_csv(out / "power_by_cell_method.csv", index=False); pd.DataFrame(flags).to_csv(out / "power_ratio_and_flag.csv", index=False)
    pd.Series({"master_seed": s3.MASTER["validation_power"], "n_per_cell": n, "c3_crit_59": crit, "calibration_outcome_at_run": outcome, "smoke": a.smoke, "wall_seconds": round(time.perf_counter() - t0, 1),
               "note": "ALL DATA SIMULATED; diagnostic only; not for selection"}).to_csv(out / "run_metadata.csv", header=["value"])
    print("COMPLETE")


if __name__ == "__main__":
    main()
