# 24 — H1 calibration, Stage 5 decision report

**Status:** Stage 5 (decision and reporting) written under the user's authorisation of 2026-11-10. **Documentation only: saved outputs were read; no simulation was run, no real market data was accessed, no frozen input, seed, threshold, acceptance criterion, method or historical record was changed, and nothing was committed or pushed.**
**Labels:** **[EVIDENCE]** read from saved files; **[PROTOCOL]** pre-specified or approved earlier; **[READING]** my interpretation; **[DECISION]** belongs to the user.

## 1. Decision

**Classification: PARTIAL (preliminary, as set by the user).**
C3, a fixed critical value per sample size, satisfied its pre-specified **upper rejection-rate limits** in every gated cell of the validated **simulated** domain (section 5) and on six alternative simulated processes, and all Stage 4 integrity checks passed. Its rejection rates are **conservative** (far below 5% in most cells). **Calibration on real market data is unverified.** The test is **not** described as universally calibrated, nor as valid on real markets.

Why PARTIAL and not PASS ([PROTOCOL], docs/13 Stage 5): a Pass is worded "calibrated within the validated domain (stated explicitly)". Here (i) the evidence is judged on upper limits only, so it shows the test does not over-reject, not that the rate is held near 5%; (ii) the domain is a simulated family whose relation to the real data was not checked (the optional real-data placement was not authorised); (iii) boundaries exist inside the family (section 5.3). Why not FAIL: no pre-specified gate for C3 failed in Stages 3 or 4.

## 2. Question and decision rule [PROTOCOL]
H1: does volatility differ across open, middle and close? The M4b baseline (iid-day bootstrap-t, B = 999) over-rejects the true null under heavy tails with uneven within-period shapes (4.6%–10.9% in Stage 1). docs/13 set up a staged investigation (Option 2, with fallback to Option 1: disclose the limitation) to find a corrected critical value; Stage 5 decides the wording of the conclusion. Candidate C3: critical value 3.298658 (59 days), 2.946701 (90), 2.880076 (125), 2.854727 (180), 2.816000 (250), frozen before validation. C1 was not selected; C2 is unverified and report-only (v1.1 A6) and plays no part in this decision.

## 3. Gate interpretation and its historical discrepancy

**Interpretation used (approved by the user, 2026-11-10):** for C3, a gated cell passes when its rejection rate is **at most the upper bound** of the cell's gate (v1.1 A2, `classify_cell(..., c3_mode=True)`). For the alternative processes the upper bound is 6.0%. The lower bound is not a requirement for C3.

**Discrepancy, with the original documents preserved unchanged:**

| Source | What it says |
|---|---|
| `docs/13` §4.6 [PROPOSED] | Alternative DGPs (Stage 4): "point estimate in **[4.0%, 6.0%]**" for each; tier A point estimate in [4.5%, 5.5%] and Wilson upper ≤ 6.0% in every cell. |
| `docs/15a` §3 gate table (frozen v1.1) | Alternative processes: 4.0% ≤ p̂ ≤ 6.0% (no Wilson clause). Separate **C3 row** only for tiers A and B: p̂ ≤ 5.5% (A), ≤ 6.0% (B). It has no C3 row for the alternative processes. |
| `docs/15a` A2, `spec_v1_1.json` (frozen) | `point_pass`: "… for C3 only p_hat <= hi"; `ambiguous`: "hi only for C3". |
| `docs/17` (Stage 2 plan), `docs/17b` D1, `docs/20` | C3 "gated on upper limits only"; used so in Stage 2 and Stage 3. |
| `docs/22` §4, `docs/22b` D5 (approved 2026-11-05, before any Stage 4 simulation) | "C3 passes an alternative-process cell when its rate is at most 6.0% (frozen v1.1 rule A2); the baseline remains reference-only." |

**What this means.** The text of A2 is general ("for C3 only p̂ ≤ hi"); the gate table in `docs/15a` has no C3 alternative-process row, so applying A2 to the alternative processes is an extension that was **made explicit only by D5**. The record `docs/15b` lists its approvals and does not itemise A2's C3-only clause; `docs/15a` still carries the header "PROPOSED for your review" (it is hashed and was not edited). I could verify the clause in the frozen files, in the code, in the use in Stages 2–3 and in D5; I could not find a single earlier record that approves the C3-only clause for the alternative processes by itself. The user has now confirmed the interpretation.

