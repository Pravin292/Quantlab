# M4b — H1 Inference Investigation and H2 Power Validation (final audit report)

**Status of this document:** diagnostic report. `docs/07_research_protocol.md` **does not exist**; docs 09, 10, 11 and this document are diagnostic reports, **not a frozen protocol**. No protocol was frozen or approved in M4b.

**Everything below is computed on SIMULATED data.** No real-market H1/H2/H3 test was run. Planted effects are known effects placed in synthetic data; they are not market relationships. Nothing here says anything about profitability or causality.

**How to read the labels**

- **[VERIFIED]** = recomputed from the saved simulation-level outputs, logs or the test run in this audit.
- **[INTERPRETATION]** = my reading of the verified numbers; it could change with more simulations or other assumptions.
- **[ESTIMATE]** = a number whose precision is limited (stated in the text).

Rejection rates are percentages; the nominal level is 5%. With 5,000 simulations the Monte-Carlo standard error at 5% is about 0.3 points (95% interval roughly ±0.6); with 10,000 it is about 0.2 points; with 120 simulations (H2) it is about 2 points for a 5% rate and up to 4.6 points for a rate near 50%.

---

## 1. Executive summary

1. **[VERIFIED] Execution is complete and clean.** Every queued job finished (`COMPLETE` in every log). 814,880 H1 and H2 simulation rows are saved; planned and actual counts match in all six files. No seed repeats inside any file. 28 seed values appear in two different files (always in different scenarios, so none is a repeated simulation; section 13).
2. **[VERIFIED] No H1 method is calibrated across the stress scenarios.** Under Gaussian or flat-shape worlds the log-ratio bootstrap-t (`rom_t`, and the jackknife version `rom_jack`) rejects close to 5%. With heavy tails (Student-t, 4 degrees of freedom) combined with strongly different within-period variance shapes (E, D5) it rejects 7–9% at 59 days, and still 6–9% at 125 and 250 days. The alternatives tried (diff-based bootstrap-t, wild bootstrap, empirical likelihood) are equal or worse. **H1 inference remains unresolved.**
3. **[VERIFIED] The cause is located in the critical value, not the estimator.** If the critical value is replaced by the oracle value (the simulated 95% quantile of the statistic), rejection returns to 5.0% in every cell. [INTERPRETATION] So the bootstrap critical value is too small when tails are heavy and variance shapes are uneven.
4. **[VERIFIED] The numerical failure audit found nothing:** 0 empirical-likelihood hull exits, 0 solver failures, 0 jackknife or wild-bootstrap failures, 0 non-finite statistics, 0 invalid intervals, 0 discarded replications, in 148,000 audited simulations, and 17,400 of 17,400 re-runs reproduced exactly.
5. **[VERIFIED] The fast simulator matches the bar-level pipeline exactly when fed the same returns** (160 of 160 matrices, largest relative difference 4.02e-13). Rejection rates agree statistically in 45 of 48 cells; the three exceptions are one NSE cell (section 11).
6. **[VERIFIED] H2 (the wild-cluster-bootstrap test of model M5) behaves like a calibrated test in the simulated worlds tested:** true-null rejection 3.5–5.8% at 59 days (n = 480 per outcome), negative-control rejection 5.5% (195 of 3,520 and 140 of 2,560). [ESTIMATE] The null size is only resolved to about ±2 points per cell, so "consistent with 5%" is the honest claim, not "exactly 5%".
7. **[VERIFIED] H2 power depends strongly on effect size and number of days** (section 9 and 10): a planted 10% forward-volatility multiplier is detected in 96–100% of 59-day simulations; 5% in about 48%; a planted continuation of ±0.10 volatility units in about 98%, ±0.05 in 56–74%, ±0.02 in 12–20% (barely above the 5% nominal rate).
8. **[VERIFIED] 221 tests passed, 0 failed, 0 skipped** (3 warnings, section 14). `data/clean` still has 12 files; no M1–M3 source file or data file is newer than the docs/09 report.
9. **M4b is complete as a diagnostic stage. It does not conclude that H1 can be tested. It concludes that H1 testing cannot yet be trusted when heavy tails and uneven within-period variance may both be present.**

---

## 2. Final execution status  [VERIFIED]

| Job | Output folder | Log final line | Simulations |
|---|---|---|---|
| H1 factor isolation (diag) | `h1_diag/` | COMPLETE | 320,000 |
| H1 candidate comparison (cand) | `h1_cand/` | COMPLETE | 220,000 |
| H1 sample size 125/250 (size) | `h1_size/` | COMPLETE (28 cells) | 108,000 |
| H1 scenario grid | `h1_grid/` | COMPLETE | 160,000 |
| H1 leverage analysis | `h1_leverage/` | COMPLETE | 20,000 per cell × 8 cells = 160,000 (diagnostic file; not in the count total of section 13) |
| H2 power, 59 days | `h2_p59/` | COMPLETE | 5,280 |
| H2 power, 125/250 days | `h2_pbig/` | COMPLETE | 1,600 |
| Failure audit, 59-day cases | `verification/candidate_failure_audit_cand.csv` | COMPLETE cand | 80,000 audited |
| Failure audit, 125/250-day cases | `verification/candidate_failure_audit_size.csv` | COMPLETE size | 68,000 audited |
| Fast-simulator statistical comparison | `verification/fast_vs_bar_level_rejection_rate_comparison.csv` | finished | 48 cells |
| Fast-simulator exact comparison | `verification/fast_vs_bar_level_exact_matrix_comparison.csv` | finished | 160 matrices |

