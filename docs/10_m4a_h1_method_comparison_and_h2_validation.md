# M4a — H1 method comparison (RMS estimand) and H2 validation

**Status: simulation evidence only. Nothing here is market evidence. No method is selected or approved, the protocol is not frozen, no H1/H2/H3 test was run on real outcomes, H3 calibration has not started.**
Every number below is read from the saved output files listed in section 9. Rejection rates are shown with Wilson 95% intervals in brackets. A cell's interval "excluding 5%" means the simulation shows the true size is probably not 5%.

---

## 1. Completion and quality checks

| Check | Result |
|---|---|
| H1 run | finished; log ends `COMPLETE`; no error/traceback lines |
| H1 simulations | 14,400 in the per-simulation file = 2 markets × (10 null cells × 600 + 4 power cells × 300). 28 cells, 224 summary rows (28 × 8 methods). Every planned count reached. |
| H2 extra run | finished; log ends `COMPLETE`; no error lines |
| H2 extra simulations | 2,600 = NSE 2 worlds × 800 + US 2 worlds × 500. All present. 40 summary rows. |
| Seeds | H1 master 20261040, H2-extra master 20261041. Per-simulation seeds are saved (14,400 and 2,600 unique values; no overlap between the two runs). The first H2 run (master 20261032) did not save per-simulation seeds; its independence from run 2 rests on different master seeds (SeedSequence-spawned), which makes a collision negligible but is not checked value by value. |
| Bootstrap | B = 499 for H1 tests, wild B = 199 for H2 (see limitation L3) |
| Tests | 192 pass (180 earlier + 12 new for the H1 candidates) |
| Evidence preserved | earlier `h1/`, `h2/`, both `*_QUICK_PLUMBING_CHECK` folders, logs, `data/clean` (12 files), docs 01–09 untouched. One new derived file was added inside the new `h2_extra/` folder: `H2_pooled_true_null_size_run1_plus_run2.csv`. |

---

## 2. The methods and what they estimate

All use the same simulated markets (3 stocks × 59 days per market; the same bars go to every method).

| Method | What it is | Keeps the RMS estimand? |
|---|---|---|
| `orig` | Friedman on ln RMS of all bars (the rejected design) | Aims at it but the estimator is biased by bar count |
| `sub` | Friedman on equal-size random subsets of bars | **No** — estimates a typical (geometric-type) volatility |
| `lnrms_jk` | Friedman on bar-jackknife bias-corrected ln RMS | Intended to; see section 4 |
| `lnrms_an` | Friedman on analytically bias-corrected ln RMS, using −(κ−1)/(2n) with κ estimated | Intended to; see section 4 |
| `rom_pct` | day-bootstrap percentile interval for ln(mean r² ratio), Bonferroni over 3 contrasts | **Yes** (pooled variance ratio) |
| `rom_t` | same but bootstrap-t (studentised) | **Yes** |
| `rom_bca` | same but BCa | **Yes** |
| `diff_t` | bootstrap-t test of the linear contrast E[ms_a − ms_b] = 0 (no logarithm in the test) | **Yes** (pooled variance difference) |

Estimand detail for the four `rom_*`/`diff_t` methods: the target is the ratio of period variances **averaged over days, in levels**, so high-volatility days weigh more than quiet days. That is the "RMS volatility" of your decision, but it is not the same as the typical day's ratio. Whether that weighting is what you intend should be confirmed at review.

Unit of inference throughout: the trading day (59 per market); stocks are averaged within a day first.

---

## 3. Type I error, scenario by scenario (nulls: period RMS truly equal)

Cells show rejection rate [Wilson 95%], n = 600 per cell. Scenarios: D1 Gaussian flat; D2 t4 flat; T10, T6 = t10 / t6 with day factor; D3 t4 + day factor; D4 t4 + day factor + intraday regime + AR(0.1); R1/R2/R3 realistic within-period heterogeneity (open/close decay; max/min ratio inside a period 1.8, 2.5, 2.5 + midday U + regime); D5 the extreme stress case (about 33× inside a period).

