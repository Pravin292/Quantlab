# 25 — Stage 5 errata note: Stage 2–3 repeat variability

**Status:** documentation only, written 2026-11-12 under the user's authorisation. `docs/24` is **not edited**; this note supplements it. It rests on a read-only re-analysis of saved Stage 2 and Stage 3 per-simulation files. **No simulation was run, no random number was generated, no real market data was accessed, and no frozen input, seed, threshold, acceptance criterion, manifest or source file was changed.** All data are simulated.
**Labels:** **[CALCULATED]** a number computed from saved files; **[INTERPRETATION]** a statistical reading of those numbers; **[UNCERTAIN]** not resolved by the available evidence.

## 1. Purpose and relationship to the Stage 5 decision report
`docs/24` §7 reported the repeat of the 76 development cells with fresh seeds (Stage 3 against Stage 2) and noted two comparisons with |z| > 3. It did not report the aggregate chi-square statistic of those comparisons, and it described the number of |z| > 3 events only against a naive expectation. The independent audit and the follow-up investigation found an aggregate excess variability for C3 that `docs/24` does not record. This note records it, its limits, and what it does and does not change.

**Wording in `docs/24` that this note qualifies (without changing it):**
- §7, "about 8 expected by chance … 2 above 3 against about 0.4 expected": incomplete, because it omits the aggregate statistic (section 2) and the dependence between the 152 comparisons (section 3).
- §1 and §9, "conservative": correct for the median, but at the T4/D5 125-day cells C3 is at about nominal level (section 7).
- The audit's remark that variability is "largest in T4" is **superseded** by section 4 (not statistically established).

## 2. Reproduced Stage 2–3 repeat statistics [CALCULATED]
Source: `stage2/development/cell_*.parquet` and `stage3/validation/cell_*.parquet` (76 matched cells, development row = validation row), `stage3/summary/stage3_vs_stage2_repeat.csv`. Every z-score was recomputed from the raw per-simulation rows with the same pooled two-proportion formula; the largest difference from the saved CSV is 0.0. The critical value 3.298658 is identical in both stages for the C3 cells.

| | C3 | Baseline (reference) |
|---|---|---|
| Comparisons | 76 | 76 |
| Sum of z² | **113.41** | **83.26** |
| Chi-square reference, 76 df: p | **0.0035** | **0.266** |
| SD of z-scores | **1.214** | **1.054** |
| Mean z | +0.195 (one-sample t p = 0.17) | −0.010 |
| Cells with Stage 3 rate above Stage 2 | 43 of 76 (sign test p = 0.30) | 37 of 76 |
| Ratio sum z² / 76 | 1.49 (rough 95% interval 1.11–2.11) | 1.10 (0.82–1.55) |
| Extra SD of the (Stage 3 − Stage 2) rate difference beyond binomial noise | about 0.09 points | about 0.05 points |

The largest absolute rate difference is 0.53 points for C3 and 0.60 points for the baseline; typical binomial SD of the difference is 0.15 points (C3) and 0.24 points (baseline). The distribution of the C3 z-scores is close to normal in shape (Shapiro p = 0.57, skew −0.05, excess kurtosis −0.6): the excess is a broad variance inflation, not a few extreme outliers.

## 3. Statistical assumptions and multiplicity considerations
**Assumptions tested [CALCULATED]:**
- *Normal approximation:* adequate. Exact (Fisher mid-p) z-values differ from the normal ones by at most 0.002; the smallest pooled rejection count in any cell is 278.
- *Independence of simulations inside a cell:* supported in both stages and both methods. Ten-block dispersion tests give p between 0.39 and 0.71, and lag-1 autocorrelations average 0.000 ± 0.001.
- *Independence between cells:* supported. Across 2,278 cell pairs the correlation of T at the same simulation index has SD 0.0064 (0.0063 expected for independence); the variance of the per-simulation count of cells exceeding 3.2987 is 1.033 (Stage 2) and 1.040 (Stage 3) against 1.036 and 1.048 expected for independence.
- *No seed reuse:* 0 identical T values in 1,780,000 same-cell cross-stage pairs; same-index correlations are about 0.
- *Whole-distribution drift between stages:* none detected. Kolmogorov–Smirnov tests of T, Stage 2 against Stage 3, over the 76 cells have uniformly distributed p-values (p = 0.57); Fisher's combined statistic gives p = 0.74.
- *Dependence between C3 and baseline:* the 152 comparisons are **not** 152 independent tests. Both methods are applied to the same datasets inside each stage; the within-cell correlation of their rejection indicators averages 0.536 and the observed correlation between the C3 and baseline z-scores is 0.477, as shared data would predict.

