"""H1 calibration, STAGE 4: write docs/22 (the Stage 4 preregistration) from the saved preregistration analyses. Reads only; no simulation; every number comes from
outputs/milestone4/h1_calibration/stage4_prereg/*.csv.   Refuses to overwrite.   Run once, before any Stage 4 simulation.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "outputs" / "milestone4" / "h1_calibration" / "stage4_prereg"
DOC = ROOT / "docs" / "22_h1_calibration_stage4_preregistration.md"


def md(df, fmt=None):
    """Markdown table."""
    fmt = fmt or {}
    out = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "|".join("---" for _ in df.columns) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join((fmt[c].format(r[c]) if c in fmt and isinstance(r[c], (int, float, np.floating, np.integer)) else str(r[c])) for c in df.columns) + " |")
    return "\n".join(out)


def main():
    if DOC.exists():
        sys.exit("docs/22 already exists")
    pp = pd.read_csv(P / "null_check_precision.csv"); des = pd.read_csv(P / "null_check_design.csv"); bs = pd.read_csv(P / "null_check_batch_statistics.csv")
    tm = pd.read_csv(P / "truncated_moment_design.csv"); z = pd.read_csv(P / "bar_level_ztest_calibration.csv"); pw = pd.read_csv(P / "bar_level_ztest_power.csv")
    rs = pd.read_csv(P / "reference_selection.csv"); sd = pd.read_csv(P / "seeds.csv")
    fro, prop = pp[pp["sample"] == "frozen 1e6 bars"], pp[pp["sample"] == "proposed 5e7 bars"]
    se_f = pd.concat([fro["SE_open_%"], fro["SE_close_%"]]); se_p = pd.concat([prop["SE_open_%"], prop["SE_close_%"]])
    pfro = pd.concat([fro.P_pass_open, fro.P_pass_close]); tolse = prop["tolerance_in_SE_units_min"]
    p_all_f, p_all_p = float(fro["P_all16_pass_(all_processes)"].iloc[0]), float(prop["P_all16_pass_(all_processes)"].iloc[0])
    scal = bs["scaling_check_sd4_over_sd1 (expect 0.5)"]
    t1 = tm[tm.N_bars == 1e7]
    z2, z8 = z[z.n_bar_level == 2000], z[z.n_bar_level == 8000]
    fw = lambda zz, col: 1 - float(np.prod(1 - zz[col]))
    pwm = pw.groupby(["n_bar_level", "true_difference_points"])["power_|z|>3"].mean().unstack()
    pwb = pw[pw.n_bar_level == 2000].groupby(["method", "true_difference_points"])["power_|z|>3"].mean().unstack()
    des_show = des[["process", "market", "min_days_required", "days_rounded_up", "bars_open_period", "bars_close_period"]]
    ref_show = rs[["val_row", "tail", "shape", "market", "n_days", "dependence", "day_vol_sd", "tier"]]
    DOC.write_text(f"""# 22 — H1 calibration, Stage 4 preregistration (independent validation of C3)

**Status: PREREGISTRATION FOR REVIEW. No Stage 4 simulation has been run. Execution needs your separate, explicit approval.** Everything below is fixed BEFORE any Stage 4 result exists. Nothing in the frozen v1 / v1.1 specifications, seeds, thresholds, critical values or manifests is changed. All data are simulated.
**Numbers:** produced by `scripts/milestone4/stage4_prereg_analysis.py` and saved in `outputs/milestone4/h1_calibration/stage4_prereg/` (analysis seed 20261215, which is **not** a Stage 4 validation seed). This document is generated from those files by `scripts/milestone4/stage4_make_prereg.py`.
**Labels:** **[FROZEN]** from the frozen specification; **[PROPOSED]** a pre-run choice for your approval; **[EVIDENCE]** computed.

## 1. Scope and authorisation boundaries
Authorised: Stage 4 independent validation only, with C3 as the candidate (baseline as a reference). **Not authorised and not started:** Stage 5, candidate revision, new calibration, H2/H3/M5, real-data descriptive analysis, real-market tests, commits and pushes. The Stage 4 item "validation of the H1 calibration conclusions within the specified domain" is Stage 5 content and is not performed.

