# H1 Calibration Investigation — Diagnosis, Option Comparison and Proposed Plan

**Status: PROPOSAL. Nothing in this plan has been executed.** No experiment was run, no source file, dataset or existing output was modified, M1–M3 were not touched, H3 and M5 were not started. The M4b results (`docs/12_...`, `outputs/milestone4/m4b/`) stay as the untouched diagnostic baseline.

The only analysis behind this document is a **read-only re-analysis of per-simulation results that M4b had already saved** (`h1_diag_per_simulation.parquet`, `h1_diag_factor_isolation.csv`, `h1_leverage_*`). It involved no new simulation. I describe it in section 2.1 so it can be repeated.

**Labels:** **[VERIFIED]** = computed from saved M4b outputs. **[REASONING]** = statistical argument that follows from the design, not tested here. **[HYPOTHESIS]** = plausible, needs an experiment. **[PROPOSED]** = a design choice for you to approve or change.

`docs/07_research_protocol.md` is still absent. Nothing here freezes a protocol.

---

## 1. Starting point (baseline, unchanged)

H1 estimand (unchanged): day-volatility-weighted pooled RMS variance ratio between open, middle and close. Tests use the days × 3 market matrix of period mean squares; statistic = largest absolute studentised log-ratio over the 3 contrasts; critical value from a bootstrap-t (days or blocks of 5 rows resampled).

[VERIFIED, docs/12] Rejection under the true null: about 5% for Gaussian shocks or flat within-period variance, and 7–9% (59 days), 6–9% (250 days) when Student-t shocks with 4 degrees of freedom (T4) combine with uneven within-period variance shapes (E, D5). Jackknife-t, wild bootstrap and empirical likelihood were equal or worse. No method was calibrated.

---

## 2. Phase 1 — Diagnosis

### 2.1 A correction to the working explanation  [VERIFIED]

docs/12 said "the bootstrap critical value is too small" because the **oracle** critical value (the 95% quantile of the statistic in the simulated null) restores 5.0%. That is true of the **typical** bootstrap critical value, but the mean tells a different story. Re-analysis of the saved diagnostic runs (8,000 simulations per cell, B = 999, `rom_t`, max rule; "median/mean crit" = bootstrap critical value over the 8,000 simulations; "oracle" = fixed constant that gives exactly 5%):

| Market | Scenario | Rejection % | Oracle | Median crit | Mean crit | Crit SD / mean | Spearman(max\|t\|, crit) |
|---|---|---|---|---|---|---|---|
| NSE | G E | 5.4 | 2.51 | 2.49 | 2.52 | 0.07 | −0.06 |
| NSE | T4 flat | 5.1 | 2.63 | 2.63 | 2.96 | 0.41 | −0.07 |
| NSE | T4 E | 7.5 | 2.95 | 2.78 | 3.17 | 0.40 | −0.16 |
| NSE | T4 D5 | 8.2 | 3.06 | 2.82 | 3.21 | 0.40 | −0.20 |
| US | G E | 5.4 | 2.51 | 2.49 | 2.52 | 0.06 | −0.07 |
| US | T4 flat | 4.3 | 2.56 | 2.62 | 2.91 | 0.36 | −0.06 |
| US | T4 E | 7.1 | 2.83 | 2.73 | 3.12 | 0.43 | −0.17 |
| US | T4 D5 | 8.1 | 3.02 | 2.81 | 3.22 | 0.41 | −0.18 |

Rejection rate within each quartile of the bootstrap critical value (lowest to highest), NSE T4 E: 16.8 / 9.4 / 3.4 / 0.4 %, with mean critical values 2.49 / 2.67 / 2.96 / 4.56. NSE T4 D5: 21.0 / 8.5 / 2.9 / 0.5 %, mean crit 2.51 / 2.70 / 3.01 / 4.61. NSE G E: 8.5 / 6.2 / 5.2 / 1.8 %.

What this establishes:

1. **The bootstrap critical value is not systematically too small. It is too variable, and wrong in the wrong samples.** With heavy tails its coefficient of variation is about 0.40, against 0.06–0.07 for Gaussian shocks. In one quarter of the samples it is about 2.5, which is what a Gaussian world would give, whereas the true 95% point of the statistic in these worlds is 2.8–3.1. Those are exactly the samples where rejection reaches 15–21%.
2. **The mean critical value exceeds the oracle** (3.17 vs 2.95) only because of a long right tail (top quartile mean 4.6). Those large critical values occur in samples where \|t\| is rarely large (rejection 0.4%), so they buy no protection.
3. **|t| and the critical value are negatively associated** in the inflated cells (Spearman −0.16 to −0.20) and much less so in the calibrated ones (−0.06 to −0.07). This is the signature of a studentised statistic that is not pivotal and a bootstrap that cannot repair it.
4. **The median critical value is 3.5–8% below the oracle in the inflated cells** (NSE T4 E 2.78 vs 2.95; D5 2.82 vs 3.06; US D5 2.81 vs 3.02) and equal to it in T4 flat (2.63 vs 2.63; 2.62 vs 2.56).
5. **"T4 flat is calibrated" is a marginal statement that hides conditional miscalibration.** Its critical value is equally variable (CV 0.41) and its lowest-crit quartile rejects 9.9% while the highest rejects 0.2%; it averages to 5%. I should not have implied more than "marginally near 5%".

Procedure (repeatable, read-only): for each cell take `max(|rom_t0|,|rom_t1|,|rom_t2|)` and `rom_critmax` from `h1_diag_per_simulation.parquet`; reject when the first exceeds the second; take medians, means, SD/mean, Spearman correlation and quartiles of `rom_critmax`. No file was written. docs/12 is not edited; this section is the erratum to its wording in sections 1 and 4.1.

### 2.2 Other verified facts that constrain the explanation  [VERIFIED, from M4b]

| Fact | Evidence | What it rules out or supports |
|---|---|---|
| Heavy tails alone do not inflate; uneven shape alone does not inflate; together they do | `h1_diag_factor_isolation.csv` (Gaussian E/D5 ≈ 5%; T4 flat ≈ 5%; T4 E/D5 7.1–9.9%) | An interaction, not a single cause |
| Inflation grows as tails thicken (`rom_t`, E/D5 shapes, 8,000 simulations): G 4.8–5.4, T10 5.2–5.9, T6 5.8–6.6, T4 7.1–8.2 (`diff_t` up to 9.9) | grid and diag files | Tail weight matters, monotonically |
| Inflation persists with no day factor and with estimated cross-stock dependence | T4 E no-day-factor 7.3 / 6.1 vs 7.5 / 7.1; "dep" 7.8 / 7.0 | Rules out day-volatility persistence and cross-stock dependence as primary causes |
| Over-rejection sits in the **lowest**-leverage simulations (T4 E NSE Q1 20.2% vs Q4 0.7%) | `h1_leverage_by_quartile.csv` | Rules out "a single dominant day drives it" |
| Replacing the oracle critical value restores 5.0% in all 80 cells | `h1_diag_factor_isolation.csv` | A critical value that does not depend on the sample would work, but the oracle is scenario-specific (2.4 to 3.2 across cells) |
| Jackknife SE gives the same rejection as the delta-method SE | `rom_jack` ≈ `rom_t` in every cell | The SE formula itself is not the lever |
| Removing the analytic estimator bias helps `rom_t` (7.5 → 6.0) but not `diff_t` | factor isolation file | Some, not all, of the effect is estimator bias |
| Close-spike scale scan: tau 0.37 → 8.1%, 4.0 → 5.8% (NSE `rom_t`) | factor isolation file | A sharp spike concentrated in few bars strengthens it (simulation evidence only) |
| Wild bootstrap and empirical likelihood are worse | cand file | They do not repair non-pivotality either |
| Bonferroni and max rules are both inflated | docs/11 | Multiplicity rule is not the cause |
| Fast simulator matches the bar-level pipeline | 160/160 exact; 45/48 statistical cells | Not a fast-simulator artefact (one NSE cell differs by about 2 points, unresolved) |
| SE / "true SD" ≈ 0.80 (rom) and 0.64–0.73 (diff) at T4 | factor isolation file | Caution: with T4 shocks the fourth moment of returns is infinite, so a "true SD" estimated from simulation is itself unstable; treat as descriptive |

### 2.3 Statistical assumptions that may be violated

