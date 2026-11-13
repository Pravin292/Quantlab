# 21 — H1 calibration, Stage 3 report (locked validation of C3)

**Status:** Stage 3 executed once under the frozen protocol; this report states what the pre-specified gates give for C3. **It does not make the Stage 5 decision and does not claim that H1 is calibrated.** Stages 4 and 5 are not authorised by the Stage 3 decision and were not started. **All data are simulated.** Generated 2026-11-05 14:25 by `scripts/milestone4/stage3_make_report.py` from saved files only.
**Labels:** **[EVIDENCE]** computed from the saved files; **[HYPOTHESIS]** my reading; **[PROTOCOL]** pre-specified in docs/13, 15a, 20; **[DECISION]** belongs to the user.

## 1. Summary (computed evidence)
- **Authorisation:** the user designated **C3 the sole candidate** (C1 not selected) and authorised Stage 3 under the frozen protocol (`docs/20`). Candidate, critical values, thresholds and methodology were not modified.
- **Run:** 2,280,000 simulations in 96 cells (88 gated, 8 df 3 report-only), run once; failed simulations: baseline 0, C3 0.
- **C3 outcome under the v1.1 classifier (upper limits only):** **PASS_CLEAR** — 88 PASS, 0 PASS_AMBIGUOUS, 0 FAIL, 0 FAIL_AMBIGUOUS of 88 gated cells. Highest C3 rate: tier A 2.98% (limit 5.5%), tier B 5.28% (limit 6.0%); lowest cell 0.59%.
- **Failure conditions triggered for C3:** none.
- **What this means and does not mean:** C3 stayed within its upper limits in every validated cell, **including the 20 cells never used in development**. Because C3 is judged on upper limits only and rejects far below 5% in most cells (median 1.82%), this shows it does not over-reject in the simulated family; **it does not show that C3 holds the rate near 5%**, and it says nothing outside the family (Stage 4) or about power beyond the diagnostic below.
- **Baseline (reference only):** 40 FAIL and 17 FAIL_AMBIGUOUS of 88 gated cells; highest rate 8.72%.
- **D2 (judgement-based):** 320 computable comparisons, 143 flagged (34 for C3); 32 C3 comparisons in the 16 cells with no matched df ∞ reference are **not computable as specified**. All flags and 20 borderline comparisons are preserved below.
- **Power cells:** run (diagnostic only) (section 9).

## 2. Scope and frozen specification [PROTOCOL]
Frozen grid `outputs/milestone4/h1_calibration/frozen_spec/cells_validation.csv` (96 cells, 2,280,000 simulations): the 76 development cells re-run with fresh seeds (master 20261204, rows 0–75) and 20 new intermediate cells (master 20261205, rows 76–95: df 7 tier A and df 5 tier B, shape E at 59/90/180 days, shapes D1.5/D3.0 at 59 days, both markets). Per-simulation seeds `SeedSequence(master, spawn_key=(val_row, i, stream))`. Fill-ins decided before the run (D1.5/D3.0 as τ = 1.5/3.0 exponential profiles, df 7, the 90/180-day C3 training, seeds, power-run condition, D2 handling): **`docs/20`**. Run once, no retuning. C1 and C2 were not run.

## 3. Integrity and reproducibility (recomputed when this report was generated)
| Check | Result |
|---|---|
| Frozen v1 / v1.1 / Stage 1 code manifests | 23 / 7 / 8 files verified |
| Stage 2 inputs / addendum / C3 table manifests | 18 / 2 / 2 files verified |
| **Stage 3 inputs manifest** (`frozen_stage3_inputs.sha256`) | 12 files verified (frozen before any Stage 3 data existed) |
| **90/180-day C3 table** (`stage3/c3_intermediate/C3_INTERMEDIATE_TABLE.sha256`) | 2 files verified (frozen before validation) |
| Validation cell files | 96 files, 2,280,000 rows (plan 2,280,000), simulation ids exact, C3 rule `T > crit` exact, one C3 value per cell; problems: none |
| C3 values used equal the frozen tables | True |
| Validation outputs digest | `c39310c13539afece74f252c…`; summaries digest `433a08e72c905dd9b10b8a51…` |
| Test suite | 333 passed, 3 warnings in 58.42s (python -m pytest -q, run immediately before generation) |
| Environment | Python 3.12.13, numpy 2.5.4, pandas 3.1.0; macOS-15.4.1-arm64-arm-64bit |
**Run history [EVIDENCE].** Compute time 1.03 h (3703.6 s); wall-clock span of the cell files 1.17 h; machine-sleep difference 0.16 h (the run is resumable and seeds do not depend on the clock).

