# 26 — Real-data descriptive validation protocol (PROPOSED, not approved, not executed) — revision 5

**Status:** protocol design only; first draft 2026-11-12; revisions 2–4 after methodological reviews; **revision 5** is a narrow consistency audit (reference modes A and B, withheld-label wording, and one newly recorded unresolved decision D17; Appendix B). **Not approved. Not executed.** No real market data was accessed, downloaded, purchased or processed; no simulation (including D6) was run; no random number was generated; no H1 statistic, rejection rate or critical value was computed; C3, the frozen specifications, seeds, manifests, validation outputs, source code, scripts and tests were not touched. The only computations in revisions 2–4 are deterministic arithmetic: shape-profile distances from frozen definitions (Appendix A), analytic strengths and tail values (sections 8.2, 8.6), and algebraic consistency checks of the jackknife estimator on constructed index sets and deterministic toy sequences (Appendix C), run in a scratch script outside the repository. Approving this document would not authorise data access; that needs a separate, explicit authorisation (section 13).
**Labels:** **[ESTABLISHED]** a finding in the accepted record (docs 13–25); **[PROPOSED]** a design choice for the user; **[PROVISIONAL]** a numeric threshold or convention with no statistical validation; **[ASSUMPTION]** taken as true without proof; **[UNRESOLVED]** a decision or fact not settled here; **[PRIMARY-READ]** a provider fact read on the provider's own page on 2026-11-12; **[LEAD]** a provider fact from a search snippet, a project document or a third party.

## 1. Purpose and scope
**Purpose.** Decide, by a deterministic rule fixed before any data is seen, whether real NSE and US 5-minute equity data blocks *resemble the conditions simulated and validated* for the H1 critical value C3. The output is a **descriptive domain-placement label** per pre-specified block (section 8), not a statement about the real market.

**What it is not.** It does not (a) compute the H1 statistic T or any period-variance comparison on real data, (b) estimate or report any real-data rejection rate, (c) recalculate, tune or replace C3 or its five critical values, (d) claim that simulation results transfer to financial markets, or (e) start the research protocol (`docs/07`), H2, H3 or M5.

**Conclusion it must preserve [ESTABLISHED, docs 24–25].** Classification **PARTIAL**: C3 stayed within its pre-specified upper rejection limits in every gated cell of a *simulated* domain (highest Stage 3 rate 5.28%, at the T4/D5 125-day cells; alternative processes 1.23%–4.41%), is conservative in most cells, is at about nominal level at that frontier, and is **not** shown to be a calibrated 5% test, universally or on real data. All limitations in `docs/24` and `docs/25` remain, including the unexplained excess variability of the C3 repeat comparisons (sum of z² 113.41, p = 0.0035) and the unresolved threshold-specific effect near 3.3. Simulated-domain evidence and real-market descriptive placement are kept distinct throughout.

## 2. Research questions (all descriptive)
- **RQ1.** For each pre-specified block, what are the descriptive measures of tail weight, intraday shape, day-volatility level and persistence, cross-stock dependence, clustering and jump frequency (section 7)?
- **RQ2.** Does each block lie *within*, *near the boundary of*, *partly within*, *outside*, or *cannot be placed in* the validated simulated domain (section 8)?
- **RQ3.** How stable is that placement to estimation error, cleaning choices, window and securities (sections 7.2, 7.3, 9)?
- **RQ4.** Which aspects of real data are not represented in the simulated family (sections 8.9, 9)?
RQ1–RQ4 are answered without any H1 test statistic. A block may end as "insufficient evidence to place" (section 8.5).

## 3. Established record this protocol relies on
### 3.1 The validated domain [ESTABLISHED: `frozen_spec/cells_validation.csv`, `cells_alternative_dgps.csv`, `alt_dgp_parameters.json`, docs 21 and 23]
The domain is a **sparse set of points**, not a grid. Unit: **3 stocks per market**, all days complete (no missing bars), iid days unless stated, H0 true by construction, two markets (NSE 71 used slots, US 77) with the frozen period definitions of `docs/06` §3. C3 values exist for exactly five sample sizes.

| Student-t df (label, tier) | 59 days | 90 | 125 | 180 | 250 |
|---|---|---|---|---|---|
| ∞ (G, A) | flat, E, D5, R2 | – | E, D5 | – | E, D5 |
| 10 (T10, A) | flat, E, D5, R2 | – | – | – | – |
| 7 (T7, A) | E, D1.5, D3.0 | E | – | E | – |
| 6 (T6, A) | flat, E, D5, R2; E and D5 also with estimated dependence | – | E, D5 | – | E, D5 |
| 5 (T5, B) | E, D1.5, D3.0 | E | – | E | – |
| 4 (T4, B) | flat, E, D5, R2; E and D5 also with estimated dependence and with day-factor sd 0.6 | – | E, D5 | – | E, D5 |
| 3 (T3, report only) | flat, E, D5, R2 | – | – | – | – |

Every entry is run for NSE and US. Unless stated, day-factor sd = 0.3 and no dependence. **Counts: 88 gated cells (tier A 54, tier B 34); 8 df 3 report-only cells; 12 Stage 4 alternative-process cells; 108 validated points in all.** Shapes: flat; E = the market-specific "empirical" shape (NSE open amp 2.031, tau 2.063, close amp 4.581, tau 0.365; US open amp 5.695, tau 3.366, close amp 3.174, tau 1.232); D5 = exponential, tau 2.0; D1.5 and D3.0 = exponential, tau 1.5 and 3.0; R2 = `dep.shaped_profile` with all four shape parameters 2.0 (`run_h1_inference.profile_for`; definitions in `docs/20`). "Estimated dependence" = NSE return correlation 0.355, cross-stock day-factor share 0.454, day-factor lag-1 autocorrelation 0.441; US 0.187, 0.141, 0.190 (`run_h1_next.EMP_DEP`). Alternative processes (Stage 4; shape E, 59 days, NSE and US, one parameter setting each): (a) intraday volatility clustering (AR(1) log-volatility, phi 0.9, sd 0.25, t6), (b) jumps (t10 plus 0.002 per bar, size 4–8 bar scales), (c) period-specific tails (t4 open and close, t8 middle), (d) stock-specific tails (t3, t5, t8), (e) heavy-tailed day factor (5% mixture, sd 0.76 against 0.25, t8), (f) Laplace shocks.

### 3.2 Results by region [ESTABLISHED]
C3 rejection rate: tier A at most 2.98%; tier B at most 5.28% (T4/D5, 125 days: NSE 5.268%, US 5.276%; Stage 2 value 5.116% in both); df 3 report-only cells 1.61%–6.24% (three at or above 5.2%; two above the 6.0% tier B limit); alternative processes 1.23%–4.41%. 90- and 180-day cells exist only for df 7 and 5 with shape E. Stage 3's pass on the 76 re-run development cells carries less independent evidence than its 88-cell count suggests, because C3's critical values were set from those same cells (`docs/25` §9).

### 3.3 What the real data have already shown [ESTABLISHED; matters for independence]
The six-stock sample (RELIANCE.NS, TCS.NS, INFY.NS, AAPL, MSFT, NVDA; one Yahoo pull, about 59 usable days) has **already been examined descriptively** (period volatility, `docs/06`; tail summaries and df-equivalents, `docs/14` §6: NSE pooled df 4–6, NSE close df 3–4, US pooled df 6–8; fitted shape; dependence; day-volatility sd 0.5–0.64). **The simulated domain was partly built from that sample**: shape E *is* its fitted shape, "estimated dependence" *is* its estimate, and the day-factor sd 0.6 cells were added because of its day-volatility estimate (`docs/14` section 10 item 7). A placement of *those* six stocks is partly true by construction and **is not independent confirmation**.

## 4. Data selection methodology
### 4.1 Blocks: fixed windows, scheduled sessions, usable sessions [PROPOSED]
- **Scheduled session list.** Before any data is fetched, the exchange calendar is used to list, in time order, the **scheduled regular full trading sessions** of the span (excluding holidays, scheduled early closes, Muhurat and other scheduled special sessions). This list is frozen in the manifest. It depends on the calendar only, never on the data.
- **Block.** For each market and each target n ∈ {59, 90, 125, 180, 250}, blocks are **consecutive, non-overlapping runs of exactly n scheduled sessions** starting at the first scheduled session of the span. The window of a block is fixed by this list; there is no choice left after data is seen.
- **Usable complete session.** A scheduled session is usable for a security if every used slot has a valid bar for it (section 5). A security is **ELIGIBLE** for a block if all n scheduled sessions are usable for it; otherwise it is **INCOMPLETE** for the block (ledger, 4.3).
- **Exactly n.** The H1 sample size of a classified block is always exactly its target n. **There is no replacement date, no later day substituted for an excluded one, no extension of the window and no relabelling of the block as a smaller n.** A candidate panel with any INCOMPLETE security is not analysed (4.2).
- **Unscheduled events** (unannounced halts, unscheduled closures) make a session unusable by the rule above; they are not removed from the scheduled list.
- **Span:** [UNRESOLVED D4] as long as the provider allows; recommended at least two years per market. Blocks of different n cover the same dates and are nested or overlapping (section 9.3).
- **Feed-quality measures at pair level and panel level, and the review conditions, are defined in 4.5.** The 10% figure of earlier drafts is only one of those conditions and is not a tolerance inside a block.

### 4.2 Universe, candidate panels and panels [PROPOSED]
- **Universe per block:** the constituents of the NIFTY 50 (NSE) or S&P 500 (US) **on the first scheduled session of that block**, from a documented index-membership history (D3/D14), frozen in the manifest before any price data is fetched.
- **Liquidity strata:** rank the block's universe by median daily traded value (price × volume) over the quarter before the block, from daily data only; three strata (high, medium, low).
- **Candidate panels (revision 4).** Within each stratum, take **all provider-carried securities** (status ELIGIBLE or INCOMPLETE, 4.3) in liquidity-rank order and form **candidate panels from consecutive triples** (ranks 1–3, 4–6, …). A final remainder of fewer than three securities forms no panel and is recorded. No randomness.
- **Analysable panels.** A candidate panel is **ANALYSABLE** if all three securities are ELIGIBLE; otherwise it is an **INCOMPLETE PANEL**, recorded with the security, the unusable sessions and their reason codes. **Incomplete panels are not re-formed from other securities**; no substitute security is introduced. Every ANALYSABLE panel is analysed; none is dropped for its results.
- **Sectors:** recorded, not used for selection (D8). **No selection on results:** no security, panel, block or date is added or removed after any section 7 measure is computed.
- **The six exposed stocks (3.3):** analysed, if at all, as a separate *exploratory* set, never pooled (D7).

### 4.3 Survivorship, delisting, suspension and provider-missing securities (no silent exclusion)
A **universe ledger** is written for every block with one row for **every constituent of the block's universe**:

| Status | Definition | Treatment |
|---|---|---|
| ELIGIBLE | all n scheduled sessions usable | may enter an analysable panel |
| DELISTED / ACQUIRED / MERGED | listing ends inside or before the block (end date recorded) | contributes to earlier blocks it fully covers; for the block in which it ends it is unavailable and recorded as "ends inside block" (reported, not in the pair-level denominator) |
| SUSPENDED | whole-day suspensions or a halt for most of the block | suspended sessions are unusable; the security is INCOMPLETE ("incomplete (suspension)") |
| PROVIDER-MISSING | in the universe list but absent from the provider's data (including delisted names the provider does not keep) | counted and named; **not replaced silently** (reported, not in the pair-level denominator) |
| SYMBOL-CHANGE / CORPORATE-EVENT | ticker change, split, bonus, demerger | mapped through the provider's identifier history if available; otherwise PROVIDER-MISSING |
| INCOMPLETE | at least one scheduled session unusable (reason codes per session) | listed; its candidate panels are INCOMPLETE PANELS |

