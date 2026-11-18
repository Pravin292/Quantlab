"""Write the Stage 6 dashboard datasets (dashboard/datasets/stage6_*.csv) from the saved Stage 6 result files (outputs/milestone4/stage6).
Aggregates only: no market data, no new analysis.

    python dashboard/build_stage6_datasets.py                       # reads outputs/milestone4/stage6, writes dashboard/datasets
    python dashboard/build_stage6_datasets.py --src DIR --out DIR   # (tests on scratch results)
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from quantlab.research import stage6 as s6                      # noqa: E402

LEVEL_LABEL = {"S0_none": "S0 independent", "S1_validated": "S1 earlier estimate", "S2_fresh_point": "S2 US fresh, measured", "S3_fresh_upper": "S3 US fresh, upper range",
               "S4_one_and_half_x": "S4 1.5 × measured", "S5_illustrative": "S5 illustrative stress"}


def pct(x):
    return round(100 * float(x), 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(ROOT / "outputs" / "milestone4" / "stage6"))
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "datasets"))
    a = ap.parse_args()
    src, out = Path(a.src), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    size = pd.read_csv(src / "part_a" / "size_by_cell.csv")
    outcome = pd.read_csv(src / "part_a" / "part_a_outcome.csv").iloc[0]
    d = pd.DataFrame({"level": size.level, "level_label": size.level.map(LEVEL_LABEL), "market": size.market, "shape": size["shape"], "tail": size["tail"], "tier": size.tier, "n_days": size.n_days,
                      "gated": size.gated, "ret_corr": size.ret_corr, "share": size.share, "phi": size.phi, "c3_rate_pct": size.rate_c3.map(pct), "baseline_rate_pct": size.rate_base.map(pct),
                      "wilson_low_pct": size.wilson_low.map(pct), "wilson_high_pct": size.wilson_high.map(pct), "limit_pct": size.tier.map({"A": 5.5, "B": 6.0}),
                      "status": size.status.str.replace("REPORTED_", "")})
    d.to_csv(out / "stage6_size.csv", index=False)

    power = pd.read_csv(src / "part_b" / "power_by_cell.csv")
    pd.DataFrame({"market": power.market, "level": power.level, "n_days": power.n_days, "mult": power["mult"], "power_pct": power.power.map(pct),
                  "wilson_low_pct": power.wilson_low.map(pct), "wilson_high_pct": power.wilson_high.map(pct)}).to_csv(out / "stage6_power.csv", index=False)
    mde = pd.read_csv(src / "part_b" / "min_detectable_effect.csv")
    mde.rename(columns={"min_detectable_mult": "mde_mult"}).to_csv(out / "stage6_mde.csv", index=False)

    pl = pd.read_csv(src / "part_c" / "placebo_results.csv")
    pl["rate_pct"] = pl.rate.map(pct) if "rate" in pl else None
    for c in ("wilson_low", "wilson_high"):
        pl[c + "_pct"] = pl[c].map(pct) if c in pl else None
    pl["label"] = pl.rate.map(lambda r: "PLACEBO_OK" if r <= 0.055 else ("PLACEBO_WARN" if r <= 0.07 else "PLACEBO_HIGH") if pd.notna(r) else None)
    keep = [c for c in ("sample", "market", "status", "usable_market_sessions", "real_T", "n_rep", "rate_pct", "wilson_low_pct", "wilson_high_pct", "T_median", "T_p95", "T_max", "label", "note") if c in pl]
    pl[keep].to_csv(out / "stage6_placebo.csv", index=False)

    meta_b = pd.read_csv(src / "part_b" / "run_metadata.csv", index_col=0)["value"]
    meta_a = pd.read_csv(src / "part_a" / "run_metadata.csv", index_col=0)["value"]
    pd.DataFrame([{"outcome": outcome.outcome, "gated_cells": int(outcome.gated_cells), "n_pass": int(outcome.n_PASS), "n_pass_ambiguous": int(outcome.n_PASS_AMBIGUOUS),
                   "n_fail_ambiguous": int(outcome.n_FAIL_AMBIGUOUS), "n_fail": int(outcome.n_FAIL), "highest_gated_pct": pct(outcome.highest_gated_rate), "highest_reported_pct": pct(outcome.highest_reported_rate),
                   "sims_part_a": int(len(size) * int(size.n_sims.iloc[0])), "sims_part_b": int(len(power) * int(power.n_sims.iloc[0])), "master_seed_a": int(meta_a["master_seed"]),
                   "master_seed_b": int(meta_b["master_seed"])}]).to_csv(out / "stage6_summary.csv", index=False)
    # keep the dashboard's simulation ledger in step: the two Stage 6 runs after the nine earlier ones
    led_path = out / "simulation_ledger.csv"
    led = pd.read_csv(led_path)
    led = led[~led.stage.str.startswith("Stage 6")]
    n_a, n_b = int(len(size) * int(size.n_sims.iloc[0])), int(len(power) * int(power.n_sims.iloc[0]))
    led = pd.concat([led, pd.DataFrame({"stage": ["Stage 6 dependence stress test", "Stage 6 power curve"], "simulations": [n_a, n_b]})], ignore_index=True)
    led.to_csv(led_path, index=False)
    print("wrote", sorted(p.name for p in out.glob("stage6_*.csv")), "and the ledger now has", len(led), "runs")


if __name__ == "__main__":
    main()