### NSE
| | orig | sub | lnrms_jk | lnrms_an | rom_pct | rom_bca | rom_t | diff_t |
|---|---|---|---|---|---|---|---|---|
| D1 | .492 | .062 [.05,.08] | .065 [.05,.09] | .057 [.04,.08] | .067 [.05,.09] | .062 [.05,.08] | **.043 [.03,.06]** | **.047 [.03,.07]** |
| D2 | .925 | .062 | .163 [.14,.20] | .058 [.04,.08] | .103 [.08,.13] | .138 [.11,.17] | .063 [.05,.09] | .063 [.05,.09] |
| T10 | .617 | .048 | .050 | .058 | .065 [.05,.09] | .075 [.06,.10] | .043 [.03,.06] | .043 [.03,.06] |
| T6 | .772 | .047 | .062 | .033 [.02,.05] | .070 [.05,.09] | .103 [.08,.13] | .047 [.03,.07] | .042 [.03,.06] |
| D3 | .940 | .050 | .163 [.14,.20] | .068 [.05,.09] | .100 [.08,.13] | .125 [.10,.15] | .045 [.03,.06] | .050 [.04,.07] |
| D4 | .953 | .045 | .252 [.22,.29] | .032 [.02,.05] | .107 [.08,.13] | .148 [.12,.18] | .050 [.04,.07] | .048 [.03,.07] |
| R1 | .963 | .077 [.06,.10] | .167 [.14,.20] | .072 [.05,.10] | .105 [.08,.13] | .150 [.12,.18] | .057 [.04,.08] | .070 [.05,.09] |
| R2 | .995 | **.218 [.19,.25]** | .223 [.19,.26] | .087 [.07,.11] | .110 [.09,.14] | .158 [.13,.19] | .070 [.05,.09] | **.087 [.07,.11]** |
| R3 | .990 | **.192 [.16,.23]** | .293 [.26,.33] | .082 [.06,.11] | .110 [.09,.14] | .150 [.12,.18] | .063 [.05,.09] | .068 [.05,.09] |
| D5 | 1.00 | 1.00 | .063 [.05,.09] | **.762 [.73,.79]** | .158 [.13,.19] | .167 [.14,.20] | .110 [.09,.14] | .125 [.10,.15] |

### US
| | orig | sub | lnrms_jk | lnrms_an | rom_pct | rom_bca | rom_t | diff_t |
|---|---|---|---|---|---|---|---|---|
| D1 | .305 | .050 | .052 | .033 [.02,.05] | .068 [.05,.09] | .072 [.05,.10] | .040 [.03,.06] | .045 [.03,.06] |
| D2 | .770 | .045 | .140 [.11,.17] | .048 | .087 [.07,.11] | .125 [.10,.15] | .047 [.03,.07] | .042 [.03,.06] |
| T10 | .473 | .060 | .042 | .042 | .053 | .062 | .038 [.03,.06] | .045 |
| T6 | .598 | .065 | .080 [.06,.10] | .053 | .077 [.06,.10] | .095 [.07,.12] | .040 | .047 |
| D3 | .773 | .050 | .158 [.13,.19] | .050 | .108 [.09,.14] | .145 [.12,.18] | .068 [.05,.09] | .063 [.05,.09] |
| D4 | .800 | .073 | .220 [.19,.25] | .052 | .117 [.09,.14] | .153 [.13,.18] | .047 | .050 |
| R1 | .845 | .075 | .170 [.14,.20] | .040 | .125 [.10,.15] | .147 [.12,.18] | **.077 [.06,.10]** | **.085 [.07,.11]** |
| R2 | .942 | **.248 [.22,.28]** | .182 [.15,.21] | .097 [.08,.12] | .105 [.08,.13] | .135 [.11,.16] | .065 [.05,.09] | .070 [.05,.09] |
| R3 | .962 | **.253 [.22,.29]** | .275 [.24,.31] | **.107 [.08,.13]** | .093 [.07,.12] | .123 [.10,.15] | .063 [.05,.09] | .060 [.04,.08] |
| D5 | 1.00 | 1.00 | .058 [.04,.08] | **.907 [.88,.93]** | .160 [.13,.19] | .173 [.15,.21] | .093 [.07,.12] | .118 [.09,.15] |