| Assumption (where it is used) | Status | Reasoning |
|---|---|---|
| Finite variance of the period mean square, needed for the CLT and for any variance estimate of the mean | **Violated by design in T4** [REASONING] | A Student-t return with 4 degrees of freedom has an infinite fourth moment, so the squared return has infinite variance (tail index 2, the boundary of the normal domain of attraction). Convergence to normality is then very slow. For T6 the variance is finite but higher moments are not; T10 is milder. This ordering matches the observed severity G < T10 < T6 < T4 |
| The studentised statistic is (approximately) pivotal, so bootstrap-t is second-order accurate | **Violated** [VERIFIED indirectly, section 2.1] | The null distribution of \|t\| and the bootstrap critical value depend on the sample's tail behaviour, and the dependence is in the wrong direction |
| Higher-order accuracy of bootstrap-t needs several finite moments of the resampled variable (here the squared return) | **Not met** [REASONING; recalled from the bootstrap literature, not checked for this project] | With the squared return as variable, the moment conditions translate into return moments of order 6 to 8 or more; those exist only for df above 6 to 8. T10 satisfies them, T6 and T4 do not |
| The sample contains the rare large observations that shape the true tail of the statistic | **Violated in most 59-day samples** [HYPOTHESIS, consistent with the leverage and critical-value quartiles] | Resampling cannot create observations larger than those present; in a "quiet" sample the bootstrap distribution looks close to normal (crit about 2.5) while the true distribution is heavier |
| All periods behave alike under the null apart from scale | **Violated by uneven shapes** [VERIFIED by construction] | The open period is dominated by its first few bars (effective number of bars about 2.2 for D5, docs/11), so the open and close mean squares average far fewer heavy-tailed terms than the middle. The three columns have different distributional shapes under the null |
| The analytic bias correction assumes equal bar variance inside a period | **Violated** [VERIFIED, docs/11 and section 2.2] | Explains part of the inflation only |
| Days are exchangeable / independent for resampling | **Not the cause here** [VERIFIED] | Inflation persists without a day factor; estimated dependence changes it little. Dependence beyond what was simulated is untested |
| Bootstrap Monte Carlo error is negligible (B = 999 / 1,999) | Not tested | Very unlikely to produce this pattern, but cheap to exclude |

### 2.4 Why the bootstrap critical value fails — confirmed vs hypothesised

**Confirmed (from saved results):**
- C1. The inflation requires the combination of heavy tails and uneven shape (section 2.2).
- C2. It is not caused by day-volatility persistence, cross-stock dependence, a single dominant day, the multiplicity rule, the SE formula, bootstrap type (wild, empirical likelihood) or the fast simulator.
- C3. A constant critical value works (oracle), but the bootstrap's sample-dependent critical value fails: it is far too variable (CV 0.4) and low in precisely those samples where |t| is large.
- C4. The medians of the bootstrap critical value are below the oracle in inflated cells; means are above it (section 2.1).

**Hypotheses (not yet tested; each with a prediction that can fail):**

| ID | Hypothesis | Prediction | What would refute it |
|---|---|---|---|
| HA | Tail index of the squared return crossing the infinite-variance boundary (df 4) causes non-pivotality | Rejection rises smoothly as df falls through 10, 8, 6, 5, 4, 3 at fixed shape; no abrupt behaviour change at df 4 other than a sharper rise; df 3 worse than df 4 | A flat or non-monotone response across df |
| HB | The **effective number of heavy-tailed terms** in a period (shape unevenness) is the second ingredient | At fixed df 4, increasing the effective bar count (smoother shapes, finer averaging by merging bars) removes the inflation; reducing it (sharper spikes) increases it | Inflation unrelated to effective bar count |
| HC | The bootstrap critical value tracks the *observed* tail heaviness of the sample, which is negatively associated with large \|t\| | Conditional on the **observed** sample kurtosis (or the maximum day share), the critical value rises while true conditional rejection falls; a critical value that does not use sample extremes (fixed or model-based) removes the pattern | Critical value uncorrelated with sample extremes after conditioning |
| HD | A model that learns tail index and shape from the **bar-level** data (about 13,000 bar returns per market, versus 59 day-level observations) can supply the missing tail information | A null-imposed model-based bootstrap using empirical standardised shocks restores 5% where day-resampling cannot | It inherits the same conditional failure, or it is unstable because the fitted tail index is |
| HE | Bootstrap B is too small | Raising B from 999 to 9,999 changes rejection by under 0.3 points | Larger change |

