"""H1 calibration, STAGE 0: write the experimental specification v1 (grids, thresholds, seeds, rules) and its SHA-256 manifest.
Generates files only; runs no simulation.   Output: outputs/milestone4/h1_calibration/frozen_spec/"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "milestone4" / "h1_calibration" / "frozen_spec"
BENCH = ROOT / "outputs" / "milestone4" / "h1_calibration" / "stage0" / "benchmark" / "single_core_timing.csv"
SPEEDUP = 4.0                                                     # measured 3.8-4.2 on this machine (parallel_scaling_large_batch.csv)

GATED_TAILS = {"G": "A", "T10": "A", "T6": "A", "T4": "B"}
SHAPES = ["flat", "E", "D5", "R2"]
N_GATED, N_REPORT = 25_000, 10_000


def dev_cells():
    rows = []
    for tail in ["G", "T10", "T6", "T4", "T3"]:
        for sh in SHAPES:
            for mk in ("NSE", "US"):
                rows.append(dict(tail=tail, shape=sh, market=mk, n_days=59, dependence="none", day_vol_sd=0.3))
    for tail in ("T6", "T4"):
        for sh in ("E", "D5"):
            for mk in ("NSE", "US"):
                rows.append(dict(tail=tail, shape=sh, market=mk, n_days=59, dependence="estimated", day_vol_sd=0.3))
    for sh in ("E", "D5"):
        for mk in ("NSE", "US"):
            rows.append(dict(tail="T4", shape=sh, market=mk, n_days=59, dependence="none", day_vol_sd=0.6))
    for tail in ("G", "T6", "T4"):
        for sh in ("E", "D5"):
            for mk in ("NSE", "US"):
                for nd in (125, 250):
                    rows.append(dict(tail=tail, shape=sh, market=mk, n_days=nd, dependence="none", day_vol_sd=0.3))
    d = pd.DataFrame(rows)
    d["tier"] = d["tail"].map({**GATED_TAILS, "T3": "C"})
    d["n_sims"] = d.tier.map({"A": N_GATED, "B": N_GATED, "C": N_REPORT})
    return d


def val_cells(dev):
    v = dev.copy()
    v["origin"] = "development cell, FRESH seeds"
    rows = []
    for tail in ("T7", "T5"):
        for mk in ("NSE", "US"):
            for nd in (59, 90, 180):
                rows.append(dict(tail=tail, shape="E", market=mk, n_days=nd, dependence="none", day_vol_sd=0.3))
            for sh in ("D1.5", "D3.0"):
                rows.append(dict(tail=tail, shape=sh, market=mk, n_days=59, dependence="none", day_vol_sd=0.3))
    x = pd.DataFrame(rows)
    x["tier"] = x["tail"].map({"T7": "A", "T5": "B"})
    x["n_sims"] = N_GATED
    x["origin"] = "NEW intermediate cell (not used in development)"
    return pd.concat([v, x], ignore_index=True)


def stage1_cells():
    rows = []
    for tail in ["G", "T20", "T10", "T8", "T6", "T5", "T4", "T3"]:
        for sh in ("flat", "E", "D5"):
            for mk in ("NSE", "US"):
                rows.append(dict(experiment="HA tail scan", tail=tail, shape=sh, market=mk, n_days=59, merge=1, B=999, n_sims=20_000))
    for sh in ("E", "D5"):
        for mk in ("NSE", "US"):
            for g in (1, 2, 3):
                rows.append(dict(experiment="HB effective-bar (merge g consecutive bars)", tail="T4", shape=sh, market=mk, n_days=59, merge=g, B=999, n_sims=20_000))
    for sh in ("E", "D5"):
        for mk in ("NSE", "US"):
            for B in (999, 9999):
                rows.append(dict(experiment="HE bootstrap size", tail="T4", shape=sh, market=mk, n_days=59, merge=1, B=B, n_sims=5_000))
    return pd.DataFrame(rows)


def alt_dgp_cells():
    dg = {"a_intraday_volatility_clustering": "log-vol AR(1) across bars within day, phi 0.9, stationary sd 0.25, t6 shocks",
          "b_jumps": "t10 shocks plus per-bar jump probability 0.002, jump size uniform 4-8 times the bar scale, random sign",
          "c_period_specific_tails": "df 4 in open and close, df 8 in middle",
          "d_stock_specific_tails": "df 3, 5, 8 for the three stocks",
          "e_heavy_tailed_day_factor": "log day scale t3 distributed with sd 0.3, t8 shocks",
          "f_laplace_shocks": "generalised error shape 1 (Laplace), unit variance"}
    return pd.DataFrame([dict(dgp=k, description=v, shape="E", market=mk, n_days=59, n_sims=N_GATED, tier="alt")
                         for k, v in dg.items() for mk in ("NSE", "US")])


def cost(cells, per_sim_ms):
    return float((cells.n_sims * cells.n_days.map(per_sim_ms)).sum() / 1000.0)


def main():
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files.")
    OUT.mkdir(parents=True, exist_ok=True)
    t = pd.read_csv(BENCH)

    def ms(task, nd):
        return 1000 * float(t[(t.task == task) & (t.n_days == nd)].median_s.iloc[0])
    interp = lambda f: (lambda nd: f(59) + (f(250) - f(59)) * (nd - 59) / (250 - 59) if nd not in (59, 125, 250) else f(nd))
    per_all = lambda nd: (ms("C1 full test, R=499", nd) + ms("C2 fast double bootstrap, B=999", nd) +
                          ms("base bootstrap-t, B=999 (M4b method)", nd) + ms("generate data (fast generator)", nd)) / SPEEDUP
    per_c1 = lambda nd: (ms("C1 full test, R=499", nd) + ms("generate data (fast generator)", nd)) / SPEEDUP
    per_base = lambda nd: (ms("base bootstrap-t, B=999 (M4b method)", nd) + ms("generate data (fast generator)", nd)) / SPEEDUP
    dev, val, s1, alt = dev_cells(), None, stage1_cells(), alt_dgp_cells()
    val = val_cells(dev)
    d_all = lambda nd: per_all(nd) if nd in (59, 125, 250) else per_all(59) + (per_all(250) - per_all(59)) * (nd - 59) / 191
    d_c1 = lambda nd: per_c1(nd) if nd in (59, 125, 250) else per_c1(59) + (per_c1(250) - per_c1(59)) * (nd - 59) / 191
    d_base = lambda nd: per_base(nd) if nd in (59, 125, 250) else per_base(59) + (per_base(250) - per_base(59)) * (nd - 59) / 191
    reduced = dev[dev.n_days != 250]
    est = pd.DataFrame([
        dict(stage="Stage 1 mechanism diagnosis (base method only)", cells=len(s1), simulations=int(s1.n_sims.sum()), est_wall_hours=cost(s1, d_base) / 3600),
        dict(stage="Stage 2 development, all candidates + baseline on shared data (FULL grid)", cells=len(dev), simulations=int(dev.n_sims.sum()), est_wall_hours=cost(dev, d_all) / 3600),
        dict(stage="Stage 2 development (REDUCED: no 250-day cells)", cells=len(reduced), simulations=int(reduced.n_sims.sum()), est_wall_hours=cost(reduced, d_all) / 3600),
        dict(stage="Stage 3 validation, worst case = C1 selected (FULL)", cells=len(val), simulations=int(val.n_sims.sum()), est_wall_hours=cost(val, d_c1) / 3600),
        dict(stage="Stage 4 alternative DGPs, C1 (generation cost of non-standard DGPs NOT included; assume x3)", cells=len(alt), simulations=int(alt.n_sims.sum()), est_wall_hours=3 * cost(alt, d_c1) / 3600),
    ])
    est["total_core_assumption"] = f"measured single-core times divided by an observed parallel speedup of {SPEEDUP}"
    spec = {
        "version": "v1", "status": "FROZEN for review; any change requires a numbered new version approved by the user",
        "estimand": "unchanged: day-volatility-weighted pooled variance ratio (RMS volatility) between open, middle, close",
        "statistic": "T = max over the 3 pairwise contrasts of |ln(mean_a/mean_b)| / influence-function SE (rom, block 1, as h1_rms2)",
        "alpha": 0.05, "stocks_per_market": 3,
        "baseline_for_comparison": "M4b bootstrap-t, B=999, rom, max rule, iid days",
        "candidates": {
            "C1": "null-imposed model-based bootstrap with empirical bar-level shocks; R=499 artificial datasets; decision p=(1+#{T*>=T})/(R+1)<=alpha; "
                  "robust (median) day scale; slot profile equalised within period; shocks drawn jointly over stocks from the same period; day scales drawn iid",
            "C2": "fast double bootstrap-t; B=999; one inner resample per outer; adjusted p = share of T** above the (1-p1) quantile of T**, reject if <= alpha "
                  "(formula recalled from Davidson & MacKinnon 2007; NOT verified against the paper; Stage 1 verifies the implementation on a case with known behaviour)",
            "C3": "fixed critical value per sample size = max over gated development cells of the 95% quantile of T, from a SEPARATE training run "
                  "(disjoint seeds, 25,000 simulations per cell); no extra margin; evaluated on the upper gates only (conservative benchmark/fallback)"},
        "fair_comparison_rules": [
            "all candidates and the baseline are run on the SAME simulated dataset (same seed) in every simulation of every cell",
            "same alpha, same cells, same number of simulations, same gates; computing cost is reported for each",
            "no candidate is chosen on one cell, one scenario or on power",
            "selection among candidates that pass the two-sided gates in every gated cell: the simplest; ties broken by cost; power is reported only after calibration passes"],
        "gates": {
            "tier_A_core (df G,10,6,7)": "point estimate in [4.5%,5.5%] AND Wilson 95% upper limit <= 6.0%, every cell",
            "tier_B_stress (df 4,5)": "point estimate in [4.0%,6.0%] AND Wilson 95% upper limit <= 6.5%, every cell",
            "tier_C (df 3)": "report only",
            "ceiling": "no validated cell above 7.0%",
            "C3_only": "upper limits only (point <= 5.5% tier A, <= 6.0% tier B); its conservatism (lowest cell rate) is reported",
            "alternative_DGPs": "point estimate in [4.0%,6.0%] each",
            "conditional_behaviour": "rejection by leverage quartile and by critical-value quartile: reported, flagged if clearly steeper than the Gaussian reference",
            "numerical": "any failure rate above 0.1% needs a pre-specified fallback; denominators reported",
            "n_per_gated_cell": N_GATED, "n_per_report_cell": N_REPORT,
            "basis": "stage0_mc_precision.py: 25,000 simulations give 95% joint pass probability for up to ~96 gated cells at a true 5.0% rate (30,000 for 192)",
            "bradley_note": "Bradley (1978) liberal band 0.5-1.5 alpha is attested only via secondary sources; the original and any stringent band were NOT verified and are not cited"},
        "seeds": {"stage1": 20261201, "c3_training": 20261202, "development": 20261203, "validation_cells": 20261204,
                  "validation_intermediate_cells": 20261205, "alternative_dgps": 20261206, "bar_level_pipeline_check": 20261207,
                  "reference_implementation_check": 20261208, "rule": "per-simulation child SeedSequence passed to default_rng; validation seeds unused until Stage 3"},
        "failure_conditions": ["any tier A cell outside gate on validation", "any tier B cell outside gate (domain narrowed to df>=6 and reported)",
                               "any alternative DGP outside gate", "fitted-parameter instability (critical-value CV of the candidate >= that of the baseline)",
                               "power collapse flagged (<70% of baseline power at T4 flat x1.2)", "retuning after seeing validation",
                               "reference implementation disagrees", "required simulations unreachable within the approved budget"],
        "environment": {"python": "3.12.13", "numpy": "2.5.4", "pandas": "3.1.0", "scipy": "1.18.1", "statsmodels": "0.15.0", "os": "macOS Darwin 24.4.0"},
        "descriptive_real_data_note": "descriptive tail/shape summaries only; they place real data on the grid; no H1 test on real data",
    }
    (OUT / "spec_v1.json").write_text(json.dumps(spec, indent=2))
    dev.to_csv(OUT / "cells_development.csv", index=False)
    val.to_csv(OUT / "cells_validation.csv", index=False)
    s1.to_csv(OUT / "cells_stage1.csv", index=False)
    alt.to_csv(OUT / "cells_alternative_dgps.csv", index=False)
    est.to_csv(OUT / "resource_estimate.csv", index=False)
    print(est.round(2).to_string())
    files = sorted(OUT.glob("*")) + [ROOT / p for p in [
        "src/quantlab/research/h1_calibration.py", "src/quantlab/research/tail_descriptives.py",
        "tests/test_research_h1_calibration.py", "tests/test_research_tail_descriptives.py",
        "scripts/milestone4/stage0_benchmark.py", "scripts/milestone4/stage0_benchmark_parallel.py",
        "scripts/milestone4/stage0_mc_precision.py", "scripts/milestone4/stage0_real_data_descriptive.py",
        "scripts/milestone4/stage0_freeze_spec.py",
        "src/quantlab/research/h1_rms.py", "src/quantlab/research/h1_rms2.py", "src/quantlab/research/direct_sim.py",
        "src/quantlab/research/dependence.py", "src/quantlab/research/inference.py", "src/quantlab/research/nulls.py",
        "scripts/milestone4/run_h1_inference.py", "scripts/milestone4/run_h1_next.py"]]
    lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT)}" for p in files]
    (OUT / "FROZEN_v1.sha256").write_text("\n".join(lines) + "\n")
    print(f"{len(lines)} files hashed")


if __name__ == "__main__":
    main()