All folders are under `outputs/milestone4/m4b/`. The H2 run was started once. An earlier accidental start (a wrongly specified wait on the wrong process id) was stopped within seconds, before any result existed; its empty log is kept as `h2_p59_ABORTED_EARLY_START.log`. **Verified: it contributed zero results** (the count script found no output file for it, and the final H2 files hold exactly the planned 5,280 rows).

---

## 3. H1 comparison of methods (59 days)  [VERIFIED rates; INTERPRETATION in text]

H1 target (unchanged): the day-volatility-weighted pooled variance ratio between periods (RMS volatility). Tests use the days × 3 matrix of period mean squares. Rejection rate, max rule, 10,000 simulations per cell (`h1_cand_size_and_power.csv`):

| Market | Scenario (null) | rom_t | rom_jack | diff_t | wild Rademacher | wild Mammen | Empirical likelihood |
|---|---|---|---|---|---|---|---|
| NSE | G flat | 4.6 | 4.6 | 4.3 | 5.1 | 4.9 | 5.5 |
| NSE | G E | 5.3 | 5.2 | 5.4 | 7.0 | 6.6 | 6.5 |
| NSE | G D5 | 5.2 | 5.2 | 5.1 | 6.9 | 6.6 | 6.5 |
| NSE | T4 flat | 5.0 | 4.9 | 5.1 | 8.8 | 8.4 | 10.1 |
| NSE | T6 E | 6.4 | 6.4 | 7.4 | 10.5 | 10.4 | 9.2 |
| NSE | T4 E | 8.2 | 8.1 | 9.2 | 15.3 | 15.2 | 13.7 |
| NSE | T4 D5 | 8.3 | 8.2 | 9.6 | 16.5 | 16.5 | 13.4 |
| NSE | T4 R2 | 6.2 | 6.0 | 6.6 | 11.0 | 10.8 | 11.6 |
| NSE | T4 E dependent | 7.8 | 7.8 | 8.9 | 15.0 | 14.9 | 13.4 |
| NSE | T4 E no day factor | 7.0 | 7.0 | 8.3 | 13.7 | 13.6 | 11.2 |
| US | G flat | 5.3 | 5.3 | 5.0 | 5.8 | 5.4 | 6.1 |
| US | G E | 5.2 | 5.1 | 5.0 | 6.2 | 6.0 | 6.4 |
| US | T4 flat | 5.0 | 4.9 | 4.9 | 8.0 | 7.6 | 10.3 |
| US | T6 E | 5.6 | 5.7 | 6.1 | 9.2 | 8.8 | 8.3 |
| US | T4 E | 6.9 | 7.0 | 7.5 | 12.6 | 12.7 | 12.2 |
| US | T4 D5 | 8.0 | 7.9 | 9.5 | 16.4 | 16.3 | 13.6 |
| US | T4 R2 | 5.6 | 5.5 | 5.7 | 9.6 | 9.3 | 10.7 |
| US | T4 E dependent | 7.0 | 7.0 | 7.6 | 12.9 | 12.4 | 12.3 |

Notation: G = Gaussian returns; T10, T6, T4 = Student-t with 10, 6, 4 degrees of freedom; flat = equal bar variance inside periods; E, D5, R2 = empirical-style, strong and "realistic strong" within-period shapes (docs/11).

**Reading** [INTERPRETATION]: the log-ratio bootstrap-t is the best of the candidates; the jackknife standard error adds nothing; the wild bootstraps and empirical likelihood are worse because they reject too often even with Gaussian shapes E and D5 (6–7%) and badly with heavy tails (12–17%). Assumptions behind each method: the bootstrap-t resamples whole days (or blocks of 5 consecutive rows) and studentises with a delta-method standard error; wild bootstrap imposes the null by randomly flipping the sign of each day's contrast and treats days as independent; empirical likelihood uses a chi-square limit that needs a moderate sample size and light tails. Heavy tails break all three assumptions in different ways.

**Multiplicity:** the table shows the "max" rule (one critical value for the largest of 3 contrasts). The Bonferroni rule (alpha/3 per contrast) is in the same CSV; it was never better calibrated by a margin that changes any conclusion.

---

## 4. H1 calibration and power  [VERIFIED]

### 4.1 Factor isolation (8,000 simulations per cell, `h1_diag_factor_isolation.csv`)

| Market | Scenario | rom_t as run | rom_t if estimator bias removed | rom_t with oracle critical value | diff_t as run | SE / true SD (rom) |
|---|---|---|---|---|---|---|
| NSE | G flat | 4.9 | 4.9 | 5.0 | 4.8 | 0.98 |
| NSE | G E | 5.4 | 5.2 | 5.0 | 5.6 | 0.97 |
| NSE | T4 flat | 5.1 | 4.7 | 5.0 | 5.3 | 0.83 |
| NSE | T4 E | 7.5 | 6.0 | 5.0 | 8.9 | 0.80 |
| NSE | T4 D5 | 8.2 | 6.7 | 5.0 | 9.9 | 0.81 |
| NSE | T4 E no day factor | 7.3 | 6.0 | 5.0 | 8.2 | 0.82 |
| US | G E | 5.4 | 5.3 | 5.0 | 5.5 | 0.97 |
| US | T4 flat | 4.3 | 4.0 | 5.0 | 4.2 | 0.84 |
| US | T4 E | 7.1 | 5.9 | 5.0 | 7.9 | 0.80 |
| US | T4 D5 | 8.1 | 6.6 | 5.0 | 9.6 | 0.79 |

