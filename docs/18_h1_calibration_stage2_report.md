# 18 — H1 calibration, Stage 2 report (candidate development, development grid only)

**Status: PENDING USER REVIEW. This report does NOT classify the candidates and does NOT recommend or decide advancement.** The formal classification (advance / further investigation / no candidate, docs/17 section 10) and any advancement decision are left to the user.
**What this shows:** the consolidated results of Stage 2 (C3 training, E4 development run, E5 summaries, the read-only D7/D2 investigation and the E6 power check), with integrity checks. **All data are simulated.** Generated 2026-11-05 12:54 by `scripts/milestone4/stage2_make_report.py --tests "<pytest line>"` from saved files only.
**Labels used throughout:** **[EVIDENCE]** computed from the saved files; **[HYPOTHESIS]** my reading, not proven; **[PROTOCOL]** a criterion fixed in docs/17, 17b, 17c; **[DECISION]** a choice that belongs to the user.

## 1. Summary of findings (computed evidence)
- **Run:** 1,780,000 development simulations (76 cells, seed 20261203), baseline + C1 + C3 on the same datasets, **0 failed simulations** for any method (0/0/0). No cell is near the 0.1% failure limit.
- **Baseline (reference only):** 28 FAIL and 8 FAIL_AMBIGUOUS of 68 gated cells; 16 of 44 tier A cells ambiguous.
- **C1:** 31 PASS, 25 PASS_AMBIGUOUS, **3 FAIL, 9 FAIL_AMBIGUOUS**; 17 of 44 tier A cells ambiguous (yardstick: fewer than 10); **4 D7 violations**; **52 D2 flags in 30 of 40 in-scope cells**.
- **C3 (labelled fallback):** all 68 gated cells pass its upper-limit-only gate (PASS_CLEAR); rejection rates are far below 5% in most cells (tier A median 1.43%, tier B median 3.44%; 40 of 68 cells below 2%); **22 D2 flags in 22 of 40 in-scope cells**, all on leverage.
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
| Frozen v1 manifest | 23 files verified |
| Frozen v1.1 manifest | 7 files verified |
| Stage 1 code manifest | 8 files verified |
| Stage 2 inputs manifest (`frozen_stage2_inputs.sha256`) | 18 files verified |
| Stage 2 addendum manifest | 2 files verified |
| C3 table manifest (`C3_TABLE.sha256`) | 2 files verified |
| E4 cell files | 76 files, 1,780,000 rows, simulation ids exact; statistic T identical across methods in every simulation; C3 rule `T > crit` holds exactly; problems: none |
| C3 table used by E4 equals the frozen table | True |
| Raw E4 outputs (digest of 77 file hashes) | `e4eb0a611e11453d71bc0190…` (byte-identical before and after E5 and E6, checked at each step) |
| E5 summaries (digest) | `10f978eca044d8d1eff40d9c…` |
| E6 outputs (digest) | `8dda8773a06ef8c78249e6ad…` |
| Test suite | 324 passed, 3 warnings in 48.50s (python -m pytest -q, run immediately before generation) |
| Environment | Python 3.12.13, numpy 2.5.4, pandas 3.1.0, scipy 1.18.1; macOS-15.4.1-arm64-arm-64bit |

**Run history [EVIDENCE].** E4 started 2026-11-02 13:26 and its last cell file was written 2026-11-03 12:46. The runner's compute clock shows 15.67 h (56397.0 s); the wall-clock span between the first and last cell files is 23.18 h. The 7.67 h difference is machine sleep (largest gaps before cells 12 and 13: 2.93 h and 2.84 h) despite `caffeinate`. The run continued and completed; seeds do not depend on the clock, so results are unaffected. The compute time exceeds the 11–12 h central estimate and sits at the top of the stated ±30% band (8–15.5 h). The power check took 463.2 s.

## 4. C3 training table and conservative behaviour
**Frozen table [EVIDENCE]** (`outputs/milestone4/h1_calibration/stage2/c3_training/c3_critical_values.csv`; 68 cells × 25,000 simulations, seed 20261202, 0 failures):
| n_days | c3_crit | source_dev_row | n_cells |
|---|---|---|---|
| 59 | 3.298658 | 50 | 44 |
| 125 | 2.880076 | 72 | 12 |
| 250 | 2.816000 | 73 | 12 |
- At 59 days the value is set by the day-volatility-0.6 stress cells: of the four such cells, rows 48, 50, 51 give 3.2280, 3.2987, 3.2892; the fourth (row 49) gives 3.0394, below the highest day-volatility-0.3 cell (3.0569). **Correction of an earlier chat statement:** an earlier summary described all four 0.6 cells as 3.23–3.30; row 49 is 3.0394.
- At 125 and 250 days the top cells are within about 0.5 to 2 standard errors of the maximum, so taking the maximum of noisy quantiles biases the value slightly upward [HYPOTHESIS, consistent with the bootstrap standard errors in `c3_training_cell_results.csv`].
- The in-sample "PASS" statuses in the training results used the same data the table was built from and carry no information about validity.

**Rejection behaviour in E4 (null) [EVIDENCE].** C3's null rejection rates in the 68 gated cells range from 0.49% to 5.25%: tier A median 1.43% (max 2.96%), tier B median 3.44% (max 5.25%); 40 of 68 cells are below 2%. C3 passes its upper-limit gate because it rarely rejects, not because it is calibrated: it is a conservative fixed critical value, valid only inside its training family (44 cells at 59 days, 12 at 125, 12 at 250), and it trades power for size (section 10).

