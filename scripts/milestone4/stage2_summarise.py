"""H1 calibration, STAGE 2, step E5: summarise the development run into the diagnostics approved in docs/17 + docs/17b (D1-D10).
WRITTEN IN E1; NOT RUN on real data until E4 has run.   Reads the per-cell parquet files; runs no simulation; writes new CSVs.   ALL DATA SIMULATED.
Outputs (folder --out, default outputs/milestone4/h1_calibration/stage2/summary/):
  stage2_cell_method_results.csv       rejection rate, Wilson interval, gate status, distance to the bound, failures and D6 blocking, per cell and method
  stage2_candidate_outcomes.csv        per method: v1.1 candidate outcome, ambiguous tier A cells vs the yardstick (D4), advancement-status check
  stage2_conditional_calibration.csv   quartile rates by leverage, kurtosis and own critical value; D2 flags (JUDGEMENT-BASED) with the unmatched-reference label
  stage2_critical_value_diagnostics.csv  CV, Spearman(T, crit), oracle q95 of T; D7 rule for C1 in the 40-cell scope (C3 exempt)
  stage2_c1_pvalue_deciles.csv         C1 Monte-Carlo p-value deciles (uniform under a calibrated test)
  stage2_plumbing_vs_stage1.csv        baseline vs Stage 1 baseline in the 30 overlapping cells (plumbing check, not validation)
  stage2_paired_vs_baseline.csv        discordant counts and sign test, C1 and C3 against the baseline on the same datasets
The baseline is a reference only; C2 does not exist in Stage 2.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage2_common as sc                                                 # noqa: E402
from quantlab.research import h1_calibration_v11 as v11, h1_stage2 as s2   # noqa: E402

DEV = sc.BASE / "stage2" / "development"
METHODS = {"baseline": "base", "c1": "c1", "c3": "c3"}


def load_cell(dev: Path, row: int) -> pd.DataFrame:
    """One cell's per-simulation results."""
    return pd.read_parquet(dev / f"cell_{row:02d}.parquet")


