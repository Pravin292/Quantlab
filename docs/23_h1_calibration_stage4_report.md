# 23 — H1 calibration, Stage 4 report (independent validation of C3)

**Status:** Stage 4 executed once under the preregistration (`docs/22`, `docs/22b`, frozen in `frozen_stage4_inputs.sha256` before any Stage 4 simulation). **This report states what the pre-specified criteria give. It does not make the Stage 5 decision.** Generated 2026-11-08 00:06 by `scripts/milestone4/stage4_make_report.py` from saved files only. **All data are simulated; nothing here is real-market evidence.**
**Labels:** **[EVIDENCE]** computed from the saved files; **[PROTOCOL]** pre-specified; **[HYPOTHESIS]** my reading; **[DECISION]** belongs to the user.

## 1. Exact status
**Stage 4 is COMPLETE: all five preregistered acceptance criteria are met.**
| criterion | result |
|---|---|
| A. null check: all 16 ratios (a, b, e, f) within 0.5%; all 12 truncated moments (c, d) within 0.5%; analytic factors = 1 | MET |
| B. alternative processes: C3 rate at most 6.0% in all 12 cells (v1.1 A2); no numerical failures above 0.1% | MET |
| C1. bar-level: no |z| > 3 in the 16 comparisons (C3 and baseline, 8 cells x 8,000 vs Stage 3 fast route) | MET |
| C2. same-returns matrices (80): identical shape and max relative difference <= 1e-9 | MET |
| D. reference implementation: T within 1e-9 in 100 datasets, identical C3 decisions, five C3 values re-derived to 1e-12 | MET |
No acceptance criterion, tolerance or gate was changed after freezing. Real-data descriptive analysis (optional, unauthorised) was not run. Stage 5 was not started.

## 2. Frozen specification and preregistration [PROTOCOL]
Frozen v1 / v1.1 (`docs/13` §4, `docs/15a` §4, `frozen_spec/cells_alternative_dgps.csv`, `frozen_spec_v1_1/alt_dgp_parameters.json`, seeds 20261206, 20261207, 20261208); preregistration `docs/22` with the user's approvals in `docs/22b` (D1–D6, bar-level size 8,000 per cell). Candidate: C3 with its frozen critical values, unchanged; the M4b baseline bootstrap-t (B = 999) is reference only; C1 and C2 not run.

## 3. Validation methods (summary)
(A) null check of the alternative processes before use; (B) 12 alternative-process cells × 25,000 simulations; (C) bar-level pipeline check: 8 cells × 8,000 new bar-level simulations compared with the Stage 3 fast-route data by pooled two-proportion z-tests, plus 80 same-returns matrices; (D) a second, independent exact-arithmetic implementation compared on 100 datasets. Details and tolerances: `docs/22`.