## 5. E4 results by method [EVIDENCE]
Rejection rates are null rejection rates, nominal 5%. Source: `stage2/summary/stage2_cell_method_results.csv`, `stage2_candidate_outcomes.csv`.
| method | tier | cells | rate_min_% | rate_median_% | rate_max_% | PASS | PASS_AMBIG | FAIL | FAIL_AMBIG |
|---|---|---|---|---|---|---|---|---|---|
| baseline | A | 44 | 4.68 | 5.24 | 6.48 | 19 | 10 | 9 | 6 |
| baseline | B | 24 | 5.12 | 7.49 | 8.64 | 2 | 1 | 19 | 2 |
| c1 | A | 44 | 4.47 | 4.91 | 5.40 | 27 | 15 | 0 | 2 |
| c1 | B | 24 | 5.26 | 5.86 | 6.58 | 4 | 10 | 3 | 7 |
| c3 | A | 44 | 0.49 | 1.43 | 2.96 | 44 | 0 | 0 | 0 |
| c3 | B | 24 | 1.18 | 3.44 | 5.25 | 24 | 0 | 0 | 0 |

Candidate-level v1.1 outcomes computed by the classifier (not a selection): baseline **FAIL**, C1 **FAIL**, C3 **PASS_CLEAR** (C3 on upper limits only). Failures: 0 for every method and cell; no cell blocked by D6.

**C1: every gated cell that is not a clear PASS** (rate and Wilson 95% interval in %):
| dev_row | cell | tier | p_hat | wilson_low | wilson_high | status |
|---|---|---|---|---|---|---|
| 2 | G E NSE 59d | A | 4.47 | 4.22 | 4.73 | FAIL_AMBIGUOUS |
| 3 | G E US 59d | A | 4.72 | 4.47 | 4.99 | PASS_AMBIGUOUS |
| 4 | G D5 NSE 59d | A | 4.66 | 4.40 | 4.92 | PASS_AMBIGUOUS |
| 6 | G R2 NSE 59d | A | 4.60 | 4.35 | 4.87 | PASS_AMBIGUOUS |
| 7 | G R2 US 59d | A | 4.71 | 4.45 | 4.98 | PASS_AMBIGUOUS |
| 11 | T10 E US 59d | A | 4.66 | 4.40 | 4.92 | PASS_AMBIGUOUS |
| 12 | T10 D5 NSE 59d | A | 4.72 | 4.46 | 4.99 | PASS_AMBIGUOUS |
| 14 | T10 R2 NSE 59d | A | 4.76 | 4.50 | 5.03 | PASS_AMBIGUOUS |
| 15 | T10 R2 US 59d | A | 4.72 | 4.46 | 4.99 | PASS_AMBIGUOUS |
| 23 | T6 R2 US 59d | A | 5.30 | 5.03 | 5.58 | PASS_AMBIGUOUS |
| 24 | T4 flat NSE 59d | B | 5.74 | 5.46 | 6.04 | PASS_AMBIGUOUS |
| 25 | T4 flat US 59d | B | 5.72 | 5.43 | 6.01 | PASS_AMBIGUOUS |
| 26 | T4 E NSE 59d | B | 6.17 | 5.88 | 6.47 | FAIL_AMBIGUOUS |
| 27 | T4 E US 59d | B | 6.00 | 5.71 | 6.30 | PASS_AMBIGUOUS |
| 28 | T4 D5 NSE 59d | B | 6.36 | 6.06 | 6.67 | FAIL |
| 29 | T4 D5 US 59d | B | 6.21 | 5.92 | 6.51 | FAIL_AMBIGUOUS |
| 30 | T4 R2 NSE 59d | B | 6.03 | 5.74 | 6.33 | FAIL_AMBIGUOUS |
| 31 | T4 R2 US 59d | B | 5.86 | 5.57 | 6.15 | PASS_AMBIGUOUS |
| 40 | T6 E NSE 59d, est. dependence | A | 5.26 | 4.99 | 5.54 | PASS_AMBIGUOUS |
| 42 | T6 D5 NSE 59d, est. dependence | A | 5.25 | 4.98 | 5.54 | PASS_AMBIGUOUS |
| 43 | T6 D5 US 59d, est. dependence | A | 5.40 | 5.13 | 5.69 | PASS_AMBIGUOUS |
| 44 | T4 E NSE 59d, est. dependence | B | 6.22 | 5.93 | 6.53 | FAIL_AMBIGUOUS |
| 45 | T4 E US 59d, est. dependence | B | 5.84 | 5.55 | 6.13 | PASS_AMBIGUOUS |
| 46 | T4 D5 NSE 59d, est. dependence | B | 6.36 | 6.06 | 6.67 | FAIL |
| 47 | T4 D5 US 59d, est. dependence | B | 6.58 | 6.28 | 6.89 | FAIL |
| 48 | T4 E NSE 59d, day-vol 0.6 | B | 5.80 | 5.52 | 6.10 | PASS_AMBIGUOUS |
| 49 | T4 E US 59d, day-vol 0.6 | B | 6.07 | 5.78 | 6.37 | FAIL_AMBIGUOUS |
| 50 | T4 D5 NSE 59d, day-vol 0.6 | B | 6.19 | 5.90 | 6.50 | FAIL_AMBIGUOUS |
| 51 | T4 D5 US 59d, day-vol 0.6 | B | 6.07 | 5.78 | 6.37 | FAIL_AMBIGUOUS |
| 52 | G E NSE 125d | A | 4.71 | 4.46 | 4.98 | PASS_AMBIGUOUS |
| 54 | G E US 125d | A | 4.66 | 4.41 | 4.93 | PASS_AMBIGUOUS |
| 56 | G D5 NSE 125d | A | 4.48 | 4.23 | 4.74 | FAIL_AMBIGUOUS |
| 57 | G D5 NSE 250d | A | 4.66 | 4.41 | 4.93 | PASS_AMBIGUOUS |
| 68 | T4 E NSE 125d | B | 5.87 | 5.58 | 6.17 | PASS_AMBIGUOUS |
| 72 | T4 D5 NSE 125d | B | 5.75 | 5.47 | 6.05 | PASS_AMBIGUOUS |
| 73 | T4 D5 NSE 250d | B | 5.80 | 5.51 | 6.09 | PASS_AMBIGUOUS |
| 74 | T4 D5 US 125d | B | 5.80 | 5.51 | 6.09 | PASS_AMBIGUOUS |