## 4. C3 critical values used [EVIDENCE]
| n_days | c3_crit | source_dev_row | n_cells | source |
|---|---|---|---|---|
| 59 | 3.298658 | 50 | 44 | Stage 2 training (68 cells, seed 20261202) |
| 90 | 2.946701 | 10 | 12 | Stage 3 intermediate training (24 cells, seed 20261209) |
| 125 | 2.880076 | 72 | 12 | Stage 2 training (68 cells, seed 20261202) |
| 180 | 2.854727 | 22 | 12 | Stage 3 intermediate training (24 cells, seed 20261209) |
| 250 | 2.816000 | 73 | 12 | Stage 2 training (68 cells, seed 20261202) |
The 90/180-day values come from 12-cell families (tails G, T6, T4 × E, D5 × NSE, US; 25,000 simulations each, 0 failures). They contain no estimated-dependence, no 0.6-volatility and no flat or R2 shapes, so **C3 provides less scenario coverage at 90, 125, 180 and 250 days than at 59 days and is valid only inside those families.** The maximum over noisy cell quantiles is biased slightly upward (the top cells at each size lie within about 2 standard errors; `c3_intermediate_cell_results.csv`).

## 5. Validation results [EVIDENCE]
Rates are null rejection rates (nominal 5%), judged for C3 on upper limits only. Sources: `stage3/summary/stage3_cell_results.csv`, `stage3_candidate_outcome.csv`. All 96 cells in both columns are in `stage3/report_tables/stage3_all_cells_rates.csv` and appendix A.
| method | group | cells | rate_min_% | rate_median_% | rate_max_% | PASS | PASS_AMBIG | FAIL | FAIL_AMBIG |
|---|---|---|---|---|---|---|---|---|---|
| c3 | A, re-run | 44 | 0.59 | 1.47 | 2.98 | 44 | 0 | 0 | 0 |
| c3 | A, new | 10 | 1.26 | 1.64 | 2.43 | 10 | 0 | 0 | 0 |
| c3 | B, re-run | 24 | 0.97 | 3.40 | 5.28 | 24 | 0 | 0 | 0 |
| c3 | B, new | 10 | 1.69 | 2.51 | 3.56 | 10 | 0 | 0 | 0 |
| baseline | A, re-run | 44 | 4.61 | 5.35 | 6.34 | 18 | 7 | 10 | 9 |
| baseline | A, new | 10 | 5.21 | 5.65 | 6.33 | 1 | 1 | 4 | 4 |
| baseline | B, re-run | 24 | 4.52 | 7.63 | 8.72 | 2 | 1 | 20 | 1 |
| baseline | B, new | 10 | 5.94 | 6.44 | 7.20 | 0 | 1 | 6 | 3 |

