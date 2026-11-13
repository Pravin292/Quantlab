# 28 — Stage 0 reference layout verification for Mode B (read-only) — documentation only

**Status:** written 2026-11-13. **Read-only verification.** No real market data was accessed; no simulation was run; no random number was generated; no H1 statistic, rejection rate or critical value was computed; D6 was not authorised; `docs/26` and `docs/27`, source code, tests, manifests and outputs were not modified; nothing was committed or pushed. The Stage 0 reference file was opened only to read its structure, and it contains simulated worlds only.

**Labels:** **VERIFIED** supported by evidence in the file, metadata or code; **NOT VERIFIED** cannot be established from what was read; **CONTRADICTED** the evidence disagrees with the protocol statement; **NOT APPLICABLE** an assumption or label that no file can confirm.

## 1. Verification scope
Question: does the existing Stage 0 reference file support the Mode B rules of `docs/26` revision 5 (section 8.2, Mode B paragraph; section 12; section 16)? Open item from `docs/27` (§4, §7 item 2, §10): whether the Stage 0 worlds' layout equals the validated 59-session layout.
**Not opened, deliberately:** `real_tail_statistics.csv` and `observed_vs_reference.csv`, which hold real-data statistics, and the real-data folders. Nothing was inferred, interpolated or approximated for any missing dimension.
**Evidence used:** the reference CSV; `run_metadata.csv` (parameters only); the generating script `scripts/milestone4/stage0_real_data_descriptive.py`; the simulator and helper code it calls (`direct_sim.simulate_returns_sq`, `direct_sim.used_slot_index`, `h1_calibration.fit_bar_model`, `tail_descriptives.tail_summary`); `docs/14` §6 and `docs/26`.

## 2. Exact source file inspected
| Item | Value |
|---|---|
| Path | `outputs/milestone4/h1_calibration/stage0/real_data_descriptive/reference_known_df_distribution.csv` |
| Size | 61,169 bytes; last modified 2026-11-01 02:55 (same as the other four files in the folder) |
| Rows / columns | 576 data rows (577 lines with header) / 9 columns |
| Columns | `market, scope, true_df, statistic, ref_mean, ref_q05, ref_q50, ref_q95, reps` |
| Producer | `scripts/milestone4/stage0_real_data_descriptive.py`, master seed 20261102 (per `run_metadata.csv`) |
| Modified by me | No |

## 3. Actual reference file structure
- **Markets (2):** NSE, US.
- **Scopes (4):** all, open, middle, close. **No per-stock scope.** Each scope is pooled over the 3 stocks of the market (the script builds one 3-stock simulated panel per repetition).
- **True df (8):** 3, 4, 5, 6, 8, 10, 20, 1000.
- **Statistics (9):** `kurtosis`, `max_abs_z`, `share_abs_z_gt_3_per_1000`, `share_abs_z_gt_4_per_1000`, `share_abs_z_gt_5_per_1000`, `hill_alpha_top1pct`, `hill_alpha_top2pct`, `hill_alpha_top5pct`, `hill_alpha_top10pct`.
- **Reference quantities:** `ref_mean`, `ref_q05`, `ref_q50`, `ref_q95`.
- **Repetitions:** `reps` = 200 in every row.
- **Completeness:** 2 × 4 × 8 × 9 = 576 = rows; no duplicate key; no missing combination.
- **Parameters not stored as columns** (from `run_metadata.csv` and the script): day-factor sd 0.3; no volatility clustering inside a day, no price rounding, no cross-stock shock dependence; Student-t shocks only (`standard_t`); the slot profile used is the **fitted profile of the real sample for that market** (`profile` built from `model.v2` of the real data), not one of the frozen simulator shapes; the number of days is `len(dates)` of the real clean sample; the number of stocks is the number of real symbols per market.
- **Dimensions the file does not have:** sample size n (no column), shape, day-factor sd, dependence, Laplace or any non-Student-t shock, per-stock scope, fit-noise or profile-distance statistics, alternative-process features.

