"""M4a: calibration (false-positive rate) and power simulations.

ALL DATA HERE IS SIMULATED. No real market data is read. The simulator pushes
synthetic bars through the real clean() and build_bar_table() code, so the
research functions are exercised exactly as they will be on real data.

Outputs (new folder, never overwritten): outputs/milestone4/calibration/
Usage:  python scripts/milestone4/run_calibration.py [--quick]
"""
import argparse
import platform
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from quantlab.calendars import NSE, US                          # noqa: E402
from quantlab.research import h1_volatility as h1               # noqa: E402
from quantlab.research import h2_volume as h2                   # noqa: E402
from quantlab.research import h3_serial as h3                   # noqa: E402
from quantlab.research.nulls import simulate_table              # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "calibration"
MASTER_SEED = 20261030
ALPHA = 0.05
N_STOCKS = 3
N_DAYS = 59
MARKETS = {"NSE": NSE, "US": US}


# ----------------------------------------------------------------- H3
def h3_one(args):
    seed, market, rho, quirks = args
    rng = np.random.default_rng(seed)
    kw = dict(rho=rho, df=4, day_vol_sd=0.3, vol_edge_boost=1.0, nse_feed_quirks=quirks)
    tabs = [simulate_table(MARKETS[market], f"S{i}", N_DAYS, rng, **kw) for i in range(N_STOCKS)]
    res = h3.omnibus_autocorr([h3.zscore_matrix(t) for t in tabs])
    return {"p": res["p"], "rho1": res["rho"][0], "rho2": res["rho"][1]}


# ----------------------------------------------------------------- H1
def h1_one(args):
    seed, market, open_mult, close_mult = args
    rng = np.random.default_rng(seed)
    mult = {"open": open_mult, "close": close_mult}
    tabs = [simulate_table(MARKETS[market], f"S{i}", N_DAYS, rng, df=4, day_vol_sd=0.3, period_mult=mult,
                           nse_feed_quirks=(market == "NSE")) for i in range(N_STOCKS)]
    panel = h1.market_panel([h1.period_panel(t, market) for t in tabs])
    return {"p": h1.omnibus(panel)["p"]}


# ----------------------------------------------------------------- H2
def h2_one(args):
    seed, market, loading, fwd_mult, cont, wild_B, day_fe = args
    rng = np.random.default_rng(seed)
    kw = dict(day_vol_sd=0.3, volume_day_loading=loading, fwd_vol_mult=fwd_mult, continuation=cont,
              nse_feed_quirks=(market == "NSE"))
    tabs = [simulate_table(MARKETS[market], f"S{i}", N_DAYS, rng, **kw) for i in range(N_STOCKS)]
    feat = pd.concat([h2.outcome_features(t) for t in tabs])
    ret = h2.event_regression(feat, "g_open", wild_B, rng, day_fe=day_fe)
    vol = h2.event_regression(feat, "y_fv_open", wild_B, rng, day_fe=day_fe)
    return {"p_ret": ret["p_wild"], "p_vol": vol["p_wild"], "p_ret_cr1": ret["p_cr1"], "p_vol_cr1": vol["p_cr1"],
            "beta_ret": ret["beta"], "beta_vol": vol["beta"], "n_events": ret["n_events"],
            "n_event_days": ret["n_event_days"], "adequacy": ret["adequacy"]}


def run(pool, fn, jobs):
    return pd.DataFrame(list(pool.map(fn, jobs, chunksize=2)))