- **Pattern [EVIDENCE]:** C1's rejection rate is slightly below nominal in Gaussian-like tier A cells (minimum 4.47%; the two tier A FAIL_AMBIGUOUS cells sit just under the 4.5% lower bound) and above nominal in the T4 (tier B) cells (median 5.86%, maximum 6.58%). It is closer to 5% than the baseline (tier B median 7.49%) but does not reach the tier B gate in every cell.
- **df 3 report-only cells** (no gate; rates in %):
| dev_row | cell | baseline | c1 | c3 |
|---|---|---|---|---|
| 32 | T3 flat NSE 59d | 5.94 | 7.17 | 2.07 |
| 33 | T3 flat US 59d | 4.69 | 6.39 | 1.31 |
| 34 | T3 E NSE 59d | 9.66 | 7.81 | 5.61 |
| 35 | T3 E US 59d | 7.84 | 7.92 | 3.66 |
| 36 | T3 D5 NSE 59d | 10.92 | 8.96 | 6.66 |
| 37 | T3 D5 US 59d | 10.36 | 8.36 | 6.26 |
| 38 | T3 R2 NSE 59d | 6.52 | 7.53 | 3.08 |
| 39 | T3 R2 US 59d | 5.66 | 6.80 | 2.27 |

## 6. Ambiguity flags (D4) [EVIDENCE + PROTOCOL]
The yardstick is 10 ambiguous tier A cells; it is a judgement value that assumes every cell is exactly 5.0% and cells are independent (for such a method the expectation is 4.2 ambiguous cells of 44; docs/17 section 5). Computed: baseline 16, **C1 17**, C3 0. The yardstick is reached by the baseline and by C1. For C1 several ambiguous tier A cells are slightly *below* the 5% centre (rates of about 4.5–4.8%), consistent with the mild under-rejection noted above. No replication was run and none is automatic (D10).

## 7. Critical-value variability and the D7 violations (D7, 40-cell scope)
**[PROTOCOL]** D7: C1's critical-value CV must be below the baseline's in the 40 in-scope cells (24 tier B + 16 tier A at 125/250 days); C3 exempt; CV reported in all cells.
**[EVIDENCE]** C1's CV is below the baseline's in 36 of 40 in-scope cells (median C1 CV 0.060 against 0.393). **There are 4 violations, all kept as counted:**
| dev_row | tail | shape | market | n_days | tier | baseline_crit_cv | c1_crit_cv | diff | ratio | baseline_crit_mean | c1_crit_mean | oracle_q95_T |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 53 | G | E | NSE | 250 | A | 0.0313 | 0.0352 | +0.0040 | 1.127 | 2.3638 | 2.3701 | 2.3717 |
| 55 | G | E | US | 250 | A | 0.0296 | 0.0346 | +0.0050 | 1.170 | 2.3707 | 2.3711 | 2.3772 |
| 57 | G | D5 | NSE | 250 | A | 0.0311 | 0.0347 | +0.0036 | 1.115 | 2.3766 | 2.3826 | 2.3652 |
| 59 | G | D5 | US | 250 | A | 0.0313 | 0.0347 | +0.0034 | 1.109 | 2.3769 | 2.3815 | 2.3722 |
- Common features: df ∞, tier A, 250 days, no dependence, day-volatility 0.3; E and D5 shapes in both markets: these are **all four df ∞ cells that exist at 250 days**, so no cell in that category passes the rule.
- Similar cells (df ∞, all sizes):
| dev_row | shape | market | n_days | in_D7_scope_40 | baseline_crit_cv | c1_crit_cv | diff | ratio | d7_violation_c1 |
|---|---|---|---|---|---|---|---|---|---|
| 4 | D5 | NSE | 59 | False | 0.0683 | 0.0384 | -0.0299 | 0.562 | False |
| 5 | D5 | US | 59 | False | 0.0693 | 0.0386 | -0.0307 | 0.557 | False |
| 2 | E | NSE | 59 | False | 0.0712 | 0.0392 | -0.0320 | 0.551 | False |
| 3 | E | US | 59 | False | 0.0618 | 0.0376 | -0.0241 | 0.609 | False |
| 6 | R2 | NSE | 59 | False | 0.0525 | 0.0371 | -0.0155 | 0.705 | False |
| 7 | R2 | US | 59 | False | 0.0509 | 0.0363 | -0.0146 | 0.712 | False |
| 0 | flat | NSE | 59 | False | 0.0383 | 0.0355 | -0.0028 | 0.926 | False |
| 1 | flat | US | 59 | False | 0.0372 | 0.0351 | -0.0021 | 0.944 | False |
| 56 | D5 | NSE | 125 | True | 0.0437 | 0.0360 | -0.0077 | 0.824 | False |
| 58 | D5 | US | 125 | True | 0.0454 | 0.0360 | -0.0094 | 0.793 | False |
| 52 | E | NSE | 125 | True | 0.0456 | 0.0361 | -0.0095 | 0.793 | False |
| 54 | E | US | 125 | True | 0.0405 | 0.0359 | -0.0046 | 0.886 | False |
| 57 | D5 | NSE | 250 | True | 0.0311 | 0.0347 | +0.0036 | 1.115 | True |
| 59 | D5 | US | 250 | True | 0.0313 | 0.0347 | +0.0034 | 1.109 | True |
| 53 | E | NSE | 250 | True | 0.0313 | 0.0352 | +0.0040 | 1.127 | True |
| 55 | E | US | 250 | True | 0.0296 | 0.0346 | +0.0050 | 1.170 | True |
- Mean CV over the df ∞ cells by sample size: 59 days: baseline 0.0562 / C1 0.0372, 125 days: baseline 0.0438 / C1 0.0360, 250 days: baseline 0.0308 / C1 0.0348. The baseline's CV falls with sample size while C1's is nearly constant, so the ratio crosses 1 between 125 and 250 days. In the other 36 in-scope cells C1's CV is 0.13–0.28 of the baseline's (T4 and T6), so the violations are confined to the benign df ∞ cells.
- Sampling noise [EVIDENCE]: a paired bootstrap over the 25,000 simulations gives CV differences of 0.0034–0.0050, about 8.5 bootstrap standard errors above zero, with 95% intervals that exclude zero. The differences are not noise.
- **Monte-Carlo floor (contextual evidence only, NOT a waiver):** the asymptotic CV of a 95% quantile estimated from R Monte-Carlo draws is computed from a kernel-density estimate of T at its 95% quantile.
| dev_row | observed_cv_baseline | mc_floor_B999 | observed_cv_c1 | mc_floor_R499 | cv_diff | boot_se | corr_crit_baseline_c1 |
|---|---|---|---|---|---|---|---|
| 53 | 0.0313 | 0.0242 | 0.0352 | 0.0342 | 0.0040 | 0.0005 | 0.010 |
| 55 | 0.0296 | 0.0244 | 0.0346 | 0.0345 | 0.0050 | 0.0005 | 0.004 |
| 57 | 0.0311 | 0.0244 | 0.0347 | 0.0345 | 0.0036 | 0.0005 | 0.001 |
| 59 | 0.0313 | 0.0254 | 0.0347 | 0.0359 | 0.0034 | 0.0004 | 0.003 |
- **[HYPOTHESIS]** C1's CV at 250 days is essentially Monte-Carlo noise from using R = 499 resamples: its observed CV (0.0346–0.0352) is close to the R = 499 floor (0.0342–0.0359), while the baseline's (0.0296–0.0313) lies above its B = 999 floor (0.0242–0.0254); critical values of the two methods are uncorrelated across datasets (0.001 to 0.010). C1's mean critical value matches the oracle 95% quantile to within 0.017. Not tested: whether a larger R would remove the violations; that would be a candidate revision (D5) and was not done.

