# 30 — Real-data H1 test: pre-registration plan (PROPOSED, not approved, not run)

**Status:** written 2026-11-13 after the project owner answered "Real H1 test" to the question of what the real data should answer. **That answer states a direction. It is not an approval of this plan, of any data use, or of a run.** Nothing in this document has been executed: no H1 statistic, rejection decision or critical-value comparison was computed on real data; no data file was read; no simulation was run; no random number was generated; C3, the frozen specifications, manifests, source, tests and `docs/24`–`docs/29` were not touched.
**Labels:** **[ESTABLISHED]** in the accepted record; **[PROPOSED]** my design choice for your approval; **[DECISION]** needs the owner; **[RISK]** a way the result could be over-read.

## 1. Why a pre-registration, and how it relates to `docs/26`
- `docs/24` (Stage 5): C3 is **PARTIAL**: within its upper limits on a sparse simulated domain, conservative, not shown calibrated, never tested on real data. `docs/25` and `docs/26` keep that limitation.
- `docs/26` §1 and §13 E9 state that H1 testing on real data "would need a new authorisation". This plan is the request for that authorisation, written **before** any run so that nothing can be chosen after seeing a result. It does **not** amend `docs/26`. The descriptive placement protocol remains separate and unapproved; the two can proceed independently.
- Standing project rules apply: no fabricated results, no look-ahead, preserve every outcome including failures, frozen items untouched, no commit or push without your instruction.

## 2. The test [ESTABLISHED code, PROPOSED use]
- **Null (H1):** the three periods (open, middle, close) have equal root-mean-square return volatility in a market.
- **Statistic:** T = max over the 3 contrasts of |ln(X̄_a / X̄_b)| / SE, where X is the (days × 3) matrix of period mean squares averaged over the market's stocks (`h1_calibration.market_matrix_from_r2`, `max_abs_t`).
- **Decision rule:** **C3**: reject H1 if T > the frozen critical value for the sample size (`h1_calibration.c3_test`). For n = 59 sessions the frozen value is **3.298658** (`docs/24` §domain; not recomputed here).
- **Deterministic:** C3 uses a fixed critical value, so the primary test needs **no random numbers and no seed**. (The baseline bootstrap would need a seed and is left out; see R4.)

## 3. What can be tested now, and what cannot
- **Data on hand [ESTABLISHED, `docs/01`, `docs/14`]:** one Yahoo Finance 5-minute pull of 2026-10-30, about 60 trading dates, three NSE stocks (RELIANCE.NS, TCS.NS, INFY.NS) and three US stocks (AAPL, MSFT, NVDA), stored locally under `data/clean` (not in the repository; Yahoo terms allow personal use only, `docs/03`). A second pull exists (`data/raw_revision`) of the same dates; it is **not** independent data.
- **Primary tests [PROPOSED]:** **one per market** (NSE, US), n = 59 sessions, 3 stocks: exactly the validated layout of the 59-day cells. No other n is possible with this sample.
- **Not possible with this sample:** 90, 125, 180 or 250 sessions; different stocks; out-of-sample confirmation. Anything beyond requires new data, which needs a provider, licences and data-access authorisation (`docs/27`).

## 4. Design choices to fix before any run [PROPOSED; every one a decision]
- **R1 — Window.** Use the **first 59 usable complete scheduled sessions** of each market's sample, in time order, as in `docs/26` §4.1 (no choice after seeing data). If the sample has 60 dates, the 60th is not used. *Alternative:* a different rule must be stated now. How "usable" is judged (no missing used bar; first session bar excluded as in the simulator) is taken from the project's existing cleaning pipeline and is not changed.
- **R2 — Which stocks.** All three per market, as sampled. No selection by results. NVDA, AAPL etc. are the same six stocks that informed the simulation design (shape E, dependence, day-factor sd 0.6); **[RISK]** this is therefore **not independent confirmation** of the simulated domain's relevance (`docs/26` §3.3).
- **R3 — Primary decision.** C3 at its frozen n = 59 value, per market, at the nominal 5% level, **no multiplicity adjustment across the two markets**; both outcomes reported in full and neither is combined into a joint claim. *Alternative:* a Bonferroni-type rule (a different critical value) is **not available**: only frozen C3 values may be used, and no new critical value will be computed.
- **R4 — Baseline.** The M4b bootstrap-t baseline is **excluded** from the primary analysis (uncalibrated, report-only in the record). If you want it shown, a master seed has to be registered and it must be labelled report-only.
- **R5 — Also reported, descriptively, no decision:** the three log ratios of period volatilities with their standard errors, the day count used, and the date range. These are components of T, not extra tests.
- **R6 — Single run.** The analysis is executed **once** by a script written and hashed before the run; the output files are write-once; a rerun writes new files and the first output is kept. No alternative windows, stock subsets, cleaning variants or thresholds are tried afterwards.
- **R7 — Stopping and failure rules.** If the sample cannot supply 59 usable sessions for a market, that market is reported as "not testable" (not shortened to a smaller n, as in `docs/26` §4.1). Any data-quality failure, code error or inconsistency stops the run and is reported without altering the plan.
- **R8 — Reporting.** Aggregates only (T, critical value, decision, ratios, SEs, counts); no raw or bar-level data in `outputs/` or on GitHub (Yahoo terms, `.gitignore`). Results go into a new report numbered after this plan.