## 4. Null check (A) [EVIDENCE]
Processes a, b, e, f: ratios open/middle and close/middle of period mean squares, 5×10⁷ bars in the open period, literal tolerance 0.5% (the standard error is shown; deviations in standard-error units):
| process | market | days | bars_open | dev_open_% | dev_close_% | se_open | se_close | dev_open_in_SE | dev_close_in_SE | pass_open | pass_close |
|---|---|---|---|---|---|---|---|---|---|---|---|
| a_intraday_volatility_clustering | NSE | 2083334 | 50000016 | -0.0133 | -0.0622 | 0.00055 | 0.00115 | -0.24 | -0.54 | True | True |
| a_intraday_volatility_clustering | US | 1515152 | 50000016 | -0.0841 | +0.1119 | 0.00071 | 0.00090 | -1.19 | +1.25 | True | True |
| b_jumps | NSE | 2083334 | 50000016 | -0.0266 | +0.0325 | 0.00045 | 0.00098 | -0.60 | +0.33 | True | True |
| b_jumps | US | 1515152 | 50000016 | +0.0143 | +0.0058 | 0.00062 | 0.00076 | +0.23 | +0.08 | True | True |
| e_heavy_tailed_day_factor | NSE | 2083334 | 50000016 | -0.0180 | +0.1433 | 0.00055 | 0.00143 | -0.33 | +1.00 | True | True |
| e_heavy_tailed_day_factor | US | 1515152 | 50000016 | +0.0129 | +0.0281 | 0.00071 | 0.00096 | +0.18 | +0.29 | True | True |
| f_laplace_shocks | NSE | 2083334 | 50000016 | -0.0358 | +0.0038 | 0.00055 | 0.00077 | -0.65 | +0.05 | True | True |
| f_laplace_shocks | US | 1515152 | 50000016 | -0.1537 | +0.0233 | 0.00056 | 0.00077 | -2.74 | +0.30 | True | True |
**Largest deviation 0.1537%** (tolerance 0.5%); the largest in standard-error units is 2.74, which among 16 ratios is not unusual by chance. Processes c and d: truncated second moment E[ε²·1{|ε|≤c}] against its exact value (c = 99.9% two-sided quantile), at least 10⁷ bars per component:
| process | market | component | df | cutoff | bars | rel_dev | se_rel | tail_variance_share_beyond_cutoff | pass |
|---|---|---|---|---|---|---|---|---|---|
| c_period_specific_tails | NSE | open | 4 | 6.088 | 10000008 | +0.00052 | 0.00092 | 0.076 | True |
| c_period_specific_tails | NSE | middle | 8 | 4.366 | 67500054 | +0.00002 | 0.00019 | 0.027 | True |
| c_period_specific_tails | NSE | close | 4 | 6.088 | 11250009 | +0.00077 | 0.00064 | 0.076 | True |
| c_period_specific_tails | US | open | 4 | 6.088 | 10000023 | +0.00030 | 0.00099 | 0.076 | True |
| c_period_specific_tails | US | middle | 8 | 4.366 | 49091022 | -0.00007 | 0.00024 | 0.027 | True |
| c_period_specific_tails | US | close | 4 | 6.088 | 10909116 | -0.00073 | 0.00071 | 0.076 | True |
| d_stock_specific_tails | NSE | stock 1 | 3 | 7.462 | 10000066 | +0.00020 | 0.00151 | 0.169 | True |
| d_stock_specific_tails | NSE | stock 2 | 5 | 5.321 | 10000066 | -0.00085 | 0.00159 | 0.049 | True |
| d_stock_specific_tails | NSE | stock 3 | 8 | 4.366 | 10000066 | -0.00029 | 0.00132 | 0.027 | True |
| d_stock_specific_tails | US | stock 1 | 3 | 7.462 | 10000067 | -0.00054 | 0.00080 | 0.169 | True |
| d_stock_specific_tails | US | stock 2 | 5 | 5.321 | 10000067 | -0.00027 | 0.00094 | 0.049 | True |
| d_stock_specific_tails | US | stock 3 | 8 | 4.366 | 10000067 | +0.00018 | 0.00038 | 0.027 | True |
Analytic checks: the exact second moment of the shock part equals 1 for a, b, e, f (maximum error 2.2e-16); unit-variance scale constants are tested for c and d. **Limitation of the c/d check [PROTOCOL]:** the variance beyond the 99.9% cutoff (2.7% to 16.9% of the total) cannot be verified by Monte Carlo at 0.5% (infinite fourth moment); it rests on the exact analytic scale constants and the tail-probability unit tests. **What the check can and cannot catch:** period-specific variance errors (for example a 5% open/middle error would be about 49 standard errors); not a factor common to all periods, which does not break H0 and is verified analytically.