**The 20 new intermediate cells** (rates in %, C3 upper Wilson limit in %):
| val_row | cell | tier | baseline | c3 | c3_status | c3_wilson_upper_% |
|---|---|---|---|---|---|---|
| 76 | T7 E NSE 59d | A | 6.02 | 1.59 | PASS | 1.75 |
| 77 | T7 E NSE 90d | A | 5.96 | 2.43 | PASS | 2.63 |
| 78 | T7 E NSE 180d | A | 5.35 | 2.20 | PASS | 2.39 |
| 79 | T7 D1.5 NSE 59d | A | 5.83 | 1.62 | PASS | 1.78 |
| 80 | T7 D3.0 NSE 59d | A | 5.64 | 1.29 | PASS | 1.44 |
| 81 | T7 E US 59d | A | 5.61 | 1.26 | PASS | 1.40 |
| 82 | T7 E US 90d | A | 5.64 | 2.23 | PASS | 2.42 |
| 83 | T7 E US 180d | A | 5.21 | 1.93 | PASS | 2.11 |
| 84 | T7 D1.5 US 59d | A | 6.33 | 1.66 | PASS | 1.82 |
| 85 | T7 D3.0 US 59d | A | 5.66 | 1.34 | PASS | 1.49 |
| 86 | T5 E NSE 59d | B | 6.84 | 2.11 | PASS | 2.30 |
| 87 | T5 E NSE 90d | B | 6.94 | 3.56 | PASS | 3.79 |
| 88 | T5 E NSE 180d | B | 6.35 | 3.22 | PASS | 3.45 |
| 89 | T5 D1.5 NSE 59d | B | 7.12 | 2.44 | PASS | 2.63 |
| 90 | T5 D3.0 NSE 59d | B | 6.52 | 1.93 | PASS | 2.11 |
| 91 | T5 E US 59d | B | 5.94 | 1.69 | PASS | 1.86 |
| 92 | T5 E US 90d | B | 6.24 | 2.82 | PASS | 3.03 |
| 93 | T5 E US 180d | B | 6.03 | 2.95 | PASS | 3.17 |
| 94 | T5 D1.5 US 59d | B | 7.20 | 2.58 | PASS | 2.78 |
| 95 | T5 D3.0 US 59d | B | 6.23 | 1.85 | PASS | 2.02 |
**df 3 report-only cells (8):**
| val_row | cell | baseline | c3 |
|---|---|---|---|
| 32 | T3 flat NSE 59d | 5.43 | 2.18 |
| 33 | T3 flat US 59d | 4.50 | 1.61 |
| 34 | T3 E NSE 59d | 9.16 | 5.20 |
| 35 | T3 E US 59d | 7.54 | 3.58 |
| 36 | T3 D5 NSE 59d | 10.40 | 6.13 |
| 37 | T3 D5 US 59d | 10.51 | 6.24 |
| 38 | T3 R2 NSE 59d | 6.79 | 3.08 |
| 39 | T3 R2 US 59d | 5.63 | 2.34 |
**C3 gated cells that are not a clear PASS** (all kept; 0 cells):
None: every gated cell is a clear PASS for C3.

**Failure conditions (docs/13 §4.7 as applicable to Stage 3, evaluated for C3):**
| condition | cells_violating | triggered |
|---|---|---|
| 1. any tier A cell outside its gate (C3: rate above 5.5%) | 0 | False |
| 2. any tier B cell outside its gate (C3: rate above 6.0%) | 0 | False |
| ceiling: any validated cell above 7.0% | 0 | False |
| numerical: method-cells above 0.1% failures | 0 | False |
| clear FAIL or FAIL_AMBIGUOUS statuses for C3 | 0 | False |

**C3's conservative behaviour [EVIDENCE]:** C3 rates range from 0.59% to 5.28% (tier A median 1.56%, tier B median 3.26%); 49 of 88 gated cells are below 2%. Passing an upper-limit gate this way reflects a rarely-rejecting fixed critical value; it is expected to cost power (section 9).