## 4. Dimension-by-dimension compatibility table
| Dimension | Mode B requirement (`docs/26`) | File evidence | Result |
|---|---|---|---|
| Rows / structure | one single-variant file | 576 rows, one variant | VERIFIED |
| Market | NSE and US | both present | VERIFIED |
| Scopes | all, open, middle, close | exactly these four | VERIFIED |
| Per-stock scope | none | none | VERIFIED (absent) |
| df grid | 3, 4, 5, 6, 8, 10, 20, 1000 (1000 as ∞) | identical set | VERIFIED; "1000 as ∞" is an assumption: NOT APPLICABLE to the file |
| Repetitions | 200 per df | `reps` = 200 everywhere | VERIFIED |
| Statistics M2, M3 (5%), M4 | kurtosis; Hill 5%; exceedances of \|z\| > 4 per 1,000 | `kurtosis`, `hill_alpha_top5pct`, `share_abs_z_gt_4_per_1000` present (plus Hill 1/2/10%, exceedances at 3 and 5, `max_abs_z`) | VERIFIED |
| Quantiles | 5%, 50%, 95% | `ref_q05`, `ref_q50`, `ref_q95` (plus `ref_mean`) | VERIFIED |
| Day-factor sd | 0.3 only | `run_metadata.csv`, script (`day_vol_sd=0.3`); not a column | VERIFIED by metadata |
| Shape variants | none | one profile per market, but it is the **real sample's fitted profile**, which `docs/26` does not say | VERIFIED (no variants); undocumented property noted |
| Sample size n | n = 59 only | **no n column**; days = `len(dates)` of the real sample; `docs/14` §3 gives "60 dates" and §6 "3 stocks, 60 days"; US standardised-bar count in `docs/14` §6 (13,777) exceeds 3 × 59 × 77 = 13,629 | **CONTRADICTED** (n = 60 on the available evidence) |
| Laplace | none | Student-t only | VERIFIED (absent) |
| Fit-noise | none | no profile or RMSD statistic | VERIFIED (absent) |
| Used slots / layout | validated layout (NSE 71, US 77 used slots) | `used_slot_index` is the same function the validation scripts use (`stage3_common.py`); `docs/14` §6: 71 and 77 used slots | VERIFIED for slots and 3 stocks; n differs (above) |

## 5. D-tail availability assessment
- **Statistics and quantiles:** all of M2, M3 (5%) and M4 (> 4) exist with q05 and q95 for all eight df, both markets, and the by-period scopes, so the ingredients of R_S(d) = [q05, q95] are present.
- **n = 59:** **not supported as written.** The file has no n dimension, and the evidence indicates its worlds used the real sample's 60 days, not 59. `docs/26` §8.2 says D-tail is classified only "for n = 59" using this file. Using a 60-day reference for a 59-session block would be an approximation, and `docs/26` §8.2 forbids substitute or workaround references. I did not test how much the two differ and did not compute anything.
- **Other n (90, 125, 180, 250):** **unavailable.** The file has a single, unlabelled n. The protocol's D-TAIL-NO-REFERENCE rule for n ≠ 59 is consistent with the file, but the premise "n = 59 is available" fails.
- **The day-count is inferred, not read from the file.** The direct confirmation would be the `days` field of `real_tail_statistics.csv`, which I did not open because it holds real-data statistics. `docs/14` and the script both point to 60.
- **Also undocumented in `docs/26`:** the reference profile is the fitted real-sample profile, not one of the frozen shapes. How it relates to the validated shapes E, D5, R2 or flat was not computed.

## 6. D-alt availability assessment
Alternative feature (d) needs a per-stock reference range. The file has no per-stock scope (each repetition pools 3 stocks, and no per-stock statistic is written). **Unavailable, as `docs/26` states.** Consequently D-alt is U in every Mode B block, reason D-ALT-NO-PER-STOCK-REFERENCE. No substitute (for example deriving a per-stock range from pooled values) was attempted. The other alternative features (c: by-period) have the open, middle and close scopes available for the tail statistics; I did not assess the feature definitions beyond that.

## 7. Laplace and fit-noise availability assessment
- **Laplace:** not present (the script draws `standard_t` shocks only). Unavailable; LAPLACE-UNEVALUATED stands.
- **Fit-noise (M8) reference:** not present (no profile fit or distance is stored). Unavailable; SHAPE-THRESHOLDS-UNCHECKED stands.
- Neither can be approximated from this file.

## 8. Mode B readiness conclusion
Claim-by-claim check of the Mode B paragraph and related statements of `docs/26`:

| # | Claim in `docs/26` | Class | Evidence |
|---|---|---|---|
| 1 | The reference is the file `reference_known_df_distribution.csv`, simulated worlds only | VERIFIED | §2; script draws simulated returns only |
| 2 | 200 repetitions per df | VERIFIED | `reps` = 200, all 576 rows |
| 3 | df 3, 4, 5, 6, 8, 10, 20, 1000 | VERIFIED | `true_df` set |
| 4 | df 1000 is treated as ∞ | NOT APPLICABLE | stated as an assumption; the file labels it 1000 |
| 5 | day-factor sd 0.3 only | VERIFIED | `run_metadata.csv`, script |
| 6 | no shape variants | VERIFIED | one profile per market; but it is the real sample's fitted profile (not stated in `docs/26`) |
| 7 | scopes all, open, middle, close for each market | VERIFIED | §3 |
| 8 | statistics: kurtosis, Hill 1/2/5/10%, \|z\| exceedance counts | VERIFIED | §3 (plus `max_abs_z`) |
| 9 | quantiles 5%, 50%, 95% | VERIFIED | `ref_q05/50/95` |
| 10 | no per-stock scope | VERIFIED | §3 |
| 11 | no Laplace worlds | VERIFIED | Student-t only |
| 12 | no fit-noise reference | VERIFIED | none stored |
| 13 | D-alt is U because no per-stock reference exists | VERIFIED | follows from 10 |
| 14 | D-tail classifiable for n = 59 with M2 = kurtosis, M3 = Hill 5%, M4 = exceedance > 4 | **CONTRADICTED** in the n = 59 part; VERIFIED in the statistic and quantile part | the file has no n; evidence says n = 60 |
| 15 | for n ≠ 59 D-TAIL-NO-REFERENCE | VERIFIED as a consequence (no other n exists), but its premise (n = 59 is covered) fails | §5 |
| 16 | Stage 0 worlds' layout equals the validated 59-session layout (marked UNRESOLVED in `docs/26`) | **CONTRADICTED** for the session count (60 against 59); NOT VERIFIED for exactness of the other layout parts beyond slots and 3 stocks | §4 |
| 17 | single-variant: nothing approximates a four-variant envelope | VERIFIED | one variant only |

**Conclusion.** Stage 0 supports the statistics, quantiles, markets, scopes, df grid and repetition count that Mode B describes, and it confirms the stated absences (per-stock, Laplace, fit-noise). It does **not** support the claim that D-tail can be classified at n = 59: the reference worlds were generated for the real sample's day count (60 on the available evidence), the file does not record n, and `docs/26` forbids approximation. **Mode B is not ready to be used as written.** What to do about it (amend `docs/26` in a numbered revision, restrict Mode B to a descriptive report without D-tail, or produce a 59-day reference, which would be new simulation) is **your decision**; this verification does not choose and changes no rule. As `docs/26` already says, Mode B yields no coverage label in any case, so the finding affects the content of the Mode B measurement report (and the exactness of its reasons), not whether coverage labels are possible.

## 9. Outstanding limitations
1. The day count of 60 rests on `docs/14` and the generating code; the direct field was not read (kept closed on purpose). A read of its `days` column, or of the script's inputs, would settle it; that opens real-data statistics and needs your say-so.
2. Whether the fitted real-sample profile differs materially from the validated shapes is not known; not computed.
3. The effect of 60 versus 59 days on the reference quantiles is unknown; not computed (it would need simulation or a new reference).
4. Which statistic "pooling" the reference uses across the three stocks matches the protocol's per-panel measurement is assumed, not checked end to end.
5. `docs/27` records the Stage 0 layout check as outstanding; this document shows it is **not resolved in favour of Mode B** and leaves `docs/26` and `docs/27` unedited. Their statements that the matter is "UNRESOLVED" remain true of the decision; the factual evidence is now here.
6. D1–D17, the mode declaration, provider and licence items remain as recorded in `docs/27`. Nothing here approves or authorises anything.

## 10. Git status and restriction compliance
- HEAD: `080f5be29d5a70e86dbaaa5eac135be932ed6187`.
- Tracked modifications: README.md and docs/README.md (Stage 5, unchanged). Untracked: as before plus `docs/27` (previous task) and this file.
- No file other than `docs/28` was created or changed by this task. `docs/24`, `docs/25`, `docs/26`, `docs/27`, C3, source code, tests, manifests and outputs are untouched (manifest verification and modification times are reported in the chat summary).
- Restrictions respected: no real data opened (the two real-statistics files were left closed), no simulation, no random numbers, no H1 statistic or critical value, no D6, no change to Mode A or Mode B rules, nothing committed or pushed.