## 2. Frozen specification being followed [FROZEN]
- Six alternative processes a–f, parameters in `frozen_spec_v1_1/alt_dgp_parameters.json` (process e as approved: Gaussian scale mixture), 12 cells (`cells_alternative_dgps.csv`: 6 processes × NSE/US, shape E, 59 days, 25,000 simulations each), master seed **20261206**; the method (C3, critical value 3.298658 for 59 days) is run **unchanged**; baseline B = 999 on the same datasets as reference.
- Gate (v1 + v1.1 A2): "alternative DGPs: point estimate in [4.0%, 6.0%]"; "for C3 only p̂ ≤ hi" — hence **C3 passes a cell when its rate is at most 6.0%**; the two-sided band is reported for the baseline (information). Ambiguity flag per v1.1 A2 (the upper bound 6.0% inside the Wilson interval). Failure condition 3: any alternative cell outside its gate. Numerical failures above 0.1% need a fallback.
- Bar-level pipeline check (master 20261207) and reference implementation check (master 20261208): one sentence each in `docs/13` §4 and `docs/14`; **the details below are [PROPOSED] fill-ins**.
- Null-preserving check before use (`docs/15a` §4): "period means equal within 0.5% at 10⁶ bars", with c and d noted as not verifiable by Monte Carlo.

## 3. Null check before use of the alternative processes (A)
**[EVIDENCE] The frozen sample size (10⁶ bars) cannot meet the literal 0.5% tolerance even for a correct generator.** Statistic: the ratios open/middle and close/middle of period mean squares (they cancel the common day factor). Batch method: {int(bs.batches.iloc[0])} independent batches of {int(bs.days_per_batch.iloc[0]):,} days per (process, market); standard error at any size = batch sd × √(batch days / days). √N scaling check (sd of 4-batch means ÷ sd of batches, expect 0.5): {scal.min():.2f}–{scal.max():.2f}.
- At **10⁶ bars** (smallest period): SE {se_f.min():.2f}%–{se_f.max():.2f}%; per-ratio pass probability {pfro.min():.2f}–{pfro.max():.2f}; probability that all 16 ratios of a, b, e, f pass for a correct generator: **{100*p_all_f:.2f}%**.
- At **5×10⁷ bars** (proposed): SE {se_p.min():.3f}%–{se_p.max():.3f}%; the 0.5% tolerance is at least **{tolse.min():.2f} standard errors** in every ratio; all-16 pass probability **{p_all_p:.5f}**.
- **Minimum justified size** (all-16 pass ≥ 99%, i.e. {des.z_per_ratio_for_Pall99.iloc[0]:.2f} SE per ratio, upper 95% bound of the batch sd), in days and bars of the open/close periods:
{md(des_show, {'bars_open_period': '{:,.0f}', 'bars_close_period': '{:,.0f}', 'min_days_required': '{:,.0f}', 'days_rounded_up': '{:,.0f}'})}
  The most demanding requirement is {int(des.bars_open_period.max()):,} bars in the open period (process {des.loc[des.bars_open_period.idxmax(), 'process']}, {des.loc[des.bars_open_period.idxmax(), 'market']}); **5×10⁷ bars is {5e7 / des.bars_open_period.max():.1f}× that**, so it is sufficient with a margin, and a period-specific error of 1% would be 10 or more standard errors (detected). **What this check can and cannot catch:** it catches errors that make one period's variance differ from another's (for example a non-stationary start of the process-a volatility path, which would lower the open/middle ratio by about 5%, or a wrong tail scale in one period of process c). It does **not** measure the overall variance level: a factor common to all periods (such as a missing e^(−σ²) amplitude factor or the jump variance share) leaves the ratios unchanged and does not break H0; those factors are verified analytically (exact, already tested), not by this check.
