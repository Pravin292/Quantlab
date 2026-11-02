import pandas as pd, numpy as np
OUT = "/private/tmp/claude-501/-Users-pravin-Quantlab-/8e530746-918a-43df-9ac2-b50b52ab0120/scratchpad/"
for s, exp in [("RELIANCE.NS",75),("TCS.NS",75),("INFY.NS",75),("AAPL",78),("MSFT",78),("NVDA",78)]:
    df = pd.read_csv(f"{OUT}{s}_5m_60d.csv", index_col=0)
    df.index = pd.to_datetime(df.index, utc=True).tz_convert("Asia/Kolkata" if s.endswith(".NS") else "America/New_York")
    print("=====", s)
    print("dup timestamps:", df.index.duplicated().sum(), "| NaN-OHLC rows:", df[["open","high","low","close"]].isna().any(axis=1).sum(),
          "| zero-volume rows:", (df.volume==0).sum(), "| NaN volume:", df.volume.isna().sum())
    ohlc_bad = ((df.high < df[["open","close"]].max(axis=1)) | (df.low > df[["open","close"]].min(axis=1))).sum()
    print("OHLC inconsistent rows:", ohlc_bad)
    g = df.groupby(df.index.date)
    n = g.size()
    print("trading days:", len(n), "| first/last:", n.index[0], n.index[-1])
    print("bars/day value counts (expected %d):" % exp, n.value_counts().to_dict())
    odd = n[n != exp]
    print("days != expected:", {str(k): int(v) for k, v in odd.items()})
    print("first bar time set:", sorted({t.strftime('%H:%M') for t in g.apply(lambda x: x.index.min())}))
    print("last bar time set:", sorted({t.strftime('%H:%M') for t in g.apply(lambda x: x.index.max())}))
    # weekday gaps (calendar-day gaps >3 suggest holidays)
    days = pd.to_datetime(n.index)
    gaps = pd.Series(days[1:] - days[:-1], index=days[1:])
    print("gaps >1 weekday (holiday/missing days):", [str(d.date()) + f"(+{g.days}d)" for d, g in gaps.items() if (np.busday_count(d.date()-g, d.date()) > 1)])
    # within-day missing 5m slots
    miss = 0
    for d, x in g:
        full = pd.date_range(x.index.min(), x.index.max(), freq="5min")
        miss += len(full.difference(x.index))
    print("missing interior 5m slots (between first and last bar of each day):", miss)
    print("median volume per bar:", int(df.volume.median()), "| mean daily volume:", int(g.volume.sum().mean()))
    print("share of bars with volume < 1000:", round((df.volume<1000).mean(),4))
