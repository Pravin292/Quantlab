# 44: Independent holdout check: design only (NOT run; needs your approval for a data pull)

**Status: DESIGN FOR REVIEW. No data has been pulled and nothing here has been run.** A holdout check needs new market data, and the project rule is that each pull needs your separate, explicit approval. This document fixes the plan so that, if you approve, the pull and the test follow rules written *before* any result exists.

## 1. Why a holdout
All real samples so far use the same six stocks (RELIANCE, TCS, INFY, AAPL, MSFT, NVDA) that helped shape the simulations. The fresh US sample added a new period and a new data source, but not new stocks, so the evidence is only partly independent ([docs/36](36_project_summary_in_plain_language.md) §5). A holdout asks: **does the frozen C3 test behave the same way on stocks that played no part in designing or calibrating it?**

## 2. Proposed stocks (US first)
- **JPM** (banking), **XOM** (energy), **KO** (consumer staples): large, liquid, in different sectors from the six already used.
- **Independence check done:** a search of the whole repository (code, data lists, reports, results) finds none of the three ticker symbols anywhere except in the Stage 6 plan, where they appear only as proposals. Selection rule, fixed now: three large US stocks from three different sectors that are absent from the repository. If you prefer other names, give them before the plan is frozen.
- NSE holdout: not proposed, because every free NSE route found needs an account with identity checks that only you can create ([docs/34](34_provider_research_for_p2.md), [37](37_fresh_us_check_design.md)).

## 3. Data source and cost
- **Preferred: Alpaca free plan, `feed=sip`, `adjustment=raw`**, the same source and settings as the fresh US check ([docs/37](37_fresh_us_check_design.md)). Cost ₹0. You create the keys yourself and pass them only as the environment variables `ALPACA_KEY_ID` and `ALPACA_SECRET_KEY`; they are never stored or printed. (Your earlier keys were regenerated, so new ones are needed.)
- **Fallback without keys: Yahoo public chart endpoint**: about 60 trading days only, so a 59-session test could end as NOT TESTABLE.
- **Correction to earlier wording.** The project's closing notes say a 90–250-session study "needs data that free sources do not provide". For the **US**, Alpaca's free plan may allow it: its documentation says historical all-exchange bars older than 15 minutes are available without a subscription ([docs/34](34_provider_research_for_p2.md)), and the earlier pull covered about four months. The depth beyond that is **unverified** until a small test pull. C3 already has frozen critical values for 59, 90, 125, 180 and 250 sessions, so longer samples would need no new calibration. For **NSE** the free route (Fyers, one year of history) needs your own KYC account, so it stays out of reach for me.

## 4. What would be run (frozen before the pull)
1. **Pull once** (JPM, XOM, KO; one window fixed in advance; write-once files with hashes), then clean with the project's pipeline.
2. **Real-data H1 test** with C3 unchanged, using the first 59 complete sessions (and, only if the data allow, the first 125, 180 and 250 as separate, pre-named tests). The `quantlab-h1` tool reproduces the three recorded real results exactly, so it can be used as the runner.
3. **Real-data placebo** (the Stage 6 Part C procedure): shuffle time-of-day labels, count false alarms.
4. **Where does the sample sit?** Measure persistence, shared volatility and return correlation as in Phase 6 and compare with the dependence levels Stage 6 tested (S0–S3).
5. Report every result, including NOT TESTABLE, the same way as [docs/31](31_real_data_h1_test_report.md), [35](35_nse_h1_check_report.md) and [39](39_fresh_us_check_report.md).

## 5. What it can and cannot show
- It can show whether the **same pattern** appears on untouched stocks and whether C3's behaviour on their structure (placebo, dependence) matches what Stage 6 found.
- A rejection is expected (the open is known to be more volatile), so a rejection alone says little about C3's false-alarm rate; the placebo is the part that does.
- It cannot prove a real-market false-alarm rate, and it says nothing about trading.

## 6. What I need from you to proceed
1. A yes to **one** pull of the three stocks from the preferred source (or the keyless fallback).
2. If Alpaca: new free keys exported in your terminal as environment variables (I cannot create them or read them).
3. Your choice of stocks (or confirmation of JPM, XOM, KO) and whether to try the longer 125/180/250-session windows.
After that I would write and hash the exact window and rules first, then pull once, then run.