(The oracle column is 5.0 in every one of the 80 rows of the file.)

What this shows [VERIFIED]: heterogeneity alone (Gaussian E, D5) is fine; heavy tails alone (T4 flat) is fine; **the combination inflates**. Removing the analytic estimator bias helps `rom_t` (7.5 → 6.0) but not `diff_t`. The standard error is too small by about 20% for `rom` and 30–35% for `diff` in heavy-tail cells. [INTERPRETATION] T4 flat stays near 5% because the bootstrap-t partly compensates; it cannot do so when the variance shape is also uneven.

### 4.2 Close-spike scan (NSE, rom_t, T4 E; simulation evidence only)

| Close-spike decay scale tau | 0.37 | 1.0 | 2.0 | 4.0 |
|---|---|---|---|---|
| Rejection % | 8.1 | 7.6 | 6.1 | 5.8 |

Open-only spike: 5.6%. Close-only spike: 7.5%. **[INTERPRETATION] This shows that in this simulator a sharp spike concentrated in the last bars drives the inflation. It is simulation evidence for a mechanism of the simulated test, not proof that any real-market feature has the same effect.** The fitted NSE close spike (tau ≈ 0.37) is one bar, a poor description; US close tau ≈ 1.2.

### 4.3 Power  [VERIFIED rates; INTERPRETATION about meaning]

"x1.1" means volatility in the open and close periods is multiplied by 1.1 (variance by 1.21) relative to the middle period, with the same shape and tail assumptions. 59 days, 2,000 simulations per power cell (`rom_t`, max rule):

| Scenario | NSE | US | Size of the same test (null) |
|---|---|---|---|
| T4 flat x1.1 | 32.0 | 41.0 | 5.0 / 5.0 |
| T4 flat x1.2 | 84.4 | 89.9 | |
| T4 E x1.1 | 12.2 | 14.2 | 8.2 / 6.9 (inflated) |
| T4 E x1.2 | 63.6 | 70.8 | |
| T4 E x1.3 | 88.0 | 91.1 | |

[INTERPRETATION] Only the T4 flat rows are power of a test with correct size. For T4 E the rejection rates under an effect mix real power with the 7–8% size inflation; the wild and empirical-likelihood versions show higher "power" (for example NSE T4 E x1.2: 82% and 89%) only because they also reject too often under the null. **No method was selected on power.**

---

## 5. H1 sample size (59, 125, 250 days)  [VERIFIED]

Null rejection, `rom_t`, max rule, 5,000 simulations per cell (59 days from the grid file for the same scenario name where available; 125 and 250 from `h1_size_size_and_power.csv`):

| Market | Scenario | 59 days | 125 days | 250 days |
|---|---|---|---|---|
| NSE | G E | 5.0 | 4.8 | 4.7 |
| NSE | T4 flat | 5.3 | 4.9 | 5.2 |
| NSE | T4 E | 7.9 | 7.7 | 7.1 |
| NSE | T4 D5 | 8.5 | 7.2 | 6.7 |
| NSE | T4 E dependent | 7.8* | 6.6 | 7.3 |
| US | G E | 4.8 | 5.2 | 5.7 |
| US | T4 flat | 4.2 | 4.2 | 4.7 |
| US | T4 E | 6.9 | 6.3 | 6.3 |
| US | T4 D5 | 7.8 | 8.9 | 7.7 |
| US | T4 E dependent | 7.0* | 6.7 | 6.2 |

\* 59-day "dependent" values come from the 10,000-simulation candidate file (section 3), the others from the 5,000-simulation grid.

Power of the same test, T4 E (size-inflated, so interpret with care), 125 → 250 days: x1.1: NSE 32.0 → 68.6, US 37.9 → 72.6; x1.2: NSE 86.8 → 94.2, US 91.8 → 96.8.

[INTERPRETATION] More days **do not remove the inflation**: heavy tails with uneven shape still reject 6–9% at 250 days (95% interval about ±0.6). The improvement is slow; this is a statement about these simulated worlds only. Sample size does clearly raise power. Note that 59 days is the actual length of the real NSE sample, so the 59-day rows are the most relevant for later work.

---

## 6. Numerical failure audit  [VERIFIED]

Audited: the first 3,000 simulations (null cells) or 2,000 (power cells) of every cell. Each simulation has 3 contrasts. Reproducibility: the first 300 seeds per cell were re-run and compared with the saved result.

| Case | Cells | Simulations audited (denominator) | Re-runs checked | Re-run mismatches |
|---|---|---|---|---|
| 59 days (`audit_cand`) | 30 | 80,000 | 9,000 | 0 |
| 125 and 250 days (`audit_size`) | 28 | 68,000 | 8,400 | 0 |

For both files, summed over all cells (each count is out of the denominator above):

