# 17b — Stage 2 design decisions: review record

**What this is:** the written record of your ten Stage 2 design decisions (D1–D10) on `docs/17_h1_calibration_stage2_plan.md`. It sits **outside** every frozen manifest (v1, v1.1, Stage 1 code); no frozen file is edited. Where this record differs from docs/17, **this record governs** (listed in section 3).
**Date:** 2026-11-02. **Source:** your messages of this date.

## 0. What this record does NOT authorise
**Not authorised, not done:** writing the Stage 2 runner, the C3 training run, the development run, the power check, any simulation, any other stage. This is approval of the design decisions and compute logistics only. Your separate, explicit execution approval is required, and a second explicit go after the C3 table is shown (D8).

## 1. The ten decisions

| ID | Decision (as approved) | Notes and labels |
|---|---|---|
| **D1** | **C1 is preferred if both C1 and C3 qualify; C3 is a labelled fallback.** | *Reason:* C1's decision adapts to each dataset through its fitted bar-level null model, keeps power, and is judged on a two-sided gate that shows actual calibration. C3 is a family-wide maximum: conservative in benign worlds (power loss), valid only inside its training family, with nothing from the sample except T, and judged only on upper limits. This changes the v1 "simplest first" tie-break wording for this case, by your approval. |
| **D2** | Conditional-calibration flag: the spread across quartiles (max − min rejection rate) exceeds **1.25 × the Gaussian reference spread** of the same shape, market and sample size **and** the excess is **at least 2 percentage points**. | **Label: judgement-based diagnostic threshold, not a statistical theorem or test.** Reference = the df ∞ cell matched by shape, market and sample size (**confirmed**). In 12 cells that reference does not match dependence / day-volatility; see section 5a. |
| **D3** | A **small, pre-specified early-warning power check** in development. It must not influence candidate selection rules and must not be presented as validation. | Specification in section 2. **Seed 20261212 CONFIRMED by you (2026-11-02).** |
| **D4** | `PASS_AMBIGUOUS` counts as a pass and is listed. `FAIL_AMBIGUOUS` blocks advancement. **Investigate when 10 or more of the 44 tier A cells are ambiguous.** No automatic replication. | **Labels:** the threshold is a *judgement value*. The 0.8% reference probability assumes (i) every tier A cell has a true rate of exactly 5.0%, giving a per-cell ambiguity probability of 9.6% at n = 25,000, and (ii) the 44 cells are independent (true by the seed scheme: different datasets per cell). Real candidates have unequal true rates, so the 0.8% is a yardstick, not the size of a test. |
| **D5** | **No candidate revisions during Stage 2.** Any revision needs a new numbered specification version, your explicit approval and the reserved development seed **20261211**. | Candidates C1 and C3 are fixed as in docs/17 §3. |
| **D6** | A *failure* = non-finite statistic, critical value or p-value, or a raised error. Failures are **excluded from the denominator and reported separately** (per method and cell), and the rate counting failures as non-rejections is also shown. A method-cell whose failure rate exceeds **0.1%** (more than 25 of 25,000; more than 10 of 10,000) is **blocked** pending your approval of a fallback. | **CONFIRMED (2026-11-02):** the 0.1% blocking threshold applies **only to gated cells**. Report-only df 3 cells (10,000 sims, no gate) above 0.1% are flagged and reported but **do not block** advancement. |
| **D7** | The critical-value variability rule (candidate CV ≥ baseline CV is a failure condition) applies to **40 cells: the 24 tier B cells plus the 16 tier A cells at 125 and 250 days.** C3 is exempt (constant critical value). CV is **reported in all cells**. | CV = standard deviation divided by mean of the per-simulation critical value over the cell's valid simulations (as in Stage 1). The rule is applied to C1; the baseline's CV comes from the same datasets. |
| **D8** | Approved: a resumable compute run, **with a pause after the C3 training run**. **The frozen C3 training table is shown to you before the main run starts.** No automatic early stopping. Runtime and completed cells are reported accurately. **You retain the right to stop the run.** | The C3 table is hashed and frozen before the main run, as planned. Per-cell output files make resuming exact. |
| **D9** | **C2 is skipped in Stage 2.** It stays report-only and unverified (A6); no Stage 2 result about C2 exists. | Changes docs/17 §3, §6, §7 and §10 (section 3 below). Its random stream `(dev_row, i, 3)` is reserved and unused. |
| **D10** | Ambiguity flags are used during Stage 2. **No automatic replication.** Replication still requires your written approval of the exact cell list (and applies only in Stage 3/4 under the rule in docs/15b §4). | Unchanged from docs/15b. |

