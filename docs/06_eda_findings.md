# Milestone 3 — Exploratory Data Analysis: findings

**Status: EXPLORATORY.** The data is one 60-day Yahoo Finance pull per stock (about 59 usable trading days). It is not sufficient evidence for any robust or profitable trading strategy, and nothing below should be read as one. No hypothesis was formally tested. Reproduce with `python scripts/milestone3/run_eda.py`; all numbers come from CSVs in `outputs/milestone3/`.

## 1. Data used and preservation
| Symbol | Rows | Days | Raw snapshot SHA-256 | Duplicates removed |
|---|---|---|---|---|
| RELIANCE.NS | 4,460 | 2026-08-05 → 10-30 | cfd0857862bb4efec2fea98c0011df216240d101d6166145791790409582fec1 | 0 |
| TCS.NS | 4,460 | same | 66f1a9d1601db3aeec867edae3da3691441c9e7865f5d1180153916b4672d653 | 0 |
| INFY.NS | 4,460 | same | c08ef11b563e37e51c2de6e412ecdaea3f4212618b493c444357cd0f258d74f2 | 0 |
| AAPL | 4,681 | 2026-08-06 → 10-29 | 8faf215de09383030514c660c7420a8b85be065594e8daa449aa75a85340bc92 | 0 |
| MSFT | 4,681 | same | 983f387b97df90e11edb77c99ccdaf14e03f56a652f3d1c303b05238b399aff6 | 0 |
| NVDA | 4,681 | same | 99b1f2f46d2ea39cf07897b33d38b7c5d4bfc5776cbcb8cdf5c03d559ba3986e | 0 |

(Also in `outputs/milestone3/snapshots.csv`.) The runner re-parsed each raw file (read-only), confirmed its hash equals the one stored in the cleaned file, and confirmed re-cleaning reproduces the stored cleaned data exactly. Raw snapshots and the 12 cleaned sample files were not modified. The NSE snapshots were taken at about 12:02 IST on the last day, so that day is partial.

## 2. Not verified (carried over)
- **Corporate-action adjustment** of intraday prices is unverified. A split or dividend in the window would look like a return. None was checked for.
- **Official holiday and early-close calendars** are unverified. Days with no data are assumed to be holidays; early closes would show as missing bars.
- **Volume** is Yahoo's, not exchange-verified. US volume definition (consolidated or not) is unconfirmed.
- Yahoo revises history between pulls (docs/04), so numbers may change on a re-pull.

## 3. Definitions and exclusions
**Return** = log return ln(close_t / close_{t-1}) between two consecutive, usable bars (5 minutes apart, same day). No overnight returns; a missing bar gives no multi-bar return.

**Opening candle** (09:15 NSE, 09:30 US): has no previous bar, so it has no close-to-close return. Its open-to-close return is a separate analysis (`opening_candle_open_to_close.csv`) and is excluded from every other return statistic.

**Period mapping** (bar START time, half-open intervals, so each candle falls in exactly one period; verified by tests on all 75 and 78 slots):
| Market | open | middle | close | separate |
|---|---|---|---|---|
| NSE | 09:15–09:55 (9 bars) | 10:00–14:25 (54) | 14:30–15:10 (9) | 15:15–15:25 (3): unreliable closing window |
| US | 09:30–10:25 (12) | 10:30–14:55 (54) | 15:00–15:55 (12) | none |

**Exclusions** (each bar has exactly one reason; see `exclusions.csv`). Returns for the NSE stocks: about 94.6% usable (e.g. TCS 4,218 of 4,460 bars), with 113–123 empty bars, 56–66 NSE closing-window bars set aside, 60 opening candles, 2 forming bars and 1 bar after a gap. US stocks: 4,620 of 4,681 usable (98.7%), 60 opening candles and 1 unexpected 16:00 bar each.
- Forming bars: excluded everywhere.
- Empty, invalid, off-grid bars: excluded, never filled.
- NSE closing window 15:15–15:25: kept out of all main results and shown shaded on charts. Of its bars, 15:20 is empty on all 59 days and 15:25 on 46 of 59 for each stock; 15:15 is empty on 6–16 days. The few returns it does have are in `nse_closing_window.csv`.
- Volume statistics: NSE 09:15 volume is excluded entirely (reliability unproven), as are zero-volume bars, flagged bars and the NSE closing window.