## 6. Stage 3 against Stage 2 for the re-run cells [EVIDENCE]
Independent seeds, same cells (76 cells). C3: mean Stage 3 − Stage 2 rate +0.010 points, maximum |z| 3.31, 1 cells with |z| above 3 and 5 above 2. Baseline: mean -0.011 points, maximum |z| 3.13, 1 above 3. Cells with |z| above 2 (C3): row 23 (T6 R2 US 59d, 0.93% → 1.14%, z +2.30), row 25 (T4 flat US 59d, 1.18% → 0.97%, z -2.21), row 30 (T4 R2 NSE 59d, 1.74% → 2.14%, z +3.31), row 60 (T6 E NSE 125d, 2.96% → 2.63%, z -2.28), row 70 (T4 E US 125d, 3.53% → 3.88%, z +2.08). Among 76 independent comparisons about 3.5 are expected above 2 and about 0.2 above 3 by chance alone. This is a reproducibility check of the machinery on fresh seeds (the Stage 2 development rates are reproduced), not a validation by itself.

## 7. Conditional calibration and D2 flags (D2, judgement-based) [PROTOCOL + EVIDENCE]
**Formula (same as Stage 2):** flag `<=>` `spread − 1.25 × reference_spread >= 0.02` (fractions; 0.02 = 2 percentage points); reference = same method and variable in the df ∞ cell matched on shape, market and sample size; unmatched dependence/day-volatility cells keep the label "reference not matched on dependence / day-volatility". Stage 2's advancement scope and D4/D7 rules are not applied in Stage 3 (docs/20 fill-in 7).
- **Computable:** 320 comparisons (baseline and C3, all conditioning variables); **flagged: 143** (34 for C3). **Not computable as specified:** the 32 C3 comparisons (and the same for the baseline) in the 16 cells with no df ∞ reference in the frozen grid (90 and 180 days; shapes D1.5 and D3.0). Their spreads are in `stage3_conditional_calibration.csv`, marked "NO MATCHED df-infinity REFERENCE IN THE FROZEN GRID". No substitute reference was invented.
| method | conditioning_variable | flagged | computable |
|---|---|---|---|
| baseline | kurtosis | 1 | 64 |
| baseline | leverage | 55 | 64 |
| baseline | own_critical_value | 53 | 64 |
| c3 | kurtosis | 0 | 64 |
| c3 | leverage | 34 | 64 |
- **Flags for C3 (all preserved)** in `stage3/report_tables/d2_stage3_flagged.csv`; C3 flagged cells: 26 (T4 E NSE 59d, leverage), 27 (T4 E US 59d, leverage), 28 (T4 D5 NSE 59d, leverage), 29 (T4 D5 US 59d, leverage), 30 (T4 R2 NSE 59d, leverage), 32 (T3 flat NSE 59d, leverage), 34 (T3 E NSE 59d, leverage), 35 (T3 E US 59d, leverage), 36 (T3 D5 NSE 59d, leverage), 37 (T3 D5 US 59d, leverage), 38 (T3 R2 NSE 59d, leverage), 39 (T3 R2 US 59d, leverage), 40 (T6 E NSE 59d, est. dependence, leverage), 44 (T4 E NSE 59d, est. dependence, leverage), 45 (T4 E US 59d, est. dependence, leverage), 46 (T4 D5 NSE 59d, est. dependence, leverage), 47 (T4 D5 US 59d, est. dependence, leverage), 48 (T4 E NSE 59d, day-vol 0.6, leverage), 49 (T4 E US 59d, day-vol 0.6, leverage), 50 (T4 D5 NSE 59d, day-vol 0.6, leverage), 51 (T4 D5 US 59d, day-vol 0.6, leverage), 60 (T6 E NSE 125d, leverage), 61 (T6 E NSE 250d, leverage), 64 (T6 D5 NSE 125d, leverage), 67 (T6 D5 US 250d, leverage), 68 (T4 E NSE 125d, leverage), 69 (T4 E NSE 250d, leverage), 70 (T4 E US 125d, leverage), 71 (T4 E US 250d, leverage), 72 (T4 D5 NSE 125d, leverage), 73 (T4 D5 NSE 250d, leverage), 74 (T4 D5 US 125d, leverage), 75 (T4 D5 US 250d, leverage), 86 (T5 E NSE 59d, leverage).
- **Borderline comparisons** (within ±0.005 of the threshold; flagged or not by the exact rule, threshold unchanged): 20 — `d2_stage3_borderline.csv`.
| val_row | cell | method | conditioning_variable | spread | reference_spread | threshold_1.25x_ref | margin_vs_0.02 | d2_flag_judgement_based | d2_label |
|---|---|---|---|---|---|---|---|---|---|
| 31 | T4 R2 US 59d | c3 | leverage | 0.0200 | 0.0038 | 0.0048 | -0.0048 | False |  |
| 63 | T6 E US 250d | c3 | leverage | 0.0286 | 0.0106 | 0.0132 | -0.0046 | False |  |
| 24 | T4 flat NSE 59d | c3 | leverage | 0.0186 | 0.0022 | 0.0028 | -0.0042 | False |  |
| 12 | T10 D5 NSE 59d | baseline | own_critical_value | 0.0926 | 0.0614 | 0.0768 | -0.0042 | False |  |
| 43 | T6 D5 US 59d, est. dependence | c3 | leverage | 0.0269 | 0.0086 | 0.0108 | -0.0039 | False | reference not matched on dependence / day-volatility |
| 42 | T6 D5 NSE 59d, est. dependence | c3 | leverage | 0.0282 | 0.0096 | 0.0120 | -0.0038 | False | reference not matched on dependence / day-volatility |
| 33 | T3 flat US 59d | c3 | leverage | 0.0192 | 0.0024 | 0.0030 | -0.0038 | False |  |
| 81 | T7 E US 59d | baseline | own_critical_value | 0.0883 | 0.0576 | 0.0720 | -0.0037 | False |  |
| 13 | T10 D5 US 59d | baseline | leverage | 0.0848 | 0.0544 | 0.0680 | -0.0032 | False |  |
| 15 | T10 R2 US 59d | baseline | leverage | 0.0560 | 0.0309 | 0.0386 | -0.0026 | False |  |
| 76 | T7 E NSE 59d | c3 | leverage | 0.0339 | 0.0130 | 0.0162 | -0.0023 | False |  |
| 16 | T6 flat NSE 59d | baseline | leverage | 0.0597 | 0.0328 | 0.0410 | -0.0013 | False |  |
| 66 | T6 D5 US 125d | c3 | leverage | 0.0379 | 0.0154 | 0.0192 | -0.0013 | False |  |
| 67 | T6 D5 US 250d | c3 | leverage | 0.0304 | 0.0083 | 0.0104 | -0.0000 | True |  |
| 27 | T4 E US 59d | c3 | leverage | 0.0331 | 0.0101 | 0.0126 | +0.0005 | True |  |
| 40 | T6 E NSE 59d, est. dependence | c3 | leverage | 0.0371 | 0.0130 | 0.0162 | +0.0009 | True | reference not matched on dependence / day-volatility |
| 64 | T6 D5 NSE 125d | c3 | leverage | 0.0347 | 0.0106 | 0.0132 | +0.0015 | True |  |
| 81 | T7 E US 59d | baseline | leverage | 0.0882 | 0.0522 | 0.0652 | +0.0030 | True |  |
| 86 | T5 E NSE 59d | c3 | leverage | 0.0403 | 0.0130 | 0.0162 | +0.0041 | True |  |
| 49 | T4 E US 59d, day-vol 0.6 | c3 | leverage | 0.0371 | 0.0101 | 0.0126 | +0.0045 | True | reference not matched on dependence / day-volatility |
- **[HYPOTHESIS]** A fixed critical value rejects more when leverage is high, so C3's leverage flags may be built in; no evidence beyond the pattern.

