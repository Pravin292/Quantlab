# 29 — Stage 0 D-tail compatibility: decision memo for the project owner

**Status:** written 2026-11-13. **Documentation only. This memo chooses nothing and approves nothing.** No real market data or real-data statistics file was opened; no simulation was run; no random number was generated; no H1 statistic or critical value was computed; D6 was not authorised; `docs/24`–`docs/28`, source code, tests, manifests and outputs were not modified; nothing was committed or pushed.
**Sources read:** `docs/26` (§8.2, 8.3, 8.5, 8.8, 8.10, 11.7, 12, 13, 16), `docs/27`, `docs/28`, `docs/14` (§1, §6), `docs/01`, `docs/04`, `docs/06` (day counts only), `scripts/milestone4/stage0_real_data_descriptive.py`, `src/quantlab/research/direct_sim.py`, `h1_calibration.py`, `tail_descriptives.py`.
**Labels:** DIRECT = read in the file or code itself; INDIRECT = stated in a report about the data or derived by arithmetic from such a statement; READING = my interpretation; NOT SPECIFIED = the documents do not say.

## 1. The evidence
### 1.1 Why `docs/26` requires an n = 59 D-tail reference
Every validated cell that carries a sample-size label uses n ∈ {59, 90, 125, 180, 250}, and the protocol's blocks have exactly the target n (§4.1: "no replacement date ... no relabelling of the block as a smaller n"). D-tail compares a block's standardised kurtosis, Hill index and exceedance rate (M2–M4) with the reference range of simulated worlds **of the same market and the same n** (§8.2; Mode A uses D6 cells (μ, n, d, shape, sd)). Those statistics depend on n (few events at n = 59, §7.1). So a reference for a 59-session block has to be built from 59-session worlds. Mode B (§8.2) states that the Stage 0 file supplies this reference "only for n = 59" and forbids any substitute, proxy or workaround.

### 1.2 What the Stage 0 reference contains (`docs/28`, repeated briefly)
576 rows: markets NSE and US; scopes all, open, middle, close (pooled over 3 stocks, no per-stock scope); Student-t df 3, 4, 5, 6, 8, 10, 20, 1000; nine statistics; mean and 5%, 50%, 95% quantiles; 200 repetitions; day-factor sd 0.3; no Laplace worlds; no fit-noise statistic; **no sample-size column**; one slot profile per market, namely the fitted profile of the real sample.

### 1.3 Why the evidence points to 60 days, and what is direct or indirect
| Evidence | Kind | What it shows |
|---|---|---|
| The reference file has no n column and `run_metadata.csv` lists no n | DIRECT | The file cannot say what n it represents |
| `stage0_real_data_descriptive.py` calls `simulate_returns_sq(market, len(syms), len(dates), ...)`, where `dates` is the set of dates in the real clean data of that market | DIRECT (code) | The simulated n equals the number of real dates, not a constant 59 |
| `docs/14` §1: real cleaned data "60 dates"; §6: "3 stocks, 60 days" | INDIRECT (a report) | The number of real dates is stated as 60 |
| `docs/14` §6 US standardised bars: 13,777, which exceeds 3 × 59 × 77 = 13,629 (max if 59 days) and is at most 3 × 60 × 77 = 13,860 | INDIRECT (arithmetic on a report figure) | At least 60 days for the US reference; the same test is uninformative for NSE because bars are missing |
| `docs/01` §data: "59 days of 78 bars, 1 day with 79" (US) | INDIRECT | A US pull of 60 dates, one of them unusual |
| `docs/04` and `docs/06` count "59 days" for NSE closing-window bars; `docs/14` also says "about 59 days" in its cost discussion | INDIRECT | **The documents mix 59 and 60.** "59 days" appears in places where one date may have been dropped or counted differently |
| The `days` field written by the script into `real_tail_statistics.csv` | Would be DIRECT | **Not read**, because that file holds real-data statistics and you excluded it |

**Assessment (READING).** The code makes n = number of real dates; the reports give that number as 60; the US arithmetic supports at least 60. Counting is inconsistent elsewhere (59 appears in several documents), so the exact n of each market's reference is **not established by a direct read**. It is very probably 60 and cannot be 59 for the US. `docs/28` classified the protocol's n = 59 claim as CONTRADICTED on this basis; this memo keeps that, with the caveat that the confirming number sits in a file not opened. Note also that the reference worlds were built on the real sample's fitted slot profile, which is not stated in `docs/26`; this adds a second respect in which the Stage 0 worlds differ from "59 validated-layout worlds".

