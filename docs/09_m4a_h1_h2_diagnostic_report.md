# M4a diagnostic report: H1 and H2 calibration failures

**Status: diagnostic only. No method is selected or frozen.** All numbers come from SIMULATED data (synthetic bars pushed through the real `clean()` and `build_bar_table()` code). No real-market outcome was read for any H1, H2 or H3 test. `docs/07_research_protocol.md` has not been written or frozen. The research sample, Milestones 1–3 and all diagnostic outputs are untouched.

## 0. Completion and quality of the runs

| Check | Result |
|---|---|
| Processes | H1 and H2 runs both finished; no run process remains |
| Marker | `ALLDONE` present in the H2 log |
| Errors | No traceback or error text in either log |
| H1 output rows | 54 = 2 markets × 9 scenarios × 3 methods (complete) |
| H2 output rows | size 168 = 2 markets × 6 worlds × 14 model/outcome/p-value rows; power 48 = 2 markets × 2 worlds × 6 effects × 2 models (complete) |
| Simulations completed | H1: 800 per null scenario, 400 per power scenario, per market. H2: 240 (US) and 120 (NSE) per world; 100 per power cell. Every cell reached its planned count (min = max in the saved tables). Nothing was dropped. |
| Seeds | Master seeds: H1 **20261031**, H2 **20261032**. Each simulation gets a seed spawned from its master via `numpy.random.SeedSequence(master).spawn(...)` in the main process, in a fixed order, so the full run is exactly reproducible by re-running the script. The individual per-simulation seeds are not written to disk. Only the master seed and counts are (`run_metadata.csv`). |
| Intervals | Wilson 95% intervals. I recomputed two cells independently: 120/240 gives [0.437, 0.563] and 0/100 gives [0.000, 0.037], matching the saved formula. I did not cross-check against a second library. |
| Monte Carlo uncertainty at a true 5% rate | ±1.5 pp (n = 800), ±2.1 pp (400), ±2.8 pp (240), ±3.9 pp (120), ±4.3 pp (100) as 95% half-widths. NSE H2 cells (n = 120) can only distinguish 5% from roughly 10%. |
| Disclosure | Before the full runs I deleted the outputs of two small plumbing ("--quick") runs and the stopped, unfinished full calibration (which had written no files). Their numbers were low-n and are not used here. Everything from the full runs is kept. |

## 1. H1: why the original test fails, and what the alternatives do

### 1.1 Cause of the failure (Part A and B, 200,000 and 20,000 replications)
The per-day statistic ln(root-mean-square return) is **biased low, and by an amount that depends on how many bars it uses**. True volatility = 1:

| Returns | n = 8 (NSE open) | n = 9 | n = 11 / 12 | n = 54 (middle) |
|---|---|---|---|---|
| Gaussian | −0.065 | −0.057 | −0.047 / −0.042 | −0.009 |
| Student-t, 10 df | −0.085 | −0.077 | −0.064 / −0.059 | −0.014 |
| Student-t, 4 df | −0.160 | −0.146 | −0.125 / −0.117 | −0.039 |

- Comparing an 8-bar period with a 54-bar period therefore builds in a gap of 0.056 (Gaussian) to 0.12 (fat tails), while the standard error of the 59-day average gap is only about 0.02.
- **Unequal sample size alone is the cause:** the original method rejects 29–48% of the time under Gaussian returns with flat volatility. Fat tails raise this to 79–91%.
- **Implementation is correct:** Friedman on iid 59×3 panels rejected 4.84% (CI 4.55–5.15%), and an independent permutation implementation agreed with scipy on 199 of 200 panels.
- **Dependence is not the cause:** adding a day factor, an intraday regime and AR(0.1) (D3, D4) leaves the original method at 77–95% rejection, about where fat tails alone put it (79–91%), while the same additions leave the subsampled method at 4–6%.

