# H1 Calibration — Stage 0 Report (preparation only)

**Status:** Stage 0 is complete. **No calibration experiment was run** (no null-rejection rate was estimated for any candidate), no Stage 1 or Stage 2 work was started, and H3, M5 and the protocol freeze were not touched. M1–M3, `data/clean`, the raw data and the M4b outputs are unchanged (section 9). All new work is in new files. Everything below is **simulated or descriptive**; nothing is an H1 test on real data.

Labels: **[VERIFIED]** computed or tested in this stage. **[ESTIMATE]** extrapolated from a measurement. **[RECALLED/UNVERIFIED]** from memory or a source I could not read. **[PROPOSED]** a design choice for you to approve.

---

## 1. What was done (against your authorisation list)

| Item | Done | Where |
|---|---|---|
| 1. Read-only inspection of the existing implementation | yes (section 2) | — |
| 2. Unit-test preparation and execution | yes: 22 new tests, full suite 243 passed (section 3) | `tests/test_research_h1_calibration.py`, `tests/test_research_tail_descriptives.py` |
| 3. Compute benchmark | yes (section 5) | `outputs/milestone4/h1_calibration/stage0/benchmark/` |
| 4. Draft and freeze the experimental specification | yes, as v1 with SHA-256 manifest (section 7) | `outputs/milestone4/h1_calibration/frozen_spec/` |
| 5. Descriptive real-data tail analysis | yes (section 6) | `outputs/milestone4/h1_calibration/stage0/real_data_descriptive/` |
| Threshold justification, sample sizes, Monte-Carlo uncertainty | yes (section 4) | `.../stage0/mc_precision/` |

New code (all new files, nothing existing edited): `src/quantlab/research/h1_calibration.py` (C1, C2, C3 and helpers), `src/quantlab/research/tail_descriptives.py`, and the scripts `stage0_benchmark.py`, `stage0_benchmark_parallel.py`, `stage0_mc_precision.py`, `stage0_mc_precision_n25k.py`, `stage0_real_data_descriptive.py`, `stage0_freeze_spec.py` in `scripts/milestone4/`.

---

## 2. Read-only inspection of the existing implementation  [VERIFIED]

- The test statistic is built in `h1_rms2.py`: the log ratio of period means with an influence-function standard error (`_influence`, `_se_blocks`); the days × 3 matrix and day resampling are in `h1_rms.py`, `inference.resample_days`. The new module **imports** these helpers and reproduces M4b's statistic exactly (a unit test compares its |t| with the existing `bootstrap_t` output to 1e-12), so the estimand and statistic are unchanged and only the source of the critical value differs.
- The fast generator (`direct_sim.py`) produces squared returns by stock × day × slot, which is exactly the bar-level input C1 needs; no change to it was required.
- M4b drew each simulation's seed as a 32-bit integer, which produced the 28 harmless cross-file coincidences. The new module provides `child_seeds`, giving each simulation a spawned `SeedSequence` that is passed straight to `default_rng` (full width; a unit test checks 20,000 children have distinct 256-bit states and are reproducible).
- Real cleaned data: 6 files, 60 dates, 4,460 (NSE) / 4,681 (US) bars per stock; usable returns have `status == ok` and period open / middle / close.

---

## 3. Implementation and unit tests

**Components [VERIFIED by tests]**