### 1.4 Why the file cannot be treated as an n = 59 reference automatically
(1) It is not recorded as n = 59 and probably is not. (2) The effect of 60 versus 59 on the quantile ranges is **unknown**; I computed nothing, and the statistics (especially Hill and exceedance counts) vary with n. (3) `docs/26` §8.2 forbids approximation: "no workaround reference is permitted". (4) Per §11.7 the protocol "changes only by a numbered new version", so a documented acceptance of the deviation belongs in the protocol, not in an implicit reading. (5) The file differs from the validated layout in profile as well as n.

## 2. The three possible resolutions
No option is recommended. "Revision" means a numbered new version of `docs/26` (the protocol edits only by that route; §11.7). READING: all three options touch text now saying Stage 0 is an n = 59 reference (§8.2, 8.5, 8.8, 8.10, 12, 13, 16), so all three involve a revision; its content would be your decision and I have not drafted it.

### Option A — Report-only Mode B, D-tail explicitly unavailable at n = 59
- **Methodology.** Mode B becomes a measurement and data-quality report. D-tail is U for every n, with reason D-TAIL-NO-REFERENCE. No Stage 0 reference range enters any classification. Nothing is approximated. A D-tail-based OUTSIDE outcome (TAIL-DF3-ONLY) is no longer possible in Mode B.
- **Approvals.** Your decision for the option; approval of the revised protocol (D1 applies to the revision); the other open decisions D2–D17 are unchanged.
- **Revision.** Yes (the n = 59 clauses and the Mode B test expectations, §8.10, change).
- **D6.** Not required.
- **Remains blocked.** Everything that is already blocked per `docs/27` §8 (data access, freeze, tests and code, provider confirmation). Additionally: any coverage label (as before), and any D-tail-based placement in Mode B.
- **Whether Stage 0 ranges may still be shown as unclassified context is NOT SPECIFIED**; if wanted, the revision must say so and label them "60-day Stage 0 worlds, not n = 59".

### Option B — A separately authorised 59-day reference simulation
- **Methodology.** A new reference exercise with 59-session worlds would provide a proper n = 59 D-tail reference. It would be simulation of descriptive reference worlds, kept apart from C3 and the validated domain like D6 (§12). It would still have **no per-stock scope unless designed in**, so D-alt stays U in Mode B-type use unless the new design adds per-stock statistics, which is the territory of full D6 (Mode A). Which design (single variant at 59 days, or part of D6) is NOT SPECIFIED. Its profile and day-factor settings would need to be chosen and frozen (validated shapes or a fitted profile; unspecified).
- **Approvals.** Written authorisation for the new simulation: cell list, counts, seed (a new master seed would have to be registered; 20261201–20261213 and 20261215 are in use, 20261216 is only proposed for D6), output location with its own manifest (the Stage 0 script refuses to write into a folder that already has files); freeze before use; approval of the revision defining it.
- **Revision.** Yes: `docs/26` has no such reference; §8.2 calls any other reference a workaround and §12 says a partially completed D6 is neither mode. A new mode or an amended Mode B definition would be needed.
- **D6.** **Whether this is "D6" is NOT SPECIFIED.** As written, D6 is the Mode A exercise (320 + 40 + 60 cells, seed proposed 20261216). A 59-day Stage 0-style reference is a different, smaller exercise; my reading is that it needs its own explicit authorisation and a protocol definition rather than being covered by an authorisation of D6, and that authorising it does not by itself select Mode A. Please state which you intend.
- **Remains blocked.** All of Phase 6 on this path until the reference is authorised, run to completion, hashed and reviewed; real-data access stays blocked in any case. No H1 statistic or C3 interaction (§12).

### Option C — Explicitly accepting the existing 60-day reference for the n = 59 requirement
- **Methodology.** A deliberate, documented deviation: the 60-day Stage 0 worlds (on the fitted real-sample profile) are used as the D-tail reference for 59-session blocks. No new simulation. The size and direction of the error are **unknown** and unmeasured (not computed); the quantile ranges could be slightly different at 59. Every Mode B report would have to say so. It does not make Stage 0 an n = 59 reference; the label would be "60-day reference, accepted for n = 59 by owner decision".
- **Approvals.** Your explicit acceptance, recorded; approval of the revision that states the deviation, replaces the n = 59 wording and adds the caveat to the Mode B wording of §8.8.
- **Revision.** Yes (see above).
- **D6.** Not required.
- **Remains blocked.** Same as `docs/27` §8; D-alt remains U; no coverage label. Accepting the deviation does not enable any gate: it only restores D-tail at n = 59 under the stated caveat. The exact stage-0 n must still be established before acceptance if you want the caveat to state it correctly (see §5).

