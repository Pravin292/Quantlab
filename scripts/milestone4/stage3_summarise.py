"""H1 calibration, STAGE 3: summarise the locked validation run (reads per-cell parquet; runs no simulation; writes new CSVs).   ALL DATA SIMULATED.
Outputs (--out, default outputs/milestone4/h1_calibration/stage3/summary/):
  stage3_cell_results.csv           rate, Wilson interval, status (C3: upper limits only; baseline two-sided, reference only), failures, per cell and method
  stage3_candidate_outcome.csv      v1.1 outcome of C3 (and of the baseline for reference), counts, extremes, lowest-cell rate
  stage3_failure_conditions.csv     docs/13 4.7 conditions that apply to Stage 3, evaluated for C3
  stage3_vs_stage2_repeat.csv       the 76 re-run development cells: Stage 3 vs Stage 2 rate, z
  stage3_conditional_calibration.csv  quartile rates (leverage, kurtosis, own critical value for the baseline), spreads, D2 flags where a matched df-infinity reference exists
D2 (same formula as Stage 2): spread - 1.25 x reference_spread >= 0.02, fractions, judgement-based. Where the frozen grid has no df-infinity reference (90/180 days, D1.5/D3.0)
the D2 comparison is NOT COMPUTABLE as specified and is reported as such (no substitute reference is invented).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage3_common as c3c                                                # noqa: E402
from quantlab.research import h1_calibration_v11 as v11, h1_stage2 as s2, h1_stage3 as s3   # noqa: E402

VAL = c3c.S3 / "validation"
PLAN = c3c.B / "stage3_plan" / "stage3_cells_plan.csv"
S2CM = c3c.B / "stage2" / "summary" / "stage2_cell_method_results.csv"
METHODS = {"baseline": "base", "c3": "c3"}


def status(k, n, tier, method):
    """Cell status: C3 on upper limits only, baseline on the two-sided v1.1 gate (information only), df 3 report-only."""
    lo_w, hi_w = (float(x) for x in v11.wilson_interval(k, n))
    if tier == "C":
        return {"p_hat": k / n, "wilson_low": lo_w, "wilson_high": hi_w, "status": "REPORT_ONLY"}
    cl = v11.classify_cell(k, n, tier, c3_mode=(method == "c3"))
    return {"p_hat": cl["p_hat"], "wilson_low": cl["wilson_low"], "wilson_high": cl["wilson_high"], "status": cl["status"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--val", default=str(VAL))
    ap.add_argument("--out", default=str(c3c.S3 / "summary"))
    ap.add_argument("--rows", default=None, help="smoke only")
    a = ap.parse_args()
    val, out = Path(a.val), Path(a.out)
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} already has files.")
    out.mkdir(parents=True, exist_ok=True)
    plan = pd.read_csv(PLAN, keep_default_na=False)
    rows = [int(x) for x in a.rows.split(",")] if a.rows else list(plan.val_row)
    data = {r: pd.read_parquet(val / f"cell_{r:02d}.parquet") for r in rows}
    cm = []
    for r in rows:
        c, d = plan.loc[r], data[r]
        for name, m in METHODS.items():
            v = d[d[f"valid_{m}"]]
            k, n, nf = int(v[f"reject_{m}"].sum()), len(v), len(d) - len(v)
            cm.append({"val_row": r, "tail": c["tail"], "shape": c["shape"], "market": c["market"], "n_days": c["n_days"], "dependence": c["dependence"], "day_vol_sd": c["day_vol_sd"], "tier": c["tier"],
                       "kind": c["kind"], "method": name, "n_total": len(d), "n_valid": n, "n_failed": nf, "fail_rate": nf / len(d), "failure_flag": s2.failure_flag(nf, len(d)),
                       "blocked_by_failures": s2.failure_blocks(nf, len(d), c["tier"] != "C"), "rejections": k, **status(k, n, c["tier"], name)})
    cmr = pd.DataFrame(cm); cmr.to_csv(out / "stage3_cell_results.csv", index=False)
    # candidate outcome
    co = []
    for name in METHODS:
        g = cmr[(cmr["method"] == name) & (cmr.tier != "C")]
        st = g.status.tolist(); aa = g[g.tier == "A"]
        co.append({"method": name, "role": "candidate (C3, frozen values)" if name == "c3" else "reference only", "gated_cells": len(g), "n_PASS": st.count("PASS"), "n_PASS_AMBIGUOUS": st.count("PASS_AMBIGUOUS"),
                   "n_FAIL": st.count("FAIL"), "n_FAIL_AMBIGUOUS": st.count("FAIL_AMBIGUOUS"), "v1_1_candidate_outcome": v11.classify_candidate([{"status": s} for s in st]),
                   "lowest_cell_rate": float(g.p_hat.min()), "highest_cell_rate": float(g.p_hat.max()), "tierA_highest": float(aa.p_hat.max()), "tierB_highest": float(g[g.tier == "B"].p_hat.max()),
                   "cells_blocked_by_failures": int(g.blocked_by_failures.sum())})
    pd.DataFrame(co).to_csv(out / "stage3_candidate_outcome.csv", index=False)
    # failure conditions (docs/13 4.7) evaluated for C3
    c3g = cmr[(cmr["method"] == "c3") & (cmr.tier != "C")]
    fc = [("1. any tier A cell outside its gate (C3: rate above 5.5%)", int((c3g[c3g.tier == "A"].p_hat > 0.055 + 1e-12).sum())),
          ("2. any tier B cell outside its gate (C3: rate above 6.0%)", int((c3g[c3g.tier == "B"].p_hat > 0.060 + 1e-12).sum())),
          ("ceiling: any validated cell above 7.0%", int((c3g.p_hat > 0.07).sum())),
          ("numerical: method-cells above 0.1% failures", int(cmr[cmr.tier != "C"].blocked_by_failures.sum())),
          ("clear FAIL or FAIL_AMBIGUOUS statuses for C3", int(c3g.status.isin(["FAIL", "FAIL_AMBIGUOUS"]).sum()))]
    pd.DataFrame([{"condition": k, "cells_violating": v, "triggered": v > 0} for k, v in fc]).to_csv(out / "stage3_failure_conditions.csv", index=False)
    # Stage 3 vs Stage 2 for the re-run development cells
    if S2CM.exists():
        s2cm = pd.read_csv(S2CM, keep_default_na=False)
        rep = []
        for r in [x for x in rows if x < s3.NEW_FIRST_ROW]:
            for name in METHODS:
                a3 = cmr[(cmr.val_row == r) & (cmr["method"] == name)].iloc[0]; a2 = s2cm[(s2cm.dev_row == r) & (s2cm["method"] == name)].iloc[0]
                rep.append({"val_row": r, "method": name, "stage2_rate": a2.p_hat, "stage3_rate": a3.p_hat, "diff": a3.p_hat - a2.p_hat, "z": s2.plumbing_z(int(a3.rejections), int(a3.n_valid), int(a2.rejections), int(a2.n_valid))})
        pd.DataFrame(rep).to_csv(out / "stage3_vs_stage2_repeat.csv", index=False)
    # conditional calibration with D2 where a matched df-infinity reference exists
    cc = []
    refrow = plan.set_index("val_row").d2_reference_row.to_dict()
    for r in rows:
        c = plan.loc[r]
        for name, m in (("baseline", "base"), ("c3", "c3")):
            for var, col in (("leverage", "maxshare"), ("kurtosis", "kurt"), ("own_critical_value", f"crit_{m}")):
                if var == "own_critical_value" and name == "c3":
                    continue
                def sp(row):
                    d = data.get(row)
                    if d is None:
                        return np.nan, np.full(4, np.nan)
                    v = d[d[f"valid_{m}"]]; q = s2.quartile_rates(v[col].to_numpy(), v[f"reject_{m}"].to_numpy())
                    return (s2.spread(q) if not np.isnan(q).all() else np.nan), q
                s_, q = sp(r); rr = int(refrow[r]); is_ref = c["tail"] == "G"
                s_ref = sp(rr)[0] if rr >= 0 and not is_ref else np.nan
                computable = rr >= 0 and not is_ref and np.isfinite(s_) and np.isfinite(s_ref)
                label = "" if is_ref else (s2.reference_label(c["dependence"], float(c["day_vol_sd"])) if rr >= 0 else "NO MATCHED df-infinity REFERENCE IN THE FROZEN GRID: D2 not computable as specified")
                cc.append({"val_row": r, "tail": c["tail"], "shape": c["shape"], "market": c["market"], "n_days": c["n_days"], "dependence": c["dependence"], "day_vol_sd": c["day_vol_sd"], "tier": c["tier"],
                           "kind": c["kind"], "method": name, "conditioning_variable": var, "q1": q[0], "q2": q[1], "q3": q[2], "q4": q[3], "spread": s_, "reference_val_row": rr if not is_ref else np.nan,
                           "reference_spread": s_ref, "d2_computable": bool(computable), "d2_flag_judgement_based": bool(computable and s2.d2_flag(s_, s_ref)), "d2_label": label})
    ccd = pd.DataFrame(cc); ccd.to_csv(out / "stage3_conditional_calibration.csv", index=False)
    print(pd.DataFrame(co).round(4).to_string(index=False))
    print("D2: computable comparisons", int(ccd.d2_computable.sum()), "| flagged", int(ccd.d2_flag_judgement_based.sum()), "| not computable (no reference)", int(((ccd.d2_label.str.startswith("NO MATCHED")) & (ccd.method == "c3")).sum()), "C3 comparisons")


if __name__ == "__main__":
    main()
