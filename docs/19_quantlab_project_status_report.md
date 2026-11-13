# 19 — QuantLab project status report (as of 2026-11-13, after Stage 5 and Phase 6 documentation)

**What this is:** one consolidated, honest status report for the whole project: what is finished, what is blocked and why, what was found, what the findings do and do not show, and how to verify everything.
**What it is not:** it is not a research protocol and it contains **no claim about real-market behaviour and no profitability claim**. All inferential work in M4 and the H1 calibration investigation uses **simulated** data. No real-market H1, H2 or H3 test has been run.
**Evidence labels:** **[VERIFIED]** checked in the repository on 2026-11-08 (Stage 4 sections) or 2026-11-05 (earlier sections); **[REPORTED]** taken from a project document (path given); **[BLOCKED]** needs an approval that has not been given.

## 1. Status at a glance
| Part | State |
|---|---|
| M1 data availability, M2 ingestion/validation/cleaning, M3 EDA | **Complete** (exploratory, one ~60-day pull per stock) |
| M4a / M4b: H1 and H2 diagnostics and power on simulated data | **Complete as diagnostic stages** (not a frozen protocol) |
| H1 calibration: Stage 0 (preparation) and Stage 1 (baseline diagnosis, 1,240,000 simulations) | **Complete** |
| Stage 2 (candidate development, report `docs/18`) | **Complete.** User decision (2026-11-05): **C3 is the sole candidate for Stage 3; C1 is not selected** |
| **Stage 3 locked validation of C3** (96 cells, 2,280,000 simulations, run once; report `docs/21`) | **Complete.** C3 outcome **PASS_CLEAR** on its upper-limit gates; see section 4 for what that does and does not mean |
| **Stage 4 independent validation of C3** (report `docs/23`, preregistration `docs/22`, approvals `docs/22b`) | **Complete: all five preregistered criteria met** (null check, 12 alternative-process cells, bar-level check, 80 same-returns matrices, independent reference implementation); see section 4 |
| **Stage 5 decision report** (`docs/24`) | **Complete (documentation only). Preliminary classification: PARTIAL**: C3 satisfies its upper rejection-rate limits within the validated simulated domain and is conservative; calibration on real market data is unverified |
| **Phase 6 documentation** (`docs/25`–`docs/29`, added 2026-11-13) | Protocol `docs/26` revision 5 **proposed, not approved**; register `docs/27`: D1–D17 all pending; `docs/28`–`docs/29`: Stage 0 reference does not support the Mode B n = 59 D-tail claim (owner decision pending). **No real data accessed, no simulation run, real-data work not authorised** |
| **Real-data H1 test** (`docs/30` plan, `docs/31` report, 2026-11-13, existing sample only) | **Run once.** US: reject (T = 22.59 against C3 3.30); NSE: not testable (58 of 59 required complete sessions). Not independent of the simulation design; C3's real-data size unverified |
| Research protocol (`docs/07_research_protocol.md`, does not exist), real-market tests, H3, M5 | **[BLOCKED]**, not started |

**The project is not complete.** The M4b/baseline H1 test remains uncalibrated under heavy tails with uneven shapes. C3 (a conservative fixed critical value) stayed within its upper limits in every Stage 3 cell, but that does not show the rate is held near 5%, and nothing has yet been shown outside the simulated family. Stage 4 found no problem in its checks, but it is still simulated evidence. Stage 5 classified the result as PARTIAL (`docs/24`); real-data behaviour and the research protocol are the remaining open steps and need separate approval.

## 2. Data and pipeline (M1–M3) [REPORTED, integrity VERIFIED]
- Universe: RELIANCE.NS, TCS.NS, INFY.NS, AAPL, MSFT, NVDA; 5-minute OHLCV from Yahoo Finance, an unofficial personal-use source whose terms do not allow redistribution (`docs/03_data_sources_and_licensing.md`). The data is therefore **not in the repository**.
- One pull per stock (about 59 usable trading days). Raw files are immutable snapshots; **6 of 6 raw files match their SHA-256 in `data/manifest.csv`**, are read-only, and `data/clean/` holds 12 files (6 Parquet, 6 reports). [VERIFIED]
- Code: `src/quantlab/` (calendars, ingest, parse, validate, clean, eda); rules in `docs/05_validation_rules.md`; EDA findings in `docs/06_eda_findings.md` (descriptive only: the sample is far too short for any robust claim).