### What each method does, by scenario (not averaged)
- **orig** — fails everywhere (30–99.5%), as established before.
- **sub** — controls size in D1–D4 and the tail scenarios, but **fails in the realistic scenarios R2/R3 (19–25%)** as well as D5 (100%). This is new evidence: its failure is not confined to the extreme stress case. Together with the estimand argument, it does not meet your requirement.
- **lnrms_jk** — the jackknife correction is not enough: it still has an average bias of −0.03 to −0.06 in log ratio, and size 14–29% in every fat-tailed scenario, 6% in D5. It looks fine only at Gaussian and t10.
- **lnrms_an** — good in D1–D4, T6, T10 (3–7%, a few cells at 3%, i.e. slightly conservative), mildly high in R2/R3 (up to 10.7%), but **collapses in D5 (76% NSE, 91% US)**. I have not established why (see section 6).
- **rom_pct / rom_bca** — over-reject in every fat-tailed scenario (percentile 6.5–12.5%, BCa 6–15%; D5 about 16–17%). BCa is worse than the percentile interval.
- **rom_t and diff_t** — much closer to nominal: outside D5, rom_t ranges 3.8–7.7% and diff_t 4.2–8.7%. Neither is clean:
  - cells whose interval excludes 5%: diff_t NSE R2 (8.7%) and US R1 (8.5%); rom_t US R1 (7.7%, lower bound just above 5%);
  - several other cells have a lower bound at 5–6%;
  - both are at 9–12.5% in the D5 stress world, where the null is true.
  Neither is shown to control size across the scenarios tested; they come closest of the RMS-preserving methods.

Also note sizes of 3–4.5% (rom_t D1, T10, T6, US D1) are slightly conservative, which costs power rather than inflating false positives.

---

## 4. Does each method estimate the right thing? (mean estimated open-vs-middle log ratio minus the true RMS value; true value is 0 under nulls)

| | orig | sub | lnrms_jk | lnrms_an | rom_*/diff_t |
|---|---|---|---|---|---|
| D1 (Gaussian) | −0.05 / −0.04 | 0.00 | +0.004 | −0.003 | +0.001 |
| D2–D4 (t4), NSE | −0.12 to −0.14 | 0 to −0.013 | −0.03 to −0.05 | +0.02 to +0.01 | −0.005 to −0.011 |
| R2, R3, NSE | −0.14, −0.16 | −0.023, −0.034 | −0.037, −0.060 | +0.008, 0.00 | −0.006, −0.019 |
| D5, NSE | −0.30 | −0.21 | −0.002 | −0.123 | −0.021 |

(Values for US are similar; the full table is in `H1_methods_size_and_power.csv`.)

- The ratio-of-means estimates are essentially unbiased (|bias| ≤ 0.02 in these scenarios; −0.02 to −0.03 in D5). So **their over-rejection is not caused by a biased estimate**; it is a problem with how uncertainty is calibrated.
- `sub` is nearly unbiased for the geometric-type target but its estimate of the **RMS** log ratio is off by 0.02–0.03 in R2/R3 and 0.2–0.27 in D5, confirming it is not an RMS estimator.
- `lnrms_an` removes the bias in D1–D4 and R but not in D5 (−0.12 to −0.16).
- Power rows: with open and close volatility ×1.1 the true log RMS ratio is ln 1.1 = 0.095 and the true log **variance** ratio is 0.19. The ratio-of-means methods report the log variance ratio, so against the saved RMS column they appear to be biased by +0.08 to +0.10 (and +0.17 at ×1.2). That is a units mismatch in the comparison, not an estimation error (their estimates are about 0.19 and 0.37 as they should be, i.e. close to twice the stored value). Null rows are unaffected (both are 0), and rejection rates are unaffected.

---

## 5. Power (rejection when open and close volatility are really higher than middle)

Volatility ×1.1 means variance ×1.21. n = 300 per cell. Power is only comparable between methods whose size is acceptable.