## 8. Conditional calibration and the D2 flags (D2, 40-cell scope)
**[PROTOCOL]** Flag `<=>` `observed_spread − 1.25 × reference_spread >= 0.02` (fractions); spread = max − min rejection rate across quartiles of leverage, kurtosis or the method's own critical value; reference = same method and variable in the df ∞ cell matched on shape, market and sample size; a **judgement-based diagnostic threshold, not a statistical test**. In 12 gated cells (dev_row 44–51 inside the scope, 40–43 outside) the reference is not matched on dependence / day-volatility and every flag there is labelled **"reference not matched on dependence / day-volatility"**.
**[EVIDENCE]** Of 200 in-scope C1/C3 comparisons, **74 are flagged** (C1 52 of 120, C3 22 of 80); the baseline (reference only) has 64 of 120. All 74 are preserved in `stage2/report_tables/d2_flagged_74.csv` (and listed in appendix A); the full 200 comparisons with the exact calculation are in `d2_inscope_comparisons_c1_c3.csv`.
| method | conditioning_variable | flagged | compared |
|---|---|---|---|
| c1 | kurtosis | 0 | 40 |
| c1 | leverage | 29 | 40 |
| c1 | own_critical_value | 23 | 40 |
| c3 | kurtosis | 0 | 40 |
| c3 | leverage | 22 | 40 |
- **By cell (cells with at least one flag):** C1 30 of 40, C3 22 of 40.
  - C1 by tail: G: 0/8, T4: 24/24, T6: 6/8; by sample size: 59: 16/16, 125: 6/12, 250: 8/12; by market: NSE: 16/20, US: 14/20; by tier: A: 6/16, B: 24/24.
  - C3 by tail: G: 0/8, T4: 19/24, T6: 3/8; by sample size: 59: 11/16, 125: 6/12, 250: 5/12; by market: NSE: 14/20, US: 8/20; by tier: A: 3/16, B: 19/24.
  - Dependence / day-volatility (C1): ('estimated', 0.3): 4/4, ('none', 0.3): 22/32, ('none', 0.6): 4/4; (C3): ('estimated', 0.3): 3/4, ('none', 0.3): 15/32, ('none', 0.6): 4/4.
- Cells with no C1 flag: 52, 53, 54, 55, 56, 57, 58, 59, 62, 66 (df ∞ cells and two T6 US 125-day cells). No flag appears on kurtosis for either method (0 of 80); T6 flags are all on leverage.
- Median spreads, flagged vs unflagged (fractions): c1/leverage: 0.0821 vs 0.0312; c1/own_critical_value: 0.0787 vs 0.0325; c3/leverage: 0.0532 vs 0.0154.
- Reference (df ∞) spreads are not small: leverage median 0.0275 (max 0.0667); own critical value median 0.0287.
- Link to rejection rates (C1, 40 in-scope cells): flagged cells have median rate 5.80% against 4.89% for unflagged; all three clear FAIL cells are flagged.
- **Labelled cells [EVIDENCE]:** 40 labelled in-scope comparisons (dev_row 44–51), 22 flagged (55.0%), against 19 of 40 (47.5%) in unlabelled T4 59-day cells with a matched reference. Labels are preserved in every output. Flags in the labelled cells are less reliable (a Gaussian world with dependence or higher volatility could itself show a different gradient) and are not stronger evidence than flags in the 32 matched cells.

