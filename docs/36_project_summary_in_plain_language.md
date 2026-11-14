# 36 — QuantLab in plain language: what was done, what was found, what is left (as of 2026-11-14)

**Purpose:** one readable summary for the project owner. It adds no new analysis. Numbers are from `docs/24`, `docs/31`, `docs/35` and the manifests; where something is unverified, it says so.

## 1. The question
Does the volatility (size of price moves) of a stock differ between the **open**, **middle** and **close** of the trading day, in NSE (India) and US 5-minute data? The project calls this H1. The hard part is not asking the question but having a **statistical test you can trust** on short samples (about 59 days, 3 stocks) where price moves have fat tails and uneven intraday shapes.

## 2. What was built (all on simulated data first)
1. **Diagnostics (M4a/M4b):** the ordinary bootstrap test **over-rejected** (it said "different" too often) when tails were heavy.
2. **Calibration programme (Stages 0–5):** a fixed critical value called **C3** was developed and then tested on fresh simulations it had not been tuned on. About **8.02 million simulations**, with frozen specifications, fixed seeds and file hashes so nothing could be quietly changed.
3. **Result:** C3 **never rejected more often than its allowed limit** in the tested simulated worlds (it is deliberately conservative, near 5.3% at its worst corner), also under six harder alternative processes. Verdict: **PARTIAL**, because it was shown only on a **sparse set of simulated cases (108 points)**, not everywhere and not on real data.
4. **Honest flags kept in the record:** the same simulations helped choose C3 (so part of the evidence is less independent than the cell count suggests); C3 has less power than the ordinary test; the repeat-run variability is larger than chance alone explains (cause unknown).

## 3. The real-data check (both free, both pre-registered, each run once)
| Market | Sample | Result |
|---|---|---|
| US (AAPL, MSFT, NVDA) | 59 sessions, 2026-08-06 to 2026-10-28 | T = 22.59 against 3.30: **reject** |
| NSE (RELIANCE, TCS, INFY) | 59 complete sessions, 2026-08-18 to 2026-11-13 | T = 17.31 against 3.30: **reject** |
In both, the open is far more volatile than the middle (about 2 times in volatility). This is the textbook intraday pattern, so the test **agrees with what was expected**; it is not a discovery.

## 4. What these results do not show
- Not independent: same source (Yahoo), same stocks that shaped the simulation design, overlapping dates.
- They do **not** show that C3 has a 5% error rate on real data, or that anything holds for other stocks, years or markets.
- A "reject" with T far above the limit is robust to C3's conservatism; a close call would not have been.

## 5. Phase 6 (the large real-data placement protocol)
Documents `docs/26`–`29`: a careful but heavy protocol that would place real-data blocks against the simulated cases. **Proposed and unapproved**; all 17 decisions are pending; one of its fallbacks (Mode B) does not match the existing Stage 0 reference (60 versus 59 days). The real-data H1 checks above did **not** need it. It can stay shelved.

## 6. What is left, all optional
1. **A truly fresh US check** (dates before 2026-08-06) using Alpaca's free plan; needs your own free sign-up and keys, and a separate authorisation. Only this would reduce the independence caveat.
2. **Phase 6**, if you ever want the descriptive placement: decide D1–D17 (`docs/32` lists suggested answers).
3. **Housekeeping you may want:** choose a licence for the repository; read the Yahoo and Alpaca terms yourself before publishing anything beyond aggregates.

## 7. Cost, safety and reproducibility
- **Cost:** nothing was spent. No account, subscription or paid data was used.
- **Integrity:** 11 hashed manifests, all verifying; 360 tests passing; frozen files, seeds and C3 were never edited; every outcome (including a not-testable NSE result in `docs/31`) was kept.
- **Data handling:** raw market data stays on your Mac (git-ignored); only aggregates are in GitHub.
- **Repository:** `https://github.com/Pravin292/Quantlab`, branch `main`.
