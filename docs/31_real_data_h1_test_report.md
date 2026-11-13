# 31 — Real-data H1 test report (one run, existing local sample, frozen C3)

**Status:** run once on 2026-11-13 under `docs/30` (plan R1–R8 plus the session-count stop rule; authorisation recorded in `docs/30` §9). Frozen inputs: `outputs/milestone4/frozen_real_h1_inputs.sha256` (plan, script, module, tests, C3 table; verified before the run). Outputs: `outputs/milestone4/real_h1/real_h1_results.csv` and `real_h1_metadata.json` (aggregates and file hashes only). No random numbers, no simulation, no rule changed after the run, C3 untouched. **All data are the one Yahoo Finance pull of 2026-10-30 (about 60 dates, 3 NSE and 3 US stocks), not independent of the simulation design (`docs/26` §3.3).**

## 1. Results
| Market | Dates in sample | Usable complete sessions (market) | Status | T | C3 critical value (n = 59) | Decision |
|---|---|---|---|---|---|---|
| NSE (INFY.NS, RELIANCE.NS, TCS.NS) | 60 | **58** (58 for each stock) | **NOT TESTABLE** | not computed | 3.298658 | none |
| US (AAPL, MSFT, NVDA) | 60 | 60 | TESTED, first 59 usable sessions 2026-08-06 to 2026-10-28 | **22.594** | 3.298658 | **Reject** equal period volatility |

**US components (log ratio of period mean squares, standard error):** open versus middle 1.457 (0.065); open versus close 1.478 (0.085); close versus middle −0.020 (0.090). The statistic is driven by the open: its mean square is about e^1.46 ≈ 4.3 times the middle's (volatility about 2.1 times), while close and middle are indistinguishable in this sample.

## 2. How to read it (as pre-registered in `docs/30` §5)
- **NSE:** per rule R7 the market is reported as not testable. Only 58 of 60 dates were complete for every stock and every used slot, so no 59-session window exists; n was not shortened and no incomplete session was admitted. No NSE inference is drawn. This is a data-completeness result, not evidence about NSE volatility.
- **US:** T exceeds the critical value by a very large margin (22.6 against 3.30), so the rejection does not depend on the exact size of C3 or on its conservatism. It says that, in these 59 sessions of three US stocks, the open period's volatility is clearly higher than the middle's. This is the well-documented intraday pattern; it **confirms an expected pattern and is not a new finding**.
- **What it does not show:** that C3 has a 5% rate on real data (unverified; real tails may lie outside the validated domain, `docs/14`), anything about the other US stocks, other periods or NSE, or any statement about close versus middle (the close-versus-middle contrast is near zero here, but the test was not designed or powered to establish equality).
- **Independence:** the six stocks informed the simulation design (shape E, dependence, day-factor sd); the second Yahoo pull covers the same dates. This is one first check of the procedure, not an independent replication.
- **Multiplicity:** two markets, no adjustment (R3); only one was testable, so the issue did not arise.

## 3. Checks and integrity
- Tests: `tests/test_research_real_h1.py`, 5 passed on constructed deterministic arrays (selection order, not-testable rule, equality of T with the direct statistic, decision rule, critical value) before the run.
- The nine earlier manifests verify (0 mismatches) after the run; `frozen_real_h1_inputs.sha256` verifies.
- The runner refuses a second run (write-once folder); no alternative windows, subsets or cleaning variants were tried.

## 4. What remains open
1. **NSE** needs a sample with 59 complete sessions: new data (a provider with complete bars), or a decision to admit incomplete sessions (a different, unvalidated rule; not authorised).
2. Any further real-data H1 test, other sample sizes, or an independent sample goes through the data-acquisition decisions of `docs/27` (provider, licence, D1–D17).
3. The descriptive placement of `docs/26` is still unapproved; this test does not replace it.
4. Nothing from this step is committed or pushed.