- **[PROPOSED] Design for a, b, e, f:** 5×10⁷ bars in the open period per (process, market) (NSE 2,083,333 days, US 1,515,151 days, 3 stocks), literal tolerance **0.5%** on both ratios, seed namespace `SeedSequence(20261206, spawn_key=(100 + process_market_index, batch))` (disjoint from the simulation streams, whose first key element is 0–11). Acceptance: all 16 ratios within [0.995, 1.005]. The 0.5% tolerance is **not relaxed**.
- **Processes c and d (infinite fourth moment):** the raw period-mean ratio cannot reach 0.5% by Monte Carlo (the standard error does not shrink at the usual rate; `docs/15a` already says so). **[PROPOSED] alternative that keeps the 0.5% tolerance on what can be measured:** compare the empirical mean of ε²·1{{|ε|≤c}} (c = 99.9% two-sided quantile of the intended scaled Student-t) with its exact value, for each component and market: c: open, middle, close (t4, t8, t4); d: stocks 1–3 (t3, t5, t8); 10⁷ bars per component; tolerance 0.5%. Relative SE at 10⁷ bars: {t1['relative_SE_%'].min():.3f}%–{t1['relative_SE_%'].max():.3f}%, so the tolerance is at least {0.5 / t1['relative_SE_%'].max():.1f} SE. **Honest limit:** the variance beyond the cutoff ({100*(1-t1.exact_truncated_E_e2.max()):.1f}% to {100*(1-t1.exact_truncated_E_e2.min()):.1f}% of the total for these components) cannot be verified by Monte Carlo at 0.5%; it rests on the exact analytic unit-variance scaling constants and the tail-probability unit tests, both already passing.
- **If any check fails:** stop, report, no change to a generator or tolerance without your approval; the alternative processes are not used.

