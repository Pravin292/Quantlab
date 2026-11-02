"""Check that the optional dependence hooks added to nulls.simulate_raw do NOT change its output when unused.

Method: rebuild the PRE-EDIT simulate_raw by reverting the three added code fragments in the current source text
(in memory only), run both versions with identical seeds over many option combinations, and compare the raw
bar frames exactly (DataFrame.equals; no tolerance). Writes outputs/milestone4/next_round/verification/.
"""
import sys, types
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from quantlab.calendars import NSE, US                      # noqa: E402
from quantlab.research import nulls as new                  # noqa: E402

src = Path(new.__file__).read_text()
rev = [("                 start: str = \"2026-08-03\",\n                 day_factor: np.ndarray | None = None,\n"
        "                 common_z: np.ndarray | None = None, shock_corr: float = 0.0) -> pd.DataFrame:",
        "                 start: str = \"2026-08-03\") -> pd.DataFrame:"),
       ("    if day_factor is not None:\n        f = np.asarray(day_factor, float)\n", ""),
       ("        if common_z is None:\n            eps = rng.standard_t(df, n) * scale\n        else:\n"
        "            zg = np.sqrt(shock_corr) * common_z[d] + np.sqrt(1 - shock_corr) * rng.standard_normal(n)\n"
        "            eps = zg / np.sqrt(rng.chisquare(df, n) / df) * scale\n",
        "        eps = rng.standard_t(df, n) * scale\n")]
for a, b in rev:
    assert a in src, "fragment not found: " + a[:40]
    src = src.replace(a, b)
old = types.ModuleType("quantlab.research.nulls_old"); old.__package__ = "quantlab.research"
exec(compile(src, "nulls_old", "exec"), old.__dict__)

CONFIGS = [dict(), dict(df=4.0, day_vol_sd=0.3), dict(df=1000.0, day_vol_sd=0.0, rho=0.2),
           dict(df=4.0, intraday_regime_sd=0.25, volume_intraday_loading=0.8, day_vol_sd=0.3, volume_day_loading=0.8),
           dict(vol_edge_boost=1.0, period_mult={"open": 1.8, "close": 1.3}),
           dict(fwd_vol_mult=1.5, continuation=0.1), dict(missing_prob=0.02),
           dict(slot_vol=None, nse_feed_quirks=True), dict(df=6.0, day_vol_sd=0.5, volume_edge_boost=2.0)]
rows = []
for mk in (NSE, US):
    for i, kw in enumerate(CONFIGS):
        for seed in (1, 2, 3):
            kw2 = {k: v for k, v in kw.items() if not (k == "slot_vol" and v is None)}
            a = new.simulate_raw(mk, 6, np.random.default_rng(seed), **kw2)
            b = old.simulate_raw(mk, 6, np.random.default_rng(seed), **kw2)
            rows.append({"market": mk.name, "config": i, "seed": seed, "identical": bool(a.equals(b)), "n_rows": len(a)})
res = pd.DataFrame(rows)
out = ROOT / "outputs" / "milestone4" / "next_round" / "verification" / "simulator_unchanged_check.csv"
res.to_csv(out, index=False)
print(f"{res.identical.sum()} of {len(res)} comparisons identical")
sys.exit(0 if res.identical.all() else 1)
