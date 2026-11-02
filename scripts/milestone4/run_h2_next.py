"""M4a NEXT ROUND, H2.  ALL DATA SIMULATED.

Parts (new folders under outputs/milestone4/next_round/):
  us   Task E  Many more TRUE-NULL replications for the US (worlds A and F: volume independent of returns), models
               M0 (c1 c2), M5 (c1 c2 c3 c4), DFE (exploratory), clustered-t and wild-cluster-bootstrap p-values.
               Saves n_events / n_event_days per simulation to look for a structural reason for US-vs-NSE differences.
  dep  Task B  TRUE-NULL world F with cross-stock correlation and/or day-to-day volatility clustering (NSE and US):
               independent (X0), empirical-parameter dependence (X3), illustrative strong dependence (X4).
SHARED-REGIME worlds are NOT mixed in here (they answer a different question; see docs 09/10).
Usage: python scripts/milestone4/run_h2_next.py --part us|dep [--quick]
"""
import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))

from quantlab.calendars import NSE, US                                 # noqa: E402
from quantlab.research import dependence as dep, h2_volume as h2       # noqa: E402
from quantlab.research.nulls import simulate_table                     # noqa: E402
import run_h1_next as nxt_h1                                           # noqa: E402

OUT_ROOT = ROOT / "outputs" / "milestone4" / "next_round"
SEEDS = {"us": 20261053, "dep": 20261054}
MARKETS = {"NSE": NSE, "US": US}
N_DAYS, N_STOCKS, ALPHA = 59, 3, 0.05
WORLDS = {"A day factor in returns, volume independent": dict(day_vol_sd=0.3),
          "F day factor + intraday regime in returns, volume independent": dict(day_vol_sd=0.3, intraday_regime_sd=0.25)}
MODELS = {"M0 original (c1 c2)": (False, ("c1", "c2"), False),
          "M5 + c3 + c4 [primary candidate]": (False, ("c1", "c2", "c3", "c4"), True),
          "DFE day effects + c3 (within-day question)": (True, ("c1", "c2", "c3"), True)}


def one(args):
    seed, market, kw, dcfg, wild_B = args
    rng = np.random.default_rng(seed)
    if dcfg is None:
        tabs = [simulate_table(MARKETS[market], f"S{i}", N_DAYS, rng, nse_feed_quirks=(market == "NSE"), **kw)
                for i in range(N_STOCKS)]
    else:
        tabs = dep.simulate_market_tables(
            MARKETS[market], N_STOCKS, N_DAYS, rng, day_share=dcfg["share"], day_phi=dcfg["phi"],
            ret_corr=dep.core_corr_for_pearson(dcfg["ret_corr"], 4.0) if dcfg["ret_corr"] > 0 else 0.0,
            nse_feed_quirks=(market == "NSE"), **kw)
    feat = pd.concat([h2.outcome_features(t) for t in tabs])
    out = {"seed": seed}
    for mname, (fe, controls, wild) in MODELS.items():
        for oname, col in (("vol", "y_fv_open"), ("ret", "g_open")):
            r = h2.event_regression(feat, col, wild_B if wild else 0, rng, day_fe=fe, controls=controls)
            out[f"{mname}|{oname}|p"] = r["p_cr1"]
            if wild and wild_B:
                out[f"{mname}|{oname}|p_wild"] = r["p_wild"]
            if mname.startswith("M5") and oname == "vol":
                out["n_events"], out["n_event_days"] = r["n_events"], r["n_event_days"]
    return out


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True, choices=["us", "dep"])
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
    jobs = []                                              # (label, market, world kw, dependence cfg, n)
    if a.part == "us":
        n = 4 if q else 1500
        jobs = [(w, "US", kw, None, n, "independent") for w, kw in WORLDS.items()]
    else:
        n = 4 if q else 500
        wF = "F day factor + intraday regime in returns, volume independent"
        for mk in ("NSE", "US"):
            e = nxt_h1.EMP_DEP[mk]
            for lab, cfg in (("X0 independent", dict(ret_corr=0, share=0, phi=0)),
                             ("X3 empirical-parameter dependence", e),
                             ("X4 illustrative strong dependence", nxt_h1.ILLUSTRATIVE_DEP)):
                jobs.append((wF, mk, WORLDS[wF], cfg, n, lab))
    rows, sims = [], []
    with ProcessPoolExecutor() as pool:
        for world, mk, kw, cfg, n, lab in jobs:
            res = pd.DataFrame(list(pool.map(one, [(nxt(), mk, kw, cfg, wild) for _ in range(n)], chunksize=2)))
            res.insert(0, "world", world); res.insert(1, "market", mk); res.insert(2, "dependence", lab)
            sims.append(res)
            for col in [c for c in res.columns if c.endswith("|p") or c.endswith("|p_wild")]:
                mname, oname, ptype = col.split("|")
                pv = res[col].dropna()
                k = int((pv < ALPHA).sum()); lo, hi = wilson(k, len(pv))
                rows.append({"world": world, "truth": "TRUE NULL", "market": mk, "dependence": lab, "model": mname,
                             "outcome": oname, "p_type": ptype, "n_sims": len(pv), "rejection_rate": k / len(pv),
                             "ci95_low": lo, "ci95_high": hi, "mc_se": float(np.sqrt(k / len(pv) * (1 - k / len(pv)) / len(pv)))})
            print(mk, world, lab, "done", flush=True)
    pd.DataFrame(rows).to_csv(out / f"h2_{a.part}_true_null_size.csv", index=False)
    pd.concat(sims).to_csv(out / f"h2_{a.part}_per_simulation.csv", index=False)
    pd.Series({"master_seed": SEEDS[a.part], "quick": q, "n_sims_per_cell": n, "wild_B": wild,
               "dependence_params": str(nxt_h1.EMP_DEP) + " | illustrative " + str(nxt_h1.ILLUSTRATIVE_DEP),
               "note": "ALL DATA SIMULATED; TRUE-NULL worlds only"}).to_csv(out / "run_metadata.csv", header=["value"])
    print("COMPLETE", flush=True)


if __name__ == "__main__":
    main()