| scenario | market | rom_t | diff_t | rom_pct | rom_bca | lnrms_an | sub | orig |
|---|---|---|---|---|---|---|---|---|
| flat ×1.1 | NSE | .317 | .187 | .527 | .660 | .923 | .820 | .090 |
| flat ×1.1 | US | .413 | .337 | .600 | .687 | .933 | .883 | .073 |
| R1 ×1.1 | NSE | .263 | .163 | .477 | .610 | .870 | .700 | .090 |
| R1 ×1.1 | US | .337 | .220 | .547 | .633 | .860 | .727 | .057 |
| flat ×1.2 | NSE | .923 | .857 | .960 | .963 | 1.00 | 1.00 | .487 |
| flat ×1.2 | US | .960 | .927 | .973 | .973 | 1.00 | 1.00 | .897 |
| R1 ×1.2 | NSE | .893 | .773 | .957 | .960 | 1.00 | 1.00 | .370 |
| R1 ×1.2 | US | .900 | .867 | .950 | .950 | 1.00 | 1.00 | .790 |

Interpretation, separating power from size:
- The high powers of `lnrms_an` and `sub` cannot be credited: `lnrms_an` fails size in D5, and `sub` fails size in R2/R3 and D5 and changes the estimand. A test that rejects 76–100% in a stress null is also likely to reject for reasons other than the effect.
- `rom_pct`/`rom_bca` power is inflated by their size inflation.
- Among the better-calibrated methods, **power for a 10% volatility difference is modest** (rom_t 26–41%, diff_t 16–34%) and good only for a 20% difference (rom_t 89–96%, diff_t 77–93%). With 59 days this is a property of the data size, not a defect to be fixed by choice of test. `rom_t` has more power than `diff_t` in every cell here, although its size is not uniformly better (R-scenarios similar).
- `orig` has power of only 6–9% at ×1.1: its negative bias (−0.1) cancels much of a real effect — a second reason it is unusable.

---

## 6. Why does the ratio-of-means over-reject? Is it heavy tails?

Evidence (rom_pct / rom_bca / rom_t, NSE; US in parentheses for rom_pct):

| tails | rom_pct | rom_bca | rom_t |
|---|---|---|---|
| Gaussian (D1) | .067 (.068) | .062 | .043 |
| t10 (T10) | .065 (.053) | .075 | .043 |
| t6 (T6) | .070 (.077) | .103 | .047 |
| t4 (D3) | .100 (.108) | .125 | .045 |

What the data show:
1. The over-rejection of the percentile and BCa versions **rises as tails get heavier** (BCa NSE .062 → .075 → .103 → .125; the same direction in US). That is consistent with the heavy-tail explanation.
2. The estimate is not biased (section 4), so the problem is the interval/test calibration.
3. **Studentising removes it**: `rom_t` stays at 4–6% across all four tail settings in NSE, and `diff_t` (also bootstrap-t) behaves the same. A bootstrap-t corrects for a mis-estimated standard error, which is what heavy tails in r² would cause.
4. But heavy tails are **not the whole story**: with Gaussian returns (D1) the percentile and BCa versions are already at 6.2–7.2% (intervals mostly just above 5%). Small samples of 59 days, the skewness of the log ratio, and the use of a 0.83% tail quantile from only 499 bootstrap draws (Bonferroni over 3 contrasts, two-sided) probably contribute. I did not separate these.
5. Residual: even `rom_t` and `diff_t` over-reject somewhat in realistic heterogeneity (R1–R3) and clearly in D5 (9–12.5%), so heterogeneity inside periods is a second, separate issue.

**Conclusion: the heavy-tail explanation is supported (dose-response across t∞, t10, t6, t4, and removal by studentisation) but not proven.** I did not test the infinite-fourth-moment property itself (a t4 sample has finite sample kurtosis; there is no scenario with t3 or with finite-fourth-moment heavy tails that isolates that property), and the Gaussian result shows other causes exist.

The `lnrms_an` D5 failure: untested hypothesis — the correction assumes iid returns with one pooled κ, but in D5 returns within a period have very different variances, so the period-specific bias differs from the pooled formula. A second hypothesis: Friedman ranks ln-levels, whose day-level expectation differs from the log of the pooled variance when volatility varies within the period. Neither tested.

---

## 7. H2 additional true-null simulations

