# 15a — H1 calibration specification v1.1 (change log, definitions, gates)

**What this is:** the written record of addenda A1–A6 approved for incorporation into spec v1.1. **Status: PROPOSED for your review. No experiment has run. Stage 1 has not started.** v1 is untouched.
**Reproduce the files:** `python scripts/milestone4/stage0_freeze_spec_v11.py` (refuses to overwrite). **Verify:** `shasum -a 256 -c outputs/milestone4/h1_calibration/frozen_spec_v1_1/FROZEN_v1_1.sha256` and the same for `…/frozen_spec/FROZEN_v1.sha256`, both from the repository root.

## 1. Change log

| ID | What changed in v1.1 | Where |
|---|---|---|
| A1 | New corrected C2, named **"FDB-like procedure, formula UNVERIFIED"**. v1 C2 code and text stay as they were (frozen, defective). | `h1_calibration_v11.py::fdb_like_test`, `spec_v1_1.json` |
| A2 | Exact cell statuses (PASS, PASS_AMBIGUOUS, FAIL, FAIL_AMBIGUOUS), candidate outcomes, replication rule. | `h1_calibration_v11.py::classify_*`, `spec_v1_1.json` |
| A3 | Wilson-upper clause and 7% ceiling documented as redundant at n ≥ 10,000, with exhaustive evidence. | `gate_redundancy_check.csv` |
| A4 | Exact alternative-process parameters and null-preserving normalisations. **One content change (process e), needs your decision.** | `alt_dgp_parameters.json` |
| A5 | C3 at 90 and 180 days: separate training, 12-cell families, new seed 20261209. | `cells_c3_training_intermediate.csv` |
| A6 | C2 may be reported, never used for conclusions, selection or validity claims until verified. | `spec_v1_1.json` |
| – | New seeds 20261209 (C3 intermediate training) and 20261210 (ambiguity replication); neither collides with a v1 seed. | `spec_v1_1.json` |

Nothing else changed. Estimand, statistic, α, C1, C3 at 59/125/250 days, all grids, the gate bounds and tiers, v1 seeds and failure conditions are as in v1.

## 2. Exact definitions

**Common (unchanged).** Day matrix M (n days × 3 periods: open, middle, close). For a contrast (a, b): θ = ln(X̄_a / X̄_b), standard error from the influence function (sd(u)/√n, ddof 1). T = max over the three contrasts of |θ/se|. Reject H0 (equal period RMS volatility) at α = 0.05.

**A1 — FDB-like procedure (UNVERIFIED).**
1. Outer: B = 999 day-resamples M\*_b; T\*_b = max_c |(θ\*_c − θ_c)/se\*_c|.
2. Inner: one day-resample M\*\*_b of each M\*_b; T\*\*_b = max_c |(θ\*\*_c − θ\*_c)/se\*\*_c|.
3. p1 = (1/B) Σ 1{T\*_b ≥ T}; Q = the (1 − p1) quantile of {T\*\*_b} (linear interpolation).
4. **p_fdb = (1/B) Σ 1{T\*_b > Q}**; reject iff p_fdb ≤ 0.05.
v1 used 1{T\*\*_b > Q}, which equals p1 up to rounding. The corrected formula comes from my derivation of Beran's double-bootstrap logic plus a recollection returned by a search tool. **I have not read the original paper.** It is therefore not attributed to Davidson–MacKinnon or to anyone.

**A2 — statuses.** For a cell with k rejections in n valid simulations: p̂ = k/n; Wilson 95 % interval [L, U], z = 1.959964.
- *point_pass:* lo ≤ p̂ ≤ hi, and (tiers A, B) U ≤ the Wilson limit, and p̂ ≤ 0.07. For C3 only p̂ ≤ hi.
- *ambiguous:* a bound that applies (lo and hi; hi only for C3) satisfies L ≤ bound ≤ U.
- *status* = PASS / FAIL, with suffix _AMBIGUOUS when ambiguous.

| Candidate outcome | Condition |
|---|---|
| **FAIL** | at least one gated cell is FAIL |
| **FAIL_BOUNDARY_ONLY** | no FAIL, at least one FAIL_AMBIGUOUS. Decision remains "not selected" |
| **MARGINAL_NOT_DEMONSTRATED** | every gated cell point-passes, at least one is PASS_AMBIGUOUS. No claim of calibration |
| **PASS_CLEAR** | every gated cell is PASS |

*Replication rule:* only with your explicit approval, never automatic. The ambiguous cells alone, 100,000 simulations, fresh seed 20261210, same method. The decision uses the replication estimate alone (the original estimate is discarded, no pooling, to avoid optional stopping). If still ambiguous, the final status stays MARGINAL_NOT_DEMONSTRATED and there is no further replication.

## 3. Gates (v1 bounds, unchanged)

| Cells | Point rule | Wilson-upper clause | Simulations |
|---|---|---|---|
| Tier A (df ∞, 10, 7, 6) | 4.5 % ≤ p̂ ≤ 5.5 % | U ≤ 6.0 % | 25,000 |
| Tier B (df 5, 4) | 4.0 % ≤ p̂ ≤ 6.0 % | U ≤ 6.5 % | 25,000 |
| Tier C (df 3) | report only | – | 10,000 |
| Alternative processes | 4.0 % ≤ p̂ ≤ 6.0 % | – | 25,000 |
| C3 | p̂ ≤ 5.5 % (A), ≤ 6.0 % (B) | – | 25,000 |

A candidate passes only if every gated cell passes. No averaging; "the interval includes 5 %" is never used. Ceiling: no gated cell above 7.0 %.

**A3 — what the extra clauses do.** Exhaustive over every k, with and without them:

