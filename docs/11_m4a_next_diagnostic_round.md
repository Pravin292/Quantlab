# M4a — next diagnostic round (H1 calibration, dependence, D5 diagnosis, H2 US)

**Everything below is synthetic simulation or descriptive counting. No H1/H2/H3 test was run on real market outcomes. The research protocol is not frozen. H3 has not been started. The working H1 estimand is RMS volatility (day-volatility-weighted pooled variance ratio), a diagnostic choice, not a protocol decision.**

## 0. Protocol file is absent

`docs/07_research_protocol.md` **does not exist** — it was never written. The only protocol-related file is `docs/07_test_registry.csv` (the pre-specified list of tests). Docs 09 and 10 are *diagnostic reports*; they are the available references for the current findings, and they are **not** evidence that a complete protocol was drafted, reviewed or frozen. Nothing here depends on, or substitutes for, a frozen protocol.

---

## 1. Evidence tiers (kept separate)

### 1a. Verified implementation properties
- **Simulator unchanged when the new hooks are unused: 54 / 54 exact matches.** The pre-edit `simulate_raw` was rebuilt in memory by reverting the three added code fragments; both versions were run with identical seeds over 9 option combinations × 2 markets × 3 seeds and compared with `DataFrame.equals` (no tolerance). Script: `scripts/milestone4/verify_simulator_unchanged.py`; result: `outputs/milestone4/next_round/verification/simulator_unchanged_check.csv`.
- **Job completion and counts** (section 2): every planned cell reached its planned count; no errors in any log; no skipped cells.
- **Block-resampling construction** (section 4): consecutive-day blocks, each day's cross-section kept together (verified by a test, not just argued).
- Data untouched: `data/clean` still has 12 files, `data/manifest.csv` present, docs 01–10 and earlier outputs not modified.

