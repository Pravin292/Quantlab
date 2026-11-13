# 22b — Stage 4 approval record (decisions D1–D6 on docs/22)

**What this is:** the written record of the user's approval of the Stage 4 preregistration (`docs/22`), made 2026-11-05 BEFORE any Stage 4 simulation. `docs/22` is not edited; **where this record differs from docs/22, this record governs.** It is hashed in `frozen_stage4_inputs.sha256`. Nothing in the frozen v1/v1.1 specifications, seeds, thresholds, critical values or manifests changes.

| ID | Decision | Notes |
|---|---|---|
| D1 | **Approved:** the null-check design of docs/22 §3, including the truncated-moment check for processes c and d; the literal **0.5%** tolerance is preserved | The limitations are documented in the report: for c and d the variance beyond the 99.9% cutoff (about 8–17%) is not verified by Monte Carlo and rests on exact analytic unit-variance scale constants and the tail-probability tests |
| D2 | **Approved with a change:** **8,000** bar-level simulations per cell (not 2,000) | 8 cells × 8,000 = 64,000 bar-level simulations; the power calculation for 8,000 is in docs/22 §5 (75% at a 1-point difference) |
| D3 | **Approved:** acceptance is |z| ≤ 3 for every comparison (C3 and baseline, 16 comparisons); same-returns matrices within **1e-9** | The multiple-comparison analysis is preserved (about 4.2% family-wise false-flag rate at 8,000 per cell, 4.5% at 2,000); **every individual comparison is reported, including values between 2 and 3** |
| D4 | **Approved:** the 10 cells (val rows 14, 34, 50, 60, 77, 3, 9, 11, 43, 45), 100 datasets, seed convention, tolerances 1e-9 (statistic) and 1e-12 (quantile), identical C3 decisions required | `stage4_prereg/reference_selection.csv` |
| D5 | **Approved:** C3 passes an alternative-process cell when its rate is **at most 6.0%** (frozen v1.1 rule A2); the baseline remains reference-only | |
| D6 | **Approved:** freeze the Stage 4 inputs manifest and execute Stage 4 under docs/22 and this record | Conditions: no change to the design after freezing; no real-data descriptive analysis; no Stage 5, H2, H3, candidate revision; nothing committed or pushed; an unfavourable or inconsistent result is documented as it is and no acceptance criterion is changed to obtain a pass |

## Fill-ins made while implementing (all inside the approved design)
1. **Bar-level bootstrap stream:** `SeedSequence(20261207, spawn_key=(cell_index, i, 2))` (stream 0 = bar-level data, stream 1 = same-returns check, stream 2 = the baseline bootstrap). docs/22 §7 listed streams 0 and 1.
2. **Null-check batches:** 20,000 days per batch; batch `b` of combination `idx` uses `SeedSequence(20261206, spawn_key=(100 + idx, b))`; idx 0–7 = processes a, b, e, f × (NSE, US) in that order; idx 8–11 = truncated-moment checks c (NSE, US), d (NSE, US).
3. **Cell index of the bar-level check:** 0–7 = Stage 3 validation rows 2, 3, 4, 5, 26, 27, 28, 29.
4. **Order of work:** the null checks must pass before the alternative-process run; the bar-level and reference checks are independent of that gate.
5. **Near-boundary listing** in the reference check (|T − critical value| below 1e-6 relative) is informational.