**Consequence if the original two-sided reading were applied.** [EVIDENCE] C3's alternative-process rates are 1.23%–4.41%; **11 of 12 cells are below 4.0%**, so a two-sided [4.0%, 6.0%] requirement would fail those cells for conservatism, not for over-rejection. The same would apply to the tier A band [4.5%, 5.5%] in Stage 3 (highest C3 tier A rate 2.98%). This is the reason the C3 reading is upper-limit only, and it is why the result is **PARTIAL**, not a calibration to 5%. The baseline, judged on the two-sided band, is reported as reference only (Stage 4: 6 FAIL and 3 FAIL_AMBIGUOUS of 12).

## 4. Why this report is docs/24 and not docs/14
`docs/13` names the Stage 5 report `docs/14_h1_calibration_results.md`. That number was written before the later stages; **`docs/14` is now the Stage 0 report** (`14_h1_calibration_stage0_report.md`), and documents 15–23 follow. Reusing 14 would overwrite a record, so the Stage 5 report is `docs/24_h1_calibration_stage5_decision_report.md`. `docs/13` is unchanged (this note is the only record of the renaming).

## 5. Validated domain [EVIDENCE: `frozen_spec/cells_validation.csv`, Stage 3 and Stage 4 summaries]

### 5.1 What was validated (all simulated; 3 stocks; H0 true by construction)
| Dimension | Values validated (gated cells) |
|---|---|
| Tail of shocks (Student-t df) | ∞ (G), 10, 7, 6 (tier A); 5, 4 (tier B) |
| Within-period shape | flat, E, D5, R2 (development); D1.5, D3.0 (new, 59 days only) |
| Market | NSE, US |
| Sample size | 59, 90, 125, 180, 250 days. Cells: 56 / 4 / 12 / 4 / 12 (gated). Only the five sizes with a frozen C3 value; **intermediate sizes are not validated**. |
| Dependence / day volatility | none (80 cells) and estimated (8 cells), day-factor sd 0.3 (84 cells) and 0.6 (4 cells) |
| Alternative processes (Stage 4, shape E, 59 days, NSE and US) | intraday volatility clustering, jumps, period-specific tails, stock-specific tails, heavy-tailed day factor, Laplace shocks |
Gated: 88 cells (tier A 54, tier B 34). Report-only: 8 cells at df 3.

### 5.2 Result inside the domain [EVIDENCE]
- Stage 3: **PASS_CLEAR**, 88 of 88 gated cells PASS for C3; highest rate tier A 2.98% (limit 5.5%), tier B 5.28% (limit 6.0%), lowest 0.59%; no cell above the 7.0% ceiling; 0 failed simulations.
- Stage 4: 12 of 12 alternative-process cells at most 6.0% (1.23%–4.41%); 0 ambiguous; null check, bar-level check (largest |z| 1.86), 80 matrices (3.59e-13) and the independent reference (4.77e-14, 100 of 100 identical decisions) all met.

### 5.3 Boundaries and thin coverage [EVIDENCE]
- **df 3 (report-only):** C3 rates 1.61%–6.24%; three cells at or above 5.2% (T3 E NSE 5.20%, T3 D5 NSE 6.13%, T3 D5 US 6.24%). The gated domain ends at df 4; **no claim is made for df 3 or heavier tails**.
- **Tier B headroom is small:** highest 5.28% against the 6.0% limit.
- **90 and 180 days:** 4 gated cells each, **all shape E, df 7 or 5, no dependence, day-factor sd 0.3**; C3 values there come from 12-cell families without estimated-dependence, 0.6-volatility, flat or R2 cells (A5 limitation).
- **Shapes D1.5/D3.0** only at 59 days; **day-factor sd 0.6** only in 4 cells; **estimated dependence** only in 8 cells.
- The alternative processes cover **one shape (E), one sample size (59 days)**.

## 6. Planned-versus-actual simulation counts and seed audit