## 5. Alternative-process validation (B) [EVIDENCE]
12 cells × 25,000 simulations (300,000), C3 unchanged (critical value 3.298658), seeds `SeedSequence(20261206, spawn_key=(cell_row, i, stream))`. Gate: C3 passes a cell when its rate is at most 6.0% (v1.1 A2); the baseline's two-sided band 4.0–6.0% is information only. Failed simulations in total: 0.
| cell_row | process | market | n_valid | n_failed | rate_% | wilson_low_% | wilson_high_% | status | c3_gate_rate_le_6.0% |
|---|---|---|---|---|---|---|---|---|---|
| 0 | a_intraday_volatility_clustering | NSE | 25000 | 0 | 1.98 | 1.81 | 2.16 | PASS | True |
| 1 | a_intraday_volatility_clustering | US | 25000 | 0 | 1.63 | 1.48 | 1.80 | PASS | True |
| 2 | b_jumps | NSE | 25000 | 0 | 2.37 | 2.19 | 2.56 | PASS | True |
| 3 | b_jumps | US | 25000 | 0 | 1.96 | 1.80 | 2.14 | PASS | True |
| 4 | c_period_specific_tails | NSE | 25000 | 0 | 4.41 | 4.16 | 4.67 | PASS | True |
| 5 | c_period_specific_tails | US | 25000 | 0 | 3.70 | 3.47 | 3.94 | PASS | True |
| 6 | d_stock_specific_tails | NSE | 25000 | 0 | 2.78 | 2.58 | 2.99 | PASS | True |
| 7 | d_stock_specific_tails | US | 25000 | 0 | 2.02 | 1.85 | 2.20 | PASS | True |
| 8 | e_heavy_tailed_day_factor | NSE | 25000 | 0 | 1.44 | 1.30 | 1.59 | PASS | True |
| 9 | e_heavy_tailed_day_factor | US | 25000 | 0 | 1.23 | 1.10 | 1.37 | PASS | True |
| 10 | f_laplace_shocks | NSE | 25000 | 0 | 1.65 | 1.50 | 1.82 | PASS | True |
| 11 | f_laplace_shocks | US | 25000 | 0 | 1.34 | 1.21 | 1.49 | PASS | True |
- **C3: highest rate 4.41%, lowest 1.23%, median 1.97%; candidate outcome PASS_CLEAR; ambiguous cells (6.0% inside the Wilson interval): 0.** C3 is conservative: it rejects far below 5% in most cells.
Baseline (reference only, two-sided band 4.0–6.0%):
| cell_row | process | market | rate_% | wilson_low_% | wilson_high_% | status |
|---|---|---|---|---|---|---|
| 0 | a_intraday_volatility_clustering | NSE | 6.69 | 6.38 | 7.00 | FAIL |
| 1 | a_intraday_volatility_clustering | US | 6.11 | 5.82 | 6.41 | FAIL_AMBIGUOUS |
| 2 | b_jumps | NSE | 7.26 | 6.94 | 7.59 | FAIL |
| 3 | b_jumps | US | 6.37 | 6.08 | 6.68 | FAIL |
| 4 | c_period_specific_tails | NSE | 9.45 | 9.10 | 9.82 | FAIL |
| 5 | c_period_specific_tails | US | 8.61 | 8.27 | 8.96 | FAIL |
| 6 | d_stock_specific_tails | NSE | 7.52 | 7.20 | 7.85 | FAIL |
| 7 | d_stock_specific_tails | US | 6.18 | 5.88 | 6.48 | FAIL_AMBIGUOUS |
| 8 | e_heavy_tailed_day_factor | NSE | 5.04 | 4.78 | 5.32 | PASS |
| 9 | e_heavy_tailed_day_factor | US | 5.09 | 4.82 | 5.37 | PASS |
| 10 | f_laplace_shocks | NSE | 6.16 | 5.86 | 6.46 | FAIL_AMBIGUOUS |
| 11 | f_laplace_shocks | US | 5.58 | 5.31 | 5.88 | PASS |
Descriptive conditional spreads (quartile range of the rejection rate, points; no df ∞ reference exists for these processes, so D2 is **not computable** and no substitute was invented) are in `stage4/report_tables/alt_conditional_spreads.csv`: C3 leverage spread median 3.29 points, maximum 7.89.

