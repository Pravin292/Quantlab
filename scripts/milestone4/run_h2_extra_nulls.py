"""M4a H2 EXTRA TRUE-NULL SIMULATIONS to tighten NSE (and US world A) calibration precision.  ALL SIMULATED.

Same DGPs, models and estimators as run_diagnostics_h2.py (worlds A and F: volume independent of
returns = TRUE NULL), new master seed, more simulations, only the three models that matter:
  M0 original (c1 c2) | M5 primary candidate (c1 c2 c3 c4) | DFE (exploratory same-day effects)
Wild-cluster-bootstrap p-values for M5 and DFE (B=199). Per-simulation p-values and seeds are saved.
Output folder (new): outputs/milestone4/diagnostics/h2_extra/
Usage: python scripts/milestone4/run_h2_extra_nulls.py [--quick]
"""
import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from quantlab.calendars import NSE, US                       # noqa: E402
from quantlab.research import h2_volume as h2                # noqa: E402
from quantlab.research.nulls import simulate_table           # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "diagnostics" / "h2_extra"
MASTER_SEED = 20261041
MARKETS = {"NSE": NSE, "US": US}
N_DAYS, N_STOCKS, ALPHA = 59, 3, 0.05
WORLDS = {"A day factor in returns, volume independent": dict(day_vol_sd=0.3),
          "F day factor + intraday regime in returns, volume independent": dict(day_vol_sd=0.3, intraday_regime_sd=0.25)}
MODELS = {"M0 original (c1 c2)": (False, ("c1", "c2"), False),
          "M5 + c3 + c4 [primary candidate]": (False, ("c1", "c2", "c3", "c4"), True),
          "DFE day effects + c3 (within-day question)": (True, ("c1", "c2", "c3"), True)}


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def one(args):
    seed, market, kw, wild_B = args
    rng = np.random.default_rng(seed)
    tabs = [simulate_table(MARKETS[market], f"S{i}", N_DAYS, rng, nse_feed_quirks=(market == "NSE"), **kw)
            for i in range(N_STOCKS)]
    feat = pd.concat([h2.outcome_features(t) for t in tabs])
    out = {"seed": seed}
    for mname, (fe, controls, wild) in MODELS.items():
        for oname, col in (("vol", "y_fv_open"), ("ret", "g_open")):
            r = h2.event_regression(feat, col, wild_B if wild else 0, rng, day_fe=fe, controls=controls)
            out[f"{mname}|{oname}|p"] = r["p_cr1"]
            if wild and wild_B:
                out[f"{mname}|{oname}|p_wild"] = r["p_wild"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    n_nse, n_us, wild = (4, 4, 29) if a.quick else (800, 500, 199)
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files; move them yourself first.")
    OUT.mkdir(parents=True, exist_ok=True)
    seeds = iter(np.random.SeedSequence(MASTER_SEED).spawn(100000))
    nxt = lambda: int(next(seeds).generate_state(1)[0])
    rows, sims = [], []
    with ProcessPoolExecutor() as pool:
        for mk, n in (("NSE", n_nse), ("US", n_us)):
            for wname, kw in WORLDS.items():
                res = pd.DataFrame(list(pool.map(one, [(nxt(), mk, kw, wild) for _ in range(n)], chunksize=2)))
                res.insert(0, "world", wname); res.insert(1, "market", mk)
                sims.append(res)
                for col in [c for c in res.columns if c.endswith("|p") or c.endswith("|p_wild")]:
                    mname, oname, ptype = col.split("|")
                    pv = res[col].dropna()
                    k = int((pv < ALPHA).sum()); lo, hi = wilson(k, len(pv))
                    rows.append({"world": wname, "truth": "TRUE NULL", "market": mk, "model": mname, "outcome": oname,
                                 "p_type": ptype, "n_sims": len(pv), "rejection_rate": k / len(pv),
                                 "ci95_low": lo, "ci95_high": hi})
                print(mk, wname, "done", flush=True)
    pd.DataFrame(rows).to_csv(OUT / "H2_extra_true_null_size.csv", index=False)
    pd.concat(sims).to_csv(OUT / "H2_extra_per_simulation.csv", index=False)
    pd.Series({"master_seed": MASTER_SEED, "quick": a.quick, "n_sims_NSE": n_nse, "n_sims_US": n_us, "wild_B": wild,
               "note": "ALL DATA SIMULATED; independent of the first H2 diagnostic run (different seed)"}).to_csv(
        OUT / "run_metadata.csv", header=["value"])
    print("COMPLETE", flush=True)


if __name__ == "__main__":
    main()
