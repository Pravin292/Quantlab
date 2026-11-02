"""M4a H1 METHODOLOGY COMPARISON for the RMS-volatility estimand.   ALL DATA SIMULATED.

Compares candidate H1 methods on identical simulated markets (same bars for every method):
  orig     Friedman on ln RMS of all bars               (rejected design; reference)
  sub      Friedman on equal-size subsampled ln RMS      (changes the estimand; reference)
  lnrms_jk Friedman on bar-jackknife bias-corrected ln RMS     } keep RMS estimand
  lnrms_an Friedman on analytically bias-corrected ln RMS      }
  rom_pct  day-bootstrap percentile CI of ln(mean r^2 ratio), Bonferroni over 3 contrasts
  rom_t    day-bootstrap-t (studentised) CI, same multiplicity rule
  rom_bca  day-bootstrap BCa CI, same rule
  diff_t   bootstrap-t test of the LINEAR contrast E[ms_a - ms_b] = 0
Scenarios (nulls = equal period RMS, so the RMS null is TRUE):
  D1-D5 as in the first diagnostics; T10/T6 vary tail heaviness; R1-R3 realistic within-period heterogeneity.
Every simulation's seed is saved. Output folder (new): outputs/milestone4/diagnostics/h1_methods/
Usage: python scripts/milestone4/run_h1_methods.py [--quick]
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

from quantlab.calendars import NSE, US, expected_slots                  # noqa: E402
from quantlab.eda.masks import assign_period                            # noqa: E402
from quantlab.research import h1_rms, h1_volatility as h1               # noqa: E402
from quantlab.research.nulls import simulate_table                      # noqa: E402
import run_diagnostics_h1 as base                                       # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "diagnostics" / "h1_methods"
MASTER_SEED = 20261040
MARKETS = {"NSE": NSE, "US": US}
N_DAYS, N_STOCKS, ALPHA, BOOT_B = 59, 3, 0.05, 499
METHODS = ["orig", "sub", "lnrms_jk", "lnrms_an", "rom_pct", "rom_t", "rom_bca", "diff_t"]
RMS_PRESERVING = {"lnrms_jk", "lnrms_an", "rom_pct", "rom_t", "rom_bca", "diff_t", "orig"}


def realistic_profile(market, amp, scale, middle_u=0.0, mult=1.0, v=0.0012):
    """Decaying open volatility, rising close volatility, optional mild midday U. Each period is
    rescaled to the SAME RMS (so the RMS null is true), then open and close multiplied by `mult`."""
    n = market.bars_per_day
    periods = assign_period(expected_slots(market, "2026-08-03"), market).to_numpy()
    prof = np.ones(n)
    for name in ("open", "middle", "close"):
        idx = np.where(periods == name)[0]
        j = np.arange(len(idx))
        if name == "open":
            prof[idx] = 1 + amp * np.exp(-j / scale)
        elif name == "close":
            prof[idx] = 1 + amp * np.exp(-(len(idx) - 1 - j) / scale)
        else:
            x = 2 * j / (len(idx) - 1) - 1
            prof[idx] = 1 + middle_u * x ** 2
    for name in ("open", "middle", "close"):
        u = base.used_slots(market, name)
        prof[u] = prof[u] / np.sqrt(np.mean(prof[u] ** 2))
    for name in ("open", "close"):
        prof[base.used_slots(market, name)] *= mult
    prof[0] = prof[1]
    return prof * v


def scenario_kwargs(name, mk):
    m = MARKETS[mk]
    flat = base.flat_profile(m)
    if name in ("D1 gaussian, flat", "D2 fat tails (t4), flat", "D3 t4 + day volatility factor",
                "D4 t4 + day factor + intraday regime + AR(0.1)",
                "D5 t4 + day factor, EQUAL period RMS but uneven inside periods"):
        return base.dgp_kwargs(name, mk)
    if name == "T10 t10 + day factor, flat":
        return dict(df=10.0, day_vol_sd=0.3, slot_vol=flat)
    if name == "T6 t6 + day factor, flat":
        return dict(df=6.0, day_vol_sd=0.3, slot_vol=flat)
    if name == "R1 realistic moderate open/close decay (max/min 1.8), t4, day factor":
        return dict(df=4.0, day_vol_sd=0.3, slot_vol=realistic_profile(m, 1.0, 3.0))
    if name == "R2 realistic strong open/close decay (max/min 2.5), t4, day factor":
        return dict(df=4.0, day_vol_sd=0.3, slot_vol=realistic_profile(m, 2.0, 2.0))
    if name == "R3 R2 + midday U + intraday regime + AR(0.1)":
        return dict(df=4.0, day_vol_sd=0.3, rho=0.1, intraday_regime_sd=0.25,
                    slot_vol=realistic_profile(m, 2.0, 2.0, middle_u=0.5))
    if name.startswith("POWER flat x"):
        return base.power_kwargs(mk, float(name.split("x")[-1]))
    if name.startswith("POWER R1 x"):
        return dict(df=4.0, day_vol_sd=0.3, slot_vol=realistic_profile(m, 1.0, 3.0, mult=float(name.split("x")[-1])))
    raise ValueError(name)


NULLS = ["D1 gaussian, flat", "D2 fat tails (t4), flat", "T10 t10 + day factor, flat", "T6 t6 + day factor, flat",
         "D3 t4 + day volatility factor", "D4 t4 + day factor + intraday regime + AR(0.1)",
         "R1 realistic moderate open/close decay (max/min 1.8), t4, day factor",
         "R2 realistic strong open/close decay (max/min 2.5), t4, day factor",
         "R3 R2 + midday U + intraday regime + AR(0.1)",
         "D5 t4 + day factor, EQUAL period RMS but uneven inside periods"]
POWERS = ["POWER flat x1.1", "POWER flat x1.2", "POWER R1 x1.1", "POWER R1 x1.2"]


def one_sim(args):
    seed, market, kw, boot_B = args
    rng = np.random.default_rng(seed)
    tabs = [simulate_table(MARKETS[market], f"S{i}", N_DAYS, rng, nse_feed_quirks=(market == "NSE"), **kw)
            for i in range(N_STOCKS)]
    out = {"seed": seed}
    for name, sub in (("orig", False), ("sub", True)):
        panel = h1.market_panel([h1.period_panel(t, market, subsample=sub) for t in tabs])
        d = panel.dropna()
        out[f"{name}_p"] = h1.omnibus(panel)["p"]
        out[f"{name}_open_mid"] = float((d["open"] - d["middle"]).mean())
        out[f"{name}_close_mid"] = float((d["close"] - d["middle"]).mean())
    for name, how in (("lnrms_jk", "jackknife"), ("lnrms_an", "analytic")):
        r = h1_rms.friedman_on_levels([h1_rms.corrected_level_panel(t, market, how) for t in tabs])
        out[f"{name}_p"], out[f"{name}_open_mid"], out[f"{name}_close_mid"] = r["p"], r["open_mid"], r["close_mid"]
    M = h1_rms.market_matrix([h1_rms.mean_square_panel(t, market) for t in tabs])
    for name, how in (("rom_pct", "pct"), ("rom_t", "t"), ("rom_bca", "bca"), ("diff_t", "diff")):
        r = h1_rms.rms_ratio_test(M, rng, how, B=boot_B)
        out[f"{name}_reject"], out[f"{name}_open_mid"], out[f"{name}_close_mid"] = r["reject"], r["open_mid"], r["close_mid"]
    return out


def rejected(df, m):
    return df[f"{m}_reject"].astype(bool) if f"{m}_reject" in df else df[f"{m}_p"] < ALPHA


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    n_size, n_pow, boot_B = (8, 6, 49) if a.quick else (600, 300, BOOT_B)
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files; move them yourself first.")
    OUT.mkdir(parents=True, exist_ok=True)
    seeds = iter(np.random.SeedSequence(MASTER_SEED).spawn(200000))
    nxt = lambda: int(next(seeds).generate_state(1)[0])
    rows, sims = [], []
    with ProcessPoolExecutor() as pool:
        for mk in ("NSE", "US"):
            for name, n in [(s, n_size) for s in NULLS] + [(s, n_pow) for s in POWERS]:
                kw = scenario_kwargs(name, mk)
                df = pd.DataFrame(list(pool.map(one_sim, [(nxt(), mk, kw, boot_B) for _ in range(n)], chunksize=4)))
                df.insert(0, "scenario", name); df.insert(1, "market", mk)
                sims.append(df)
                tr = base.true_log_ratios(MARKETS[mk], kw["slot_vol"])
                for m in METHODS:
                    rej = rejected(df, m)
                    k, N = int(rej.sum()), len(rej)
                    lo, hi = base.wilson(k, N)
                    rows.append({"scenario": name, "market": mk, "method": m, "n_sims": N, "rejection_rate": k / N,
                                 "ci95_low": lo, "ci95_high": hi,
                                 "mean_est_log_ratio_open_vs_middle": df[f"{m}_open_mid"].mean(),
                                 "mean_est_log_ratio_close_vs_middle": df[f"{m}_close_mid"].mean(),
                                 "true_log_ratio_open_RMS": tr[0], "true_log_ratio_close_RMS": tr[1]})
                print(mk, name, "done", flush=True)
    pd.DataFrame(rows).to_csv(OUT / "H1_methods_size_and_power.csv", index=False)
    pd.concat(sims).to_csv(OUT / "H1_methods_per_simulation.csv", index=False)
    pd.Series({"master_seed": MASTER_SEED, "quick": a.quick, "n_sims_size": n_size, "n_sims_power": n_pow,
               "bootstrap_B": boot_B, "n_days": N_DAYS, "stocks_per_market": N_STOCKS,
               "note": "ALL DATA SIMULATED; per-simulation seeds saved in H1_methods_per_simulation.csv"}).to_csv(
        OUT / "run_metadata.csv", header=["value"])
    print("COMPLETE", flush=True)


if __name__ == "__main__":
    main()