### 6.1 Counts [EVIDENCE: row counts of saved parquet files, re-counted for this report]
| Component | Planned | Actual (rows) | Master seed | Status |
|---|---|---|---|---|
| Stage 1 baseline (68 cells) | 1,240,000 | 1,240,000 | 20261201 | equal |
| Stage 2 C3 training (68 files) | 1,700,000 | 1,700,000 | 20261202 | equal |
| Stage 2 development (76 cells) | 1,780,000 | 1,780,000 | 20261203 | equal |
| Stage 2 power check | 30,000 | 30,000 | 20261212 | equal |
| Stage 3 C3 training at 90/180 days (24 files) | 600,000 | 600,000 | 20261209 | equal |
| Stage 3 validation (96 cells) | 2,280,000 | 2,280,000 | 20261204 (rows 0–75), 20261205 (rows 76–95) | equal |
| Stage 3 power cells | 30,000 | 30,000 | 20261213 | equal |
| Stage 4 alternative processes (12 cells) | 300,000 | 300,000 | 20261206 | equal |
| Stage 4 bar-level simulations (8 cells) | 64,000 | 64,000 | 20261207 | equal |
| Stage 4 same-returns matrices | 80 | 80 | 20261207 | equal |
| Stage 4 reference datasets | 100 | 100 | 20261208 | equal |
| **Total simulations, Stages 1–4** | 8,024,000 | 8,024,000 | – | equal |
(The null-check bars, 5×10⁷ per process/market cell, are not counted as simulations; M4a/M4b and Stage 0 are earlier work in docs/09–14.) Failed simulations: Stage 3 0 (baseline and C3), Stage 4 0 in B and 0 invalid in C.

### 6.2 Seed audit
Registered master seeds 20261201–20261209 and 20261212–20261213 were all used; each is distinct. Per-simulation seeds are full-width `SeedSequence(master, spawn_key=…)` objects. **Reserved and never used:** 20261210 (ambiguity replication, not needed: no ambiguous C3 cell in Stages 3–4) and 20261211 (candidate revision, not authorised). Stage 4's null check used a namespace under 20261206 (first key ≥ 100); the reference's analysis seed 20261215 is analysis only. No seed was reused to rerun a validation cell (run-once rule held in Stages 3 and 4).

## 7. Development versus validation evidence [EVIDENCE]
| | Stage 2 development (76 cells, 1,780,000 sims) | Stage 3 validation (96 cells, 2,280,000 sims) |
|---|---|---|
| C3 outcome | all 68 gated cells pass | **PASS_CLEAR**, 88 of 88 |
| C3 highest / lowest gated rate | 5.25% / 0.49% | 5.28% / 0.59% |
| Baseline (reference) | 28 FAIL, 8 FAIL_AMBIGUOUS of 68 | 40 FAIL, 17 FAIL_AMBIGUOUS of 88 |
| C1 (not selected) | 3 FAIL, 9 FAIL_AMBIGUOUS | not run |
- **Repeat of the 76 development cells with fresh seeds:** the mean difference in rejection rate (Stage 3 minus Stage 2) is +0.0001 points for C3 and −0.0001 points for the baseline; 152 comparisons, of which **2 have |z| > 3** (baseline val row 25, z = −3.13; C3 val row 30, z = +3.31) and 9 have |z| > 2 (about 8 expected by chance for 152 comparisons at 5%; 2 above 3 against about 0.4 expected). These are preserved and reported, not explained away; both are within the gated ranges.
- **The 20 new cells never used in development** (10 tier A, 10 tier B): C3 highest 2.43% (tier A) and 3.56% (tier B); all PASS. Their rates are lower than the development maxima, so there is no sign that C3 was tuned to the development cells.
- C3's training families and critical values were frozen before validation; no retuning followed a validation result.

## 8. Failure and limitation audit
**Preserved non-passes and flags [EVIDENCE]:**
- Baseline: 40 FAIL and 17 FAIL_AMBIGUOUS of 88 in Stage 3; 9 of 12 alternative cells outside its two-sided band in Stage 4 (reference only).
- C1: 3 FAIL and 9 FAIL_AMBIGUOUS in Stage 2; 4 D7 violations; 52 D2 flags; not selected.
- C3 D2 (judgement-based conditional-behaviour diagnostic): 143 of 320 computable comparisons flagged in Stage 3, 34 of them for C3; 32 C3 comparisons in the 16 cells with no matched df ∞ reference are **not computable** and no substitute was invented. In Stage 4, D2 is not computable (no df ∞ reference); descriptive C3 leverage spread median 3.29 points, maximum 7.89. docs/13 requires conditional behaviour to be reported, not gated.
- df 3 report-only cells (section 5.3).
- Two |z| > 3 repeat comparisons (section 7).

