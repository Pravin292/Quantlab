"""Read-only probe of Yahoo Finance's public chart endpoint (what yfinance wraps). Stdlib + pandas only."""
import json, sys, urllib.request, urllib.error
import pandas as pd

OUT = "/private/tmp/claude-501/-Users-pravin-Quantlab-/8e530746-918a-43df-9ac2-b50b52ab0120/scratchpad/"
TICKERS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "AAPL", "MSFT", "NVDA"]

def fetch(sym, interval, rng):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval={interval}&range={rng}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:300]}
    except Exception as e:
        return None, {"error": repr(e)}

for rng in ["60d", "1y"]:
    for s in TICKERS:
        status, d = fetch(s, "5m", rng)
        res = (d.get("chart") or {}).get("result")
        if not res:
            print(rng, s, "FAILED", status, str(d)[:250]); continue
        r = res[0]
        q = r["indicators"]["quote"][0]
        df = pd.DataFrame(q, index=pd.to_datetime(r["timestamp"], unit="s", utc=True))
        tz = r["meta"]["exchangeTimezoneName"]
        df.index = df.index.tz_convert(tz)
        df.to_csv(f"{OUT}{s}_5m_{rng}.csv")
        print(rng, s, status, "rows", len(df), df.index.min(), "->", df.index.max(), "tz", tz)
