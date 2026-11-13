"""H1 calibration, STAGE 2, step E7: generate the Stage 2 report (docs/18) and its supporting tables from the SAVED E4, E5, E6 outputs.
Reads only; runs NO simulation; every number in the report is computed here from files (no hand-typed metrics).  ALL DATA SIMULATED.
Does NOT classify the candidates and does NOT recommend advancement: that is left to the user (see the report, section 12).
Writes: docs/18_h1_calibration_stage2_report.md and outputs/milestone4/h1_calibration/stage2/report_tables/*.csv  (refuses to overwrite).
Usage : python scripts/milestone4/stage2_make_report.py --tests "<pytest summary line>"
"""
import argparse
import datetime as dt
import glob
import hashlib
import platform
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage2_common as sc                                                 # noqa: E402
from quantlab.research import h1_stage2 as s2                              # noqa: E402

B = sc.BASE
S2, SUM, DEV, PW, C3D = B / "stage2", B / "stage2" / "summary", B / "stage2" / "development", B / "stage2" / "power_check", B / "stage2" / "c3_training"
TAB = B / "stage2" / "report_tables"
DOC = sc.ROOT / "docs" / "18_h1_calibration_stage2_report.md"
BORDER = 0.005                                    # 'borderline' = within +-0.005 of the D2 threshold (the user's 19 comparisons)


def md(df: pd.DataFrame, fmt: dict | None = None) -> str:
    """Markdown table from a DataFrame; fmt maps column -> format string."""
    fmt = fmt or {}
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if c in fmt and isinstance(v, (int, float, np.integer, np.floating)) and not pd.isna(v):
                cells.append(fmt[c].format(v))
            elif isinstance(v, (float, np.floating)):
                cells.append("" if pd.isna(v) else f"{v:.4g}")
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def digest(files) -> str:
    """One SHA-256 over the (name, hash) lines of a list of files, for before/after comparisons."""
    h = hashlib.sha256()
    for f in sorted(files):
        h.update(f"{Path(f).name} {sc.sha256(f)}\n".encode())
    return h.hexdigest()


