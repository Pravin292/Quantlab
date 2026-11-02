# Milestone 1 — Data Requirements, Hypotheses, Screening, Assumptions

## 1. Data requirements (5-minute OHLCV)

- Fields: timestamp (stored timezone-aware, UTC plus exchange-local), open, high, low, close, volume.
- Sessions: NSE 09:15–15:30 IST (75 bars); US 09:30–16:00 ET (78 bars). Early-close days are flagged, not assumed.
- Bar timestamps = bar **start**. A bar's close is only known at start + 5 min; any signal using it may trade no earlier than the next bar's open (anti look-ahead).
- Minimum history for a meaningful study: **at least ~250 trading days per stock** (about one year). Free data gives ~60, so Milestone 2+ conclusions are provisional until more is collected.
- Corporate actions: need a record of splits/dividends per stock. Unadjusted intraday bars crossing one must be excluded or adjusted.
- Cleaning rules (to be implemented later, tested): drop the forming last bar; drop the zero-volume 16:00 US artifact; treat NaN placeholder bars as missing (never forward-fill prices into returns without flagging); report missing share per stock/day.

## 2. Hypotheses in testable form

| ID | Null hypothesis (H0) | Statistic and test | What would reject it |
|---|---|---|---|
| H1 | Variance of 5-min returns is the same in every session bucket | Return volatility per time bucket; Levene / Brown–Forsythe, Kruskal–Wallis on \|returns\|; time-of-day profile with confidence bands | Small p-value after multiple-testing correction, and the pattern repeats in separate weeks and in both markets |
| H2 | Volume spikes (relative to that time-of-day's trailing median, using past data only) have no relation to next-bar return or volatility | Event study: next-k-bar return and realised volatility after spike vs non-spike; permutation test or Mann–Whitney | Difference larger than chance and larger than transaction costs |
| H3 | 5-min returns have no autocorrelation (neither momentum nor reversion) | Autocorrelation at lags 1–6, Ljung–Box test, variance ratio test | Significant autocorrelation that survives costs and holds out-of-sample |

Caveat: with ~60 days, statistical power is low. Each result must report sample size and effect size, not only p-values. Testing many buckets and lags requires multiple-comparison correction.

## 3. Universe screening criteria (applied to each stock)

1. Data accessible from the chosen source.
2. ≥ 95% of expected bars present and non-NaN.
3. Median daily volume ≥ 1M shares (India) / 5M shares (US) and median 5-min volume large enough that cost assumptions are sane.
4. No unresolved corporate action in the window.

Status from the sample pull: all six pass 1 and 3. **Criterion 2 is borderline for the Indian stocks (~97.5% non-NaN, but the gaps cluster in specific times)**, and 4 is unchecked. Final pass/fail is deferred until the cleaning stage.

## 4. Assumptions and limitations log (living document)

- A1: Free Yahoo data is unofficial and may change or disappear.
- A2: ~60 trading days only; results are exploratory, not evidence of profitability.
- A3: Volume is as reported by Yahoo, which may not equal exchange volume.
- A4: Holiday and early-close calendars are not yet cross-checked against official exchange calendars.
- A5: Transaction costs and slippage are not yet modelled (Milestone for backtesting; must be included before any strategy result is shown).
- A6: No claim of profitability is made anywhere in this project at this stage.

## 5. Proposed next milestone (needs your approval)

**Milestone 2: Data pipeline.** Create a project virtual environment, an ingestion module that stores raw Yahoo pulls to Parquet without overwriting, a validation/cleaning module following section 1, and unit tests. No strategies, no dashboard.