Same DGPs, models and estimators as the first H2 run. New master seed. TRUE NULL worlds only (volume independent of returns). Rejection rate at 5%, run 2 only first, then run 1 + run 2 pooled.

**Run 2 only** (NSE n = 800 per world, US n = 500):

| market | world | outcome | M0 clustered-t | M5 clustered-t | M5 wild | DFE clustered-t |
|---|---|---|---|---|---|---|
| NSE | A | vol | .049 | .048 | .044 [.03,.06] | .062 [.05,.08] |
| NSE | A | ret | .056 | .056 | .050 | .052 |
| NSE | F | vol | .054 | .050 | .049 | .055 |
| NSE | F | ret | .054 | .052 | .050 | .050 |
| US | A | vol | .066 [.05,.09] | .068 [.05,.09] | .062 [.04,.09] | .082 [.06,.11] |
| US | A | ret | .054 | .050 | .048 | .050 |
| US | F | vol | .064 | .060 | .054 | .052 |
| US | F | ret | .070 [.05,.10] | .070 | .058 | .068 |

**Pooled run 1 + run 2** (NSE n = 920, US n = 740; full table `H2_pooled_true_null_size_run1_plus_run2.csv`):

| market | world | outcome | M0 clustered-t | M5 clustered-t | **M5 wild** | DFE clustered-t |
|---|---|---|---|---|---|---|
| NSE | A | vol | .050 [.04,.07] | .048 [.04,.06] | **.045 [.03,.06]** | .064 [.05,.08] |
| NSE | A | ret | .055 | .055 | **.050 [.04,.07]** | .052 |
| NSE | F | vol | .052 | .049 | **.046 [.03,.06]** | .051 |
| NSE | F | ret | .052 | .051 | **.047 [.04,.06]** | .049 |
| US | A | vol | .066 [.05,.09] | **.073 [.06,.09]** | **.065 [.05,.09]** | **.081 [.06,.10]** |
| US | A | ret | .059 | .057 | **.053 [.04,.07]** | .057 |
| US | F | vol | .065 [.05,.09] | .059 | **.053 [.04,.07]** | .054 |
| US | F | ret | .065 [.05,.09] | .066 [.05,.09] | **.057 [.04,.08]** | .064 |

Findings:
- **NSE precision is resolved to about ±1.5 points** (it was about ±4). Every NSE cell for the leading candidate (M5, wild bootstrap) is 4.5–5.0%, intervals containing 5%. The original and +c3+c4 models with clustered-t are also 4.8–5.5%.
- **US is not perfectly clean.** With 740 pooled simulations, M5 with clustered-t shows 7.3% in world A / volatility (interval excludes 5%) and 6.6% for continuation in world F. The wild bootstrap reduces this (6.5% [4.9, 8.5]) and is compatible with 5%, but the upper end of the interval, 8.5%, cannot be ruled out. So the earlier suggestion that the wild bootstrap is needed is supported; I cannot claim it is exactly 5% in the US.
- The exploratory DFE model with clustered-t is the least well behaved (8.1% in US A/vol).
- This is size under **independent stocks** only; correlated stocks are not simulated (L5).

This supports keeping M5 with wild-bootstrap p-values as the **leading candidate**, interpreted as "predictive information beyond past measures". It does not select it. Power for H2 was not re-run (first run: 96–100% for forward vol ×1.1; 56–78% for continuation of 0.05 vol-units).

---

## 8. Limitations and unresolved issues

