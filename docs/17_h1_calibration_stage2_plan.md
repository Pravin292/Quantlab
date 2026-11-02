# 17 — H1 calibration, Stage 2 plan (candidate development)

**Status: PLAN ONLY. No Stage 2 code has been written to run, no simulation has been started, nothing frozen has been touched.** Stage 2 runs only after you approve this plan and its open decisions (section 12).
**What this shows:** what Stage 2 will establish, the exact grid, candidates, seeds, simulation counts, runtime, diagnostics, gates and decision rules, plus my recommendation on the three open Stage 1 items.
**Numbers come from:** `outputs/milestone4/h1_calibration/stage2_plan/` (produced by `scripts/milestone4/stage2_plan_tables.py`, which reads frozen files and runs no simulation). Labels: **[VERIFIED]** computed by code from saved files; **[PROPOSAL]** my design choice needing your approval; **[ESTIMATE]** uncertain forecast.

## 1. Purpose
Stage 2 asks one question: **do the pre-specified candidates C1 (null-imposed bar-level bootstrap) and C3 (conservative fixed critical value) hold the null rejection rate near 5% across the frozen development grid, where the M4b baseline does not?** It also reports the corrected C2 procedure for information only.

It will establish, for each method and development cell: the rejection rate with Wilson interval, gate status, numerical failure counts, how the critical value behaves, and whether calibration holds conditionally (by leverage, kurtosis and critical value), all on shared simulated datasets.

It will **not** establish: validity outside the simulated family, validity on real data, power as a ranking criterion, or any claim about C2. Passing Stage 2 only makes a candidate **eligible for the single locked Stage 3 validation** (fresh seeds); it is never evidence of validity by itself (section 9).

## 2. Development grid (frozen v1, unchanged in v1.1) [VERIFIED]
File: `outputs/milestone4/h1_calibration/frozen_spec/cells_development.csv` (76 cells). Row-by-row plan with roles and seed rows: `…/stage2_plan/stage2_cells_plan.csv`.

| Block | Cells | n_days | Dependence | Day-vol sd | Design |
|---|---|---|---|---|---|
| Main | 40 | 59 | none | 0.3 | tails {G, T10, T6, T4, T3} × shapes {flat, E, D5, R2} × {NSE, US} |
| Estimated dependence | 8 | 59 | estimated (M4b `EMP_DEP`) | 0.3 | tails {T6, T4} × {E, D5} × {NSE, US} |
| Day-vol sensitivity | 4 | 59 | none | **0.6** | T4 × {E, D5} × {NSE, US} |
| 125 days | 12 | 125 | none | 0.3 | tails {G, T6, T4} × {E, D5} × {NSE, US} |
| 250 days | 12 | 250 | none | 0.3 | same, full 250-day cells |
| **Total** | **76** | | | | |

By tier: **A (G, T10, T6): 44 cells, 25,000 sims each = 1,100,000; B (T4): 24 cells, 25,000 each = 600,000; C (T3, report-only): 8 cells, 10,000 each = 80,000. Total 1,780,000 simulations per method.** Gated (two-sided or C3 upper-only) cells: 68. By sample size: 52 cells / 1,180,000 sims at 59 days; 12 / 300,000 at 125 days; 12 / 300,000 at 250 days. The full 250-day grid is kept, as you preferred. The 0.6 day-volatility sensitivity cells are included.
Data generator: the validated M4b generator `direct_sim.simulate_returns_sq`; for no-dependence cells it is bit-identical to the Stage 1 generator (tested). df ∞ is coded Student-t(1000), as in M4b and Stage 1.