## 4. Statistics: how they are calculated
- **Standardised return z** = ret / (sample std of that stock's returns in the same 5-minute slot). Not de-meaned. It uses the whole sample, so it is descriptive only.
- **Confidence interval** for the mean return in a slot: mean ± t(0.975, n−1) × sd/√n, treating each day's value as independent. It ignores autocorrelation and changing volatility, and slots with fewer than 5 observations are left blank. With ~71–77 slots per stock, about 5% of intervals are expected to exclude 0 by chance.
- **Tail event**: |z| > 3. A normal distribution would give 2×(1−Φ(3)) = 0.27% of observations.
- **Volatility** = sample standard deviation (ddof = 1) of 5-minute log returns; period values pool all returns in the period.
- **Outliers** are never removed. The ten largest |z| moves per stock are listed with timestamps in `largest_moves.csv`. Their causes are **unknown**; no earnings or news explanation has been verified or assumed.

## 5. What the data shows (descriptive)
**Return distributions.** Mean 5-minute returns are essentially zero (within ±0.4 bps). Standard deviations (bps): RELIANCE 11.6, AAPL 12.5, MSFT 13.5, INFY 15.2, NVDA 15.3, TCS 16.4. All six have fat tails: excess kurtosis 4.6–13 (TCS 39), and 0.9–1.4% of observations beyond 3 z, i.e. 3.4–5.3 times the normal-curve share. Skew is small (TCS +1.27 and INFY +0.69 are the largest).

**Mean return by time of day.** Per stock, 2–5 of 71–77 slots have a confidence interval excluding zero, versus about 3.5–3.9 expected by chance. This gives no evidence of a time-of-day drift in this sample. With about 59 observations per slot, the intervals are wide.

**Volatility by period** (std of 5-minute returns, bps):
| | open | middle | close |
|---|---|---|---|
| RELIANCE | 18.3 | 10.3 | 11.6 |
| TCS | 27.2 | 13.2 | 20.5 |
| INFY | 27.2 | 12.3 | 15.6 |
| AAPL | 20.6 | 10.7 | 9.9 |
| MSFT | 25.4 | 10.3 | 9.9 |
| NVDA | 25.5 | 12.8 | 13.3 |
Volatility is highest in the opening period for all six stocks, roughly 1.5–2.5 times the middle of the day. The NSE closing period is also above its middle for all three stocks, while the US close is at or slightly below the middle for AAPL and MSFT. NSE close values exclude 15:15–15:25.

**Opening candle (open-to-close).** Std 46–98 bps, several times a typical 5-minute bar. Means are noisy (n=60 each) and not distinguishable from zero here.

**Volume.** Both markets are U-shaped through the session, relative to each stock's typical slot. US volume in the 09:30 bar is about 10.6 times typical, and about 7.3 times at 15:55. The first reliable NSE bar (09:20) is about 2.8 times typical, and 15:10 about 4.4 times, but NSE's own 09:15 bar is excluded, so its opening peak is not measured. Volume shape comparisons across the two markets are qualitative only.

**NSE vs US (shape only).** Both markets show elevated volatility at the open (relative to typical: about 2.8 at 09:20 for NSE and 3.3 at 09:35 for US) that settles to a flat middle. The US market's close is mildly elevated (about 1.5); NSE's last reliable slot (15:10) is about 2.3, driven mostly by TCS and INFY and in part by one TCS move on 2026-08-31 (+2.97%), cause unknown. Absolute levels and the effects of different tick sizes, price levels and volume definitions are not compared.

**Data quality.** Missing-data patterns are concentrated at the end of the NSE session and at 09:15 volume; US data is clean apart from a handful of zero-volume bars and one 16:00 bar. The off-grid last bar of the partial NSE day appears as a one-day column in the heatmap.

## 6. What this does and does not tell us
- It describes how a small sample behaved. It does **not** show that any pattern persists, is statistically significant after multiple-testing correction, or survives transaction costs.
- Hypotheses H1–H3 remain untested. These plots may motivate formal tests later, on more data.
- Findings for the NSE opening candle's volume and the closing window are limited by the data feed, not the market.

## 7. Files
`outputs/milestone3/`: 15 CSV tables (including `snapshots.csv`, `exclusions.csv`, `largest_moves.csv`) and 11 Plotly HTML charts (01 distributions, 02 Q-Q, 03 mean return, 04 volatility, 05 volume, 06 NSE vs US, 07 data quality), plus `plotly.min.js` shared by the charts.