**Multiplicity [INTERPRETATION]:**
- The smallest of the 152 individual p-values is 0.00094; after Bonferroni over 152 it is 0.14. No single comparison is significant.
- The aggregate chi-square for C3 (p = 0.0035) is a different test. Allowing for the two methods that were examined, its adjusted p is about 0.007. The audit then examined further subgroups (tail, shape, market, sample size); those are post hoc, and their p-values should not be read at face value.
- C3 and the baseline are applied to the same datasets, so the 152 z-scores are not 152 independent observations. This matters differently for three quantities, which should not be conflated:
  1. *Expected number of extreme z-scores.* It is the sum of the individual marginal probabilities (for example 152 × 0.0027 ≈ 0.4 values with |z| > 3 under the null) and **does not require independence**. Dependence does not change it.
  2. *Probability of observing a particular number of extreme results* (for example "at least two with |z| > 3"). This **does depend on the dependence structure**: a positive correlation between the paired z-scores can change the joint probability of extreme results, but the precise effect depends on the joint tail distribution, which was not calculated in this investigation. The observed correlation of 0.477 therefore does not prove that extreme values cluster. A figure computed as if the 152 z-scores were independent, as in the audit and in the informal comparison in `docs/24`, is only approximate, and its error cannot be signed or sized without the joint distribution. The Bonferroni adjustment quoted above does not require independence (it is conservative under dependence).
  3. *Amount of independent statistical information.* The two methods are paired because they use the same datasets, and the observed correlation of their z-scores is 0.477 (explained by the shared datasets, as in the dependence bullet above). This indicates that the two sets of comparisons are not fully independent. However, correlation alone does not establish a universal effective sample size, and it does not prove that the amount of independent information lies strictly between 76 and 152. Any effective sample size would depend on the statistical quantity considered and on the dependence structure, and none was calculated here.

## 4. T4-specific findings and why the apparent concentration is not statistically established
**Calculated:** sum of z² by tail for C3 is T4 46.8 on 24 comparisons (p = 0.004), T6 32.6 on 20 (p = 0.038), G 19.5 on 16, T10 6.9 on 8, T3 7.6 on 8; for the baseline T4 is 37.8 on 24 (p = 0.037). Inside T4, the large values sit in 59-day cells (C3 NSE 24.5 on 8, p = 0.002; baseline US 20.7 on 8, p = 0.008) and in the shapes with only two cells (R2 and flat).

**Why this is not established [INTERPRETATION]:**
1. T4 was identified after the aggregate result, as one slice among five tails and two methods. A Šidák adjustment for ten tail-by-method slices raises the T4 C3 p-value to about 0.04.
2. A direct contrast does not support a T4 effect: comparing the per-cell z² of T4 cells with all others gives Mann–Whitney p = 0.12 (C3) and 0.20 (baseline); the ratio of z SDs is 1.28 and 1.36, with wide uncertainty on 24 against 52 cells.
3. T6 is also elevated for C3, while T3, the heaviest tail, is not (SD 1.04), so the pattern does not rise with tail weight.
4. Within T4 the 125- and 250-day cells are close to expectation.

The statement that variability is "largest in T4" should therefore be read as an observation about these 24 cells, not as a demonstrated feature of the test.

## 5. The two notable comparisons and their interpretation
| | Row 25: T4, flat shape, US, 59 days | Row 30: T4, R2 shape, NSE, 59 days |
|---|---|---|
| C3, Stage 2 → Stage 3 | 294 → 243 of 25,000 (1.176% → 0.972%); z = −2.21 | 434 → 536 (1.736% → 2.144%); z = **+3.31**; exact p = 0.0011 |
| Baseline | 1,281 → 1,131 (5.124% → 4.524%); z = **−3.13**; exact p = 0.0019 | 1,520 → 1,631 (6.080% → 6.524%); z = +2.04 |
| Direction | both methods lower in Stage 3 | both methods higher in Stage 3 |
| Bonferroni over 152 comparisons | baseline 0.265; C3 not significant | C3 0.143; baseline not significant |
| Stage 2 vs Stage 3 distribution of T (KS) | p = 0.286 | p = 0.187 |

**Calculated:** the counts in the saved files are correct; `reject_c3` equals `T > 3.298658` in every row of both cells; simulation ids are unique; the critical value is constant. About 97% of C3 rejections are also baseline rejections (285 of 294 in row 25), so the two methods move together. In row 30 the change is in the upper tail (exceedances of T above 3.3: 434 → 534; above 3.6: 255 → 285; above 4.0: 117 → 129) while the mean of T changes by about 1%.

**Interpretation:** neither comparison is significant after correction for the number of comparisons made; both are compatible with sampling variation; the same-direction movement of the two methods is explained by shared datasets. **No computational or statistical error was identified in either cell.** This does not prove that they are chance events (section 6).

## 6. The unresolved threshold-specific effect around 3.3
**Calculated:** the cross-stage comparison of exceedance counts of T over the 76 cells gives, for each threshold, sum of z² (p against 76 df): T > 2.4: 71.8 (0.62); 2.6: 79.2 (0.38); 2.8: 79.5 (0.37); 3.0: 82.6 (0.28); **3.3: 112.5 (0.004)**; 3.6: 86.5 (0.19). The threshold 3.3 is C3's critical value, so its result reproduces the C3 statistic above. The cell-level z-scores at neighbouring thresholds are correlated (0.73 between 3.0 and 3.3; 0.74 between 3.3 and 3.6).