**The 19 borderline comparisons** (within ±0.005 of the threshold, i.e. `|spread − 1.25 × reference − 0.02| <= 0.005`). They are flagged or not by the exact rule; **nothing about the threshold was changed**. The flag status of these comparisons is sensitive to small changes. Full file: `stage2/report_tables/d2_borderline_19.csv`.
| dev_row | cell | method | conditioning_variable | spread | reference_spread | threshold_1.25x_ref | excess | margin_vs_0.02 | flagged | d2_label |
|---|---|---|---|---|---|---|---|---|---|---|
| 66 | T6 D5 US 125d | c1 | leverage | 0.0566 | 0.0333 | 0.0416 | 0.0150 | -0.0050 | False |  |
| 51 | T4 D5 US 59d, day-vol 0.6 | c3 | kurtosis | 0.0174 | 0.0019 | 0.0024 | 0.0150 | -0.0050 | False | reference not matched on dependence / day-volatility |
| 62 | T6 E US 125d | c1 | leverage | 0.0528 | 0.0298 | 0.0372 | 0.0156 | -0.0044 | False |  |
| 51 | T4 D5 US 59d, day-vol 0.6 | c1 | leverage | 0.0710 | 0.0442 | 0.0552 | 0.0158 | -0.0042 | False | reference not matched on dependence / day-volatility |
| 64 | T6 D5 NSE 125d | c1 | own_critical_value | 0.0387 | 0.0182 | 0.0228 | 0.0159 | -0.0041 | False |  |
| 62 | T6 E US 125d | c3 | leverage | 0.0304 | 0.0115 | 0.0144 | 0.0160 | -0.0040 | False |  |
| 31 | T4 R2 US 59d | c3 | leverage | 0.0253 | 0.0062 | 0.0078 | 0.0175 | -0.0025 | False |  |
| 27 | T4 E US 59d | c3 | leverage | 0.0318 | 0.0107 | 0.0134 | 0.0184 | -0.0016 | False |  |
| 45 | T4 E US 59d, est. dependence | c3 | leverage | 0.0318 | 0.0107 | 0.0134 | 0.0184 | -0.0016 | False | reference not matched on dependence / day-volatility |
| 63 | T6 E US 250d | c3 | leverage | 0.0285 | 0.0078 | 0.0098 | 0.0187 | -0.0013 | False |  |
| 25 | T4 flat US 59d | c1 | own_critical_value | 0.0562 | 0.0298 | 0.0372 | 0.0190 | -0.0010 | False |  |
| 65 | T6 D5 NSE 250d | c3 | leverage | 0.0309 | 0.0090 | 0.0112 | 0.0197 | -0.0003 | False |  |
| 65 | T6 D5 NSE 250d | c1 | leverage | 0.0557 | 0.0282 | 0.0352 | 0.0205 | +0.0005 | True |  |
| 67 | T6 D5 US 250d | c1 | leverage | 0.0488 | 0.0224 | 0.0280 | 0.0208 | +0.0008 | True |  |
| 49 | T4 E US 59d, day-vol 0.6 | c3 | leverage | 0.0344 | 0.0107 | 0.0134 | 0.0210 | +0.0010 | True | reference not matched on dependence / day-volatility |
| 64 | T6 D5 NSE 125d | c3 | leverage | 0.0402 | 0.0147 | 0.0184 | 0.0218 | +0.0018 | True |  |
| 51 | T4 D5 US 59d, day-vol 0.6 | c1 | own_critical_value | 0.0544 | 0.0261 | 0.0326 | 0.0218 | +0.0018 | True | reference not matched on dependence / day-volatility |
| 49 | T4 E US 59d, day-vol 0.6 | c1 | leverage | 0.0677 | 0.0355 | 0.0444 | 0.0233 | +0.0033 | True | reference not matched on dependence / day-volatility |
| 30 | T4 R2 NSE 59d | c3 | leverage | 0.0312 | 0.0053 | 0.0066 | 0.0246 | +0.0046 | True |  |
- **[HYPOTHESES]** (a) A fixed critical value rejects more when leverage is high, so C3's leverage flags may be built in; no evidence beyond the pattern. (b) C1 reduces the critical-value gradient relative to the baseline (median own-critical-value spread 0.0469 against 0.1060) but not to the df ∞ reference level in T4 cells. (c) The binomial noise of a spread from four equal true rates is about 0.0057; the 0.02 excess is about 3.5 times that, so most flags look like real gradients while the borderline ones are sensitive.

## 9. Plumbing, p-values and paired comparisons [EVIDENCE]
- **Plumbing check vs Stage 1 (baseline, 30 overlapping cells):** maximum |z| = 2.48; 0 cells above 3 and 1 above 2. The Stage 2 pipeline reproduces Stage 1 baseline rates; this checks the machinery, it is not validation.
- **C1 p-value deciles** (mean over 76 cells; uniform = 0.100): 0.105, 0.102, 0.104, 0.100, 0.101, 0.102, 0.098, 0.095, 0.096, 0.097.
- **Paired with the baseline on the same datasets:** C1: baseline-only rejections 24,368, C1-only 11,062; cells with sign-test p < 0.001: 60 of 76. C3: baseline-only 71,017, C3-only 2,447; 76 of 76. Descriptive only.

## 10. E6 power check — diagnostic only, not candidate selection or validation
Six cells (T4 flat ×1.1 and ×1.2, T4 E ×1.2; both markets; 59 days; no dependence; day-volatility 0.3), 5,000 simulations each, seed 20261212, baseline, C1 and C3 on the same data; 0 failures. Power (%) [Wilson 95%] (`stage2/power_check/power_by_cell_method.csv`):
| power_cell | shape | mult | market | base | c1 | c3 |
|---|---|---|---|---|---|---|
| 0 | flat | 1.1 | NSE | 31.3 [30.0, 32.6] | 35.6 [34.3, 37.0] | 12.9 [12.0, 13.8] |
| 1 | flat | 1.1 | US | 42.4 [41.0, 43.8] | 48.4 [47.0, 49.8] | 20.3 [19.2, 21.4] |
| 2 | flat | 1.2 | NSE | 86.0 [85.0, 86.9] | 93.4 [92.7, 94.1] | 82.4 [81.3, 83.4] |
| 3 | flat | 1.2 | US | 89.5 [88.6, 90.3] | 95.2 [94.5, 95.7] | 88.1 [87.2, 89.0] |
| 4 | E | 1.2 | NSE | 64.3 [63.0, 65.6] | 69.1 [67.8, 70.3] | 54.3 [52.9, 55.7] |
| 5 | E | 1.2 | US | 71.7 [70.5, 73.0] | 79.7 [78.5, 80.8] | 60.6 [59.2, 61.9] |