Competing explanations I will test and exclude explicitly: HE, and "the oracle is only a post-hoc number that tells us nothing about a usable method" (it only shows that a better calibrated threshold exists, not that we can estimate it).

### 2.5 Interpretation caveats  [REASONING]

- T4 is a stress world. Whether real 5-minute returns have comparable tails is **unknown for this dataset**. The empirical-finance literature is often cited as reporting return tail indices of about 3 to 5, which would put squared returns at about 1.5 to 2.5; I recall this but have not verified it for these data, and it must not be treated as established. A descriptive tail-index estimate from the cleaned data would settle which part of the grid is realistic (a decision for you, section 6).
- If the real tail is heavier than T4, no studentised-mean method may be reliable at 59 days, and that would argue for revisiting the estimand (not within this plan, which keeps the estimand fixed).

---

## 3. Phase 2 — The three options in docs/12, section 16

### Option 1 — Pre-register the limitation instead of fixing it

**What it is:** Keep the current bootstrap-t. State in advance that its size may reach about 8–9% under heavy tails with uneven shape, and treat H1 results as exploratory with that caveat. (Variants: report simulation-based p-value ranges; use a stricter nominal level.)

### Option 2 — A simulation-calibrated critical value (one narrowly scoped diagnostic round)

**What it is:** Estimate the nuisance features that drive the failure (tail weight, within-period shape) from the data, simulate the null with those features imposed, and take the critical value from that simulated null. Candidates are specified in section 4. It targets the diagnosed problem (a critical value that is variable and mis-targeted).

### Option 3 — Write the research protocol (`docs/07_research_protocol.md`) after H1 is decided

**What it is:** A sequencing step, not an alternative way of handling H1. It freezes definitions, tests and decision rules. It needs either Option 1 or Option 2 to have been settled first.

### Comparison

| Criterion | Option 1: disclose | Option 2: calibrate | Option 3: freeze protocol |
|---|---|---|---|
| Statistical validity | None gained. The test stays known to over-reject; real-world size is unknown | Can restore nominal size **inside the validated domain** if it works; validity is conditional on the model family | None by itself. Freezing an uncalibrated test would make the invalidity permanent |
| Implementation complexity | Minimal | High: fitting, nested simulation, new code and tests; compute benchmark needed first | Low–moderate (writing and review) |
| Research credibility | Honest but weak: a primary test with admitted size inflation invites rejection; a p-value near 0.05 is uninterpretable | High **if** pre-registered and independently validated; low if tuned on the same scenarios the simulator author built (circularity) | High as a process step; empty without a valid H1 test |
| Main risks | Anchoring on false positives; reviewers discount all H1 results | (a) Circularity: the correction is built and tested on our own simulator; (b) model misspecification at n = 59; (c) unstable fitted tail parameter; (d) power loss; (e) researcher degrees of freedom; (f) cost | Locks in a defect; protocol would need amendment, damaging credibility |
| Limitations | Gives no way to say a result is significant | Cannot guarantee success; the result is "calibrated for these worlds", never "valid in general" | Cannot resolve H1 |
| Reversibility | Easy | Easy (a failed attempt leaves Option 1 available) | Hard once frozen |

### Recommendation

**Staged Option 2 with a pre-committed fallback to Option 1, then Option 3.**

Reasons: (i) the diagnosis points at a concrete, fixable mechanism (a variable, mis-targeted critical value), and a bar-level model can plausibly supply what 59 days cannot (about 13,000 bar returns per market instead of 59 days); (ii) failure costs little because Option 1 stays available and is made explicit up front as the outcome of a failed gate; (iii) Option 3 should not start until H1 has a defensible status either way. I do not claim Option 2 will succeed; the plan is built so that failure is detected and reported.

---

## 4. Phase 3 — Proposed staged research plan

All results below would be written to a **new** folder `outputs/milestone4/h1_calibration/` and a new report `docs/14_...`; nothing existing is overwritten. Code goes into new files; no existing source file is edited (if a helper in an existing module is needed, I will ask first).