## 5. How to read each outcome (written in advance)
- **Reject (T > 3.298658):** evidence against equal period volatility in that market's sample, under the assumptions of the validated simulated domain. C3 is **conservative** (it did not over-reject in simulated nulls up to 6.0% in gated cells), so a rejection is the more informative direction. It does not say *which* periods differ beyond the three contrasts, and does not show the true rate is 5%.
- **Do not reject:** **weak evidence of equality.** C3's power is lower than the baseline's and the sample is 59 days; failing to reject mostly says the test could not detect a difference of this size.
- **Either result:** a statement about **these 59 sessions of three stocks from one Yahoo pull**, not about the markets in general. The real tails may lie outside the validated domain (`docs/14` suggests NSE close df about 3–4, where df 3 cells are report-only), so the validity of C3's size on these data is **unverified**; this is the main limitation and it is stated with every result.
- **[RISK] Multiplicity and forking paths** are controlled by fixing everything above; none of the other design choices (R1–R8) may change after the run.
- **[RISK] Prior knowledge:** intraday volatility differing by period is a long-documented market pattern, so a rejection would be expected and would **confirm** rather than discover. The test's value here is as a first real-data check of the procedure, not a research finding.

## 6. Approvals and steps (none given)
| # | Step | Needs |
|---|---|---|
| 1 | Review R1–R8; approve, change or reject each | **You** |
| 2 | Confirm this exploratory use of the existing local sample is acceptable under your reading of the Yahoo terms (aggregates only; no redistribution) | **You** (docs/03: terms not fully read; personal use) |
| 3 | Write the run script and tests (including a synthetic check that the script reproduces C3's `T` on a constructed matrix, no real data), freeze them in a new hashed manifest | Your authorisation to write code (not given) |
| 4 | Run once on the two markets; save outputs write-once | Your explicit run authorisation (not given) |
| 5 | Report per §5; update the record; commit only if you instruct | You |

**Not affected:** the larger real-data programme of `docs/26` (new provider, 59–250-session blocks, descriptive placement) stays unapproved and needs its own decisions (D1–D17, `docs/27`). A real-data H1 test on that data would also need its own authorisation.

## 7. Decision request
Please record, in writing: (a) approve, modify or reject **each of R1–R8**; (b) whether the exploratory test on the **existing sample** is what you want, or whether you want to wait for new data via `docs/26`; (c) your authorisation to write and test the script (step 3); and (d) your separate authorisation to run it (step 4). Until (c) and (d) are given, nothing is executed.

## 8. Restriction compliance
Documentation only. No real data read, no statistic computed, no simulation, no random number, no change to C3, frozen files, manifests, source, tests or earlier documents. Nothing committed or pushed in this step.

## 9. Authorisation record (added 2026-11-13, before any run)
The owner replied "ok go ahead and finish the work" after reading the review of R1–R8 (including the recommended extra rule that the script reports the session counts and stops before computing T if a market has fewer than 59 usable complete sessions). **Interpretation recorded here:** R1–R8 are approved as written, with that stop rule (it is R7); writing and testing the script and running it once on the existing local sample are authorised. Nothing else is authorised: no new data, no other n, no baseline, no change of any rule after the run, no commit or push. If this reading is wrong, the owner should say so before the results are used. The runner is `scripts/milestone4/real_h1_run.py`, its logic is `src/quantlab/research/real_h1.py`, its synthetic tests are `tests/test_research_real_h1.py`, and all are hashed in `frozen_real_h1_inputs.sha256` before the run.