| Problem | Count |
|---|---|
| Empirical likelihood: zero outside convex hull (counts as rejection) | 0 |
| Empirical likelihood: solver exception | 0 |
| Empirical likelihood: not converged | 0 |
| Empirical likelihood: invalid statistic | 0 |
| Jackknife: invalid observed statistic / bad resamples | 0 / 0% |
| Wild bootstrap (Rademacher, Mammen): invalid observed statistic / bad resamples | 0 / 0% |
| Delta-method bootstrap-t: invalid observed statistic | 0 |
| Discarded or retried replications | 0 (the code has no discard or retry path) |
| Missing values in decision columns of the saved results | 0 |

Limitations of the audit [VERIFIED scope]: it covers the first 3,000 / 2,000 seeds per cell (148,000 of 328,000 simulations in those two files), not every simulation. The un-audited simulations used the same code and the saved decision columns contain no missing value, but a rare failure outside the audited block cannot be excluded by this audit alone. [INTERPRETATION] A zero hull-exit rate is plausible: with 59 days and 3 contrasts the day-level differences almost always include both signs unless the effect is huge.

The unit tests of `el_statistic` (`test_research_robust.py`) check that the hull rule returns infinity (counted as rejection); the audit shows that this path was never reached in the audited simulations.

---

## 7. Leverage analysis (diagnostic only, not an estimator)  [VERIFIED]

Leverage of a simulation = the largest share any single day contributes to the sum of a period (`max over periods of max_d X[d,p] / Σ_d X[d,p]`). Simulations were split into quartiles; 20,000 per cell. No data were modified and nothing is trimmed or reweighted. Rejection of `rom_t`, % (59 days):

| Market | Scenario | Q1 (lowest leverage) | Q2 | Q3 | Q4 (highest) |
|---|---|---|---|---|---|
| NSE | G E | 9.2 | 5.7 | 4.1 | 2.2 |
| NSE | T4 flat | 10.3 | 5.8 | 3.2 | 0.7 |
| NSE | T4 E | 20.2 | 7.6 | 3.6 | 0.7 |
| NSE | T4 D5 | 19.2 | 8.6 | 3.8 | 1.0 |
| US | G E | 7.3 | 5.1 | 4.2 | 2.5 |
| US | T4 flat | 10.1 | 5.3 | 3.4 | 0.6 |
| US | T4 E | 15.8 | 6.4 | 3.8 | 1.0 |
| US | T4 D5 | 18.5 | 8.1 | 4.0 | 0.9 |

(The marginal rates over all quartiles are in sections 3–4. `diff_t` shows the same pattern, for example NSE T4 E 23.9 / 9.5 / 3.8 / 0.4.)

[INTERPRETATION] The over-rejection sits in the **lowest**-leverage simulations (where no single day dominates), not the highest. A single dominant day therefore does not explain the inflation. Even Gaussian E shows a gradient (9.2% → 2.2%), so the gradient alone is a property of how the bootstrap-t behaves conditionally on leverage; it is not evidence of an outlier problem. An earlier "replace the largest returns" diagnostic was found to be confounded (it breaks the null under uneven shapes) and its columns in `h1_diag_factor_isolation.csv` (`reject_after_removing_*_extreme_obs`) **are not used for any conclusion here**.

---

## 8. H2 true-null calibration  [VERIFIED counts; ESTIMATE precision]

Model M5 (stock × slot effects, controls c1–c4), day-clustered tests; "wild" = wild-cluster-bootstrap p-value (B = 199), "t" = clustered CR1 with t(G−1). World: day factor + intraday regime, volume independent of returns (a true null). Pooled over market and dependence cell, rejections / simulations:

| Outcome | p-value | 59 days | 125 days | 250 days |
|---|---|---|---|---|
| Forward volatility | wild | 28 / 480 = 5.8% [4.1, 8.3] | 8 / 160 = 5.0% [2.6, 9.6] | 4 / 160 = 2.5% [1.0, 6.3] |
| Forward volatility | t | 36 / 480 = 7.5% [5.5, 10.2] | 7 / 160 = 4.4% | 5 / 160 = 3.1% |
| Continuation | wild | 17 / 480 = 3.5% [2.2, 5.6] | 7 / 160 = 4.4% | 4 / 160 = 2.5% |
| Continuation | t | 24 / 480 = 5.0% [3.4, 7.3] | 9 / 160 = 5.6% | 4 / 160 = 2.5% |

Brackets are Wilson 95% intervals. By cell (120 simulations each at 59 days), wild-p rejection of volatility is 5.8 (NSE independent), 3.3 (NSE dependent), 7.5 (US independent), 6.7 (US dependent); continuation 2.5, 4.2, 5.0, 2.5.

**Negative controls** (the other outcome tested in a world where only the first outcome has a planted effect, so the true rejection rate is 5%): wild p: volatility outcome 195 / 3,520 = 5.5% [4.8, 6.3]; continuation outcome 140 / 2,560 = 5.5% [4.7, 6.4]. Clustered-t is slightly more liberal (6.3% and 6.0%).

Earlier (docs/11, larger counts of 2,240 per world) the same test showed 4.3–5.3% under the true null. Together: [INTERPRETATION] the wild-bootstrap M5 test is consistent with its nominal level in the simulated worlds studied; clustered-t is a little liberal for volatility at 59 days. This is calibration in **these simulated worlds only**. It says nothing yet about real-market dependence beyond the estimated stock correlation and day-persistence used here (itself estimated from about 59 days, so imprecise).

**True-null check of the planted-effect machinery** [VERIFIED by unit tests `test_research_h2_effects.py`, 3 tests]: effects begin after the event bar, last 3 bars, never cross a day boundary, have the right sign, volume is identical with and without effects, and null arguments reproduce the default world exactly.