def status_for(k: int, n: int, tier: str, method: str) -> dict:
    """Gate status of one method-cell: two-sided v1.1 gate (baseline, C1), upper-limit-only (C3), report-only for df 3."""
    if tier == "C":
        return {"p_hat": k / n, "wilson_low": float(v11.wilson_interval(k, n)[0]), "wilson_high": float(v11.wilson_interval(k, n)[1]), "status": "REPORT_ONLY", "distance_se": np.nan}
    cl = v11.classify_cell(k, n, tier, c3_mode=(method == "c3"))
    lo, hi, _ = v11.GATES[tier]
    dist = s2.distance_to_bound_se(cl["p_hat"], n, -1.0 if method == "c3" else lo, hi)
    return {"p_hat": cl["p_hat"], "wilson_low": cl["wilson_low"], "wilson_high": cl["wilson_high"], "status": cl["status"], "distance_se": dist}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", default=str(DEV))
    ap.add_argument("--out", default=str(sc.BASE / "stage2" / "summary"))
    ap.add_argument("--rows", default=None, help="smoke only: comma-separated dev_rows present in --dev")
    a = ap.parse_args()
    dev, out = Path(a.dev), Path(a.out)
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} already has files.")
    out.mkdir(parents=True, exist_ok=True)
    plan = sc.load_plan()
    rows = [int(x) for x in a.rows.split(",")] if a.rows else list(plan.dev_row)
    data = {r: load_cell(dev, r) for r in rows}
    s1sum = pd.read_csv(sc.BASE / "stage1" / "stage1_cell_summary.csv", keep_default_na=False)

    # ---- per cell and method
    cm = []
    for r in rows:
        c, d = plan.loc[r], data[r]
        for name, m in METHODS.items():
            v = d[d[f"valid_{m}"]]
            k, n, nf = int(v[f"reject_{m}"].sum()), len(v), len(d) - len(v)
            gated = c["tier"] != "C"
            cm.append({"dev_row": r, "tail": c["tail"], "shape": c["shape"], "market": c["market"], "n_days": c["n_days"], "dependence": c["dependence"],
                       "day_vol_sd": c["day_vol_sd"], "tier": c["tier"], "method": name, "n_total": len(d), "n_valid": n, "n_failed": nf, "fail_rate": nf / len(d),
                       "failure_flag": s2.failure_flag(nf, len(d)), "blocked_by_failures_D6": s2.failure_blocks(nf, len(d), gated),
                       "rate_if_failures_counted_as_non_rejections": k / len(d), "rejections": k, **status_for(k, n, c["tier"], name)})
    cmr = pd.DataFrame(cm)
    cmr.to_csv(out / "stage2_cell_method_results.csv", index=False)

    # ---- candidate level (all 68 gated cells, only when the full grid is present)
    co = []
    for name in METHODS:
        g = cmr[(cmr.method == name) & (cmr.tier != "C")]
        st = g.status.tolist()
        a_st = g[g.tier == "A"].status.tolist()
        co.append({"method": name, "eligible": name in ("c1", "c3"), "role": {"baseline": "reference only (never selectable)", "c1": "preferred if it qualifies (D1)",
                                                                               "c3": "labelled fallback (D1)"}[name],
                   "gated_cells": len(g), "n_PASS": st.count("PASS"), "n_PASS_AMBIGUOUS": st.count("PASS_AMBIGUOUS"), "n_FAIL": st.count("FAIL"),
                   "n_FAIL_AMBIGUOUS": st.count("FAIL_AMBIGUOUS"), "v1_1_candidate_outcome": v11.classify_candidate([{"status": s} for s in st]),
                   "ambiguous_tierA_cells": sum(s.endswith("_AMBIGUOUS") for s in a_st), "tierA_cells": len(a_st), "ambiguous_yardstick_reached_D4": s2.ambiguous_flag(a_st),
                   "advancement_statuses_ok_D4": s2.can_advance_cell_statuses(st), "cells_blocked_by_failures_D6": int(g.blocked_by_failures_D6.sum()),
                   "lowest_cell_rate": float(g.p_hat.min()), "highest_cell_rate": float(g.p_hat.max())})
    pd.DataFrame(co).to_csv(out / "stage2_candidate_outcomes.csv", index=False)

    # ---- conditional calibration with D2 flags
    ref = {(c["shape"], c["market"], int(c["n_days"])): r for r, c in plan.iterrows() if c["tail"] == "G" and c["dependence"] == "none" and abs(float(c["day_vol_sd"]) - 0.3) < 1e-12}
    cc = []
    for r in rows:
        c = plan.loc[r]
        for name, m in (("baseline", "base"), ("c1", "c1"), ("c3", "c3")):
            for var, col in (("leverage", "maxshare"), ("kurtosis", "kurt"), ("own_critical_value", f"crit_{m}")):
                if var == "own_critical_value" and name == "c3":
                    continue                                                                       # C3's critical value is constant
                def spread_of(row):
                    d = data.get(row)
                    if d is None:
                        return np.nan, np.full(4, np.nan)
                    v = d[d[f"valid_{m}"]]
                    q = s2.quartile_rates(v[col].to_numpy(), v[f"reject_{m}"].to_numpy())
                    return s2.spread(q) if not np.isnan(q).all() else np.nan, q
                sp, q = spread_of(r)
                rr = ref.get((c["shape"], c["market"], int(c["n_days"])))
                sp_ref, _ = spread_of(rr) if rr is not None else (np.nan, None)
                is_ref = c["tail"] == "G"
                flag = (not is_ref) and np.isfinite(sp) and np.isfinite(sp_ref) and s2.d2_flag(sp, sp_ref)
                label = s2.reference_label(c["dependence"], float(c["day_vol_sd"])) if not is_ref else ""
                scope = s2.in_advancement_scope(c["tier"], int(c["n_days"]))
                cc.append({"dev_row": r, "tail": c["tail"], "shape": c["shape"], "market": c["market"], "n_days": c["n_days"], "dependence": c["dependence"],
                           "day_vol_sd": c["day_vol_sd"], "tier": c["tier"], "method": name, "conditioning_variable": var, "q1": q[0], "q2": q[1], "q3": q[2], "q4": q[3],
                           "spread": sp, "reference_dev_row": rr if not is_ref else np.nan, "reference_spread": sp_ref, "d2_flag_judgement_based": bool(flag),
                           "d2_label": label, "in_advancement_scope_40": scope, "counts_toward_advancement": bool(flag and scope)})
    pd.DataFrame(cc).to_csv(out / "stage2_conditional_calibration.csv", index=False)

    # ---- critical-value diagnostics and the D7 rule
    cd = []
    for r in rows:
        c, d = plan.loc[r], data[r]
        t = d["T"].dropna()
        entry = {"dev_row": r, "tail": c["tail"], "shape": c["shape"], "market": c["market"], "n_days": c["n_days"], "tier": c["tier"], "oracle_q95_T": float(np.quantile(t, 0.95))}
        for name, m in (("baseline", "base"), ("c1", "c1")):
            v = d[d[f"valid_{m}"]]
            entry[f"{name}_crit_mean"] = float(v[f"crit_{m}"].mean())
            entry[f"{name}_crit_cv"] = s2.cv(v[f"crit_{m}"])
            entry[f"{name}_spearman_T_crit"] = float(stats.spearmanr(v["T"], v[f"crit_{m}"])[0])
        entry["c3_crit"] = float(d["crit_c3"].iloc[0])
        entry["in_D7_scope_40"] = s2.in_advancement_scope(c["tier"], int(c["n_days"]))
        entry["c1_cv_below_baseline_cv"] = bool(entry["c1_crit_cv"] < entry["baseline_crit_cv"])
        entry["d7_violation_c1"] = bool(entry["in_D7_scope_40"] and not entry["c1_cv_below_baseline_cv"])
        cd.append(entry)
    pd.DataFrame(cd).to_csv(out / "stage2_critical_value_diagnostics.csv", index=False)

    # ---- C1 p-value deciles
    pv = []
    for r in rows:
        v = data[r][data[r].valid_c1]
        h = np.histogram(v["p_c1"], bins=np.linspace(0, 1, 11))[0] / len(v)
        pv.append({"dev_row": r, **{f"decile_{i + 1}": h[i] for i in range(10)}})
    pd.DataFrame(pv).to_csv(out / "stage2_c1_pvalue_deciles.csv", index=False)

    # ---- plumbing check vs Stage 1 (baseline only)
    s1i = s1sum.set_index("cell_row")
    pl = []
    for r in rows:
        ref_row = int(plan.loc[r, "stage1_reference_row"])
        if ref_row < 0:
            continue
        b = cmr[(cmr.dev_row == r) & (cmr.method == "baseline")].iloc[0]
        k1, n1 = int(s1i.loc[ref_row, "rejections"]), int(s1i.loc[ref_row, "n_valid"])
        z = s2.plumbing_z(int(b.rejections), int(b.n_valid), k1, n1)
        pl.append({"dev_row": r, "stage1_cell_row": ref_row, "stage2_rate": b.p_hat, "stage1_rate": k1 / n1, "z": z, "abs_z_over_3": bool(abs(z) > 3)})
    plf = pd.DataFrame(pl)
    plf.to_csv(out / "stage2_plumbing_vs_stage1.csv", index=False)

    # ---- paired comparison with the baseline
    pr = []
    for r in rows:
        d = data[r]
        for m in ("c1", "c3"):
            ok = d["valid_base"] & d[f"valid_{m}"]
            x, y = d.loc[ok, "reject_base"].to_numpy(bool), d.loc[ok, f"reject_{m}"].to_numpy(bool)
            b, c_ = int((x & ~y).sum()), int((~x & y).sum())
            pr.append({"dev_row": r, "method": m, "n_paired": int(ok.sum()), "baseline_only_rejects": b, "method_only_rejects": c_, "sign_test_p": s2.sign_test_p(b, c_)})
    pd.DataFrame(pr).to_csv(out / "stage2_paired_vs_baseline.csv", index=False)
    print(pd.DataFrame(co).round(4).to_string())
    if len(plf):
        print("plumbing: cells", len(plf), "with |z|>3:", int(plf.abs_z_over_3.sum()))


if __name__ == "__main__":
    main()