## 3. What M4 found (simulated data) [REPORTED: docs/09–12]
- **H1** (volatility differs across open, middle, close) is tested with a studentised max-contrast statistic and an iid-day bootstrap-t. It rejects about 5% under Gaussian or flat-shape worlds but **7–9% at 59 days** (6–9% at 125 and 250 days) with Student-t(4) shocks and uneven within-period shapes. Alternatives tried were equal or worse. Replacing the critical value by the simulated 95% quantile restores exactly 5.0%, so the defect sits in the bootstrap critical value, not the estimator. **H1 inference under heavy tails is unresolved.**
- **H2** (volume carries predictive, not causal, information) behaved like a calibrated test in the simulated worlds studied (null rejection 3.5–5.8% at 59 days; resolved only to about ±2 points per cell); power depends strongly on effect size and days. Planted effects are not market relationships.
- Execution was audited: 814,880 H1/H2 simulation rows, planned equal to actual counts, the fast simulator equal to the bar-level pipeline on identical returns (`docs/12`).

## 4. H1 calibration investigation
**Stage 0 [REPORTED: docs/14, 15, 15a, 15b].** Benchmark, precision arithmetic, descriptive real-data tails (no hypothesis tests), frozen specification v1 (23 hashed files) and corrected v1.1 (7 hashed files). A defect in the frozen C2 implementation (it equalled the ordinary bootstrap p-value) was left unedited and handled by an addendum. **C2 remains unverified against the original paper and report-only; it was never run in Stages 2–3.**
**Stage 1 [REPORTED: docs/16].** 68 cells, 1,240,000 baseline-only simulations, 0 failures. Baseline null rejection 4.6% to 10.9% on the tail-scan grid; it rises gradually with tail weight, needs both heavy tails and an uneven within-period shape, and the bootstrap size is not the cause.
**Stage 2 [REPORTED: docs/17, 17b, 17c, 18].** 76 development cells, 1,780,000 simulations, baseline + C1 + C3, 0 failures. C1: 3 FAIL, 9 FAIL_AMBIGUOUS, 17 ambiguous tier A cells, 4 D7 violations, 52 D2 flags; C3: all 68 gated cells pass its upper-limit gate but rejects far below 5% (median 1.43% tier A, 3.44% tier B), with 22 D2 flags. All failures, violations and the 19 borderline D2 comparisons are preserved in `docs/18`. A diagnostic power check (30,000 simulations) raised no collapse flag.
**Stage 3 [REPORTED: docs/20 pre-run record, docs/21 report; counts VERIFIED].** Authorised by the user's designation of C3 as sole candidate. Frozen 96-cell grid (76 development cells re-run with fresh seeds + 20 new intermediate cells: df 7 and df 5, shape E at 59/90/180 days, shapes D1.5/D3.0), 2,280,000 simulations, run once, 0 failures. The C3 values at 90 and 180 days (2.9467, 2.8547) were trained first (600,000 simulations, seed 20261209) and frozen before validation.
| | Baseline (reference only) | C3 (candidate, upper limits only) |
|---|---|---|
| Gated cells (88): PASS / PASS_AMBIG / FAIL / FAIL_AMBIG | 21 / 10 / 40 / 17 | **88 / 0 / 0 / 0 → PASS_CLEAR** |
| Rate range (%) | 4.52–8.72 | 0.59–5.28 (tier A max 2.98, tier B max 5.28; median 1.82) |
| Failed simulations | 0 | 0 |
- The 20 new cells all pass for C3 (rates 1.26–3.56%). Against the Stage 2 rates on fresh seeds C3 differs by +0.01 points on average (one cell at |z| 3.31, five above 2, listed in `docs/21`).
- **What PASS_CLEAR means:** C3 did not exceed its upper limits anywhere in the simulated family, including cells it never saw. **It does not mean the rate is held near 5%** (C3 is very conservative), and it makes no statement outside the family, about dependence/volatility beyond the simulated settings, or about other processes (Stage 4).
- D2 (judgement-based, same formula as Stage 2): 320 computable comparisons, 143 flagged (34 for C3), 20 borderline; 16 cells (90/180 days, D1.5/D3.0) have no df ∞ reference in the frozen grid, so D2 is not computable there as specified (no substitute invented). Everything is in `docs/21`.
- Power cells (run only because calibration passed; diagnostic only): no collapse flag; C3 power is 12–19% against the baseline's 30–41% at the smaller effect, and 82–89% against 86–90% at T4 flat ×1.2.

