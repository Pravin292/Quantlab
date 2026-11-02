import json, urllib.request, pandas as pd, numpy as np
D = "/private/tmp/claude-501/-Users-pravin-Quantlab-/8e530746-918a-43df-9ac2-b50b52ab0120/scratchpad/"
T = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]

def pull(s, interval="5m", rng="60d"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?interval={interval}&range={rng}"
    r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30))["chart"]["result"][0]
    df = pd.DataFrame(r["indicators"]["quote"][0], index=pd.to_datetime(r["timestamp"], unit="s", utc=True).tz_convert("Asia/Kolkata"))
    return df, r["meta"]

def load(s):
    df = pd.read_csv(f"{D}{s}_5m_60d.csv", index_col=0)
    df.index = pd.to_datetime(df.index, utc=True).tz_convert("Asia/Kolkata"); return df

dfs = {s: load(s) for s in T}
for s, df in dfs.items():
    print("=====", s)
    df = df[df.index.date < pd.Timestamp("2026-10-30").date()]  # drop partial today
    nan = df[df.close.isna()]
    z = df[(df.volume == 0)]
    z0915 = z[z.index.strftime("%H:%M") == "09:15"]
    print("zero-vol bars:", len(z), "| at 09:15:", len(z0915), "| other times:", sorted({t.strftime('%H:%M') for t in z.index if t.strftime('%H:%M')!='09:15'}))
    if len(z0915):
        r = z0915
        print("09:15 zero-vol: flat O=H=L=C?", int(((r.open==r.high)&(r.high==r.low)&(r.low==r.close)).sum()), "of", len(r),
              "| dates:", sorted({str(d) for d in r.index.date})[:6], "...")
        nxt = df.shift(-1).loc[r.index]
        print("   next bar (09:20) volume median:", int(nxt.volume.median()), "| typical 09:20 median over all days:", int(df[df.index.strftime('%H:%M')=='09:20'].volume.median()))
        print("   09:15 median volume on days it is NON-zero:", int(df[(df.index.strftime('%H:%M')=='09:15')&(df.volume>0)].volume.median()))
    print("NaN bars time-of-day counts:", nan.index.strftime('%H:%M').value_counts().sort_index().to_dict())
    last = df.groupby(df.index.date).tail(1)
    print("last bar of day: zero/NaN volume:", int((last.volume.fillna(0)==0).sum()), "of", len(last))
    # Do NaN bars share timestamps across tickers?
nanset = {s: set(dfs[s][dfs[s].close.isna()].index) for s in T}
print("\nNaN timestamps shared by all three NSE tickers:", len(set.intersection(*nanset.values())), "| per ticker:", {s: len(v) for s, v in nanset.items()})
print("pairwise Jaccard:", {f"{a[:4]}-{b[:4]}": round(len(nanset[a]&nanset[b])/len(nanset[a]|nanset[b]),2) for i,a in enumerate(T) for b in T[i+1:]})

# Repeat pull: are NaN positions stable?
print("\n--- repeat pull ---")
for s in T:
    new, meta = pull(s)
    old = dfs[s]
    common = old.index.intersection(new.index)
    o_nan = set(old.loc[common][old.loc[common].close.isna()].index); n_nan = set(new.loc[common][new.loc[common].close.isna()].index)
    both = old.loc[common].dropna(); b2 = new.loc[common].dropna()
    cc = both.index.intersection(b2.index)
    diff = (both.loc[cc, ["open","high","low","close","volume"]] != b2.loc[cc, ["open","high","low","close","volume"]]).any(axis=1).sum()
    print(s, "common bars", len(common), "| NaN old", len(o_nan), "new", len(n_nan), "same", len(o_nan & n_nan), "| bars with changed values:", int(diff), "of", len(cc))

# Compare with daily bars (volume cross-check, not official exchange data)
print("\n--- intraday daily sum vs Yahoo daily bar ---")
for s in T:
    d1, _ = pull(s, "1d", "3mo")
    intr = dfs[s][dfs[s].index.date < pd.Timestamp("2026-10-30").date()]
    sums = intr.groupby(intr.index.date).volume.sum()
    d1.index = d1.index.date
    j = pd.concat([sums.rename("intraday"), d1.volume.rename("daily")], axis=1).dropna()
    ratio = (j.intraday / j.daily)
    print(s, "days", len(j), "ratio intraday/daily volume: min %.3f median %.3f max %.3f" % (ratio.min(), ratio.median(), ratio.max()))
