# 42 — Stage 6 preregistration: does C3 survive realistic dependence, how big a difference can it detect, and does it behave on real data?

**Status: FROZEN BEFORE ANY STAGE 6 RESULT EXISTS (2026-11-19).** Everything below was written, hashed (`outputs/milestone4/frozen_stage6_inputs.sha256`) and only then run, once each. Authorisation: the owner's instruction of 2026-11-19 to do all the work that closes the gaps. Nothing in the frozen v1 / v1.1 specifications, seeds, thresholds, critical values, manifests or earlier reports is changed; C3 is applied **unchanged**.

## 1. Why this stage exists (the gaps)
| Gap found earlier | What Stage 6 does about it |
|---|---|
| Phase 6 ([41](41_phase6_exploratory_report.md)): the fresh US sample had stronger day-to-day volatility persistence (0.42) and shared volatility (0.30) than the simulations used (0.19, 0.14), so C3 had **no simulation evidence for that period** | **Part A** simulates exactly those stronger levels (and a range around them) and measures C3's false-alarm rate |
| "C3 is cautious" was never measured | **Part B** measures power: how big an open/close difference C3 detects, at five sample sizes |
| On real data nobody knows the truth, so a false-alarm rate could never be checked | **Part C** builds a *placebo* on the real samples: time-of-day labels are shuffled so the truth is "equal", and the real tails and dependence stay |

Parts A and B use **simulated data only**. Part C re-uses the three real samples already tested; **no new data is pulled or read**.

## 2. Part A — size of C3 under dependence (the main test)
- **Question:** when volatility is truly equal in the open, middle and close, does C3 still reject at most as often as its frozen limit when stocks and days are dependent as in the real markets?
- **Generator:** the validated M4b generator with the dependence module (`direct_sim.simulate_returns_sq`), unchanged. Dependence is set by three numbers: `phi` (day-to-day persistence of day volatility), `share` (how much of day volatility is common to all three stocks) and `ret_corr` (return correlation between stocks).
- **Cells (96, fixed order):** 2 markets (NSE, US) × 2 intraday shapes (R2, E) × 2 tails (T6 = Student-t with 6 degrees of freedom, tier A; T4, tier B) × 2 sample sizes (59 and 125 sessions) × 6 dependence levels. 25,000 simulations per cell, master seed **20261401**, per-simulation seed `SeedSequence(20261401, spawn_key=(cell_row, i, stream))`.
- **Dependence levels** (`ret_corr`, `share`, `phi`):
| Level | Values | Meaning | Gated? |
|---|---|---|---|
| S0 none | 0, 0, 0 | independent stocks and days (reproduces the validated setting) | yes |
| S1 validated | NSE 0.355, 0.454, 0.441 · US 0.187, 0.141, 0.190 | the "estimated" values already inside the frozen validation grid | yes |
| S2 fresh point | 0.24, 0.30, 0.42 | the US fresh sample as measured in Phase 6 | yes |
| S3 fresh upper | 0.29, 0.50, 0.61 | the top of that measurement's ±2 standard-error range (the estimates are uncertain) | yes |
| S4 one-and-a-half | 0.36, 0.45, 0.63 | 1.5 × S2, the Phase 6 "outside" line | **no, reported only** |
| S5 illustrative | 0.5, 0.7, 0.7 | the earlier registered illustrative stress value | **no, reported only** |
- **Gate (frozen rule, applied unchanged):** a gated cell passes when C3's rejection rate is at most **5.5%** (T6, tier A) or **6.0%** (T4, tier B); statuses PASS / PASS_AMBIGUOUS / FAIL_AMBIGUOUS / FAIL come from the frozen v1.1 A2 classifier (`classify_cell`, C3 mode) with a Wilson 95% interval.
- **Outcome label (from the 64 gated cells only):** STRESS_PASS (all PASS) · STRESS_MARGINAL (no FAIL, some PASS_AMBIGUOUS) · STRESS_BOUNDARY (no clear FAIL, some FAIL_AMBIGUOUS) · STRESS_FAIL (any FAIL).
- **Reference:** the old bootstrap test runs on the same datasets (B = 999). It is information only and gates nothing.
- **Committed interpretation (whatever the result is):**
  - STRESS_PASS: "C3 stayed within its limits at the dependence levels measured in real data, including their upper uncertainty range, in the cells tested." Not "validated everywhere".
  - Any FAIL or FAIL_AMBIGUOUS: reported with the exact cells. **C3 is not retuned and no cell is dropped.** The honest statement becomes "C3 is not shown safe above dependence level X". A remedy would be a separate new method, with its own preregistration, calibration and approval.
  - S4 and S5 results are described as the *edge of the evidence*, not as pass or fail.

