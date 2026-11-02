"""M4b, H2 POWER and SAMPLE-SIZE sensitivity for the leading model M5 (c1 c2 c3 c4) with wild-cluster-bootstrap p-values.
ALL DATA SIMULATED.  Predictive information beyond past controls is the quantity tested; NOT a causal effect of volume.

How effects are injected (src/quantlab/research/nulls.simulate_raw): the baseline world is world F (day factor + intraday
volatility regime in returns; volume independent of everything). After every bar whose volume is >= 2x its past-only baseline
(an "event"), for the next k=3 bars
  fwd_vol_mult = m   multiplies the bar volatility by m        (m>1 raises, m<1 lowers volatility after high volume)
  continuation = c   adds a drift of c volatility-units in the direction of the event candle's return
                     (c>0 momentum after high volume, c<0 reversal)
These are KNOWN effects planted in synthetic data; they are not observed market relationships.
Outcome tested: forward volatility (y_fv_open) for volatility effects, return continuation (g_open) for drift effects; each effect
is also tested on the other outcome as a NEGATIVE CONTROL (should reject at about the nominal rate).
Dependence: X0 independent stocks / X3 estimated cross-stock correlation + day-volatility persistence (see doc 11).
Parts: p59 (59 days, all effects, X0 and X3); pbig (125 and 250 days, X3, subset of effects).
Usage: python scripts/milestone4/run_h2_power.py --part p59|pbig [--quick]
"""
import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))

from quantlab.calendars import NSE, US                                  # noqa: E402
from quantlab.research import dependence as dep, h2_volume as h2        # noqa: E402
import run_h1_next as nx                                                # noqa: E402

OUT_ROOT = ROOT / "outputs" / "milestone4" / "m4b"
SEEDS = {"p59": 20261080, "pbig": 20261081}
MARKETS = {"NSE": NSE, "US": US}
ALPHA, N_STOCKS = 0.05, 3
EFFECTS = {"null": dict(), "vol x0.90": dict(fwd_vol_mult=0.90), "vol x1.05": dict(fwd_vol_mult=1.05),
           "vol x1.10": dict(fwd_vol_mult=1.10), "vol x1.25": dict(fwd_vol_mult=1.25),
           "cont -0.10": dict(continuation=-0.10), "cont -0.05": dict(continuation=-0.05), "cont -0.02": dict(continuation=-0.02),
           "cont +0.02": dict(continuation=0.02), "cont +0.05": dict(continuation=0.05), "cont +0.10": dict(continuation=0.10)}
CONTROLS = ("c1", "c2", "c3", "c4")


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def one(args):
    seed, mk, dcfg, eff, n_days, wild_B = args
    rng = np.random.default_rng(seed)
    tabs = dep.simulate_market_tables(
        MARKETS[mk], N_STOCKS, n_days, rng, day_vol_sd=0.3, day_share=dcfg["share"], day_phi=dcfg["phi"],
        ret_corr=dep.core_corr_for_pearson(dcfg["ret_corr"], 4.0) if dcfg["ret_corr"] > 0 else 0.0,
        intraday_regime_sd=0.25, df=4.0, nse_feed_quirks=(mk == "NSE"), **eff)
    feat = pd.concat([h2.outcome_features(t) for t in tabs])
    out = {"seed": seed}
    for oname, col in (("vol", "y_fv_open"), ("ret", "g_open")):
        r = h2.event_regression(feat, col, wild_B, rng, day_fe=False, controls=CONTROLS)
        out[f"{oname}|p_wild"], out[f"{oname}|p_t"], out[f"{oname}|beta"] = r["p_wild"], r["p_cr1"], r["beta"]
        out["n_events"], out["n_event_days"] = r["n_events"], r["n_event_days"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True, choices=list(SEEDS))
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    q = a.quick
    out = OUT_ROOT / f"h2_{a.part}"
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} already has files.")
    out.mkdir(parents=True, exist_ok=True)
    wild = 29 if q else 199
    seeds = iter(np.random.SeedSequence(SEEDS[a.part]).spawn(200000))
    nxt = lambda: int(next(seeds).generate_state(1)[0])
    jobs = []                                              # (market, dep label, dep cfg, effect, n_days, n)
    zero = dict(ret_corr=0.0, share=0.0, phi=0.0)
    for mk in ("NSE", "US"):
        e = nx.EMP_DEP[mk]
        if a.part == "p59":
            n = 3 if q else 120
            for lab, cfg in (("X0 independent", zero), ("X3 estimated dependence", e)):
                jobs += [(mk, lab, cfg, en, 59, n) for en in EFFECTS]
        else:
            n = 3 if q else 80
            for nd in (125, 250):
                jobs += [(mk, "X3 estimated dependence", e, en, nd, n) for en in ("null", "vol x1.05", "vol x1.10", "cont +0.02", "cont +0.05")]
    rows, sims = [], []
    t0 = time.time()
    with ProcessPoolExecutor() as pool:
        for mk, lab, cfg, en, nd, n in jobs:
            res = pd.DataFrame(list(pool.map(one, [(nxt(), mk, cfg, EFFECTS[en], nd, wild) for _ in range(n)], chunksize=2)))
            res.insert(0, "market", mk); res.insert(1, "dependence", lab); res.insert(2, "effect", en); res.insert(3, "n_days", nd)
            sims.append(res)
            for oname in ("vol", "ret"):
                for pt in ("p_wild", "p_t"):
                    pv = res[f"{oname}|{pt}"].dropna()
                    k = int((pv < ALPHA).sum()); lo, hi = wilson(k, len(pv))
                    role = ("TARGET outcome" if (en.startswith("vol") and oname == "vol") or (en.startswith("cont") and oname == "ret")
                            else ("NULL-WORLD size" if en == "null" else "NEGATIVE CONTROL outcome"))
                    rows.append({"market": mk, "dependence": lab, "effect": en, "n_days": nd, "outcome": oname, "p_type": pt,
                                 "role": role, "n_sims": len(pv), "rejection_rate": k / len(pv), "ci95_low": lo, "ci95_high": hi,
                                 "mean_beta": res[f"{oname}|beta"].mean() * (1e4 if oname == "ret" else 1.0),
                                 "median_events": res["n_events"].median()})
            print(mk, lab, en, nd, f"done {time.time() - t0:.0f}s", flush=True)
    pd.DataFrame(rows).to_csv(out / f"h2_{a.part}_power.csv", index=False)
    pd.concat(sims).to_parquet(out / f"h2_{a.part}_per_simulation.parquet", index=False)
    pd.Series({"master_seed": SEEDS[a.part], "quick": q, "wild_B": wild, "stocks_per_market": N_STOCKS,
               "dependence_params": str(nx.EMP_DEP), "note": "ALL DATA SIMULATED; planted effects, not market relationships"}).to_csv(
        out / "run_metadata.csv", header=["value"])
    print("COMPLETE", flush=True)


if __name__ == "__main__":
    main()