### 1b. Unit-test evidence
- Full suite: **205 passed, 0 failed** (3 warnings, pre-existing). 192 before + 13 new in `tests/test_research_dependence.py`.
- New tests cover: default-simulator hashes (2 configs), day-factor SD / lag-1 autocorrelation / cross-stock correlation, return-correlation and t-tails of the shared-shock generator, equal-RMS shaped profile and multiplier, cross-stock structure of a simulated market, bootstrap-t detects a difference and returns both rules, max rule not grossly liberal, block SE reduces to iid SE for block = 1 and is larger for persistent series, jackknife output present only for `rom`, and block resampling (consecutive days within blocks; a day's three values travel together).
- Unit tests show the code does what it says. They are **not** evidence of statistical calibration.

### 1c. Statistical calibration evidence
Sections 5–9. Simulation only, independent stocks unless stated, 59 days, 3 stocks per market.

### 1d. Remaining assumptions and limitations
Section 11.

---

## 2. Job verification and counts

| Batch | Planned | Present | Log |
|---|---|---|---|
| H1 calibration (`h1_calib`) | 2 markets × (9 null cells × 1000 + 3 power cells × 300) = 19,800 sims; 24 cells; 288 summary rows (× 2 tests × 3 B × 2 rules) | 19,800 sims, 288 rows, 19,800 unique seeds | ends `COMPLETE`, no error |
| H1 dependence (`h1_dep`) | 2 × (5 × 800 + 2 × 300) = 9,200; 14 cells; 112 rows | 9,200, 112, 9,200 unique seeds | `COMPLETE` |
| H1 D5 diagnosis (`h1_d5`) | 2 × 6 × 600 = 7,200; 12 cells | 7,200 | `COMPLETE` |
| H2 US (`h2_us`) | 2 worlds × 1500 = 3,000 | 3,000 (1500 per world), no NaN | `COMPLETE` |
| H2 dependence (`h2_dep`) | 2 markets × 3 settings × 500 = 3,000 | 3,000 (500 per cell), no NaN | `COMPLETE` |
| Block-gap diagnostic | 2 markets × 2 scenarios × 600 = 2,400 | 2,400 | `COMPLETE` |

- **Failures / skipped cells: none.** No days were dropped by the pipeline in any completed batch (see section 4).
- **Process incident (disclosed):** the automatic launcher intended to start the gap diagnostic after the other batches used a `pgrep` pattern that also matched its own command line, so it never advanced. I stopped that waiter (reported as exit 144 — my kill, not a job failure) and started the gap diagnostic directly after verifying the other batches had completed. No simulation was interrupted or rerun.
- **Seeds:** master seeds 20261050 (calibration), 20261051 (dependence), 20261052 (D5), 20261053 (H2 US), 20261054 (H2 dependence), 20261060 (gap diagnostic); per-simulation seeds saved in every `*_per_simulation.csv`. Independent of earlier runs (different master seeds).
- **Environment:** Python 3.12.13, numpy 2.5.4, pandas 3.1.0, scipy 1.18.1, statsmodels 0.15.0; macOS Darwin 24.4.0, 8 cores.
- **Plumbing checks kept:** `h1_calib/dep/d5_QUICK_PLUMBING_CHECK`, `h2_us/dep_QUICK_PLUMBING_CHECK` (tiny runs, not results).

---

## 3. How the synthetic dependence is implemented, and where each input comes from

### Implementation (`src/quantlab/research/dependence.py`, hooks in `nulls.py`)
- **Across-day volatility persistence.** Each stock s has a day log-volatility factor
  `L[s,d] = sd · ( √share · F[d] + √(1−share) · E[s,d] )`, where `F` (shared) and each `E[s]` (idiosyncratic) are independent unit-variance stationary AR(1) series with coefficient `phi`. So every stock's day-factor has SD `sd` and lag-1 autocorrelation `phi`, and two stocks' day factors have correlation `share`. The factor multiplies that day's volatility (`exp(L)`) for all of a stock's bars.
- **Cross-stock return correlation.** All stocks share a Gaussian shock matrix `Z[day, slot]`. Each stock's Gaussian shock is `√c·Z + √(1−c)·own`, then divided by an *independent* chi-square mixing variable so that each stock's marginal returns remain Student-t(4). Independent mixing shrinks the Pearson correlation, so the Gaussian-core `c` is chosen by `core_corr_for_pearson` to hit a target Pearson correlation (e.g. target 0.355 → core 0.452). Verified in a test (target 0.4 reproduced within 0.06).
- No tail dependence beyond what the shared Gaussian core and the shared day factor imply. Volume is independent of returns in all of these runs (true-null H2 world F).
- Unchanged-when-unused property: section 1a.

### Which inputs are estimated and which are assumed
| Input | Value | Source |
|---|---|---|
| Within-period shape (open/close decay amplitude b, scale τ in `1 + b·exp(−j/τ)`) | NSE open b = 2.03, τ = 2.06; NSE close b = 4.58, τ = 0.36; US open b = 5.70, τ = 3.37; US close b = 3.17, τ = 1.23 | **Estimated descriptively** from the 6-stock cleaned sample (`describe_next_round.py`; only the shape *within* each period, no between-period comparison). Fits are rough: NSE close residual 0.34 in logs and τ < 1 bar (essentially one spike bar). The raw max/min of slot SD (1.7–3.1) is inflated by noise, the fitted ratio is 1.7–2.4. |
| Cross-stock Pearson correlation of standardised returns | NSE 0.355, US 0.187 | **Estimated** (mean over the 3 pairs per market) |
| Cross-stock correlation of day log-volatility (`share`) | NSE 0.454, US 0.141 | **Estimated** (pairwise range NSE 0.31–0.57, US −0.02–0.29) |
| Lag-1 autocorrelation of day log-volatility (`phi`) | NSE 0.441, US 0.190 | **Estimated** from ~59 days; SE about 0.13 per stock — imprecise |
| Day-volatility SD | 0.30 | **Illustrative**, kept from earlier rounds; the sample value (NSE 0.31, US 0.24) includes estimation noise so it overstates the true factor SD |
| Return distribution t(4), intraday regime SD 0.25, AR(0.1) in R3 | | **Illustrative** (carried over) |
| Strong dependence X4: corr 0.5, share 0.7, phi 0.7 | | **Illustrative stress values**, not observed |
| R1–R3, D5 shapes | | **Illustrative** (from earlier rounds / the scan) |
| "E" empirical-shape profile | the fitted shape above | **Estimated shape**, smooth parametric fit, period RMS set equal so the null is true |

These are modelling devices. They are not market facts.

---

## 4. Block bootstrap: resampling unit, construction, and gap exposure

- **Unit:** the trading day, as one row of the market matrix (period mean-squares already averaged over the 3 stocks). Each row holds that day's three period values.
- **Cross-stock dependence is preserved by construction**: stocks are averaged within a day *before* resampling, so a resampled day carries all stocks' same-day values together (tested). Cross-day dependence is preserved only *within* blocks.
- **Block construction ("as run", `resample_days(block=5)`):** 12 start positions drawn uniformly from the allowed starts of the market matrix; each takes 5 consecutive rows; the 12 blocks are concatenated and cut to 59 rows. Moving (overlapping) blocks. The studentising SE uses non-overlapping blocks of 5 in the observed order (59 → 11 full blocks; the last 4 days are not used for the SE).
- **Gap issue:** rows are consecutive *rows*, not necessarily consecutive trading days — a day dropped for incomplete coverage creates a gap that a block can silently span.

### Gap diagnostic results
| Question | Result |
|---|---|
| Completed simulation batches that dropped any day | **0 of 29,000** (calibration 19,800 + dependence 9,200; `n_days_used` = 59 in every simulation). So **0 bootstrap samples were affected** in any reported run. |
| Real cleaned sample (coverage counting only, no test) | NSE: 60 trading dates, 59 kept; the single dropped date is the **last** one (position 59), so no interior gap. US: 60 of 60 kept. **0 of 55 / 56 windows span a gap**; 0% of bootstrap samples affected. |
| Why no gaps in simulation | Simulated bars have no random missing data; the NSE feed quirks hit only the closing window, which is outside the three periods. |
| Sensitivity experiment (simulated, 2,400 sims; X3 and X4; both markets): randomly remove 0 / 4 / 8 days | With 4 days removed: **25%** of 5-row windows span a gap, **94.8%** of bootstrap samples contain ≥ 1 gap-spanning block; with 8 removed: 45% and 99.7%. |
| Does handling matter? "ignore" (as run) vs "aware" (blocks only from truly consecutive days; SE blocks within runs) | 0 days removed: agree (rom Bonferroni 7.4% vs 7.0%; 44 of 2,400 sims differ). 4 removed: ignore 8.0% vs aware 5.3% (rom), 7.3% vs 5.0% (diff). 8 removed: 6.8% vs 3.9% and 6.4% vs 3.8%. |

Interpretation: for the present sample (no interior gaps) the issue has **no effect**. If a sample did have gaps, the as-run method would be somewhat liberal and the gap-aware version noticeably conservative (3–4% at 8 days removed, partly because fewer days and fewer valid blocks remain). A 2–3 point sensitivity is comparable to this study's precision, so a gap-handling rule would need deciding and validating before use on any gapped sample. The gap-aware variant itself is untested beyond this experiment. Treated as a documented limitation, not a driver of the conclusions.

---

## 5. Task A — calibration of `rom_t` and `diff_t`: bootstrap size, and Bonferroni versus max-|t|

Setup: market matrix of mean squares; bootstrap-t for three contrasts; B = 199 / 499 / 1999 computed on identical datasets; two multiplicity rules: **Bonferroni** (each contrast at α/3) and **max** (one critical value for max |t| over the three contrasts). n = 1000 per null cell, 300 per power cell. Wilson 95% intervals; a Monte Carlo SE near 5% with n = 1000 is about 0.7 points (interval ± 1.4).

### 5.1 Type I error (B = 1999), rejection rate (Wilson 95% intervals for every cell are in the CSV)
| Scenario | rom Bonf NSE | rom max NSE | rom Bonf US | rom max US | diff Bonf NSE | diff max NSE | diff Bonf US | diff max US |
|---|---|---|---|---|---|---|---|---|
| D1 Gaussian flat | .039 | .047 | .040 | .045 | .039 | .047 | .042 | .048 |
| D2 t4 flat | .060 | .062 | .052 | .049 | .063 | .064 | .056 | .049 |
| T6 | .060 | .053 | .043 | .050 | .057 | .059 | .043 | .048 |
| D3 t4 + day factor | .063 | .063 | .049 | .054 | .066 | .058 | .044 | .049 |
| R1 | .052 | .052 | .057 | .054 | .063 | .055 | .059 | .051 |
| R2 | .089 | .082 | .060 | .061 | .092 | .085 | .063 | .056 |
| R3 | .070 | .068 | .063 | .061 | .079 | .072 | .062 | .059 |
| **E empirical-shape** | **.095** | **.085** | **.079** | **.069** | **.125** | **.106** | **.094** | **.079** |
| D5 stress | .109 | .091 | .097 | .078 | .136 | .105 | .124 | .096 |

(Intervals for these cells are about ±1.4–2 points; all cell-level intervals are in `h1_calib_size_and_power.csv`.) Number of the 18 null cells whose interval excludes 5%: rom Bonferroni 6, rom max 6, diff Bonferroni 7, diff max 7.

### 5.2 Effect of the number of bootstrap replications
Bonferroni rejection falls as B grows, max much less: e.g. NSE D3 rom Bonferroni .077 (B = 199) → .064 (499) → .063 (1999); NSE E rom .108 → .099 → .095; diff on E .129 → .132 → .125. Intervals excluding 5% (Bonferroni, 18 cells): B = 199: 14 (rom) and 14 (diff); B = 499: 7 and 8; B = 1999: 6 and 7. So B = 199 is clearly inadequate for the α/3 tails (a 1.7% tail from 199 draws is about 3 draws), B = 499 is borderline, and B = 1999 is stable (changes from 499 are within about 1 point). **Computational trade-off:** B = 1999 costs about 4× B = 499 for the bootstrap step; since table simulation and cleaning dominate the cost per simulated dataset here, the whole job grew only modestly, and for a single real dataset B = 1999–9999 is trivial.

### 5.3 Bonferroni versus max-|t| — Type I error **and** power (paired on identical datasets, B = 1999)
- **Type I error:** the max rule is slightly lower on average (rom 6.2% vs 6.5%; diff 6.6% vs 7.3% across the 18 null cells). Paired differences: Bonferroni significantly higher (|z| > 2) in 3 of 18 cells for rom and 6 of 18 for diff; max significantly higher in 2 cells each. The gap is largest in the worst cells (D5 diff: .136 vs .105; E diff: .125 vs .106). The max rule does not repair the miscalibration; it reduces it by 0–3 points.
- **Power** (300 sims per cell; Monte Carlo SE about 2.5–3 points, paired differences SE 1.2–2.6):

| Scenario (market) | rom Bonf | rom max | diff Bonf | diff max |
|---|---|---|---|---|
| flat ×1.1 (NSE) | .277 | .293 | .167 | .187 |
| flat ×1.1 (US) | .440 | .457 | .333 | .353 |
| E-shape ×1.1 (NSE) | .117 | .103 | .057 | .040 |
| E-shape ×1.1 (US) | .177 | .177 | .077 | .070 |
| E-shape ×1.2 (NSE) | .703 | .630 | .523 | .420 |
| E-shape ×1.2 (US) | .747 | .707 | .590 | .523 |

  Where power is low (flat ×1.1) the max rule is about 2 points higher, within noise (paired SE ≈ 1.6). Where power is substantial (E ×1.2) the max rule loses 4–10 points (paired z ≈ 2–4 in 4 of the 12 cells). **Bonferroni's extra power is bought partly by its larger size**, so the comparison is not a free advantage for either rule.
- **Power is low where it matters:** with the empirical-shape profile a 10% volatility increase in open and close is detected only 4–18% of the time (≈ the size level, i.e. essentially undetectable), and even a 20% increase 42–75%. That is a property of 59 days and heterogeneous, heavy-tailed bars, not of the choice of rule.

### 5.4 What this shows
- The tests are **not calibrated**: under the empirically-shaped profile (E), rejection is 7–13% (for the max rule the interval lies entirely above 5% in all four market/test cells), and D5 is worse. In flat or mildly heterogeneous settings (D1–R1, T6, D3) rom_t is within about 4–7%; `diff_t` is slightly worse. "The interval contains 5%" is not what I'm using as the criterion — several cells with intervals touching 5% still sit at 6%.
- The empirically-shaped profile is more demanding than the invented R1–R3. A likely cause is the sharp NSE closing spike (τ ≈ 0.4 bars), an untested hypothesis.

---

## 6. Task B — cross-stock correlation and volatility clustering (H1)

Profile: empirical-shape E, t4. Settings per market: **X0** independent; **X1** cross-stock correlation + shared day factor (estimated values); **X2** volatility persistence only (estimated phi); **X3** both (estimated); **X4** illustrative strong (0.5 / 0.7 / 0.7). B = 999. "iid" = ordinary day bootstrap; "blk5" = block bootstrap with blocks of 5 days (gap-free in these runs). 800 sims per cell.

### Type I error (Bonferroni; max in parentheses)
| | NSE rom iid | NSE rom blk5 | NSE diff iid | NSE diff blk5 | US rom iid | US rom blk5 | US diff iid | US diff blk5 |
|---|---|---|---|---|---|---|---|---|
| X0 independent | .094 (.084) | .072 (.064) | .107 (.094) | .086 (.075) | .061 (.062) | .066 (.054) | .083 (.065) | .064 (.059) |
| X1 cross-stock | .101 (.089) | .071 (.064) | .116 (.100) | .087 (.079) | .076 (.069) | .055 (.048) | .087 (.074) | .055 (.045) |
| X2 persistence | .099 (.087) | .074 (.070) | .115 (.096) | .081 (.072) | .069 (.060) | .064 (.054) | .077 (.070) | .065 (.051) |
| X3 both | .094 (.084) | .079 (.062) | .134 (.109) | .083 (.077) | .090 (.081) | .055 (.052) | .094 (.081) | .066 (.051) |
| X4 strong | .081 (.070) | .075 (.064) | .102 (.084) | .070 (.065) | .075 (.065) | .061 (.060) | .084 (.071) | .055 (.050) |

Findings:
1. **Dependence has little effect on the size of the iid-day test.** X1–X4 are within about ±3 points of X0 (X3 US rom .090 vs .061 is the largest, +2.9 points with Monte Carlo interval about ±2; weak evidence of inflation). The strong illustrative case X4 is *not* worse than X0. A plausible reason — not separately tested — is that the statistic is a within-day ratio of periods, so a day factor and its persistence cancel largely. The over-rejection in these scenarios is mostly the empirical-shape/heavy-tail effect already seen in X0 (and in section 5).
2. **The block bootstrap lowers size in NSE (by about 2–4 points, even in X0 where there is no clustering; in US the change is −3 to +0.5 points) but costs power:** X3 ×1.2 NSE rom Bonferroni .673 (iid) → .487 (blk5), US .767 → .623; diff .420 → .330 and .533 → .417. At ×1.1 power is 3–15% either way. With only 11 blocks the SE is noisy; I did not tune the block length.
3. Cross-stock correlation is preserved in the bootstrap (section 4). Neither version is validated as *calibrated*; blk5 is closer to 5% but sits at 5–9% (NSE).

---

## 7. Task D — why do the methods fail in D5?

D5 = equal period RMS, with volatility decaying as `exp(−j/2)` inside the open (mirrored in the close), t(4) returns, day factor. Scan: τ = flat, 8, 5, 3.5, 2 (= D5), and a Gaussian D5 (df = 1000). 600 sims per cell. All figures from `h1_d5_diagnosis.csv`.

### 7.1 Analytic bias correction (`lnrms_an`)
| | NSE open−middle | NSE close−middle | US open−middle |
|---|---|---|---|
| Raw ln-level bias (simulated) | −0.304 | −0.306 | −0.306 |
| True bias from a separate Monte Carlo of the same profile | −0.305 | −0.304 | −0.303 |
| Left after the analytic correction | −0.124 | −0.149 | −0.162 |
| Jackknife correction leaves | −0.002 | +0.004 | +0.015 |
| Friedman rejection (raw → analytic) | 100% → 79% | | 100% → 92% |

- The estimator bias is **real and fully accounted for** (simulated = Monte Carlo truth to ±0.005).
- The analytic correction removes only about half in D5 and under-corrects more as heterogeneity grows (Friedman rejection after correction: flat 6%/3%; τ = 8: 7%/9%; τ = 5: 9%/21%; τ = 3.5: 28%/51%; τ = 2: 79%/92%; NSE/US).
- **Mechanism, supported by arithmetic and by the Gaussian cell:** the correction assumes the n bars have equal variance and uses (κ−1)/(2n). When bar variances differ, the relative variance of the period mean square is (κ−1)·Σv²/(Σv)², not (κ−1)/n. For the D5 open period (8 bars) Σv²/(Σv)² = 0.46 versus 1/n = 0.125, i.e. the period behaves like about 2.2 bars, not 8, so the correction is too small by about 3.7× (`h1_d5_analytic_bias_arithmetic.csv`). A second-order Gaussian formula gives −0.22 for open−middle against −0.195 observed in the Gaussian D5 cell — close, not exact. In the **Gaussian** D5 cell (no tail issue) the corrected Friedman still rejects 72% / 78%, so heterogeneity alone is sufficient. This is a mechanism supported by two consistent checks, not a complete proof (no run with an oracle weighted correction).
- The jackknife nearly removes this bias in D5 (it makes no equal-variance assumption), but it under-corrects in the flat t4 case (−0.035 left) and over-corrects in Gaussian D5 (+0.09), and was already shown not to control size in the previous round.

### 7.2 `rom_t` and `diff_t`
Per-contrast rejection (nominal 1.67% each under Bonferroni) and ingredients, NSE open−middle, τ = 2: 

| | rom_t | diff_t |
|---|---|---|
| Bias / SD of the estimate | −0.08 | +0.01 |
| Mean SE ÷ true SD of the estimate | 0.80 | 0.75 |
| Bootstrap critical value vs. the true quantile of \|t\| | 3.21 vs 3.58 | 3.49 vs 3.76 |
| Rejection as run | 6.5% | 7.8% |
| Rejection if bias removed | 5.7% | 8.2% |
| Rejection using the jackknife estimate (rom) | 6.2% | — |

(US τ = 2 open−middle: rom 6.2% as run, 4.5% bias removed; SE ratio 0.81; critical value 3.21 vs 3.53.)

- **Not an estimator-bias problem:** bias is small relative to its SD (|bias/SD| ≤ 0.16), removing it or using the jackknife changes rejection by about 1–2 points (rom) or not at all (diff).
- **Variance estimation and the bootstrap tail:** the delta-method SE is about 20–25% too small in the strongest-heterogeneity cells, and the bootstrap critical value falls below the simulated quantile in the same cells. Both push toward over-rejection. With a Gaussian D5 both ratios are ≈ 0.95–1.0 and rejection is 5.8% / 4.8% (rom, any contrast) and 5.5% / 4.7% (diff).
- **So the failure needs heavy tails *and* strong heterogeneity together.** Heterogeneity alone (Gaussian D5) is fine; heavy tails alone with moderate shape are modest; both together break calibration of the variance estimate. "Any contrast" rejection with τ: NSE rom 7.0 (flat), 6.3, 5.8, 10.0, 10.8 (τ = 2); US 5.0, 5.7, 8.7, 7.0, 11.2. The path is noisy (±2 points at n = 600); I can't locate a threshold.
- Not tested: whether a different variance estimator (e.g. a bias-aware or Edgeworth-corrected one) would fix it.

---

## 8. Task E — H2, US calibration (TRUE-NULL worlds only)

World A = day factor in returns, volume independent. World F = day factor + intraday regime, volume independent. Independent stocks. 1500 new simulations per world, combined with the earlier independent runs (240 + 500) for 2240 per world. Model M5 = c1 c2 c3 c4 (the leading candidate); p-values clustered-t or wild cluster bootstrap (B = 199).

| World / outcome | M5 clustered-t, new 1500 | M5 **wild**, new 1500 | M5 **wild**, pooled 2240 | M5 clustered-t, pooled 2240 | M0 clustered-t, pooled |
|---|---|---|---|---|---|
| A volatility | .047 [.037,.059] | .047 [.037,.059] | **.053 [.044,.063]** | .055 [.047,.066] | .056 [.047,.066] |
| A continuation | .057 [.047,.070] | .050 [.040,.062] | **.051 [.043,.061]** | .057 [.048,.068] | .058 [.049,.068] |
| F volatility | .048 [.038,.060] | .043 [.034,.055] | **.046 [.038,.056]** | .052 [.043,.062] | .057 [.048,.067] |
| F continuation | .057 [.047,.070] | .051 [.041,.064] | **.053 [.045,.063]** | .060 [.051,.071] | .061 [.052,.071] |

- The earlier US excess (a 6.5% wild-bootstrap cell) is not reproduced with 1500 fresh simulations per world; it is consistent with Monte Carlo noise in the earlier n = 240–740 samples.
- **M5 with the wild bootstrap: 4.3–5.3% in every US cell**, all intervals contain 5%; with the pooled counts, any true size above about 6.5% is excluded, and any below about 3.8% too. This is evidence of no *detectable* size distortion at ±1 point, not proof of exactly 5%.
- Clustered-t is slightly liberal for continuation (5.7–6.0%, lower interval bounds 4.7–5.1%), another reason to prefer the wild bootstrap.
- Rejection by number of events (quartiles, 823–1045 events; 49 event-days): 3.6–5.9%, no pattern; so no structural event-count explanation for any US/NSE difference was found.
- Exploratory DFE (same-day effects) wild: 4.3–5.7%. Its interpretation remains different (within-day question) and exploratory.
- **Shared-regime worlds are not mixed in here.** They test a different question (volume as a proxy for a hidden volatility regime); results from the first diagnostic (doc 09) stand and were not rerun.

### H2 under cross-stock dependence and volatility clustering (world F, 500 per cell)
M5 wild-bootstrap rejection: NSE X0 .044–.054, X3 (estimated parameters) .036, X4 (strong illustrative) .046; US X0 .034–.042, X3 .048–.052, X4 .038–.052. All between 3.4% and 5.4% (intervals ±2 points), none above 5.4%. The NSE X3 volatility cell is conservative (M5 3.6–4.0%, DFE 2.6–3.2%). Day-clustering in the regression absorbs same-day cross-stock dependence; across-day persistence at the tested strength did not inflate size. **Precision here is ±2 points per cell**, enough to rule out gross distortion, not 1–2 point ones.

NSE (pooled earlier): 920 per world with M5 wild 4.5–5.0% in all four cells (doc 10); unchanged.

---

## 9. H1 method comparison (this round; RMS estimand)

| Method | Evidence this round | Verdict |
|---|---|---|
| `rom_t` (Bonferroni, B ≥ 1999) | 4–6% in Gaussian, t6, day-factor and R1 cells; 6–9% in R2/R3; **8–10% with the empirical shape (7–10% for the max rule); ~10% in D5** | Best of the tested RMS-preserving methods; **not calibrated** |
| `rom_t` / `diff_t` max-|t| rule | 0–3 points lower size than Bonferroni, 4–10 points less power at ×1.2 | Modest size gain, real power cost |
| `diff_t` | similar to `rom_t`, 1–3 points worse in size, ~half the power at ×1.1 | Dominated by `rom_t` here |
| Block bootstrap (5 days) | lower size, much lower power; no gain from dependence | Not shown to be needed |
| B | 199 inadequate; 499 borderline; ≥ 1999 stable | Use ≥ 1999 in any later run |
| `lnrms_an` | fails D5 (79–92%) via equal-variance assumption | Not usable under strong within-period heterogeneity |
| Round-1 `sub`, `orig`, `lnrms_jk`, percentile/BCa | unchanged (not rerun) | Remain rejected |

---

## 10. Status table

| Component | Status | Evidence | Remaining issue |
|---|---|---|---|
| H1 calibration | **Not calibrated** (best candidates: `rom_t`, max rule, B ≥ 1999) | 5.1: 4–7% in simple cells, 7–10% (rom) and 8–13% (diff) with empirical shape, ~10–14% D5; CI excludes 5% in 6–7 of 18 null cells | Size 7–13% under the empirically shaped profile; power 4–18% at a 10% effect; no RMS-preserving method meets 5% |
| H1 D5 diagnosis | Mechanisms identified, partly supported | 7.1–7.2: analytic correction under-corrects because bar variances are unequal (arithmetic + Gaussian cell); `rom_t`/`diff_t`: SE 20–25% too small and critical value too small when heavy tails × strong heterogeneity, bias minor | No oracle-weighted-correction run; no alternative variance estimator tested; threshold of heterogeneity unknown |
| Dependence simulations | Done; weak effect on size | Section 6: X1–X4 within about ±3 points of X0; block bootstrap lowers size and power | Estimates are imprecise (59 days); strong persistence not tested beyond 0.7; empirical-shape size problem is in X0 itself |
| H2 NSE | No detectable size distortion in true-null worlds (independent and dependent) | doc 10 (920/world, 4.5–5.0%); section 8 dependence cells 3.6–5.4% | ±1.5 points (pooled), ±2 (dependence cells); power not rerun this round |
| H2 US | No detectable size distortion at ±1 point (M5 wild) | Section 8: 2240/world, 4.3–5.3%; clustered-t slightly liberal for continuation | Not proven exact 5%; power not rerun; shared-regime interpretation unchanged |
| H3 | **Paused** | not started | — |
| Protocol freeze | **Not approved** | `docs/07_research_protocol.md` does not exist | Nothing frozen |

---

## 11. Limitations and unresolved issues

1. **No H1 method is calibrated.** The size problem is concentrated where the within-period shape is realistic (the empirical profile) and returns are heavy-tailed; this is the realistic case.
2. **The empirical-shape cause is untested.** The NSE close is fitted as essentially one spike bar (τ = 0.36, poor fit); I did not isolate that from the open shape.
3. **The dependence parameters are imprecise**, from ~59 days and 3 stocks per market (φ SE ≈ 0.13), and a three-stock average treats the market as a three-stock average.
4. **Only a few dependence structures were explored**; no time-varying correlations, no tail dependence, no cross-market effects.
5. **Estimand scope:** the working estimand weights high-volatility days more; no check was made of what a typical-day estimand would show in this round.
6. **Bootstrap-t critical values at α/3 or α with B = 1999** are adequate here; larger B was not tried.
7. **Gap handling:** no effect on the present sample, but sensitive (2–3 points) if gaps exist (section 4); the gap-aware variant is untested beyond this experiment.
8. **H2 power was not re-estimated** under the new dependence structures or for US specifically; the earlier power results (doc 09) apply only to the earlier design.
9. **Simulation ≠ market.** None of this is evidence about NSE or US volatility or volume, and none of it can show that real data satisfy the assumptions (real volume distributions, real correlation structure, any look-ahead issues in real feeds).
10. The round-1 saved column `true_log_ratio_*_RMS` vs the log-variance units remains as documented in doc 10; the new outputs avoid this by reporting only rejection rates for the bootstrap tests.

## 12. Recommended next steps (not executed)

1. Isolate why the empirical-shape profile inflates size (e.g. vary only the NSE close spike τ and amplitude; add bar-level heterogeneity of the open period) before choosing any H1 inference.
2. Try variance estimators that handle heavy tails and heterogeneous bars without changing the estimand (e.g. a studentiser built from bar-level influence functions, or a larger-B/BCa-on-t hybrid), and re-run the empirical-shape, D5 and dependence scenarios at B ≥ 1999.
3. Decide whether H1 should be reported primarily as **estimates with intervals** (open/middle/close variance ratios), with the omnibus rejection secondary, given the low power at a 10% effect.
4. Fix the gap-handling rule (require complete trading days, or the gap-aware blocks) before it could matter.
5. For H2, re-estimate power under the dependence settings, and keep M5 + wild bootstrap as the leading candidate; no more US size simulations seem necessary.
6. Only after your review: draft `docs/07_research_protocol.md` (it does not exist) — no real-data tests before it is reviewed and frozen by you.

---

## 13. Files

**New source and tests:** `src/quantlab/research/dependence.py`, `src/quantlab/research/h1_rms2.py`, `tests/test_research_dependence.py` (13 tests).
**Modified:** `src/quantlab/research/nulls.py` (three optional arguments `day_factor`, `common_z`, `shock_corr`; defaults reproduce the previous output exactly — 54/54).
**New scripts (`scripts/milestone4/`):** `describe_next_round.py`, `run_h1_next.py`, `run_h2_next.py`, `diagnose_block_gaps.py`, `summarise_bonf_vs_max.py`, `verify_simulator_unchanged.py`.
**New outputs (`outputs/milestone4/next_round/`):** `descriptive/`, `h1_calib/`, `h1_dep/`, `h1_d5/`, `h2_us/`, `h2_dep/`, `block_gap_diagnostic/`, `verification/`, the `*_QUICK_PLUMBING_CHECK` folders, and the run logs.
**Unchanged:** M1–M3 code and outputs, `data/` (raw, clean, manifests), docs 01–10, earlier diagnostic outputs.
