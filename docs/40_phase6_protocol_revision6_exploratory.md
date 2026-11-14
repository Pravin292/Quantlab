# 40 — Phase 6 protocol, revision 6: exploratory descriptive placement under Option A (frozen before measurement)

**Status:** numbered revision of `docs/26` (revision 5), written and frozen on 2026-11-14 **before any section 7 measurement was computed**. `docs/26` itself is not edited. Approved by the owner in this session: "Exploratory report"; "Yes, use defaults"; "Both, corrected first" for the shape method (§3). Earlier decisions: Option A (`docs/29`, recorded in `docs/38` §2.2).

**What had been seen before freezing:** the H1 results on these samples (`docs/31`, `docs/35`, `docs/39`); the first-sample descriptives of `docs/14` (which shaped the simulated domain, `docs/26` §3.3); and, for this revision, the session completeness of each sample (§R6.2). No tail, shape, day-volatility, dependence or clustering measure from `docs/26` §7 had been computed on any of these samples by this phase.

## 1. Decisions applied (docs/26 §14)

| ID | Applied |
|---|---|
| D1 | `docs/26` revision 5, amended by this revision 6, approved for this exploratory run |
| D2, D3, D4, D8, D12, D14, D16 | Not applicable: no universe, provider selection or index membership in an exploratory run on existing samples |
| D5 | All provisional thresholds as proposed in `docs/26` (strict z 8, n_s ≥ 54, rounding 5%, shape s/2s/4s and near-tie 1.15, day-sd bands, dependence cut points, feature zones, jackknife failure thresholds) |
| D6 | Not authorised (no D6 reference exercise); with Option A this is neither Mode A nor full Mode B (§R6.3) |
| D7 | The exposed stocks are analysed **only as a separate exploratory set, never pooled** |
| D9 | Baseline and strict (whole-session) variants |
| D10, D11, D13 | All blocks reported; counts only; aggregates only in the repository; stop rules as `docs/26` §11.7 |
| D15 | The unequal-group delete-block jackknife of `docs/26` §7.2, with tests T1–T6 |
| D17 | **(i) Lenient variant dropped.** On a complete block it equals the baseline |

## 2. Rules of this revision

- **R6.1 Samples.** The four existing real-data samples, each analysed separately: NSE first Yahoo sample (`data/clean`), US first Yahoo sample (`data/clean`), NSE fresh Yahoo pull (`data/clean_p2`) and US fresh Alpaca pull (`data/clean_p2_us`). One panel each (the three sampled stocks).
- **R6.2 Blocks.** One block per sample: the **first 59 scheduled sessions**. The scheduled list is the provider's session list, because the project has no official holiday calendar. For the fresh US sample this list equals the frozen 80-session list of `docs/37`. As `docs/26` §4.1 requires, a block containing any unusable session (a missing used bar for any stock) is **INSUFFICIENT**: nothing is measured and no session is substituted. The completeness check before freezing found that both NSE blocks contain 2026-10-15, which is incomplete, so **both NSE blocks are INSUFFICIENT**. The two US blocks are complete.
- **R6.3 Option A mapping.** D-tail is unavailable at every n (reason D-TAIL-UNAVAILABLE-OPTION-A). D-alt is U, because no per-stock reference exists (D-ALT-NO-PER-STOCK-REFERENCE). No Laplace reference exists (LAPLACE-UNEVALUATED). D-shape, D-daysd and D-dep are computed with the zone tables of `docs/26` §8.2. Phase 2 precedence applies: a reliable rank 4 on any dimension gives **OUTSIDE**; otherwise **CANNOT BE CLASSIFIED**. No coverage rank (1–3) can be assigned.
- **R6.4 Special rules without D-tail.** E-ZONE-DEP and DAYSD-0.6 need the required df set Dreq, which needs D-tail. Under Option A they are **not evaluable**: the dimension becomes U (E-ZONE-DEP-UNEVALUABLE or DAYSD-0.6-UNEVALUABLE), not rank 4. A rank 4 would claim OUTSIDE from missing information.
- **R6.5 Shape (M8): primary and secondary.** As the owner approved, the **primary** comparison uses the data's own volatility shape: the M4b variance-decay fit (`describe_next_round.fit_decay`) is converted to volatility as sqrt(1 + b·e^(−j/τ)), with j = 0 at the first used slot, and normalised per period exactly as `dependence.shaped_profile`. The **secondary**, report-only comparison is the literal route of `docs/26`, which feeds the fitted parameters to `shaped_profile`, as shape E was built. Only the primary enters the label.
- **R6.6 Measurement definitions.**
  - M2–M4 come from `fit_bar_model` and `tail_summary`, pooled and by period.
  - M10–M12 use the estimators that produced the domain's "estimated dependence" (`describe_next_round`): the day log-volatility is 0.5·ln(mean of positive squared returns). M10 is its standard deviation (ddof 1), M11 its lag-1 autocorrelation, M12 s the mean pairwise correlation of day log-volatility, and M12 ρ the mean pairwise correlation of slot-standardised returns. Each is averaged over the stocks or pairs.
  - M13 is the mean of the lag 1–5 autocorrelations of standardised squared shocks between adjacent used slots within a day.
  - M15 is the (non-excess) kurtosis of day log-volatility.
  - M9 is (Σw)²/Σw² of the primary fitted variance weights per period.
  - M16 is the share of unusable sessions in the sample.
  - M17 infers the tick as the smallest positive 5-minute price step in the block, and compares it with the median absolute step; above 5% the block gets ROUNDING-MATERIAL.
  - M5–M7 and M14 need a reference and are not computed.
