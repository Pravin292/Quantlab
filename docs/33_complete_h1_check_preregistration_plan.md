# 33 — Completing the real-data H1 check on new data: pre-registration plan (PROPOSED, not approved, not run)

**Status:** written 2026-11-13 after the owner chose path P2 (`docs/32`). **Choosing P2 is a direction, not an approval of this plan, of any provider, or of any data access.** Documentation only: no data was obtained or read, no statistic computed, no simulation run, no random number generated; C3, frozen files, manifests, source, tests and earlier documents are untouched.
**Labels:** **[CARRIED]** unchanged from `docs/30`; **[NEW]** new in this plan; **[DECISION]** needs the owner; **[BLOCKER]** nothing can start until it is settled.

## 1. Purpose
`docs/31`: US rejected equal period volatility (T = 22.59 against the frozen C3 value 3.298658); NSE was **not testable** (58 of 59 required complete sessions). This plan repeats the **same pre-registered test, once**, on new data so that (a) NSE can be tested and (b) the US result can be checked on sessions that were not used in the simulation design. It is a check of the procedure, not a new research claim; the expected volatility pattern makes a rejection the likely outcome.

## 2. What stays exactly as in `docs/30` [CARRIED]
Statistic T (max of the three |log ratio / SE| contrasts, `h1_calibration`), decision rule T > frozen C3 value for n = 59 (3.298658000460969, read from the frozen table, never recomputed); three stocks per market; first 59 usable complete sessions in date order; usable = every used slot finite for every stock (NSE 71 and US 77 used slots, the validated layout); fewer than 59 usable sessions means NOT TESTABLE with no shortening and no incomplete sessions; no multiplicity adjustment across markets and no combined claim; baseline excluded; no random numbers; single run with write-once outputs; aggregates only in the repository; the interpretation rules of `docs/30` §5 apply to each result.