- **C1** `fit_bar_model` → `null_world_matrices` → `c1_test`. Model: squared return = slot profile × robust day scale (median over the day's bars) × standardised squared shock. The null is imposed by rescaling the profile inside each period so the period variances are equal; shocks are drawn jointly over the three stocks from the same period's empirical shocks; day scales are drawn from the observed ones. Decision: Monte-Carlo p = (1 + #{T\* ≥ T}) / (R + 1) ≤ 0.05 with R = 499 (so that 0.05·(R+1) is an integer).
- **C2** `fast_double_bootstrap`: one inner resample per outer resample.
- **C3** `c3_test`: reject when T exceeds a supplied fixed value.
- **Tail summaries** `tail_summary`, `hill_alpha` (descriptive).

**Tests: 22 new, all pass** (17 + 1 for the p-value + 4 tail tests). They check among others: the statistic equals M4b's; the slot shape is recovered (within 6% with 1,500 Gaussian days); standardised shocks have mean 1 inside each period; **the artificial worlds have equal period means (spread < 3%) even when the input data have period means differing by more than 1.5×** (null imposition works); the resampler refuses missing shocks; the fit tolerates missing bars; the C1 critical value matches a large independent null in a Gaussian world (within 8%); C1 and C2 are deterministic given a seed and reject clear violations; the C2 edge case "first-level p = 0" rejects with finite statistics; loose smoke bounds for null rejection (60 and 200 simulations: these are plumbing checks, **not calibration evidence**); Hill estimator recovers a Pareto tail index of 3 within 5%.

**Full suite:** `python -m pytest -q` → **243 passed, 0 failed, 0 skipped, 3 warnings** (the same three `h2_volume.py:157` warnings as before). Baseline was 221; 22 new tests.

**Limitations and open points about the candidates**

1. C1 draws day scales iid; day-to-day persistence is not reproduced. In M4b the estimated persistence changed H1 size little, but this is a modelling choice to validate.
2. C1 needs finite shocks (no missing bars). Real-data application would need a documented treatment of missing bars (only about 1% of used NSE bars are missing); not needed for simulations.
3. **C2 formula [RECALLED/UNVERIFIED].** I implemented the fast double bootstrap p-value from memory of Davidson and MacKinnon (2007) and could not read the paper (the pages I tried returned an error). A search result states the method needs the test statistic to be asymptotically independent of the random parts of the bootstrap data-generating process, and that it can perform poorly otherwise. That condition is plausibly violated here, because section 2.1 of docs/13 shows the statistic and the bootstrap critical value are dependent. So C2 may well fail; the plan still tests it, as you approved.
4. C1's slot profile and tail features are estimated from the same sample; the full pipeline (fit, calibrate, test) is run inside every simulation, so the estimation noise is included in the rejection rate.

---

## 4. Thresholds: statistical justification, sample sizes, Monte-Carlo uncertainty

Rejection rates are estimated by Wilson 95% intervals. All numbers below are exact binomial arithmetic (`stage0_mc_precision.py`, `stage0_mc_precision_n25k.py`); no simulation.

**4.1 Monte-Carlo uncertainty of one rate near 5%  [VERIFIED]**

| n simulations per cell | MC standard error (points) | Wilson 95% half-width (points) | 0.5-point band in SE units |
|---|---|---|---|
| 2,000 | 0.49 | 0.96 | 1.0 |
| 5,000 (M4b) | 0.31 | 0.60 | 1.6 |
| 10,000 | 0.22 | 0.43 | 2.3 |
| 20,000 | 0.154 | 0.30 | 3.2 |
| **25,000 (proposed)** | **0.138** | **0.27** | **3.6** |
| 40,000 | 0.109 | 0.21 | 4.6 |
| 100,000 | 0.069 | 0.14 | 7.3 |

**4.2 What each gate can and cannot resolve [VERIFIED]**

Probability that the gate passes, if the test's true rejection rate is p, at n = 25,000:

| True rate | 4.5% | 5.0% | 5.2% | 5.4% | 5.5% | 5.6% | 5.8% | 6.0% | 6.5% |
|---|---|---|---|---|---|---|---|---|---|
| Tier A pass probability | 0.50 | 1.00 | 0.98 | 0.76 | 0.51 | 0.25 | 0.02 | 0.0004 | 0.0000 |

| True rate | 3.8% | 4.0% | 5.0% | 5.8% | 6.0% | 6.2% | 6.5% |
|---|---|---|---|---|---|---|---|
| Tier B pass probability | 0.05 | 0.50 | 1.00 | 0.91 | 0.51 | 0.10 | 0.0006 |

Reading: a gate that uses the point estimate is **50% likely to pass a test whose true rate is exactly on the boundary** (5.5% for tier A, 6.0% for tier B). So tier A reliably certifies "true rate ≲ 5.2%" and reliably rejects "true rate ≳ 5.8%"; it cannot separate 5.0% from 5.4%. Anything finer than about ±0.3 points is unresolved by this design and I will say so in every result.

**4.3 Family-wise error and the number of simulations  [VERIFIED]**

Probability that at least one of K independent cells fails although every true rate is exactly 5.0% (tier A gate):

| n per cell | 1 cell | 96 cells |
|---|---|---|
| 10,000 | 2.1% | 86.3% |
| 20,000 | 0.11% | 10.2% |
| 40,000 | ≈0 | 0.04% |

The smallest n (multiples of 5,000) giving at least a 95% chance that all K cells pass at a true 5.0%: tier A: 20,000 for 24 cells, **25,000 for 48 or 96 cells**, 30,000 for 192 cells; tier B: 10,000 for all of these. So I set **25,000 per gated cell** (68 development cells; 10,000 for the report-only df 3 cells). With fewer than 25,000 simulations, tier A would reject a perfectly calibrated test about 10% of the time somewhere in the grid.

**4.4 Justification of the bands themselves**

- The tier A half-width of 0.5 points is a **judgement about practical materiality** (±10% relative to 5%), chosen because it is about 3.6 Monte-Carlo standard errors at 25,000 simulations: wide enough that a truly calibrated test is not rejected by noise, narrow enough that the M4b inflation (7–9%) fails clearly. It is not derived from a theorem.
- Tier B (stress) is wider because a fitted-parameter procedure in a hard world should be allowed a little slack: [4.0%, 6.0%].
- **Bradley (1978).** A search confirmed the reference (J. V. Bradley, "Robustness?", British Journal of Mathematical and Statistical Psychology 31, 144–152) and, through secondary sources, a "liberal" robustness band of 0.5α to 1.5α (2.5% to 7.5% at α = 5%). I could not read the original and could not confirm any "stringent" band such as 0.9α to 1.1α. **I do not cite Bradley for the tier bands** and the specification says so; the liberal band is mentioned only as context (it would allow every M4b-inflated cell below 7.5% to pass, which is why we do not use it).
- Gates are applied cell by cell, not on an average across cells, and not on "the interval includes 5%".
- Power is not a gate (as you instructed), and C3 is judged on the upper limits only (it is conservative by construction; its lowest cell rate is reported).

---

## 5. Compute benchmark  [VERIFIED timings; ESTIMATE extrapolations]

Single core, median of 20 null datasets, fast generator, NSE T4-like profile (timing only; no rejection rates were recorded):

| Task (seconds per dataset) | 59 days | 125 days | 250 days |
|---|---|---|---|
| Generate data | 0.0005 | 0.0010 | 0.0020 |
| Baseline bootstrap-t (M4b), B = 999 | 0.0014 | 0.0029 | 0.0063 |
| C2 fast double bootstrap, B = 999 | 0.0034 | 0.0070 | 0.0148 |
| C3 fixed critical value | ≈0 | ≈0 | ≈0 |
| C1 fit only | 0.0018 | 0.0033 | 0.0059 |
| C1 full test, R = 199 | 0.021 | 0.044 | 0.088 |
| **C1 full test, R = 499** | **0.049** | **0.104** | **0.210** |
| C1 full test, R = 999 | 0.095 | 0.211 | 0.421 |

C1 costs about 35 times the baseline bootstrap-t at R = 499. Parallel scaling on this machine (8 logical cores): a batch of 960 tests gave a speed-up of **4.2×** at 59 days and **3.8×** at 250 days (13.1 ms and 58.0 ms of wall time per test); a first small batch (64 tests) gave only 1.3× because process start-up dominated, which is why the larger measurement was added (`parallel_scaling_large_batch.csv`).

**Estimated wall-clock for the proposed program** (measured times ÷ 4.0; ±30%; generation of non-standard alternative DGPs not measured):

| Stage | Cells | Simulations | Estimated hours |
|---|---|---|---|
| Stage 1 mechanism diagnosis (baseline method only) | 68 | 1,240,000 | 0.2 |
| Stage 2 development, C1 + C2 + C3 + baseline on shared data, **full grid** | 76 | 1,780,000 | **11.7** |
| Stage 2 development, **reduced grid** (no 250-day cells) | 64 | 1,480,000 | 6.8 |
| Stage 3 validation, worst case (C1 selected), full grid | 96 | 2,280,000 | 13.3 |
| Stage 4 alternative DGPs (C1; assumes generation costs 3× more) | 12 | 300,000 | 3.1 |
| **Total, full program** | | | **≈ 28 hours** |

**Reduced-grid option and its limits.** Dropping the 250-day cells saves about 5 hours in Stage 2 and a similar share in Stage 3, but **sample-size behaviour would then be validated only up to 125 days**. Since the real samples have about 59 days and M4b showed inflation persisting at 250 days, the 250-day cells matter for the claim "more data does not fix it" but not for the 59-day question. A middle option is to keep 250 days for only tail T4 and shape E and D5 (4 cells instead of 12), saving about 3.5 hours; I have not generated that variant.

---

## 6. Descriptive real-data tail and shape analysis (data/clean, read-only)  [VERIFIED computations; descriptive only]

This is **not** an H1 test and compares no period variances. Each return was divided by a slot scale and a robust day scale (the same standardisation C1 uses), and tail summaries were computed. The same summaries were computed on **simulated worlds with known Student-t tails** (200 repetitions per degrees-of-freedom value, same layout and the real slot profile, no volatility clustering inside a day, no price rounding) so the observed numbers can be read against a reference. The Hill estimator is biased in samples of this size, so only the comparison with the reference is meaningful.

Observed (all periods pooled):

| | NSE | US |
|---|---|---|
| Standardised bars | 12,245 (3 stocks, 60 days, 71 used slots; 1% missing) | 13,777 (3 stocks, 60 days, 77 used slots; 0% missing) |
| Kurtosis | 7.40 | 4.57 |
| Hill tail index, top 1% / 2% / 5% / 10% | 3.94 / 3.91 / 3.64 / 3.24 | 5.18 / 4.85 / 4.26 / 3.55 |
| \|z\| > 4 per 1,000 | 4.1 | 2.0 |
| \|z\| > 5 per 1,000 | 1.1 | 0.4 |
| Largest \|z\| | 10.0 | 6.4 |
| SD of the log robust day scale | 0.64 | 0.51 |

Reference medians for known tails (NSE layout; US is nearly identical): kurtosis 14.3 (df 3), 8.5 (4), 6.4 (5), 5.3 (6), 4.5 (8), 4.1 (10), 3.5 (20), 3.2 (Gaussian); Hill top 5%: 2.75, 3.26, 3.60, 3.91, 4.27, 4.49, 5.02, 5.55; \|z\| > 4 per 1,000: 7.1, 5.0, 3.6, 2.7, 1.8, 1.3, 0.55, 0.23.

Which known-tail worlds have a 5%–95% range containing the observed value (pooled periods): **NSE: df 4 to 6** (kurtosis 4–5, Hill 4–6, exceedances 5–6); **US: df 6 to 8**. By period: NSE close **df 3 to 4** (kurtosis 20.7, outside every reference except df 3), NSE middle df 5–6, NSE open df 4–8; US close df 5–10, US middle df 6–8, US open df 8–10 and above (lighter).

How to read this [INTERPRETATION]:
1. The simulated T4 world is **not obviously unrealistic for NSE** pooled, and the NSE close period looks heavier still; the US sample looks closer to T6–T8. This is a statement about a 60-day standardised sample, **not** a conclusion about market return tails.
2. Several things besides Student-t shocks can fatten these tails: volatility clustering inside the day, price rounding, feed quirks (NSE closing window), the NSE closing-period outlier (largest \|z\| of 10 sits in the close), and the choice of day scale. The reference worlds contain none of these. A real tail index could therefore be lighter or heavier than the df-equivalents above.
3. The robust day-scale SD (0.5–0.64) is larger than the 0.3 used in M4b simulations, partly because it includes day-to-day variation of true volatility and partly sampling noise. Therefore the specification adds development cells with day-volatility SD 0.6.
4. Because the NSE close behaves like df 3 to 4, the report-only df 3 cells are informative for NSE. **Decision for you (section 10).**

Files: `real_tail_statistics.csv`, `reference_known_df_distribution.csv`, `observed_vs_reference.csv`, `df_equivalence_summary_all_periods.csv`, `run_metadata.csv`.

---

## 7. Frozen specification v1 and proposed experiment grid  [PROPOSED]

Location: `outputs/milestone4/h1_calibration/frozen_spec/` — `spec_v1.json` (rules), `cells_stage1.csv`, `cells_development.csv`, `cells_validation.csv`, `cells_alternative_dgps.csv`, `resource_estimate.csv`, and **`FROZEN_v1.sha256`** (SHA-256 of these files and of every code file the experiments depend on, 23 files). "Frozen" means: any change creates a numbered new version that you approve; the validation seed is recorded now and unused until Stage 3.

**Common rules.** Estimand and statistic unchanged; α = 0.05; 3 stocks per market. **All candidates and the M4b baseline are run on the same simulated dataset (same seed) in every simulation**, with the same cells, n and gates; cost is reported. Candidates: C1 (R = 499), C2 (B = 999), C3 (per-sample-size fixed value = the largest 95% quantile of T over the gated development cells, estimated from a separate training run with disjoint seeds, 25,000 per cell). No candidate is chosen on one scenario or on power; among candidates passing every gated cell, the simplest is chosen, with cost as tie-break. If no candidate passes, H1 remains unresolved.

**Gates** (provisional, per your approval; basis in section 4): tier A (df ∞, 10, 6, 7): point in [4.5%, 5.5%] and Wilson upper ≤ 6.0%; tier B (df 4, 5): point in [4.0%, 6.0%] and Wilson upper ≤ 6.5%; tier C (df 3): report only; no validated cell above 7.0%; alternative DGPs: point in [4.0%, 6.0%]; C3 on the upper limits only.

**Stage 1 grid (baseline method only; 20,000 per cell, 5,000 for the B comparison): 68 cells**
- HA tail scan: df ∈ {∞, 20, 10, 8, 6, 5, 4, 3} × shape ∈ {flat, E, D5} × market (48 cells).
- HB effective-bar test: T4 × shape {E, D5} × merging 1, 2 or 3 consecutive bars × market (12 cells).
- HE bootstrap size: T4 × {E, D5} × market × B ∈ {999, 9,999} (8 cells).
- Also saved per simulation: t, critical value, sample kurtosis and maximum day share (HC).

**Stage 2 development grid: 76 cells** (68 gated at 25,000 and 8 report-only df 3 cells at 10,000; 1,780,000 simulations)
- 59 days, no cross-stock dependence: tail {G, T10, T6, T4, T3} × shape {flat, E, D5, R2} × market {NSE, US} (40 cells).
- 59 days, estimated dependence: tail {T6, T4} × shape {E, D5} × market (8 cells).
- 59 days, day-volatility SD 0.6: T4 × {E, D5} × market (4 cells).
- 125 and 250 days: tail {G, T6, T4} × shape {E, D5} × market × days (24 cells).

**Stage 3 validation (fresh seeds, run once): 96 cells** = the 76 development cells plus 20 **new intermediate cells** not used in development: df {7, 5} × shape E at 59, 90, 180 days, and df {7, 5} × shapes D1.5 and D3.0 (decay scale between those used) at 59 days, both markets. Power cells (T4 flat ×1.1, ×1.2 and E ×1.2) at 5,000 are reported only after calibration passes.

**Stage 4 independent validation:** 6 alternative DGPs × 2 markets × 25,000 (12 cells): (a) intraday volatility clustering, (b) jumps, (c) period-specific tails (df 4 open/close, 8 middle), (d) stock-specific tails (df 3, 5, 8), (e) heavy-tailed day factor, (f) Laplace shocks; parameters are in `cells_alternative_dgps.csv`. Each must be normalised so that the period variances are equal in expectation (checked by a large-sample test before use). Plus: a reduced bar-level pipeline check, and an independent slow reference implementation compared on 100 inputs.

**Failure conditions, reproducibility and seed rules** are in `spec_v1.json` (as in docs/13, with the items you added: fresh validation seeds, no tuning on validation, H1 stays unresolved if nothing passes).

---

## 8. Plumbing indicator (not evidence)

On 40 simulated NSE T4-E-like datasets (59 days), the spread of C1's critical value was smaller than the baseline bootstrap-t's: coefficient of variation 0.057 for C1 against 0.222 for the baseline (means 2.69 and 2.82). With only 40 datasets this is a plumbing check that the code behaves as the hypothesis HC would predict; **it is not a result and must not be used to prefer C1**. It is in `plumbing_indicator_crit_spread.csv`. It says nothing about whether C1's rejection rate is near 5%, because that was deliberately not measured.

---

## 9. Integrity checks  [VERIFIED]

- Full test suite: **243 passed, 0 failed, 0 skipped**, 3 warnings (unchanged `h2_volume.py:157`).
- `data/clean`: **12 files**; no file under `data/` is newer than the docs/12 report.
- M4b outputs (`outputs/milestone4/m4b/`): **0 files newer than the docs/12 report**; docs/12 not edited; docs/13 not changed in this stage.
- Source files: only `h1_calibration.py` and `tail_descriptives.py` are new; no existing `.py` under `src/` is newer than docs/12 (checked), so M1–M3 and all M4 modules are untouched.
- The only background process was the single benchmark run (finished, log kept); no experiment queue exists.

New output folders (all new): `outputs/milestone4/h1_calibration/stage0/{benchmark,mc_precision,real_data_descriptive}`, `outputs/milestone4/h1_calibration/frozen_spec`, and `benchmark_run.log`.

---

## 10. Decisions and open points for your review

1. **Approve the frozen specification v1**, including the grids and the 25,000-simulation rule.
2. **Full or reduced grid.** Full ≈ 28 hours of compute in total; the reduced option removes the 250-day cells (saves roughly 10 hours across Stages 2–3) at the cost of validating sample-size behaviour only up to 125 days. A 4-cell 250-day compromise is also possible.
3. **Should df 3 become a gated tier for NSE?** Section 6 puts the NSE close period at df 3 to 4. Gating it would likely fail every candidate (squared returns then have a tail index of 1.5), which would be an honest "H1 is unresolved for NSE tails this heavy"; the current plan reports it without gating.
4. **C2's formula is unverified** (section 3). Please confirm that I may verify it from the original paper if it becomes accessible, or keep it as an implementation to be checked against a case with known behaviour in Stage 1.
5. **C1 model choices to confirm:** iid day scales (no persistence), median day scale, period-pooled shocks drawn jointly across stocks.
6. **Alternative DGP parameters** in `cells_alternative_dgps.csv` are my choices and should be confirmed before they are frozen into Stage 4.
7. **Descriptive tail results:** the day-scale SD of 0.5–0.64 led me to add 0.6 sensitivity cells; confirm.

I will not start Stage 1 or any candidate experiment until you approve.