### 1.2 Methods compared (same simulated markets for all three)
- **orig**: ln RMS over all bars in each period, Friedman test (the original design).
- **sub**: ln RMS on equal-size random subsets (7 bars NSE, 9 bars US, 25 draws, seeded), Friedman test (the proposed fix).
- **rom**: ratio of average variances (all bars, no per-day logs), day-block bootstrap; reject if any of 3 contrasts' Bonferroni interval excludes 0 (an alternative that keeps the RMS meaning).

Data-generating processes (every one has equal true RMS volatility in all three periods, i.e. H0 true for an RMS estimand, except D5's geometric differences described below):

| ID | Definition |
|---|---|
| D1 | Gaussian returns, flat volatility |
| D2 | Student-t 4 df, flat volatility |
| D3 | t4 + day-level volatility factor (sd 0.3) |
| D4 | t4 + day factor + slowly moving intraday volatility regime (sd 0.25, φ 0.97) + AR(0.1) |
| D5 | **Stress:** t4 + day factor; period RMS equal, but volatility very uneven inside the open (decays by exp(−j/2)) and close (grows by exp(j/2)) periods |
| Power | open and close volatility ×1.05 / 1.1 / 1.2 / 1.5 relative to the middle (true ln ratio 0.049 / 0.095 / 0.182 / 0.405), D3-type market |

### 1.3 Type I error (rate, Wilson 95% CI; 800 simulations per cell)

| Scenario | Market | orig | sub | rom |
|---|---|---|---|---|
| D1 Gaussian, flat | NSE | 0.475 [0.441, 0.510] | **0.049** [0.036, 0.066] | 0.058 [0.043, 0.076] |
| | US | 0.290 [0.260, 0.322] | **0.054** [0.040, 0.072] | 0.059 [0.044, 0.077] |
| D2 fat tails | NSE | 0.914 [0.892, 0.931] | **0.040** [0.028, 0.056] | 0.094 [0.075, 0.116] |
| | US | 0.789 [0.759, 0.816] | **0.042** [0.031, 0.059] | 0.096 [0.078, 0.119] |
| D3 + day factor | NSE | 0.935 [0.916, 0.950] | **0.054** [0.040, 0.072] | 0.124 [0.103, 0.148] |
| | US | 0.768 [0.737, 0.795] | **0.054** [0.040, 0.072] | 0.086 [0.069, 0.108] |
| D4 + regime + AR | NSE | 0.950 [0.933, 0.963] | **0.051** [0.038, 0.069] | 0.104 [0.084, 0.127] |
| | US | 0.810 [0.781, 0.836] | **0.064** [0.049, 0.083] | 0.110 [0.090, 0.134] |
| D5 stress | NSE | 1.000 [0.995, 1.000] | **1.000** [0.995, 1.000] | 0.169 [0.144, 0.196] |
| | US | 1.000 [0.995, 1.000] | **1.000** [0.995, 1.000] | 0.148 [0.125, 0.174] |

### 1.4 Power (rejection rate, 95% CI; 400 simulations per cell; ratio is on volatility)

| Market | True ratio | orig (invalid size) | sub | rom |
|---|---|---|---|---|
| NSE | ×1.05 | 0.415 [0.368, 0.464] | 0.270 [0.229, 0.316] | 0.175 [0.141, 0.215] |
| | ×1.10 | 0.090 [0.066, 0.122] | **0.877** [0.842, 0.906] | 0.527 [0.479, 0.576] |
| | ×1.20 | 0.500 [0.451, 0.549] | 1.000 [0.990, 1.000] | 0.973 [0.951, 0.985] |
| | ×1.50 | 1.000 | 1.000 | 0.998 [0.986, 1.000] |
| US | ×1.05 | 0.158 [0.125, 0.196] | 0.343 [0.298, 0.390] | 0.233 [0.194, 0.276] |
| | ×1.10 | 0.062 [0.043, 0.091] | **0.910** [0.878, 0.934] | 0.642 [0.594, 0.688] |
| | ×1.20 | 0.855 [0.817, 0.886] | 1.000 [0.990, 1.000] | 0.960 [0.936, 0.975] |
| | ×1.50 | 1.000 | 1.000 | 0.998 [0.986, 1.000] |

The original method's "power" is meaningless: at ×1.05 and ×1.1 it rejects less than under the null, because its bias runs opposite to the true effect.

### 1.5 Estimated vs true log ratios (open vs middle, mean over simulations)

| Case | True ln ratio | orig | sub | rom (÷2, since rom reports ln of a VARIANCE ratio) |
|---|---|---|---|---|
| Flat nulls D1–D3 (NSE) | 0 | −0.056 / −0.120 / −0.119 | −0.000 / 0.000 / 0.001 | −0.001 / −0.002 / −0.004 |
| D4 (NSE) | 0 | −0.139 | −0.013 | −0.006 |
| ×1.05 / 1.1 / 1.2 / 1.5 (NSE) | 0.049 / 0.095 / 0.182 / 0.405 | −0.070 / −0.023 / 0.064 / 0.285 | 0.050 / 0.097 / 0.184 / 0.405 | 0.051 / 0.091 / 0.179 / 0.402 |
| D5 (NSE) | 0 (RMS), −0.94 (geometric) | −0.304 | −0.213 | −0.008 |

- **orig** is biased by −0.06 to −0.14, enough to reverse the sign of small effects.
- **sub** and **rom** are unbiased in the flat worlds and under the power alternatives (sub is essentially exact; rom after halving).

### 1.6 What D5 shows, and a caveat on how much it matters
- When RMS volatility is equal but concentrated differently inside a period, **sub rejects 100% of the time**, and its estimate (−0.21 to −0.31) does not equal the RMS ratio (0). So sub tests whether *typical (geometric-type) per-bar volatility* is equal, not whether *RMS volatility* is equal. **It changes the estimand.** It also discards information: each draw uses 7–9 of up to 54 bars.
- **rom keeps the RMS estimand** (D5 estimate −0.008 to −0.011 after halving) but its Type I error is inflated (8.6–12.4% in D2–D4, 14.8–16.9% in D5) and its power is clearly lower (e.g. 53–64% vs 88–91% at ×1.1). Its Bonferroni day-bootstrap interval is too narrow with 59 days and fat tails.
- **D5 is deliberately extreme** (volatility ratio of about 33× between the first and last bar of a period). Real opening periods are heterogeneous but milder. I did **not** simulate a realistic degree of heterogeneity, so the size of the sub mismatch under real conditions is unknown.

### 1.7 H1 verdict
- **Reject the original method.** It is invalid even for Gaussian returns, and biased.
- **Subsampling is statistically valid for its own estimand and the most powerful, but its estimand differs from "RMS volatility"**, and with strongly concentrated volatility it rejects when RMS volatility is equal.
- **Ratio-of-means preserves the RMS estimand but is not yet properly sized** (10–17% at a nominal 5%) and less powerful.
- Neither is ready to be frozen. Which one is defensible depends on a decision that is yours: whether H1's estimand is *RMS volatility* (the risk-relevant quantity, dominated by the most volatile bars) or *typical per-bar volatility* (less affected by a few bars). The EDA showed large opening-period effects (1.5–2.5×), so either test would almost certainly reject on real data. The choice mainly affects the **size of the ratio we report** and how defensible it is.

## 2. H2: what the simulations show

### 2.1 Correcting my own earlier diagnosis
I previously treated "volume and volatility share a day-level factor" as a null world and called the resulting rejections mis-sizing. **That was a mislabelling.** H2 asks whether volume carries information about later volatility or returns. If volume merely proxies a hidden volatility regime, volume *does* carry information, so rejecting is a correct detection. The simulations are therefore classified:
- **TRUE NULL**: volume independent of returns; returns may still have a day factor (A) or a day factor plus slow intraday regime (F). Rejection = Type I error.
- **SHARED REGIME**: volume loads on a hidden volatility regime (B day factor 0.8; C day factor + intraday regime, loadings 0.8; D intraday regime only, loading 1.0; E stress, day-factor sd 0.5, loading 1.5). Rejection = correct detection of information. It is **not** evidence that volume has an effect beyond the hidden regime, and it is not a Type I error.

### 2.2 Model configurations (seven; the first four are the main comparison)
All use stock×slot effects, day-clustered inference, and the next-open entry timing. Outcomes: forward volatility `y_fv_open` and continuation `g_open`.

| Model | Controls and effects | What it estimates |
|---|---|---|
| **M0 original** | c1 = \|r_t\| vs past norm; c2 = last-6-candle volatility vs past norm | Whether an event predicts later volatility beyond the event candle's size and the very recent volatility |
| **M1 + c3** | M0 + c3 = volatility so far today, vs its past norm | Same, also controlling for how active the day has been |
| **M5 + c3 + c4** (primary candidate) | M1 + c4 = previous day's volatility vs the recent norm | Same, also controlling for yesterday's volatility |
| **DFE same-day effects** | stock×**day** effects absorbed too, with c1, c2, c3 | Compares an event only with other candles of the same stock on the same day, so it removes day-level information. A different, "within-day" question. |
| S1 / S2 / S3 | c3_12 (last 12 candles) / c3_24 (last 24) / c4 only, instead of c3 | Sensitivity of the control definition |

Look-ahead: every control uses only candles up to and including the event candle (known when its volume is final), plus earlier days. Six leakage unit tests pass, including one that scrambles all later prices and volumes and confirms no feature at the decision time changes, and one confirming c4 ignores the current day.

### 2.3 Type I error in TRUE NULL worlds (volatility outcome; Wilson 95% CI; US n = 240, NSE n = 120)

| Model (p-value) | US A | US F | NSE A | NSE F |
|---|---|---|---|---|
| M0 original (CR1 t) | 0.067 [0.041, 0.106] | 0.067 [0.041, 0.106] | 0.058 [0.029, 0.116] | 0.042 [0.018, 0.094] |
| M1 + c3 | 0.079 [0.051, 0.120] | 0.058 [0.035, 0.096] | 0.050 [0.023, 0.105] | 0.042 [0.018, 0.094] |
| M5 + c3 + c4 (CR1 t) | 0.083 [0.055, 0.125] | 0.058 [0.035, 0.096] | 0.050 [0.023, 0.105] | 0.042 [0.018, 0.094] |
| **M5 (wild cluster bootstrap)** | 0.071 [0.045, 0.110] | **0.050** [0.029, 0.085] | 0.050 [0.023, 0.105] | 0.025 [0.009, 0.071] |
| DFE (CR1 t) | 0.079 [0.051, 0.120] | 0.058 [0.035, 0.096] | 0.075 [0.040, 0.136] | 0.025 [0.009, 0.071] |
| DFE (wild) | 0.058 [0.035, 0.096] | 0.050 [0.029, 0.085] | 0.058 [0.029, 0.116] | 0.017 [0.005, 0.059] |
| S1 / S2 / S3 | 0.062–0.067 | 0.067 | 0.042–0.067 | 0.042–0.050 |

- **Every model, including the original, has acceptable size in both true-null worlds, with three exceptions that are mild:** the day-clustered t for M1, M5 and DFE in US world A (7.9%, 8.3% and 7.9%; lower interval bounds 5.1–5.5%, just above 5%). The earlier "mis-sizing" of M0 does not exist (M0: 6.7%, interval includes 5%).
- The wild cluster bootstrap brings those cells to 5.8–7.1%, with intervals including 5%. NSE intervals are too wide to separate 5% from about 10%.
- Continuation outcome, all worlds (TRUE NULL and SHARED REGIME): rejection rates 1.7–8.3% for every model (all CIs include 5%). A shared regime does **not** create false continuation.

### 2.4 SHARED REGIME worlds (volatility outcome; these are detections, not Type I errors)

| Model | B (day) | C (day + intraday) | D (intraday only) | E (stress) |
|---|---|---|---|---|
| M0, M1, M5, S1, S2, S3 (no day effects), both markets | 99.2–100% | 100% | 100% | 100% |
| DFE (US, CR1) | 0.046 [0.026, 0.080] | **0.912** [0.870, 0.942] | **1.000** [0.984, 1.000] | 0.042 [0.023, 0.075] |
| DFE (NSE, CR1) | 0.042 [0.018, 0.094] | 0.900 [0.833, 0.942] | 1.000 [0.969, 1.000] | 0.025 [0.009, 0.071] |

- The mean coefficient on the event shows what is going on: M0 0.18–0.41, M5 0.12–0.23, DFE ≈ 0 in B and E but 0.07–0.13 in C and D. The extra controls absorb part of the regime but not enough to change any decision.
- **The same-day effects (DFE) remove day-level information but not intraday-regime information**, so my proposed fix does not isolate a "pure" volume effect either.
- **The control definitions (c3, c3_12, c3_24, c4) make no difference to any rejection.** In shared-regime worlds every one rejects; in true nulls every one has about 5%.

### 2.5 Power for genuine injected effects (US and NSE, 100 simulations per cell; CI shown for the US)

| True effect | World F (true null otherwise) M5 | World F DFE | World C (shared regime) M5 | World C DFE |
|---|---|---|---|---|
| Forward volatility ×1.10 for 3 candles | 0.98 [0.93, 0.99] | 0.99 [0.95, 1.00] | 1.00 | 1.00 |
| ×1.25, ×1.50 | 1.00 | 1.00 | 1.00 | 1.00 |
| Continuation 0.05 vol-units/candle | 0.64 [0.54, 0.73] | 0.65 [0.55, 0.74] | 0.74 [0.65, 0.82] | 0.75 [0.66, 0.82] |
| Continuation 0.10 | 0.99 [0.95, 1.00] | 0.98 [0.93, 0.99] | 1.00 | 1.00 |
| Continuation 0.20 | 1.00 | 1.00 | 1.00 | 1.00 |

NSE numbers are within 0.02–0.09 of these (e.g. continuation 0.05: 0.57 and 0.56 in world F). The estimated coefficient for volatility is essentially unbiased in world F (true ln 1.1 = 0.095 → 0.096; 1.25 → 0.227 vs 0.223; 1.5 → 0.422 vs 0.405). **In the shared-regime world C the estimate is inflated** (0.277 vs 0.095 for M5; DFE 0.174), so an effect size from real data cannot be read as volume's own incremental effect.

### 2.6 Does the simulation match its intended DGPs?
Yes, on every check I could make from the saved outputs:
- True-null worlds: mean volatility coefficient −0.004 to 0.001 (≈0); shared-regime worlds: positive and ordered by loading strength (E > D ≈ C > B).
- Injected volatility effects are recovered at ln(multiplier); injected continuation effects at about 1.7–2.4 bps per 0.05 vol-units.
- Continuation coefficient in non-injected worlds: −0.1 to 0.12 bps, i.e. zero.
- Not checked: that simulated volume distributions resemble real ones (that would need a comparison with the real volume series, which I deliberately did not make), and cross-stock correlation (simulated stocks are independent).

## 3. Statistical interpretation

### What we learned
1. **H1.** Comparing periods by ln RMS over all bars is invalid when periods have different bar counts, even for Gaussian returns. Equalising the number of bars removes that problem. The remaining issue is not statistical noise but a **choice of estimand**: RMS volatility versus typical per-bar volatility. These coincide only when volatility is spread evenly inside each period.
2. **H2.** There was no size problem to fix. Under true nulls the original controls-based model has acceptable size (a wild cluster bootstrap is slightly better than the clustered t). What looked like a failure was volume carrying real information through a hidden volatility regime. That is a correct detection, and it means the volatility test **cannot separate "volume has its own effect" from "volume tracks the volatility regime"**, whatever controls are used. Continuation is unaffected by this.
3. **Controls.** c3, c3_12, c3_24 and c4 all behave the same; extra controls absorb part of the regime bias in the coefficient but never change a rejection decision.

### Defensible vs rejected
- **Rejected:** original H1 (invalid size, biased); the day-fixed-effects "fix" as a size correction (not needed, and it changes the question and still fails under intraday regimes).
- **Defensible with stated limits:** H1 subsampling (valid size, unbiased, powerful; but estimates a different quantity than RMS volatility and is fooled by concentration); H1 ratio-of-means (right estimand and unbiased, but over-rejects 9–17% and is less powerful); H2 controls-based model with wild-bootstrap p-values, **interpreted as "predictive information beyond the listed past measures", not as a causal or incremental volume effect**; H2 continuation test.
- **Exploratory only:** the day-effects model (a "within-day" question).

### What remains uncertain
- Which H1 estimand you want, and how large the sub-vs-RMS mismatch is for realistic (milder) within-period heterogeneity.
- Whether a properly sized RMS-based test exists with 59 days and fat tails (rom's size problem is unsolved).
- Real volume behaves differently from the simulated lognormal volume, real events are not exactly "injected" effects, and the stocks in a market are correlated; none of this is simulated.
- The H2 power numbers are for strong injected effects. Real effects may be smaller.
- NSE H2 Type I error cannot be confirmed tighter than about ±4 pp with 120 simulations.

### Are more simulations needed before choosing?
**Yes.**
1. H1: a realistic-heterogeneity scenario (volatility decaying by roughly 2–3× across the opening period, not 33×) to size the estimand mismatch.
2. H1: an improved ratio-of-means test (e.g. studentised bootstrap or block bootstrap) and its size, because the current one over-rejects.
3. H2: more simulations in the true-null worlds (for example 1,000 per market) to confirm size to about ±1.5 pp and to compare clustered t with the wild bootstrap.
4. H2: one world with correlated stocks.
5. H3 calibration is still to be run (not started, as you instructed).

## 4. Files

All paths are relative to `/Users/pravin/Quantlab`.

| Purpose | Path |
|---|---|
| H1 bias by sample size (Part A) | `outputs/milestone4/diagnostics/h1/A_ln_rms_bias_by_sample_size.csv` |
| H1 Friedman implementation check (Part B) | `outputs/milestone4/diagnostics/h1/B_friedman_implementation_check.csv` |
| H1 size and power by method | `outputs/milestone4/diagnostics/h1/C_size_and_power_by_method.csv` |
| H1 run metadata | `outputs/milestone4/diagnostics/h1/run_metadata.csv` |
| H2 size by model and world | `outputs/milestone4/diagnostics/h2/size_by_model_and_dgp.csv` |
| H2 power | `outputs/milestone4/diagnostics/h2/power_proposed_model.csv` |
| H2 run metadata | `outputs/milestone4/diagnostics/h2/run_metadata.csv` |
| Scripts | `scripts/milestone4/run_diagnostics_h1.py`, `scripts/milestone4/run_diagnostics_h2.py` |
| Code | `src/quantlab/research/` (`inference.py`, `panel.py`, `nulls.py`, `h1_volatility.py`, `h2_volume.py`, `h3_serial.py`) |
| Tests | `tests/test_research_*.py` (including `test_research_leakage.py`) |
| Earlier M4a outputs | `outputs/milestone4/feasibility/`, `outputs/milestone4/revision/`, `docs/07_test_registry.csv` |