- **R6.7 Reliability.**
  - All rules of `docs/26` §7.2 apply.
  - The zone-crossing and split-half rules are checked for the mapped dimensions. The split halves are the first 30 and last 29 sessions, each classified from its point estimate.
  - The heavy-tail rules for M2 and M3 are reported, but those measures do not enter a label.
  - Intervals are θ̂ ± 2·SE_J (stability intervals, not confidence intervals).
- **R6.8 Strict variant.** One detection pass marks bars with |z| > 8 on the baseline standardisation. A session is removed if it has a flagged bar or a zero-volume used bar for any stock; it is evaluable only if 54 or more sessions remain. Everything is then recomputed from scratch. The strict result is reported. Because every baseline label is OUTSIDE (already the worst) or CANNOT BE CLASSIFIED (final, `docs/26` §8.4), the strict variant cannot change a final label.
- **R6.9 Run once.** The run uses `scripts/milestone4/phase6_run.py` and `src/quantlab/research/phase6.py`, tested by `tests/test_phase6.py`. All three are hashed with this document in `outputs/milestone4/frozen_phase6_inputs.sha256` before the run. Outputs are write-once under `outputs/milestone4/phase6/`, aggregates only.

## 3. Finding recorded before measurement: shape E is not the real fitted volatility shape

Shape E was fitted to **slot variances** (`describe_next_round.fit_decay`), but its parameters were passed to `dependence.shaped_profile`, which builds a **volatility** profile (the simulator draws return = profile × day factor × shock). The open decay is also indexed from the session's first candle, while the fit indexes from the first used slot. So the simulated E world is steeper at the edges than the real sample it was meant to copy.

Measured from the definitions alone (no data, no random numbers), the volatility shape implied by E's own fitted parameters lies:
- **NSE:** 0.172 from simulated E (2.0 × s(E)), and nearest to **R2** (0.080).
- **US:** 0.148 from simulated E (2.4 × s(E)), and nearest to **R2** (0.069).

**Consequences.**
- The statement in `docs/26` §3.3 that shape E "*is*" the fitted shape is not exact.
- C3's simulation results are **not** affected: E was one of six validated shapes, and C3 passed in every gated cell for all of them, including R2 and flat.
- For Phase 6 this is the reason for R6.5.

## 4. Wording attached to every label

"The measured dimensions of this block are reported against simulated worlds in which C3 stayed within its pre-specified upper limit; features listed in docs/26 §8.9 as unmapped are not covered. Reference: Option A (`docs/29`, `docs/38`): D-tail unavailable, no per-stock and no Laplace reference; no coverage label is assigned." Every label also carries EXPLORATORY-EXPOSED-STOCKS and NOT-INDEPENDENT-OF-DOMAIN, because these stocks shaped the simulated domain.