Per block and market, the ledger gives the share in each status. If PROVIDER-MISSING securities are not a random subset (for example all delisted names are missing), the block's reports carry **SURVIVOR-BIASED** and every statement is restricted to "the securities the provider carries". Using the membership at block start (not span start, not today's) avoids dropping securities that later left the index.

### 4.4 Other bias controls
Corporate actions: section 5. Index constituents are liquid; results say nothing about small or illiquid securities. Price level and tick size are recorded per security.

### 4.5 Feed-quality measures, review conditions and descriptive comparisons (revision 4)
**Definitions [PROPOSED]** (per market, per target n, per stratum and block; all reported separately):
- **Pair-level incompleteness P_pair** = (number of INCOMPLETE (security, block) pairs) / (number of (security, block) pairs whose security is provider-carried, i.e. ELIGIBLE or INCOMPLETE). DELISTED and PROVIDER-MISSING shares are reported beside it, not inside it.
- **Panel-level incompleteness P_panel** = (number of INCOMPLETE PANELS) / (number of candidate panels), computed on the candidate panels of 4.2. It is **not** derived from P_pair.
- **Analysable-panel count** per (market, n, stratum).
**Deterministic review condition.** The market's data are flagged **FEED-QUALITY-REVIEW**, the stop rule of 11.7 applies, labels for that market are computed but **withheld**, and the user reviews before any label is released or interpreted, if **any** of these holds: (i) P_pair > 10% [PROVISIONAL, D5]; (ii) P_panel > 27% [PROVISIONAL, D5]; (iii) fewer than three ANALYSABLE panels in any (market, n); (iv) the ELIGIBLE share of the universe is below 80% [PROVISIONAL, D5]. *The value 27% is arithmetic, not a validated threshold:* 1 − 0.9³ = 27.1% is the panel-level incompleteness that a 10% pair-level rate would produce if incompleteness were independent across the three securities of a panel; the real dependence between securities is unknown. **No threshold here is claimed to eliminate, bound or detect selection bias**; the conditions only detect gross feed failure.
**Descriptive comparison of included and excluded units (required, outcome-free).** For each market and target n the report tabulates, for (a) ELIGIBLE against INCOMPLETE securities and (b) ANALYSABLE against INCOMPLETE panels (panel values by the median of its three securities): liquidity rank; median daily traded value; price level; tick size relative to price; listing age within the span; sector; provider coverage start and end; number of corporate events; share of zero-volume 5-minute bars within the *available* sessions; share of missing used slots over the whole span; and one daily-data volatility characteristic (median absolute daily return from daily bars, available for every security). These are counts, medians and ranges **without tests**. No 5-minute return statistic (M2–M15) is computed for an INCOMPLETE unit for these tables; the lenient variant of 7.3, which would need such statistics for incomplete sessions, conflicts with this sentence and is **UNRESOLVED (D17)**. **Interpretation limit:** surviving blocks are complete by construction and may differ from excluded ones in ways (calmer trading, liquidity, listing age) that the comparison shows only for the characteristics listed; it cannot show differences in unlisted ones, and it does not remove selection bias.

## 5. Inclusion, exclusion and data-quality procedures
All rules are fixed before data access. Every unusable session is logged with a reason code; nothing is filled, interpolated or deleted for being "extreme".

| Issue | Detection | Handling (baseline) | Documentation |
|---|---|---|---|
| Missing 5-minute bars | expected used slots with no row (as `validate.missing_slots`) | the **session is unusable** for that security (no fill); the security is INCOMPLETE for the block (4.1) | session-level table |
| Duplicate timestamps | `duplicate_timestamp` flag | identical rows dropped; conflicting rows stop the process for that file (as `clean.py`) | log |
| Invalid OHLCV | `invalid_ohlc`, `missing_ohlc` | bar unusable, hence session unusable | log |
| Zero-volume bars | `zero_volume` | kept if prices valid (measures use prices only); counted; sessions removed only in the strict variant | counts |
| Trading halts, circuit breakers | 3 or more consecutive missing used bars, or a documented halt | missing bars make the session unusable | log; halt dates from exchange records where available |
| Special or incomplete sessions | exchange calendar | scheduled ones are outside the scheduled list (4.1); unscheduled ones make the session unusable | calendar source frozen in the manifest |
| Time zone, DST | timestamps converted once to exchange local time (IST; US Eastern with DST); bar-start convention as `docs/05` | conversion tested across both DST transitions before use | conversion log |
| Corporate actions | provider action file | the provider's *adjustment convention is verified before use*; a split or bonus on a scheduled session can break prices inside the day: such sessions are unusable; dividend days are kept | action list |
| Outliers, provider errors | the largest absolute standardised returns are listed with timestamps | **never removed in the baseline**; whole-session removal only in the strict variant (7.3) | `largest_moves`-type table |
| Provider revisions | data fetched once; raw files written once with SHA-256 (as `docs/05`) | re-pulls are new files | manifest |
| NSE opening candle and closing window | the 09:15 candle has no return; 15:15–15:25 bars were empty or unreliable in the Yahoo feed (`docs/04`) | the **same used-slot definition as the simulator** is applied; presence of 15:15–15:25 bars is recorded | slot table |

**Block inclusion** reduces to: all three securities of an analysable panel ELIGIBLE (all n scheduled sessions usable); same session layout throughout; no change of session hours inside the block (checked against exchange circulars; a block spanning a change is INSUFFICIENT).

## 6. Provider-independent definitions to be frozen with the protocol
Standardisation, period definitions and used-slot sets are those of `docs/06` §3 and `docs/14` §6, implemented by the existing `h1_calibration.fit_bar_model` (robust median day scale, mean slot profile, three alternations, within-period renormalisation of the squared shocks to mean 1) and `tail_descriptives.py` for the *standardisation and tail summaries only*. [PROPOSED] The code computing section 7 is written, tested and hashed before any data access, with a test that it never imports or calls `max_abs_t`, the bootstrap or any critical value.

## 7. Descriptive measurements, intervals and reliability
### 7.1 Measurements and what each maps to
All are computed per security, per panel and per block, and by period where relevant. **None is a hypothesis test and none compares period variances.**

| # | Measurement | Simulation-domain parameter it is compared with | Main limitation |
|---|---|---|---|
| M1 | Usable sessions n (= target n by 4.1) | n ∈ {59, 90, 125, 180, 250}; panel of 3 | 90 and 180 only for df 7 and 5, shape E, no dependence |
| M2 | Standardised-return kurtosis (pooled and by period) | Student-t df ∈ {∞, 10, 7, 6, 5, 4, 3} | undefined for df ≤ 4 in theory; unstable and biased downward in short samples |
| M3 | Hill tail index at the 5% cut-off (primary; 1%, 2%, 10% reported) | same | depends on the cut-off; high variance at n = 59 |
| M4 | Exceedance rate of \|z\| > 4 per 1,000 | same | few events at n = 59 |
| M5 | **df-equivalent set G** (8.2 D-tail) | gated df set; df 3 boundary | a *descriptive index, not an estimate of the data-generating distribution* |
| M6 | M5 by period | alternative (c) | thin periods |
| M7 | M5 by stock | alternative (d) | small per-stock samples |
| M8 | Fitted profile (open amp and tau, close amp and tau; M4b routine) for the panel and for each stock, and distances to the six validated shapes | shapes E, D5, D1.5, D3.0, R2, flat | fit noise; the simulator uses one common profile for all three stocks |
| M9 | Effective bars per period, (Σw)²/Σw² of fitted weights | mechanism found in simulation (`docs/13` §2.2) | simulation-only mechanism |
| M10 | Day log-volatility factor sd | day-factor sd 0.3 and 0.6 (T4, E/D5, 59 days, no dependence only) | estimated from n days |
| M11 | Lag-1 autocorrelation of day log-volatility | "estimated dependence" | imprecise at n ≤ 90 |
| M12 | Cross-stock day-factor correlation; return correlation | estimated dependence | three pairs only |
| M13 | Mean of lag 1–5 autocorrelations of squared standardised returns within day | alternative (a) | rounding and microstructure also create autocorrelation |
| M14 | Excess exceedance of \|z\| > 4 per 1,000 beyond the reference for the block's own G | alternative (b) | not separable from a heavy tail |
| M15 | Kurtosis of estimated day log-volatility factors | alternative (e) | factors are estimated |
| M16 | Unusable-session share (ledger) | simulator has none | reported, not mapped |
| M17 | Price level; tick size relative to bar volatility | not simulated | rounding screen in 8.9 |
| M18 | Market and session layout | two layouts | other exchanges outside |

### 7.2 Intervals and reliability diagnostics (deterministic jackknife)
For every scalar measurement θ (M2–M4, M8 distances, M10–M15) on n sessions:

**Delete-one-session jackknife.** θ_(−i) with session i removed; θ̄ = (1/n) Σ_i θ_(−i); **SE_J² = ((n − 1)/n) Σ_i (θ_(−i) − θ̄)²**. **Interval I_θ = [θ̂ − 2·SE_J, θ̂ + 2·SE_J].** It is a stability interval, not a confidence interval of stated coverage.

**Delete-block jackknife for unequal groups (revision 4; derivation and verification in Appendix C).**
- *Groups.* Cut the n sessions into g = 10 consecutive groups of sizes m_1 ≥ … ≥ m_10 differing by at most one (the larger groups first; for n = 59: nine groups of 6 and one of 5), Σ m_j = n. h_j = n / m_j. θ_(−j) = θ computed with group j removed.
- ***Group weights* w_j = (n − m_j) / ((g − 1)·n) = (h_j − 1) / ((g − 1)·h_j)**, with Σ_j w_j = 1.
- ***Weighted mean of the deleted estimates* θ̄_w = Σ_j w_j θ_(−j).**
- ***Variance* SE_B² = (1/g) Σ_j (h_j − 1)·(θ_(−j) − θ̄_w)² = (1/g) Σ_j ((n − m_j)/m_j)·(θ_(−j) − θ̄_w)².**
- *Equal sizes.* If every m_j = n/g then h_j = g, w_j = 1/g, θ̄_w = θ̄_B (the plain mean of the θ_(−j)), and SE_B² = ((g − 1)/g) Σ_j (θ_(−j) − θ̄_B)², the standard grouped-jackknife formula (checked in Appendix C).
- *Basis.* For the sample mean **of independent, identically distributed (equal-variance) observations** the estimator is exactly unbiased for Var(θ̂) for any group sizes, and θ̄_w equals θ̂ exactly (Appendix C; the algebraic identities for θ̄_w and the weights hold for any data, the unbiasedness needs the iid, equal-variance condition). **No unbiasedness claim is made for dependent data such as financial time series**: consecutive groups capture some serial dependence, but nothing here establishes unbiasedness or validity for dependent, heteroscedastic or heavy-tailed data. **[ASSUMPTION]** This unbiasedness for a linear statistic is the property by which the estimator was chosen. Nothing is claimed for kurtosis, Hill or other non-linear or non-smooth statistics; the equal weighting 1/g in front of the sum is a **convention [PROVISIONAL, D15]** (any weights summing to 1 are also unbiased for the mean). No external source was consulted; the derivation in Appendix C is self-contained. The pseudo-value formula with an unweighted pseudo-value mean and the factor 1/(g(g − 1)) used in revision 3 is **withdrawn**: for unequal groups its expectation for the sample mean is not σ²/n (it is 1.003 σ²/n at n = 59 and 1.008 σ²/n at n = 54, Appendix C).
- Delete-block quantities are used only for the diagnostic ratio SE_B/SE_J.

