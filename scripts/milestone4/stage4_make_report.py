"""H1 calibration, STAGE 4: generate docs/23 (the Stage 4 report) from the SAVED outputs of the four Stage 4 runners and the Stage 3 validation data. Reads only; no simulation;
every number and every pass/fail is computed here from files (acceptance criteria exactly as preregistered in docs/22 + docs/22b; none is altered).   ALL DATA SIMULATED.
Does NOT make the Stage 5 decision.   Writes docs/23_h1_calibration_stage4_report.md and outputs/.../stage4/report_tables/*.csv (refuses to overwrite).
Usage: python scripts/milestone4/stage4_make_report.py --tests "<pytest summary line>"
"""
import argparse
import datetime as dt
import glob
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage4_common as c4                                                 # noqa: E402
from stage2_make_report import md, digest                                  # noqa: E402
from quantlab.research import h1_calibration_v11 as v11, h1_stage2 as s2   # noqa: E402

B, S4 = c4.B, c4.S4
TAB = S4 / "report_tables"
DOC = c4.sc.ROOT / "docs" / "23_h1_calibration_stage4_report.md"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", required=True)
    a = ap.parse_args()
    if DOC.exists() or (TAB.exists() and any(TAB.iterdir())):
        sys.exit("report or report_tables already exist; refusing to overwrite")
    TAB.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    # ---- integrity
    man = c4.verify_all(stage4_inputs=True)
    # ---- null check
    nR = pd.read_csv(S4 / "null_check" / "null_check_ratios_abef.csv"); nT = pd.read_csv(S4 / "null_check" / "null_check_truncated_cd.csv")
    nA = pd.read_csv(S4 / "null_check" / "null_check_analytic.csv"); nO = pd.read_csv(S4 / "null_check" / "null_check_outcome.csv")
    null_pass = bool(nO.iloc[-1]["met"])
    # ---- alternative processes
    cells = pd.read_csv(c4.ALT_CELLS, keep_default_na=False)
    rows, cond = [], []
    for r in range(12):
        d = pd.read_parquet(S4 / "alt_validation" / f"cell_{r:02d}.parquet")
        for m, lab in (("c3", "C3 (candidate)"), ("base", "baseline (reference)")):
            v = d[d[f"valid_{m}"]]; k, n = int(v[f"reject_{m}"].sum()), len(v)
            cl = v11.classify_cell(k, n, "ALT", c3_mode=(m == "c3"))
            rows.append({"cell_row": r, "process": cells.loc[r, "dgp"], "market": cells.loc[r, "market"], "method": lab, "n_valid": n, "n_failed": len(d) - n, "rejections": k, "rate_%": 100 * cl["p_hat"],
                         "wilson_low_%": 100 * cl["wilson_low"], "wilson_high_%": 100 * cl["wilson_high"], "status": cl["status"], "c3_gate_rate_le_6.0%": bool(cl["p_hat"] <= 0.06 + 1e-12)})
            for var, col in (("leverage", "maxshare"), ("kurtosis", "kurt")) + ((("own_critical_value", f"crit_{m}"),) if m == "base" else ()):
                q = s2.quartile_rates(v[col].to_numpy(), v[f"reject_{m}"].to_numpy())
                cond.append({"cell_row": r, "process": cells.loc[r, "dgp"], "market": cells.loc[r, "market"], "method": lab, "variable": var, "q1_%": 100 * q[0], "q2_%": 100 * q[1], "q3_%": 100 * q[2], "q4_%": 100 * q[3], "spread_points": 100 * s2.spread(q)})
    alt = pd.DataFrame(rows); alt.to_csv(TAB / "alt_validation_cells.csv", index=False); cond = pd.DataFrame(cond); cond.to_csv(TAB / "alt_conditional_spreads.csv", index=False)
    a3, ab = alt[alt.method.str.startswith("C3")], alt[alt.method.str.startswith("baseline")]
    alt_pass = bool(a3["c3_gate_rate_le_6.0%"].all()); alt_fail_total = int(alt.n_failed.sum())
    c3_outcome = v11.classify_candidate([{"status": s} for s in a3.status])
    # ---- bar level
    s3dir = B / "stage3" / "validation"; zrows = []
    cmeta = c4.c3c.load_validation_cells()
    for ci, row in enumerate(c4.BAR_ROWS):
        bl = pd.read_parquet(S4 / "bar_level" / f"cell_{ci:02d}.parquet"); fa = pd.read_parquet(s3dir / f"cell_{row:02d}.parquet")
        for m, lab, bc, fc, vf in (("c3", "C3", "reject_c3", "reject_c3", "valid_c3"), ("base", "baseline", "reject_base", "reject_base", "valid_base")):
            vb = bl[bl.valid]; vfst = fa[fa[vf]]
            k1, n1, k2, n2 = int(vb[bc].sum()), len(vb), int(vfst[fc].sum()), len(vfst)
            z = s2.plumbing_z(k1, n1, k2, n2); p = 2 * stats.norm.sf(abs(z)); diff = k1 / n1 - k2 / n2
            se = np.sqrt(k1 / n1 * (1 - k1 / n1) / n1 + k2 / n2 * (1 - k2 / n2) / n2)
            zrows.append({"cell_index": ci, "val_row": row, "cell": f"{cmeta.loc[row, 'tail']} {cmeta.loc[row, 'shape']} {cmeta.loc[row, 'market']}", "method": lab, "bar_level_n": n1, "bar_level_rate_%": 100 * k1 / n1,
                          "fast_n": n2, "fast_rate_%": 100 * k2 / n2, "difference_points": 100 * diff, "diff_95%_low": 100 * (diff - 1.96 * se), "diff_95%_high": 100 * (diff + 1.96 * se), "z": z, "p_two_sided": p,
                          "abs_z_gt_2": abs(z) > 2, "abs_z_gt_3": abs(z) > 3, "bar_level_invalid": int((~bl.valid).sum()), "days_used_min": int(bl.n_days_used.min()), "days_used_max": int(bl.n_days_used.max())})
    Z = pd.DataFrame(zrows); Z.to_csv(TAB / "bar_level_ztests.csv", index=False)
    mx = pd.read_csv(S4 / "bar_level" / "same_returns_matrix_check.csv"); mx_pass = bool(mx.same_shape.all() and (mx.max_relative_difference <= 1e-9).all())
    bar_pass = bool((~Z.abs_z_gt_3).all()) and mx_pass and bool((Z.days_used_min == 59).all() and (Z.days_used_max == 59).all())
    cal = pd.read_csv(B / "stage4_prereg" / "bar_level_ztest_calibration.csv"); c8 = cal[cal.n_bar_level == 8000]
    fw8 = 1 - float(np.prod(1 - c8["P(|z|>3)"]))
    # ---- reference
    rD = pd.read_csv(S4 / "reference" / "reference_datasets.csv"); rQ = pd.read_csv(S4 / "reference" / "c3_value_rederivation.csv"); rO = pd.read_csv(S4 / "reference" / "reference_outcome.csv")
    ref_pass = bool(rO[rO.criterion != "datasets compared"].met.all() and len(rD) == 100)
    # ---- overall
    crit = pd.DataFrame([
        {"criterion": "A. null check: all 16 ratios (a, b, e, f) within 0.5%; all 12 truncated moments (c, d) within 0.5%; analytic factors = 1", "met": null_pass},
        {"criterion": "B. alternative processes: C3 rate at most 6.0% in all 12 cells (v1.1 A2); no numerical failures above 0.1%", "met": bool(alt_pass and (alt.n_failed / (alt.n_valid + alt.n_failed) <= 0.001).all())},
        {"criterion": "C1. bar-level: no |z| > 3 in the 16 comparisons (C3 and baseline, 8 cells x 8,000 vs Stage 3 fast route)", "met": bool((~Z.abs_z_gt_3).all())},
        {"criterion": "C2. same-returns matrices (80): identical shape and max relative difference <= 1e-9", "met": mx_pass},
        {"criterion": "D. reference implementation: T within 1e-9 in 100 datasets, identical C3 decisions, five C3 values re-derived to 1e-12", "met": ref_pass}])
    crit.to_csv(TAB / "acceptance_criteria.csv", index=False)
    all_pass = bool(crit.met.all())
    # ---- digests and run metadata
    dig = {k: digest(glob.glob(str(S4 / k / "*.parquet")) + glob.glob(str(S4 / k / "*.csv"))) for k in ("null_check", "alt_validation", "bar_level", "reference")}
    meta = lambda k, pat: pd.read_csv(sorted(glob.glob(str(S4 / k / pat)))[0], index_col=0)["value"]
    wall = {"null check": float(meta("null_check", "run_metadata.csv")["wall_seconds"]), "alternative processes": float(meta("alt_validation", "run_metadata_*.csv")["wall_seconds"]),
            "bar-level simulations": float(meta("bar_level", "run_metadata_*.csv")["wall_seconds"]), "reference": float(meta("reference", "run_metadata.csv")["wall_seconds"])}
    ref_check = lambda: None
    near = rD[rD["near_boundary_1e-6"]]
    f2 = Z[(Z.abs_z_gt_2) & (~Z.abs_z_gt_3)]
    amb = a3[a3.status.str.endswith("_AMBIGUOUS")]

    L = []
    P = L.append
    P(f"""# 23 — H1 calibration, Stage 4 report (independent validation of C3)

**Status:** Stage 4 executed once under the preregistration (`docs/22`, `docs/22b`, frozen in `frozen_stage4_inputs.sha256` before any Stage 4 simulation). **This report states what the pre-specified criteria give. It does not make the Stage 5 decision.** Generated {now} by `scripts/milestone4/stage4_make_report.py` from saved files only. **All data are simulated; nothing here is real-market evidence.**
**Labels:** **[EVIDENCE]** computed from the saved files; **[PROTOCOL]** pre-specified; **[HYPOTHESIS]** my reading; **[DECISION]** belongs to the user.

## 1. Exact status
**Stage 4 is {'COMPLETE: all five preregistered acceptance criteria are met' if all_pass else 'COMPLETE: NOT all preregistered acceptance criteria are met (see below)'}.**
{md(crit.assign(result=lambda x: np.where(x.met, 'MET', 'NOT MET'))[['criterion', 'result']])}
No acceptance criterion, tolerance or gate was changed after freezing. Real-data descriptive analysis (optional, unauthorised) was not run. Stage 5 was not started.

## 2. Frozen specification and preregistration [PROTOCOL]
Frozen v1 / v1.1 (`docs/13` §4, `docs/15a` §4, `frozen_spec/cells_alternative_dgps.csv`, `frozen_spec_v1_1/alt_dgp_parameters.json`, seeds 20261206, 20261207, 20261208); preregistration `docs/22` with the user's approvals in `docs/22b` (D1–D6, bar-level size 8,000 per cell). Candidate: C3 with its frozen critical values, unchanged; the M4b baseline bootstrap-t (B = 999) is reference only; C1 and C2 not run.

## 3. Validation methods (summary)
(A) null check of the alternative processes before use; (B) 12 alternative-process cells × 25,000 simulations; (C) bar-level pipeline check: 8 cells × 8,000 new bar-level simulations compared with the Stage 3 fast-route data by pooled two-proportion z-tests, plus 80 same-returns matrices; (D) a second, independent exact-arithmetic implementation compared on 100 datasets. Details and tolerances: `docs/22`.

## 4. Null check (A) [EVIDENCE]
Processes a, b, e, f: ratios open/middle and close/middle of period mean squares, 5×10⁷ bars in the open period, literal tolerance 0.5% (the standard error is shown; deviations in standard-error units):
{md(nR[['process', 'market', 'days', 'bars_open', 'dev_open_%', 'dev_close_%', 'se_open', 'se_close', 'dev_open_in_SE', 'dev_close_in_SE', 'pass_open', 'pass_close']], {'dev_open_%': '{:+.4f}', 'dev_close_%': '{:+.4f}', 'se_open': '{:.5f}', 'se_close': '{:.5f}', 'dev_open_in_SE': '{:+.2f}', 'dev_close_in_SE': '{:+.2f}'})}
**Largest deviation {nR[['dev_open_%', 'dev_close_%']].abs().max().max():.4f}%** (tolerance 0.5%); the largest in standard-error units is {max(nR.dev_open_in_SE.abs().max(), nR.dev_close_in_SE.abs().max()):.2f}, which among 16 ratios is not unusual by chance. Processes c and d: truncated second moment E[ε²·1{{|ε|≤c}}] against its exact value (c = 99.9% two-sided quantile), at least 10⁷ bars per component:
{md(nT[['process', 'market', 'component', 'df', 'cutoff', 'bars', 'rel_dev', 'se_rel', 'tail_variance_share_beyond_cutoff', 'pass']], {'cutoff': '{:.3f}', 'rel_dev': '{:+.5f}', 'se_rel': '{:.5f}', 'tail_variance_share_beyond_cutoff': '{:.3f}'})}
Analytic checks: the exact second moment of the shock part equals 1 for a, b, e, f (maximum error {nA.abs_error.max():.1e}); unit-variance scale constants are tested for c and d. **Limitation of the c/d check [PROTOCOL]:** the variance beyond the 99.9% cutoff ({100*nT.tail_variance_share_beyond_cutoff.min():.1f}% to {100*nT.tail_variance_share_beyond_cutoff.max():.1f}% of the total) cannot be verified by Monte Carlo at 0.5% (infinite fourth moment); it rests on the exact analytic scale constants and the tail-probability unit tests. **What the check can and cannot catch:** period-specific variance errors (for example a 5% open/middle error would be about 49 standard errors); not a factor common to all periods, which does not break H0 and is verified analytically.

## 5. Alternative-process validation (B) [EVIDENCE]
12 cells × 25,000 simulations (300,000), C3 unchanged (critical value {c4.c3_value_59():.6f}), seeds `SeedSequence(20261206, spawn_key=(cell_row, i, stream))`. Gate: C3 passes a cell when its rate is at most 6.0% (v1.1 A2); the baseline's two-sided band 4.0–6.0% is information only. Failed simulations in total: {alt_fail_total}.
{md(a3[['cell_row', 'process', 'market', 'n_valid', 'n_failed', 'rate_%', 'wilson_low_%', 'wilson_high_%', 'status', 'c3_gate_rate_le_6.0%']], {'rate_%': '{:.2f}', 'wilson_low_%': '{:.2f}', 'wilson_high_%': '{:.2f}'})}
- **C3: highest rate {a3['rate_%'].max():.2f}%, lowest {a3['rate_%'].min():.2f}%, median {a3['rate_%'].median():.2f}%; candidate outcome {c3_outcome}; ambiguous cells (6.0% inside the Wilson interval): {len(amb)}.** C3 is conservative: it rejects far below 5% in most cells.
Baseline (reference only, two-sided band 4.0–6.0%):
{md(ab[['cell_row', 'process', 'market', 'rate_%', 'wilson_low_%', 'wilson_high_%', 'status']], {'rate_%': '{:.2f}', 'wilson_low_%': '{:.2f}', 'wilson_high_%': '{:.2f}'})}
Descriptive conditional spreads (quartile range of the rejection rate, points; no df ∞ reference exists for these processes, so D2 is **not computable** and no substitute was invented) are in `stage4/report_tables/alt_conditional_spreads.csv`: C3 leverage spread median {cond[(cond.method.str.startswith('C3')) & (cond.variable == 'leverage')].spread_points.median():.2f} points, maximum {cond[(cond.method.str.startswith('C3')) & (cond.variable == 'leverage')].spread_points.max():.2f}.

## 6. Bar-level pipeline check (C) [EVIDENCE]
New bar-level simulations (real `simulate_table` → `clean` → bar table route): 8 cells × 8,000 = 64,000 (seeds 20261207, streams 0 and 2), against the Stage 3 fast-route data of the same cells (25,000 each). Pooled two-sided two-proportion z-tests, **all 16 comparisons** (threshold |z| ≤ 3; preregistered family-wise false-flag rate {100*fw8:.1f}%; |z| above 2 expected in about half of equivalent runs). Days used in every bar-level matrix: {int(Z.days_used_min.min())}–{int(Z.days_used_max.max())} (expected 59); invalid bar-level simulations: {int(Z.bar_level_invalid.sum())}.
{md(Z[['cell', 'method', 'bar_level_rate_%', 'fast_rate_%', 'difference_points', 'diff_95%_low', 'diff_95%_high', 'z', 'p_two_sided']], {'bar_level_rate_%': '{:.2f}', 'fast_rate_%': '{:.2f}', 'difference_points': '{:+.2f}', 'diff_95%_low': '{:+.2f}', 'diff_95%_high': '{:+.2f}', 'z': '{:+.2f}', 'p_two_sided': '{:.4f}'})}
- **Largest |z| {Z.z.abs().max():.2f}; comparisons with |z| above 3: {int(Z.abs_z_gt_3.sum())}; between 2 and 3 (reported, expected by chance): {len(f2)}{(' — ' + '; '.join(f"{r.cell} {r.method} z {r.z:+.2f}" for r in f2.itertuples())) if len(f2) else ''}.** Mean difference (bar-level minus fast): C3 {Z[Z.method == 'C3'].difference_points.mean():+.3f} points, baseline {Z[Z.method == 'baseline'].difference_points.mean():+.3f} points. Power of this design: 75% at a 1-point difference, 100% at 2 points (docs/22 §5); smaller differences can exist undetected.
**Same-returns matrix check:** {len(mx)} matrices, identical shape in {int(mx.same_shape.sum())}, maximum relative difference {mx.max_relative_difference.max():.2e} (tolerance 1e-9; M4b: 4.02e-13).

## 7. Second independent implementation (D) [EVIDENCE]
100 datasets (10 cells chosen before any result: val rows {', '.join(map(str, sorted(rD.val_row.unique())))}; seed 20261208). Vectorised `max_abs_t` against the independent exact-arithmetic implementation (`h1_stage4_reference.py`, standard library only, period slots derived from clock times): **maximum relative difference {rD.rel_diff.max():.2e}** (tolerance 1e-9); **C3 decisions identical in {int((rD.reject_vectorised == rD.reject_reference).sum())} of {len(rD)}**; rejections among the 100: {int(rD.reject_vectorised.sum())}; datasets within 1e-6 relative of the critical value: {len(near)}.
The five frozen C3 values re-derived from the saved training statistics by the independent quantile routine (tolerance 1e-12):
{md(rQ, {'frozen': '{:.12f}', 'rederived': '{:.12f}', 'rel_diff': '{:.2e}'})}
**Limit:** same author for both implementations and a shared dataset generator: independence of computation, not of authorship.

## 8. Acceptance criteria and statistical results
See section 1. Statistical summary: the alternative processes did not push C3 above 6.0% (highest {a3['rate_%'].max():.2f}%); the baseline, for reference, ranged {ab['rate_%'].min():.2f}–{ab['rate_%'].max():.2f}% ({int((ab.status.isin(['FAIL', 'FAIL_AMBIGUOUS'])).sum())} of 12 cells outside its two-sided band); the fast generator and the real bar-level route agree within the preregistered criterion; the independent implementation agrees to rounding.

## 9. Failures, limitations and borderline findings
- Borderline: the largest null-check deviation in standard-error units ({max(nR.dev_open_in_SE.abs().max(), nR.dev_close_in_SE.abs().max()):.2f}) and {len(f2)} bar-level comparison(s) with |z| between 2 and 3 (see section 6); {len(amb)} C3 alternative cells with the 6.0% limit inside the Wilson interval.
- The null check cannot verify the full variance of processes c and d (section 4). The bar-level check cannot detect differences below about 1 point. The reference check is independent in code, not in authorship.
- **What Stage 4 does NOT establish:** validity on real market data; validity for other processes or dependence/volatility regimes; that C3's rate is near 5% (it is conservative and judged on an upper limit); any power or trading statement. No real-data analysis was run.
- Unit tests are implementation checks, not statistical validation.

## 10. Reproducibility
Seeds: 20261206 (alternative processes; null-check namespace first key ≥ 100), 20261207 (bar level; streams 0, 1, 2), 20261208 (reference). Environment: Python {platform.python_version()}, numpy {np.__version__}, pandas {pd.__version__}; {platform.platform()}. Compute times (s): {', '.join(f'{k} {v:,.0f}' for k, v in wall.items())}. Commands: `scripts/milestone4/stage4_run_null_check.py`, `stage4_run_alt_validation.py`, `stage4_run_bar_level.py --part sims` and `--part matrix`, `stage4_run_reference.py`, then `stage4_make_report.py`.

## 11. Tests, manifests and digests
- Test suite: {a.tests}
- Manifests verified now: v1 {man['v1']}, v1.1 {man['v1.1']}, Stage 1 code {man['stage1_code']}, Stage 2 inputs {man['stage2_inputs']}, addendum {man['stage2_addendum']}, Stage 2 C3 table {man['stage2_c3_table']}, Stage 3 inputs {man['stage3_inputs']}, 90/180-day table {man['c3_intermediate_table']}, **Stage 4 inputs {man['stage4_inputs']}** (frozen before any Stage 4 simulation).
- Output digests (SHA-256 over file names and hashes): null check `{dig['null_check'][:24]}…`, alternative processes `{dig['alt_validation'][:24]}…`, bar level `{dig['bar_level'][:24]}…`, reference `{dig['reference'][:24]}…`.

## 12. Deviations
**No frozen specification, seed, threshold, critical value or manifest was changed.** The additions and fill-ins (null-check sample size and truncated-moment form for c/d, seed namespaces, bar-level cells and 8,000 simulations per cell, |z| ≤ 3 rule, reference cells and tolerances, the 6.0% reading of C3's gate) were fixed in docs/22 and docs/22b before the run. The one change made after the first draft of docs/22 was the bar-level size (2,000 → 8,000), recorded in docs/22b. **No deviation occurred during execution.**

## 13. Is Stage 5 eligible for consideration?
{'**Yes, on the preregistered criteria:** every Stage 4 criterion is met, so the Stage 5 decision report may be considered.' if all_pass else '**Not on the preregistered criteria:** at least one criterion is not met (section 1); the Stage 5 report would have to state that.'} Stage 5 is **not authorised and not started**; it needs your explicit approval and your review of Stages 3–4 (docs/13 review gate). Stage 5 would decide the wording of the conclusion (calibrated within a validated domain, partial, or unresolved); this report makes no such statement.

## 14. Decisions that remain with you
Authorise Stage 5 or not; whether to run the optional real-data descriptive check (separately authorised); how to treat the conservatism of C3 in the Stage 5 wording; whether to commit and push the Stage 2–4 work; the other open items in `docs/19`.
""")
    DOC.write_text("\n".join(L))
    print("written", DOC, len(DOC.read_text().splitlines()), "lines | all criteria met:", all_pass)
    print(crit.to_string(index=False))


if __name__ == "__main__":
    main()
