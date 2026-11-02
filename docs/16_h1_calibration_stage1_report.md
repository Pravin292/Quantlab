# 16 — H1 calibration, Stage 1 report (baseline mechanism diagnosis)

**What this shows:** the null rejection rate of the M4b baseline (bootstrap-t, `rom`, max rule, iid days) across the frozen 68-cell Stage 1 grid, and what the cells say about hypotheses HA–HE. **All data are simulated; null only; baseline only (no C1, C2, C3); no real-market test.** Stage 2 has not started.
**Reproduce:** `python scripts/milestone4/stage1_run_baseline.py` (about 20 min, 8 cores; refuses to run on a hash mismatch or a non-empty output folder), then `python scripts/milestone4/stage1_summarise.py`.
**Files:** `outputs/milestone4/h1_calibration/stage1/` — `cell_00..67.parquet` (per-simulation rows), `stage1_cell_summary.csv`, `stage1_hc_quartiles.csv`, `stage1_hb_effective_bars.csv`, `stage1_he_bootstrap_size.csv`, `stage1_count_check.csv`, `run_metadata.csv`, `STAGE1_CODE.sha256`; log `outputs/milestone4/h1_calibration/stage1_run.log`. Launch conditions and implementation fill-ins: `docs/15b`.

Labels: **[VERIFIED]** = computed by code from saved files; **[INTERPRETATION]** = my reading, not proved.

## 1. Counts and integrity [VERIFIED]
- 68 cells, 1,240,000 planned = 1,240,000 run; **0 failed** simulations (non-finite statistic or error) in any cell; every simulation index unique in every cell.
- Seeds: master 20261201, `SeedSequence(master, spawn_key=(cell_row, i))`, one generator per simulation; 400 sampled seeds all distinct (the full uniqueness is by construction and is tested on 4,000).
- Hashes after the run: v1 23 of 23, v1.1 7 of 7, Stage 1 code manifest 8 of 8. Full test suite 297 passed (243 earlier + 30 for v1.1 + 24 for Stage 1 helpers), 0 failed; tests are implementation checks, not statistical validation.
- Replicates: T4 · E · NSE appears three times with independent seeds (HA 7.99%, HB g=1 8.01%, HE B=999 7.76% with n=5,000) and M4b found 7.9%.

## 2. Rejection rates, HA tail scan (59 days, 20,000 simulations per cell) [VERIFIED]
Nominal 5%. Wilson 95% half-width ≈ 0.3 points.

| tail | flat NSE / US | E NSE / US | D5 NSE / US |
|---|---|---|---|
| df ∞ (t1000) | 4.9 / 4.9 | 5.1 / 5.1 | 5.2 / 5.3 |
| df 20 | 4.8 / 4.8 | 5.6 / 5.0 | 5.2 / 5.3 |
| df 10 | 4.7 / 5.1 | 5.5 / 4.8 | 5.7 / 5.5 |
| df 8 | 4.6 / 4.6 | 5.5 / 5.4 | 5.9 / 5.9 |
| df 6 | 4.7 / 5.0 | 6.4 / 5.8 | 6.2 / 6.3 |
| df 5 | 4.9 / 4.8 | 6.7 / 6.0 | 7.1 / 6.8 |
| df 4 | 5.3 / 4.8 | 8.0 / 7.0 | 8.2 / 8.1 |
| df 3 (report only) | 5.8 / 4.7 | 9.6 / 7.8 | 10.0 / 10.9 |

Range over the 48 cells: 4.6% to 10.9%.

## 3. Gate outcomes for the baseline [VERIFIED; informational, see docs/15b §6 item 5]
Classifier of spec v1.1 (tier A: df ∞, 20, 10, 8, 6; tier B: df 5, 4; df 3 report-only), applied to the baseline as a diagnostic subject, not as a candidate:

| Status | All 68 cells | HA 48 cells |
|---|---|---|
| PASS | 14 | 14 |
| PASS_AMBIGUOUS | 12 | 12 |
| FAIL | 28 | 12 |
| FAIL_AMBIGUOUS | 8 | 4 |
| REPORT_ONLY (df 3) | 6 | 6 |