---

## 9. H2 power  [VERIFIED rates; ESTIMATE precision]

Wild-p rejection rate, %, target outcome (volatility effects tested on forward volatility; continuation effects tested on continuation). 120 simulations per cell at 59 days (power MC standard error up to 4.6 points); ~850 events per simulation on NSE and ~930 on US. Planted effects are not market relationships.

### 9.1 Volatility effects (forward volatility after a high-volume event, next 3 bars)

| Planted multiplier | NSE independent | NSE dependent | US independent | US dependent |
|---|---|---|---|---|
| x0.90 (reduction) | 100.0 | 98.3 | 100.0 | 99.2 |
| x1.05 | 53.3 | 48.3 | 51.7 | 48.3 |
| x1.10 | 94.2 | 96.7 | 97.5 | 99.2 |
| x1.25 | 100.0 | 100.0 | 100.0 | 100.0 |

### 9.2 Continuation effects (drift in the event candle's direction; negative = reversal)

| Planted drift (volatility units) | NSE independent | NSE dependent | US independent | US dependent |
|---|---|---|---|---|
| −0.10 | 98.3 | 98.3 | 99.2 | 97.5 |
| −0.05 | 55.8 | 55.8 | 62.5 | 57.5 |
| −0.02 | 12.5 | 13.3 | 12.5 | 11.7 |
| +0.02 | 17.5 | 19.2 | 12.5 | 18.3 |
| +0.05 | 65.0 | 60.8 | 51.7 | 74.2 |
| +0.10 | 99.2 | 98.3 | 98.3 | 99.2 |

### 9.3 Negative controls (wrong outcome for the planted effect), wild p

Volatility effects tested on continuation: 0–10% (pooled 5.5%). Continuation effects tested on forward volatility: 2.5–12.5% (pooled 5.5%). Both pooled intervals contain 5%. Individual cells vary because each has only 120 simulations.

### 9.4 Mean estimated effect (dependent world, 59 days; wild-p files `h2_p59_power.csv`, `mean_beta`)

Forward-volatility coefficient: x0.90 → −0.108 (NSE) / −0.109 (US); x1.05 → 0.052 / 0.048; x1.10 → 0.097 / 0.095; x1.25 → 0.233 / 0.230 (planted log multipliers: −0.105, 0.049, 0.095, 0.223). Continuation coefficient (return × 10,000, i.e. basis points): ±0.10 → ±3.3–3.6; ±0.05 → ±1.7–1.9; ±0.02 → ±0.7–0.8. [INTERPRETATION] The estimates track the planted sizes and signs, which supports the timing and sign of the injected effects.

### 9.5 Direction and dependence [INTERPRETATION]

- **Direction:** no consistent asymmetry between momentum (+) and reversal (−) drift. +0.05 beats −0.05 in three cells but loses in one (US independent: 51.7 vs 62.5). The differences are within about two standard errors in most cells. The data cannot resolve a direction effect at 120 simulations.
- **Dependence:** X0 (independent stocks) and X3 (estimated cross-stock correlation and day-volatility persistence) give similar power; differences are within Monte-Carlo noise. Stronger dependence than estimated (X4) was not run for H2.
- **Market:** NSE and US power are similar; the US has slightly more events per simulation.
- **Volatility vs continuation:** reported separately above; they are different outcomes with different planted-effect units, so their power levels must not be compared as "which is easier".
- The x0.90 effect looks easy to detect compared with x1.05 simply because it is a larger planted change, not because reductions are special.

---

## 10. H2 sample size (59, 125, 250 days, dependent world X3, 80 simulations per cell at 125/250)

| Effect | Market | 59 days | 125 days | 250 days |
|---|---|---|---|---|
| vol x1.05 | NSE | 48.3 | 81.2 | 100.0 |
| vol x1.05 | US | 48.3 | 85.0 | 98.8 |
| vol x1.10 | NSE | 96.7 | 100.0 | 100.0 |
| vol x1.10 | US | 99.2 | 100.0 | 100.0 |
| cont +0.02 | NSE | 19.2 | 28.7 | 55.0 |
| cont +0.02 | US | 18.3 | 25.0 | 46.2 |
| cont +0.05 | NSE | 60.8 | 90.0 | 100.0 |
| cont +0.05 | US | 74.2 | 91.2 | 100.0 |

True-null and negative-control rows at 125 and 250 days are in section 8 (null: 2.5–6.2%; 160 simulations per day count, imprecise). Note the 125/250-day rows have only 80 simulations per cell (MC standard error up to 5.6 points).

[INTERPRETATION] A planted continuation of 0.02 volatility units is **not reliably detectable even at 250 days** (about half of simulations); a planted 5% volatility multiplier needs about 125 days for 80–85% detection. Longer samples help roughly as expected.

---

## 11. Fast-simulator validation  [VERIFIED]

Why a fast simulator exists: it computes each period's mean squared return directly (return = profile × exp(day factor) × shock) instead of building bar tables and running cleaning, which allows thousands of simulations per scenario. It is valid only without intraday regime, autoregression or missing bars; the H1 scenarios here have none of these.

