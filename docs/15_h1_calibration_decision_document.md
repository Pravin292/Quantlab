# H1 Calibration — Decision Document (before Stage 1)

**Nothing was started.** No calibration experiment was run; Stage 1 has not begun. **Frozen specification v1 and its hashes are unchanged** (`shasum -c FROZEN_v1.sha256`: 23 of 23 files match). Everything proposed below that differs from v1 is listed in section F as a *numbered addendum (v1.1) for your approval*; none of it has been applied.

Your provisional decisions are recorded as: full grid including 250-day cells; Student-t(3) report-only; C2 explicitly unverified; 0.6 day-volatility cells kept; no silent changes.

## 0. Finding that needs your attention first: the frozen C2 implementation is defective

While writing section E I re-derived the fast double bootstrap from Beran's double bootstrap. The adjusted p-value should be the share of the **first-level** statistics T\* that exceed the (1 − p1) quantile of the **second-level** statistics T\*\*. My implementation (and the sentence in `spec_v1.json`) compares **T\*\*** with the quantile of T\*\*.

**[VERIFIED]** On 300 simulated datasets (`scripts/milestone4/stage0_c2_defect_check.py`, output `stage0/c2_defect_check/`), the p-value as implemented equals the ordinary bootstrap p-value in every case (mean and maximum absolute difference 0.0000), whereas the corrected variant differs from it by 0.014 on average (maximum 0.062). So **the frozen C2 is, in effect, the same test as the M4b bootstrap-t** and would add no information. My unit tests missed it because their null-rejection bounds were loose.

**[UNVERIFIED]** The corrected formula comes from my derivation and agrees with a recollection of the original, but I still have not read the original paper (section E). I did not change `h1_calibration.py` or the spec; doing so would change their hashes. Proposed handling: addendum A1 in section F.

---

## A. The three candidates

### A.0 Common setting (unchanged by every candidate)

Stocks s = 1..S (S = 3); days d = 1..n; used 5-minute slots j; periods p ∈ {1 = open, 2 = middle, 3 = close} with slot sets K_p; r_sdj the close-to-close return.

- Period mean square of day d: X_dp = (1/S) Σ_s (1/|K_p|) Σ_{j∈K_p} r²_sdj; matrix M = (X_dp), n × 3; X̄_p = (1/n) Σ_d X_dp.
- **Estimand** (unchanged): μ_p = E[X_dp], the pooled mean squared return of period p (days enter in proportion to their volatility, hence "day-volatility-weighted"), compared as ratios μ_a/μ_b.
- **Null hypothesis H0:** μ_open = μ_middle = μ_close (equal RMS volatility). Alternative: any inequality.
- Contrasts c ∈ {(open, middle), (close, middle), (open, close)} = `CONTRAST_IDX`.
- **Statistic:** θ̂_c = ln(X̄_a / X̄_b); u_dc = X_da/X̄_a − X_db/X̄_b; se_c = √( s²(u_c) / n ), s² the sample variance (ddof 1); t_c = θ̂_c / se_c; **T = max_c |t_c|**. Reject H0 when T exceeds a critical value, or equivalently when a p-value is ≤ α = 0.05.
- **M4b baseline:** draw n days with replacement B = 999 times, compute T\*_b = max_c |(θ\*_c − θ̂_c)/se\*_c|, critical value = 0.95 quantile of T\* (linear interpolation).

All candidates use the same T and the same H0 and the same estimand. They differ only in how the reference distribution of T under H0 is obtained.

### A.1 C1 — null-imposed model-based bootstrap with empirical bar-level shocks

Input: squared returns r²_sdj (stocks × days × used slots) and the three slot sets.