**Interpretation:** a genuine difference between the two stages' generating processes would be expected to appear at several neighbouring thresholds; it does not. The excess is confined to the single statistic that equals C3's decision rule. This is consistent with a chance excess in a statistic chosen in advance as the one of interest (C3's threshold), and also with a modest effect specific to the tail near the cutoff.

**[UNCERTAIN]:** the available data cannot distinguish these. **Chance is not proven to be the cause**, and no alternative cause has been identified. All artifact-type explanations that could be tested from saved data (arithmetic, normal approximation, within-cell or cross-cell dependence, seed reuse, whole-distribution drift) were excluded (section 3). Settling the question would require new, pre-registered simulation, which is outside the present authorisation.

## 7. Frontier cells reaching approximately 5.27–5.28%
**Calculated (C3, T4 shape D5, no dependence, day-factor sd 0.3):**

| Cell (validation row) | Market | Days | Stage 2 rate | Stage 3 rate | Stage 3 Wilson 95% | Stage 3 z |
|---|---|---|---|---|---|---|
| 72 | NSE | 125 | 5.116% | **5.268%** | 4.998%–5.552% | +0.77 |
| 74 | US | 125 | 5.116% | **5.276%** | 5.006%–5.560% | +0.81 |
| 50 | NSE | 59 | 5.248% | 4.868% | 4.608%–5.142% | −1.94 |
| 51 | US | 59 | 5.220% | 4.932% | 4.670%–5.207% | −1.47 |
In training, the cell that set the 125-day critical value (row 72) had an in-sample rate of 5.000% by construction (`stage2/c3_training/c3_training_cell_results.csv`).

**Interpretation:** at the cells that determine C3's critical values, the rejection rate in both stages is about 5.1% to 5.3%, i.e. about the nominal level, not clearly below it. The two 125-day Stage 3 intervals touch or exclude 5.0% at their lower end. C3 is conservative in most cells (median about 1.8% in Stage 3), but **it is not shown to be conservative in these cells**. The gate allows 6.0% in tier B, and these cells pass it (the highest Stage 3 tier B rate is 5.28%, 0.72 points below the limit). The accurate statement is that the observed rate stayed at or below 5.28% in every gated Stage 3 cell, **not** that C3 is a validated 5% test and **not** that it is conservative everywhere. The stage-to-stage differences in these cells are within sampling noise.

## 8. Effect on the Stage 5 classification
**PARTIAL remains unchanged.** Reasons [INTERPRETATION]: the extra variability is small (about 0.09 points of extra SD in the rate difference, against a binomial SD of 0.15 points) and the smallest margin to a gate is 0.72 points; no cell left its gate in either stage; the statistic behind every Stage 3 and Stage 4 gate (a rate against an upper limit) is unaffected by a variance of this size. The classification was already based on upper limits only, on a simulated domain, with real-data behaviour unverified; none of that changes. This note does not alter any result, gate, threshold, seed or acceptance criterion.

## 9. Limitations and remaining uncertainties
- The cause of the C3 excess (p = 0.0035) is unknown. Chance with post-hoc selection and a modest tail-specific effect near the cutoff are both compatible with the data; neither is proven.
- The chi-square reference assumes independent, standard-normal comparisons. Independence between cells was supported, but the p-value is an approximation (z² are only approximately chi-square) and the C3 and baseline sets are dependent.
- The variance-ratio interval (1.11–2.11) is approximate.
- The subgroup analyses are post hoc and underpowered (some cells have only two members).
- Only the 76 development cells that were re-run can be compared; the 20 new Stage 3 cells have no Stage 2 counterpart.
- This note only re-analyses the saved data; it does not repair the underlying gap that Stage 3's pass on re-run development cells carries less independent evidence than its 88-cell count suggests (the critical values were set from those same cells). That point is from the audit and is not resolved here.
- Nothing here shows that C3 is calibrated, universally or at 5%.

## 10. Implications for future real-data descriptive validation
(Not started and not authorised; recorded for the planning stage only.)
1. Descriptive validation should place the real data on the validated points using a rule written before looking at the data, and should not compute an H1 statistic on real data.
2. Real-data placement should not be summarised as "C3 is calibrated here". At best it can say whether the real tails and shapes lie near points where C3 stayed within its limits in simulation.
3. Because C3 is near nominal at the T4/D5 frontier and sample sizes other than 59, 90, 125, 180 and 250 days are not validated, any real data that fall near that frontier or at an unvalidated size should be flagged.
4. Any future replication of selected cells to resolve section 6 would need its own written authorisation, cell list, seed and decision rule before any run; this note authorises none.
5. The repeat variability does not by itself block descriptive validation.

**Files and evidence behind this note:** `outputs/milestone4/h1_calibration/stage2/development/cell_00..75.parquet`; `stage3/validation/cell_00..75.parquet`; `stage3/summary/stage3_vs_stage2_repeat.csv`; `stage2/c3_training/c3_training_cell_results.csv` and `c3_critical_values.csv`; `frozen_spec/cells_development.csv` and `cells_validation.csv`. Intermediate files from the analysis were kept outside the repository.