1. **Exact comparison (160 matrices):** identical returns were fed through both routes (`direct_bridge.py`: the bridge rebuilds raw bars, then runs the real `clean()` and `build_bar_table()`). All 160 matrices had the same shape and the largest relative difference was 4.02e-13 (floating point rounding). **Verified.**
2. **Statistical comparison (48 cells)** with two-proportion z-tests of the fast rejection rates against the earlier bar-level results (`fast_vs_bar_level_rejection_rate_comparison.csv`):

| Quantity | Value |
|---|---|
| Cells compared | 48 |
| Cells with \|z\| > 2 | 3 (expected by chance about 2 of 48) |
| Cells with \|z\| > 3 | 0 |
| Mean difference (bar-level − fast) | +0.63 points |
| Largest absolute difference | 3.65 points |

The three cells with \|z\| > 2 are all one scenario, **NSE R2 realistic strong (T4)**: bar-level rates 8.2 / 8.9 / 8.5 % versus fast 6.2 / 6.8 / 6.6 % (rom_t max, rom_t bonf, diff_t max; z = 2.3–2.5). The bar-level reference there has only 1,000 simulations (MC SE about 0.9 points). The three rules in that cell are strongly correlated, so they are not three independent surprises. [INTERPRETATION] The evidence supports equivalence for the purpose of this report but does not prove it; the R2 NSE difference and the small positive mean difference are not explained and are listed as an unresolved item.

3. **Limitation: identical seeds do not give identical numbers.** The two generators consume random numbers in a different order and different amounts (the bar-level route draws raw bar quantities, volume and quirks that the fast route never draws), so the same seed produces different random streams. Equivalence is therefore established by (a) identical-returns matrices (exact) and (b) matching distributions of rejection rates (statistical), not by seed-for-seed agreement. **Verified by design; the statistical agreement is an estimate with the precision above.**

---

## 12. Dependence and heavy-tail findings  [VERIFIED rates; INTERPRETATION]

- **Heavy tails alone do not inflate; unequal within-period variance alone does not inflate; the two together do** (section 4.1).
- **Severity ranking** (rom_t max rule, 59 days, NSE/US): T4 D5 8.5/7.8, T4 E 7.9/6.9, T4 R2 6.5/5.9, T6 D5 6.4/6.3, T6 E 6.3/6.0, T10 D5 5.7/5.8, T4 flat 5.3/4.2, G cells ≈5 (grid file, 5,000 each).
- **Cross-stock correlation and day-volatility persistence (estimated levels, X3)** made little difference to H1 size (T4 E dependent 7.8/7.0 vs independent 8.2/6.9). Stronger dependence (X4: correlation 0.5, share 0.7, persistence 0.7) was a docs/11 scenario and is illustrative only.
- Dependence parameters (NSE correlation 0.355, share 0.454, persistence 0.441; US 0.187, 0.141, 0.190) come from about 59 days per market and are **imprecise estimates**.
- **Block bootstrap gaps:** blocks are 5 consecutive rows after dropping days with missing stock values. 0 of 29,000 simulations dropped a day; the real NSE sample dropped only the last date, so no interior gap. Forcing gaps changes the as-run method's rejection by 2–3 points compared with a gap-aware version (docs/11).
- The analytic bias correction assumes equal variance across bars within a period; this is false for realistic shapes, and removing the bias reduces `rom_t` rejection by about 1.5 points in heavy-tail cells (section 4.1) without solving the problem.

---

## 13. Exact counts and seed audit  [VERIFIED]

| File | Cells | Planned | Actual | Cells with wrong count | Duplicate seeds inside file | Missing values in decision columns |
|---|---|---|---|---|---|---|
| h1_diag | 40 | 320,000 | 320,000 | 0 | 0 | 0 |
| h1_cand | 30 | 220,000 | 220,000 | 0 | 0 | 0 |
| h1_size | 28 | 108,000 | 108,000 | 0 | 0 | 0 |
| h1_grid | 32 | 160,000 | 160,000 | 0 | 0 | 0 |
| h2_p59 | 44 | 5,280 | 5,280 | 0 | 0 | 0 |
| h2_pbig | 20 | 1,600 | 1,600 | 0 | 0 | 0 |
| **Total** | **194** | **814,880** | **814,880** | **0** | **0** | **0** |

**Seed overlap across files.** The count script reports 814,852 unique seed values among 814,880 rows, so 28 values occur twice. I traced all 28 (checked after the first count script flagged "DUPLICATE SEEDS ACROSS FILES"):

- Every one of the 28 pairs lies in **two different files** (file counts: diag 24 rows, grid 15, size 13, cand 1, p59 1, pbig 2; total 56 rows = 28 pairs).
- In **none** of the 28 pairs do the two simulations share the same file **and** the same cell (market, scenario, days, effect), i.e. no simulation was repeated. Example: seed 252588794 is a US "T6 E" 59-day grid simulation and a US "T4 Etau4.0" 59-day factor-isolation simulation; seed 314156934 is a US "T4 flat" 250-day size simulation and an NSE "G E" 59-day factor-isolation simulation.
- Cause: each part draws one 32-bit integer per simulation from its own master seed (`SeedSequence.spawn` then `generate_state(1)`). With about 815,000 draws in a space of 2³² ≈ 4.29 × 10⁹, chance coincidences between different parts are expected (my estimate of the expected chance coincidences between files is about 55, i.e. about 77 for all pairs minus about 22 within files; 28 observed). [INTERPRETATION] Two simulations with the same seed but different scenario or parameters use the same underlying random draws, so they are correlated through common random numbers; with 28 such pairs among 814,880 (0.003%), the effect on any reported rate is negligible. No result was removed or changed.
- Within every single file the seeds are all distinct.