## 8. Reading of the result [EVIDENCE vs HYPOTHESIS vs DECISION]
- **[EVIDENCE]** C3's outcome is PASS_CLEAR; no failure condition applicable to Stage 3 was triggered unless listed above; the 20 new cells and the fresh-seed re-run behave as the development stage predicted (section 6).
- **[HYPOTHESIS]** The result is a property of a conservative fixed critical value anchored to the worst development cells; it would not by itself show that the H1 test is calibrated.
- **[DECISION]** Whether Stage 4 (alternative processes, bar-level check, second implementation) is to be run, and the Stage 5 decision report, belong to the user.

## 9. Power cells — diagnostic only
Six cells (T4 flat ×1.1 and ×1.2, T4 E ×1.2; both markets; 59 days), 5,000 simulations each, new seed 20261213, baseline and C3 on the same data, run only because the C3 outcome was PASS_CLEAR (docs/20 fill-in 6). Power (%) [Wilson 95%]:
| power_cell | shape | mult | market | base | c3 |
|---|---|---|---|---|---|
| 0 | flat | 1.1 | NSE | 29.9 [28.6, 31.2] | 12.3 [11.5, 13.3] |
| 1 | flat | 1.1 | US | 40.7 [39.3, 42.1] | 19.2 [18.2, 20.4] |
| 2 | flat | 1.2 | NSE | 86.1 [85.1, 87.0] | 81.8 [80.7, 82.9] |
| 3 | flat | 1.2 | US | 89.7 [88.8, 90.5] | 89.3 [88.4, 90.1] |
| 4 | E | 1.2 | NSE | 64.6 [63.3, 65.9] | 54.2 [52.8, 55.6] |
| 5 | E | 1.2 | US | 71.5 [70.2, 72.7] | 62.0 [60.7, 63.4] |