Ratio to the baseline and the single D3 flag (candidate power below 70% of the baseline's at T4 flat ×1.2):
| power_cell | shape | mult | market | method | power_method | power_baseline | ratio_to_baseline | flag_cell | power_collapse_flag |
|---|---|---|---|---|---|---|---|---|---|
| 0 | flat | 1.1 | NSE | c1 | 0.3564 | 0.3126 | 1.1401 | False | False |
| 0 | flat | 1.1 | NSE | c3 | 0.1288 | 0.3126 | 0.4120 | False | False |
| 1 | flat | 1.1 | US | c1 | 0.4842 | 0.4238 | 1.1425 | False | False |
| 1 | flat | 1.1 | US | c3 | 0.2026 | 0.4238 | 0.4781 | False | False |
| 2 | flat | 1.2 | NSE | c1 | 0.9344 | 0.8600 | 1.0865 | True | False |
| 2 | flat | 1.2 | NSE | c3 | 0.8236 | 0.8600 | 0.9577 | True | False |
| 3 | flat | 1.2 | US | c1 | 0.9516 | 0.8950 | 1.0632 | True | False |
| 3 | flat | 1.2 | US | c3 | 0.8810 | 0.8950 | 0.9844 | True | False |
| 4 | E | 1.2 | NSE | c1 | 0.6908 | 0.6432 | 1.0740 | False | False |
| 4 | E | 1.2 | NSE | c3 | 0.5432 | 0.6432 | 0.8445 | False | False |
| 5 | E | 1.2 | US | c1 | 0.7966 | 0.7174 | 1.1104 | False | False |
| 5 | E | 1.2 | US | c3 | 0.6056 | 0.7174 | 0.8442 | False | False |

- **Flag:** not raised for either method in either market.
- **Not size-adjusted [EVIDENCE]:** the null rejection rates in the matching development cells are
| dev_row | cell | baseline | c1 | c3 |
|---|---|---|---|---|
| 24 | T4 flat NSE 59d | 5.30 | 5.74 | 1.19 |
| 25 | T4 flat US 59d | 5.12 | 5.72 | 1.18 |
| 26 | T4 E NSE 59d | 7.95 | 6.17 | 3.36 |
| 27 | T4 E US 59d | 6.64 | 6.00 | 2.21 |
  so part of C1's higher power in the flat cells may reflect its larger size there (about 5.7% against 5.1–5.3%), and C3's low power at ×1.1 reflects its conservatism (about 1.2% null rejection). In the E cells the baseline over-rejects, so the power ratios there are not a fair yardstick and no flag applies.
- This check **plays no role in candidate selection or validation**.

## 11. Advancement criteria as computed (docs/17 section 10 A) [PROTOCOL + EVIDENCE]
These compare the computed results with the pre-specified criteria. **They are facts, not a classification.**
| Criterion | C1 | C3 |
|---|---|---|
| A.1 gates (D4): no FAIL or FAIL_AMBIGUOUS | **Not met:** 3 FAIL and 9 FAIL_AMBIGUOUS of 68 | Met: 68 of 68 pass on upper limits only |
| A.2 ambiguous tier A cells below 10 | **Not met:** 17 of 44 | Met: 0 |
| A.3 failures at most 0.1% per cell | Met (0) | Met (0) |
| A.4 CV below baseline in the 40 cells (D7) | **Not met:** 4 violations | Exempt (constant critical value) |
| A.5 no D2 flag in the 40 in-scope cells | **Not met:** 52 flagged comparisons in 30 cells | **Not met:** 22 flagged comparisons in 22 cells |
| A.6 plumbing check passed; no power-collapse flag (diagnostic) | Met; flag not raised | Met; flag not raised |
| A.7 explicit user approval | **Pending** | **Pending** |

**Formal classification (docs/17 section 10: advance to Stage 3 / further investigation / no candidate selected): PENDING USER REVIEW. This report makes no recommendation.** The baseline is never selectable; C2 was not run.

## 12. Evidence, hypotheses, protocol criteria and decisions that remain
**Computed evidence:** sections 3–10 and the tables in `stage2/report_tables/`.
**Hypotheses (not proven):** the Monte-Carlo-noise reading of the D7 violations (section 7); the built-in leverage gradient of a fixed critical value, the partial reduction of C1's critical-value gradient, and the noise scale of the D2 borderline calls (section 8); the upward bias of the C3 maximum (section 4); C1's power advantage partly reflecting size (section 10).
**Protocol criteria applied unchanged:** gates, D2 formula and threshold, D4 yardstick, D6, D7 scope, D3 flag. All four D7 violations and all 74 D2 flags stand as counted; the 19 borderline comparisons are highlighted and unchanged; no candidate was revised.
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

## Appendix A. All 74 flagged D2 comparisons (C1 and C3, in scope)
| dev_row | cell | method | conditioning_variable | spread | reference_spread | excess | margin_vs_0.02 | borderline_pm0.005 | d2_label |
|---|---|---|---|---|---|---|---|---|---|
| 24 | T4 flat NSE 59d | c1 | leverage | 0.0726 | 0.0221 | 0.0450 | +0.0250 | False |  |
| 24 | T4 flat NSE 59d | c1 | own_critical_value | 0.0728 | 0.0238 | 0.0430 | +0.0230 | False |  |
| 25 | T4 flat US 59d | c1 | leverage | 0.0582 | 0.0144 | 0.0402 | +0.0202 | False |  |
| 26 | T4 E NSE 59d | c1 | leverage | 0.1187 | 0.0477 | 0.0591 | +0.0391 | False |  |
| 26 | T4 E NSE 59d | c1 | own_critical_value | 0.0822 | 0.0235 | 0.0528 | +0.0328 | False |  |
| 27 | T4 E US 59d | c1 | leverage | 0.0832 | 0.0355 | 0.0388 | +0.0188 | False |  |
| 27 | T4 E US 59d | c1 | own_critical_value | 0.0891 | 0.0229 | 0.0605 | +0.0405 | False |  |
| 28 | T4 D5 NSE 59d | c1 | leverage | 0.0870 | 0.0304 | 0.0490 | +0.0290 | False |  |
| 28 | T4 D5 NSE 59d | c1 | own_critical_value | 0.0867 | 0.0283 | 0.0513 | +0.0313 | False |  |
| 29 | T4 D5 US 59d | c1 | leverage | 0.0890 | 0.0442 | 0.0338 | +0.0138 | False |  |
| 29 | T4 D5 US 59d | c1 | own_critical_value | 0.0848 | 0.0261 | 0.0522 | +0.0322 | False |  |
| 30 | T4 R2 NSE 59d | c1 | leverage | 0.0896 | 0.0317 | 0.0500 | +0.0300 | False |  |
| 30 | T4 R2 NSE 59d | c1 | own_critical_value | 0.0883 | 0.0274 | 0.0541 | +0.0341 | False |  |
| 31 | T4 R2 US 59d | c1 | leverage | 0.0819 | 0.0184 | 0.0589 | +0.0389 | False |  |
| 31 | T4 R2 US 59d | c1 | own_critical_value | 0.0787 | 0.0256 | 0.0467 | +0.0267 | False |  |
| 44 | T4 E NSE 59d, est. dependence | c1 | leverage | 0.1106 | 0.0477 | 0.0510 | +0.0310 | False | reference not matched on dependence / day-volatility |
| 44 | T4 E NSE 59d, est. dependence | c1 | own_critical_value | 0.0774 | 0.0235 | 0.0480 | +0.0280 | False | reference not matched on dependence / day-volatility |
| 45 | T4 E US 59d, est. dependence | c1 | leverage | 0.0861 | 0.0355 | 0.0417 | +0.0217 | False | reference not matched on dependence / day-volatility |
| 45 | T4 E US 59d, est. dependence | c1 | own_critical_value | 0.0858 | 0.0229 | 0.0572 | +0.0372 | False | reference not matched on dependence / day-volatility |
| 46 | T4 D5 NSE 59d, est. dependence | c1 | leverage | 0.0856 | 0.0304 | 0.0476 | +0.0276 | False | reference not matched on dependence / day-volatility |
| 46 | T4 D5 NSE 59d, est. dependence | c1 | own_critical_value | 0.0845 | 0.0283 | 0.0491 | +0.0291 | False | reference not matched on dependence / day-volatility |
| 47 | T4 D5 US 59d, est. dependence | c1 | leverage | 0.0872 | 0.0442 | 0.0320 | +0.0120 | False | reference not matched on dependence / day-volatility |
| 47 | T4 D5 US 59d, est. dependence | c1 | own_critical_value | 0.0846 | 0.0261 | 0.0520 | +0.0320 | False | reference not matched on dependence / day-volatility |
| 48 | T4 E NSE 59d, day-vol 0.6 | c1 | leverage | 0.0885 | 0.0477 | 0.0289 | +0.0089 | False | reference not matched on dependence / day-volatility |
| 48 | T4 E NSE 59d, day-vol 0.6 | c1 | own_critical_value | 0.0662 | 0.0235 | 0.0368 | +0.0168 | False | reference not matched on dependence / day-volatility |
| 49 | T4 E US 59d, day-vol 0.6 | c1 | leverage | 0.0677 | 0.0355 | 0.0233 | +0.0033 | True | reference not matched on dependence / day-volatility |
| 49 | T4 E US 59d, day-vol 0.6 | c1 | own_critical_value | 0.0762 | 0.0229 | 0.0476 | +0.0276 | False | reference not matched on dependence / day-volatility |
| 50 | T4 D5 NSE 59d, day-vol 0.6 | c1 | leverage | 0.0709 | 0.0304 | 0.0329 | +0.0129 | False | reference not matched on dependence / day-volatility |
| 50 | T4 D5 NSE 59d, day-vol 0.6 | c1 | own_critical_value | 0.0734 | 0.0283 | 0.0380 | +0.0180 | False | reference not matched on dependence / day-volatility |
| 51 | T4 D5 US 59d, day-vol 0.6 | c1 | own_critical_value | 0.0544 | 0.0261 | 0.0218 | +0.0018 | True | reference not matched on dependence / day-volatility |
| 60 | T6 E NSE 125d | c1 | leverage | 0.0781 | 0.0411 | 0.0267 | +0.0067 | False |  |
| 61 | T6 E NSE 250d | c1 | leverage | 0.0763 | 0.0312 | 0.0373 | +0.0173 | False |  |
| 63 | T6 E US 250d | c1 | leverage | 0.0549 | 0.0213 | 0.0283 | +0.0083 | False |  |
| 64 | T6 D5 NSE 125d | c1 | leverage | 0.0635 | 0.0283 | 0.0281 | +0.0081 | False |  |
| 65 | T6 D5 NSE 250d | c1 | leverage | 0.0557 | 0.0282 | 0.0205 | +0.0005 | True |  |
| 67 | T6 D5 US 250d | c1 | leverage | 0.0488 | 0.0224 | 0.0208 | +0.0008 | True |  |
| 68 | T4 E NSE 125d | c1 | leverage | 0.1010 | 0.0411 | 0.0496 | +0.0296 | False |  |
| 68 | T4 E NSE 125d | c1 | own_critical_value | 0.0790 | 0.0256 | 0.0470 | +0.0270 | False |  |
| 69 | T4 E NSE 250d | c1 | leverage | 0.0971 | 0.0312 | 0.0581 | +0.0381 | False |  |
| 69 | T4 E NSE 250d | c1 | own_critical_value | 0.0776 | 0.0298 | 0.0404 | +0.0204 | False |  |
| 70 | T4 E US 125d | c1 | leverage | 0.0805 | 0.0298 | 0.0433 | +0.0233 | False |  |
| 70 | T4 E US 125d | c1 | own_critical_value | 0.0851 | 0.0277 | 0.0505 | +0.0305 | False |  |
| 71 | T4 E US 250d | c1 | leverage | 0.0771 | 0.0213 | 0.0505 | +0.0305 | False |  |
| 71 | T4 E US 250d | c1 | own_critical_value | 0.0712 | 0.0278 | 0.0364 | +0.0164 | False |  |
| 72 | T4 D5 NSE 125d | c1 | leverage | 0.0853 | 0.0283 | 0.0499 | +0.0299 | False |  |
| 72 | T4 D5 NSE 125d | c1 | own_critical_value | 0.0854 | 0.0182 | 0.0626 | +0.0426 | False |  |
| 73 | T4 D5 NSE 250d | c1 | leverage | 0.0878 | 0.0282 | 0.0526 | +0.0326 | False |  |
| 73 | T4 D5 NSE 250d | c1 | own_critical_value | 0.0760 | 0.0184 | 0.0530 | +0.0330 | False |  |
| 74 | T4 D5 US 125d | c1 | leverage | 0.0821 | 0.0333 | 0.0405 | +0.0205 | False |  |
| 74 | T4 D5 US 125d | c1 | own_critical_value | 0.0709 | 0.0256 | 0.0389 | +0.0189 | False |  |
| 75 | T4 D5 US 250d | c1 | leverage | 0.0821 | 0.0224 | 0.0541 | +0.0341 | False |  |
| 75 | T4 D5 US 250d | c1 | own_critical_value | 0.0667 | 0.0250 | 0.0355 | +0.0155 | False |  |
| 26 | T4 E NSE 59d | c3 | leverage | 0.0613 | 0.0123 | 0.0459 | +0.0259 | False |  |
| 28 | T4 D5 NSE 59d | c3 | leverage | 0.0440 | 0.0093 | 0.0324 | +0.0124 | False |  |
| 29 | T4 D5 US 59d | c3 | leverage | 0.0467 | 0.0104 | 0.0337 | +0.0137 | False |  |
| 30 | T4 R2 NSE 59d | c3 | leverage | 0.0312 | 0.0053 | 0.0246 | +0.0046 | True |  |
| 44 | T4 E NSE 59d, est. dependence | c3 | leverage | 0.0618 | 0.0123 | 0.0464 | +0.0264 | False | reference not matched on dependence / day-volatility |
| 46 | T4 D5 NSE 59d, est. dependence | c3 | leverage | 0.0446 | 0.0093 | 0.0330 | +0.0130 | False | reference not matched on dependence / day-volatility |
| 47 | T4 D5 US 59d, est. dependence | c3 | leverage | 0.0467 | 0.0104 | 0.0337 | +0.0137 | False | reference not matched on dependence / day-volatility |
| 48 | T4 E NSE 59d, day-vol 0.6 | c3 | leverage | 0.0651 | 0.0123 | 0.0497 | +0.0297 | False | reference not matched on dependence / day-volatility |
| 49 | T4 E US 59d, day-vol 0.6 | c3 | leverage | 0.0344 | 0.0107 | 0.0210 | +0.0010 | True | reference not matched on dependence / day-volatility |
| 50 | T4 D5 NSE 59d, day-vol 0.6 | c3 | leverage | 0.0549 | 0.0093 | 0.0433 | +0.0233 | False | reference not matched on dependence / day-volatility |
| 51 | T4 D5 US 59d, day-vol 0.6 | c3 | leverage | 0.0563 | 0.0104 | 0.0433 | +0.0233 | False | reference not matched on dependence / day-volatility |
| 60 | T6 E NSE 125d | c3 | leverage | 0.0515 | 0.0146 | 0.0333 | +0.0133 | False |  |
| 61 | T6 E NSE 250d | c3 | leverage | 0.0438 | 0.0147 | 0.0254 | +0.0054 | False |  |
| 64 | T6 D5 NSE 125d | c3 | leverage | 0.0402 | 0.0147 | 0.0218 | +0.0018 | True |  |
| 68 | T4 E NSE 125d | c3 | leverage | 0.0829 | 0.0146 | 0.0647 | +0.0447 | False |  |
| 69 | T4 E NSE 250d | c3 | leverage | 0.0778 | 0.0147 | 0.0594 | +0.0394 | False |  |
| 70 | T4 E US 125d | c3 | leverage | 0.0507 | 0.0115 | 0.0363 | +0.0163 | False |  |
| 71 | T4 E US 250d | c3 | leverage | 0.0470 | 0.0078 | 0.0372 | +0.0172 | False |  |
| 72 | T4 D5 NSE 125d | c3 | leverage | 0.0720 | 0.0147 | 0.0536 | +0.0336 | False |  |
| 73 | T4 D5 NSE 250d | c3 | leverage | 0.0696 | 0.0090 | 0.0584 | +0.0384 | False |  |
| 74 | T4 D5 US 125d | c3 | leverage | 0.0696 | 0.0160 | 0.0496 | +0.0296 | False |  |
| 75 | T4 D5 US 250d | c3 | leverage | 0.0704 | 0.0130 | 0.0542 | +0.0342 | False |  |

## Appendix B. Files
- Report generator: `scripts/milestone4/stage2_make_report.py`; supporting tables: `outputs/milestone4/h1_calibration/stage2/report_tables/` (`d2_flagged_74.csv`, `d2_borderline_19.csv`, `d2_inscope_comparisons_c1_c3.csv`, `d7_four_violations.csv`, `d7_mc_floor_evidence.csv`).
- E4: `stage2/development/` (76 cell files, run metadata), log `stage2_development_run.log`. E5: `stage2/summary/` (7 CSVs). E6: `stage2/power_check/`, log `stage2_power_check_run.log`. C3: `stage2/c3_training/`.
- Records: docs/17, 17b, 17c. Frozen inputs and manifests were not modified.