**Limitations [READING where not stated as evidence]:**
1. **Simulation only.** Real-data behaviour is untested; the optional descriptive placement of the real data on the grid was out of scope. It is unknown whether the real NSE/US data lie inside the domain.
2. **Conservatism.** The test rejects far below 5% (median 1.8% in Stage 3, 1.97% in Stage 4). Power cost [EVIDENCE, Stage 3 power cells, 5,000 each]: T4 flat ×1.1: C3 12.3% (NSE) and 19.2% (US) against the baseline's 29.9% and 40.7%; T4 flat ×1.2: C3 81.8% and 89.3% against 86.1% and 89.7%; E ×1.2: C3 54.2% and 62.0% against 64.6% and 71.5%. Power results are not size-adjusted.
3. **C3 is limited by its training families** (44 cells at 59 days, 12 at each other size); the maximum over noisy quantiles is biased upward (conservative).
4. **Stage 4 limits:** null check cannot verify 2.7%–16.9% of the variance of processes c and d by Monte Carlo (analytic constants instead); bar-level check cannot detect differences below about 1 point; the reference implementation shares its author and dataset generator.
5. **Judgement-based thresholds** (D2, D4) and fill-ins (D1.5/D3.0 definitions) were fixed before the runs; different readings would give different cells.
6. **Not validated:** other sample sizes, df 3 or heavier, non-iid days, other numbers of stocks, other markets, other processes, real data.

**Unresolved items (carried over, none affects the simulated results):** C2 unverified against the original paper (A6); stale wording in hashed `docs/17b` and the `d2_flag` docstring (blocker B10); `docs/15a` header still reads "PROPOSED" (hashed); gate-wording discrepancy (section 3); Stage 2–5 work uncommitted; licence not chosen.

## 9. What this establishes and does not establish
**Establishes (simulated evidence):** within the validated domain, C3 did not reject a true H1 null more often than 5.5% (tier A) or 6.0% (tier B and the alternative processes) in any gated cell, including 20 never-developed cells and six alternative generating processes; the result is reproducible (fast route and real bar-level route agree, an independent exact-arithmetic implementation agrees); and C3 is, by comparison, more conservative than the baseline, which does over-reject in the same family.
**Does not establish:** that the rate is near 5% (it is not: C3 is conservative); validity on real market data or any empirical relation; validity outside the domain; adequate power in all settings; that any volatility pattern exists in NSE or US data; anything about H2, H3 or trading. **No profitability or market claim is made.**

## 10. Verification summary
Run when this report was finished (2026-11-10):
| Check | Result |
|---|---|
| Test suite (`python -m pytest -q`) | **355 passed, 0 failed**, 3 pre-existing warnings (`h2_volume.py:157`), 84 s |
| Manifests | all 9 verify: v1 23, v1.1 7, Stage 1 code 8, Stage 2 inputs 18, addendum 2, Stage 2 C3 table 2, Stage 3 inputs 12, 90/180-day table 2, Stage 4 inputs 21 (0 mismatches) |
| Output digests, recomputed | Stage 3 validation `c39310c13539afece74f252c…` and summaries `433a08e72c905dd9b10b8a51…` equal `docs/21`; Stage 4 null check `7d570f8f…`, alternative processes `77cd77c2…`, bar level `d2d753cd…`, reference `44394a0c…` equal `docs/23` |
| Row counts | re-counted from saved parquet files: all equal the plan (section 6.1) |
| Files under `src/`, `scripts/`, `tests/`, `outputs/` newer than the Stage 4 report | **none**: no script, test, frozen input, seed table or simulation output was changed during Stage 5 |
| Temporary or incomplete files | none (`*.tmp` count 0) |
| Git | HEAD still `080f5be`; **nothing committed or pushed**; tracked files modified: `README.md`, `docs/README.md`; everything else untracked |
| Files created by Stage 5 | `docs/24_h1_calibration_stage5_decision_report.md` (this report) |
| Files modified by Stage 5 | `docs/19_quantlab_project_status_report.md`, `README.md`, `docs/README.md` (status text only) |
| Real data / simulations | none accessed or run |

## 11. Decisions that remain with you
(1) Whether a real-data descriptive placement (no H1 statistic on real data) should be authorised separately; (2) whether and how to proceed to Option 1 wording or to the research protocol (`docs/07`, not started, not authorised); (3) how to treat C3's conservatism and power cost in any protocol; (4) commit and push of the Stage 2–5 work; (5) licence; (6) the stale-wording and C2 items. **Nothing beyond Stage 5 has been started.**
