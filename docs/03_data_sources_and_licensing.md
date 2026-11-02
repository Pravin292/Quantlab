# Data Sources and Licensing (research on 2026-10-30)

Sources are listed so each claim can be checked. "Official" = vendor's own page. Everything labelled **third-party** should be verified before relying on it. No accounts were created and nothing was purchased.

## Yahoo Finance (current source)
- Access: free, no key. Verified by direct testing (doc 01): 5-minute bars, about 60 days max.
- Terms: no official Yahoo API documentation exists. The yfinance project states the data is for personal use only and tells users to read [Yahoo's terms](https://policies.yahoo.com/us/en/yahoo/terms/index.htm). [Yahoo's help page](https://help.yahoo.com/kb/SLN2310.html) says users must not redistribute the information. Redistribution and commercial use are not allowed. I did not find Yahoo's current terms text itself in search results, so please read them directly.
- Reliability: unofficial endpoint (can break), data revised between pulls, NSE closing-bar gaps (doc 04).
- Verdict: acceptable for private learning only; not a basis for long-term research.

## India

| Source | Cost | 5-min depth | Restrictions | Needs |
|---|---|---|---|---|
| Zerodha Kite Connect ([official FAQ](https://support.zerodha.com/category/trading-and-markets/general-kite/kite-api/articles/historical-data-and-live-market-data-payment-plan)) | Free Personal plan has **no** historical data. Paid Connect plan **₹500/month** includes historical and live data | Official [docs](https://kite.trade/docs/connect/v3/historical/) support `5minute` but state no per-request or depth limit. A third-party post says 100 days per request (unverified). Depth in total: not stated | Rate limit not stated on the docs page (third-party says 3/s, unverified). Licence for storing/redistributing: not checked | Zerodha account |
| Upstox API ([official](https://upstox.com/developer/api-documentation/v3/get-historical-candle-data/)) | Page states no price; not verified whether free | Minute intervals 1–15: up to 1 month per request, data from **January 2022** | Rate limits and licence not on that page | Upstox account and token |
| Angel One SmartAPI ([docs](https://smartapi.angelbroking.com/docs)) | Not verified | Third-party reports conflict: 100 days, 60 days or 500 candles per request | Unverified | Angel One account |
| Fyers, Dhan | Not researched yet | | | |
| NSE official | Free | Daily bhavcopy only; no free 5-minute history | | |

India summary: the only item I could confirm from official pages is Zerodha's ₹500/month, and Upstox's depth back to Jan 2022. Whether Upstox's API is free to all account holders, and what each broker's licence allows for storing data, is **not verified**. Depth of 3+ years at 5-minute would need chunked requests.

## United States

| Source | Cost | 5-min depth | Restrictions |
|---|---|---|---|
| Alpaca Basic ([official](https://docs.alpaca.markets/us/docs/about-market-data-api)) | Free; Algo Trader Plus $99/month | History since 2016; the latest 15 minutes withheld | Basic is **IEX-only** (about 2.5% of US volume per Alpaca's own comparison, per search summary), 200 calls/min. IEX volume would distort H2. Redistribution terms are not stated on that page |
| Polygon.io (now Massive) | Third-party sources: free tier 5 calls/min, about 2 years, Starter $29/month, higher tiers up to $199. Sources disagree whether minute data is in the free tier | About 2 years on free (third-party) | Unverified; check Massive's own pricing page |
| Databento, Twelve Data, Alpha Vantage | Not researched yet | | |

US summary: Alpaca's official page confirms a free tier with deep history, but only IEX volume. Price data from IEX is real, but volume is a small sample of market volume, which matters for H2.

## Assessment (my reading, not a decision)
- No free option checked so far provides both depth (~1 year or more) and full-market US volume.
- Free and plausible: Upstox (India, from 2022, if free for account holders) and Alpaca Basic (US prices, IEX volume). These need your accounts and credentials, which I will not create or enter.
- Cheapest verified paid option for India: Zerodha ₹500/month.
- Before choosing: read each licence for storage, derived-work and redistribution rights.

## Questions for you
1. Do you already hold a broker account with Zerodha, Upstox or Angel One?
2. Is H2 (volume) on US data important enough to justify a paid consolidated feed later?