| n | tier A decisions changed by Wilson clause | tier B | ceiling |
|---|---|---|---|
| 1,000 | 10 | 11 | 0 |
| 2,000 | 11 | 12 | 0 |
| 5,000 | 8 | 10 | 0 |
| ≥ 10,000 (10k, 20k, 25k, 50k, 100k) | **0** | **0** | 0 |

So at the planned 25,000 simulations removing them changes no decision; they only bind in cells with fewer than about 10,000 valid simulations. A 500-step scan first finds them redundant at n = 8,500 (A) and 9,500 (B); redundancy is not claimed for untested n. Source: `gate_redundancy_check.csv`. (My earlier draft sentence "redundant at every n ≥ 5,000" was wrong and was corrected before freezing.)

## 4. A4 — alternative processes (exact)

Common: 3 stocks, shape E, 59 days, NSE and US, 25,000 simulations, H0 true by construction, day factor f ~ N(0, 0.3²) unless stated, unit-variance shocks. Student-t(ν) is multiplied by √((ν−2)/ν) for unit variance.

| ID | Exact specification | Null-preserving normalisation | Check |
|---|---|---|---|
| a | h₀ ~ N(0, 0.25²); h_j = 0.9 h_{j−1} + √(1−0.9²)·0.25·η_j; r = profile·e^f·e^{h−0.25²}·ε, ε ~ t(6) | e^{−σ²} on the amplitude, since E e^{2h} = e^{2σ²} | quadrature gives 1.000000000 |
| b | r = profile·e^f·(0.9619 ε + J), ε ~ t(10); per bar and stock, with prob. 0.002, J = ± U(4, 8), else 0 | E J² = 37.333; jump share 0.07467; shock multiplier √(1−0.07467) = 0.9619 | analytic 1.000000000 |
| c | ε ~ t(4) in open and close, t(8) in middle | unit variance each | multipliers tested |
| d | ε ~ t(3), t(5), t(8) for stocks 1, 2, 3 | unit variance each (t3 × 1/√3) | multipliers tested |
| e | **see below** | – | analytic 1.000000000 |
| f | ε ~ Laplace(scale 1/√2), f ~ N(0, 0.3²) | variance 2b² = 1 | analytic 1.000000000 |

**Process e is a content change, not a normalisation.** The v1 / docs/15 wording had the log day factor f ~ 0.3·t(3)/√3. A Student-t variable has no moment-generating function, so E[e^{2f}] is infinite: the expected squared return, and with it the estimand, would not exist (the null would be meaningless). v1.1 instead uses a Gaussian scale mixture: f ~ N(0, 0.2535²) with probability 0.95 and N(0, 0.7606²) with probability 0.05, overall sd exactly 0.3, shocks t(8). E[e^{2f}] is finite. **This needs your approval; if you reject it, process e is dropped rather than run as originally worded.**

A Monte-Carlo period-mean check (within 0.5 % at 10⁶ bars) is still required in Stage 4 before use; the analytic checks above are tested now. Processes with infinite fourth moments (c, d) cannot be verified to 0.5 % by Monte Carlo, which is why their unit-variance multipliers are checked analytically.

## 5. A5 — C3 at 90 and 180 days

Before v1.1 C3 was undefined for the validation cells at 90 and 180 days. Now: for each size train a separate critical value on 12 cells (tails G, T6, T4 × shapes E, D5 × NSE, US), 25,000 simulations per cell (24 cells, 600,000 simulations, generation-only about 0.05 hours), seed 20261209, disjoint from every development and validation seed. crit_n = the maximum over the 12 cells of the 0.95 quantile of T; reject when T > crit_n. Applies to validation cells T7 and T5 (shape E) at 90 and 180 days. The 59-day cells keep crit₅₉ from the 44-cell development family.
**Limitation:** like 125 and 250 days, these families have 12 cells (no estimated-dependence, no 0.6 day-volatility, no flat or R2 shapes), so C3 is less conservative there than at 59 days and valid only inside its family.

## 6. A6 — restrictions on C2 (any version)
- Results may be run and reported, labelled **"FDB-like procedure, formula UNVERIFIED"**.
- Not used for any methodological conclusion, candidate selection or ranking, and not called validated, calibrated, or the Davidson–MacKinnon method.
- The restrictions lapse only after you record that the formula was verified against the original paper.
- Selecting it even then needs your explicit written approval of a "procedure-defined, simulation-evidence-only" status.

## 7. Verification

- **v1 manifest:** `shasum -a 256 -c …/frozen_spec/FROZEN_v1.sha256` → 23 of 23 OK (also guarded by a test).
- **v1.1 manifest:** `FROZEN_v1_1.sha256` hashes 7 files (4 spec files, the v1.1 module, this script, the v1.1 test file) → 7 of 7 OK. This document is not in the manifest because it quotes the hashes.
- **Tests:** `tests/test_research_h1_calibration_v11.py` (30 tests). They check code behaviour (hand-computed p-values, edge cases p1 = 0 and 1, that v1.1 uses the same random draws as v1 but a different p-value, exhaustive redundancy, status logic, analytic normalisations). **They are not evidence that the corrected C2 or any procedure is statistically valid.** The full-suite result is in the chat report.
- Untouched: all v1 files, `h1_calibration.py` and its tests, all M4b outputs and Stage 0 results, M1–M3, data.

## 8. Unresolved decisions for you
1. Approve or reject the process e replacement (A4).
2. Approve the 12-cell C3 families at 90 and 180 days (A5), accepting reduced conservatism there.
3. Approve the wording of the ambiguity-replication rule (A2).
4. If the C2 paper stays unavailable: report-only, never selected (A6 default), or ask me to try other routes to the paper.
5. Stage 1 start (baseline method only, 68 cells) — not started, awaiting your explicit approval of v1.1.