---

## 14. Test results  [VERIFIED]

Command: `python -m pytest -q` in `/Users/pravin/Quantlab`, run after all M4b code changes and after all jobs ended.

**221 passed, 0 failed, 0 skipped**, 3 warnings, 9.98 s. (205 passed at the end of the docs/11 round; the three M4b test files `test_research_robust.py` (11), `test_research_direct_bridge.py` (2) and `test_research_h2_effects.py` (3) add 16, giving 221.)

Warnings (all 3 are the same line): `RuntimeWarning: invalid value encountered in scalar divide` at `src/quantlab/research/h2_volume.py:157` (`prev_ratio[i] = day_rms[i-1] / np.nanmedian(...)`), raised in three existing H2 tests (`test_primary_outcomes_use_next_open_entry...`, `test_continuation_sign_follows_the_event_candle_direction`, `test_delay_shifts_entry_one_candle`). It occurs when a window has no valid previous day. This file was not changed in M4b; the warning does not fail any test. I did not investigate whether it affects results beyond noting it (see section 15).

**M1–M3 and data unchanged** [VERIFIED]:

- `data/clean` has **12 files** (`ls data/clean | wc -l` = 12).
- No file under `data/` is newer than `docs/09_m4a_h1_h2_diagnostic_report.md` (count = 0).
- No `.py` file in `src/quantlab/` outside `research/` is newer than that same report (count = 0). The research files modified in M4b are listed in section 17.
- Earlier outputs (`outputs/milestone4/next_round/`, `outputs/milestone4/diagnostics/`, all `*_QUICK_PLUMBING_CHECK` folders and the aborted-run log) are present and not deleted.
- Caveat on this check [VERIFIED scope]: it compares file modification times, not checksums, so it shows "not touched", not a byte-for-byte hash comparison.

---

## 15. Warnings, limitations and unresolved issues

1. **H1 inference is unresolved.** No candidate is calibrated across the heavy-tail + uneven-shape scenarios, at 59, 125 or 250 days. I did not call any method calibrated just because its interval includes 5% in a mild cell.
2. **Real-market relevance of the stress scenarios is unknown.** Student-t with 4 degrees of freedom and shapes E/D5 are described from small samples (59 days) and are imprecise.
3. **No H1 correction was proposed or tested beyond the listed candidates.** Possible next steps (a different studentisation, variance-stabilising transforms, calibrating the critical value by simulation under the fitted shape) change the methodology and need your approval.
4. **H2 precision:** 120 simulations per cell (59 days) and 80 (125/250 days) leave null-size and power cells with ±2–5 point Monte-Carlo error; "consistent with nominal" is not "equal to nominal". Only a subset of effect sizes was run at 125/250 days, only the dependent world X3 at those lengths, and stronger dependence (X4) was not run for H2.
5. **H2 results are for planted effects in synthetic data.** They show how strongly the test could detect such effects, not whether any exists in real data. No causal reading is allowed ("predictive information beyond past controls" only).
6. **Failure audit covers the first 3,000 / 2,000 simulations per cell**, not all of them (section 6).
7. **Fast simulator:** exact equivalence is verified only for these H1 scenarios; the NSE R2 cell differs by about 2 points from the earlier 1,000-simulation bar-level run (z ≈ 2.5), unresolved; the mean difference over 48 cells is +0.63 points (bar-level higher).
8. **Seed overlap:** 28 cross-file coincidences, harmless but documented (section 13).
9. **Warning in `h2_volume.py:157`** (3 occurrences, all tests passing): not changed or investigated in M4b.
10. **Estimand:** unchanged (RMS volatility, day-volatility-weighted pooled variance ratio). The "x" scenarios multiply open and close volatility, not variance.
11. **Leverage analysis is descriptive** (section 7); the earlier "replace extremes" columns are confounded and must not be cited.
12. **Missing document:** `docs/07_research_protocol.md` does not exist; docs 09–12 are diagnostic reports, not a frozen protocol.
13. **Not done by design:** no real-market H1/H2/H3 test, no H3, no protocol freeze, no strategies or backtests, no M5, no paid data.

---

## 16. Recommended next step (not executed)

Decision needed from you before anything else: **how to handle H1 given that no tested inference method is calibrated under heavy tails with uneven within-period variance.** Options, in the order I would consider them:

1. **Pre-register the limitation instead of fixing it:** state that H1 results are reported with a simulation-based critical value or with an explicit "size may be up to ~8–9% under heavy tails" caveat. This does not change the estimand.
2. **One further, narrowly scoped diagnostic round** on a simulation-calibrated critical value (fit the shape and tail from the sample, simulate the null, take the critical value from that simulation) tested at 59, 125 and 250 days.
3. **Only after you decide on H1:** write the research protocol (`docs/07_research_protocol.md`) for freezing, including the H2 calibration evidence above.

Both H2 evidence (calibrated in the worlds studied; power depends on effect size and days) and H1 evidence (not calibrated) are now in place for you to review. I will not start any of these until you approve.

---

## 17. Decision table