### Stage 0 — Lock-in and prerequisites (no experiments)

1. Your approval of this plan and of the acceptance criteria (section 4.6).
2. Unit tests written first for every new component, including: the null-imposition step makes period variances equal; a scenario with known critical value reproduces it; fitted-parameter extraction recovers planted values; calibration code is deterministic given a seed.
3. A **compute benchmark** on a handful of simulations (not a result) to confirm feasibility of nested simulation; if infeasible, reduce grids and say so before any gated run.
4. A frozen specification file (grid, thresholds, seeds, candidate definitions, selection rule) saved with a SHA-256 hash **before** Stage 2 starts.

### Stage 1 — Mechanism diagnosis on the existing generator (tests hypotheses HA–HE)

Design (new simulation on the validated fast generator, 59 days, both markets, null only):

| Experiment | Purpose | Cells |
|---|---|---|
| Tail scan | HA | df ∈ {∞, 20, 10, 8, 6, 5, 4, 3} × shapes {flat, E, D5} |
| Effective-bar manipulation | HB | df 4; shapes with the same period variance but different spike sharpness (tau 0.37, 1, 2, 4) and with bars merged in groups of 1, 2, 3 |
| Critical-value anatomy | HC | Save, per simulation, t, critical value, sample kurtosis, maximum day share, effective bar count; test the conditional prediction |
| Bootstrap B | HE | B = 999 vs 9,999 on 4 cells |
| Pivotality map | Supports design of candidates | Oracle critical value as a function of (df, shape) |

At least 20,000 simulations per null cell (Monte-Carlo SE about 0.15 points at 5%). Output: which of HA–HE are supported or refuted, with the denominators. This stage uses development seeds only.

### Stage 2 — Candidate development (development grid only)

**Pre-specified candidates (maximum three, to limit forking paths):**

- **C1 — Null-imposed model-based bootstrap with empirical standardised shocks.**
  - *Idea:* from the bar level (about 13,000 returns per market) estimate the within-slot scale profile and a day factor; standardise bar returns; rescale the profile so that period variances are equal (imposing the null); build artificial days by multiplying empirical standardised shocks by the profile and resampled day factors; compute the same studentised statistic; take its 95% quantile as the critical value. No Student-t assumption is made.
  - *Justification:* [REASONING] If the null distribution of the statistic depends on the data mainly through the tail behaviour and shapes (the diagnosed nuisance features), those can be estimated with far more information at the bar level than at the day level, which should reduce the critical value's dependence on which few extreme days a 59-day sample happens to contain. The statistic's conditional miscalibration (section 2.1) is exactly the kind of thing a sample-independent reference distribution avoids.
  - *Known weaknesses:* within-day volatility clustering and jumps are not in the model; fitted shape error propagates; computation.
- **C2 — Fast double bootstrap-t (prepivoting).** Corrects the bootstrap's own level error with a second-level resample (single inner resample per outer, to keep cost near that of one bootstrap). *Justification:* data-driven, no model. *Weakness:* may inherit the same heavy-tail failure; the literature suggests double bootstraps need the same moment conditions as the first.
- **C3 — Conservative envelope constant.** One fixed critical value chosen so that rejection stays ≤ the target over the *development* family (the oracle values span about 2.4 to 3.2 in the existing cells). *Justification:* simple, transparent, sample-independent. *Weakness:* conservative (power loss) in benign worlds, and only valid within the family it was derived from.

**Selection rule (fixed in advance):** a candidate is eligible only if it passes the **calibration gate** (4.6) on the development grid. Among eligible candidates, choose by simplicity first, then power as a tie-breaker. Power is never used to rank candidates that fail calibration.

**Development grid (null cells):** tails {G, T10, T6, T4, and T3 as report-only stress} × shapes {flat, E, D5, R2, Etau variants} × markets {NSE, US} × days {59, 125, 250} × dependence {none, estimated}, ≥ 20,000 simulations per cell. The **whole pipeline** (fit → calibrate → test) is run inside every simulation: nuisance parameters are *estimated from that simulated sample*, never plugged in from the truth.

### Stage 3 — Locked validation (run once)