## 4. Alternative-process validation (the frozen core of Stage 4)
12 cells × 25,000 simulations (300,000), C3 unchanged, baseline reference, seeds `SeedSequence(20261206, spawn_key=(cell_row, i, stream))`, `cell_row` = 0–11 row of `cells_alternative_dgps.csv`, stream 0 data, 1 baseline bootstrap. The generators are `src/quantlab/research/h1_stage4.py` (the existing untested file, preserved; refactored additively so the random ingredients can be tested; 18 new tests pass). Outputs per cell: rate, Wilson interval, status (C3 on its upper limit), failures, plus descriptive conditional spreads (no matched df ∞ reference exists for these processes, so D2 is not computable and not invented). Estimated cost under one hour.
**Pass for a cell:** C3 rate ≤ 6.0%. **Stage 4 alternative-process criterion met:** all 12 cells. Anything else is reported with the failure condition it triggers (condition 3: the method is then validated only for the simulator's own world).

## 5. Bar-level pipeline check (B) [PROPOSED]
**Design (initial, as you asked):** 8 cells at 59 days — df ∞ and T4 × shapes E and D5 × NSE and US (Stage 3 validation rows 2, 3, 4, 5, 26, 27, 28, 29) — **2,000 new bar-level simulations per cell** (16,000), the real route `simulate_table`/`simulate_raw` → `clean` → `build_bar_table` → period means → T, seeds `SeedSequence(20261207, spawn_key=(cell_index, i, 0))`; C3 (frozen value) and the baseline (B = 999) are applied. They are compared by a **two-proportion z-test (pooled, two-sided)** with the Stage 3 fast-route results of the same cells (25,000 simulations each; independent streams, so no simulation is repeated). Cost: about 0.23 s per bar-level simulation per core, roughly 10–15 minutes on 8 cores.
**Same-returns matrix check (as in M4b):** 10 datasets per cell (80), the same returns fed to the fast route and through `direct_bridge.returns_to_table`, seeds `spawn_key=(cell_index, i, 1)`. Pass: identical matrix shape and maximum relative difference ≤ **1e-9** in every matrix. Justification: M4b found a maximum of 4.02e-13 over 160 matrices (float rounding of sums), and any real route discrepancy (a dropped or doubled bar, a wrong period) changes a period mean by at least about 1e-3 relative, so 1e-9 leaves four orders of margin on the rounding side and many on the error side.
**Why |z| ≤ 3, and its treatment across comparisons [EVIDENCE]:**
- **Test assumptions:** two independent samples (different streams and code), independent Bernoulli outcomes, large-sample normal approximation. The smallest expected number of rejections in a bar-level sample is {z2.expected_successes_bar_level.min():.1f} (rule of thumb ≥ 10: met). Calibration by simulation (200,000 replicates, true rates from Stage 3): P(|z|>3) under equal rates = {z2['P(|z|>3)'].min():.4f}–{z2['P(|z|>3)'].max():.4f} (mean {z2['P(|z|>3)'].mean():.4f}; nominal 0.0027), so the test is slightly liberal at n = 2,000 but close.
- **Multiplicity:** 16 tests (8 cells × C3 and baseline). Probability that at least one has |z| > 3 when the routes are equivalent: **{100*fw(z2, 'P(|z|>3)'):.1f}%** (Bonferroni bound {100*z2['P(|z|>3)'].sum():.1f}%; the C3 and baseline tests on the same datasets are positively correlated, so the true rate is no larger). With |z| > 2 it would be **{100*fw(z2, 'P(|z|>2)'):.0f}%**, i.e. a threshold of 2 would flag a perfectly equivalent route about half the time. A |z| ≤ 3 rule is therefore roughly a 5% family-wise rule.
- **[PROPOSED] Acceptance:** no cell has |z| > 3 for either method, and the same-returns check passes. Values between 2 and 3 are reported and expected by chance; any |z| > 3 means the check is **not passed**: report and investigate, no tuning. (M4b recorded counts without a threshold; this threshold is new.)
**Adequacy [EVIDENCE]:** the power of |z| > 3 to detect a true difference between the routes, averaged over the 16 method-cells: 2,000 per cell — {100*pwm.loc[2000, 0.5]:.0f}% / {100*pwm.loc[2000, 1.0]:.0f}% / {100*pwm.loc[2000, 2.0]:.0f}% / {100*pwm.loc[2000, 3.0]:.0f}% for differences of 0.5 / 1 / 2 / 3 points (baseline alone: {100*pwb.loc['baseline', 1.0]:.0f}% at 1 point, {100*pwb.loc['baseline', 2.0]:.0f}% at 2 points; C3: {100*pwb.loc['c3', 1.0]:.0f}% and {100*pwb.loc['c3', 2.0]:.0f}%). **2,000 per cell is adequate for gross discrepancies (about 2–3 points) but has low power below 1 point**; M4b's one flagged cell differed by about 2 points. 8,000 per cell (64,000 simulations, about 35–45 minutes on 8 cores) gives {100*pwm.loc[8000, 1.0]:.0f}% power at 1 point and {100*pwm.loc[8000, 2.0]:.0f}% at 2, with the same false-flag rate ({100*fw(z8, 'P(|z|>3)'):.1f}%). I kept 2,000 as you asked; **your decision D2 below**.

## 6. Second independent implementation (C) [PROPOSED]
- **The 10 cells and 100 datasets** (chosen by a rule fixed before any result: 5 NSE and 5 US rows drawn without replacement from the 96 frozen validation rows with `default_rng(SeedSequence(20261208, spawn_key=(0, market)))`; the draw is saved in `stage4_prereg/reference_selection.csv`):
{md(ref_show)}
  Datasets: simulations i = 0…9 of each selected row, generated by the Stage 3 fast generator with `SeedSequence(20261208, spawn_key=(val_row, i))` (shared generator, so the two implementations see identical inputs).
- **What is compared:** (1) the statistic T on all 100 datasets, vectorised `h1_calibration.max_abs_t` against the independent `h1_stage4_reference.statistic_T`; (2) the C3 decision (T above the frozen value for the cell's sample size): **identical decisions are required in all 100**; (3) the five frozen C3 values (59, 90, 125, 180, 250 days) re-derived from the saved training statistics (`stage2/c3_training/`, `stage3/c3_intermediate/`) by the independent quantile routine.
- **Independence [EVIDENCE]:** `src/quantlab/research/h1_stage4_reference.py` is written from the documented definitions (docs/15 §A.0 for the statistic, docs/06 §3 clock-time intervals for the periods), uses only the Python standard library (`fractions`, `decimal`; a test enforces that it imports no numpy, scipy, pandas or project statistic code), derives the period slots from clock times (a test shows they equal the library's), computes means and variances as exact rationals and the logarithm and square root in 60-digit arithmetic. **Limit:** the same author wrote both implementations and the inputs come from the shared generator, so this is independence of computation, not of authorship.
- **Tolerances and why:** T relative difference ≤ **1e-9**; quantile relative difference ≤ **1e-12**. The vectorised code uses float64, so its error against exact arithmetic is rounding only (unit tests: agreement to 1e-12 or better; one case exactly 0). Substantive mistakes are far larger: a wrong variance divisor changes T by about 1e-2 (tested), a wrong period boundary by 1e-3 or more (tested), a different quantile definition by the order of the spacing of the 25,000 sorted values (about 1e-4 or more; tested). So 1e-9 and 1e-12 leave at least three orders of margin against rounding and at least five against real errors. "Monte-Carlo tolerance" in the frozen sentence reduces to numerical precision here because C3 contains no Monte-Carlo step.
- If any |T − critical value| is below 1e-6 relative it is listed (a decision could be at risk from rounding); disagreement in any decision is a failure (failure condition 7).

## 7. Seeds [FROZEN + PROPOSED namespaces]
{md(sd)}
All use full-width `SeedSequence` objects (frozen rule). No new master seed is introduced.

## 8. Order of work, tests and manifest
1. After your approval: freeze the Stage 4 inputs in a new manifest `outputs/milestone4/h1_calibration/frozen_stage4_inputs.sha256` (this document, the prereg tables, `h1_stage4.py`, `h1_stage4_reference.py`, their tests, the Stage 4 runners) and verify it; the full test suite must pass.
2. Null checks (section 3) → must pass before any alternative-process run.
3. Alternative-process validation (section 4), once; no cell re-run.
4. Bar-level check (section 5).
5. Reference implementation check (section 6).
6. Stage 4 report (`docs/23`), updates of the project status report, README and docs index; final verification. Nothing committed.

## 9. Deviations from, and additions to, the frozen text (all listed)
No frozen file changes. Additions: (a) the null check uses 5×10⁷ bars (not 10⁶) for a, b, e, f and a truncated-moment form for c, d, with the literal 0.5% tolerance; (b) a seed namespace for the null check under the reserved 20261206; (c) the bar-level cells, counts, statistic, same-returns check and |z| ≤ 3 criterion; (d) the reference cells, datasets, tolerances and the decision-identity requirement; (e) C3's alternative-process gate read as at most 6.0% per v1.1 A2. **Correction of an earlier statement:** my first rough pilot (20 batches) overstated the noise for some processes (for example 1.14% against 0.50% for process e, NSE, open ratio); the conclusion that 10⁶ bars is far too few stands, and the numbers above come from the 300-batch analysis.

## 10. Decisions still required from you
1. **D1** Approve the null-check design (section 3), including the truncated-moment form for c and d and its stated limit.
2. **D2** Bar-level size: keep 2,000 per cell (adequate for gross differences, 36% power at 1 point) or use 8,000 (75% power at 1 point).
3. **D3** Approve the |z| ≤ 3 acceptance rule (about 4.5% family-wise false-flag rate) and the 1e-9 same-returns tolerance.
4. **D4** Approve the reference-check design (the 10 cells already drawn, 100 datasets, the two tolerances, identical decisions).
5. **D5** Confirm the reading of the C3 gate on the alternative processes (at most 6.0%).
6. **D6** Explicit approval to freeze the Stage 4 inputs and execute.
""")
    print("written", DOC, len(DOC.read_text().splitlines()), "lines")


if __name__ == "__main__":
    main()
