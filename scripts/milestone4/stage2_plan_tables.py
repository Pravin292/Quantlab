"""H1 calibration, STAGE 2 PLANNING: derive the exact cell, seed, runtime and gate-arithmetic tables for the Stage 2 plan (docs/17).
Reads frozen v1 / v1.1 files and the Stage 0 benchmark, the Stage 1 summary. Runs NO simulation and writes only NEW files.
Output: outputs/milestone4/h1_calibration/stage2_plan/
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from quantlab.research import h1_calibration_v11 as v11                   # noqa: E402

BASE = ROOT / "outputs" / "milestone4" / "h1_calibration"
OUT = BASE / "stage2_plan"
SPEC = BASE / "frozen_spec"
SPEEDUP = {59: 4.17, 125: 4.0, 250: 3.85}                # measured on C1 batches (parallel_scaling_large_batch.csv); 125 days interpolated -> 4.0
STAGE1_OVERHEAD_MS = 2.0                                  # per-simulation cost seen in Stage 1 beyond the Stage 0 benchmark (derived below)
DEV_SEED, C3_SEED = 20261203, 20261202


def per_sim_ms(bench: pd.DataFrame, n_days: int) -> dict:
    """Single-core milliseconds per simulation for each component at one sample size (Stage 0 benchmark medians)."""
    g = lambda task: 1000 * float(bench[(bench.task == task) & (bench.n_days == n_days)].median_s.iloc[0])
    return {"generate": g("generate data (fast generator)"), "baseline": g("base bootstrap-t, B=999 (M4b method)"),
            "c2_report_only": g("C2 fast double bootstrap, B=999"), "c1": g("C1 full test, R=499")}


def main():
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files.")
    OUT.mkdir(parents=True, exist_ok=True)
    dev = pd.read_csv(SPEC / "cells_development.csv", keep_default_na=False)
    s1 = pd.read_csv(BASE / "stage1" / "stage1_cell_summary.csv", keep_default_na=False)
    bench = pd.read_csv(BASE / "stage0" / "benchmark" / "single_core_timing.csv")

    # ---- cell table with the row index that fixes every simulation's seed
    plan = dev.copy()
    plan.insert(0, "dev_row", plan.index)
    plan["role"] = np.where(plan.tier == "C", "report_only_df3", "gated_two_sided")
    plan["c3_training_member"] = plan.tier != "C"
    ha = s1[s1.experiment.str.startswith("HA")].set_index(["tail", "shape", "market"])
    plan["stage1_reference_row"] = [int(ha.loc[(r.tail, r.shape, r.market), "cell_row"]) if (r.n_days == 59 and r.dependence == "none" and r.day_vol_sd == 0.3
                                    and (r.tail, r.shape, r.market) in ha.index) else -1 for r in plan.itertuples()]
    plan.to_csv(OUT / "stage2_cells_plan.csv", index=False)

    # ---- C3 training cells (the gated development cells, separate seeds)
    c3 = plan[plan.c3_training_member][["dev_row", "tail", "shape", "market", "n_days", "dependence", "day_vol_sd", "tier"]].copy()
    c3["n_sims"] = 25_000
    c3["seed_master"] = C3_SEED
    c3.to_csv(OUT / "stage2_c3_training_cells.csv", index=False)

    # ---- seed scheme
    pd.DataFrame([
        dict(purpose="C3 training run", master_seed=C3_SEED, spawn_key="(dev_row, i)", rows_from="stage2_c3_training_cells.csv dev_row", sims=int(c3.n_sims.sum())),
        dict(purpose="Stage 2 development run (data)", master_seed=DEV_SEED, spawn_key="(dev_row, i, 0)", rows_from="cells_development.csv row", sims=int(plan.n_sims.sum())),
        dict(purpose="  baseline bootstrap draws", master_seed=DEV_SEED, spawn_key="(dev_row, i, 1)", rows_from="same", sims=int(plan.n_sims.sum())),
        dict(purpose="  C1 bootstrap draws", master_seed=DEV_SEED, spawn_key="(dev_row, i, 2)", rows_from="same", sims=int(plan.n_sims.sum())),
        dict(purpose="  C2 (report-only) draws", master_seed=DEV_SEED, spawn_key="(dev_row, i, 3)", rows_from="same", sims=int(plan.n_sims.sum())),
    ]).to_csv(OUT / "stage2_seed_scheme.csv", index=False)

    # ---- runtime
    rows = []
    for nd in (59, 125, 250):
        ms = per_sim_ms(bench, nd)
        sub = plan[plan.n_days == nd]
        sims = int(sub.n_sims.sum())
        single = ms["generate"] + ms["baseline"] + ms["c2_report_only"] + ms["c1"]
        hours = lambda ms_per_sim, speed: sims * ms_per_sim / 1000 / speed / 3600
        rows.append(dict(n_days=nd, cells=len(sub), simulations=sims, **{f"ms_{k}": v for k, v in ms.items()}, ms_all_methods=single,
                         hours_benchmark_x4=hours(single, 4.0), hours_measured_speedup=hours(single, SPEEDUP[nd]),
                         hours_with_stage1_overhead=hours(single + STAGE1_OVERHEAD_MS, SPEEDUP[nd])))
    rt = pd.DataFrame(rows)
    tot = rt[["cells", "simulations", "hours_benchmark_x4", "hours_measured_speedup", "hours_with_stage1_overhead"]].sum()
    rt["n_days"] = rt["n_days"].astype(object)                                  # allow the text label "total" in the last row
    rt.loc[len(rt)] = {"n_days": "total", **tot.to_dict()}
    c3_rows = []
    for nd in (59, 125, 250):
        ms = per_sim_ms(bench, nd)
        n = int(c3[c3.n_days == nd].n_sims.sum())
        c3_rows.append(dict(n_days=nd, simulations=n, hours_low=n * (ms["generate"]) / 1000 / SPEEDUP[nd] / 3600,
                            hours_high=n * (ms["generate"] + 2 * STAGE1_OVERHEAD_MS) / 1000 / SPEEDUP[nd] / 3600))
    c3rt = pd.DataFrame(c3_rows)
    rt.to_csv(OUT / "stage2_runtime_estimate.csv", index=False)
    c3rt.to_csv(OUT / "stage2_c3_training_runtime_estimate.csv", index=False)

    # ---- how wrong was the Stage 1 estimate
    plan_h = float(pd.read_csv(SPEC / "resource_estimate.csv").est_wall_hours.iloc[0])
    meta = pd.read_csv(BASE / "stage1" / "run_metadata.csv", index_col=0)["value"]
    actual_h = float(meta["seconds"]) / 3600
    pd.DataFrame([dict(stage1_estimated_hours=plan_h, stage1_actual_hours=actual_h, ratio_actual_over_estimate=actual_h / plan_h,
                       implied_extra_ms_per_sim_single_core_equiv=(float(meta["seconds"]) * 4 / 1.24e6 * 1000) - 1.9)]).to_csv(OUT / "stage1_estimate_vs_actual.csv", index=False)

    # ---- gate arithmetic: per-cell and joint pass probability at a true rate of 5.0%, and detection of small excesses
    g = []
    n = 25_000
    k = np.arange(n + 1)
    for tier in ("A", "B"):
        ok = v11.gate_pass(k, n, tier)
        for p in (0.050, 0.052, 0.055, 0.056, 0.058, 0.060):
            g.append(dict(tier=tier, true_rate=p, per_cell_pass_prob=float(stats.binom.pmf(k[ok], n, p).sum())))
    gp = pd.DataFrame(g)
    gp.to_csv(OUT / "stage2_gate_pass_probability.csv", index=False)
    a = float(gp[(gp.tier == "A") & (gp.true_rate == .05)].per_cell_pass_prob.iloc[0])
    b = float(gp[(gp.tier == "B") & (gp.true_rate == .05)].per_cell_pass_prob.iloc[0])
    nA, nB = int((plan.tier == "A").sum()), int((plan.tier == "B").sum())
    pd.DataFrame([dict(grid="development (Stage 2)", tier_A_cells=nA, tier_B_cells=nB, joint_pass_prob_if_all_true_5pct=a ** nA * b ** nB),
                  dict(grid="validation (Stage 3): 44+10 A, 24+10 B", tier_A_cells=nA + 10, tier_B_cells=nB + 10,
                       joint_pass_prob_if_all_true_5pct=a ** (nA + 10) * b ** (nB + 10))]).to_csv(OUT / "stage2_joint_pass_probability.csv", index=False)

    pd.set_option("display.width", 250)
    print(plan.groupby(["role", "tier"]).agg(cells=("tail", "size"), sims=("n_sims", "sum")))
    print("stage1 reference overlap cells:", int((plan.stage1_reference_row >= 0).sum()))
    print(rt.round(3).to_string()); print(c3rt.round(3).to_string())
    print(pd.read_csv(OUT / "stage1_estimate_vs_actual.csv").round(3).to_string())
    print(gp.round(4).to_string()); print(pd.read_csv(OUT / "stage2_joint_pass_probability.csv").round(4).to_string())
    print("C3 training:", len(c3), "cells,", int(c3.n_sims.sum()), "simulations")


if __name__ == "__main__":
    main()