After the Stage 2 candidate and its settings are frozen and hashed:
- fresh master seeds, disjoint from all earlier ones;
- validation grid = development cells **plus** intermediate values not used in development (for example df 5 and 7, shapes interpolated between E and D5, 90 and 180 days);
- ≥ 20,000 simulations per null cell, power cells at ≥ 5,000 (reference: T4 flat ×1.1 and ×1.2; E ×1.2);
- run **once**. If it fails, the failure is reported; no retuning against the validation set.

### Stage 4 — Independent validation

1. **Alternative data-generating processes** not used in development, still pure simulation: (a) intraday volatility clustering (GARCH-type); (b) jumps; (c) different tail weight per period (heavier at the open than at the middle); (d) different df per stock; (e) stochastic day volatility with heavy tails; (f) Laplace-type shocks. The method must be run unchanged.
2. **Bar-level pipeline check:** the real `simulate_raw` → `clean` → table route on a reduced number of simulations for selected cells, compared to the fast route with two-proportion z-tests (same method as M4b).
3. **Second implementation:** a plain, slow reference implementation of the calibration step, run on 100 inputs and compared with the vectorised code (agreement within Monte-Carlo tolerance).
4. **Descriptive real-data check (only if you approve):** estimate tail weight and shape from the cleaned data to place the real data on the validated grid. **No H1 test statistic is computed on real data.**
5. **Review gate:** you review the Stage 3–4 results before any statement that H1 is calibrated is made.

### Stage 5 — Decision and reporting

New report `docs/14_h1_calibration_results.md` with: planned vs actual counts and seed audit; development vs validation results kept apart; failure audit with denominators; tests passed/failed/skipped; limitations. Possible conclusions:
- **Pass:** "H1 test is calibrated within the validated domain (stated explicitly)." Not "calibrated in general."
- **Partial:** calibrated for some tails/sample sizes only; state the boundary and use Option 1 beyond it.
- **Fail:** H1 inference stays unresolved; use Option 1 and record that all attempted corrections failed.
Only then does Option 3 (writing the protocol) start, if you approve.

### 4.6 Calibration acceptance criteria  [PROPOSED — thresholds are for you to confirm]

I do not accept "the confidence interval includes 5%" as sufficient. Both the point estimate and the upper confidence limit must fall in a stated band, in **every** cell of the tier, not on average across cells. The bands are in the spirit of the Bradley-type criteria used in simulation studies (stringent roughly 0.9α to 1.1α; liberal 0.5α to 1.5α); I am recalling these from memory and they should be checked before they are cited.

| Tier | Cells | Gate (null rejection, nominal 5%) |
|---|---|---|
| A — core | df ∈ {∞, 10, 6}, all shapes, both markets, days 59/125/250, dependence none and estimated | point estimate in **[4.5%, 5.5%]** and Wilson 95% upper limit **≤ 6.0%** in every cell |
| B — stress | df 4, all shapes, both markets, days 59/125/250 | point estimate in **[4.0%, 6.0%]**, Wilson upper limit ≤ 6.5% |
| C — extreme stress | df 3 | **report only**, no gate |
| Ceiling | any validated cell | no cell above **7.0%** |
| Alternative DGPs (Stage 4) | each | point estimate in [4.0%, 6.0%] |
| Conditional behaviour | rejection by leverage quartile and by critical-value quartile | **report**; the Gaussian reference itself shows a gradient (9.2% to 2.2% across leverage quartiles), so the gradient is not a failure, but a gradient clearly steeper than the Gaussian one is flagged |
| Numerical reliability | fit failures, non-finite statistics, non-convergence | counts and denominators reported; any rate above 0.1% needs a pre-specified fallback and a rerun of the affected cells |
| Power | T4 flat ×1.1 and ×1.2, E ×1.2 | reported **after** calibration passes; flagged if the calibrated test has less than about 70% of the uncalibrated test's power at T4 flat ×1.2 (uncalibrated reference 84% NSE, 90% US); never used for selection |
| Monte-Carlo precision | critical-value Monte-Carlo error | contributes under 0.15 points to the rejection rate (checked by varying B) |

### 4.7 Failure conditions  [PROPOSED]