## 3. Part B — power curve (diagnostic, nothing gated)
- **Question:** how large must the open and close volatility be, relative to the middle, for C3 to reject with probability at least 80%?
- **Cells (120):** 2 markets × 5 sample sizes (**59, 90, 125, 180, 250**; each has a frozen C3 value) × 6 multipliers (**1.05, 1.10, 1.20, 1.30, 1.50, 2.00**) × 2 dependence levels (S0, S2). Shape R2, tail T4 (the heavier tail, so the more demanding setting). 10,000 simulations per cell, master seed **20261402**.
- **Multiplier:** open and close volatility (root-mean-square return) are `mult` times the middle's. The real samples showed open/middle ≈ 1.95–2.17.
- **Minimum detectable multiplier:** the smallest grid value with power ≥ 80%, or a linear interpolation in log(mult) between the last grid value below 80% and the first at or above it; labelled `at_or_below_first` if even 1.05 reaches 80%, `not_reached` if 2.00 does not.
- Power below 100% at the sizes of real interest is reported as it is. Nothing is selected on it.

## 4. Part C — real-data placebo (false-alarm check on real structure)
- **Idea:** take the 59 sessions the frozen real test used. In every session, shuffle which 5-minute slot belongs to which period (same shuffle for all three stocks, group sizes kept). Now open, middle and close have the same expected variance **by construction**, so every rejection is a false alarm, while the real fat tails, day-to-day dependence and cross-stock dependence remain.
- **Samples:** US first (Yahoo), NSE fresh (Yahoo), US fresh (Alpaca). NSE first was **not testable** (58 of 59 sessions) and gets no placebo. The rebuilt data must reproduce each recorded real T exactly (tolerance 1e-9) or the run stops.
- **Replications:** 10,000 shuffles per sample, master seed **20261403**, one generator per sample (`spawn_key=(sample_index,)`).
- **Reading (fixed now):** PLACEBO_OK when the rejection rate is ≤ 5.5%; PLACEBO_WARN when 5.5% < rate ≤ 7.0%; PLACEBO_HIGH when above 7.0% (the frozen ceiling). Wilson intervals are shown.
- **Limits stated in advance:** the shuffle also breaks the within-day pattern of volatility, so it is a stress check, not a proof of size; the 10,000 shuffles reuse the same 59 sessions, so they describe C3's behaviour *on these sessions*, not on all possible days; and it does not test power.

## 5. What is deliberately not in this stage
- **Independent holdout stocks** (e.g. JPM, XOM, KO) need a **new data pull**. Each pull needs its own explicit approval, so it is designed but **not performed** here.
- No change to C3, no new candidate, no real-data re-test, no trading claims.

## 6. Run order, files and checks
1. This document, `src/quantlab/research/stage6.py`, `scripts/milestone4/stage6_*.py` and `tests/test_stage6.py` are hashed in `frozen_stage6_inputs.sha256`.
2. Each runner first verifies **all earlier frozen manifests** plus this one, refuses to run if its output folder is not empty, and writes to `outputs/milestone4/stage6/part_a|part_b|part_c/`.
3. Smoke runs (tiny, scratch folder, `--smoke`) were used only to check the code runs; their numbers are discarded.
4. Report: [43](43_stage6_report.md), generated from the saved files.

## 7. Numbers used
- Frozen C3 critical values: 59 → 3.298658; 90 → 2.946701; 125 → 2.880076; 180 → 2.854727; 250 → 2.816000.
- Simulation counts: Part A 96 × 25,000 = 2,400,000 · Part B 120 × 10,000 = 1,200,000 · Part C 3 × 10,000 shuffles.