## 3. Interaction with D-alt, D-tail and the Phase 2 precedence
`docs/26` §8.3 Phase 2: (i) a reliable rank 4 on any dimension → **OUTSIDE**; (ii) else any U → **CANNOT BE CLASSIFIED**; (iii) else the maximum rank. In Mode B D-alt is always U (no per-stock reference, so indicator (d) cannot be evaluated; §8.2). Therefore, in Mode B:
- **Classification outcome.** A block ends **OUTSIDE** only if some dimension is a reliable rank 4 (for example D-tail G_I = {3}, D-shape, D-daysd, D-dep, or a failed special rule); otherwise **CANNOT BE CLASSIFIED**. Step (iii) is never reached, so no block gets REPRESENTED, NEAR BOUNDARY or PARTIALLY REPRESENTED, and the Phase 3 caps are moot.
- **Effect of D-tail availability.** D-tail availability does **not change the fact that a coverage label is impossible**; D-alt's U settles that. It changes only (a) whether D-tail can supply a rank-4 OUTSIDE (only TAIL-DF3-ONLY does) and (b) which reason codes appear: D-TAIL-NO-REFERENCE (unavailable) versus the tail reasons (TAIL-DF3-ONLY, TAIL-DF3-WITH-OTHERS, TAIL-DF4) when available. If D-tail is itself U, a block can still be OUTSIDE through another dimension's reliable rank 4, because rank 4 precedes U.
- **Reason codes** (Phase 5) are collected from every dimension and cap whatever the outcome: always D-ALT-NO-PER-STOCK-REFERENCE and LAPLACE-UNEVALUATED; D-TAIL-NO-REFERENCE if D-tail is unavailable; plus any other dimension reasons; flags SINGLE-VARIANT-REFERENCE and SHAPE-THRESHOLDS-UNCHECKED.
- **Descriptive information that may still be reported** (READING of §8.5 and §8.8): the §7 measurements (M1–M4 and the others), intervals and reliability diagnostics, the cleaning variants, ledgers, feed-quality tables, the reasons and flags above, and the mode statement. "Reported" for the Stage 0 quantile ranges alongside observed values is NOT SPECIFIED under Option A.
- **Coverage label.** **None can be assigned in Mode B** under any of Options A, B or C, unless Option B were to be extended into a full D6 (Mode A), which is a different decision (D6).

## 4. Decision request for the project owner
Please record, in writing, one of the following (or another resolution of your own), and do not treat silence as a choice:
1. **Option A** — Mode B is report-only; D-tail unavailable at n = 59.
2. **Option B** — authorise a separately defined 59-day reference simulation (and say whether it is a part of D6 / Mode A or a separate exercise, its design, seed and folder).
3. **Option C** — accept the 60-day Stage 0 reference for n = 59, with the caveat stated.
4. **Other** — specify.

Also record: (a) whether to allow the one-field read of the `days` value in `real_tail_statistics.csv` to settle the exact n (it is stored next to real-data statistics; **I have not opened it and will not unless you permit**); (b) for Option A, whether Stage 0 ranges may be shown as unclassified context; (c) that the chosen path leads to a numbered revision of `docs/26`, whose content and approval remain yours. This memo does not change the mode, D6 or any approval status in `docs/27`.

## 5. Outstanding limitations
- The exact day count of each Stage 0 reference market is **not read directly**. US ≥ 60 is supported by arithmetic; NSE rests on `docs/14`'s statement.
- The size of the 59-versus-60 effect on any reference quantile is **unknown**.
- The difference between the fitted real-sample profile and the validated shapes is **unknown**.
- The other items of `docs/27` (D1–D17, provider and licence, Mode A/B declaration, data access) are unchanged and unresolved. `docs/27`'s statement that the Stage 0 layout check is outstanding stays on file; `docs/28` and this memo are the later evidence, and neither edits it.

## 6. Git status and restriction compliance
HEAD `080f5be29d5a70e86dbaaa5eac135be932ed6187`; tracked modifications README.md and docs/README.md only (Stage 5); this task added `docs/29`. No restriction was breached (no real data or real-data statistics file opened, no simulation, no random numbers, no H1 statistic or critical value, no D6, no changes to `docs/24`–`docs/28`, source, tests, manifests or outputs, nothing committed or pushed).