A measurement is **UNRELIABLE** (its dimension becomes "cannot be classified") if **any** of these holds:
1. **Single-session influence:** one session's |θ_(−i) − θ̂| exceeds 50% of Σ_j |θ_(−j) − θ̂|, or deleting one session moves θ̂ across a zone boundary of its dimension.
2. **Dependence inconsistency:** SE_B / SE_J > 1.5 or < 0.67.
3. **Pseudo-value shape:** the sample skewness of the delete-one pseudo-values n·θ̂ − (n − 1)·θ_(−i) exceeds 2 in absolute value.
4. **Heavy-tail failure:** for M2 the largest single standardised return accounts for more than 25% of the fourth-power sum; for M3 the Hill estimate recomputed without the single largest standardised return differs from the full-sample estimate by more than 2 SE_J.
5. **Width:** the interval of a dependence component is wider than 0.4; of the day-factor sd wider than 0.3; the set G spans more than four steps of the grid {3, 4, 5, 6, 8, 10, 20, ∞}.
6. **Non-computable:** θ undefined for any replicate.
7. **Split-half instability:** the two chronological halves give dimension classes that differ by two or more ranks.
Known weakness [ASSUMPTION flagged]: the jackknife is inconsistent for non-smooth statistics (quantiles, order-statistic estimators such as Hill) and unreliable for heavy tails; the diagnostics detect failures, they do **not** guarantee validity. Every report says so.

**Consistency checks required before use (automated tests to be written at E3 under `tests/`, with deterministic inputs and no random numbers; they are specified here, not created now, because this task forbids modifying tests).** (T1) the weights w_j sum to 1; (T2) for the sample mean, θ̄_w equals θ̂ to numerical precision for equal and unequal group sizes; (T3) for the sample mean the delete-block pseudo-values h_jθ̂ − (h_j − 1)θ_(−j) equal the group means; (T4) **equal-size check:** for n ∈ {50, 60, 90, 180, 250} the estimator equals the standard grouped-jackknife formula to 10⁻¹⁴; (T5) **unequal-size check:** for n ∈ {54, 59, 61, 81, 113, 125, 162, 225} the quadratic form y′Qy defining SE_B² for the sample mean satisfies trace(Q) = 1/n and Q·1 = 0, which is exact unbiasedness for iid data; (T6) for n = 59 the group sizes are nine of 6 and one of 5. The results of the equivalent scratch checks are in Appendix C.

### 7.3 Cleaning variants [PROPOSED]
- **Baseline:** section 5; all n scheduled sessions usable; nothing removed. This is the only variant that corresponds to the complete-bar simulated domain at the validated n.
- **Strict (whole-session removal), exact procedure (revision 4).**
  - *S1 — detection data and estimator.* On the baseline sample of the panel (the 3 securities × n sessions × the used slots, nothing removed) apply the **frozen standardisation `fit_bar_model(r2, groups, n_iter = 3)`** of `h1_calibration` (section 6): robust median day scales, mean slot profile, within-period renormalisation of the squared shocks e2 to mean 1. The detection statistic is **|z| = √e2** for every stock, session and slot. **Initial detection therefore uses the baseline scale estimates, with no other estimator.**
  - *S2 — flagged set (single pass).* A bar is **flagged** if |z| > 8 [PROVISIONAL, D5], using these baseline z only. The detection is done **once**; it is not iterated.
  - *S3 — removal.* Remove as **whole sessions** every session (for the panel, a session removed for any of the three securities is removed for all three) that contains a flagged bar, a halt, or a zero-volume used bar. Bars are never removed individually and no incomplete session is retained. The removed set R_s is fixed at this point.
  - *S4 — size condition.* n_s = n − |R_s|. **Evaluated before any recomputation:** the strict variant is evaluable only if **n_s ≥ ⌈0.9 n⌉** [PROVISIONAL, D5], that is n_s ≥ 54, 81, 113, 162, 225 for n = 59, 90, 125, 180, 250. Otherwise it is "not evaluable", flag CLEANING-HEAVY, nothing is recomputed, and the baseline label stands.
  - *S5 — recomputation.* On the n_s remaining sessions **everything is recomputed from scratch**: `fit_bar_model`, slot scales, day scales, standardised returns, the profile fit (M8), M2–M15, and both jackknives with n_s sessions and groups sized for n_s (7.2). The recomputed |z| of the remaining sessions may exceed 8; those bars are **not** removed (no second pass) and their number is reported.
  - *S6 — use.* The strict variant is evaluated with the reference of the **target n** and may only worsen the label (8.4).
  - *Avoiding circularity.* The removal decision depends only on S1–S2 (baseline z, a fixed constant, one pass); no measurement of S5 and no mapping outcome feeds back into S1–S3; the threshold and the procedure are frozen before data.
  - *Known limitations.* The baseline slot profile is a mean, so an extreme bar inflates its own slot's scale: ignoring the median day scale and the within-period renormalisation, a flagged bar needs a raw standardised ratio of about 100 at n = 59 (about 70 at n = 250), i.e. |z_raw| of about 10, so detection can miss outliers (masking). The strict sample is **not** the complete-bar domain at the validated n: n_s is not a validated sample size, and removing sessions *because of their returns* truncates the tails so the strict sample is not representative of the unconditional process and can look lighter-tailed than the data are. The strict variant therefore never improves a label and never supports a claim of equivalence to the complete-bar domain at the validated n.
- **Lenient.** Baseline plus sessions that miss up to two used slots, retained as incomplete sessions; standardisation, day scales and the profile fit use the available bars, with slot counts reported. Because the validated domain assumes complete bars, **lenient can never support a label of REPRESENTED or NEAR BOUNDARY and never rescues a block that has fewer than n complete sessions**. It is a stability check only (8.4). **UNRESOLVED (D17):** this variant conflicts with 4.5, 4.1 and 8.1 (see the D17 row); until D17 is decided it is not part of the executable protocol and its clauses here and in 8.4 are provisional text.

## 8. Simulation-domain mapping algorithm (deterministic)
**Conventions.** Ranks: REPRESENTED = 1, NEAR BOUNDARY = 2, PARTIALLY REPRESENTED = 3, OUTSIDE = 4. CANNOT BE CLASSIFIED (C), UNRELIABLE (U) and INSUFFICIENT (I) are not ranks. A zone table lists contiguous, non-overlapping zones with explicit endpoints. **Interval rule:** for a measurement with interval I, the dimension rank is the **highest rank among zones intersecting I** (touching an endpoint counts). The mapping uses only the validated points of 3.1, **never interpolates or extrapolates**; "nearest-point assignment" is flagged and never produces a rank better than 2. **No step of 8 involves a free choice made after real data are seen:** every nearest value, tie-break and cell lookup is a table or order frozen in this document. **Unit of labelling:** a label is assigned to each (ANALYSABLE panel, block) pair; "block" in section 8 and in reports of its results means that pair. **Reference mode:** every label is computed in exactly one reference mode (A or B, 8.2), declared in the freeze manifest.

### 8.1 Step 1 — eligibility
1. 3 securities; market ∈ {NSE, US}; the simulator's session layout. Otherwise **OUTSIDE** (cannot arise by design).
2. All three securities ELIGIBLE (4.1) for the block, i.e. an ANALYSABLE panel. Otherwise the panel is not analysed (INCOMPLETE PANEL, 4.2); a block with no ANALYSABLE panel is **INSUFFICIENT**.
3. Report the ELIGIBLE share; FEED-QUALITY-REVIEW is applied per 4.5.