| Item | Evidence (from this report) | Status |
|---|---|---|
| H1 calibration | Gaussian / flat OK (≈5%); T4 + shape E/D5 rejects 7–9% at 59 days and 6–9% at 125/250 days | **NOT calibrated** |
| H1 candidates | rom_t ≈ rom_jack best; diff_t, wild, EL equal or worse; none calibrated | **No candidate selected** |
| H1 power | Reported only as power of tests with known size problems; T4 flat x1.2: 84–90% at 59 days | **Measured, interpret with size caveat** |
| H1 sample size | 59/125/250 days: inflation persists, falls slowly; power rises clearly | **Measured; does not fix calibration** |
| H2 calibration | Null 3.5–5.8% (wild, n = 480 per outcome at 59 days), negative controls 5.5% | **Consistent with nominal in tested worlds** (limited precision) |
| H2 power | 48% at x1.05, ≥96% at x1.10; continuation ±0.10 ≈98%, ±0.05 56–74%, ±0.02 12–20% (59 days); rises with days | **Measured (planted effects only)** |
| H2 sample size | x1.05: 48% → 81–85% → 99–100%; cont +0.02: 18–19% → 25–29% → 46–55% | **Measured (80 simulations per cell at 125/250)** |
| Numerical reliability | 0 failures of any type in 148,000 audited simulations; 17,400/17,400 reproduced | **Verified (audited block only)** |
| Simulator equivalence | 160/160 exact; 45/48 statistical cells agree, 3 (one NSE cell) at \|z\| 2.3–2.5 | **Supported, not proven** |

**Findings supported by completed simulations:** counts, the failure audit, simulator exact equivalence, the oracle-critical-value diagnosis, H1 size by scenario and days, H2 size and power by effect, direction, market, dependence and days. **Methods that failed calibration:** all six tested H1 candidates in heavy-tail + uneven-shape worlds. **Unresolved:** H1 inference; real-market relevance of the stress worlds; the NSE R2 simulator difference. **Sample-size sensitivity:** section 5 (H1) and section 10 (H2). **Numerical and implementation limitations:** sections 6, 11 and 15.

---

## Appendix A — New and modified files

**Source (`src/quantlab/research/`)**

| File | Status |
|---|---|
| `direct_sim.py` | new (M4b): fast generator, leverage helpers |
| `direct_bridge.py` | new (M4b): feeds identical returns through the real cleaning pipeline |
| `h1_robust.py` | new (M4b): jackknife-t, wild bootstrap-t, empirical likelihood |
| `dependence.py` | modified (M4b): `core_corr_for_pearson` made stable for large degrees of freedom (value for 4 df unchanged, 0.452) |

(`h1_rms2.py`, `nulls.py`, `h1_rms.py` were created or modified in earlier rounds, before docs/11 was written; they were not edited in M4b.)

**Scripts (`scripts/milestone4/`)**: `run_h1_inference.py`, `run_h1_grid.py`, `diag_extreme_leverage.py`, `run_h2_power.py`, `validate_fast_simulator.py`, `audit_candidate_failures.py`, `verify_m4b_counts.py` (all new in M4b).

**Tests (`tests/`)**: `test_research_robust.py` (11 tests), `test_research_direct_bridge.py` (2), `test_research_h2_effects.py` (3) — new in M4b. (`test_research_dependence.py`, 13 tests, dates from the docs/11 round.)

**Docs**: `docs/12_m4b_h1_inference_and_h2_power_report.md` (this file).

**Outputs (`outputs/milestone4/m4b/`)**

| Path | Contents |
|---|---|
| `h1_diag/` | `h1_diag_per_simulation.parquet`, `h1_diag_size_and_power.csv`, `h1_diag_factor_isolation.csv`, `run_metadata.csv` |
| `h1_cand/` | `h1_cand_per_simulation.parquet`, `h1_cand_size_and_power.csv`, `run_metadata.csv` |
| `h1_size/` | `h1_size_per_simulation.parquet`, `h1_size_size_and_power.csv`, `run_metadata.csv` |
| `h1_grid/` | `h1_grid_per_simulation.parquet`, `h1_grid_size.csv`, `run_metadata.csv` |
| `h1_leverage/` | `h1_leverage_per_simulation.parquet`, `h1_leverage_by_quartile.csv`, `run_metadata.csv` |
| `h2_p59/` | `h2_p59_per_simulation.parquet`, `h2_p59_power.csv`, `run_metadata.csv` |
| `h2_pbig/` | `h2_pbig_per_simulation.parquet`, `h2_pbig_power.csv`, `run_metadata.csv` |
| `verification/` | `planned_vs_actual_counts.csv`, `candidate_failure_audit_cand.csv`, `candidate_failure_audit_size.csv`, `fast_vs_bar_level_exact_matrix_comparison.csv`, `fast_vs_bar_level_rejection_rate_comparison.csv` |
| logs | `h1_diag_run.log`, `h1_cand_run.log`, `h1_size_run.log`, `h1_grid_run.log`, `h1_leverage_run.log`, `h2_p59_run.log`, `h2_pbig_run.log`, `audit_cand_run.log`, `audit_size_run.log`, `validate_stat_run.log`, `full_test_run.log` |
| preserved | `h2_p59_ABORTED_EARLY_START.log`; `*_QUICK_PLUMBING_CHECK` folders for diag, cand, size, grid, leverage |

Note: the new `full_test_run.log` was produced in this audit (the pytest output quoted in section 14). The same-named folder `h1_leverage/` belongs to `diag_extreme_leverage.py`.