**Stage 4 [REPORTED: docs/22, 22b, 23; counts VERIFIED 2026-11-08].** Authorised by the user's approval of decisions D1–D6 (8,000 bar-level simulations per cell). Run once under the frozen preregistration; the Stage 4 inputs manifest (21 files) was created before any Stage 4 simulation. All data simulated.
- **A. Null check:** the alternative processes a, b, e, f keep equal period variance (largest deviation 0.154% against the literal 0.5% tolerance); processes c, d pass the truncated-moment check. Limitation: 2.7–16.9% of the variance of c and d lies beyond the cutoff and rests on exact analytic constants, not on Monte Carlo.
- **B. Alternative processes a–f (12 cells × 25,000 = 300,000 simulations, 0 failures):** C3 rejection rate 1.23% to 4.41% (median 1.97%), at most 6.0% in all 12 cells; no ambiguous cell. The baseline, for reference only, ranged 5.04–9.45%.
- **C. Bar-level pipeline check:** 8 cells × 8,000 new bar-level simulations against the Stage 3 fast route: 16 pooled z-tests, largest |z| = 1.86 (limit 3), none between 2 and 3. 80 same-returns matrices: maximum relative difference 3.59e-13 (limit 1e-9). Power note: differences below about 1 point could go undetected.
- **D. Independent exact-arithmetic reference implementation:** 100 datasets, maximum relative difference of the statistic 4.77e-14 (limit 1e-9), identical C3 decisions in 100 of 100, five frozen C3 values re-derived to 1.6e-16 (limit 1e-12). Same author, shared dataset generator.
**Stage 5 [REPORTED: docs/24].** Documentation-only decision report (2026-11-10): validated-domain definition, planned-versus-actual counts and seed audit (8,024,000 simulations, all equal to plan), development-versus-validation comparison, failure and limitation audit. **Classification PARTIAL.** The gate for C3 is read as an upper limit (v1.1 A2; D5 approved 2026-11-05, confirmed 2026-11-10); the original two-sided wording in docs/13 §4.6 is preserved and the discrepancy is documented. The report is `docs/24` because `docs/14` already exists (Stage 0). No simulation, real data or frozen file was touched.
- **What Stage 4 does not establish:** validity on real market data, validity outside the simulated processes, that C3's rate is near 5% (it is conservative), or anything about power or trading. D2 is not computable for the alternative processes (no df ∞ reference) and no substitute was invented.

## 5. Simulation ledger
| Stage | Simulations | Master seed(s) | Authorisation basis | Status |
|---|---|---|---|---|
| M4a / M4b | 814,880 rows in the M4b files (plus smaller M4a diagnostics) | integers in 20261030–20261081 (32-bit; 28 harmless cross-file coincidences, documented in `docs/12`) | M4a/M4b approvals | complete |
| Stage 0 benchmark and descriptive checks | small | 20261100–20261103 | Stage 0 approval | complete |
| Stage 1 | 1,240,000 | 20261201 | Stage 1 approval | complete, verified |
| Stage 2: C3 training / E4 development / E6 power | 1,700,000 / 1,780,000 / 30,000 | 20261202 / 20261203 / 20261212 | E3, E4, E6 authorisations | complete, verified |
| **Stage 3: C3 training at 90/180 days** | **600,000** | **20261209** | spec v1.1 A5, within the Stage 3 authorisation (2026-11-05) | complete, verified |
| **Stage 3: locked validation** | **2,280,000** | **20261204 (rows 0–75), 20261205 (rows 76–95)** | user designation of C3 and Stage 3 authorisation (2026-11-05) | complete, verified, run once |
| **Stage 3: power cells** | **30,000** | **20261213** (new, registered in `docs/20`) | frozen Stage 3 spec; run only because calibration passed | complete, verified |
| **Stage 4: alternative processes** | **300,000** | **20261206** | Stage 4 approvals D1–D6 (`docs/22b`) | complete, verified, run once |
| **Stage 4: bar-level pipeline check** | **64,000** (+ 80 matrices) | **20261207** | same | complete, verified, run once |
| **Stage 4: reference check** | **100 datasets** | **20261208** | same | complete, verified |
| **Stage 4: null check** | 5×10⁷ bars per process/market cell (not counted as simulations) | namespace under 20261206 | same | complete, passed |
Total simulated since Stage 1: 8,024,000 (Stages 1–4, not counting the null-check bars, matrices or reference datasets). Registered master seeds 20261201–20261213 are all distinct [VERIFIED]; per-simulation seeds are full-width `SeedSequence` objects. Reserved and unused: 20261210 (replication), 20261211 (candidate revision).