1. **Fit** (3 alternations, v2 starts at 1): g_sd = median_j( r²_sdj / v2_j ); then v2_j = mean_{s,d}( r²_sdj / g_sd ), rescaled to mean 1 over slots. (A non-finite or non-positive g is replaced by the mean of the valid ones.) Standardised squared shock e2_sdj = r²_sdj / (v2_j · g_sd), using the final v2 and the g from the last median step.
2. **Rescale per period:** e2 ← e2 / mean_{s,d,j∈K_p}(e2); slot shape w_j = v2_j / mean_{j'∈K_p} v2_{j'}.
3. **Artificial dataset b** (R = 499 of them), with n days: for each artificial day i draw a source day d_i uniformly from the D observed days and set g\*_{si} = g_{s,d_i} for all stocks together; for each period p and slot j ∈ K_p draw a pair (d', j') uniformly from the pooled set {1..D} × K_p and take the 3-stock vector e2_{:,d',j'}. Then X\*_ip = (1/S) Σ_s g\*_si · (1/|K_p|) Σ_{j∈K_p} w_j · e2\*_sij.
4. T\*_b = max_c |θ̂\*_c / se\*_c| computed on the artificial matrix exactly as T is computed on the data (no centring; the artificial world is null).
5. **Monte-Carlo p-value** p = (1 + #{b : T\*_b ≥ T}) / (R + 1); reject when p ≤ 0.05 (R + 1 = 500, so 0.05·500 = 25 is an integer).

**How H0 is imposed:** each period's shock mean is 1 and each period's mean slot shape is 1, so E[X\*_ip] = E[g\*] for all three periods: equal in expectation whatever the data say. Unit-tested: input data with period means differing by more than 1.5× give artificial worlds equal within 3%.

### A.2 C2 — fast double bootstrap-t (**as intended; the frozen code differs, see section 0**)

Outer: B = 999 day-resamples of M give M\*_b and T\*_b as in the baseline. Inner: for each b, one further day-resample of M\*_b gives M\*\*_b and T\*\*_b = max_c |(θ\*\*_c − θ\*_c)/se\*\*_c|. First-level p1 = (1/B) Σ 1{T\*_b ≥ T}; Q = the (1 − p1) quantile of {T\*\*_b}.

- **Intended (derived, not verified against the paper):** p_FDB = (1/B) Σ 1{T\*_b > Q}.
- **Implemented in the frozen code:** (1/B) Σ 1{T\*\*_b > Q}, which equals p1 up to rounding.

H0 is imposed only through centring, as in the baseline. Dependence on the data: day-level matrix only.

### A.3 C3 — conservative fixed critical value

crit_n = max over the gated development cells with sample size n of the 0.95 quantile of T, computed from a separate training run (25,000 simulations per cell, seeds disjoint from development and validation). Reject when T > crit_n. It uses nothing from the sample except T.

### A.4 What differs

| | Baseline (M4b) | C1 | C2 (intended) | C3 |
|---|---|---|---|---|
| Reference distribution of T comes from | resampling the observed days, centred | simulating a fitted null model of the bar-level data | two-level resampling of the observed days, centred | other simulations (worst case over a family) |
| Information used | day matrix | bar-level profile, day scales, shocks | day matrix | none (except T) |
| H0 imposed by | centring | rescaling the slot profile inside periods | centring | being a bound over null worlds |
| Time per test at 59 days (single core) | 1.4 ms | 49 ms | 3.4 ms | ≈ 0 |

### A.5 Assumptions that could affect validity

- **Baseline / C2:** days are exchangeable and the studentised statistic is close enough to pivotal. docs/13 §2.1 shows that with heavy tails it is not (T and the bootstrap critical value are dependent). A search result I could read states that the fast double bootstrap needs the statistic to be asymptotically independent of the random parts of the bootstrap data-generating process and can perform poorly otherwise; that condition is therefore in doubt here.
- **C1:** (i) the model r² = profile × day scale × shock describes the data well enough that T's null distribution depends on the data only through these features; (ii) the features are estimated accurately enough from 59 days (shape noise, shock-pool size ≈ 500 to 3,500 vectors per period); (iii) day scales are independent of shocks and iid across days; (iv) shocks are independent across slots; (v) the same fitted features apply under H0 and under the alternative (the profile equalisation prevents leakage of the alternative into the critical value, which also protects power). Violations: day-to-day persistence and within-day volatility clustering are not reproduced.
- **C3:** the true null distribution of T is dominated by the worst cell in the development family. It is **valid only inside that family**. A smaller family at 125/250 days (12 cells) than at 59 days (44 cells) makes crit_125 and crit_250 less conservative.

---

## B. C1 model choices

**B.1 Independent day scales.** Exactly: step 3 above draws d_i iid uniform on the D observed days and uses the stock vector g_{:,d_i}.
*Rationale:* the test's own standard error and the baseline bootstrap both treat days as iid (block = 1), so artificial worlds mirror the structure the statistic assumes. M4b found estimated persistence (phi 0.44 NSE, 0.19 US) changed H1 size little (T4 E: 7.8 vs 8.2 on NSE, 7.0 vs 6.9 on US). *Risk:* if real days are persistent, both the test's SE and C1's reference distribution understate variability of the period means, and C1 would inherit that. The development grid includes estimated-dependence cells (8) to check; a block variant (blocks of 5 days for d_i) is an alternative I have not built.

**B.2 Median-based day scale.** Exactly: g_sd = median over used slots of r²_sdj / v2_j.
*Rationale:* with heavy tails a mean-based scale would absorb an extreme bar into the day scale and shrink the standardised shock, removing the very tail we need to resample (breakdown point 50% versus 0%). The median's bias factor (ratio of median to mean of the shock distribution) is a constant common to all days and is removed by the per-period rescaling of the shocks to mean 1 and the profile to mean 1. *Risk:* it estimates the dominant volatility regime of a day, so within-day clustering is not treated as day-scale variation; the sampling noise of the median adds a little spread to g.

**B.3 Joint cross-stock shocks.** The 3-stock vector e2_{:,d',j'} is drawn as one unit, so contemporaneous cross-stock co-movement of shock sizes (including common large bars) is preserved, as is stock-specific tail weight (each stock keeps its own shock). The day-scale vector g_{:,d_i} is also drawn as a unit, preserving the cross-stock day-factor correlation. *Lost:* dependence of shocks across slots or days, and any link between a bar's shock and the day scale.

---

## C. The six alternative-process parameter sets (Stage 4)

Common to all: 3 stocks, shape E (market-specific), 59 days, both markets, 25,000 simulations, H0 true by construction. Unless stated: Gaussian log day factor with sd 0.3, independent across stocks, shocks of unit variance. **Null check before use:** expected period mean squares must be equal within 0.5% in a large sample (10⁶ bars) for each scenario and market.
*Parameter values beyond the text already in `cells_alternative_dgps.csv` (marked †) are additions needing approval (A4).*

| ID | Exact parameters | What it tests | Why it is relevant |
|---|---|---|---|
| a. Intraday volatility clustering | log-vol h_j = 0.9·h_{j−1} + √(1 − 0.9²)·0.25·η_j, η ~ N(0,1), h_0 ~ N(0, 0.25²) for each stock-day, independent across days; r = profile · e^{f} · e^{h − 0.25²}† · ε, ε ~ Student-t(6) unit variance († e^{−σ²} keeps E r² unchanged since E e^{2h} = e^{2σ²}) | A violation of C1's independent-slot shock draws and of the day-level iid structure; fattens period means through serial dependence | Intraday volatility clustering is a standard feature of intraday returns; the earlier H2 world F used a comparable regime with sd 0.25 |
| b. Jumps | ε ~ Student-t(10) unit variance, multiplied by √(1 − 0.0747)† = 0.9619; plus per bar and stock a jump with probability 0.002, size ±U(4, 8) × (profile · e^{f}), random sign († E[J²] = (8³ − 4³)/12 = 37.33; 0.002 × 37.33 = 0.0747 keeps E r² unchanged) | Rare very large idiosyncratic squared returns: a concentrated, non-Student tail (about 25 jumps per sample) | News-type events; checks procedures that learn tails from smooth shock pools |
| c. Period-specific tails | Student-t(4) in open and close, Student-t(8) in middle, unit variance | Tails differing across periods under H0 (equal variance, unequal shape) | Real open and close periods look heavier than the middle in the descriptive analysis (NSE close df 3–4, middle 5–6) |
| d. Stock-specific tails | Student-t(3), Student-t(5), Student-t(8) for stocks 1, 2, 3, unit variance (t3 scaled by 1/√3) | Mixed tails across stocks inside the market average | The six stocks are not identical; tests that C1 keeps each stock's own shock |
| e. Heavy-tailed day factor | f_sd = 0.3 · Student-t(3) / √3 (so sd 0.3), independent across stocks; shocks Student-t(8) | Rare very volatile days in the day-scale pool (C1 resamples only ~59 observed scales) | Volatility spikes on event days |
| f. Laplace shocks | ε ~ Laplace with scale 1/√2 (unit variance, kurtosis 6), iid | Heavy but exponential tails, all moments finite: a non-Student check on whether C1 helps or hurts where moment conditions hold | Guards against a method that only works for the Student-t family used in development |

---

## D. Calibration gates

**D.1 Exact rule (v1).** For each cell, k rejections in n simulations, p̂ = k/n and Wilson 95% interval [L, U].
- Tier A (df ∞, 10, 7, 6): **pass iff 0.045 ≤ p̂ ≤ 0.055 and U ≤ 0.060.**
- Tier B (df 5, 4): **pass iff 0.040 ≤ p̂ ≤ 0.060 and U ≤ 0.065.**
- Tier C (df 3): reported, not gated. Alternative processes: pass iff 0.040 ≤ p̂ ≤ 0.060. C3: upper bounds only (p̂ ≤ 0.055 tier A, ≤ 0.060 tier B).
- **A candidate passes only if every gated cell passes.** No averaging across cells; "the interval includes 5%" is never used.
- **Observations on v1 [VERIFIED by arithmetic]:** at n = 25,000 the Wilson clause is never binding (p̂ = 0.055 gives U ≈ 0.058; p̂ = 0.060 gives U = 0.0629) and the 7.0% ceiling is redundant for gated cells. They matter only if a cell has fewer valid simulations. They are harmless but should be stated, not implied to add protection (A3).

**D.2 Multiplicity across cells.** The gates are acceptance rules on estimated rates, not hypothesis tests, so no p-value adjustment is applied. Multiplicity enters as a design property: if every cell's true rate were exactly 5.0% and cells independent, a cell passes the tier A rule with probability 0.9997 at n = 25,000, so all 96 cells pass with probability about 0.97 (above 95% for up to 96 cells; `mc_precision/n_needed_for_joint_pass.csv`). Conversely, a method whose true rate is 5.6% in several cells will usually fail somewhere. Passing does not prove calibration; it means no miscalibration larger than roughly 0.3–0.5 points was detected on this grid. The risk of selecting among three candidates is handled by the single, fixed-seed validation run.

**D.3 Inconclusive results (a gap in v1).** v1 has only pass or fail. I propose (A2): every cell reports p̂, the Wilson interval and the distance to the nearest gate boundary in standard-error units; a cell whose boundary lies inside its 95% interval (|p̂ − boundary| < 0.27 points at n = 25,000) is flagged **boundary-ambiguous**. The pre-specified decision stays the point rule, but any final pass that depends on a boundary-ambiguous cell is reported as **"marginal, not demonstrated"** and no claim of calibration is made until a larger replication (for example 100,000 simulations in those cells, fresh seeds, approved by you) resolves it.

**D.4 Practical tolerance versus statistical uncertainty.**
- *Tolerance* (±0.5 points tier A, ±1.0 point tier B) says how far the **true** rejection rate may be from 5% and still be accepted. It is a scientific judgement about materiality, not a statistical quantity.
- *Uncertainty* (Monte-Carlo SE 0.138 points, 95% half-width 0.27 points at 25,000) says how well the simulation measures the true rate.
- The v1 rule compares the **estimate** to the tolerance. It is therefore **not an equivalence test**: a true rate of 5.5% passes about half the time, 5.6% about a quarter, 5.8% about 2% (n = 25,000). An equivalence-style rule (Wilson interval entirely inside [4.5%, 5.5%]) would need about 50,000 simulations per cell for a 0.998 per-cell pass chance at a true 5.0% and about 75,000 for a 0.998 joint chance over 96 cells, i.e. 2 to 3 times the budget. I recommend keeping the v1 rule and reporting the interval and ambiguity flags.

---

## E. C2: verification status

- **Source status [UNVERIFIED]:** I have not read the original (Davidson and MacKinnon 2007, Computational Statistics and Data Analysis). Fetches of three working-paper PDFs failed (HTTP 403, connection refused, tool error). Searches returned only descriptive sentences: each replication yields two bootstrap statistics, the cost is about twice a single bootstrap, and validity needs asymptotic independence between the statistic and the bootstrap DGP's random parts. They did not show the p-value equation.
- **Formula status:** the corrected version in section A.2 follows from Beran's double-bootstrap logic and matches a recollection (the search tool's own recollection, labelled "from memory", gave the same comparison of T\* with the second-level quantile). That is **not** verification. The frozen implementation is wrong by my own derivation (section 0).
- **If verification stays unavailable, what can be concluded:**
  - *Can:* report the rejection rates of "the implemented procedure as specified in an addendum", labelled "FDB-like procedure, formula unverified", with the same gates.
  - *Cannot:* say it is the Davidson–MacKinnon FDB; use its success or failure to support a conclusion about the FDB or about double bootstraps in general; select it as the H1 method or use it in any methodological conclusion; present it as a validated candidate.
  - *Treatment:* even if it passed every gate, I would not select it without your explicit approval of an empirically justified, "procedure-defined" status, and the report would state that the choice rests on simulation evidence only.
  - *Cheap internal check available now:* confirm the corrected code differs from the baseline and behaves as theory says in a case that does not depend on the paper (a Gaussian studentised mean, where the FDB's advantage over the single bootstrap is the claim to check). That check itself relies on literature I recalled, so it would be labelled likewise.

---

## F. Proposed addenda to the specification (v1.1) — NOT applied

| ID | Change | Reason |
|---|---|---|
| A1 | Replace the C2 definition and code by the corrected formula (T\* compared with the (1 − p1) quantile of T\*\*), labelled "unverified"; keep v1 files and hashes; new manifest FROZEN_v1_1.sha256 | Section 0 |
| A2 | Add the "boundary-ambiguous" flag and the "marginal, not demonstrated" outcome; define the larger-replication rule | D.3 |
| A3 | State that the Wilson clause and the 7.0% ceiling are redundant at n = 25,000 (no change in decisions) | D.1 |
| A4 | Fix the exact alternative-process parameters including the normalisations marked † in section C | Section C |
| A5 | Define C3 at validation sample sizes 90 and 180 days (train separate fixed values with disjoint seeds from development-type cells at those sizes), and state that the 125/250-day values come from 12 cells | v1 is silent; section A.5 |
| A6 | Record explicitly that C2 results are not used for any methodological conclusion until the formula is verified from the original | Your decision 3 |

I will not start Stage 1 and will not alter any frozen file until you approve the addenda you want. Unchanged and unaffected by the defect: C1, C3, the grids, the gates, the benchmark and the real-data description. Stage 1 itself (baseline method only) does not involve C2.

**New files this turn (all new):** `docs/15_h1_calibration_decision_document.md`, `scripts/milestone4/stage0_c2_defect_check.py`, `outputs/milestone4/h1_calibration/stage0/c2_defect_check/`.