### 8.2 Step 2 — per-dimension zone tables (baseline cleaning)
**Reference modes (revision 5).** Exactly one mode applies to the whole phase. It is declared in the freeze manifest before any data acquisition and cannot change afterwards; switching modes needs a numbered new protocol version. The reference files of the declared mode are read by SHA-256.
- **Mode A — D6 authorised and completed.** The reference set is the frozen D6 set of section 12 (market, n, df, shape and day-factor sd configurations, reference quantities and file hashes as specified there). D-tail, M6, M7 and D-family use the four-variant envelopes defined below. D6 counts as completed only when all its cells are finished, the reference quantities are computed and the files are hashed; a partially completed D6 is not Mode A and its outputs are not used. D6 does not modify the validated C3 domain (section 12).
- **Mode B — D6 not authorised.** The only reference is the existing Stage 0 file `outputs/milestone4/h1_calibration/stage0/real_data_descriptive/reference_known_df_distribution.csv` (simulated worlds only; hashed in the manifest). It is a **single-variant reference**: 200 repetitions per df; df 3, 4, 5, 6, 8, 10, 20 and 1000 (its near-Gaussian world, treated as the grid value ∞ under **[ASSUMPTION]**); day-factor sd 0.3 only; no shape variants; scopes all, open, middle and close for each market; statistics kurtosis, Hill at the top 1%, 2%, 5% and 10%, and |z| exceedance counts; quantiles 5%, 50% and 95%. It has **no per-stock scope, no Laplace worlds and no fit-noise reference**. It is **not** the D6 reference and supplies **no four-variant envelope**; no Mode B report may imply otherwise. In Mode B: (1) D-tail is classified only for n = 59, with R_S(d) = [q05, q95] of the single variant for the block's market and M2 = kurtosis, M3 = Hill top 5%, M4 = exceedances of |z| > 4 per 1,000; for n ≠ 59 the D-tail result is **U** with reason D-TAIL-NO-REFERENCE, so a block ends CANNOT BE CLASSIFIED unless another dimension is a reliable rank 4 (then OUTSIDE, by 8.3 Phase 2); (2) there is no Laplace reference, so the D-family result is LAPLACE-UNEVALUATED and the rank-3 cap applies; (3) **alternative feature (d) needs a per-stock reference range and Stage 0 has none**, so indicator (d) cannot be evaluated and D-alt is **U** in every Mode B block, reason D-ALT-NO-PER-STOCK-REFERENCE; **no substitute reference, proxy or workaround is permitted**; (4) there is no fit-noise reference, so the shape thresholds cannot be checked and every Mode B label carries SHAPE-THRESHOLDS-UNCHECKED; (5) every Mode B label carries SINGLE-VARIANT-REFERENCE. **Consequence:** in Mode B no block can receive a coverage rank (1, 2 or 3); each block ends OUTSIDE (a reliable rank 4 on some dimension) or CANNOT BE CLASSIFIED. Mode B is a descriptive measurement and data-quality report without placement. Whether the Stage 0 worlds' layout equals the validated 59-session layout of each market (docs/14 §6 describes them as following the real sample's layout of about 59–60 days) is not verified here **[UNRESOLVED: to be confirmed from docs/14 and the Stage 0 script before Mode B is used]**.
- **Neither mode may use population kurtosis or any other approximation in production** (8.10).
If any needed measurement is UNRELIABLE (7.2), the dimension result is **U**.

**D-tail (M5) — reference selection, fixed in advance (Mode A rule; Mode B as in the Mode B paragraph above).** Reference worlds come only from the frozen reference set of the declared mode (in Mode A the D6 set of section 12), never from the data. For a block of market μ and target n, and each statistic S ∈ {M2, M3 (5% cut-off), M4}, and each reference df d ∈ {3, 4, 5, 6, 8, 10, 20, ∞}, the **reference range** R_S(d) = [ min over the four variants (shape ∈ {flat, E}) × (day-factor sd ∈ {0.3, 0.6}) of the 5th percentile, max over the four variants of the 95th percentile ] taken from the D6 cells (μ, n, d, shape, sd). This **envelope is the only rule**: no variant is chosen, and the shape and day-factor sd of the block are **not** used to select a reference cell (standardisation removes most of their influence; the envelope guards the residual). The same rule gives the by-period (M6) and by-stock (M7) ranges from the period-level and stock-level statistics saved with the same worlds. **Combination:** G_I = the set of d for which R_S(d) **overlaps I_θ for all three statistics** (intersection; no weighting). The rule, the cut-off, the grid, the envelope and the D6 cell list are frozen and hashed before any real data are obtained, and the real-data code reads the reference files of the declared mode by hash. **G_I is a set of reference worlds not contradicted by the data. It is a descriptive index; it is not an estimate of the data-generating distribution and implies no likelihood, best-fitting df or inference.**
Evaluate in order, stopping at the first match: (1) G_I empty, or its span exceeds four steps of the grid, or (Mode B) n ≠ 59 → **U**; (2) G_I = {3} → rank 4, reason **TAIL-DF3-ONLY**; (3) 3 ∈ G_I and another element → rank 3, reason **TAIL-DF3-WITH-OTHERS**; (4) min G_I = 4 → rank 2, reason **TAIL-DF4**, flag **FRONTIER** if the nearest shape is E or D5; (5) min G_I ≥ 5 → rank 1. Reference values 8 and 20 are "bracketed" and flagged, not validated. In Mode B the rule is the single-variant rule of the Mode B paragraph (n = 59 only, no envelope).

**D-shape (M8) — deterministic nearest-shape, deletion, ambiguity and degeneracy rules.** For each validated shape σ of the market compute d_σ = RMS of the difference of natural logs of the profiles on the used slots, each profile first divided by its arithmetic mean over the used slots (Appendix A); s(σ) = half the smallest distance from σ to any other validated shape of that market; q_σ = d_σ / s(σ).
- **Degeneracy guard (revision 4).** Validated shapes whose pairwise distance is below 10⁻⁹ are **identical profiles** and form one equivalence class (a cell lookup accepts any member; s(σ) is computed against the nearest *other class*). If, after merging, fewer than two classes remain, or the smallest between-class distance is below 0.05 [PROVISIONAL, D5], or any s(σ) ≤ 10⁻⁹, the shape table is **degenerate**: the freeze stops (11.7) and the protocol is revised; q_σ is never evaluated with s(σ) = 0. In the frozen shape set there are no identical profiles and the smallest distance is 0.125 (Appendix A), so the guard is inactive; it exists for future shape tables.
- **Full sample:** σ₁ = argmin d_σ; ties (|d_a − d_b| ≤ 10⁻¹² · max(d_a, d_b)) broken by the fixed order E, D5, R2, flat, D1.5, D3.0; σ₂ = the next nearest (same rule).
- **Deletion:** for each delete-one-session replicate i compute its nearest shape σ₁(i) by the same rule.
- **Flags:** **NEAR-TIE** if d_{σ₂} ≤ 1.15 · d_{σ₁} in the full sample; **SHAPE-UNSTABLE** if σ₁(i) ≠ σ₁ for **any** i; **AMBIGUOUS-SHAPE** = NEAR-TIE or SHAPE-UNSTABLE.
- **Candidate set** K = {σ₁} ∪ {σ₂ if NEAR-TIE} ∪ {σ₁(i) : i = 1..n}.
- **Class of a candidate σ ∈ K:** the interval I of d_σ (jackknife of d_σ) gives the q-interval [max(0, L)/s(σ), U/s(σ)]; the rank is the highest zone intersecting it, zones on q: q ≤ 1 → 1; 1 < q ≤ 2 → 2; 2 < q ≤ 4 → 3; q > 4 → 4. **D-shape rank = highest rank over σ ∈ K.**
- σ₁ is used for flags and reporting; **rank 1 additionally requires |K| = 1**.
- D-shape is computed for the panel and separately for each of the three stocks; the dimension rank is the highest over the four. A stock whose nearest shape differs from the panel's records STOCK-SHAPE-DIFFERS.
**These thresholds are [PROVISIONAL]; consequences in 8.7 and Appendix A.**

**D-daysd (M10).** x = day log-volatility factor sd. Zones: x < 0.15 → 4; 0.15 ≤ x < 0.20 → 2; 0.20 ≤ x ≤ 0.40 → 1; 0.40 < x < 0.50 → 2; 0.50 ≤ x ≤ 0.70 → 3 (reason DAYSD-0.6, special cell required, see special rules below); x > 0.70 → 4.

**D-dep (M11–M12).** Components φ, s, ρ (day-volatility lag-1 autocorrelation; cross-stock day-factor correlation; cross-stock return correlation); the market's estimated setting e: NSE (0.441, 0.454, 0.355), US (0.190, 0.141, 0.187). For each component: a_c = e_c/2, b_c = 1.5·e_c, c₀ = min(0.10, a_c). Zones on the component value x (negative values treated as 0, reported): x ≤ c₀ → 1; c₀ < x ≤ a_c → 2 (nearest point none; dependence not negligible); a_c < x ≤ b_c → **E-zone** (reason E-ZONE-DEP, special cell required); x > b_c → 4. The dimension rank is the highest over the three components. A component interval wider than 0.4 → U.

**D-alt (M6, M7, M13, M14, M15; features a–e).** For each feature k ∈ {a, b, c, d, e}: base value X₀ (a 0, b 0, c 0, d 0, e kurtosis 3) and tested value τ_k (a: 0.0302, the mean of the analytic lag 1–5 squared-return autocorrelations 0.0376, 0.0335, 0.0298, 0.0266, 0.0237; b: 2 excess exceedances per 1,000; c: 3 grid steps (df 4 against 8); d: 4 grid steps (df 3, 5, 8 at grid positions 0, 2, 4); e: kurtosis 7.65). Indicators: (a) M13; (b) M14; (c) the grid-position gap between the hull midpoint of G_I for the middle period and the mean of the hull midpoints for open and close (M6); (d) the range over the three stocks of the grid position of each stock's hull midpoint (M7); (e) M15. Strength f = (X − X₀)/(τ_k − X₀), interval I_f = [f_L, f_U] (from the interval of X).
- **Zone definitions on f (closed/open ends as written):** **negligible** f < 0.25 (including negative f, reported); **weaker** 0.25 ≤ f < 0.75; **comparable** 0.75 ≤ f ≤ 1.25; **stronger** f > 1.25.
- **Assigning a zone to an interval (revision 4).** The zone set Z(I_f) = all zones that intersect I_f, applying the endpoint rules above exactly: f_U = 0.25 intersects *weaker* (closed at 0.25); f_L = 0.75 and f_U = 0.75 intersect *comparable* (closed at 0.75); f_U = 1.25 intersects *comparable* (closed at 1.25) and f_L = 1.25 intersects *comparable* but not *stronger* (open above 1.25). The **feature zone** is the most restrictive zone in Z(I_f) under the order negligible < weaker < comparable < stronger. **If Z(I_f) contains three or more of the four zones, or its extreme zones are negligible and stronger, the feature indicator is UNRELIABLE (U).** A point-like interval (f_L = f_U) is treated as the single zone containing f. Intervals overlapping two adjacent zones take the more restrictive one.
- Let m = the number of features a–e whose feature zone is not negligible.
- m = 0 → rank 1 (for this dimension).
- m = 1: weaker → rank 2 **MONO-DEPENDENT**; comparable → rank 3 (reason ALT-k-COMPARABLE, special cell required); stronger → rank 4.
- m ≥ 2 → rank 3 if every non-negligible feature is weaker (MONO-DEPENDENT, combination untested), otherwise rank 4 (each alternative was validated alone).
- Any indicator UNRELIABLE → U. In Mode B indicator (d) has no reference and the dimension is U (reference modes above).
**Role of the monotonicity assumption (A-mono).** The class "weaker" rests on the *unvalidated* assumption that a feature weaker than a tested point lies between the base cell and that point in effect on C3. A-mono is used for nothing except this rank-2 placement (and the m ≥ 2 all-weaker rank-3 placement): a MONO-DEPENDENT label is never REPRESENTED, is reported as "NEAR BOUNDARY (assumption-dependent)", is counted separately in every summary, and is never included in a statement that blocks are within the validated domain.

**D-family (alternative (f), Laplace shocks, and the tail-shape family).** Laplace shocks have kurtosis 6, the same as t6, and a tail-decay ratio P(|z|>4)/P(|z|>3) of 0.243 against 0.261 for t6, 0.305 for t5 and 0.201 for t8 (analytic, unit variance); **its tail indicators are essentially indistinguishable from those of a t5–t8 world at the sample sizes used**, so it has no separate mapping indicator. It is therefore handled as a **family-ambiguity cap**, not as a feature. **Production rule (Mode A):** using the D6 Laplace worlds of section 12, form R_S^Lap analogously to D-tail (envelope over the same four variants, same market and n); the block is **Laplace-compatible** if R_S^Lap overlaps I_θ for all of M2, M3 (5%) and M4. If Laplace-compatible, or if the Laplace reference is unavailable (always the case in Mode B), the block is capped at **rank 3 with reason LAPLACE-AMBIGUOUS** (or LAPLACE-UNEVALUATED), because the validated base cells are Student-t worlds and a Laplace-type world has been validated at one point only (shape E, 59 days, ALT_f). Laplace-incompatible → no cap. **No population-kurtosis rule exists in the production algorithm** (see 8.10).

**D-complete.** The baseline requires complete bars (8.1 step 2).

### 8.3 Step 3 — precedence, joint-cell matching and special rules
**Cell types.** BASE cell: one of the 88 gated cells, (market, n, shape, df, dependence ∈ {none, estimated}, day-sd ∈ {0.3, 0.6}). ALT_k cell: one of the 12 alternative-process cells (feature k, shape E, n = 59, market). The 8 df 3 report-only cells can award no rank better than 4 and are never matched.

**Validated df order** (heavy to light): 4, 5, 6, 7, 10, ∞. For G_I with hull [min G_I, max G_I] (∞ largest): **Dreq = { v validated : min G_I ≤ v ≤ max G_I }**; if empty, Dreq = the validated values immediately below and immediately above the hull (for example G_I = {8} gives {7, 10}; G_I = {20} gives {10, ∞}). **Required df d\* = min Dreq (the heaviest compatible validated tail).**

**Order of evaluation (single, fixed pass):**
- **Phase 1 — dimension ranks.** Compute the ranks (or U) of D-tail, D-shape, D-daysd, D-dep, D-alt from 8.2.
- **Phase 1b — special-cell requirements** (they are part of the dimension rank and are evaluated before any precedence):
  - *E-ZONE-DEP* (rank 3 only if satisfied, else rank 4): every shape in K ∈ {E, D5}, n = 59, Dreq ∩ {4, 6} ≠ ∅, D-shape rank ≤ 2, D-daysd rank 1, same market. (The estimated-dependence BASE cells T6 and T4 × E, D5 at 59 days then exist.)
  - *DAYSD-0.6* (rank 3 only if satisfied, else rank 4): every shape in K ∈ {E, D5}, n = 59, 4 ∈ Dreq, D-dep rank 1, D-shape rank ≤ 2, same market (the T4 × E, D5 sd-0.6 BASE cell exists).
  - *ALT-k-COMPARABLE* (rank 3 only if satisfied, else rank 4): ALT_k of the market exists with n = 59, shape set K = {E}, D-shape rank ≤ 2, D-dep rank 1, D-daysd rank 1, and the hull of G_I, evaluated on the reference grid, containing the process's own shock dfs (a: 6; b: 10; c: 4 and 8; d: 3, 5 and 8; e: 8).
- **Phase 2 — precedence.** (i) If any dimension rank is 4 → **OUTSIDE**. (ii) Else if any dimension is U → **CANNOT BE CLASSIFIED**, listing the unreliable dimensions. (iii) Else r = maximum of the dimension ranks (each ∈ {1, 2, 3}).
- **Phase 3 — caps.** If the D-family cap applies (always, as LAPLACE-UNEVALUATED, in Mode B), or ROUNDING-MATERIAL (8.9): r := max(r, 3). Caps never lower a rank, never alter OUTSIDE or CANNOT.
- **Phase 4 — joint-cell matching (only if r ∈ {1, 2}).**
  - **Target tuple** (all required to be realised by one BASE cell): market = the block's; n = the block's target n; shape: **every σ ∈ K**; df = d\*; dependence = none; day-sd s\* where s\* = 0.3 if the point estimate x̂ ≤ 0.45, s\* = 0.6 if x̂ > 0.45, and **both** 0.3 and 0.6 are required if x̂ = 0.45 exactly.
  - **Match test:** the tuple is matched if, for every σ ∈ K and every required s\*, a BASE cell with exactly that (market, n, σ, d\*, none, s\*) exists in the frozen cell list (a table-membership test).
  - **Matched cell reported:** the cell for the first σ ∈ K in the fixed order E, D5, R2, flat, D1.5, D3.0.
  - **No metric over cells.** There is no distance that combines dimensions and no weighting. Each dimension contributes its nearest validated value by the frozen zone tables; **if different dimensions imply a tuple that is not a cell, there is no joint match** (the dimensions are not traded off against each other). Ties inside a dimension require **both** candidates (conjunction), never a choice.
  - **Outcome:** matched → r stands (r = 1 labelled THIN COVERAGE if n ∈ {90, 180}); not matched → **r := 3, reason NO-JOINT-CELL**.
  - **Rank 1** additionally requires |K| = 1, D-alt m = 0, no cap, and D-dep, D-daysd, D-tail rank 1; the same tuple rule applies with s\* = 0.3.
  - **Rank 2** (from tail df 4, a fringe dependence zone, a day-sd rank-2 zone, shape q in (1, 2], or a weaker feature) uses the same tuple rule: the nearest validated value in every dimension is realised by one BASE cell.
- **Phase 5 — label.** The outcome (r, OUTSIDE, or CANNOT BE CLASSIFIED) is reported with reason codes **collected from every dimension and cap, whatever the outcome**, so that a block that ends OUTSIDE or CANNOT BE CLASSIFIED also carries the other applicable reason codes (every dimension not at rank 1; NO-JOINT-CELL; LAPLACE-AMBIGUOUS or LAPLACE-UNEVALUATED; ROUNDING-MATERIAL; MONO-DEPENDENT; the special codes) and flags (FRONTIER, AMBIGUOUS-SHAPE, STOCK-SHAPE-DIFFERS, THIN COVERAGE, SURVIVOR-BIASED; in Mode B also SINGLE-VARIANT-REFERENCE and SHAPE-THRESHOLDS-UNCHECKED) and the reference mode (A or B). FEED-QUALITY-REVIEW is a market-level status (4.5, 8.5), not a label flag.
**Interaction of the special rank-3 rules with rank-2 matching, and consistency checks.**
1. A special rule failing (no cell) gives rank 4 in Phase 1b, so it is OUTSIDE by Phase 2 and **cannot be masked** by a cap or by rank-2 matching, which both come later.
2. A special rule succeeding gives rank 3 and **Phase 4 is not run** (r ∈ {1, 2} only): special rank-3 outcomes need their own cell, not a rank-2 match. A block with E-ZONE-DEP and tail df 4 (T4, estimated dependence) is rank 3 by E-ZONE-DEP; its tail reason TAIL-DF4 is kept as a reason code.
3. Caps and the NO-JOINT-CELL rule can only raise r from 1 or 2 to 3; no path lowers a rank or turns OUTSIDE, CANNOT or INSUFFICIENT into a coverage label.
4. Rank 3 arising from D-tail (3 ∈ G_I with others), LAPLACE-AMBIGUOUS or ROUNDING-MATERIAL needs no cell; no rank-2 matching is attempted.
5. Rank 1 and rank 2 use one match function with the same tuple rule, so they cannot select different cells for the same measurements.
6. Every nearest value is a deterministic function of the measurement intervals and frozen tables; the cell list is the frozen list of 88 + 12 cells; nothing is chosen after seeing results.

### 8.4 Step 4 — cleaning variants
- The block is labelled from the **baseline**. A C or I baseline outcome is final.
- **Strict** (if evaluable, 7.3): its label is computed with the same tables and the reference of the target n. **Final rank = max(baseline rank, strict rank).** The strict variant can only worsen the label, and reason codes it adds are marked CLEANING-SENSITIVE.
- **Lenient (provisional text pending D17):** never improves a label; never defines rank 1 or 2; reported with rank capped at 3. **Stability check:** if the strict rank (and, if D17 retains the lenient variant, the uncapped lenient rank) differs from the baseline rank by two or more, the final label is **CANNOT BE CLASSIFIED**.

### 8.5 When the conclusion must be "insufficient evidence to place this block in the validated domain"
Any of: INSUFFICIENT (8.1); CANNOT BE CLASSIFIED by Phase 2 or the stability check (in Mode B this is every block that is not OUTSIDE: D-alt is U, and D-tail is U for n ≠ 59); a split-half instability flag. For INSUFFICIENT and CANNOT BE CLASSIFIED the report gives the reason code and no class. **The two differ:** INSUFFICIENT = no analysable panel exists for the block (data completeness, 8.1); CANNOT BE CLASSIFIED = an analysable panel exists but a dimension is unreliable or lacks a reference. **FEED-QUALITY-REVIEW is a market-level status, not a label and not a label flag:** labels for the market are computed but withheld (4.5) and no class is released until the user's recorded review decision (stop rule 11.7).

### 8.6 Strength values used above [computed 2026-11-12 from `alt_dgp_parameters.json`; analytic arithmetic, no simulation]
(a) Squared-return autocorrelation at lags 1–5: 0.0376, 0.0335, 0.0298, 0.0266, 0.0237 (r = e^{h−σ²}ε, σ = 0.25, ρ = 0.9, ε ~ t6 with fourth moment 6: Var(r²) = 6·e^{4σ²} − 1 = 6.704, Cov at lag k = e^{4σ²ρ^k} − 1). (e) Day-factor mixture variance 0.0900 (sd 0.30), kurtosis 7.65. (c), (d) are df gaps on the reference grid. (b) is the jump frequency 0.002. These are population values of the simulated worlds; real-data analogues include estimation noise, rounding and microstructure.

### 8.7 Consequences of the provisional shape thresholds (Appendix A) and expected behaviour
- Radius-s zones are disjoint; 2s and 4s zones overlap for many pairs (Appendix A); the nearest-shape, near-tie, deletion and most-restrictive rules resolve this deterministically.
- E, R2 and flat are close (log-profile RMSD 0.125–0.274), so s(E) = 0.087 (NSE) and 0.063 (US) is small. The sampling noise of a fitted profile at n = 59 is **unknown** and probably larger than s; if so, rank 1 on shape is unreachable for most blocks. The fit-noise reference of section 12 (Mode A only; in Mode B no such reference exists and labels carry SHAPE-THRESHOLDS-UNCHECKED) is the planned check **before freezing**; thresholds may then be revised only in a numbered new protocol version created before real data are obtained.
- Because the domain is sparse, every dimension must agree, and the Laplace cap applies to any tail with df-equivalent roughly 5 to 8, an outcome of mostly PARTIALLY REPRESENTED and OUTSIDE blocks is expected and informative, not a defect.

### 8.8 Wording attached to every label
"The measured dimensions of this block [are / are not] consistent with simulated worlds in which C3 stayed within its pre-specified upper limit of [5.5% / 6.0%]; features listed in section 8.9 as unmapped are not covered." It never states that C3 *will* or *does* hold that rate on these data, and never that the test is calibrated. Every label also states the reference mode. Mode B reports carry: "Reference: Stage 0 single-variant reference, n = 59 only, no per-stock reference and no Laplace reference; this is not the D6 four-variant envelope; no coverage label is assigned in Mode B."

### 8.9 Register of features without a (separate) mapping rule
| Feature | Treatment | Effect on label |
|---|---|---|
| Laplace / non-Student tail shape (alternative f) | not identifiable from tail indicators (8.2 D-family) | cap rank 3, LAPLACE-AMBIGUOUS or LAPLACE-UNEVALUATED |
| Stock-specific shape differences | D-shape per stock (8.2) | rank may rise; STOCK-SHAPE-DIFFERS |
| Shape non-stationarity within the block | split-half instability (7.2 item 7) | UNRELIABLE → C |
| Price rounding / tick size (M17) | screen: if the typical tick is more than 5% [PROVISIONAL, D5] of the median absolute 5-minute return for any panel security, the block is flagged ROUNDING-MATERIAL | cap rank 3, reason ROUNDING-MATERIAL; below the screen a printed caveat only |
| Overnight returns, volume | not used by the H1 statistic (within-day prices only) | printed caveat; no rank effect |
| Auctions, closing-window feed behaviour, microstructure | the used slots are the simulator's; the NSE 15:15–15:25 behaviour is recorded | printed caveat; no rank effect |
| Regime shifts, events, announcements | split-half instability; no event calendar is used | UNRELIABLE → C when detected; otherwise caveat |
| Panels other than 3; other exchanges | excluded by design | none |
| Any other feature not listed | cannot be assessed | printed caveat; the label states it covers measured dimensions only |
A label of REPRESENTED therefore means: every measured dimension is rank 1, every feature a–e is negligible, the tail family is Laplace-incompatible and evaluated, rounding is below the screen, and a BASE cell matches. Where the evidence is insufficient the algorithm yields PARTIALLY REPRESENTED or CANNOT BE CLASSIFIED, never REPRESENTED.

### 8.10 Mapping validation tests (to be written and passed on constructed inputs before any data access)
The tests feed the algorithm **ideal zero-width inputs** (the cell's own population values) and check **exact** outcomes: label, set of reason codes, set of flags, per-dimension ranks and the identity of the matched cell. A label of PARTIALLY REPRESENTED is accepted **only** where the table below expects it **with exactly the listed reason codes**; any other reason set, or a rank 3 where rank 1 or 2 is expected, is a failed test. Report-only and alternative cells are never counted as gated cells.

**Test convention versus production rule (revision 4).**
- **Test convention (TEST-ONLY, a fixture, not a statistical claim):** because ideal zero-width inputs have no D6 envelope, the fixture marks a world Laplace-compatible iff its *population kurtosis* lies in [4.5, 9] (t5, t6, t7, t8 and Laplace itself); df ∞ (3), df 10 (4) and df 4 (infinite) are incompatible. It exists only to give the tests a defined input.
- **Production rule:** Laplace-compatibility is decided **only by the D6 envelope overlap of 8.2 D-family**, from the envelopes and the interval I_θ of the real measurements. The production function takes the envelopes as required input; **if they are absent it returns LAPLACE-UNEVALUATED and the rank-3 cap and must not fall back to the kurtosis convention** (a test asserts this; another asserts that the string "kurtosis in [4.5, 9]" and any numeric kurtosis rule do not occur in the production code path).
- **Re-derivation after D6:** once D6 envelopes exist, the 8.10 tests are rerun with envelope-derived compatibility inputs; every category whose expected label changes (notably categories A, B, D for T6 cells, and G for a, e, f) is documented and re-approved **before** any real data are obtained. Until then the expected labels of those categories are conditional on the test convention.

| Category | Cells (count) | Expected label | Expected reasons / flags | Exceptions and notes |
|---|---|---|---|---|
| A. Gated, base, Laplace-incompatible (test convention) | df ∞ (flat, E, D5, R2 at 59 days; E, D5 at 125 and 250) and df 10 (59 days, 4 shapes), both markets (24) | REPRESENTED, matched cell = itself | none | – |
| B. Gated, base, Laplace-compatible (test convention) | T7 (10), T6 plain (16), T5 (10) (36) | PARTIALLY REPRESENTED | LAPLACE-AMBIGUOUS | for df 7 the ideal G is {6, 8} (7 is not on the reference grid) |
| C. Gated T4, no features | T4 plain (16): flat, R2 at 59 days (4), E, D5 at 59, 125, 250 days (12) | NEAR BOUNDARY, matched cell = itself (rank-2 matching, d\* = 4, s\* = 0.3) | TAIL-DF4; FRONTIER for E and D5 (12 cells) | – |
| D. Gated, estimated dependence | T6 E, D5 at 59 days (4); T4 E, D5 at 59 days (4) (8) | PARTIALLY REPRESENTED | E-ZONE-DEP; T6 also LAPLACE-AMBIGUOUS; T4 also TAIL-DF4 and FRONTIER | ideal dependence = the cell's own setting; special cell exists |
| E. Gated, day-factor sd 0.6 | T4 E, D5 at 59 days (4) | PARTIALLY REPRESENTED | DAYSD-0.6; TAIL-DF4; FRONTIER | special cell exists |
| F. Report-only df 3 | T3 flat, E, D5, R2, both markets (8) | OUTSIDE | TAIL-DF3-ONLY | **not gated**: excluded from every coverage tally; the test asserts the exclusion |
| G. Stage 4 alternative processes | 12 cells (six processes × two markets) | PARTIALLY REPRESENTED, matched cell = ALT_k | (a) ALT-a-COMPARABLE, LAPLACE-AMBIGUOUS; (b) ALT-b-COMPARABLE; (c) ALT-c-COMPARABLE, TAIL-DF4; (d) ALT-d-COMPARABLE, TAIL-DF3-WITH-OTHERS; (e) ALT-e-COMPARABLE, LAPLACE-AMBIGUOUS; (f) LAPLACE-AMBIGUOUS | ideal tail inputs are the shock dfs; (c) per-period G open {4}, middle {8}, close {4}; (d) per-stock G {3}, {5}, {8}; ideal f = 1 for the process's own feature, 0 for the others |

Totals: 24 + 36 + 16 + 8 + 4 = **88 gated**; 8 report-only; 12 alternative = 108. The table gives **Mode A** expectations: under the test convention REPRESENTED is expected for 24 of the 88 gated cells; this follows from the Laplace cap and the df 4 rule and is not a defect.
**Mode B expectations (mechanical, revision 5; reason codes are collected per Phase 5, so every Mode B block carries LAPLACE-UNEVALUATED and D-ALT-NO-PER-STOCK-REFERENCE).** The tests are run in both modes. In Mode B: every cell with target n ≠ 59 → CANNOT BE CLASSIFIED with reasons D-TAIL-NO-REFERENCE, D-ALT-NO-PER-STOCK-REFERENCE and LAPLACE-UNEVALUATED; every n = 59 cell of categories A–E and G → CANNOT BE CLASSIFIED with reasons D-ALT-NO-PER-STOCK-REFERENCE and LAPLACE-UNEVALUATED (plus the Mode A reasons that the single-variant reference still yields, for example TAIL-DF4, E-ZONE-DEP, DAYSD-0.6), flags SINGLE-VARIANT-REFERENCE and SHAPE-THRESHOLDS-UNCHECKED; category F (df 3 report-only, n = 59) → OUTSIDE (a reliable rank 4 from D-tail, G = {3}, takes precedence over U in Phase 2) with reasons TAIL-DF3-ONLY, D-ALT-NO-PER-STOCK-REFERENCE and LAPLACE-UNEVALUATED. The expectations follow the production order: Phase 1 dimension results (D-alt U everywhere; D-tail U for n ≠ 59), Phase 2 precedence (any reliable rank 4 → OUTSIDE, else any U → CANNOT BE CLASSIFIED). **No cell is expected to be REPRESENTED, NEAR BOUNDARY or PARTIALLY REPRESENTED in Mode B**, because Phase 2 ends every Mode B block before ranks 1–3 are assigned; a Mode B test returning ranks 1–3 fails, and Mode B must never use the kurtosis fixture.

**Negative and boundary controls (constructed):** (1) G_I empty → CANNOT BE CLASSIFIED; (2) two non-negligible comparable features → OUTSIDE; (3) one feature with f > 1.25 → OUTSIDE; (4) shape midway between E and D5 (q > 4) → OUTSIDE; (5) dependence above b_c → OUTSIDE; (6) a near-tie between two shapes → AMBIGUOUS-SHAPE and rank not 1; (7) a candidate panel with one INCOMPLETE security → INCOMPLETE PANEL, not analysed; (8) a block labelled only through lenient data → not rank 1 or 2; (9) strict worsening → final rank = max; (10) every zone endpoint value of every table yields exactly the class stated, including the interval-zone rule for I_f (f_U = 0.25, f_L = 0.75, f_U = 1.25, f_L = 1.25, and three-zone intervals giving U); (11) Laplace reference absent → LAPLACE-UNEVALUATED, rank ≤ 3, no kurtosis fallback; (12) two weak features → rank 3 and MONO-DEPENDENT; (13) MONO-DEPENDENT labels are counted in the separate tally; (14) a rank-2 tuple that is not a BASE cell (for example E-shape, df 4 at n = 90) → rank 3 NO-JOINT-CELL; (15) x̂ = 0.45 requires both sd cells; (16) a special rank-3 rule without its cell → OUTSIDE, not masked by a cap; (17) a degenerate shape table (identical profiles, or s ≤ 10⁻⁹) stops the freeze; (18) a market in FEED-QUALITY-REVIEW produces withheld labels and no release without the recorded review; (19) declaring both modes, or neither, stops the freeze.

## 9. Uncertainty, dependence between observations and limits of inference
### 9.1 Communicating uncertainty
Every placement is reported with intervals, n, the unusable-session ledger, variant labels, reliability flags, reason codes, the universe ledger and the feed-quality tables of 4.5. Tail estimates from 59 to 250 sessions are imprecise; a df-equivalent from kurtosis is unreliable below df 5; the Hill index depends on the cut-off; short-sample estimates are not the true tail index and a fitted or reference distribution is not the true data-generating process [ASSUMPTION flagged]. Regimes change; no stationarity claim is made.

### 9.2 What the simulated domain does not contain [ESTABLISHED/ASSUMPTION]
Overnight returns, volume, price rounding and tick size, microstructure and auctions, regime shifts, events, panels other than 3 stocks, exchanges other than the two layouts, non-iid days beyond the estimated settings, tails with df below 4 as gated cells, shapes outside the list, the NSE closing-window quirk, and any process other than the six tested at single points.

### 9.3 Overlapping blocks, dependent observations and limits of inference
- **Nested and overlapping blocks:** blocks of different n cover the same dates (a 59-session block lies inside a 250-session block), so their labels are not independent. Blocks of the same n are consecutive and non-overlapping, but adjacent blocks share regime and serial dependence of volatility.
- **Panels:** securities in a panel are cross-correlated (estimated return correlation in the domain 0.19–0.36); panels in one market share the market factor and calendar; panels are not independent replications.
- **NSE and US** blocks are on different calendars and are not paired.
- **Therefore:** results are reported as **counts of labels** (k of m blocks), with no p-values, no confidence statements about proportions, no pooling across overlapping blocks. No statement is made about securities outside the universe, periods outside the span, or the average behaviour of a market. The effective number of independent blocks is unknown and no estimate is attempted.
- Differences between securities, strata, markets and periods are descriptive and untested. If one panel's label differs between blocks, the variation is reported, not averaged.
- **Multiplicity:** many blocks and panels will be examined; all are reported, none highlighted.

## 10. Data sources and licensing: what was read and what was not
No account was created, no data downloaded, nothing purchased. Pages were read on 2026-11-12 only to learn terms. Everything not marked **[PRIMARY-READ]** is a **[LEAD]** to be confirmed on the provider's own page, and the *licence text read by the user*, before any acquisition.

| Provider | Claim | Status | Notes |
|---|---|---|---|
| Databento | usage-based pricing in $/GB, "Pay as you go for historical data"; no per-GB US-equity price on the page | **[PRIMARY-READ]** (databento.com/pricing) | dataset prices are in a catalogue not read |
| Databento | redistribution depends on the dataset; publisher licence restrictions pass through; "Most of our datasets can be redistributed internally or externally after 24 hours"; derived-work terms not stated | **[PRIMARY-READ]** | derived-statistics rights need the dataset licence |
| Databento | tiers list "$1,750 license fees per month" (Plus), "$4,500" (Unlimited), Standard "No license fees" | **[PRIMARY-READ]** | which tier covers US equities history not stated |
| Databento | OHLCV-1m for US equities; "Equities Mini" 8+ years; "no licence needed for T+1 historical" | **[LEAD]** | the pricing page lists OHLCV-1m only under CME and related venues; US-equity bar availability **not confirmed** |
| Massive (Polygon) | minute aggregates "Included in select Stocks plans": Starter 5 years, Developer 10 years, Advanced and Business all history, Basic not included; records from 2003-09-10; "all U.S. equities" | **[PRIMARY-READ]** (flat-files page) | consolidated or not: **not stated**; no licence terms there |
| Massive (Polygon) | plan prices $0, $29, $79, $199 per month; terms of service | **[LEAD]** | terms not read |
| TrueData | exchange-approved intervals include Tick, 1-, 2-, 5- and 15-minute (delayed), EOD | **[PRIMARY-READ]** (truedata.in) | NSE-equity history depth not stated |
| TrueData | data licensed, not owned; internal use including analysis permitted; redistribution, resale or public sharing needs prior written permission; storage not stated; API price by sales quote; plugin ₹1,699–₹3,299 per month; statements on exchange fees conflict | **[PRIMARY-READ]** | whether publishing aggregate results counts as redistribution is **unresolved**; written confirmation needed |
| NSE Data & Analytics | historical-data products and pricing for international clients; data-sharing policy restricting historical tick-by-tick access | **[LEAD]** | **both NSE PDFs timed out twice and were not read** |
| WRDS / NYSE TAQ | WRDS-built 5-, 15- and 30-minute indicators; institutional access; coverage dates | **[LEAD]** | the TAQ introduction page was read and states none of these |
| Zerodha Kite Connect (₹500 per month), Upstox (minute data from January 2022), Angel One, Alpaca Basic (IEX only, about 2.5% of volume) | as in `docs/03` | **[LEAD]** | project document dated 2026-10-30, itself partly unverified; not re-read |
| Yahoo Finance (yfinance) | about 60 days of 5-minute bars, revised, personal use only | **[LEAD]** (`docs/03`) | not suitable here |
No provider is confirmed as meeting depth, adjustment, completeness and licence requirements; the NSE side is entirely unconfirmed. Bar construction, IEX-only versus consolidated, session completeness and adjustment convention change the measures and must be documented; **results are not pooled across providers**. [UNRESOLVED D2.]

## 11. Reproducibility and audit trail
1. **Freeze before access:** this protocol, the scheduled-session list, universe lists and sources, calendar, thresholds, the declared reference mode and its reference files by hash (the D6 files in Mode A, the Stage 0 file in Mode B) and the code, in a new manifest `frozen_phase6_inputs.sha256` created before any data are fetched (the nine existing manifests remain valid).
2. **Write-once raw data** with SHA-256 (as `docs/05`); cleaned data in separate files recording the raw hash; ledgers are outputs.
3. **Deterministic procedure:** no random numbers in selection, exclusion, jackknife or mapping. The only random numbers in the phase are in the D6 reference exercise (section 12), under a registered seed.
4. **Run once:** each measurement is computed once per block and variant; reruns write new files.
5. **Report generator** reads saved files only and states planned versus actual counts of securities, candidate panels, analysable panels, blocks and unusable sessions.
6. **Tests** before use: DST conversion; exclusion rules on synthetic sessions; the jackknife checks T1–T6 of 7.2; the zone tables and combination on constructed inputs including every boundary and tie; the mapping validation tests of 8.10; no code in the phase calls the H1 statistic.
7. **Stop rules:** a licence term forbidding storage or derived statistics, a failed adjustment verification, FEED-QUALITY-REVIEW (4.5), a degenerate shape table (8.2), an unhandled session-hours change, or any need to alter a rule after seeing data stops the phase and is reported; the protocol changes only by a numbered new version.
8. **Licensing hygiene:** raw data stay outside the repository; only aggregates are written to `outputs/`.

## 12. D6 — descriptive reference exercise (specification; not authorised)
**Nature.** D6 is a **descriptive reference exercise**: it produces sampling ranges of *descriptive statistics* under known, hand-specified worlds. It is **not** an extension, test, expansion or recalibration of the validated C3 domain, and it adds no validated point to section 3.1.
**Strict separation from C3 and the calibration record.**
- D6 never computes the H1 statistic T, a bootstrap, a critical value or a rejection rate, never loads a C3 critical value, a validation output or any `reject_*` column, and never imports `max_abs_t`, `bootstrap_t` or `c3_*` code (a test enforces this).
- The existence of a D6 world at a given df, shape or n (for example df 8, df 20, 90 or 180 days, Laplace shocks) **does not make that point validated**; section 3.1 is frozen and is the only source of validated points. Any extension of the validated domain would need a new calibration stage under separate authorisation and is not part of this protocol.
- D6 results are not added to the H1 calibration simulation ledger (8,024,000 simulations) and are recorded as "descriptive reference world-draws (not calibration)". Its outputs go to a separate folder with their own manifest and are read-only inputs to the mapping.
**Design [PROPOSED; all counts subject to approval].**
- *Tail reference (M2–M4, M6, M7):* Student-t shocks, unit variance, df ∈ {3, 4, 5, 6, 8, 10, 20, ∞}; market ∈ {NSE, US}; 3 stocks; n ∈ {59, 90, 125, 180, 250}; shape ∈ {flat, E}; day-factor sd ∈ {0.3, 0.6}; iid days; no clustering, jumps, dependence or rounding. 320 cells × 2,000 worlds = 640,000 world-draws.
- *Laplace reference (D-family):* Laplace shocks (scale 1/√2, unit variance), same market, n, shape and day-factor sd grid: 40 cells × 2,000 = 80,000 world-draws.
- *Fit-noise reference (M8):* shapes {E, D5, R2, flat, D1.5, D3.0}, day-factor sd 0.3, Student-t df 6 shocks, market × n: 60 cells × 1,000 = 60,000 world-draws; records the RMSD between the fitted and the true profile, for judging the provisional shape thresholds.
- *Pipeline:* each world goes through the same descriptive pipeline as real data (sections 6–7: standardisation, M2–M4, M8, and the period- and stock-level statistics), with nothing else.
- *Seed:* one new master seed, **proposed 20261216** (not registered until approved; 20261201–20261213 and 20261215 are in use); per-world `SeedSequence(master, spawn_key=(family, market, n, df, shape, day_sd, replication))`.
- *Reference quantities:* the 5th and 95th percentiles (linear interpolation, the quantile routine of `c3_value`) per cell and statistic; the envelope of 8.2 is computed from these; the median and 95th percentile of the fit-noise RMSD.
**Reference modes (see 8.2; exactly one applies).** *Mode A* = D6 authorised **and completed** (all cells finished, reference quantities computed, files hashed): the four-variant envelopes of 8.2 apply, the frozen configurations above are used without change, and the validated C3 domain is untouched. *Mode B* = D6 not authorised: only the existing Stage 0 file is used, identified as a **single-variant reference** (200 repetitions per df; df 3, 4, 5, 6, 8, 10, 20, 1000; day-factor sd 0.3 only; scopes all, open, middle, close; **no per-stock scope, no Laplace worlds, no fit-noise reference**); D-tail only for n = 59 and D-TAIL-NO-REFERENCE otherwise; the LAPLACE-UNEVALUATED rank-3 cap; D-alt is U because alternative feature (d) has no per-stock reference; hence no coverage label in Mode B. Stage 0 is never described as equivalent to D6 and never supplies the envelope; no workaround reference is permitted. A partially completed D6 is neither mode.

## 13. Proposed execution sequence (none of it authorised)
- **E0.** Review and approval of this protocol and D1–D17, and **declaration of reference Mode A or Mode B**. **Separate authorisation for data access.**
- **E1.** The user reads the provider licences; adjustment convention verified from the provider's documents; provider decided.
- **E2.** Mode A: authorise D6, register the seed, run the reference exercise to completion; review fit-noise and envelopes; re-derive the 8.10 expectations; issue a numbered protocol version if thresholds change. Mode B: no D6; confirm the Stage 0 layout (8.2 UNRESOLVED). Freeze scheduled sessions, universe lists, calendar, thresholds, reference files and code; create the manifest.
- **E3.** Write and test the code on synthetic data, including the jackknife checks and 8.10.
- **E4.** Acquire daily reference data for liquidity ranks, then 5-minute data for the selected panels; hash raw files.
- **E5.** Quality control, session-level usability, universe ledger, feed-quality tables (4.5).
- **E6.** Compute section 7 measures, intervals and diagnostics under the three variants.
- **E7.** Apply section 8.
- **E8.** Report: all blocks and panels, ledgers, uncertainty, what the simulations do and do not cover.
- **E9.** Review gate. H1 testing on real data or the research protocol would need a new authorisation.

## 14. Decisions requiring your approval before execution
| ID | Decision | Recommended default |
|---|---|---|
| D1 | Approve this protocol (revision 5) and its freeze | after your review |
| D2 | Provider, budget, licence sign-off; written confirmation that publishing aggregate descriptive statistics is permitted | licensed vendor or institutional access; not Yahoo |
| D3 | Universe and per-block index-membership history source | NIFTY 50 and S&P 500 at block start |
| D4 | Span; scheduled-session calendar source | at least two years |
| D5 | Provisional thresholds and conventions: pair-level 10%, panel-level 27%, minimum three analysable panels, 80% eligible share; strict-variant constant 8 and n_s ≥ ⌈0.9 n⌉; ROUNDING-MATERIAL 5%; shape multiples s/2s/4s, near-tie 1.15 and degeneracy limits (10⁻⁹, 0.05); day-sd bands; dependence cut points; feature zone cut points 0.25/0.75/1.25; jackknife failure thresholds | as proposed, to be confirmed before freezing; none statistically validated |
| D6 | Authorise the descriptive reference exercise of section 12 (cell list, counts, seed 20261216) and thereby select **Mode A**; declining selects **Mode B** (no coverage labels, 8.2) | authorise separately, with registered seed |
| D7 | Six exposed stocks | exploratory, never pooled |
| D8 | Sector information | record only |
| D9 | Cleaning variants: baseline and strict whole-session as proposed; the lenient variant is subject to D17 | baseline and strict as proposed |
| D10 | Report all panels and blocks; counts of labels only | yes |
| D11 | Aggregate outputs allowed in the repository | aggregates only |
| D12 | Security identifiers in reports | per licence |
| D13 | Stop rules (11.7) | as proposed |
| D14 | Acceptability of calendar and index-membership sources | user to confirm |
| D15 | The unequal-group jackknife estimator of 7.2 (weights, equal 1/g averaging convention) and the consistency tests T1–T6 | approve, or specify another estimator |
| D16 | The list of outcome-free feed and liquidity characteristics used in the included-versus-excluded comparison (4.5) | as proposed |
| D17 | **Lenient-variant conflict (7.3 versus 4.5, 4.1, 8.1).** Lenient needs return statistics for sessions missing up to two used slots, but such sessions make the security INCOMPLETE and the candidate panel an INCOMPLETE PANEL that is not analysed, and 4.5 forbids computing return statistics for incomplete units; on analysable panels there are no incomplete sessions, so the lenient variant equals the baseline and its stability check is vacuous. Approval needed: (i) drop the lenient variant; (ii) keep it as an exploratory report on panels that are incomplete only because of sessions missing at most two used slots, separate from labels and from the 4.5 tables, amending 4.5 and 8.4; or (iii) another specification | none recommended; a decision is required before the freeze (the lenient clauses of 7.3 and 8.4 are provisional until then) |

## 15. What could accidentally overstate the simulated evidence
1. **Circularity** (3.3). 2. **"REPRESENTED" read as "calibrated"**; frontier cells are near nominal level, and `docs/25`'s unexplained repeat variability remains. 3. **Sparse domain read as a grid.** 4. **Student-t reference worlds** and the Laplace ambiguity: tail family is not identifiable at these sample sizes. 5. **Short samples** and an unreliable jackknife. 6. **Overlapping, nested blocks, shared securities and market factors.** 7. **Conservatism of C3** mistaken for calibration. 8. **Liquid index constituents; survivorship** controlled only to the provider's coverage. 9. **Provider differences**; no provider confirmed. 10. **Multiplicity.** 11. **Unmodelled features** (8.9). 12. **Provisional thresholds** are design choices, not statistical boundaries; the shape tolerances may be too tight for estimation noise. 13. **Nearest-point assignment** and the A-mono assumption are not validation. 14. **Alternative processes** were each validated once; "comparable" is a narrow match. 15. **Strict cleaning** can make a block look lighter-tailed; it only worsens labels. 16. **Complete blocks and panels** may be a calmer, more liquid subset; the 10% and 27% review conditions and the included-versus-excluded tables do not remove selection bias. 17. **The test convention** of 8.10 could be mistaken for a production rule; it is not. 18. **Mode B** reports are measurement reports without placement, and the Stage 0 reference is not the D6 envelope.

## 16. Assumptions and unresolved questions
- **[ASSUMPTION]** Equal-RMS shape normalisation and the simulator's used slots describe real sessions adequately.
- **[ASSUMPTION]** The jackknives give usable stability intervals; heavy tails may defeat them (7.2 converts failures to "cannot classify"). The unequal-group estimator is chosen for exact unbiasedness on the sample mean only; its behaviour for non-linear statistics is unestablished.
- **[ASSUMPTION A-mono]** monotone effect between a base cell and a tested alternative point; unvalidated; limits labels to rank 2, MONO-DEPENDENT.
- **[ASSUMPTION]** The four-variant envelope (shape × day-factor sd) bounds the residual influence of shape and day-factor sd on the standardised tail statistics; not checked until D6 exists.
- **[ASSUMPTION]** The baseline `fit_bar_model` standardisation is adequate for outlier detection in the strict variant despite masking (7.3).
- **[UNRESOLVED]** D2–D17 (D17 is the lenient-variant conflict); whether the Stage 0 worlds' layout equals the validated 59-session layout (Mode B only); provider terms (especially NSE and the derived-statistics rights); handling of NSE session-hour changes; whether an exchange-grade NSE feed has the closing-window quirk; whether all five sample sizes can be met for NSE on the chosen provider; whether provider-missing delisted securities can be characterised; the expected labels of 8.10 categories A, B, D (T6) and G (a, e, f), which depend on the test convention until D6 envelopes exist; whether C3's behaviour between the five validated sample sizes (not authorised, not attempted).

## Appendix A — shape profiles and provisional thresholds (deterministic arithmetic, 2026-11-12)
Computed with the frozen profile functions (`run_h1_inference.profile_for`, `run_h1_next.exp_profile`, EXP_TAU in `h1_stage3`), multiplier 1, on the used slots (NSE 71, US 77); each profile divided by its arithmetic mean over the used slots, natural logs, root-mean-square difference. No data, no random numbers.

**NSE:**

| | flat | E | D5 | R2 | D1.5 | D3.0 |
|---|---|---|---|---|---|---|
| flat | – | 0.273 | 0.767 | 0.158 | 1.088 | 0.469 |
| E | 0.273 | – | 0.593 | 0.174 | 0.903 | 0.329 |
| D5 | 0.767 | 0.593 | – | 0.631 | 0.329 | 0.306 |
| R2 | 0.158 | 0.174 | 0.631 | – | 0.955 | 0.330 |
| D1.5 | 1.088 | 0.903 | 0.329 | 0.955 | – | 0.634 |
| D3.0 | 0.469 | 0.329 | 0.306 | 0.330 | 0.634 | – |

s: flat 0.079, E 0.087, D5 0.153, R2 0.079, D1.5 0.164, D3.0 0.153.

**US:**

| | flat | E | D5 | R2 | D1.5 | D3.0 |
|---|---|---|---|---|---|---|
| flat | – | 0.276 | 1.231 | 0.173 | 1.744 | 0.751 |
| E | 0.276 | – | 0.997 | 0.125 | 1.512 | 0.517 |
| D5 | 1.231 | 0.997 | – | 1.093 | 0.521 | 0.492 |
| R2 | 0.173 | 0.125 | 1.093 | – | 1.609 | 0.609 |
| D1.5 | 1.744 | 1.512 | 0.521 | 1.609 | – | 1.013 |
| D3.0 | 0.751 | 0.517 | 0.492 | 0.609 | 1.013 | – |

s: flat 0.087, E 0.063, D5 0.246, R2 0.063, D1.5 0.261, D3.0 0.246.

**No identical profiles** (smallest pairwise distance 0.125, US E–R2), so the degeneracy guard of 8.2 is inactive and every s(σ) > 0. **Zone overlaps:** radius-s zones (rank 1): no pair overlaps in either market. Radius-2s zones (rank 2): 8 of 15 pairs overlap in both markets (E–flat, E–R2, R2–flat, D1.5–D5, D1.5–D3.0, D3.0–E, D3.0–D5, D3.0–R2). Radius-4s zones (rank 3): 14 of 15 pairs in NSE (all but D1.5–flat), 12 of 15 in US (all but D1.5–flat, D1.5–E, D1.5–R2). Closest pairs: E–R2 0.174 (NSE) and 0.125 (US); flat–R2 0.158 and 0.173; E–flat 0.273 and 0.276. Resolution: 8.2 D-shape. The thresholds s, 2s, 4s have **no statistical basis**, only the spacing of the frozen shapes; attainability at the sample sizes in question is unknown until the fit-noise reference exists.

## Appendix B — change logs
**Revision 5 section-level classification (reconciled in the verification of revision 5):** *content changes:* 4.5, 7.2 (the iid and dependent-data wording of the Basis bullet, added in the verification), 7.3 (Lenient bullet), the conventions paragraph of 8, 8.2, 8.3, 8.4, 8.5, 8.7, 8.8, 8.10, 11 (item 1), 12 (the reference-modes paragraph), 13 (E0 and E2), 14 (D1, D6, D9, D17), 15, 16, Appendix B and Appendix C (scope paragraph and one added sentence). *Revision metadata only:* the title line and the Status paragraph at the top of the file. *Completely unchanged:* sections 1, 2 and 3 (an earlier report mistakenly said section 1 was updated; only the Status paragraph above it changed), 4.1–4.4, 5, 6, 7.1, the delete-one and delete-block formulas and diagnostics of 7.2, 8.1, 8.6, 8.9, 9, 10, Appendix A.
**Revision 5 (this revision; narrow consistency audit, no redesign):**
1. **Two mutually exclusive reference modes (8.2, 8.3, 8.5, 8.8, 8.10, 11, 12, 13, 14):** Mode A (D6 completed, four-variant envelopes) and Mode B (Stage 0 single-variant reference, D-tail only for n = 59, D-TAIL-NO-REFERENCE otherwise, LAPLACE-UNEVALUATED cap); the Stage 0 file has no per-stock scope, so alternative feature (d) cannot be evaluated and Mode B yields no coverage label; no substitute reference; mode declared in the manifest; Mode B test expectations added; the old "fallback" paragraph removed.
2. **FEED-QUALITY-REVIEW wording (4.5, 8.3, 8.5, 8.10):** it is a market-level status: labels are computed but withheld until the user's recorded review; it is not a label flag and no decision rule changed.
3. **INSUFFICIENT versus CANNOT BE CLASSIFIED (8.5):** distinguished explicitly; unit of labelling (panel, block) defined in section 8.
4. **D17 recorded (4.5, 7.3, 8.4, 14):** the lenient-variant conflict is left unresolved, with the approval required; D9 and the lenient clauses marked provisional.
5. **Jackknife re-check (Appendix C):** weights sum to 1, the weighted deleted-estimate mean equals the sample mean, the equal-size reduction holds; exact unbiasedness remains established for the sample mean only; no change to 7.2 or Appendix C.
**Revision 4 (retained):**
1. **Delete-block jackknife for unequal groups (7.2, Appendix C):** weights w_j = (n − m_j)/((g − 1)n), weighted mean of the deleted estimates, SE_B² = (1/g) Σ (h_j − 1)(θ_(−j) − θ̄_w)²; derived from exact unbiasedness for the sample mean; reduces to the standard formula for equal sizes; revision 3's formula withdrawn (slightly biased: 1.003 at n = 59); numerical verification for n = 59 and for all validated n and strict-variant thresholds; consistency tests T1–T6 specified (to be created at E3).
2. **Strict-cleaning detection (7.3):** exact S1–S6 procedure: detection by the frozen `fit_bar_model` on the baseline sample, single pass, |z| = √e2 > 8, whole-session removal, n_s ≥ ⌈0.9 n⌉ evaluated before recomputation, full recomputation on n_s sessions, no second pass, circularity and masking limitations stated.
3. **Feed quality and panel completeness (4.1, 4.2, 4.5, 8.1):** candidate panels formed from all provider-carried securities (no replacement); pair-level and panel-level incompleteness reported separately; deterministic FEED-QUALITY-REVIEW conditions (10%, 27%, three analysable panels, 80%), all PROVISIONAL; 27% shown to be arithmetic; required outcome-free included-versus-excluded tables; explicit statement that no threshold removes selection bias.
4. **Rank-2 joint-cell matching (8.3):** fixed evaluation order; target tuple (market, n, every shape in K, d\* = heaviest compatible validated df, dependence none, day-sd nearest with conjunction on ties); table-membership test; no metric over cells; conflicting dimensions give no match, not a trade-off; interplay with special rank-3 rules and six consistency checks.
5. **Further checks:** D-shape degeneracy guard (identical profiles, s = 0) and verification that none exist; D-alt interval-to-zone rule with explicit endpoint and overlap cases and U for three-zone intervals; precedence and special-rule consistency in 8.3; 8.10 separates the TEST-ONLY population-kurtosis convention from the production D6-envelope rule, forbids fallback to it, and requires re-derivation after D6; decisions D15 and D16 added; controls 14–17 added.
**Revision 3 (retained):** fixed windows of exactly n scheduled sessions; fixed D-tail reference envelope; BASE/ALT_k cell types and the Laplace family-ambiguity cap; mapping validation categories 88/8/12; strict whole-session removal; deterministic nearest-shape rule; A-mono limits; D6 strictly descriptive.
**Revision 2 (retained):** deterministic algorithm; dependence zones without gaps; alternative-feature zones; per-block universe ledger; lenient cleaning limits; stronger jackknife diagnostics; provisional shape thresholds with computed distances; D6 specified; overlap and inference limits; provider claims split into primary-read and leads.

## Appendix C — unequal-group delete-block jackknife: derivation and numerical verification (deterministic; no data, no random numbers)
**Setting.** n observations y_i with iid errors of variance σ²; g groups of sizes m_j, Σ m_j = n; θ̂ = sample mean ȳ; ȳ_j = group mean; θ_(−j) = mean without group j; h_j = n/m_j.
**Derivation.**
1. θ_(−j) = (nθ̂ − m_jȳ_j)/(n − m_j) = θ̂ − (m_j/(n − m_j))(ȳ_j − θ̂).
2. Σ_j (n − m_j) θ_(−j) = g n θ̂ − n θ̂ = (g − 1) n θ̂, and Σ_j (n − m_j) = (g − 1) n, so **Σ_j w_j θ_(−j) = θ̂ with w_j = (n − m_j)/((g − 1)n)**, Σ w_j = 1. Hence θ̄_w = θ̂ exactly for the mean.
3. Var(ȳ_j − θ̂) = σ² (n − m_j)/(n m_j) (independent group means, variances σ²/m_j: ((1 − m_j/n)²/m_j + (n − m_j)/n²)σ²).
4. From 1 and 3: E[((n − m_j)/m_j)(θ_(−j) − θ̂)²] = E[(m_j/(n − m_j))(ȳ_j − θ̂)²] = σ²/n for **every** j, whatever the group sizes. Averaging over j with weights 1/g gives **E[SE_B²] = σ²/n = Var(θ̂)**: exact unbiasedness for the sample mean, for any group sizes.
5. Equal sizes (m_j = n/g): h_j = g, w_j = 1/g, θ̄_w = θ̄_B, SE_B² = ((g − 1)/g) Σ_j (θ_(−j) − θ̄_B)², the standard grouped (delete-a-group) jackknife.
6. Pseudo-values p_j = h_jθ̂ − (h_j − 1)θ_(−j) equal ȳ_j for the mean (used in test T3). Revision 3 used the unweighted mean p̄ = (1/g) Σ p_j (which is not θ̂ when group sizes differ) and the factor 1/(g(g − 1)); for the mean its expectation is not σ²/n unless the groups are equal.
**Numerical verification (scratch script, exact algebra on constructed index sets; the sample mean written as a quadratic form y′Qy, for which E[y′Qy] = σ²·trace(Q) when Q·1 = 0).**

| n | group sizes (counts) | trace(Q_new)·n | max\|Q_new·1\| | θ̄_w = θ̂ | trace(Q_rev3)·n |
|---|---|---|---|---|---|
| 54 | 5 (×6), 6 (×4) | 1.000000000000 | 1.3e-18 | yes | 1.008000 |
| 59 | 5 (×1), 6 (×9) | 1.000000000000 | 1.4e-18 | yes | 1.003000 |
| 81 | 8 (×9), 9 (×1) | 1.000000000000 | 7.6e-19 | yes | 1.001250 |
| 90 | 9 (×10) | 1.000000000000 | 1.2e-18 | yes | 1.000000 |
| 113 | 11 (×7), 12 (×3) | 1.000000000000 | 6.9e-19 | yes | 1.001591 |
| 125 | 12 (×5), 13 (×5) | 1.000000000000 | 1.5e-18 | yes | 1.001603 |
| 162 | 16 (×8), 17 (×2) | 1.000000000000 | 2.4e-19 | yes | 1.000588 |
| 180 | 18 (×10) | 1.000000000000 | 3.2e-19 | yes | 1.000000 |
| 225 | 22 (×5), 23 (×5) | 1.000000000000 | 3.7e-19 | yes | 1.000494 |
| 250 | 25 (×10) | 1.000000000000 | 2.6e-19 | yes | 1.000000 |
Also n = 50, 60 (equal sizes): the new estimator and the revision 3 formula both equal the standard grouped-jackknife formula to 10⁻¹⁴, and n = 61: revision 3 gives 1.002143. **n = 59 worked example** (nine groups of 6 and one of 5, g = 10). For the deterministic sequence y_i = i (i = 1..59): θ̂ = 30; h_j = 9.8333 (nine groups) and 11.8 (the group of 5); w_j = 0.099812 (nine groups) and 0.101695, Σ w_j = 1; θ_(−j) = 33, 32.3208, 31.6415, 30.9623, 30.2830, 29.6038, 28.9245, 28.2453, 27.5660, 27.5; Σ w_jθ_(−j) = 30 = θ̂ exactly; pseudo-values 3.5, 9.5, 15.5, 21.5, 27.5, 33.5, 39.5, 45.5, 51.5, 57 equal the group means exactly; **SE_B² (new) = 31.8396**, revision 3 formula 32.7025, classical s²/n = 5.0. For the fixed permutation y_i = (7i mod 59), i = 0..58: θ̂ = 29; **SE_B² (new) = 2.9050**, revision 3 formula 3.0126, classical s²/n = 5.0. *These single-sequence values are not comparable to s²/n:* the first sequence is a pure trend, which block deletion deliberately captures; the second is one fixed arrangement. Unbiasedness is a property of the expectation, which the trace identity verifies exactly.
**Scope of the verification.** It establishes exact unbiasedness for the sample mean **of iid, equal-variance observations** (and no claim for dependent financial time series), the equal-size reduction, and the exact identities T1–T3 (which hold algebraically for any data). It does **not** establish properties for kurtosis, Hill, correlations or other non-linear statistics, and the jackknife remains a stability diagnostic, not a guaranteed confidence interval. These checks were run in a scratch script outside the repository (and re-run in revision 5 with the same results); no test file was created. The automated tests T1–T6 of 7.2 are specified for E3.