Baseline outcome on the tail-scan grid would be **FAIL** under the v1.1 rule (clear FAILs at df 8 D5, df 6 E/D5, df 5, df 4 with E/D5). All flat-shape gated cells point-pass (df 3 flat is report-only). The gates were designed for 25,000-simulation candidate comparisons; Stage 1 cells have 20,000 or 5,000.

## 4. What the cells say about the hypotheses
**HA — heavier tails raise the rejection rate.** [VERIFIED] With the E and D5 shapes the rate rises with tail heaviness: ≈5% at df ∞, 5.5–5.9% at df 8–10, 6–7% at df 5–6, 7–8% at df 4, 10% at df 3. [INTERPRETATION] The rise is gradual from about df 8; there is **no cliff at df 4** (the infinite-variance boundary of squared returns), and df 5 and 6 are already clearly above 5% in NSE. So the specific "boundary" form of HA is not supported; a "more tail, more inflation" form is.
**Shape is a second ingredient.** [VERIFIED] With the flat shape the gated cells stay at 4.6–5.3% even at df 4 (5.3, 4.8); the report-only df 3 flat cells are 5.8% (NSE, above 5%) and 4.7% (US). The large inflation needs an uneven within-period profile (E or D5) as well as heavy tails; df 3 flat NSE shows some excess on its own.
**HB — effective bar count.** [VERIFIED] Merging 1 → 2 → 3 bars lowers the T4 rate: NSE E 8.0 → 7.4 → 7.1; US E 6.7 → 6.3 → 6.2; NSE D5 8.3 → 7.7 → 7.1; US D5 8.0 → 7.8 → 7.1. The reduction is about 1 point and never reaches 5%. [INTERPRETATION] This is **not a clean test** of the effective-bar idea: merging also lowers the per-bar tail weight (kurtosis of merged squares falls from 9.8 to 7.9 to 7.0), and the profile-based effective bar count *falls* when bars are merged (e.g. NSE D5 open 2.2 → 1.3 → 1.1). The sharpness arm (tau 0.37, 1, 2, 4) listed in docs/13 was not in the frozen Stage 1 grid and was **not run**. HB is therefore only weakly supported (less heavy terms help a little) and not resolved.
**HC — the critical value tracks the sample.** [VERIFIED] The bootstrap critical value's coefficient of variation is 0.04 (df ∞ flat) and 0.39–0.45 (df 4 E and D5). Spearman correlation between T and the critical value is −0.02 to −0.07 for Gaussian and flat cells and −0.15 to −0.19 for T4 E/D5. Rejection by critical-value quartile for T4 E NSE is 19.0 / 9.2 / 3.2 / 0.5% (docs/13 found 16.8 / 9.4 / 3.4 / 0.4% on different data), and for T4 D5 NSE 20.1 / 8.5 / 3.4 / 0.7%. The pattern replicates. [VERIFIED] A conditional gradient also exists in Gaussian cells (D5 NSE: 8.2 / 6.1 / 4.6 / 1.9%), so a conditional gradient alone is not heavy-tail specific; what the heavy-tail cells add is its steepness and the marginal excess. [INTERPRETATION] Consistent with the diagnosis in docs/13 that the critical value is mis-targeted and highly variable, not uniformly too small. Not proof of mechanism.
**HE — bootstrap size.** [VERIFIED] B = 999 versus 9,999 (independent datasets, 5,000 each): differences +0.6 (NSE D5), +0.0 (US D5), −0.6 (NSE E), +0.3 (US E) points, every 95% interval about ±1 point and including 0. [INTERPRETATION] No evidence that B causes the inflation; the test cannot detect differences below about 1 point.

## 5. Limits of Stage 1
- Null only, 59 days, no dependence, one day-volatility level; says nothing about power or the other sample sizes.
- Merge definition and the df ∞ coding are my fill-ins (docs/15b §6 items 1–2); the HB result depends on that definition.
- Pivotality map and the oracle critical value by (df, shape) listed in docs/13 were not part of the frozen Stage 1 cells and were not computed.
- Nothing here selects or favours C1, C2 or C3; C2 remains unverified and report-only.

## 6. Not started
Stage 2, Stage 3, Stage 4, ambiguity replication, H3, M5, any real-market H1/H2/H3 test. Waiting for your review.