## 6. Bar-level pipeline check (C) [EVIDENCE]
New bar-level simulations (real `simulate_table` → `clean` → bar table route): 8 cells × 8,000 = 64,000 (seeds 20261207, streams 0 and 2), against the Stage 3 fast-route data of the same cells (25,000 each). Pooled two-sided two-proportion z-tests, **all 16 comparisons** (threshold |z| ≤ 3; preregistered family-wise false-flag rate 4.2%; |z| above 2 expected in about half of equivalent runs). Days used in every bar-level matrix: 59–59 (expected 59); invalid bar-level simulations: 0.
| cell | method | bar_level_rate_% | fast_rate_% | difference_points | diff_95%_low | diff_95%_high | z | p_two_sided |
|---|---|---|---|---|---|---|---|---|
| G E NSE | C3 | 0.85 | 0.83 | +0.02 | -0.21 | +0.25 | +0.15 | 0.8777 |
| G E NSE | baseline | 5.44 | 5.20 | +0.23 | -0.33 | +0.80 | +0.81 | 0.4155 |
| G E US | C3 | 0.82 | 0.84 | -0.01 | -0.24 | +0.22 | -0.09 | 0.9249 |
| G E US | baseline | 4.51 | 5.03 | -0.52 | -1.04 | +0.01 | -1.86 | 0.0631 |
| G D5 NSE | C3 | 0.97 | 0.87 | +0.10 | -0.14 | +0.35 | +0.85 | 0.3951 |
| G D5 NSE | baseline | 4.97 | 5.26 | -0.28 | -0.83 | +0.27 | -0.99 | 0.3240 |
| G D5 US | C3 | 0.89 | 0.84 | +0.04 | -0.19 | +0.28 | +0.37 | 0.7129 |
| G D5 US | baseline | 5.49 | 5.11 | +0.38 | -0.19 | +0.94 | +1.32 | 0.1881 |
| T4 E NSE | C3 | 3.35 | 3.08 | +0.27 | -0.18 | +0.72 | +1.20 | 0.2285 |
| T4 E NSE | baseline | 8.22 | 7.93 | +0.30 | -0.39 | +0.99 | +0.85 | 0.3941 |
| T4 E US | C3 | 2.42 | 2.38 | +0.05 | -0.34 | +0.44 | +0.25 | 0.8027 |
| T4 E US | baseline | 6.76 | 6.80 | -0.04 | -0.67 | +0.60 | -0.12 | 0.9076 |
| T4 D5 NSE | C3 | 3.06 | 3.24 | -0.17 | -0.61 | +0.26 | -0.77 | 0.4424 |
| T4 D5 NSE | baseline | 7.56 | 8.15 | -0.59 | -1.26 | +0.08 | -1.69 | 0.0909 |
| T4 D5 US | C3 | 3.34 | 3.40 | -0.06 | -0.51 | +0.39 | -0.25 | 0.8011 |
| T4 D5 US | baseline | 7.97 | 8.06 | -0.09 | -0.77 | +0.60 | -0.24 | 0.8077 |
- **Largest |z| 1.86; comparisons with |z| above 3: 0; between 2 and 3 (reported, expected by chance): 0.** Mean difference (bar-level minus fast): C3 +0.030 points, baseline -0.075 points. Power of this design: 75% at a 1-point difference, 100% at 2 points (docs/22 §5); smaller differences can exist undetected.
**Same-returns matrix check:** 80 matrices, identical shape in 80, maximum relative difference 3.59e-13 (tolerance 1e-9; M4b: 4.02e-13).

## 7. Second independent implementation (D) [EVIDENCE]
100 datasets (10 cells chosen before any result: val rows 3, 9, 11, 14, 34, 43, 45, 50, 60, 77; seed 20261208). Vectorised `max_abs_t` against the independent exact-arithmetic implementation (`h1_stage4_reference.py`, standard library only, period slots derived from clock times): **maximum relative difference 4.77e-14** (tolerance 1e-9); **C3 decisions identical in 100 of 100**; rejections among the 100: 2; datasets within 1e-6 relative of the critical value: 0.
The five frozen C3 values re-derived from the saved training statistics by the independent quantile routine (tolerance 1e-12):
| n_days | source | cells | frozen | rederived | rel_diff |
|---|---|---|---|---|---|
| 59 | Stage 2 training | 44 | 3.298658000461 | 3.298658000461 | 0.00e+00 |
| 125 | Stage 2 training | 12 | 2.880075520719 | 2.880075520719 | 0.00e+00 |
| 250 | Stage 2 training | 12 | 2.816000131597 | 2.816000131597 | 0.00e+00 |
| 90 | Stage 3 intermediate training | 12 | 2.946700601648 | 2.946700601648 | 0.00e+00 |
| 180 | Stage 3 intermediate training | 12 | 2.854727201140 | 2.854727201140 | 1.56e-16 |
**Limit:** same author for both implementations and a shared dataset generator: independence of computation, not of authorship.