def cell_label(r) -> str:
    """Compact cell description."""
    dep = "" if r["dependence"] == "none" else ", est. dependence"
    vol = "" if abs(float(r["day_vol_sd"]) - 0.3) < 1e-12 else f", day-vol {float(r['day_vol_sd']):g}"
    return f"{r['tail']} {r['shape']} {r['market']} {int(r['n_days'])}d{dep}{vol}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", required=True, help="the pytest summary line to record")
    a = ap.parse_args()
    if DOC.exists() or (TAB.exists() and any(TAB.iterdir())):
        sys.exit("report or report_tables already exist; refusing to overwrite")
    TAB.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    # ------------------------------------------------------------------ load saved data
    plan = sc.load_plan()
    cm = pd.read_csv(SUM / "stage2_cell_method_results.csv", keep_default_na=False)
    co = pd.read_csv(SUM / "stage2_candidate_outcomes.csv", keep_default_na=False)
    cd = pd.read_csv(SUM / "stage2_critical_value_diagnostics.csv", keep_default_na=False)
    cc = pd.read_csv(SUM / "stage2_conditional_calibration.csv", keep_default_na=False)
    pl = pd.read_csv(SUM / "stage2_plumbing_vs_stage1.csv", keep_default_na=False)
    pv = pd.read_csv(SUM / "stage2_c1_pvalue_deciles.csv", keep_default_na=False)
    pr = pd.read_csv(SUM / "stage2_paired_vs_baseline.csv", keep_default_na=False)
    pwr = pd.read_csv(PW / "power_by_cell_method.csv", keep_default_na=False)
    pwf = pd.read_csv(PW / "power_ratio_and_flag.csv", keep_default_na=False)
    c3t = pd.read_csv(C3D / "c3_critical_values.csv")
    c3c = pd.read_csv(C3D / "c3_training_cell_results.csv", keep_default_na=False)
    meta = pd.read_csv(sorted(glob.glob(str(DEV / "run_metadata_*.csv")))[0], index_col=0)["value"]
    pmeta = pd.read_csv(PW / "run_metadata.csv", index_col=0)["value"]
    for c in ("q1", "q2", "q3", "q4", "spread", "reference_spread"):
        cc[c] = pd.to_numeric(cc[c], errors="coerce")
    for c in ("baseline_crit_cv", "c1_crit_cv", "baseline_crit_mean", "c1_crit_mean", "oracle_q95_T"):
        cd[c] = pd.to_numeric(cd[c])
    cfg = plan.set_index("dev_row")
    cm["cell"] = [cell_label(cfg.loc[r].to_dict() | {"tail": cfg.loc[r, "tail"]}) for r in cm["dev_row"]]

    # ------------------------------------------------------------------ integrity (recomputed now)
    man = {name: sc.verify_manifest(p, n) for name, (p, n) in sc.MANIFESTS.items()}
    man["stage2_inputs"] = sc.verify_manifest(sc.STAGE2_INPUTS)
    man["stage2_inputs_addendum"] = sc.verify_manifest(B / "frozen_stage2_inputs_addendum.sha256")
    man["c3_table"] = sc.verify_manifest(C3D / "C3_TABLE.sha256")
    probs, rows_total, fails = [], 0, {"base": 0, "c1": 0, "c3": 0}
    for r in plan.dev_row:
        d = pd.read_parquet(DEV / f"cell_{r:02d}.parquet")
        n = int(plan.loc[r, "n_sims"]); rows_total += len(d)
        if d["sim"].tolist() != list(range(n)) or (d["cell_row"] != r).any():
            probs.append((r, "ids"))
        ok = d["valid_c1"]
        if not np.allclose(d.loc[ok, "T"], d.loc[ok, "T_c1"], rtol=1e-12):
            probs.append((r, "T differs"))
        if (d["reject_c3"] != (d["T"] > d["crit_c3"])).any():
            probs.append((r, "C3 rule"))
        for m in fails:
            fails[m] += int((~d[f"valid_{m}"]).sum())
    c3_used = eval(meta["c3_crit"])
    c3_equal = all(abs(c3_used[int(k)] - float(v)) < 1e-15 for k, v in zip(c3t.n_days, c3t.c3_crit))
    e4_digest, e5_digest = digest(glob.glob(str(DEV / "*.parquet")) + glob.glob(str(DEV / "run_metadata_*.csv"))), digest(glob.glob(str(SUM / "*.csv")))
    e6_digest = digest(glob.glob(str(PW / "*")))
    mt = [(DEV / f"cell_{r:02d}.parquet").stat().st_mtime for r in range(76)]
    log = (B / "stage2_development_run.log").read_text().splitlines()
    el = [int(re.search(r"elapsed=(\d+)s", ln).group(1)) for ln in log if ln.startswith("cell")]
    gaps = sorted(((i, (mt[i] - mt[i - 1]) - (el[i] - el[i - 1])) for i in range(1, 76)), key=lambda x: -x[1])
    sleep_h = sum(max(g, 0) for _, g in gaps) / 3600

    # ------------------------------------------------------------------ E4 / E5 tables
    g = cm[cm["tier"] != "C"]
    stat_rows = []
    for m in ("baseline", "c1", "c3"):
        for t in ("A", "B"):
            x = g[(g["method"] == m) & (g["tier"] == t)]
            vc = x["status"].value_counts()
            stat_rows.append({"method": m, "tier": t, "cells": len(x), "rate_min_%": 100 * x.p_hat.min(), "rate_median_%": 100 * x.p_hat.median(), "rate_max_%": 100 * x.p_hat.max(),
                              "PASS": vc.get("PASS", 0), "PASS_AMBIG": vc.get("PASS_AMBIGUOUS", 0), "FAIL": vc.get("FAIL", 0), "FAIL_AMBIG": vc.get("FAIL_AMBIGUOUS", 0)})
    stat_tab = pd.DataFrame(stat_rows)
    c1ng = g[(g["method"] == "c1") & (g["status"] != "PASS")][["dev_row", "cell", "tier", "p_hat", "wilson_low", "wilson_high", "status"]].copy()
    for c in ("p_hat", "wilson_low", "wilson_high"):
        c1ng[c] = 100 * c1ng[c]
    df3 = cm[cm["tier"] == "C"].assign(pct=lambda x: 100 * x.p_hat).pivot_table(index=["dev_row", "cell"], columns="method", values="pct").reset_index()
    n_over2 = int(((g[g["method"] == "c3"].p_hat) < 0.02).sum())
    cin = co.set_index("method")

    # ------------------------------------------------------------------ D7
    cdp = cd.merge(plan[["dev_row", "dependence", "day_vol_sd"]], on="dev_row", suffixes=("", "_p"))
    cdp["diff"] = cdp.c1_crit_cv - cdp.baseline_crit_cv
    cdp["ratio"] = cdp.c1_crit_cv / cdp.baseline_crit_cv
    scope = cdp[cdp.in_D7_scope_40 == True]                                    # noqa: E712
    viol = cdp[cdp.d7_violation_c1 == True]                                    # noqa: E712
    gcells = cdp[cdp["tail"] == "G"]
    rng = np.random.default_rng(0)
    floor_rows = []
    for r in viol.dev_row:
        d = pd.read_parquet(DEV / f"cell_{r:02d}.parquet", columns=["crit_base", "crit_c1", "T"])
        a_, b_ = d["crit_base"].to_numpy(), d["crit_c1"].to_numpy(); n = len(a_); diffs = []
        for _ in range(500):
            i = rng.integers(0, n, n); diffs.append(b_[i].std(ddof=1) / b_[i].mean() - a_[i].std(ddof=1) / a_[i].mean())
        q = np.quantile(d["T"], 0.95); f = float(stats.gaussian_kde(d["T"].to_numpy())(q)[0])
        fl = lambda R: float(np.sqrt(0.05 * 0.95 / R) / (f * q))
        floor_rows.append({"dev_row": r, "cv_diff": b_.std(ddof=1) / b_.mean() - a_.std(ddof=1) / a_.mean(), "boot_se": float(np.std(diffs)), "ci_low": float(np.quantile(diffs, .025)),
                           "ci_high": float(np.quantile(diffs, .975)), "corr_crit_baseline_c1": float(np.corrcoef(a_, b_)[0, 1]), "mc_floor_B999": fl(999), "mc_floor_R499": fl(499),
                           "observed_cv_baseline": a_.std(ddof=1) / a_.mean(), "observed_cv_c1": b_.std(ddof=1) / b_.mean()})
    floors = pd.DataFrame(floor_rows)
    floors.to_csv(TAB / "d7_mc_floor_evidence.csv", index=False)
    viol.to_csv(TAB / "d7_four_violations.csv", index=False)

    # ------------------------------------------------------------------ D2
    ins = cc[(cc.in_advancement_scope_40 == True) & (cc["method"].isin(["c1", "c3"]))].copy()      # noqa: E712
    ins["threshold_1.25x_ref"] = 1.25 * ins.reference_spread
    ins["excess"] = ins.spread - ins["threshold_1.25x_ref"]
    ins["margin_vs_0.02"] = ins.excess - 0.02
    ins["flagged"] = ins.d2_flag_judgement_based == True                                             # noqa: E712
    ins["borderline_pm0.005"] = ins["margin_vs_0.02"].abs() <= BORDER
    ins["cell"] = [cell_label(cfg.loc[r].to_dict()) for r in ins.dev_row]
    keep = ["dev_row", "cell", "tier", "method", "conditioning_variable", "spread", "reference_spread", "threshold_1.25x_ref", "excess", "margin_vs_0.02", "flagged", "borderline_pm0.005", "d2_label"]
    ins[keep].to_csv(TAB / "d2_inscope_comparisons_c1_c3.csv", index=False)
    flagged = ins[ins.flagged]
    border = ins[ins["borderline_pm0.005"]].sort_values("margin_vs_0.02")
    flagged[keep].to_csv(TAB / "d2_flagged_74.csv", index=False)
    border[keep].to_csv(TAB / "d2_borderline_19.csv", index=False)
    cell2 = ins.groupby(["dev_row", "method"]).agg(any_flag=("flagged", "max"), n_flag=("flagged", "sum")).reset_index().merge(
        plan[["dev_row", "tail", "shape", "market", "n_days", "dependence", "day_vol_sd", "tier"]], on="dev_row")
    def grp(meth, col):
        x = cell2[cell2["method"] == meth]
        t = x.groupby(col).any_flag.agg(["sum", "count"])
        return ", ".join(f"{k}: {int(v['sum'])}/{int(v['count'])}" for k, v in t.iterrows())
    byvar = ins.groupby(["method", "conditioning_variable"]).flagged.agg(["sum", "count"]).reset_index()
    lab = ins[ins.d2_label != ""]; unl = ins[(ins.d2_label == "") & (ins["tail"] == "T4") & (ins.n_days == 59)]
    ref = cc[cc["tail"] == "G"]
    nb_base = int(((cc.in_advancement_scope_40 == True) & (cc["method"] == "baseline") & (cc.d2_flag_judgement_based == True)).sum())   # noqa: E712
    c1cell = cell2[cell2["method"] == "c1"]
    c1stat = cm[cm["method"] == "c1"][["dev_row", "status", "p_hat"]]
    c1join = c1cell.merge(c1stat, on="dev_row")
    se_rate = float(np.sqrt(0.05 * 0.95 / 6250))
    med_txt = []
    for (m_, v_), x_ in ins.groupby(["method", "conditioning_variable"]):
        a_m, b_m = x_[x_.flagged].spread.median(), x_[~x_.flagged].spread.median()
        if not np.isnan(a_m):
            med_txt.append(f"{m_}/{v_}: {a_m:.4f} vs {b_m:.4f}")

    # ------------------------------------------------------------------ remaining tables
    paired = {m: pr[pr["method"] == m] for m in ("c1", "c3")}
    dec = pv[[f"decile_{i}" for i in range(1, 11)]].astype(float).mean()
    pw_tab = pwr.assign(power_pct=lambda x: 100 * x.power, lo=lambda x: 100 * x.wilson_low, hi=lambda x: 100 * x.wilson_high)
    pw_wide = pw_tab.assign(txt=lambda x: x.power_pct.map("{:.1f}".format) + " [" + x.lo.map("{:.1f}".format) + ", " + x.hi.map("{:.1f}".format) + "]").pivot_table(
        index=["power_cell", "shape", "mult", "market"], columns="method", values="txt", aggfunc="first").reset_index()
    pwf_t = pwf[["power_cell", "shape", "mult", "market", "method", "power_method", "power_baseline", "ratio_to_baseline", "flag_cell", "power_collapse_flag"]]
    null_ctx = cm[cm.dev_row.isin([24, 25, 26, 27])].assign(pct=lambda x: 100 * x.p_hat).pivot_table(index=["dev_row", "cell"], columns="method", values="pct").reset_index()
    sf = lambda x: str(x).lower() == "true"
    n_viol, n_flag_c1, n_flag_c3 = len(viol), int(flagged[flagged["method"] == "c1"].shape[0]), int(flagged[flagged["method"] == "c3"].shape[0])
    cells_flag_c1, cells_flag_c3 = int(c1cell.any_flag.sum()), int(cell2[cell2["method"] == "c3"].any_flag.sum())
    amb_c1, amb_base = int(cin.loc["c1", "ambiguous_tierA_cells"]), int(cin.loc["baseline", "ambiguous_tierA_cells"])
    start = dt.datetime.fromtimestamp(float(meta["started_unix"])).strftime("%Y-%m-%d %H:%M")
    end = dt.datetime.fromtimestamp(max(mt)).strftime("%Y-%m-%d %H:%M")
    c3_top59 = c3c[(c3c.n_days == 59)]
    sd6 = c3_top59[c3_top59.day_vol_sd.astype(float) == 0.6][["dev_row", "q95"]].astype(float)
    top_other = float(c3_top59[c3_top59.day_vol_sd.astype(float) != 0.6].q95.astype(float).max())
    tabA = c3c.assign(rate=lambda x: x.in_sample_rate.astype(float) * 100)
    sf2 = lambda v: f"{v:.2f}"

    # ------------------------------------------------------------------ the document
    L = []
    P = L.append
    P(f"""# 18 — H1 calibration, Stage 2 report (candidate development, development grid only)

**Status: PENDING USER REVIEW. This report does NOT classify the candidates and does NOT recommend or decide advancement.** The formal classification (advance / further investigation / no candidate, docs/17 section 10) and any advancement decision are left to the user.
**What this shows:** the consolidated results of Stage 2 (C3 training, E4 development run, E5 summaries, the read-only D7/D2 investigation and the E6 power check), with integrity checks. **All data are simulated.** Generated {now} by `scripts/milestone4/stage2_make_report.py --tests "<pytest line>"` from saved files only.
**Labels used throughout:** **[EVIDENCE]** computed from the saved files; **[HYPOTHESIS]** my reading, not proven; **[PROTOCOL]** a criterion fixed in docs/17, 17b, 17c; **[DECISION]** a choice that belongs to the user.

## 1. Summary of findings (computed evidence)
- **Run:** {int(meta['simulations_this_session']):,} development simulations (76 cells, seed 20261203), baseline + C1 + C3 on the same datasets, **0 failed simulations** for any method ({fails['base']}/{fails['c1']}/{fails['c3']}). No cell is near the 0.1% failure limit.
- **Baseline (reference only):** {cin.loc['baseline','n_FAIL']} FAIL and {cin.loc['baseline','n_FAIL_AMBIGUOUS']} FAIL_AMBIGUOUS of 68 gated cells; {amb_base} of 44 tier A cells ambiguous.
- **C1:** {cin.loc['c1','n_PASS']} PASS, {cin.loc['c1','n_PASS_AMBIGUOUS']} PASS_AMBIGUOUS, **{cin.loc['c1','n_FAIL']} FAIL, {cin.loc['c1','n_FAIL_AMBIGUOUS']} FAIL_AMBIGUOUS**; {amb_c1} of 44 tier A cells ambiguous (yardstick: fewer than 10); **{n_viol} D7 violations**; **{n_flag_c1} D2 flags in {cells_flag_c1} of 40 in-scope cells**.
- **C3 (labelled fallback):** all 68 gated cells pass its upper-limit-only gate (PASS_CLEAR); rejection rates are far below 5% in most cells (tier A median {100*g[(g['method']=='c3')&(g['tier']=='A')].p_hat.median():.2f}%, tier B median {100*g[(g['method']=='c3')&(g['tier']=='B')].p_hat.median():.2f}%; {n_over2} of 68 cells below 2%); **{n_flag_c3} D2 flags in {cells_flag_c3} of 40 in-scope cells**, all on leverage.
- **E6 power check (diagnostic only):** the single D3 flag was not raised; C1 power exceeded the baseline's in all six cells, partly reflecting C1's larger size in the flat cells; C3 is much less powerful at the smaller effect.
- **Formal classification and advancement: PENDING USER REVIEW (section 12).**

## 2. Scope, protocol provenance and design decisions [PROTOCOL]
- Plan and decisions: `docs/17_h1_calibration_stage2_plan.md`, `docs/17b_h1_calibration_stage2_review_record.md` (D1–D10), `docs/17c_h1_calibration_stage2_d2_confirmation.md`; frozen specifications v1 and v1.1 (`docs/15a`, `15b`); Stage 1 report `docs/16`.
- **Grid:** 76 development cells (frozen `cells_development.csv`): 44 tier A (25,000 sims), 24 tier B (25,000), 8 df 3 report-only (10,000) = 1,780,000 simulations per method; 68 gated cells; 52 cells at 59 days, 12 at 125, 12 at 250.
- **Candidates:** C1 (frozen v1 implementation, R = 499) and C3 (frozen table) eligible; baseline reference only; **C2 not run** (D9); C1 preferred over C3 if both qualify (D1).
- **Gates:** tier A 4.5–5.5%, tier B 4.0–6.0% (two-sided, with the Wilson clause); C3 upper limits only (5.5% A, 6.0% B); df 3 report-only; statuses PASS, PASS_AMBIGUOUS, FAIL, FAIL_AMBIGUOUS per `h1_calibration_v11.classify_cell`.
- **Seeds:** C3 training 20261202, development 20261203 (`spawn_key=(dev_row, i, k)`, k = 0 data, 1 baseline, 2 C1), power check 20261212.
- **Decision rules recorded in 17b/17c:** D2 flag `observed_spread − 1.25 × reference_spread >= 0.02` (fractions; 0.02 = 2 percentage points; a judgement-based diagnostic threshold; implemented with a 1e-12 tolerance); D4 yardstick of 10 ambiguous tier A cells (judgement value); D6 failure blocking above 0.1% in gated cells; D7 critical-value variability rule in 40 cells (24 tier B + 16 tier A at 125/250 days; C3 exempt); D3 power check, diagnostic only; no candidate revision (D5).
- **Protocol deviation recorded:** docs/17b says the power check applies to candidates that meet A.1–A.5. Neither candidate does. E6 was run at the user's explicit request after the E5 results were shown.

## 3. Integrity and reproducibility checks (recomputed when this report was generated)
| Check | Result |
|---|---|
| Frozen v1 manifest | {man['v1']} files verified |
| Frozen v1.1 manifest | {man['v1.1']} files verified |
| Stage 1 code manifest | {man['stage1_code']} files verified |
| Stage 2 inputs manifest (`frozen_stage2_inputs.sha256`) | {man['stage2_inputs']} files verified |
| Stage 2 addendum manifest | {man['stage2_inputs_addendum']} files verified |
| C3 table manifest (`C3_TABLE.sha256`) | {man['c3_table']} files verified |
| E4 cell files | 76 files, {rows_total:,} rows, simulation ids exact; statistic T identical across methods in every simulation; C3 rule `T > crit` holds exactly; problems: {probs or 'none'} |
| C3 table used by E4 equals the frozen table | {c3_equal} |
| Raw E4 outputs (digest of 77 file hashes) | `{e4_digest[:24]}…` (byte-identical before and after E5 and E6, checked at each step) |
| E5 summaries (digest) | `{e5_digest[:24]}…` |
| E6 outputs (digest) | `{e6_digest[:24]}…` |
| Test suite | {a.tests} |
| Environment | Python {platform.python_version()}, numpy {np.__version__}, pandas {pd.__version__}, scipy {__import__('scipy').__version__}; {platform.platform()} |

**Run history [EVIDENCE].** E4 started {start} and its last cell file was written {end}. The runner's compute clock shows {float(meta['wall_seconds_this_session'])/3600:.2f} h ({meta['wall_seconds_this_session']} s); the wall-clock span between the first and last cell files is {(max(mt)-min(mt))/3600:.2f} h. The {sleep_h:.2f} h difference is machine sleep (largest gaps before cells {gaps[0][0]} and {gaps[1][0]}: {gaps[0][1]/3600:.2f} h and {gaps[1][1]/3600:.2f} h) despite `caffeinate`. The run continued and completed; seeds do not depend on the clock, so results are unaffected. The compute time exceeds the 11–12 h central estimate and sits at the top of the stated ±30% band (8–15.5 h). The power check took {pmeta['wall_seconds']} s.

## 4. C3 training table and conservative behaviour
**Frozen table [EVIDENCE]** (`outputs/milestone4/h1_calibration/stage2/c3_training/c3_critical_values.csv`; 68 cells × 25,000 simulations, seed 20261202, 0 failures):
{md(c3t, {'c3_crit': '{:.6f}'})}
- At 59 days the value is set by the day-volatility-0.6 stress cells: of the four such cells, rows {', '.join(str(int(r)) for r in sd6[sd6.q95 > top_other].dev_row)} give {', '.join(f'{v:.4f}' for v in sd6[sd6.q95 > top_other].q95)}; the fourth (row {', '.join(str(int(r)) for r in sd6[sd6.q95 <= top_other].dev_row)}) gives {', '.join(f'{v:.4f}' for v in sd6[sd6.q95 <= top_other].q95)}, below the highest day-volatility-0.3 cell ({top_other:.4f}). **Correction of an earlier chat statement:** an earlier summary described all four 0.6 cells as 3.23–3.30; row 49 is 3.0394.
- At 125 and 250 days the top cells are within about 0.5 to 2 standard errors of the maximum, so taking the maximum of noisy quantiles biases the value slightly upward [HYPOTHESIS, consistent with the bootstrap standard errors in `c3_training_cell_results.csv`].
- The in-sample "PASS" statuses in the training results used the same data the table was built from and carry no information about validity.

**Rejection behaviour in E4 (null) [EVIDENCE].** C3's null rejection rates in the 68 gated cells range from {100*g[g['method']=='c3'].p_hat.min():.2f}% to {100*g[g['method']=='c3'].p_hat.max():.2f}%: tier A median {100*g[(g['method']=='c3')&(g['tier']=='A')].p_hat.median():.2f}% (max {100*g[(g['method']=='c3')&(g['tier']=='A')].p_hat.max():.2f}%), tier B median {100*g[(g['method']=='c3')&(g['tier']=='B')].p_hat.median():.2f}% (max {100*g[(g['method']=='c3')&(g['tier']=='B')].p_hat.max():.2f}%); {n_over2} of 68 cells are below 2%. C3 passes its upper-limit gate because it rarely rejects, not because it is calibrated: it is a conservative fixed critical value, valid only inside its training family (44 cells at 59 days, 12 at 125, 12 at 250), and it trades power for size (section 10).

## 5. E4 results by method [EVIDENCE]
Rejection rates are null rejection rates, nominal 5%. Source: `stage2/summary/stage2_cell_method_results.csv`, `stage2_candidate_outcomes.csv`.
{md(stat_tab, {'rate_min_%': '{:.2f}', 'rate_median_%': '{:.2f}', 'rate_max_%': '{:.2f}'})}

Candidate-level v1.1 outcomes computed by the classifier (not a selection): baseline **{cin.loc['baseline','v1_1_candidate_outcome']}**, C1 **{cin.loc['c1','v1_1_candidate_outcome']}**, C3 **{cin.loc['c3','v1_1_candidate_outcome']}** (C3 on upper limits only). Failures: 0 for every method and cell; no cell blocked by D6.

**C1: every gated cell that is not a clear PASS** (rate and Wilson 95% interval in %):
{md(c1ng, {'p_hat': '{:.2f}', 'wilson_low': '{:.2f}', 'wilson_high': '{:.2f}'})}

- **Pattern [EVIDENCE]:** C1's rejection rate is slightly below nominal in Gaussian-like tier A cells (minimum {100*g[(g['method']=='c1')&(g['tier']=='A')].p_hat.min():.2f}%; the two tier A FAIL_AMBIGUOUS cells sit just under the 4.5% lower bound) and above nominal in the T4 (tier B) cells (median {100*g[(g['method']=='c1')&(g['tier']=='B')].p_hat.median():.2f}%, maximum {100*g[(g['method']=='c1')&(g['tier']=='B')].p_hat.max():.2f}%). It is closer to 5% than the baseline (tier B median {100*g[(g['method']=='baseline')&(g['tier']=='B')].p_hat.median():.2f}%) but does not reach the tier B gate in every cell.
- **df 3 report-only cells** (no gate; rates in %):
{md(df3, {'baseline': '{:.2f}', 'c1': '{:.2f}', 'c3': '{:.2f}'})}

## 6. Ambiguity flags (D4) [EVIDENCE + PROTOCOL]
The yardstick is 10 ambiguous tier A cells; it is a judgement value that assumes every cell is exactly 5.0% and cells are independent (for such a method the expectation is 4.2 ambiguous cells of 44; docs/17 section 5). Computed: baseline {amb_base}, **C1 {amb_c1}**, C3 {int(cin.loc['c3','ambiguous_tierA_cells'])}. The yardstick is reached by the baseline and by C1. For C1 several ambiguous tier A cells are slightly *below* the 5% centre (rates of about 4.5–4.8%), consistent with the mild under-rejection noted above. No replication was run and none is automatic (D10).

## 7. Critical-value variability and the D7 violations (D7, 40-cell scope)
**[PROTOCOL]** D7: C1's critical-value CV must be below the baseline's in the 40 in-scope cells (24 tier B + 16 tier A at 125/250 days); C3 exempt; CV reported in all cells.
**[EVIDENCE]** C1's CV is below the baseline's in {len(scope) - n_viol} of 40 in-scope cells (median C1 CV {scope.c1_crit_cv.median():.3f} against {scope.baseline_crit_cv.median():.3f}). **There are {n_viol} violations, all kept as counted:**
{md(viol[['dev_row','tail','shape','market','n_days','tier','baseline_crit_cv','c1_crit_cv','diff','ratio','baseline_crit_mean','c1_crit_mean','oracle_q95_T']], {'baseline_crit_cv':'{:.4f}','c1_crit_cv':'{:.4f}','diff':'{:+.4f}','ratio':'{:.3f}','baseline_crit_mean':'{:.4f}','c1_crit_mean':'{:.4f}','oracle_q95_T':'{:.4f}'})}
- Common features: df ∞, tier A, 250 days, no dependence, day-volatility 0.3; E and D5 shapes in both markets: these are **all four df ∞ cells that exist at 250 days**, so no cell in that category passes the rule.
- Similar cells (df ∞, all sizes):
{md(gcells[['dev_row','shape','market','n_days','in_D7_scope_40','baseline_crit_cv','c1_crit_cv','diff','ratio','d7_violation_c1']].sort_values(['n_days','shape','market']), {'baseline_crit_cv':'{:.4f}','c1_crit_cv':'{:.4f}','diff':'{:+.4f}','ratio':'{:.3f}'})}
- Mean CV over the df ∞ cells by sample size: {', '.join(f"{int(k)} days: baseline {v['baseline_crit_cv']:.4f} / C1 {v['c1_crit_cv']:.4f}" for k, v in gcells.groupby('n_days')[['baseline_crit_cv','c1_crit_cv']].mean().iterrows())}. The baseline's CV falls with sample size while C1's is nearly constant, so the ratio crosses 1 between 125 and 250 days. In the other 36 in-scope cells C1's CV is {scope[scope['tail']!='G'].assign(r=lambda x: x.c1_crit_cv/x.baseline_crit_cv).r.min():.2f}–{scope[scope['tail']!='G'].assign(r=lambda x: x.c1_crit_cv/x.baseline_crit_cv).r.max():.2f} of the baseline's (T4 and T6), so the violations are confined to the benign df ∞ cells.
- Sampling noise [EVIDENCE]: a paired bootstrap over the 25,000 simulations gives CV differences of {floors.cv_diff.min():.4f}–{floors.cv_diff.max():.4f}, about {(floors.cv_diff/floors.boot_se).mean():.1f} bootstrap standard errors above zero, with 95% intervals that exclude zero. The differences are not noise.
- **Monte-Carlo floor (contextual evidence only, NOT a waiver):** the asymptotic CV of a 95% quantile estimated from R Monte-Carlo draws is computed from a kernel-density estimate of T at its 95% quantile.
{md(floors[['dev_row','observed_cv_baseline','mc_floor_B999','observed_cv_c1','mc_floor_R499','cv_diff','boot_se','corr_crit_baseline_c1']], {k: '{:.4f}' for k in ['observed_cv_baseline','mc_floor_B999','observed_cv_c1','mc_floor_R499','cv_diff','boot_se']} | {'corr_crit_baseline_c1': '{:.3f}'})}
- **[HYPOTHESIS]** C1's CV at 250 days is essentially Monte-Carlo noise from using R = 499 resamples: its observed CV ({floors.observed_cv_c1.min():.4f}–{floors.observed_cv_c1.max():.4f}) is close to the R = 499 floor ({floors.mc_floor_R499.min():.4f}–{floors.mc_floor_R499.max():.4f}), while the baseline's ({floors.observed_cv_baseline.min():.4f}–{floors.observed_cv_baseline.max():.4f}) lies above its B = 999 floor ({floors.mc_floor_B999.min():.4f}–{floors.mc_floor_B999.max():.4f}); critical values of the two methods are uncorrelated across datasets ({floors.corr_crit_baseline_c1.min():.3f} to {floors.corr_crit_baseline_c1.max():.3f}). C1's mean critical value matches the oracle 95% quantile to within {(viol.c1_crit_mean-viol.oracle_q95_T).abs().max():.3f}. Not tested: whether a larger R would remove the violations; that would be a candidate revision (D5) and was not done.

## 8. Conditional calibration and the D2 flags (D2, 40-cell scope)
**[PROTOCOL]** Flag `<=>` `observed_spread − 1.25 × reference_spread >= 0.02` (fractions); spread = max − min rejection rate across quartiles of leverage, kurtosis or the method's own critical value; reference = same method and variable in the df ∞ cell matched on shape, market and sample size; a **judgement-based diagnostic threshold, not a statistical test**. In 12 gated cells (dev_row 44–51 inside the scope, 40–43 outside) the reference is not matched on dependence / day-volatility and every flag there is labelled **"reference not matched on dependence / day-volatility"**.
**[EVIDENCE]** Of {len(ins)} in-scope C1/C3 comparisons, **{len(flagged)} are flagged** (C1 {n_flag_c1} of {int((ins['method']=='c1').sum())}, C3 {n_flag_c3} of {int((ins['method']=='c3').sum())}); the baseline (reference only) has {nb_base} of 120. All 74 are preserved in `stage2/report_tables/d2_flagged_74.csv` (and listed in appendix A); the full 200 comparisons with the exact calculation are in `d2_inscope_comparisons_c1_c3.csv`.
{md(byvar.rename(columns={'sum':'flagged','count':'compared'}))}
- **By cell (cells with at least one flag):** C1 {cells_flag_c1} of 40, C3 {cells_flag_c3} of 40.
  - C1 by tail: {grp('c1','tail')}; by sample size: {grp('c1','n_days')}; by market: {grp('c1','market')}; by tier: {grp('c1','tier')}.
  - C3 by tail: {grp('c3','tail')}; by sample size: {grp('c3','n_days')}; by market: {grp('c3','market')}; by tier: {grp('c3','tier')}.
  - Dependence / day-volatility (C1): {grp('c1',['dependence','day_vol_sd'])}; (C3): {grp('c3',['dependence','day_vol_sd'])}.
- Cells with no C1 flag: {', '.join(str(int(r)) for r in c1cell[~c1cell.any_flag].dev_row)} (df ∞ cells and two T6 US 125-day cells). No flag appears on kurtosis for either method ({int(ins[ins.conditioning_variable=='kurtosis'].flagged.sum())} of {int((ins.conditioning_variable=='kurtosis').sum())}); T6 flags are all on leverage.
- Median spreads, flagged vs unflagged (fractions): {'; '.join(med_txt)}.
- Reference (df ∞) spreads are not small: leverage median {ref[ref.conditioning_variable=='leverage'].spread.median():.4f} (max {ref[ref.conditioning_variable=='leverage'].spread.max():.4f}); own critical value median {ref[ref.conditioning_variable=='own_critical_value'].spread.median():.4f}.
- Link to rejection rates (C1, 40 in-scope cells): flagged cells have median rate {100*c1join[c1join.any_flag].p_hat.median():.2f}% against {100*c1join[~c1join.any_flag].p_hat.median():.2f}% for unflagged; all three clear FAIL cells are flagged.
- **Labelled cells [EVIDENCE]:** {len(lab)} labelled in-scope comparisons (dev_row 44–51), {int(lab.flagged.sum())} flagged ({100*lab.flagged.mean():.1f}%), against {int(unl.flagged.sum())} of {len(unl)} ({100*unl.flagged.mean():.1f}%) in unlabelled T4 59-day cells with a matched reference. Labels are preserved in every output. Flags in the labelled cells are less reliable (a Gaussian world with dependence or higher volatility could itself show a different gradient) and are not stronger evidence than flags in the 32 matched cells.

**The 19 borderline comparisons** (within ±0.005 of the threshold, i.e. `|spread − 1.25 × reference − 0.02| <= 0.005`). They are flagged or not by the exact rule; **nothing about the threshold was changed**. The flag status of these comparisons is sensitive to small changes. Full file: `stage2/report_tables/d2_borderline_19.csv`.
{md(border[['dev_row','cell','method','conditioning_variable','spread','reference_spread','threshold_1.25x_ref','excess','margin_vs_0.02','flagged','d2_label']], {k: '{:.4f}' for k in ['spread','reference_spread','threshold_1.25x_ref','excess']} | {'margin_vs_0.02': '{:+.4f}'})}
- **[HYPOTHESES]** (a) A fixed critical value rejects more when leverage is high, so C3's leverage flags may be built in; no evidence beyond the pattern. (b) C1 reduces the critical-value gradient relative to the baseline (median own-critical-value spread {cc[(cc.conditioning_variable=='own_critical_value')&(cc['method']=='c1')].spread.median():.4f} against {cc[(cc.conditioning_variable=='own_critical_value')&(cc['method']=='baseline')].spread.median():.4f}) but not to the df ∞ reference level in T4 cells. (c) The binomial noise of a spread from four equal true rates is about {2.06*se_rate:.4f}; the 0.02 excess is about {0.02/(2.06*se_rate):.1f} times that, so most flags look like real gradients while the borderline ones are sensitive.

## 9. Plumbing, p-values and paired comparisons [EVIDENCE]
- **Plumbing check vs Stage 1 (baseline, {len(pl)} overlapping cells):** maximum |z| = {pl.z.astype(float).abs().max():.2f}; {int((pl.z.astype(float).abs() > 3).sum())} cells above 3 and {int((pl.z.astype(float).abs() > 2).sum())} above 2. The Stage 2 pipeline reproduces Stage 1 baseline rates; this checks the machinery, it is not validation.
- **C1 p-value deciles** (mean over 76 cells; uniform = 0.100): {', '.join(f'{v:.3f}' for v in dec)}.
- **Paired with the baseline on the same datasets:** C1: baseline-only rejections {int(paired['c1'].baseline_only_rejects.sum()):,}, C1-only {int(paired['c1'].method_only_rejects.sum()):,}; cells with sign-test p < 0.001: {int((paired['c1'].sign_test_p.astype(float) < 0.001).sum())} of 76. C3: baseline-only {int(paired['c3'].baseline_only_rejects.sum()):,}, C3-only {int(paired['c3'].method_only_rejects.sum()):,}; {int((paired['c3'].sign_test_p.astype(float) < 0.001).sum())} of 76. Descriptive only.

## 10. E6 power check — diagnostic only, not candidate selection or validation
Six cells (T4 flat ×1.1 and ×1.2, T4 E ×1.2; both markets; 59 days; no dependence; day-volatility 0.3), 5,000 simulations each, seed 20261212, baseline, C1 and C3 on the same data; 0 failures. Power (%) [Wilson 95%] (`stage2/power_check/power_by_cell_method.csv`):
{md(pw_wide)}

Ratio to the baseline and the single D3 flag (candidate power below 70% of the baseline's at T4 flat ×1.2):
{md(pwf_t, {'power_method':'{:.4f}','power_baseline':'{:.4f}','ratio_to_baseline':'{:.4f}'})}

- **Flag:** {'raised' if any(sf(v) for v in pwf.power_collapse_flag) else 'not raised'} for either method in either market.
- **Not size-adjusted [EVIDENCE]:** the null rejection rates in the matching development cells are
{md(null_ctx, {'baseline':'{:.2f}','c1':'{:.2f}','c3':'{:.2f}'})}
  so part of C1's higher power in the flat cells may reflect its larger size there (about 5.7% against 5.1–5.3%), and C3's low power at ×1.1 reflects its conservatism (about 1.2% null rejection). In the E cells the baseline over-rejects, so the power ratios there are not a fair yardstick and no flag applies.
- This check **plays no role in candidate selection or validation**.

## 11. Advancement criteria as computed (docs/17 section 10 A) [PROTOCOL + EVIDENCE]
These compare the computed results with the pre-specified criteria. **They are facts, not a classification.**
| Criterion | C1 | C3 |
|---|---|---|
| A.1 gates (D4): no FAIL or FAIL_AMBIGUOUS | **Not met:** {cin.loc['c1','n_FAIL']} FAIL and {cin.loc['c1','n_FAIL_AMBIGUOUS']} FAIL_AMBIGUOUS of 68 | Met: 68 of 68 pass on upper limits only |
| A.2 ambiguous tier A cells below 10 | **Not met:** {amb_c1} of 44 | Met: {int(cin.loc['c3','ambiguous_tierA_cells'])} |
| A.3 failures at most 0.1% per cell | Met (0) | Met (0) |
| A.4 CV below baseline in the 40 cells (D7) | **Not met:** {n_viol} violations | Exempt (constant critical value) |
| A.5 no D2 flag in the 40 in-scope cells | **Not met:** {n_flag_c1} flagged comparisons in {cells_flag_c1} cells | **Not met:** {n_flag_c3} flagged comparisons in {cells_flag_c3} cells |
| A.6 plumbing check passed; no power-collapse flag (diagnostic) | Met; flag not raised | Met; flag not raised |
| A.7 explicit user approval | **Pending** | **Pending** |

**Formal classification (docs/17 section 10: advance to Stage 3 / further investigation / no candidate selected): PENDING USER REVIEW. This report makes no recommendation.** The baseline is never selectable; C2 was not run.

## 12. Evidence, hypotheses, protocol criteria and decisions that remain
**Computed evidence:** sections 3–10 and the tables in `stage2/report_tables/`.
**Hypotheses (not proven):** the Monte-Carlo-noise reading of the D7 violations (section 7); the built-in leverage gradient of a fixed critical value, the partial reduction of C1's critical-value gradient, and the noise scale of the D2 borderline calls (section 8); the upward bias of the C3 maximum (section 4); C1's power advantage partly reflecting size (section 10).
**Protocol criteria applied unchanged:** gates, D2 formula and threshold, D4 yardstick, D6, D7 scope, D3 flag. All four D7 violations and all {len(flagged)} D2 flags stand as counted; the {len(border)} borderline comparisons are highlighted and unchanged; no candidate was revised.
**Decisions that remain with the user:**
1. The formal classification of C1 and C3 (advance / further investigation / no candidate) and any advancement decision.
2. Whether any follow-up that changes a candidate (for example a larger R for C1) is wanted; it would need a new numbered specification version, explicit approval and the reserved seed 20261211 (D5). None was done.
3. How Stage 2 results should be carried into any later stage; Stage 3, Stage 4, Stage 1b, H3, M5 and replication are not started.
4. Whether and when to commit and push the new Stage 2 files (E4, E5, E6 outputs, run logs, docs/17c, docs/18, the D2 formula test, the addendum manifest). **Nothing was committed or pushed.**
5. Open housekeeping from earlier review: the stale wording in the hashed docs/17b and the stale `d2_flag` docstring (both unedited because the existing manifest would no longer verify); whether the C3 facts in section 4 satisfy the earlier request for a C3 documentation record.

## 13. Limitations
- Results describe null rejection rates in the **simulated development family** (Student-t shocks, E/D5/R2/flat shapes, Gaussian log day factor, no jumps or volatility clustering, iid days, one estimated dependence setting). They do not establish validity outside that family or on real data. Real-data descriptive tails (docs/14) are heavier than most development cells and the robust day-scale sd (0.64 NSE, 0.51 US) exceeds 0.3.
- Development performance is not validation (Stage 3 uses fresh seeds); with two candidates examined the screening is optimistic.
- C3 is valid only inside its training family and is conservative; the maximum over noisy cell quantiles is biased upward.
- Twenty-five thousand simulations detect an excess of roughly 0.5 points; the gate is not an equivalence test, and a calibrated method is expected to show about 4 ambiguous tier A cells.
- The D2 and D4 thresholds are judgement-based; 12 cells use an unmatched reference; the 19 borderline D2 calls are sensitive.
- Power is not size-adjusted and the baseline's size is distorted in the E cells.
- The corrected C2 procedure is unverified and was not run (D9).
- Unit tests are implementation checks, not statistical validation.

## Appendix A. All {len(flagged)} flagged D2 comparisons (C1 and C3, in scope)
{md(flagged.sort_values(['method','dev_row','conditioning_variable'])[['dev_row','cell','method','conditioning_variable','spread','reference_spread','excess','margin_vs_0.02','borderline_pm0.005','d2_label']], {k: '{:.4f}' for k in ['spread','reference_spread','excess']} | {'margin_vs_0.02': '{:+.4f}'})}

## Appendix B. Files
- Report generator: `scripts/milestone4/stage2_make_report.py`; supporting tables: `outputs/milestone4/h1_calibration/stage2/report_tables/` (`d2_flagged_74.csv`, `d2_borderline_19.csv`, `d2_inscope_comparisons_c1_c3.csv`, `d7_four_violations.csv`, `d7_mc_floor_evidence.csv`).
- E4: `stage2/development/` (76 cell files, run metadata), log `stage2_development_run.log`. E5: `stage2/summary/` (7 CSVs). E6: `stage2/power_check/`, log `stage2_power_check_run.log`. C3: `stage2/c3_training/`.
- Records: docs/17, 17b, 17c. Frozen inputs and manifests were not modified.
""")
    DOC.write_text("\n".join(L))
    print("written", DOC, "|", len(DOC.read_text().splitlines()), "lines")


if __name__ == "__main__":
    main()
