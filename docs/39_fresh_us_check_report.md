# 39 — Fresh-US H1 check: report (run once, 2026-11-14)

**Status:** results report for the check designed in `docs/37` (an addendum to `docs/33` §7). The owner authorised a single pull ("go ahead", in answer to the request for "pull once"). The design, runner, tests and C3 table were verified against `outputs/milestone4/frozen_p2_us_inputs.sha256` before the pull: all OK. Nothing was changed after seeing the data.

## 1. What was run

| Step | Detail |
|---|---|
| Source | Alpaca Market Data API, free paper account, `feed=sip`, `adjustment=raw`, 5-minute bars |
| Stocks | AAPL, MSFT, NVDA (as frozen) |
| Window | 2026-04-13 to 2026-08-05, fetched once (`data/p2_us_pull.done`); raw JSON kept under `data/raw/alpaca/` (git-ignored) |
| Raw bars | AAPL 15,213, MSFT 15,357, NVDA 15,360, including extended hours |
| Cleaning | Project cleaner, unchanged: 6,240 usable regular-session bars per stock (80 sessions × 78) |
| Sessions | 80 scheduled, 80 usable for every stock. Rule R1: the first 59 usable complete sessions are used, from 2026-04-13 to 2026-07-07 |
| Test | C3 at the frozen n = 59 value 3.298658 (unchanged), run once; output is write-once under `outputs/milestone4/p2_us/` |

## 2. Result

| Quantity | Value |
|---|---|
| T | **17.748** |
| C3 limit (n = 59) | 3.299 |
| Decision | **Reject equal volatility across open, middle and close** |
| Open vs middle, log ratio (SE) | 1.333 (0.075) |
| Close vs middle, log ratio (SE) | 0.180 (0.158) |
| Open vs close, log ratio (SE) | 1.153 (0.179) |

The open is again the most volatile period. Its mean square is about e^1.33 ≈ 3.8 times the middle's. Close vs middle is within about 1.1 standard errors of zero in this sample.

## 3. How it relates to earlier results

| Sample | Source | Days used | T | Decision |
|---|---|---|---|---|
| US, first (`docs/31`) | Yahoo | 2026-08-06 to 2026-10-28 | 22.594 | Reject |
| NSE, fresh (`docs/35`) | Yahoo | 2026-08-18 to 2026-11-13 | 17.305 | Reject |
| **US, fresh (this report)** | **Alpaca SIP** | **2026-04-13 to 2026-07-07** | **17.748** | **Reject** |

As `docs/37` requires, the two US results are reported side by side and not merged.

## 4. What this adds, and what it does not

- **Adds:** a US sample from a time window that does not overlap the first US sample and was never used to design the simulations, from a different data source. The rejection repeats there. This answers the "same data, same period" part of the independence limitation.
- **Does not add:** the stocks are still the same three US stocks that informed the simulation design, so independence is partial. Neither result shows that C3 has a 5% error rate on real data, which remains unverified (`docs/38` §3).
- **Expected direction:** higher volatility at the open is a well-known pattern; this confirms it rather than discovering it.

## 5. Data handling

- The raw and cleaned bars stay in `data/` (git-ignored). Only the aggregates in `outputs/milestone4/p2_us/` are committed.
- The API keys were used only as terminal environment variables and were not stored by the project. They were exposed in this working session's transcript while diagnosing a terminal problem, so the owner was advised to regenerate them.
- No money was spent.