def rate(p):
    p = np.asarray(p, float)
    r = float(np.mean(p < ALPHA))
    return r, float(np.sqrt(r * (1 - r) / len(p)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="few simulations, only to check the plumbing")
    a = ap.parse_args()
    n3, n1, n2, nw = (20, 40, 12, 49) if a.quick else (400, 600, 150, 199)
    n_pow = 10 if a.quick else 100
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files; move them yourself first (outputs are never overwritten).")
    OUT.mkdir(parents=True, exist_ok=True)
    ss = np.random.SeedSequence(MASTER_SEED)
    seeds = iter(ss.spawn(100000))
    nxt = lambda: int(next(seeds).generate_state(1)[0])
    rows_size, rows_power, rows_bias = [], [], []

    with ProcessPoolExecutor() as pool:
        # ---- H3 size + estimator bias
        for mk in ["NSE", "US"]:
            for rho in [-0.10, -0.05, 0.0, 0.05, 0.10]:
                d = run(pool, h3_one, [(nxt(), mk, rho, mk == "NSE") for _ in range(n3)])
                r, se = rate(d["p"])
                rows_bias.append({"market": mk, "true_rho1": rho, "mean_est_rho1": d["rho1"].mean(),
                                  "sd_est_rho1": d["rho1"].std(), "mean_est_rho2": d["rho2"].mean(),
                                  "true_rho2": rho ** 2, "n_sims": n3})
                (rows_size if rho == 0 else rows_power).append(
                    {"test": "H3 clustered Wald (lags 1-6)", "market": mk, "setting": f"rho1={rho}",
                     "rejection_rate": r, "mc_se": se, "n_sims": n3})
        # ---- H1 size + power
        for mk in ["NSE", "US"]:
            for om, cm in [(1.0, 1.0), (1.05, 1.05), (1.10, 1.10), (1.20, 1.20), (1.50, 1.50)]:
                d = run(pool, h1_one, [(nxt(), mk, om, cm) for _ in range(n1)])
                r, se = rate(d["p"])
                (rows_size if om == 1.0 else rows_power).append(
                    {"test": "H1 Friedman", "market": mk, "setting": f"open/close vol x{om}",
                     "rejection_rate": r, "mc_se": se, "n_sims": n1})
        # ---- H2 size (two nulls) and power
        for mk in ["US", "NSE"]:
            for loading, day_fe in [(0.0, True), (0.8, True), (0.8, False)]:
                d = run(pool, h2_one, [(nxt(), mk, loading, 1.0, 0.0, nw, day_fe) for _ in range(n2)])
                for t, col in [("H2 return continuation", "p_ret"), ("H2 forward volatility", "p_vol")]:
                    r, se = rate(d[col]); r2, _ = rate(d[col.replace("p_", "p_") + "_cr1"])
                    rows_size.append({"test": t, "market": mk, "setting": f"null, volume-day-loading={loading}, day fixed effects={day_fe}",
                                      "rejection_rate": r, "mc_se": se, "rejection_rate_cr1_t": r2, "n_sims": n2,
                                      "median_events": float(d["n_events"].median()),
                                      "share_underpowered": float((d["adequacy"] != "ADEQUATE").mean())})
            for fwd in [1.10, 1.25, 1.50]:
                d = run(pool, h2_one, [(nxt(), mk, 0.0, fwd, 0.0, nw, True) for _ in range(n_pow)])
                r, se = rate(d["p_vol"])
                rows_power.append({"test": "H2 forward volatility", "market": mk,
                                   "setting": f"true forward-vol multiplier x{fwd}",
                                   "rejection_rate": r, "mc_se": se, "n_sims": n_pow,
                                   "mean_beta": d["beta_vol"].mean()})
            for cont in [0.05, 0.10, 0.20]:
                d = run(pool, h2_one, [(nxt(), mk, 0.0, 1.0, cont, nw, True) for _ in range(n_pow)])
                r, se = rate(d["p_ret"])
                rows_power.append({"test": "H2 return continuation", "market": mk,
                                   "setting": f"true drift {cont} vol-units/bar for 3 bars",
                                   "rejection_rate": r, "mc_se": se, "n_sims": n_pow,
                                   "mean_beta_bps": d["beta_ret"].mean() * 1e4})

    pd.DataFrame(rows_size).to_csv(OUT / "size_false_positive_rates.csv", index=False)
    pd.DataFrame(rows_power).to_csv(OUT / "power.csv", index=False)
    pd.DataFrame(rows_bias).to_csv(OUT / "h3_estimator_bias.csv", index=False)
    meta = {"master_seed": MASTER_SEED, "alpha": ALPHA, "n_days": N_DAYS, "stocks_per_market": N_STOCKS,
            "quick_mode": a.quick, "python": platform.python_version(), "numpy": np.__version__,
            "note": "ALL DATA SIMULATED; no market data was read."}
    pd.Series(meta).to_csv(OUT / "run_metadata.csv", header=["value"])
    print(pd.DataFrame(rows_size).round(3).to_string(index=False))
    print(pd.DataFrame(rows_power).round(3).to_string(index=False))
    print(pd.DataFrame(rows_bias).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