## 3. What is new, and the decisions it needs
- **N1 [BLOCKER, DECISION] Provider, budget, licence.** Nothing can be acquired until the owner chooses a provider and reads its licence. The provider must (i) offer 5-minute bars for NSE and US equities over the chosen span with **no missing used bars** in a normal session, (ii) allow storing the data locally and publishing **aggregate** statistics (written confirmation recommended), (iii) state its adjustment and bar-construction conventions. From the record (`docs/26` §10, `docs/03`): TrueData (NSE; internal analysis allowed, public sharing needs written permission, NSE history depth not stated), Databento and Massive (US; availability and derived-data rights not confirmed), broker APIs (not verified); **no provider is confirmed**, and the NSE terms were never read. I cannot create accounts, enter credentials or accept terms.
- **N2 [DECISION] Stocks.** Suggested: the same three NSE and three US stocks, so the test is comparable and no stock is chosen by results. (Same stocks on new dates is independent of the *dates* in the design sample, not of the stocks' general behaviour.)
- **N3 [DECISION] Span and scheduled-session list.** Fix, before any fetch, a date range and the exchange-calendar list of scheduled regular full sessions (frozen in a manifest). Suggested: request at least 75 scheduled sessions per market so that 59 complete sessions can exist even if a few are lost; the test still uses only the first 59 usable ones. **US dates must not overlap** 2026-08-06 to 2026-10-28 (sample used in `docs/31`) if the aim is a fresh US check; NSE dates are free, because NSE was not tested.
- **N4 [NEW] Adjustment and units.** Returns are close-to-close log returns within the session as in the current pipeline; the provider's adjustment convention for splits and dividends must be verified from its documentation before the freeze. Any mismatch stops the run.
- **N5 [NEW] Data handling.** Raw files stored outside the repository, write-once, with SHA-256 (as `docs/05`); cleaned files separate and recording the raw hash; the freeze manifest lists this plan, the run script, the session lists, the stock list, the C3 table and the cleaning code, created **before** any data are fetched.
- **N6 [NEW] Session counts first.** The runner prints and saves complete-session counts and stops before computing T if a market has fewer than 59 (as `docs/30`). A missing-bar session is never repaired or imputed.
- **N7 [NEW] Interpretation addendum.** The NSE close tails may lie outside the gated validated domain (`docs/14`: df about 3–4; df 3 cells are report-only), so a non-rejection says little and a rejection is credible mainly because C3 is conservative. The fresh US result is reported next to the earlier one, never merged with it.

## 4. Steps and approvals (none given)
| # | Step | Needs |
|---|---|---|
| 1 | Decide N1–N3 (provider, stocks, span) and read the licence | **You** |
| 2 | Written confirmation from the provider on storage and publishing aggregates | **You and the provider** |
| 3 | Verify adjustment and bar conventions (N4) | You, from provider documents |
| 4 | Approve or change this plan; update it to name the provider, stocks, span | **You** |
| 5 | Freeze manifest (N5), run script tests on constructed data (reuse `tests/test_research_real_h1.py`) | Your authorisation |
| 6 | Data-access authorisation (separate, written) | **You** |
| 7 | Acquire once; hash; clean; run the counts stage, then T once | Your run authorisation |
| 8 | Report (`docs/34`), update the record; commit only on instruction | You |

## 5. Outcomes written in advance
- **NSE tested, reject:** evidence against equal period volatility in these 59 sessions of three stocks; not a statement about NSE generally, and C3's size on NSE-type tails remains unverified.
- **NSE tested, not reject:** weak evidence of equality (C3 power is low at 59 days).
- **Still fewer than 59 complete sessions:** NOT TESTABLE again; reported as a feed-quality finding, nothing changed afterwards.
- **Fresh US:** reject expected; if it does not reject, that is reported in full beside `docs/31` without reinterpreting either.

## 6. Decision request
Please give, in writing: provider and budget (N1); the stocks (N2); the span and calendar source (N3); your reading of the licence; then approval or changes to this plan. Until then no data is acquired.

## 7. Zero-cost version (added 2026-11-13 on the owner's instruction: no money may be spent)
**Constraint:** not a single rupee. Everything paid is excluded (`docs/34` §2–3: Kite Connect, TrueData, Databento, Massive, any add-on). This section replaces N1–N3 for the zero-cost case; sections 2, 3 (N4–N7), 5 are unchanged. It is **still a proposal**: choosing this constraint does not authorise any data access.
- **N1 (provider), NSE:** **Yahoo Finance via the project's existing pull script, no account, no cost.** One pull only. Yahoo returns only about 60 sessions, so the "at least 75 sessions" slack of N3 is **not available**; the test still needs 59 complete sessions. The first Yahoo sample had **58 of 60** complete NSE sessions (`docs/31`), so **NOT TESTABLE is a realistic outcome**; if it happens, it is reported as a feed-quality finding, the NSE question is closed at no cost, and no paid or alternative source is tried afterwards. Fyers Standard (free API plan) is **not planned**: it needs a brokerage account whose opening and ongoing cost I could not verify; it is used only if you personally confirm in writing that it costs nothing.
- **N1 (provider), US:** **Alpaca free plan, `feed=sip`** (needs your free sign-up and API keys; I cannot create them) for **fresh US dates**. Fallback with no account: the existing 2026-08-06 to 2026-10-28 Yahoo sample is already tested (`docs/31`) and is not repeated. If Alpaca's free terms or SIP history prove unusable, the US part is dropped, not paid for.
- **N2 (stocks):** same six stocks.
- **N3 (span):** NSE: the single Yahoo pull, frozen by hashing before analysis; the session list is whatever the pull contains, and the first 59 usable complete sessions are used. US: **59 usable sessions fully before 2026-08-06** (no overlap with the tested sample), chosen from a frozen scheduled-session list created before any fetch.
- **Cost guard:** no step may require payment, a subscription, a card, a trial that converts to paid, or a paid tier. If any page asks for payment, the step stops and is reported.
- **Licences:** Yahoo is personal use only and revised (`docs/03`); Alpaca's terms on storage and publication were not addressed in the pages read. Results are therefore kept **aggregate-only**, with no bar-level data stored in the repository or published.
- **Approvals still needed:** your explicit data-access authorisation for the single Yahoo pull (it is time-sensitive because Yahoo only serves about the last 60 sessions); your own Alpaca sign-up and keys for the US part (separate authorisation before any pull).
