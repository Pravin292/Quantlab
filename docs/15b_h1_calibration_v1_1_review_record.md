# 15b — Review record for spec v1.1 and Stage 1 launch

**What this is:** the written record of the user's decisions on spec v1.1 and of the Stage 1 launch conditions. It sits **outside** the frozen v1.1 manifest on purpose (the v1.1 files still say "PENDING YOUR APPROVAL" for process e; they are not edited because that would change their hashes — this record supersedes that wording).
**Date of the decisions:** 2026-11-02. **Source:** the user's messages of this date.

## 1. Approvals recorded

| # | Decision | Status |
|---|---|---|
| 1 | Process e replacement (Gaussian scale mixture), with exact parameters and the deviation from frozen v1 documented (section 2) | APPROVED |
| 2 | Provisional C3 training families at 90 and 180 days, with the stated coverage limitations (section 3) | APPROVED, provisional |
| 3 | Ambiguity-replication seed scheme `SeedSequence(20261210, spawn_key=(file_id, row))`, 100,000 fresh simulations per approved ambiguous cell | APPROVED |
| 4 | Replication rule (section 4) | APPROVED |
| 5 | This separate record, outside the v1.1 manifest | APPROVED |
| 6 | C2 stays report-only and unverified | CONFIRMED |
| 7 | **Stage 1: baseline-only calibration across the frozen 68-cell grid** | **APPROVED (launch condition list in section 6)** |
| – | Stage 2, Stage 3, Stage 4, ambiguity replication, H3, M5 | **NOT approved, not started** |

Frozen files: v1 (23 files, `FROZEN_v1.sha256`) and v1.1 (7 files, `FROZEN_v1_1.sha256`) are preserved unchanged. Both manifests are re-verified by the Stage 1 runner itself before any simulation, and it stops on any mismatch.

## 2. Process e — recorded deviation from frozen v1
- **v1 / docs/15 wording:** log day factor f = 0.3 · Student-t(3) / √3.
- **Why it cannot be run:** a Student-t variable has no moment-generating function, so E[e^{2f}] is infinite. The expected squared return, and hence the estimand, would not exist.
- **Replacement (Gaussian scale mixture):** f ~ N(0, 0.253546²) with probability 0.95, and f ~ N(0, 0.760639²) with probability 0.05, independent across stocks. The large sd is 3× the small one; the overall sd is exactly 0.3 (variance 0.95·0.253546² + 0.05·0.760639² = 0.09).
- **Return:** r = profile · e^f · ε, ε ~ Student-t(8) multiplied by √(6/8) = 0.866025 (unit variance).
- **Variance normalisation:** E[e^{2f}] = 1.2394 (finite), the same for every slot, so it cancels in period ratios; the shock part has second moment exactly 1 (tested to 1e-9); the shape profile keeps equal period means.
- **Status:** deviation from frozen v1, approved. Where: `alt_dgp_parameters.json` (v1.1). Used only in Stage 4, which is not started.

## 3. C3 at 90 and 180 days — limitations to state wherever C3 is reported
Training families have 12 cells (tails G, T6, T4 × shapes E, D5 × NSE, US), 25,000 simulations each, seed 20261209. They contain no estimated-dependence cells, no 0.6 day-volatility cells and no flat or R2 shapes, so they cover fewer scenarios than the 44-cell family at 59 days. C3 is therefore less conservative at 90, 125, 180 and 250 days and is valid only inside its training family. No statement of general validity will be made for C3. Approval is provisional.

## 4. Ambiguity-replication rule (final text)
1. **When:** only after the single Stage 3 validation run (gated cells of the one selected candidate) or after the Stage 4 alternative-process run. Ambiguity in development cells is reported, nothing else.
2. **Trigger:** the candidate's outcome is `MARGINAL_NOT_DEMONSTRATED` or `FAIL_BOUNDARY_ONLY`. I then list the ambiguous cells and stop. `FAIL` and `PASS_CLEAR` trigger nothing.
3. **Approval:** replication starts only after the user approves **in writing the exact list of ambiguous cells**.
4. **Run:** those cells only, 100,000 fresh simulations each, same method and settings. Cell master seed: `SeedSequence(20261210, spawn_key=(file_id, row))`, `file_id` 0 = `cells_validation.csv`, 1 = `cells_alternative_dgps.csv`, `row` = 0-based row in that file; simulation i uses spawn_key `(file_id, row, i)`.
5. **Outcome:** the point rule and the ambiguity flag are applied to the replication estimate alone. The replication estimate **replaces** the original; **no pooling**. The candidate outcome is recomputed with the replaced cell statuses.
6. **Final:** a cell still ambiguous at n = 100,000 keeps the final status `MARGINAL_NOT_DEMONSTRATED` (or `FAIL_BOUNDARY_ONLY`). **No second replication** is permitted and the seed is never reused.