## 2. D3 power check — specification (confirmed 2026-11-02)
Scope confirmed by you on 2026-11-02; this is what will be implemented:
- **When:** after the development run, only for candidates that meet the calibration conditions of docs/17 §10 A.1–A.5; run on **development-type** data and never reported as validation.
- **Cells:** T4 shape flat with open/close variance multiplier ×1.1 and ×1.2, and T4 shape E ×1.2, both markets, 59 days, no dependence → **6 cells × 5,000 simulations = 30,000 simulations per method**; the baseline runs on the same datasets as a reference.
- **Reporting:** power with Wilson intervals, paired with the baseline. The only flag is the existing v1 failure condition: candidate power below **70% of the baseline's at T4 flat ×1.2**. Caveat to state with results: the baseline's size is distorted in heavy-tailed shaped cells (E: about 7–8% null rejection), so its power there is not a fair yardstick; only the near-nominal T4 flat cells are used for the flag.
- **Role:** a diagnostic warning for you. It does not enter the advance rule, does not rank candidates, and does not select anything. Power is never used to choose among candidates.
- **Seed [CONFIRMED]:** the dedicated master seed **20261212** (`SeedSequence(20261212, spawn_key=(power_cell, i, k))`, k = 0 data, 1 baseline, 2 C1). Checked 2026-11-02: it appears in no script, source, test or output of the project, and differs from every registered seed (Stage 1 20261201; C3 training 20261202; development 20261203; validation 20261204/20261205; alternative processes 20261206; pipeline checks 20261207/20261208; C3 intermediate sizes 20261209; ambiguity replication 20261210; reserved revision seed 20261211) and from all earlier project seeds (20261030–20261103, M4b 2026107x/2026108x). The power check therefore shares no random stream with any other stage.
- **Cost:** about 0.1 hour.

## 3. Where this record supersedes docs/17
| docs/17 location | Superseded by |
|---|---|
| §3 table, C2 row ("run because it costs about 6%") | D9: C2 is not run in Stage 2 |
| §6 runtime table and totals | Recomputed below |
| §7 seed table, C2 row | Stream `(dev_row, i, 3)` unused |
| §8 diagnostics, any C2 items | Not produced in Stage 2 |
| §10 and §12 wording of D1–D10 | The decisions in section 1 |

**Updated compute estimate (C2 removed) [ESTIMATE]:** development run 1,780,000 simulations × (data + baseline + C1): **10.95 h** at the benchmark speed-up, 10.96 h with measured speed-ups, **11.2 h** with the Stage 1 per-simulation overhead (+2 ms). Plus C3 training 0.1–0.6 h and the power check about 0.1 h → **about 11.3–12 h central**; benchmark ±30% gives about 8–15.5 h; if the whole estimate were off by the Stage 1 factor (×2.05) about 23 h. C3 training: 1,700,000 simulations, seed 20261202. Development run: seed 20261203.

## 4. Unchanged and preserved
Grid (76 cells, 1,780,000 simulations per method; 68 gated), candidates C1 and C3 (baseline reference only), gate bounds, seed scheme (apart from the unused C2 stream), the three Stage 1 open items deferred to a later diagnostic stage, all frozen files and manifests (v1 23 hashes, v1.1 7 hashes, Stage 1 code 8 hashes), M4b outputs, Stage 0 and Stage 1 results.

