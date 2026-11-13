# 17c — D2 diagnostic flag: confirmed formula, units and labels

**What this is:** the written record of your confirmation (2026-11-02) of the exact D2 rule, and of the checks made before E4. It sits outside the frozen Stage 2 input manifest, which is unchanged. It does **not** authorise E4.

## 1. Confirmed formula
```
D2 flag  <=>  observed_spread − 1.25 × reference_spread  >=  0.02
```
- **Units:** both spreads are **fractions** of simulations (not percentages). `0.02` = **2 percentage points**; a spread of `0.10` = 10 percentage points. Output columns `spread` and `reference_spread` in `stage2_conditional_calibration.csv` are fractions; multiply by 100 to read percentage points.
- **observed_spread:** max − min of the rejection rates across the four quartiles of one conditioning variable (leverage, kurtosis, or the method's own critical value) for one method in one cell.
- **reference_spread:** the same method and the same conditioning variable in the df ∞ cell matched on shape, market and sample size (docs/17b §5a).
- **Status of the threshold:** a **judgement-based diagnostic**, not a statistical test or theorem. The output column is named `d2_flag_judgement_based`.
- **Reading chosen:** "exceeds 1.25 × reference by at least 2 points" means the excess over the 1.25× threshold is at least 2 points. The looser alternative (`spread − reference >= 0.02`) is **not** used; example: spread 0.09 with reference 0.06 is not flagged (0.09 − 0.075 = 0.015), though it would be under the alternative.

## 2. Where it is implemented (unchanged files, verified)
| Item | Location |
|---|---|
| Constants `D2_RATIO = 1.25`, `D2_MIN_EXCESS = 0.02` | `src/quantlab/research/h1_stage2.py` line 73 |
| Rule `method_spread − D2_RATIO × reference_spread >= D2_MIN_EXCESS − 1e-12` | same file, function `d2_flag` |
| Only call site | `scripts/milestone4/stage2_summarise.py`, `s2.d2_flag(sp, sp_ref)`; no second implementation |

**Tolerance:** the code compares with `0.02 − 1e-12` so that a case exactly on the boundary in decimal arithmetic (for example spread 0.100, reference 0.064) is not missed through floating-point rounding. The tolerance is about 10⁻¹⁰ percentage points. The test grid compares the code with the rule computed in exact decimal arithmetic at 15,376 combinations including exact boundaries: identical.

**Stale docstring:** the docstring of `d2_flag` still says "to be confirmed by the user before the main run". That is superseded by this record. It was **not edited**, because the file is hashed in `frozen_stage2_inputs.sha256`, which the runners verify before every run; editing it would stop E4 from starting, and the user asked that the existing manifest not be modified. If you want the wording fixed in the code, that needs a new manifest version and your approval (section 5).

## 3. Unmatched-reference labels (preserved, checked)
The label **"reference not matched on dependence / day-volatility"** is attached to every D2 flag and spread comparison in exactly **12 gated cells**: dev_row 44–51 (8 cells inside the 40-cell advancement scope) and dev_row 40–43 (4 tier A cells outside it, reported only). The 8 df 3 cells and the 32 matched in-scope cells carry no label. Tests: `tests/test_research_h1_stage2.py` and `tests/test_research_h1_stage2_d2_formula.py` (including a smoke run through the real summariser).

## 4. Checks run before E4 (2026-11-02)
- Implementation equals the confirmed formula (8 new tests, dense grid, exact boundaries, units, stricter-reading examples).
- Labels preserved (above).
- No frozen file or manifest modified (all manifests re-verified).
- Disk space and environment re-checked (see the readiness report in the chat).

## 5. Open choice for you (does not block anything)
Whether to correct the stale `d2_flag` docstring in the code. Costs: the file hash changes, a new Stage 2 input manifest (v2) must be issued, `stage2_common.py` must be pointed at it, and the C3 training provenance then refers to the earlier file version (the change would be comment-only). Default: leave as is; this record and the tests are the documentation.

## 6. Files added by this step
`docs/17c_h1_calibration_stage2_d2_confirmation.md`, `tests/test_research_h1_stage2_d2_formula.py`, and `outputs/milestone4/h1_calibration/frozen_stage2_inputs_addendum.sha256` (hashes of these two files only).