## 3. Candidates
| Method | Role in Stage 2 | Definition |
|---|---|---|
| **Baseline** (M4b bootstrap-t, `rom`, max rule, B = 999) | Reference only. Run on the same datasets. **Not eligible**, not selectable. | unchanged |
| **C1** null-imposed model-based bootstrap, R = 499, p = (1 + #{T* ≥ T})/(R + 1) ≤ 0.05 | Eligible, gated two-sided | frozen `h1_calibration.c1_test` |
| **C3** fixed critical value per sample size = max over gated development cells of the 0.95 quantile of T from the separate training run | Eligible as conservative benchmark/fallback; gated on **upper limits only** | `h1_calibration.c3_test` with the frozen table (section 6) |
| **C2** "FDB-like procedure, formula UNVERIFIED" (v1.1 A1, B = 999) | **Report-only. Not eligible. No validity claim, no selection, no methodological conclusion (A6).** Run because it costs about 6% of the total | `h1_calibration_v11.fdb_like_test` |

C1 and C3 definitions are fixed before the run; **no candidate is modified during Stage 2** (decision D5).

## 4. How the baseline and Stage 1 are used
- Every simulation applies the baseline, C1, C2 and C3 to the **same dataset**, so differences are paired and not driven by different data.
- The baseline is the *reference for improvement*: it tells us what miscalibration the candidates are meant to fix (Stage 1: 28 clear FAIL cells of 68; 4.6–10.9% on the tail-scan grid). It is **never** counted as evidence for or against a candidate's validity and cannot be selected: you have stated it must not be selected as a reliable candidate across the full grid.
- **Plumbing check [PROPOSAL]:** 30 development cells (59 days, no dependence, day-vol 0.3, tails G/T10/T6/T4/T3 × flat/E/D5 × 2 markets) have a Stage 1 baseline counterpart (`stage1_reference_row` in the plan table). Before reading any candidate result, the Stage 2 baseline rate in each is compared with the Stage 1 rate by a two-sample z-test. By chance about 0.1 cells exceed 3 SE; more than one flagged cell means the Stage 2 pipeline differs from Stage 1 and the run is investigated, not interpreted. This checks the machinery; it is not validation of anything.
- The Gaussian-tail cells (df G) of Stage 1 and Stage 2 serve as the **reference for conditional diagnostics** (a well-behaved bootstrap-t is not flat by critical-value quartile even under Gaussian data: 8.2 / 6.1 / 4.6 / 1.9% for D5 NSE).

## 5. Calibration gates (spec v1.1, bounds unchanged)
| Tier | Cells (dev) | Point rule | Wilson-upper clause | n |
|---|---|---|---|---|
| A: G, T10, T6 | 44 | 4.5% ≤ p̂ ≤ 5.5% | U ≤ 6.0% | 25,000 |
| B: T4 | 24 | 4.0% ≤ p̂ ≤ 6.0% | U ≤ 6.5% | 25,000 |
| C: T3 | 8 | report only | – | 10,000 |
| C3 (any tier) | 68 | upper bounds only: p̂ ≤ 5.5% (A), ≤ 6.0% (B); lowest-cell rate reported | – | 25,000 |

At n = 25,000 the Wilson clause and the 7.0% ceiling never change a decision (A3; `gate_redundancy_check.csv`). A candidate passes only if every gated cell passes; no averaging, no "interval includes 5%".

**Development gates vs validation gates (same bounds, different job):**
| | Development (Stage 2) | Validation (Stage 3) |
|---|---|---|
| Purpose | Screen for eligibility; learn where a candidate fails | One-shot confirmation, locked candidate |
| Seeds | development 20261203; C3 training 20261202 | fresh 20261204 / 20261205 |
| Cells | 76 (68 gated) | 96 (88 gated: the 68 development cells with fresh seeds + 20 new intermediate cells) |
| May a result lead to a change? | Only through a new numbered spec version you approve (D5) | No retuning after seeing validation |
| Ambiguity replication (100,000 sims, seed 20261210) | **Not used** | Only with your written approval of the exact cell list |
| What a pass means | "eligible for Stage 3" | "passed the pre-specified gates on this simulated family" |

**Behaviour of the ambiguity flag [VERIFIED, important].** If a method were exactly 5.0% in every cell, each tier A cell has a 9.6% chance of being flagged ambiguous (p̂ outside about 4.77–5.23%) because the bounds are only 0.5 points away while the Wilson half-width is 0.27 points. Over 44 tier A cells the expected number of ambiguous cells is **4.2** and the chance of none is **1.2%** (54 cells in Stage 3: expected 5.2, chance of none 0.4%). Tier B cells are practically never ambiguous. So a perfectly calibrated candidate would almost always be labelled `MARGINAL_NOT_DEMONSTRATED` until replicated; at n = 100,000 an exactly calibrated cell is ambiguous with probability ~2e-7. This is a consequence of the approved rule, not an error, but it means Stage 3 will normally need replication, and Stage 2 must not treat a handful of ambiguous cells as a warning (D4, D10). Joint pass probability if every cell were truly 5.0%: 0.988 (development), 0.985 (validation).

## 6. Simulation counts, order and runtime
**Step 2.0 (no simulation):** write the runner and unit tests; freeze inputs with a new manifest `outputs/milestone4/h1_calibration/frozen_stage2_inputs.sha256` (plan tables, runner, tests).
**Step 2.1 C3 training run:** the 68 gated development cells (`stage2_c3_training_cells.csv`), **25,000 simulations each = 1,700,000** (44 cells at 59 days: 1,100,000; 12 at 125: 300,000; 12 at 250: 300,000), seed 20261202, statistic T only. Output: the C3 critical-value table (0.95 quantile of T per cell and the maximum per sample size 59/125/250), then **frozen and hashed before Step 2.2 starts**. [ESTIMATE] 0.10–0.56 wall hours.
**Step 2.2 Development run:** 76 cells, **1,780,000 simulations**, all four methods on each dataset, seed 20261203. Every cell is run to completion regardless of interim results (no early stopping, no cherry-picked cell order); one parquet file per cell so the run can resume.

| n_days | Cells | Sims | ms per sim, single core (gen / baseline / C2 / C1) | Sum | Hours at the benchmark speed-up | With measured speed-up | With Stage 1 overhead (+2 ms) |
|---|---|---|---|---|---|---|---|
| 59 | 52 | 1,180,000 | 0.48 / 1.44 / 3.41 / 48.70 | 54.0 | 4.43 | 4.25 | 4.40 |
| 125 | 12 | 300,000 | 1.00 / 2.90 / 6.96 / 104.41 | 115.3 | 2.40 | 2.40 | 2.44 |
| 250 | 12 | 300,000 | 2.03 / 6.27 / 14.82 / 210.08 | 233.2 | 4.86 | 5.05 | 5.09 |
| **Total** | **76** | **1,780,000** | | | **11.69** | **11.70** | **11.94** |

C3 training adds 0.1–0.6 h, so the central [ESTIMATE] is **about 12–12.5 wall hours** on this machine (8 cores, measured speed-up 3.85–4.17×), with the benchmark's ±30% giving roughly 8.5–16 h. **Caution:** my Stage 1 estimate was 0.165 h and the run took 0.338 h (×2.05; the benchmark omitted about 2 ms of per-simulation work). Stage 2 is dominated by C1 (about 90% of the time), where that overhead is a few percent, so I do not expect a doubling; if the whole estimate were off by the Stage 1 factor the run would take about 25 h. Stage 2 plus Stage 3 plus Stage 4 would then total about 28–55 h of compute. Storage: about 0.4 GB of parquet. The machine must stay awake (`caffeinate`) and I would run in resumable chunks.

## 7. Seeds [VERIFIED design, to be tested before use]
| Purpose | Master seed | Per-simulation seed |
|---|---|---|
| C3 training | 20261202 | `SeedSequence(20261202, spawn_key=(dev_row, i))` |
| Development, data | 20261203 | `SeedSequence(20261203, spawn_key=(dev_row, i, 0))` |
| Baseline bootstrap draws | 20261203 | `spawn_key=(dev_row, i, 1)` |
| C1 draws | 20261203 | `spawn_key=(dev_row, i, 2)` |
| C2 draws (report-only) | 20261203 | `spawn_key=(dev_row, i, 3)` |

`dev_row` is the 0-based row of `cells_development.csv` (same value in `stage2_cells_plan.csv`). Each method gets its own stream, so adding, removing or reordering a method cannot change the data or another method's draws (Stage 1 used one stream for data then bootstrap; that is fine for one method but not for four). All full-width `SeedSequence` objects, no 32-bit truncation. Reserved and unused here: validation 20261204/20261205, alternative processes 20261206, pipeline checks 20261207/20261208, C3 intermediate sizes 20261209, ambiguity replication 20261210. **Tests required before the run:** all (dev_row, i, k) streams distinct on a large sample; no master seed shared with any registered seed (Stage 1 20261201 included, M4b seeds are 2026107x); determinism (re-running a cell reproduces it exactly); resume reproduces the same rows. Reproducibility: seeds, plan tables, code hashes and package versions recorded in the run folder.

## 8. Diagnostics (per cell, per method unless stated)
Saved per simulation: validity flags, rejection flags, statistic T, baseline critical value, C1 critical value and p-value, C2 first-level and adjusted p-values, C3 critical value, kurtosis, leverage (largest single-day share of a period total, the M4b `max_d X[d,p] / Σ_d X[d,p]` quantity, called `maxshare` in Stage 1).
1. **Numerical failures:** count of simulations with a non-finite statistic, critical value or p-value, or an error, per method and cell; denominators reported. A failure rate above 0.1% in any cell needs a fallback (D6).
2. **Rejection rate:** p̂ with Wilson 95% interval, gate status (PASS, PASS_AMBIGUOUS, FAIL, FAIL_AMBIGUOUS), distance to the nearest bound in standard errors, ambiguous-cell count against the yardstick (D4).
3. **Paired comparison with the baseline:** discordant counts (rejected by one only) with an exact test; descriptive only.
4. **Conditional calibration:** rejection rate by quartile of leverage, of kurtosis, and of the method's own critical value (baseline, C1; for C3 the critical value is constant so only leverage and kurtosis apply); for C1 the deciles of its Monte-Carlo p-value (uniform under a calibrated test). Flag when the spread across quartiles is clearly steeper than the Gaussian reference of the same shape and market (operational rule: D2).
5. **Critical-value diagnostics:** mean, median, quantiles, coefficient of variation, Spearman(T, critical value), and the C1/baseline CV ratio (the v1 "fitted-parameter instability" failure condition, scope: D7); the cell's empirical 0.95 quantile of T (oracle) against each method's average critical value.
6. **Cost:** wall time per method.
7. **Power [decision D3]:** per the frozen text power cells are reported in Stage 3 only after calibration passes (T4 flat ×1.1, ×1.2 and E ×1.2, 5,000 simulations). Power never ranks candidates. I recommend an *early-warning* check in development for candidates that pass, because a power collapse discovered only at Stage 3 would waste the single locked validation (the v1 failure condition is under 70% of baseline power at T4 flat ×1.2).
8. **Plumbing checks:** the Stage 1 overlap test (section 4), statistic T identical across methods within a simulation, C1 null-imposition (period means equal in artificial worlds, as in the unit tests).

## 9. Limitations (to be repeated in every Stage 2 result)
- Stage 2 measures **null rejection rates in a simulated family** (Student-t shocks with the E, D5, R2, flat shapes, a Gaussian log day factor, no jumps or volatility clustering, iid days, one dependence setting estimated from ~59 days). Good performance on these cells does **not** establish validity outside that family, on real data, or for processes not simulated (Stage 4 examines six alternative processes).
- Real-data descriptive tails (docs/14): NSE close looks like df 3–4 and the robust day-scale sd is 0.64 (NSE) and 0.51 (US) against 0.3 in most development cells; only the 0.6 sensitivity cells (T4) approach that.
- C3 is valid only inside its training family; at 125 and 250 days it comes from 12 cells (less coverage than 44 cells at 59 days); the 90/180-day families (v1.1 A5) are provisional.
- The development cells are used both to train C3 (separate seeds) and to screen candidates; with up to three candidates examined the screening is optimistic. This is why Stage 3 uses fresh seeds once.
- 25,000 simulations detect an excess of roughly 0.5 points; they cannot show a true rate is *exactly* 5% (the gate is not an equivalence test).
- Unit tests of the code (including 297 passing now) are implementation checks, not statistical validation.

## 10. Decision criteria after Stage 2 (on development seeds)
**A. Advance to Stage 3 validation (as the single, frozen candidate).** All of:
1. C1: all 68 gated cells are PASS or PASS_AMBIGUOUS (no FAIL, no FAIL_AMBIGUOUS). C3: all 68 cells pass on the upper limits.
2. The number of ambiguous tier A cells is below the yardstick (fewer than 10 of 44; a truly 5.0% method reaches 10 or more with probability 0.8%).
3. Numerical failure rate ≤ 0.1% in every cell for that method, or an approved fallback exists.
4. For C1: critical-value CV below the baseline's in the cells set by D7.
5. No conditional-calibration flag (D2) in the tier B and 125/250-day cells.
6. Plumbing checks passed; if D3 is approved, no power-collapse flag.
7. Your explicit approval to proceed (nothing advances automatically).
If both C1 and C3 meet these, the precedence rule is D1 (my recommendation: C1 first; C3 only as a labelled fallback).

**B. Further investigation (no selection, no tuning).**
- Failures only in tier B (T4) cells while all tier A cells pass: report the domain as narrowed to df ≥ 6 (spec failure condition) and ask you whether to proceed on that narrowed domain.
- Failures confined to estimated-dependence cells, day-vol 0.6 cells or 125/250-day cells: diagnose the cause without changing the candidate; any change needs a numbered new spec version, your approval and a new development seed (D5).
- Ambiguous-cell count at or above the yardstick, or FAIL_AMBIGUOUS cells: report; a larger development replication needs your approval and a new seed.
- Conditional-calibration flags, CV rule violations or failure rates above 0.1%: investigate, do not advance.

**C. No candidate selected.** If C1 has FAIL cells in tier A, and C3 fails its upper limits, or the only passers are rejected by your decisions D1–D3, then **no candidate is selected and H1 remains unresolved** (standing rule). The baseline is never selected; C2 is never selected.
In every outcome I report all cells including failures and stop for your review before Stage 3.

## 11. The three open Stage 1 items (not incorporated into Stage 2)
| Item | Why open | Recommendation |
|---|---|---|
| **HB merge definition and sensitivity** | The spec left "merge g bars" undefined; I chose summing returns, edge-anchored groups, a fixed null constant (1.00–1.12). The HB result (about 1 point lower with g = 3, never reaching 5%) depends on it and is confounded with lower per-bar kurtosis (9.8 → 7.0). | **Later diagnostic stage ("Stage 1b"), after Stage 2 development results, baseline only.** Reason: it changes no candidate, gate or cell of Stage 2; running it first would invite using mechanism findings to redesign candidates (forking paths); running it after keeps the candidates fixed. Variants worth approving individually: averaging squared bar returns (no cross terms), different leftover handling, no null constant. About 0.3–0.5 h per variant. Until then HB is reported as weakly supported, not resolved. |
| **Sharpness arm** (T4, tau 0.37, 1, 2, 4) | Listed in docs/13, absent from the frozen `cells_stage1.csv`, never run. | **Same Stage 1b**, baseline only, about 8–10 new cells × 20,000 simulations (about 0.1–0.2 h). It needs a numbered spec addendum with a cell file and a new seed, so it should not be slipped into Stage 2. |
| **Oracle critical-value map** | Not in the frozen Stage 1 cells. | **No new simulation is needed:** Stage 1 saved T for every simulation in all 48 tail-scan cells (20,000 each), so the 0.95 quantile of T per (df, shape, market), with bootstrap intervals, can be computed from existing files as a read-only descriptive analysis. Recommended in Stage 1b, not before. It must not be used to build or adjust C3 (C3 comes only from its own training run, seed 20261202); at most it is an after-the-fact plumbing cross-check of the frozen C3 table. |
None of the three is a prerequisite for Stage 2.

## 12. Unresolved decisions for you
| ID | Decision | My recommendation |
|---|---|---|
| D1 | If both C1 and C3 qualify, which is preferred? The v1 rule says "simplest first", which would favour C3 although it is judged only on upper limits and can be very conservative. | C1 first; C3 only as a labelled, family-limited fallback. This changes the v1 wording, so it needs your approval. |
| D2 | Operational meaning of "clearly steeper than the Gaussian reference" for conditional calibration. | Flag when the quartile range (max − min) exceeds 1.25 × the Gaussian reference range of the same shape and market, and by at least 2 points. Judgement values; yours to set. |
| D3 | Power in development. | Add a small early-warning power check (3 power cells × 2 markets × 5,000 simulations, about 0.1 h) for candidates that pass calibration, excluded from ranking; otherwise defer all power to Stage 3. |
| D4 | Development ambiguity: handling and yardstick. | Advance with the ambiguous cells listed; investigate if 10 or more tier A cells are ambiguous; use replication only in Stage 3/4 as already approved. |
| D5 | Revising a candidate after seeing Stage 2. | No revision inside Stage 2. A revision needs a numbered spec version, your approval and a new development seed (I would reserve 20261211). |
| D6 | Numerical failures above 0.1% in a cell. | Exclude from the denominator and report; treat the cell as failed for that method until you approve a fallback; also show the rate counting failures as non-rejections. |
| D7 | Scope of the CV rule ("candidate CV ≥ baseline CV" is a failure condition). | Apply in the 24 tier B cells and the 125/250-day cells; report in all. |
| D8 | Run logistics. | About 12–16 h compute (worst case about 25 h), resumable per cell, `caffeinate`, no early stopping, C3 table frozen before the main run. |
| D9 | Run C2 (report-only) in Stage 2. | Yes, about 6% of cost; labelled "FDB-like procedure, formula UNVERIFIED". |
| D10 | The ambiguity-rule behaviour in section 5 (a calibrated method is almost always MARGINAL until replicated). | Keep the approved rule; budget one routine replication of about 4–5 cells in Stage 3 (about 0.3–0.4 h per 59-day cell for C1). |

## 13. Files
New in this planning turn (nothing frozen modified): `docs/17_h1_calibration_stage2_plan.md`; `scripts/milestone4/stage2_plan_tables.py`; `outputs/milestone4/h1_calibration/stage2_plan/` with `stage2_cells_plan.csv`, `stage2_c3_training_cells.csv`, `stage2_seed_scheme.csv`, `stage2_runtime_estimate.csv`, `stage2_c3_training_runtime_estimate.csv`, `stage1_estimate_vs_actual.csv`, `stage2_gate_pass_probability.csv`, `stage2_joint_pass_probability.csv`.
Preserved unchanged: frozen v1 (23 hashes) and v1.1 (7 hashes), M4b outputs, Stage 0 and Stage 1 results (`stage1/`, Stage 1 code manifest 8 hashes).