## 5. Confirmations
| Item | Status |
|---|---|
| Power-check seed 20261212, recorded, no overlap | **CONFIRMED** |
| df 3 failures: 0.1% blocking applies to gated cells only; df 3 cells flagged, never blocking | **CONFIRMED** |
| Power-check scope: six cells (T4 flat ×1.1, ×1.2; T4 E ×1.2; both markets; 5,000 simulations each) and the single flag (power below 70% of the baseline's at T4 flat ×1.2); diagnostic-only, not for selection or validation | **CONFIRMED (2026-11-02)** |
| D2 reference spread = the df ∞ cell matched by shape, market and sample size | **CONFIRMED (2026-11-02)**; the 12-cell limitation and its handling are fixed in section 5a (documentation only; no cell added, no decision changed) |

## 5a. D2 reference rule: handling of the 12 cells without a fully matched reference
**Rule preserved (D2, approved and confirmed):** the reference spread is the df ∞ cell matched by shape, market and sample size. Nothing in D1–D10 changes and no cell is added to the frozen grid.

**How the reference is computed (all cells):** the quartile spread (max − min rejection rate) of a method is compared with the spread of **the same method and the same conditioning variable** (leverage, kurtosis, or the method's own critical value) in the reference cell. C3's critical value is constant, so for C3 only leverage and kurtosis apply.

**The limitation [VERIFIED from `outputs/milestone4/h1_calibration/stage2_plan/stage2_cells_plan.csv`].** The frozen development grid has df ∞ cells only with no dependence and day-volatility 0.3. Twelve gated cells differ from their df ∞ reference in dependence or day-volatility:

| Group | Cells | dev_row | Tier | n_days | Differs from the reference in | Counts toward the advancement rule (docs/17 §10 A.5)? |
|---|---|---|---|---|---|---|
| **In scope** | 4 × T4, estimated dependence (E, D5 × NSE, US) | 44–47 | B | 59 | dependence | **Yes** (inside the 40-cell scope: 24 tier B + 16 tier A at 125/250 days) |
| **In scope** | 4 × T4, day-volatility 0.6 (E, D5 × NSE, US) | 48–51 | B | 59 | day-volatility | **Yes** (same 40-cell scope) |
| **Outside scope** | 4 × T6, estimated dependence (E, D5 × NSE, US) | 40–43 | A | 59 | dependence | **No** (tier A at 59 days; reported only) |

So **8 cells are inside the 40-cell advancement scope** (32 of those 40 have a fully matched reference) and **4 additional tier A gated cells are outside it**. All 8 df 3 report-only cells have exact references.

**Handling (documentation rule, to be implemented as written):**
1. For these 12 cells the reference is the available df ∞ cell with **dependence = none and day-volatility = 0.3** of the same shape, market and sample size.
2. Every D2 flag, and every D2 spread comparison, computed in these 12 cells is labelled **"reference not matched on dependence / day-volatility"** in the output tables and in the report.
3. **This comparison is less reliable:** dependence or higher day-volatility could change the quartile gradient even in a Gaussian world, so a flag (or its absence) here may reflect the unmatched reference and not the method. Such flags are not treated as stronger evidence than flags in the 32 matched cells.
4. *Consequence within the existing rules (no new rule):* a marked D2 flag in one of the 8 **in-scope** cells counts like any D2 flag under docs/17 §10 B ("investigate, do not advance"), and you always make the final advancement decision; the label is there so you can weigh it. D2 flags in the 4 **outside-scope** cells are reported only and do not enter the advancement rule.
5. The unmatched reference is a property of the grid, not something Stage 2 can repair; any matched Gaussian references (dependence or 0.6 volatility) would need new cells and a numbered new specification version, which you have not requested.

## 6. Final execution checklist (NOTHING BELOW HAS BEEN DONE)
Each item needs your **explicit execution approval** before it starts. Sequence and gates:

| # | Step | Output (new paths) | Gate before the next step |
|---|---|---|---|
| E0 | Re-verify hashes: v1 23, v1.1 7, Stage 1 code 8; confirm `stage2/` and `stage2_power/` folders are absent or empty; record package versions | check printed in the log | any mismatch stops everything |
| E1 | Write `scripts/milestone4/stage2_run_c3_training.py`, `stage2_run_development.py`, `stage2_run_power_check.py`, `stage2_summarise.py`, helper module `src/quantlab/research/h1_stage2.py`, and `tests/test_research_h1_stage2.py` | code and tests only | tests pass, including: seed uniqueness for all (cell, i, k) streams and no shared master seed (20261201–20261212); determinism and exact resume; baseline/C1/C3 applied to the same dataset (identical T); C1 uses frozen `c1_test` unchanged; C3 equals `T > crit`; failure counting; no C2 code path run; gate and flag logic of D2/D4/D6/D7 against hand-computed cases, including that D2 flags in the 12 cells of section 5a carry the label "reference not matched on dependence / day-volatility" and that the 4 outside-scope cells never enter the advancement rule |
| E2 | Freeze inputs: new manifest `outputs/milestone4/h1_calibration/frozen_stage2_inputs.sha256` (plan tables, runner, helper, tests, docs/17b); verify it | manifest + verification | you may review the code first |
| E3 | **C3 training run only:** 68 gated development cells × 25,000 = 1,700,000 simulations, seed 20261202, statistic T only; output `outputs/milestone4/h1_calibration/stage2/c3_training/` and the critical-value table (0.95 quantile of T per cell, maximum per sample size 59/125/250), hashed as `C3_TABLE.sha256` | table + log (about 0.1–0.6 h) | **PAUSE (D8): I show you the frozen table; no main run without your second go** |
| E4 | **Main development run:** 76 cells × (25,000 / 10,000) = 1,780,000 simulations, seed 20261203, baseline + C1 + C3 on the same dataset, per-cell parquet, resumable, no early stopping, `caffeinate` | `outputs/milestone4/h1_calibration/stage2/development/` (about 11–12 h central, range 8–15.5, worst case about 23) | runs to completion unless you stop it; I report cells completed and elapsed time exactly |
| E5 | Summaries and diagnostics: gate statuses, ambiguous-cell count against the yardstick of 10, failures, CV rule in the 40 cells, D2 flags (the 12 cells of section 5a labelled "reference not matched on dependence / day-volatility"; 8 in scope, 4 outside scope reported only), Stage 1 plumbing check (30 cells), conditional calibration, paired comparison | `stage2_*` CSVs | none |
| E6 | **Early-warning power check** (only for candidates meeting docs/17 §10 A.1–A.5 and only if you want it run): 6 cells × 5,000 = 30,000 simulations per method, seed 20261212 | `outputs/milestone4/h1_calibration/stage2/power_check/` (about 0.1 h) | diagnostic only |
| E7 | Stage 2 report `docs/18_...` with every cell, failures, limitations (docs/17 §9) and the advance / investigate / no-candidate outcome; stop and wait | report | **no Stage 3 without your approval** |

**Remaining prerequisites (design is complete; these are all that stand between this record and execution):**
1. **Your explicit execution approval** (separate from every design confirmation so far). I will start only with E0 and E1 (verification, then writing code and tests) unless you also approve E3.
2. **Disk space:** this machine shows only 5.4 GiB free (98% full). Stage 2 needs about 0.5 GB (all project outputs together are 224 MB today), so it fits, but please do not let other jobs fill the disk; I will check free space before E3 and E4 and stop if it drops under 2 GiB.
3. **Machine availability:** about 11–12 h central (worst case about 23 h) of the 8 cores, unattended, awake (`caffeinate`) and preferably on power; the run is resumable if it is interrupted.
4. **Environment unchanged:** Python 3.12.13, numpy 2.5.4, pandas 3.1.0, scipy 1.18.1 (as in the frozen spec); I will re-check and abort on a difference.
5. *Resolved:* the D2 reference handling for the 12 cells without a fully matched reference is fixed in section 5a (flag applied, labelled, less reliable); no further decision is needed.

**Not part of Stage 2 and not started:** C2 runs, ambiguity replication, Stage 3, Stage 4, Stage 1b (HB sensitivity, sharpness arm, oracle map), H3, M5, real-market H1/H2/H3 tests.