- **L1 No H1 method is shown to control size in every scenario.** The best candidates (`rom_t`, `diff_t`) are within about 3–9% outside the D5 stress case, with some cells excluding 5% and a clear failure (9–12.5%) in D5. I can't say whether D5-like heterogeneity occurs in real data. Real within-period profiles can be described from the M3 sample (not tested here to avoid mixing evidence).
- **L2 Precision:** n = 600 gives roughly ±1.8 points around 5%. Differences of 1–2 points between methods in a cell are not meaningful.
- **L3 Bootstrap resolution:** B = 499 with Bonferroni tails of 0.83% is coarse. Larger B, or a single max-statistic bootstrap instead of Bonferroni, may change sizes. Not tested.
- **L4 Simulated days are independent;** real volatility clusters across days. The earlier plan to check this with Ljung-Box on real difference series, and a day-block bootstrap, is not exercised here.
- **L5 Stocks are independent in the simulation.** Real stocks within a market are correlated, which reduces the effective sample and might worsen size.
- **L6 Estimand weighting:** the surviving candidates test a day-volatility-weighted pooled variance ratio, not the typical day. Needs your confirmation.
- **L7 No realistic-heterogeneity profile has been estimated from the real sample.** R1–R3 are plausible shapes I chose, not fitted ones.
- **L8 Simulated returns and volume** are not real. A simulation that shows good behaviour cannot show that the real data meet the assumptions, and none of this is evidence about NSE or US volatility.
- **L9** The saved `true_log_ratio_*_RMS` column is the RMS log ratio while the rom/diff estimates are log variance ratios (a factor of 2); this only matters for power rows (section 4). I did not add a corrected column to the saved file.
- H1 `sub`/`orig` are kept in the comparison only as references.

---

## 9. What the evidence supports (recommendations — not decisions)

1. **Retire** `orig`, `sub` (changes estimand and fails in realistic R2/R3) and `lnrms_jk` (under-corrects, 14–29% size).
2. **Do not use `lnrms_an`** unless its D5 failure is understood; its other results are good, but a method that rejects 76–91% in a true-null scenario cannot be called reliable.
3. **Studentised bootstrap on mean squares (`rom_t`, and the linear `diff_t`) are the leading RMS-preserving candidates.** They are better calibrated than percentile/BCa and unbiased; they are not yet shown to be adequate (sizes up to 8.7% in realistic scenarios, 9–12.5% in D5, power for a 10% effect 16–41%). The percentile and BCa versions should not be used.
4. Suggested next simulations if you approve: (a) larger B and a max-statistic (single bootstrap for all contrasts) instead of Bonferroni; (b) correlated stocks and day-to-day volatility clustering with a block bootstrap; (c) heterogeneity profiles estimated from the existing M3 sample, to decide whether D5-like or R-like is realistic; (d) a scenario isolating the finite-fourth-moment property (e.g. t3 vs a heavy-tailed distribution with finite fourth moment); (e) a diagnosis of the `lnrms_an` D5 failure. Estimating with confidence intervals (reporting the variance ratios and their intervals) instead of only a reject/not-reject decision is also an option for the report.
5. **H2:** keep M5 + wild bootstrap as the leading candidate. NSE size is now certified within roughly ±1.5 points. The US needs either more simulations or acceptance that size may be up to about 8%. Same-day fixed effects stay exploratory.

---

## 10. Reproducibility

- Python 3.12.13, numpy 2.5.4, pandas 3.1.0, scipy 1.18.1, statsmodels 0.15.0; macOS (Darwin 24.4.0), 8 cores; process-pool with `pool.map` (ordered).
- H1: `scripts/milestone4/run_h1_methods.py`, master seed 20261040, 600/300 sims, B = 499, 59 days, 3 stocks. Code: `src/quantlab/research/h1_rms.py`, tests `tests/test_research_h1_rms.py`.
- H2 extra: `scripts/milestone4/run_h2_extra_nulls.py`, master seed 20261041, NSE 800, US 500, wild B = 199.
- Outputs (relative to the project root):
  - `outputs/milestone4/diagnostics/h1_methods/{H1_methods_size_and_power.csv, H1_methods_per_simulation.csv, run_metadata.csv}`
  - `outputs/milestone4/diagnostics/h2_extra/{H2_extra_true_null_size.csv, H2_extra_per_simulation.csv, H2_pooled_true_null_size_run1_plus_run2.csv, run_metadata.csv}`
  - logs: `outputs/milestone4/diagnostics/h1_methods_run.log`, `h2_extra_run.log`
  - preserved plumbing checks: `h1_methods_QUICK_PLUMBING_CHECK/`, `h2_extra_QUICK_PLUMBING_CHECK/` (tiny runs; not results)
  - earlier outputs untouched: `h1/`, `h2/`, `docs/09_*`.
