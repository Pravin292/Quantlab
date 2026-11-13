# 20 — Stage 3 pre-run record (locked validation of C3)

**What this is:** the written record, made BEFORE any Stage 3 data exist, of the authorisation, the exact frozen specification being run, the fill-ins for details the frozen text leaves open, and the rules for what happens next. It is hashed in `frozen_stage3_inputs.sha256` before the run. Nothing here changes a frozen specification.
**Date:** 2026-11-05. **All data are simulated.**

## 1. Authorisation and scope
- **User decision (2026-11-05):** C3 is designated the **sole candidate** for Stage 3 locked validation; **C1 is not selected for advancement**; the existing frozen protocol and C3's frozen critical values are used; the candidate, critical values, thresholds, methodology and protocol must not be modified; all failures, ambiguities, D2 flags and limitations are preserved; nothing is committed or pushed.
- **Runs in Stage 3:** C3 (candidate, frozen values) and the M4b baseline (bootstrap-t, B = 999) as a **reference only**, on the same datasets (the fair-comparison rule of spec v1). **Not run:** C1 (not selected), C2 (unverified, report-only), ambiguity replication, Stage 4, Stage 5.
- **Not authorised by the Stage 3 decision:** Stage 4, Stage 5, any candidate revision, replication, the research protocol, real-market tests.

## 2. The frozen specification being executed
- **Grid:** `outputs/milestone4/h1_calibration/frozen_spec/cells_validation.csv`, 96 cells, 2,280,000 simulations = the 76 development cells re-run with **fresh seeds** (rows 0–75, master 20261204) + 20 new intermediate cells (rows 76–95, master 20261205): df 7 (tier A) and df 5 (tier B) with shape E at 59, 90, 180 days and shapes D1.5, D3.0 at 59 days, both markets. Tier A 54 cells, tier B 34, df 3 (report-only) 8; gated cells 88.
- **Gates (v1.1):** C3 is judged on **upper limits only**: rate at most 5.5% (tier A) or 6.0% (tier B); df 3 report-only; ceiling 7.0%; statuses and candidate outcome by `h1_calibration_v11.classify_cell/classify_candidate` (PASS, PASS_AMBIGUOUS, FAIL, FAIL_AMBIGUOUS; PASS_CLEAR, MARGINAL_NOT_DEMONSTRATED, FAIL_BOUNDARY_ONLY, FAIL). The conservatism of C3 (lowest cell rate) is reported.
- **C3 values:** 59, 125, 250 days from the frozen Stage 2 table (`stage2/c3_training/c3_critical_values.csv`: 3.298658, 2.880076, 2.816000). 90 and 180 days from a training run required by spec v1.1 A5 BEFORE validation (section 3.3).
- **Run once:** no cell is re-run or retuned. An unfavourable result is reported as it is. A cell file that exists but is incomplete stops the run for a report; it is never recomputed automatically.
- **Failure conditions (docs/13 §4.7) that apply:** any tier A cell outside its gate; any tier B cell outside its gate (domain would be narrowed to df ≥ 6); numerical failures above 0.1% in a gated cell. Alternative-process and implementation-agreement conditions belong to Stage 4.
- **Power cells (docs/13):** T4 flat ×1.1, ×1.2 and T4 E ×1.2, both markets, 5,000 simulations each, "reported only after calibration passes"; flag if C3 power is below 70% of the baseline's at T4 flat ×1.2; never used for selection.

## 3. Fill-ins (details the frozen text leaves open; decided here, before the run)
1. **New shapes D1.5 and D3.0:** exponential profiles `exp(−j/τ)` in the open, mirrored in the close, equal RMS per period, with **τ = 1.5 and τ = 3.0**. The existing D5 shape uses τ = 2.0 (`run_h1_inference.profile_for`), so the new shapes bracket it ("decay scale between those used", docs/13).
2. **df 7** = Student-t(7), scaled to unit variance as for every tail; df ∞ is Student-t(1000), as in M4b and Stages 1–2.
3. **C3 at 90 and 180 days:** per v1.1 A5, 12 cells per size (tails G, T6, T4 × shapes E, D5 × NSE, US), 25,000 simulations each (24 cells, 600,000), seed 20261209 as `SeedSequence(20261209, spawn_key=(row, i))` with `row` the row of `cells_c3_training_intermediate.csv`; value = maximum over the 12 cells of the 0.95 quantile of T; frozen and hashed (`C3_INTERMEDIATE_TABLE.sha256`) before validation. **Limitation to be stated wherever used:** a 12-cell family (no dependence, no 0.6-volatility, no flat/R2 shapes), so C3 is less conservative there and valid only inside that family.
4. **Per-simulation seeds:** `SeedSequence(master, spawn_key=(validation_row, i, stream))`, stream 0 = data, 1 = baseline bootstrap; C3 needs no random draws. Full width, no truncation.
5. **Power seed:** a new master seed **20261213** (not used anywhere; the registry of 13 master seeds is distinct), `spawn_key=(power_cell, i, stream)`.
6. **Condition for running the power cells:** the C3 candidate outcome is PASS_CLEAR or MARGINAL_NOT_DEMONSTRATED (no FAIL, FAIL_BOUNDARY_ONLY). Otherwise they are not run and the report says so.
7. **D2 in Stage 3:** the same formula as Stage 2 (`spread − 1.25 × reference ≥ 0.02`, fractions, a judgement-based diagnostic), computed for the baseline (reference) and C3, where the frozen grid contains a df ∞ reference matched on shape, market and sample size. For the **16 cells with no such reference** (90 and 180 days; shapes D1.5 and D3.0) D2 is **not computable as specified** and is reported as such; no substitute reference is invented. The Stage 2 "40-cell advancement scope" and the D4/D7 rules were defined for the development stage and are not applied as advancement rules in Stage 3. The 12 cells with unmatched dependence or day-volatility keep the label "reference not matched on dependence / day-volatility".
8. **Comparison with Stage 2:** for the 76 re-run cells the Stage 3 and Stage 2 rates (independent seeds) are compared by a two-sample z; descriptive.

## 4. Order of work
1. Freeze these inputs (`outputs/milestone4/h1_calibration/frozen_stage3_inputs.sha256`: plan tables, runners, helper, tests, this record).
2. Train the 90/180-day C3 values, then freeze them.
3. Run the 96-cell validation once; summarise.
4. Run the power cells only under fill-in 6.
5. Write the Stage 3 report (docs/21); update the project status report, README and docs index.

## 5. What remains after Stage 3 (dependency chain, to be inspected after the run)
Stage 4 (docs/13 §4): alternative processes a–f (parameters frozen in v1.1 A4, process e as approved), bar-level pipeline check, second reference implementation, optional descriptive real-data check (needs separate approval; no H1 statistic on real data), then a review gate. Stage 5: decision report ("calibrated within the validated domain", partial, or unresolved). Neither is authorised by the Stage 3 decision.