## 6. Integrity and governance [VERIFIED 2026-11-08]
| Check | Result |
|---|---|
| Frozen v1 / v1.1 / Stage 1 code manifests | 23 / 7 / 8 files OK |
| Stage 2 inputs / addendum / C3 table manifests | 18 / 2 / 2 OK |
| **Stage 3 inputs manifest** (`frozen_stage3_inputs.sha256`, created before any Stage 3 data) | 12 of 12 OK |
| **90/180-day C3 table** (`stage3/c3_intermediate/C3_INTERMEDIATE_TABLE.sha256`) | 2 of 2 OK |
| **Stage 4 inputs manifest** (`frozen_stage4_inputs.sha256`, created before any Stage 4 simulation) | 21 of 21 OK |
| Stage 4 output digests (recomputed after the report) | equal to those recorded in `docs/23` §11 |
| Raw data vs `data/manifest.csv` | 6 of 6 OK (checked 2026-11-05) |
| Row counts vs plan | Stage 1 1,240,000; C3 training 1,700,000; E4 1,780,000; E6 30,000; Stage 3 intermediate training 600,000; validation 2,280,000; Stage 3 power 30,000: all equal; ids unique; 0 invalid |
| C3 values used in Stage 3 | equal to the two frozen tables in every cell |
| Test suite | **355 passed, 0 failed**, 3 pre-existing warnings (`h2_volume.py:157`) |
Governance: no frozen file, seed, threshold, critical value or manifest was modified; all failures, violations and borderline results are preserved; nothing was reclassified; the run-once rule held (no validation or Stage 4 cell was recomputed). The stale sentence in the hashed `docs/17b` and the stale `d2_flag` docstring remain unedited (blocker B10).

## 7. Blockers and the approvals that would unlock them
| # | Item | Why blocked | Approval needed | Unlocks |
|---|---|---|---|---|
| B1 | Formal Stage 2 classification | **Resolved 2026-11-05:** C3 sole candidate, C1 not selected | – | Stage 3 (done) |
| B2 | Stage 3 locked validation | **Done** | – | Stage 4 |
| B3 | Stage 4 independent validation | **Done: all five criteria met** (`docs/23`). The optional real-data descriptive check was **not run** (separate approval, still open) | – (real-data item: explicit approval) | Stage 5 |
| B4 | Stage 5 decision report | **Done: PARTIAL** (`docs/24`) | – | research protocol decision |
| B5 | Any candidate revision | Requires a new numbered specification, approval and seed 20261211 | Explicit approval | new development round |
| B6 | Stage 1b diagnostics | New diagnostic stage | Explicit approval | mechanism clarity only |
| B7 | Ambiguity replication | Only with written approval of the exact cell list. **Stages 3 and 4 had no ambiguous C3 cells, so none is needed.** | Written approval if ever needed | – |
| B8 | Verification of C2's formula against the original paper | Source not accessible to me | User or other access | removal of the report-only restriction |
| B9 | Research protocol, H3, M5, any real-market H1/H2/H3 test, strategies or backtests; optional real-data descriptive placement of the domain | Not authorised; H1 is classified PARTIAL, so a protocol must carry the limitation and the conservatism | Explicit approval of each | the original research questions |
| B10 | Stale wording in hashed `docs/17b` and the `d2_flag` docstring | Needs a new manifest version | Approval | tidiness only |
| B11 | Commit and push the untracked Stage 2–5 work to GitHub; choose a licence | **Commit and push authorised by the user on 2026-11-13** (Stage 2–5 and Phase 6 documentation); licence still not chosen | – | public record |
Dependency order: **B9** (B3, B4 done).

## 8. Limitations and what is not claimed
- Everything inferential is **simulation evidence about a simulated family** (Student-t shocks, E/D5/D1.5/D3.0/R2/flat shapes, Gaussian log day factor, no jumps or volatility clustering, iid days). It does not show that any method is valid on real data. Stage 3 validates C3 within that family and the intermediate cells only; Stage 4 adds six non-iid-Gaussian alternative processes (still simulated).
- C3 is highly conservative and judged on upper limits only; its critical values come from small cell families (44 cells at 59 days; 12 at 90, 125, 180, 250 days), so scenario coverage is limited and the maximum over noisy quantiles is biased upward. Its D2 flags (leverage gradients) are preserved, not waived.
- The real data are one short, revised, unofficial Yahoo sample; descriptive tails are imprecise.
- D2 and D4 thresholds are judgement-based; 16 Stage 3 cells have no D2 reference; fill-ins such as the definition of the D1.5/D3.0 shapes were fixed before the run (`docs/20`) and a different reading would give different new cells.
- The corrected C2 procedure is unverified. Power results are not size-adjusted.
- Nothing here supports any trading, profitability or performance statement.