## 8. Acceptance criteria and statistical results
See section 1. Statistical summary: the alternative processes did not push C3 above 6.0% (highest 4.41%); the baseline, for reference, ranged 5.04–9.45% (9 of 12 cells outside its two-sided band); the fast generator and the real bar-level route agree within the preregistered criterion; the independent implementation agrees to rounding.

## 9. Failures, limitations and borderline findings
- Borderline: the largest null-check deviation in standard-error units (2.74) and 0 bar-level comparison(s) with |z| between 2 and 3 (see section 6); 0 C3 alternative cells with the 6.0% limit inside the Wilson interval.
- The null check cannot verify the full variance of processes c and d (section 4). The bar-level check cannot detect differences below about 1 point. The reference check is independent in code, not in authorship.
- **What Stage 4 does NOT establish:** validity on real market data; validity for other processes or dependence/volatility regimes; that C3's rate is near 5% (it is conservative and judged on an upper limit); any power or trading statement. No real-data analysis was run.
- Unit tests are implementation checks, not statistical validation.

## 10. Reproducibility
Seeds: 20261206 (alternative processes; null-check namespace first key ≥ 100), 20261207 (bar level; streams 0, 1, 2), 20261208 (reference). Environment: Python 3.12.13, numpy 2.5.4, pandas 3.1.0; macOS-15.4.1-arm64-arm-64bit. Compute times (s): null check 46, alternative processes 235, bar-level simulations 4,406, reference 3. Commands: `scripts/milestone4/stage4_run_null_check.py`, `stage4_run_alt_validation.py`, `stage4_run_bar_level.py --part sims` and `--part matrix`, `stage4_run_reference.py`, then `stage4_make_report.py`.

## 11. Tests, manifests and digests
- Test suite: 355 passed, 3 warnings in 83.55s
- Manifests verified now: v1 23, v1.1 7, Stage 1 code 8, Stage 2 inputs 18, addendum 2, Stage 2 C3 table 2, Stage 3 inputs 12, 90/180-day table 2, **Stage 4 inputs 21** (frozen before any Stage 4 simulation).
- Output digests (SHA-256 over file names and hashes): null check `7d570f8feb29e3051fa7e956…`, alternative processes `77cd77c2f14253cf2bca324b…`, bar level `d2d753cd1d35e37740550e2f…`, reference `44394a0cf433ecaea1a2f817…`.

## 12. Deviations
**No frozen specification, seed, threshold, critical value or manifest was changed.** The additions and fill-ins (null-check sample size and truncated-moment form for c/d, seed namespaces, bar-level cells and 8,000 simulations per cell, |z| ≤ 3 rule, reference cells and tolerances, the 6.0% reading of C3's gate) were fixed in docs/22 and docs/22b before the run. The one change made after the first draft of docs/22 was the bar-level size (2,000 → 8,000), recorded in docs/22b. **No deviation occurred during execution.**

## 13. Is Stage 5 eligible for consideration?
**Yes, on the preregistered criteria:** every Stage 4 criterion is met, so the Stage 5 decision report may be considered. Stage 5 is **not authorised and not started**; it needs your explicit approval and your review of Stages 3–4 (docs/13 review gate). Stage 5 would decide the wording of the conclusion (calibrated within a validated domain, partial, or unresolved); this report makes no such statement.

## 14. Decisions that remain with you
Authorise Stage 5 or not; whether to run the optional real-data descriptive check (separately authorised); how to treat the conservatism of C3 in the Stage 5 wording; whether to commit and push the Stage 2–4 work; the other open items in `docs/19`.