## 5. C2
Report-only and **unverified** until the formula is independently verified against the original paper. No validity claim, no methodological conclusion, no selection (A6). It is not part of Stage 1.

## 6. Stage 1 launch conditions and confirmations

**Scope.** The M4b baseline only: bootstrap-t, statistic `rom`, max rule, iid days, B as in the cell (999, or 9,999 in the HE cells). **No C1, C2 or C3.** Null only (no effect planted). Simulated data only.

**Grid (frozen `cells_stage1.csv`, 68 cells, 1,240,000 simulations).**

| Experiment | Cells | Simulations per cell | Simulations |
|---|---|---|---|
| HA tail scan: df ∈ {∞, 20, 10, 8, 6, 5, 4, 3} × shape {flat, E, D5} × {NSE, US}; 59 days | 48 | 20,000 | 960,000 |
| HB effective bars: T4 × {E, D5} × merge {1, 2, 3} × {NSE, US} | 12 | 20,000 | 240,000 |
| HE bootstrap size: T4 × {E, D5} × {NSE, US} × B ∈ {999, 9,999} | 8 | 5,000 | 40,000 |
| **Total** | **68** | | **1,240,000** |

**Seeds.** Master seed 20261201 (`spec_v1.json`). Simulation i of cell row r (0-based row of `cells_stage1.csv`) uses `np.random.SeedSequence(20261201, spawn_key=(r, i))`, full width, one generator per simulation: data first, then the bootstrap draws. No seed is shared between cells or simulations (tested); no truncation to 32 bits (the M4b practice that produced harmless coincidences).

**Saved per simulation (hypothesis HC):** the three t-statistics, T = max |t|, the bootstrap critical value, a rejection flag, a validity flag (failures are counted, never dropped), the kurtosis of slot-standardised squares, and the largest single-day share of each period's total.

**Implementation details that v1 leaves open (filled in here; no frozen file changes; flag for review):**
1. *df ∞* is coded as Student-t(1000), as in M4b (practically Gaussian), not as an exact normal.
2. *"Merge g consecutive bars"* is defined as: within each period, the used 5-minute **returns** are summed in consecutive groups of g (squared after summing), each squared sum is divided by its group size, and the period mean is taken over groups. Groups are anchored at the session edge (open: from the open; close: from the session end; middle: from its start) so that a short leftover group falls on the quiet inner side. When a period's bar count is not a multiple of g the expected period means would no longer be exactly equal under the null; a **fixed constant per period** (derived from the profile, not from data) restores equality exactly (constants between 1.00 and 1.12; `null_scale`). With g = 1 the code reproduces the M4b simulator bit for bit (tested).
3. *HE:* each B-cell is its own cell with its own seeds (unpaired), as the frozen cell file lists them; the B = 999 cells are also replicates of the HA T4 and HB g = 1 cells.
4. *Shape names* flat, E, D5 map to the M4b profiles (`run_h1_inference.profile_for`); day-volatility sd 0.3; no cross-stock dependence; 3 stocks; 59 days.
5. *Gate outcomes for Stage 1* are **informational**: the v1.1 cell classifier is applied with tier A for df ∞, 20, 10, 8, 6, tier B for 5 and 4, df 3 report-only. The gates were designed for 25,000 simulations and candidate comparison; Stage 1 cells have 20,000 or 5,000 simulations and the baseline is a diagnostic subject, not a candidate.
6. *Failures:* a simulation whose statistic or critical value is not finite, or that raises an error, is counted as failed and excluded from the rejection-rate denominator; counts are reported per cell.
7. *Code manifest:* `STAGE1_CODE.sha256` in the Stage 1 output folder records the hashes of the runner, helper module, their tests and the M4b files it uses, at launch.

**Not started and not to be started without a new approval:** Stage 2, Stage 3, Stage 4, ambiguity replication, H3, M5, any real-market H1/H2/H3 test.