The investigation is declared **failed for the affected domain** (and Option 1 applies) if any of these happens:
1. Any Tier A cell is outside its gate on the locked validation run.
2. More than the allowed share of Tier B cells fail (proposal: **none**; one failing Tier B cell is reported and the domain is narrowed to df ≥ 6).
3. The method fails any alternative DGP gate (it is then calibrated only for the simulator's own world).
4. The fitted tail or shape parameters are unstable at 59 days (for example, the tail-index estimate varies so much that the critical value varies as much as the bootstrap's does; compared by its coefficient of variation against the bootstrap's 0.40).
5. Power collapses (flagged threshold above) so that the test is practically uninformative.
6. The method needs retuning after seeing validation results (then the validation is spent).
7. The reference implementation disagrees with the vectorised one.
8. Compute cost makes the required number of simulations unreachable (then reduce the grid openly or stop).

### 4.8 Reproducibility requirements  [PROPOSED]

- **Seeds:** pass spawned `SeedSequence` objects (or 64-bit states) to `default_rng`, not 32-bit integers. M4b's 28 cross-file coincidences were harmless but this avoids them. A seed registry (master seed per part, cell and simulation index) is saved with the outputs.
- **Frozen specification** (grid, thresholds, candidate definitions, selection rule) saved and hashed *before* each stage; stage reports state the hash.
- **Environment:** Python 3.12.13, numpy 2.5.4, pandas 3.1.0, scipy 1.18.1, statsmodels 0.15.0, macOS Darwin 24.4.0, 8 cores; recorded in each run's metadata. The project is not a git repository, so SHA-256 hashes of every code file used are stored in the run metadata.
- **Tests first, full suite after:** all new tests written before the experiments; the full suite run after code changes and reported with exact passed/failed/skipped counts (current baseline 221 passed).
- **Counts and uniqueness:** planned vs actual simulations per cell, seed uniqueness within and across files, missing-value checks, as in `verify_m4b_counts.py` (a new copy for the new outputs).
- **Logs and outputs are never overwritten**: new folder, `COMPLETE` markers, plumbing-check outputs kept separately, and an aborted run (if any) is kept and documented.
- **Waiting on queued jobs:** use a verified process id and a log check; M4b's early H2 start taught us that.
- **No selection after seeing validation data**; the order of stages is fixed; development and validation results are reported separately.

### 4.9 Rough effort estimate  [ESTIMATE, to be benchmarked in Stage 0]

M4b ran about 40 simulations per second per machine for the delta-method bootstrap-t at B around 1,000. Model-based calibration (C1) needs many artificial datasets per simulation, so it is far costlier; I expect hours to days of runtime for full grids unless the critical value is precomputed as a function of the fitted parameters and looked up. I will measure this on a few simulations before asking you to approve a full run.

---

## 5. What is verified, reasoned, hypothesised, proposed — summary

| Verified (saved M4b results) | Statistical reasoning (not yet tested) | Hypotheses to test | Proposed experiments |
|---|---|---|---|
| Inflation needs heavy tails **and** uneven shape; ordering G < T10 < T6 < T4; not caused by dependence, day factor, a dominant day, SE formula, multiplicity rule, simulator; the oracle constant restores 5%; **the bootstrap critical value is highly variable (CV 0.4), mean above and median below the oracle, with the low values where rejection is high** | T4 has infinite fourth moment, so squared returns have infinite variance; bootstrap-t's accuracy needs more moments than T4 and T6 have; quiet samples lack the rare observations that shape the true tail; open and close average fewer effective bars | HA–HE (section 2.4) | Stage 1 diagnosis; Stage 2 candidates C1–C3; Stage 3 locked validation; Stage 4 independent validation |

## 6. Decisions I need from you before anything is implemented

1. **Approve the staged approach** (Option 2 with fallback to Option 1, then Option 3).
2. **Confirm or change the acceptance thresholds** (section 4.6) and failure conditions (4.7).
3. **Candidates:** approve C1, C2, C3, or restrict to C1 alone to limit cost and degrees of freedom.
4. **Descriptive real-data tail and shape estimate** from `data/clean` to place the real data on the grid (no H1 test on real data): allow or not.
5. **Compute budget:** accept a benchmark first, and a reduced grid if the benchmark shows full grids are impractical.
6. **Estimand:** keep fixed (assumed). If calibration fails at the realistic tail weight, whether to revisit the estimand is a separate decision I will bring to you rather than make.

Nothing will be implemented until you reply.