## 9. Reproduce
```bash
python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python -m pytest -q                                   # 355 tests, synthetic data only
shasum -a 256 -c outputs/milestone4/h1_calibration/frozen_spec/FROZEN_v1.sha256   # and the other manifests (README)
python scripts/milestone4/stage1_run_baseline.py && python scripts/milestone4/stage1_summarise.py                         # Stage 1 (about 20 min)
python scripts/milestone4/stage2_run_c3_training.py                                                                        # C3 training (about 9 min)
python scripts/milestone4/stage2_run_development.py && python scripts/milestone4/stage2_summarise.py                        # E4 (about 16 compute-hours) and E5
python scripts/milestone4/stage2_run_power_check.py && python scripts/milestone4/stage2_make_report.py --tests "<pytest line>"
python scripts/milestone4/stage3_plan_tables.py                                                                            # Stage 3 plan tables
python scripts/milestone4/stage3_run_c3_intermediate.py                                                                    # 90/180-day C3 values (about 3 min)
python scripts/milestone4/stage3_run_validation.py && python scripts/milestone4/stage3_summarise.py                         # locked validation (about 1 compute-hour), run once
python scripts/milestone4/stage3_run_power.py && python scripts/milestone4/stage3_make_report.py --tests "<pytest line>"    # power cells (only if calibration passes) and the report
python scripts/milestone4/stage4_run_null_check.py && python scripts/milestone4/stage4_run_alt_validation.py                # Stage 4 A and B (about 5 min); run once
python scripts/milestone4/stage4_run_bar_level.py --part sims && python scripts/milestone4/stage4_run_bar_level.py --part matrix  # Stage 4 C (about 75 min)
python scripts/milestone4/stage4_run_reference.py && python scripts/milestone4/stage4_make_report.py --tests "<pytest line>"       # Stage 4 D and the report
```
The market data are not in the repository (README explains how to rebuild them); the Stage 1–4 scripts need only the simulated-data code.

## 10. Artifact index
- **Reports:** `docs/12` (M4b), `14` (Stage 0), `16` (Stage 1), `18` (Stage 2), `20` (Stage 3 pre-run record), `21` (Stage 3 report), **`22` (Stage 4 preregistration), `22b` (Stage 4 approval record), `23` (Stage 4 report), `24` (Stage 5 decision report)**, `25` (errata), `26`–`29` (Phase 6 protocol, register, Stage 0 checks, memo; proposed, unapproved), this report (`docs/19`); plans and records `docs/13`, `15`, `15a`, `15b`, `17`, `17b`, `17c`; index `docs/README.md`.
- **Frozen specifications and manifests:** `outputs/milestone4/h1_calibration/frozen_spec/`, `frozen_spec_v1_1/`, `frozen_stage2_inputs.sha256`, `frozen_stage2_inputs_addendum.sha256`, `frozen_stage3_inputs.sha256`, `frozen_stage4_inputs.sha256`, `stage2/c3_training/C3_TABLE.sha256`, `stage3/c3_intermediate/C3_INTERMEDIATE_TABLE.sha256`, `stage1/STAGE1_CODE.sha256`.
- **Results:** `stage1/`, `stage2/{c3_training,development,summary,power_check,report_tables}/`, `stage3/{c3_intermediate,validation,summary,power_check,report_tables}/`, `stage4/{null_check,alt_validation,bar_level,reference,report_tables}/`, plan tables `stage2_plan/`, `stage3_plan/`, `stage4_prereg/`, run logs `stage*_run.log`.
- **Code:** `src/quantlab/`, `src/quantlab/research/`, `scripts/milestone1-4/`, `tests/`.

## 11. The single most important next step
**Decide the next step after the PARTIAL classification** (`docs/24` §11): whether to authorise the optional real-data descriptive placement (no H1 statistic on real data), and whether to proceed to Option 1 wording or the research protocol. None of these is started or authorised.
