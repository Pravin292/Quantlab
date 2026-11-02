# Milestone 1 — Data Availability Report

Date of probe: 2026-10-30. All numbers below come from real pulls (scripts in `scripts/milestone1/`). Nothing is estimated unless marked **[unverified]**.

## 1. Environment (read-only inspection, nothing modified)

| Item | Finding |
|---|---|
| Default `python3` | 3.14.7 (Homebrew). Has pandas 3.0.5, numpy 2.5.1, scipy 1.18.0, matplotlib 3.11.1. **No** statsmodels, plotly, streamlit, yfinance, requests, pytest |
| Other Pythons | 3.12 (Homebrew), 3.9.6 (system). A 3.9 user site has pandas 2.3.3, plotly, streamlit, pytest, scipy 1.13.1, requests; also no statsmodels or yfinance |
| Virtual envs | None found in `~/Quantlab`; no conda/pyenv/uv |
| PostgreSQL | 16.15 installed and accepting connections on port 5432 |
| Git | /usr/bin/git present. `~/Quantlab` is not yet a repository |

Implication: packages are split across two Python versions. Before coding we should create one project virtual environment (needs your approval to install).

## 2. Free source tested: Yahoo Finance chart endpoint (the one yfinance uses)

I called the public endpoint directly (standard library only), so nothing was installed. Note: Yahoo's terms restrict this data to personal use. It is unofficial and can change or block without notice.

### Access: all six stocks work

| Market | Ticker | 5-min rows | Range returned |
|---|---|---|---|
| India | RELIANCE.NS | 4,444 | 2026-08-05 → 2026-10-30 |
| India | TCS.NS | 4,444 | same |
| India | INFY.NS | 4,444 | same |
| US | AAPL | 4,681 | 2026-08-06 → 2026-10-29 |
| US | MSFT | 4,681 | same |
| US | NVDA | 4,681 | same |

### Historical depth: the main limitation

Requesting 1 year of 5-minute data failed for **all six** with HTTP 422: *"The requested range must be within the last 60 days."* So free 5-minute depth is **about 60 calendar days (~60 trading days, ~4,500 bars per stock)**. This is the same for India and the US.

Consequences:
- ~60 days is too short for a trustworthy train/validation/test split (e.g. 36/12/12 days) or for strategy evaluation across different market regimes.
- Descriptive work (H1 time-of-day volatility) is feasible but weak; strategy conclusions would not be reliable.
- The window rolls forward. To build history we would have to **collect and store data ourselves every few weeks**; anything we miss is lost.

### Quality checks

**India (NSE, 09:15–15:30 IST, expected 75 bars/day)**
- 59 full days of 75 bars, plus today's partial session (19 bars). Today's last bar is still forming, so it must be excluded.
- Timestamps are complete (no missing slots), but **~2.5% of bars are empty placeholders** (NaN prices and volume): 113 for RELIANCE, 123 for TCS, 119 for INFY. They appear at about 11:45–11:50 and 15:15–15:25, typically 1–3 per day, and more often recently. These are data gaps hidden inside valid timestamps. The probe also shows ~61–63 zero-volume bars per stock, mostly the 09:15 opening bar on 58 days, which looks suspicious and needs checking before we trust opening-bar volume.
- Holidays visible as gaps: 2026-09-15 and 2026-10-05 (+4-day gaps) and 2026-10-21. **[Not yet cross-checked against the official NSE holiday list.]**
- Liquidity (mean daily volume, shares): RELIANCE ≈12.1M, TCS ≈3.6M, INFY ≈10.5M. All are very liquid.

**US (NYSE/Nasdaq, 09:30–16:00 ET, expected 78 bars/day)**
- 59 days of 78 bars, 1 day with 79. The extra 16:00 bar is a zero-volume copy of the last price, an artifact to drop.
- **No NaN prices**; only 1–4 zero-volume bars per stock.
- One holiday gap, 2026-09-08 (after Labor Day, 2026-09-07), is as expected.
- Mean daily volume: AAPL ≈29.4M, MSFT ≈15.8M, NVDA ≈89.2M. All very liquid.
- Early-close days (e.g. day after Thanksgiving) were not in this window, so that handling is untested.

**Both:** no duplicate timestamps and no OHLC logic violations (high < max(open, close), etc.) were found.

### Other things we have not verified
- Whether prices are split/dividend adjusted. Intraday Yahoo bars are generally unadjusted, and a corporate action inside the window would show as a fake jump. **[Unverified.]**
- Whether Yahoo's volume matches exchange-consolidated volume. For US stocks it is typically composite, but this is unverified here.
- Whether the NaN placeholders vary run to run (the same request could give different gaps tomorrow).

## 3. Other options (status)

| Option | Market | Cost | Status |
|---|---|---|---|
| Broker APIs, e.g. Zerodha Kite Connect (needs an account), Angel One SmartAPI, Upstox, Fyers | India | Some are free with a funded broker account. Kite Connect historical data was a paid add-on **[unverified; check current price]** | **Not tested**: needs your account and credentials. Intraday depth is typically many months to years, which would solve our depth problem |
| Alpaca (free tier) | US | Free tier with delayed/IEX-only data **[unverified]** | Not tested: needs sign-up and keys. IEX volume is only a fraction of total volume, which would distort H2 |
| Polygon.io, Databento, Alpha Vantage, Twelve Data | US | Free tiers have tight rate and history limits; paid tiers vary **[unverified]** | Not tested; would need current pricing and terms |
| NSE bhavcopy / official exports | India | Free | Daily data only, not intraday |

I have **not** tested these. Their depth, price and licence terms must be confirmed against each vendor's current page before we decide. I did not purchase or sign up for anything.

## 4. Licensing and usage
- Yahoo data: personal, non-commercial research use only; redistribution and republishing are not allowed. Fine for private learning, not for a product.
- Broker data usually forbids redistribution and may require the account's terms to be followed. **[Read each vendor's terms before use.]**

## 5. Conclusion
- **All six stocks are accessible and liquid.** None needs to be dropped on data or liquidity grounds.
- **Free data supports about 60 trading days only.** That is enough to *prototype* the data pipeline and run exploratory H1/H2 statistics. It is **not** enough to make any claim about strategy performance.
- Recommended path (your decision): (a) start collecting and storing Yahoo 5-minute data now, since it costs nothing and builds history; (b) in parallel, check a free broker API for India and for the US, and compare paid options with verified prices.