| power_cell | shape | mult | market | power_method | power_baseline | ratio_to_baseline | flag_cell | power_collapse_flag |
|---|---|---|---|---|---|---|---|---|
| 0 | flat | 1.1 | NSE | 0.1234 | 0.2990 | 0.4127 | False | False |
| 1 | flat | 1.1 | US | 0.1924 | 0.4070 | 0.4727 | False | False |
| 2 | flat | 1.2 | NSE | 0.8184 | 0.8608 | 0.9507 | True | False |
| 3 | flat | 1.2 | US | 0.8930 | 0.8972 | 0.9953 | True | False |
| 4 | E | 1.2 | NSE | 0.5420 | 0.6462 | 0.8387 | False | False |
| 5 | E | 1.2 | US | 0.6202 | 0.7146 | 0.8679 | False | False |

The single flag (C3 power below 70% of the baseline's at T4 flat ×1.2) was **not raised**. The power is not size-adjusted, the baseline over-rejects in the E cells (ratios there are not a fair yardstick), and this check is diagnostic only: it plays no part in any selection.

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
| val_row | cell | tier | baseline | c3 | c3_status |
|---|---|---|---|---|---|
| 0 | G flat NSE 59d | A | 4.91 | 0.62 | PASS |
| 1 | G flat US 59d | A | 4.98 | 0.62 | PASS |
| 2 | G E NSE 59d | A | 5.20 | 0.83 | PASS |
| 3 | G E US 59d | A | 5.03 | 0.84 | PASS |
| 4 | G D5 NSE 59d | A | 5.26 | 0.87 | PASS |
| 5 | G D5 US 59d | A | 5.11 | 0.84 | PASS |
| 6 | G R2 NSE 59d | A | 4.77 | 0.70 | PASS |
| 7 | G R2 US 59d | A | 4.61 | 0.60 | PASS |
| 8 | T10 flat NSE 59d | A | 4.82 | 0.75 | PASS |
| 9 | T10 flat US 59d | A | 4.63 | 0.59 | PASS |
| 10 | T10 E NSE 59d | A | 5.54 | 1.22 | PASS |
| 11 | T10 E US 59d | A | 5.49 | 1.02 | PASS |
| 12 | T10 D5 NSE 59d | A | 5.66 | 1.23 | PASS |
| 13 | T10 D5 US 59d | A | 5.59 | 1.42 | PASS |
| 14 | T10 R2 NSE 59d | A | 4.92 | 0.75 | PASS |
| 15 | T10 R2 US 59d | A | 5.10 | 0.84 | PASS |
| 16 | T6 flat NSE 59d | A | 4.90 | 0.77 | PASS |
| 17 | T6 flat US 59d | A | 4.81 | 0.70 | PASS |
| 18 | T6 E NSE 59d | A | 6.20 | 1.74 | PASS |
| 19 | T6 E US 59d | A | 6.02 | 1.48 | PASS |
| 20 | T6 D5 NSE 59d | A | 6.06 | 1.82 | PASS |
| 21 | T6 D5 US 59d | A | 6.29 | 1.82 | PASS |
| 22 | T6 R2 NSE 59d | A | 5.62 | 1.12 | PASS |
| 23 | T6 R2 US 59d | A | 5.33 | 1.14 | PASS |
| 24 | T4 flat NSE 59d | B | 5.43 | 1.37 | PASS |
| 25 | T4 flat US 59d | B | 4.52 | 0.97 | PASS |
| 26 | T4 E NSE 59d | B | 7.93 | 3.08 | PASS |
| 27 | T4 E US 59d | B | 6.80 | 2.38 | PASS |
| 28 | T4 D5 NSE 59d | B | 8.15 | 3.24 | PASS |
| 29 | T4 D5 US 59d | B | 8.06 | 3.40 | PASS |
| 30 | T4 R2 NSE 59d | B | 6.52 | 2.14 | PASS |
| 31 | T4 R2 US 59d | B | 5.79 | 1.51 | PASS |
| 32 | T3 flat NSE 59d | C | 5.43 | 2.18 | REPORT_ONLY |
| 33 | T3 flat US 59d | C | 4.50 | 1.61 | REPORT_ONLY |
| 34 | T3 E NSE 59d | C | 9.16 | 5.20 | REPORT_ONLY |
| 35 | T3 E US 59d | C | 7.54 | 3.58 | REPORT_ONLY |
| 36 | T3 D5 NSE 59d | C | 10.40 | 6.13 | REPORT_ONLY |
| 37 | T3 D5 US 59d | C | 10.51 | 6.24 | REPORT_ONLY |
| 38 | T3 R2 NSE 59d | C | 6.79 | 3.08 | REPORT_ONLY |
| 39 | T3 R2 US 59d | C | 5.63 | 2.34 | REPORT_ONLY |
| 40 | T6 E NSE 59d, est. dependence | A | 6.22 | 1.77 | PASS |
| 41 | T6 E US 59d, est. dependence | A | 5.66 | 1.26 | PASS |
| 42 | T6 D5 NSE 59d, est. dependence | A | 6.18 | 1.96 | PASS |
| 43 | T6 D5 US 59d, est. dependence | A | 6.34 | 1.77 | PASS |
| 44 | T4 E NSE 59d, est. dependence | B | 7.76 | 3.29 | PASS |
| 45 | T4 E US 59d, est. dependence | B | 7.01 | 2.40 | PASS |
| 46 | T4 D5 NSE 59d, est. dependence | B | 8.03 | 3.33 | PASS |
| 47 | T4 D5 US 59d, est. dependence | B | 7.92 | 3.33 | PASS |
| 48 | T4 E NSE 59d, day-vol 0.6 | B | 8.10 | 4.45 | PASS |
| 49 | T4 E US 59d, day-vol 0.6 | B | 6.49 | 3.41 | PASS |
| 50 | T4 D5 NSE 59d, day-vol 0.6 | B | 8.72 | 4.87 | PASS |
| 51 | T4 D5 US 59d, day-vol 0.6 | B | 8.42 | 4.93 | PASS |
| 52 | G E NSE 125d | A | 5.20 | 1.54 | PASS |
| 53 | G E NSE 250d | A | 5.09 | 1.47 | PASS |
| 54 | G E US 125d | A | 5.08 | 1.60 | PASS |
| 55 | G E US 250d | A | 5.03 | 1.60 | PASS |
| 56 | G D5 NSE 125d | A | 4.94 | 1.71 | PASS |
| 57 | G D5 NSE 250d | A | 5.38 | 1.75 | PASS |
| 58 | G D5 US 125d | A | 4.92 | 1.65 | PASS |
| 59 | G D5 US 250d | A | 5.09 | 1.61 | PASS |
| 60 | T6 E NSE 125d | A | 5.95 | 2.63 | PASS |
| 61 | T6 E NSE 250d | A | 5.60 | 2.48 | PASS |
| 62 | T6 E US 125d | A | 5.60 | 2.30 | PASS |
| 63 | T6 E US 250d | A | 5.41 | 2.27 | PASS |
| 64 | T6 D5 NSE 125d | A | 6.04 | 2.94 | PASS |
| 65 | T6 D5 NSE 250d | A | 5.78 | 2.75 | PASS |
| 66 | T6 D5 US 125d | A | 5.83 | 2.98 | PASS |
| 67 | T6 D5 US 250d | A | 5.62 | 2.59 | PASS |
| 68 | T4 E NSE 125d | B | 7.80 | 4.92 | PASS |
| 69 | T4 E NSE 250d | B | 7.12 | 4.44 | PASS |
| 70 | T4 E US 125d | B | 6.72 | 3.88 | PASS |
| 71 | T4 E US 250d | B | 6.26 | 3.63 | PASS |
| 72 | T4 D5 NSE 125d | B | 7.85 | 5.27 | PASS |
| 73 | T4 D5 NSE 250d | B | 7.55 | 4.96 | PASS |
| 74 | T4 D5 US 125d | B | 7.71 | 5.28 | PASS |
| 75 | T4 D5 US 250d | B | 6.96 | 4.52 | PASS |
| 76 | T7 E NSE 59d | A | 6.02 | 1.59 | PASS |
| 77 | T7 E NSE 90d | A | 5.96 | 2.43 | PASS |
| 78 | T7 E NSE 180d | A | 5.35 | 2.20 | PASS |
| 79 | T7 D1.5 NSE 59d | A | 5.83 | 1.62 | PASS |
| 80 | T7 D3.0 NSE 59d | A | 5.64 | 1.29 | PASS |
| 81 | T7 E US 59d | A | 5.61 | 1.26 | PASS |
| 82 | T7 E US 90d | A | 5.64 | 2.23 | PASS |
| 83 | T7 E US 180d | A | 5.21 | 1.93 | PASS |
| 84 | T7 D1.5 US 59d | A | 6.33 | 1.66 | PASS |
| 85 | T7 D3.0 US 59d | A | 5.66 | 1.34 | PASS |
| 86 | T5 E NSE 59d | B | 6.84 | 2.11 | PASS |
| 87 | T5 E NSE 90d | B | 6.94 | 3.56 | PASS |
| 88 | T5 E NSE 180d | B | 6.35 | 3.22 | PASS |
| 89 | T5 D1.5 NSE 59d | B | 7.12 | 2.44 | PASS |
| 90 | T5 D3.0 NSE 59d | B | 6.52 | 1.93 | PASS |
| 91 | T5 E US 59d | B | 5.94 | 1.69 | PASS |
| 92 | T5 E US 90d | B | 6.24 | 2.82 | PASS |
| 93 | T5 E US 180d | B | 6.03 | 2.95 | PASS |
| 94 | T5 D1.5 US 59d | B | 7.20 | 2.58 | PASS |
| 95 | T5 D3.0 US 59d | B | 6.23 | 1.85 | PASS |

## Appendix B. Files
`outputs/milestone4/h1_calibration/stage3/` — `c3_intermediate/`, `validation/` (96 cell files, run metadata), `summary/` (5 CSVs), `power_check/` (if run), `report_tables/`; plan `stage3_plan/`; manifest `frozen_stage3_inputs.sha256`; logs `stage3_*_run.log`; scripts `scripts/milestone4/stage3_*.py`; record `docs/20`.
