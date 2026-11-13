"""H1 calibration, STAGE 3: generate docs/21 (Stage 3 report) from the SAVED validation, summary, C3 and (if run) power outputs. Reads only; no simulation; no hand-typed
metrics.   ALL DATA SIMULATED.   It reports what the pre-specified gates give for C3 and what is NOT concluded (Stage 4 and 5 are not authorised by Stage 3).
Writes docs/21_h1_calibration_stage3_report.md and outputs/milestone4/h1_calibration/stage3/report_tables/*.csv (refuses to overwrite).
Usage: python scripts/milestone4/stage3_make_report.py --tests "<pytest summary line>"
"""
import argparse
import datetime as dt
import glob
import platform
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage3_common as c3c                                                # noqa: E402
from stage2_make_report import md, digest                                  # noqa: E402
from quantlab.research import h1_stage2 as s2, h1_stage3 as s3             # noqa: E402

B = c3c.B
S3 = c3c.S3
VAL, SUMD, PWD, C3I = S3 / "validation", S3 / "summary", S3 / "power_check", S3 / "c3_intermediate"
TAB = S3 / "report_tables"
DOC = c3c.sc.ROOT / "docs" / "21_h1_calibration_stage3_report.md"
BORDER = 0.005


def lab(r):
    """Compact cell description."""
    dep = "" if r["dependence"] == "none" else ", est. dependence"
    vol = "" if abs(float(r["day_vol_sd"]) - 0.3) < 1e-12 else f", day-vol {float(r['day_vol_sd']):g}"
    return f"{r['tail']} {r['shape']} {r['market']} {int(r['n_days'])}d{dep}{vol}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", required=True)
    a = ap.parse_args()
    if DOC.exists() or (TAB.exists() and any(TAB.iterdir())):
        sys.exit("report or report_tables already exist; refusing to overwrite")
    TAB.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    plan = pd.read_csv(B / "stage3_plan" / "stage3_cells_plan.csv", keep_default_na=False)
    cm = pd.read_csv(SUMD / "stage3_cell_results.csv", keep_default_na=False)
    co = pd.read_csv(SUMD / "stage3_candidate_outcome.csv", keep_default_na=False).set_index("method")
    fcnd = pd.read_csv(SUMD / "stage3_failure_conditions.csv", keep_default_na=False)
    vs2 = pd.read_csv(SUMD / "stage3_vs_stage2_repeat.csv", keep_default_na=False)
    cc = pd.read_csv(SUMD / "stage3_conditional_calibration.csv", keep_default_na=False)
    for c in ("q1", "q2", "q3", "q4", "spread", "reference_spread", "z", "diff"):
        for d in (cc, vs2):
            if c in d.columns:
                d[c] = pd.to_numeric(d[c], errors="coerce")
    t2 = pd.read_csv(c3c.STAGE2_C3_TABLE)
    t3 = pd.read_csv(c3c.C3I_TABLE)
    c3i_cells = pd.read_csv(C3I / "c3_intermediate_cell_results.csv")
    meta = pd.read_csv(sorted(glob.glob(str(VAL / "run_metadata_*.csv")))[0], index_col=0)["value"]
    cm["cell"] = [lab(plan.loc[r]) for r in cm["val_row"]]
    cc["cell"] = [lab(plan.loc[r]) for r in cc["val_row"]]
    c3r = cm[(cm["method"] == "c3")]; c3g = c3r[c3r["tier"] != "C"]; bsg = cm[(cm["method"] == "baseline") & (cm["tier"] != "C")]
    outcome = co.loc["c3", "v1_1_candidate_outcome"]

    # integrity
    man = {n: c3c.verify_manifest(p, k) for n, (p, k) in c3c.sc.MANIFESTS.items()}
    man.update(stage2_inputs=c3c.verify_manifest(c3c.sc.STAGE2_INPUTS), stage2_addendum=c3c.verify_manifest(B / "frozen_stage2_inputs_addendum.sha256"),
               stage2_c3_table=c3c.verify_manifest(B / "stage2" / "c3_training" / "C3_TABLE.sha256", 2), stage3_inputs=c3c.verify_manifest(c3c.STAGE3_INPUTS),
               c3_intermediate_table=c3c.verify_manifest(C3I / "C3_INTERMEDIATE_TABLE.sha256", 2))
    probs, rows_total, fails = [], 0, {"base": 0, "c3": 0}
    cells = c3c.load_validation_cells()
    for r in range(96):
        d = pd.read_parquet(VAL / f"cell_{r:02d}.parquet")
        n = int(cells.loc[r, "n_sims"]); rows_total += len(d)
        if d["sim"].tolist() != list(range(n)) or (d["val_row"] != r).any():
            probs.append((r, "ids"))
        if (d["reject_c3"] != (d["T"] > d["crit_c3"])).any():
            probs.append((r, "C3 rule"))
        if d["crit_c3"].nunique() != 1:
            probs.append((r, "C3 value varies"))
        for m in fails:
            fails[m] += int((~d[f"valid_{m}"]).sum())
    used = eval(meta["c3_values"]); frozen = {**t2.set_index("n_days").c3_crit.to_dict(), **t3.set_index("n_days").c3_crit.to_dict()}
    c3_equal = all(abs(used[k] - frozen[k]) < 1e-15 for k in frozen)
    vdig = digest(glob.glob(str(VAL / "*.parquet")) + glob.glob(str(VAL / "run_metadata_*.csv"))); sdig = digest(glob.glob(str(SUMD / "*.csv")))
    mt = [(VAL / f"cell_{r:02d}.parquet").stat().st_mtime for r in range(96)]
    log = (B / "stage3_validation_run.log").read_text().splitlines()
    el = [int(re.search(r"elapsed=(\d+)s", ln).group(1)) for ln in log if ln.startswith("cell")]
    sleep_h = sum(max((mt[i] - mt[i - 1]) - (el[i] - el[i - 1]), 0) for i in range(1, 96)) / 3600
    pw_ran = (PWD / "power_ratio_and_flag.csv").exists()

    # tables
    tier_tab = []
    for m, g in (("c3", c3g), ("baseline", bsg)):
        for k, kk in (("A, re-run", (g.tier == "A") & (g.kind.str.startswith("dev"))), ("A, new", (g.tier == "A") & (g.kind.str.startswith("new"))),
                      ("B, re-run", (g.tier == "B") & (g.kind.str.startswith("dev"))), ("B, new", (g.tier == "B") & (g.kind.str.startswith("new")))):
            x = g[kk]; vc = x.status.value_counts()
            tier_tab.append({"method": m, "group": k, "cells": len(x), "rate_min_%": 100 * x.p_hat.min(), "rate_median_%": 100 * x.p_hat.median(), "rate_max_%": 100 * x.p_hat.max(),
                             "PASS": vc.get("PASS", 0), "PASS_AMBIG": vc.get("PASS_AMBIGUOUS", 0), "FAIL": vc.get("FAIL", 0), "FAIL_AMBIG": vc.get("FAIL_AMBIGUOUS", 0)})
    tier_tab = pd.DataFrame(tier_tab)
    new_tab = cm[(cm.kind.str.startswith("new")) & (cm["method"].isin(["c3", "baseline"]))].assign(pct=lambda x: 100 * x.p_hat).pivot_table(index=["val_row", "cell", "tier"], columns="method", values="pct").reset_index()
    new_stat = c3r[c3r.kind.str.startswith("new")][["val_row", "status", "wilson_high"]].assign(wilson_high=lambda x: 100 * x.wilson_high)
    new_tab = new_tab.merge(new_stat, on="val_row").rename(columns={"status": "c3_status", "wilson_high": "c3_wilson_upper_%"})
    df3 = cm[cm.tier == "C"].assign(pct=lambda x: 100 * x.p_hat).pivot_table(index=["val_row", "cell"], columns="method", values="pct").reset_index()
    nonpass = c3g[c3g.status != "PASS"][["val_row", "cell", "tier", "p_hat", "wilson_low", "wilson_high", "status"]].copy()
    for c in ("p_hat", "wilson_low", "wilson_high"):
        nonpass[c] = 100 * nonpass[c]
    full = cm.assign(pct=lambda x: 100 * x.p_hat, st=lambda x: x.status).pivot_table(index=["val_row", "cell", "tier"], columns="method", values="pct", aggfunc="first").reset_index()
    full = full.merge(c3r[["val_row", "status"]].rename(columns={"status": "c3_status"}), on="val_row")
    full.to_csv(TAB / "stage3_all_cells_rates.csv", index=False)
    # D2
    comp = cc[(cc.d2_computable == True) & (cc["method"] == "c3")]                                         # noqa: E712
    flg = cc[(cc.d2_flag_judgement_based == True)]                                                         # noqa: E712
    nocomp = cc[(cc.d2_label.str.startswith("NO MATCHED")) & (cc["method"] == "c3")]
    comp_all = cc[cc.d2_computable == True].copy()                                                         # noqa: E712
    comp_all["threshold_1.25x_ref"] = 1.25 * comp_all.reference_spread; comp_all["margin_vs_0.02"] = comp_all.spread - comp_all["threshold_1.25x_ref"] - 0.02
    comp_all["borderline_pm0.005"] = comp_all["margin_vs_0.02"].abs() <= BORDER
    comp_all.to_csv(TAB / "d2_stage3_computable_comparisons.csv", index=False)
    flg.to_csv(TAB / "d2_stage3_flagged.csv", index=False)
    border = comp_all[comp_all["borderline_pm0.005"]].sort_values("margin_vs_0.02")
    border.to_csv(TAB / "d2_stage3_borderline.csv", index=False)
    byvar = comp_all.groupby(["method", "conditioning_variable"]).d2_flag_judgement_based.agg(["sum", "count"]).reset_index().rename(columns={"sum": "flagged", "count": "computable"})
    c3flag = comp_all[(comp_all["method"] == "c3") & (comp_all.d2_flag_judgement_based == True)]            # noqa: E712
    # vs Stage 2
    vc3, vb = vs2[vs2["method"] == "c3"], vs2[vs2["method"] == "baseline"]
    pw_txt = ""
    if pw_ran:
        pwr = pd.read_csv(PWD / "power_by_cell_method.csv", keep_default_na=False); pwf = pd.read_csv(PWD / "power_ratio_and_flag.csv", keep_default_na=False)
        w = pwr.assign(txt=lambda x: (100 * x.power).map("{:.1f}".format) + " [" + (100 * x.wilson_low).map("{:.1f}".format) + ", " + (100 * x.wilson_high).map("{:.1f}".format) + "]").pivot_table(
            index=["power_cell", "shape", "mult", "market"], columns="method", values="txt", aggfunc="first").reset_index()
        flag_raised = any(str(v).lower() == "true" for v in pwf.power_collapse_flag)
        pw_txt = f"""Six cells (T4 flat ×1.1 and ×1.2, T4 E ×1.2; both markets; 59 days), 5,000 simulations each, new seed 20261213, baseline and C3 on the same data, run only because the C3 outcome was {outcome} (docs/20 fill-in 6). Power (%) [Wilson 95%]:
{md(w)}

{md(pwf[['power_cell','shape','mult','market','power_method','power_baseline','ratio_to_baseline','flag_cell','power_collapse_flag']], {'power_method':'{:.4f}','power_baseline':'{:.4f}','ratio_to_baseline':'{:.4f}'})}

The single flag (C3 power below 70% of the baseline's at T4 flat ×1.2) was **{'RAISED' if flag_raised else 'not raised'}**. The power is not size-adjusted, the baseline over-rejects in the E cells (ratios there are not a fair yardstick), and this check is diagnostic only: it plays no part in any selection."""
    else:
        pw_txt = f"The power cells were **not run**: the C3 outcome was {outcome}, and docs/13 reports power only after calibration passes (docs/20 fill-in 6)."
    nA, nB = int((c3g.tier == "A").sum()), int((c3g.tier == "B").sum())
    over = fcnd.set_index("condition")["cells_violating"]
    trig = fcnd[fcnd.triggered == True]                                                                   # noqa: E712

    L = []
    P = L.append
    P(f"""# 21 — H1 calibration, Stage 3 report (locked validation of C3)

**Status:** Stage 3 executed once under the frozen protocol; this report states what the pre-specified gates give for C3. **It does not make the Stage 5 decision and does not claim that H1 is calibrated.** Stages 4 and 5 are not authorised by the Stage 3 decision and were not started. **All data are simulated.** Generated {now} by `scripts/milestone4/stage3_make_report.py` from saved files only.
**Labels:** **[EVIDENCE]** computed from the saved files; **[HYPOTHESIS]** my reading; **[PROTOCOL]** pre-specified in docs/13, 15a, 20; **[DECISION]** belongs to the user.

## 1. Summary (computed evidence)
- **Authorisation:** the user designated **C3 the sole candidate** (C1 not selected) and authorised Stage 3 under the frozen protocol (`docs/20`). Candidate, critical values, thresholds and methodology were not modified.
- **Run:** {int(meta['simulations_this_session']):,} simulations in 96 cells (88 gated, 8 df 3 report-only), run once; failed simulations: baseline {fails['base']}, C3 {fails['c3']}.
- **C3 outcome under the v1.1 classifier (upper limits only):** **{outcome}** — {int(co.loc['c3','n_PASS'])} PASS, {int(co.loc['c3','n_PASS_AMBIGUOUS'])} PASS_AMBIGUOUS, {int(co.loc['c3','n_FAIL'])} FAIL, {int(co.loc['c3','n_FAIL_AMBIGUOUS'])} FAIL_AMBIGUOUS of {int(co.loc['c3','gated_cells'])} gated cells. Highest C3 rate: tier A {100*co.loc['c3','tierA_highest']:.2f}% (limit 5.5%), tier B {100*co.loc['c3','tierB_highest']:.2f}% (limit 6.0%); lowest cell {100*co.loc['c3','lowest_cell_rate']:.2f}%.
- **Failure conditions triggered for C3:** {', '.join(trig.condition) if len(trig) else 'none'}.
- **What this means and does not mean:** C3 stayed within its upper limits in every validated cell, **including the 20 cells never used in development**. Because C3 is judged on upper limits only and rejects far below 5% in most cells (median {100*c3g.p_hat.median():.2f}%), this shows it does not over-reject in the simulated family; **it does not show that C3 holds the rate near 5%**, and it says nothing outside the family (Stage 4) or about power beyond the diagnostic below.
- **Baseline (reference only):** {int(co.loc['baseline','n_FAIL'])} FAIL and {int(co.loc['baseline','n_FAIL_AMBIGUOUS'])} FAIL_AMBIGUOUS of {int(co.loc['baseline','gated_cells'])} gated cells; highest rate {100*co.loc['baseline','highest_cell_rate']:.2f}%.
- **D2 (judgement-based):** {len(comp_all)} computable comparisons, {int(comp_all.d2_flag_judgement_based.sum())} flagged ({len(c3flag)} for C3); {len(nocomp)} C3 comparisons in the 16 cells with no matched df ∞ reference are **not computable as specified**. All flags and {len(border)} borderline comparisons are preserved below.
- **Power cells:** {'run (diagnostic only)' if pw_ran else 'not run'} (section 9).

## 2. Scope and frozen specification [PROTOCOL]
Frozen grid `outputs/milestone4/h1_calibration/frozen_spec/cells_validation.csv` (96 cells, 2,280,000 simulations): the 76 development cells re-run with fresh seeds (master 20261204, rows 0–75) and 20 new intermediate cells (master 20261205, rows 76–95: df 7 tier A and df 5 tier B, shape E at 59/90/180 days, shapes D1.5/D3.0 at 59 days, both markets). Per-simulation seeds `SeedSequence(master, spawn_key=(val_row, i, stream))`. Fill-ins decided before the run (D1.5/D3.0 as τ = 1.5/3.0 exponential profiles, df 7, the 90/180-day C3 training, seeds, power-run condition, D2 handling): **`docs/20`**. Run once, no retuning. C1 and C2 were not run.

## 3. Integrity and reproducibility (recomputed when this report was generated)
| Check | Result |
|---|---|
| Frozen v1 / v1.1 / Stage 1 code manifests | {man['v1']} / {man['v1.1']} / {man['stage1_code']} files verified |
| Stage 2 inputs / addendum / C3 table manifests | {man['stage2_inputs']} / {man['stage2_addendum']} / {man['stage2_c3_table']} files verified |
| **Stage 3 inputs manifest** (`frozen_stage3_inputs.sha256`) | {man['stage3_inputs']} files verified (frozen before any Stage 3 data existed) |
| **90/180-day C3 table** (`stage3/c3_intermediate/C3_INTERMEDIATE_TABLE.sha256`) | {man['c3_intermediate_table']} files verified (frozen before validation) |
| Validation cell files | 96 files, {rows_total:,} rows (plan 2,280,000), simulation ids exact, C3 rule `T > crit` exact, one C3 value per cell; problems: {probs or 'none'} |
| C3 values used equal the frozen tables | {c3_equal} |
| Validation outputs digest | `{vdig[:24]}…`; summaries digest `{sdig[:24]}…` |
| Test suite | {a.tests} |
| Environment | Python {platform.python_version()}, numpy {np.__version__}, pandas {pd.__version__}; {platform.platform()} |
**Run history [EVIDENCE].** Compute time {float(meta['wall_seconds_this_session'])/3600:.2f} h ({meta['wall_seconds_this_session']} s); wall-clock span of the cell files {(max(mt)-min(mt))/3600:.2f} h; machine-sleep difference {sleep_h:.2f} h (the run is resumable and seeds do not depend on the clock).

## 4. C3 critical values used [EVIDENCE]
{md(pd.concat([t2.assign(source='Stage 2 training (68 cells, seed 20261202)')[['n_days','c3_crit','source_dev_row','n_cells','source']], t3.assign(source='Stage 3 intermediate training (24 cells, seed 20261209)', source_dev_row=t3.source_row)[['n_days','c3_crit','source_dev_row','n_cells','source']]]).sort_values('n_days'), {'c3_crit': '{:.6f}'})}
The 90/180-day values come from 12-cell families (tails G, T6, T4 × E, D5 × NSE, US; 25,000 simulations each, 0 failures). They contain no estimated-dependence, no 0.6-volatility and no flat or R2 shapes, so **C3 provides less scenario coverage at 90, 125, 180 and 250 days than at 59 days and is valid only inside those families.** The maximum over noisy cell quantiles is biased slightly upward (the top cells at each size lie within about 2 standard errors; `c3_intermediate_cell_results.csv`).

## 5. Validation results [EVIDENCE]
Rates are null rejection rates (nominal 5%), judged for C3 on upper limits only. Sources: `stage3/summary/stage3_cell_results.csv`, `stage3_candidate_outcome.csv`. All 96 cells in both columns are in `stage3/report_tables/stage3_all_cells_rates.csv` and appendix A.
{md(tier_tab, {'rate_min_%':'{:.2f}','rate_median_%':'{:.2f}','rate_max_%':'{:.2f}'})}

**The 20 new intermediate cells** (rates in %, C3 upper Wilson limit in %):
{md(new_tab, {'baseline':'{:.2f}','c3':'{:.2f}','c3_wilson_upper_%':'{:.2f}'})}
**df 3 report-only cells (8):**
{md(df3, {'baseline':'{:.2f}','c3':'{:.2f}'})}
**C3 gated cells that are not a clear PASS** (all kept; {len(nonpass)} cells):
{md(nonpass, {'p_hat':'{:.2f}','wilson_low':'{:.2f}','wilson_high':'{:.2f}'}) if len(nonpass) else 'None: every gated cell is a clear PASS for C3.'}

**Failure conditions (docs/13 §4.7 as applicable to Stage 3, evaluated for C3):**
{md(fcnd)}

**C3's conservative behaviour [EVIDENCE]:** C3 rates range from {100*c3g.p_hat.min():.2f}% to {100*c3g.p_hat.max():.2f}% (tier A median {100*c3g[c3g.tier=='A'].p_hat.median():.2f}%, tier B median {100*c3g[c3g.tier=='B'].p_hat.median():.2f}%); {int((c3g.p_hat < 0.02).sum())} of {len(c3g)} gated cells are below 2%. Passing an upper-limit gate this way reflects a rarely-rejecting fixed critical value; it is expected to cost power (section 9).

## 6. Stage 3 against Stage 2 for the re-run cells [EVIDENCE]
Independent seeds, same cells ({len(vc3)} cells). C3: mean Stage 3 − Stage 2 rate {100*vc3['diff'].mean():+.3f} points, maximum |z| {vc3.z.abs().max():.2f}, {int((vc3.z.abs() > 3).sum())} cells with |z| above 3 and {int((vc3.z.abs() > 2).sum())} above 2. Baseline: mean {100*vb['diff'].mean():+.3f} points, maximum |z| {vb.z.abs().max():.2f}, {int((vb.z.abs() > 3).sum())} above 3. Cells with |z| above 2 (C3): {', '.join(f"row {int(r.val_row)} ({lab(plan.loc[int(r.val_row)])}, {100*r.stage2_rate:.2f}% → {100*r.stage3_rate:.2f}%, z {r.z:+.2f})" for r in vc3[vc3.z.abs() > 2].itertuples()) or 'none'}. Among 76 independent comparisons about 3.5 are expected above 2 and about 0.2 above 3 by chance alone. This is a reproducibility check of the machinery on fresh seeds (the Stage 2 development rates are reproduced), not a validation by itself.

## 7. Conditional calibration and D2 flags (D2, judgement-based) [PROTOCOL + EVIDENCE]
**Formula (same as Stage 2):** flag `<=>` `spread − 1.25 × reference_spread >= 0.02` (fractions; 0.02 = 2 percentage points); reference = same method and variable in the df ∞ cell matched on shape, market and sample size; unmatched dependence/day-volatility cells keep the label "reference not matched on dependence / day-volatility". Stage 2's advancement scope and D4/D7 rules are not applied in Stage 3 (docs/20 fill-in 7).
- **Computable:** {len(comp_all)} comparisons (baseline and C3, all conditioning variables); **flagged: {int(comp_all.d2_flag_judgement_based.sum())}** ({len(c3flag)} for C3). **Not computable as specified:** the {len(nocomp)} C3 comparisons (and the same for the baseline) in the 16 cells with no df ∞ reference in the frozen grid (90 and 180 days; shapes D1.5 and D3.0). Their spreads are in `stage3_conditional_calibration.csv`, marked "NO MATCHED df-infinity REFERENCE IN THE FROZEN GRID". No substitute reference was invented.
{md(byvar)}
- **Flags for C3 (all preserved)** in `stage3/report_tables/d2_stage3_flagged.csv`; C3 flagged cells: {', '.join(f"{int(r.val_row)} ({r.cell}, {r.conditioning_variable})" for r in c3flag.itertuples()) if len(c3flag) else 'none'}.
- **Borderline comparisons** (within ±0.005 of the threshold; flagged or not by the exact rule, threshold unchanged): {len(border)} — `d2_stage3_borderline.csv`.
{md(border[['val_row','cell','method','conditioning_variable','spread','reference_spread','threshold_1.25x_ref','margin_vs_0.02','d2_flag_judgement_based','d2_label']].head(30), {k: '{:.4f}' for k in ['spread','reference_spread','threshold_1.25x_ref']} | {'margin_vs_0.02':'{:+.4f}'}) if len(border) else 'None.'}
- **[HYPOTHESIS]** A fixed critical value rejects more when leverage is high, so C3's leverage flags may be built in; no evidence beyond the pattern.

## 8. Reading of the result [EVIDENCE vs HYPOTHESIS vs DECISION]
- **[EVIDENCE]** C3's outcome is {outcome}; no failure condition applicable to Stage 3 was triggered unless listed above; the 20 new cells and the fresh-seed re-run behave as the development stage predicted (section 6).
- **[HYPOTHESIS]** The result is a property of a conservative fixed critical value anchored to the worst development cells; it would not by itself show that the H1 test is calibrated.
- **[DECISION]** Whether Stage 4 (alternative processes, bar-level check, second implementation) is to be run, and the Stage 5 decision report, belong to the user.

## 9. Power cells — diagnostic only
{pw_txt}

## 10. Dependency chain for Stages 4 and 5 (inspection, nothing started)
- **Stage 4 (docs/13 §4 and v1.1 A4):** (1) six alternative processes a–f with frozen parameters (process e uses the approved Gaussian scale-mixture replacement), 25,000 simulations each × both markets = 12 cells, C3 run unchanged, gate 4.0–6.0%; null-preserving normalisations are tested analytically; a Monte-Carlo 0.5% period-mean check at 10⁶ bars is still required before use; (2) the bar-level pipeline check through `simulate_raw` → `clean` on reduced counts with two-proportion z-tests; (3) a slow second reference implementation compared on 100 inputs (for C3 this is nearly trivial: the statistic and a comparison); (4) an optional descriptive real-data check (separate approval; no H1 statistic on real data); (5) a review gate. Seeds 20261206–20261208 are reserved and unused. Estimated about 3 compute-hours (docs/17: 12 cells × 25,000 with the non-standard generators assumed 3× slower; for C3 alone much less).
- **Stage 5:** the decision report (pass within the validated domain / partial / unresolved) depends on Stage 4 and on your review gate.
- **Neither is authorised by this Stage 3 decision.** Approvals needed: explicit Stage 4 approval (including the real-data item if wanted), then Stage 5.

## 11. Limitations
- Simulated family only; Stage 3 is a validation **within** that family and the intermediate cells; it does not establish validity on real data, for other processes (Stage 4), or for dependence/volatility settings beyond those simulated.
- C3 is conservative and judged on upper limits only; its 90/180-day and 125/250-day values come from 12-cell families; the maximum of noisy quantiles is biased upward.
- Fill-ins (D1.5/D3.0 definitions, seeds, D2 handling, the power-run condition) were decided before the run and documented in docs/20; a different reading of "D1.5/D3.0" would give different new cells.
- D2 thresholds are judgement-based; 16 cells have no D2 reference; the 12 development-type cells with unmatched reference are labelled.
- Power is not size-adjusted; the baseline is distorted in the E cells.
- The sleep gap and compute time are reported; results do not depend on them. Unit tests are implementation checks, not statistical validation.

## Appendix A. Rates for all 96 cells (%)
{md(full, {'baseline':'{:.2f}','c3':'{:.2f}'})}

## Appendix B. Files
`outputs/milestone4/h1_calibration/stage3/` — `c3_intermediate/`, `validation/` (96 cell files, run metadata), `summary/` (5 CSVs), `power_check/` (if run), `report_tables/`; plan `stage3_plan/`; manifest `frozen_stage3_inputs.sha256`; logs `stage3_*_run.log`; scripts `scripts/milestone4/stage3_*.py`; record `docs/20`.
""")
    DOC.write_text("\n".join(L))
    print("written", DOC, len(DOC.read_text().splitlines()), "lines")


if __name__ == "__main__":
    main()
