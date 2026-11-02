import json, urllib.request, pandas as pd
D="./"
def pull(s):
    url=f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?interval=5m&range=60d"
    r=json.load(urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=30))["chart"]["result"][0]
    return pd.DataFrame(r["indicators"]["quote"][0],index=pd.to_datetime(r["timestamp"],unit="s",utc=True).tz_convert("Asia/Kolkata"))
for s in ["INFY.NS","RELIANCE.NS"]:
    old=pd.read_csv(f"{s}_5m_60d.csv",index_col=0); old.index=pd.to_datetime(old.index,utc=True).tz_convert("Asia/Kolkata")
    new=pull(s); c=old.dropna().index.intersection(new.dropna().index)
    cols=["open","high","low","close","volume"]; m=(old.loc[c,cols]!=new.loc[c,cols])
    print(s,"changed by column:",m.sum().to_dict(),"| by date:",pd.Series(c[m.any(axis=1)].date).value_counts().sort_index().head(8).to_dict())
    ch=c[m.any(axis=1)][:3]; print(pd.concat([old.loc[ch,cols],new.loc[ch,cols]],axis=1,keys=["old","new"]).to_string())
