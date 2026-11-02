"""M4a DIAGNOSTICS for the H1 calibration failure.   ALL DATA SIMULATED.

Questions answered
  A. How large is the finite-sample bias of ln(RMS) for n=8 vs n=54 bars, for different
     return distributions?  (pure statistics, no market simulation)
  B. Is the Friedman implementation itself correct?  (iid exchangeable panels)
  C. How do four methods behave on identical simulated markets: size under several nulls,
     power under several alternatives, and what log-ratio each one estimates?
        orig  : ln RMS of ALL bars in each period, Friedman test        (the original design)
        sub   : ln RMS of equal-size random subsets (m=7 NSE / 9 US), Friedman (the proposal)
        rom   : ratio of AVERAGE variances (all bars, no logs per day) with a day-block
                bootstrap interval, Bonferroni over the 3 contrasts   (an alternative)
        ref   : permutation-calibrated orig? NOT included; see report.
Outputs (new folder): outputs/milestone4/diagnostics/h1/
Usage: python scripts/milestone4/run_diagnostics_h1.py [--quick]
"""
import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from quantlab.calendars import NSE, US                                  # noqa: E402
from quantlab.eda.masks import PERIODS, assign_period                    # noqa: E402
from quantlab.calendars import expected_slots                            # noqa: E402
from quantlab.research import h1_volatility as h1                       # noqa: E402
from quantlab.research.nulls import simulate_table                      # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "diagnostics" / "h1"
MASTER_SEED = 20261031
MARKETS = {"NSE": NSE, "US": US}
N_DAYS, N_STOCKS, ALPHA = 59, 3, 0.05


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


# ------------------------------------------------------------------ profiles
def used_slots(market, period):
    """Slots (columns) whose CLOSE-TO-CLOSE return is used by H1 for this period."""
    periods = assign_period(expected_slots(market, "2026-08-03"), market).to_numpy()
    idx = np.where(periods == period)[0]
    return idx[idx > 0]                                       # the opening candle has no c2c return


def flat_profile(market, v=0.0012):
    return np.full(market.bars_per_day, v)


def equal_rms_heterogeneous_profile(market, v=0.0012):
    """Every period has the SAME root-mean-square volatility, but volatility is spread very
    unevenly inside the open and close periods. H0 for the RMS estimand is TRUE here."""
    n = market.bars_per_day
    periods = assign_period(expected_slots(market, "2026-08-03"), market).to_numpy()
    prof = np.ones(n)
    for name, shape in [("open", lambda j: np.exp(-j / 2.0)), ("close", lambda j: np.exp(j / 2.0))]:
        idx = np.where(periods == name)[0]
        prof[idx] = shape(np.arange(len(idx)))
    for name in ["open", "middle", "close"]:
        idx = used_slots(market, name)
        prof[idx] = prof[idx] / np.sqrt(np.mean(prof[idx] ** 2))         # equal period RMS
    prof[0] = prof[1]
    return prof * v


def true_log_ratios(market, prof):
    """ln(RMS_period / RMS_middle): the population value of the RMS-based estimand."""
    rms = {p: np.sqrt(np.mean(prof[used_slots(market, p)] ** 2)) for p in ["open", "middle", "close"]}
    return np.log(rms["open"] / rms["middle"]), np.log(rms["close"] / rms["middle"])


def true_log_ratios_geometric(market, prof):
    g = {p: np.mean(np.log(prof[used_slots(market, p)])) for p in ["open", "middle", "close"]}
    return g["open"] - g["middle"], g["close"] - g["middle"]


# ------------------------------------------------------------------ DGPs (the nulls)
def dgp_kwargs(name, market):
    m = MARKETS[market]
    if name == "D1 gaussian, flat":
        return dict(df=1000.0, day_vol_sd=0.0, slot_vol=flat_profile(m))
    if name == "D2 fat tails (t4), flat":
        return dict(df=4.0, day_vol_sd=0.0, slot_vol=flat_profile(m))
    if name == "D3 t4 + day volatility factor":
        return dict(df=4.0, day_vol_sd=0.3, slot_vol=flat_profile(m))
    if name == "D4 t4 + day factor + intraday regime + AR(0.1)":
        return dict(df=4.0, day_vol_sd=0.3, rho=0.1, intraday_regime_sd=0.25, slot_vol=flat_profile(m))
    if name == "D5 t4 + day factor, EQUAL period RMS but uneven inside periods":
        return dict(df=4.0, day_vol_sd=0.3, slot_vol=equal_rms_heterogeneous_profile(m))
    raise ValueError(name)


def power_kwargs(market, mult):
    m = MARKETS[market]
    prof = flat_profile(m)
    for p in ["open", "close"]:
        prof[used_slots(m, p)] *= mult
    prof[0] = prof[1]
    return dict(df=4.0, day_vol_sd=0.3, slot_vol=prof)


# ------------------------------------------------------------------ methods
def rom_decision(panels_level, rng, B=999):
    """Ratio-of-average-variances with day-block bootstrap; reject if ANY contrast's
    (1 - alpha/3) interval excludes zero. panels_level: per-stock day x period of mean r^2."""
    stack = np.nanmean(np.stack([p.to_numpy() for p in panels_level]), axis=0)          # days x 3
    stack = stack[~np.isnan(stack).any(axis=1)]
    idx = rng.integers(0, len(stack), size=(B, len(stack)))
    boot = stack[idx].mean(axis=1)                                                      # B x 3 (open, middle, close)
    est = stack.mean(axis=0)
    res = []
    for a, b in [(0, 1), (2, 1), (0, 2)]:
        d = np.log(boot[:, a] / boot[:, b])
        lo, hi = np.quantile(d, [ALPHA / 6, 1 - ALPHA / 6])
        res.append((lo > 0) or (hi < 0))
    return any(res), float(np.log(est[0] / est[1])), float(np.log(est[2] / est[1]))


def mean_square_panel(table, market_name):
    ok = table[(table["status"] == "ok") & table["period"].isin(["open", "middle", "close"])]
    g = ok.groupby(["date", "period"])["ret"]
    ms = g.apply(lambda s: np.mean(s.to_numpy() ** 2))
    n = g.count()
    exp = pd.Series([h1.EXPECTED_RETURNS[market_name][p] for p in n.index.get_level_values("period")], index=n.index)
    ms = ms.where(n / exp >= h1.MIN_COVERAGE)
    return ms.unstack("period").reindex(columns=["open", "middle", "close"])


def one_sim(args):
    seed, market, kw = args
    rng = np.random.default_rng(seed)
    tabs = [simulate_table(MARKETS[market], f"S{i}", N_DAYS, rng, nse_feed_quirks=(market == "NSE"), **kw)
            for i in range(N_STOCKS)]
    out = {}
    for name, sub in [("orig", False), ("sub", True)]:
        panel = h1.market_panel([h1.period_panel(t, market, subsample=sub) for t in tabs])
        om = h1.omnibus(panel)
        d = panel.dropna()
        out[f"{name}_p"] = om["p"]
        out[f"{name}_open_mid"] = float((d["open"] - d["middle"]).mean())
        out[f"{name}_close_mid"] = float((d["close"] - d["middle"]).mean())
    rej, lo, lc = rom_decision([mean_square_panel(t, market) for t in tabs], rng)
    out.update(rom_reject=rej, rom_open_mid=lo, rom_close_mid=lc)
    return out


def summarise(df, label, market, sims, true_rms, true_geo):
    rows = []
    for m in ["orig", "sub", "rom"]:
        rej = (df[f"{m}_p"] < ALPHA) if m != "rom" else df["rom_reject"].astype(bool)
        k, n = int(rej.sum()), len(rej)
        lo, hi = wilson(k, n)
        rows.append({"scenario": label, "market": market, "method": m, "n_sims": n, "rejection_rate": k / n,
                     "ci95_low": lo, "ci95_high": hi,
                     "mean_est_log_ratio_open_vs_middle": df[f"{m}_open_mid"].mean(),
                     "mean_est_log_ratio_close_vs_middle": df[f"{m}_close_mid"].mean(),
                     "true_log_ratio_open_RMS": true_rms[0], "true_log_ratio_close_RMS": true_rms[1],
                     "true_log_ratio_open_geometric": true_geo[0], "true_log_ratio_close_geometric": true_geo[1]})
    return rows


# ------------------------------------------------------------------ A and B
def bias_table(rng, reps=200000):
    rows = []
    for dist, gen in [("gaussian", lambda size: rng.standard_normal(size)),
                      ("student t, 10 df", lambda size: rng.standard_t(10, size) / np.sqrt(10 / 8)),
                      ("student t, 4 df", lambda size: rng.standard_t(4, size) / np.sqrt(2))]:
        for n in [7, 8, 9, 11, 12, 54]:
            x = gen((reps, n))
            ln_rms = 0.5 * np.log((x ** 2).mean(axis=1))
            rows.append({"returns": dist, "bars_n": n, "mean_ln_rms_minus_true": ln_rms.mean(),
                         "sd_ln_rms": ln_rms.std(), "median_ln_rms_minus_true": float(np.median(ln_rms))})
    return pd.DataFrame(rows)


def implementation_check(rng, reps=20000):
    rej = 0
    perm_agree = 0
    for r in range(reps):
        x = rng.standard_normal((59, 3))
        p = stats.friedmanchisquare(x[:, 0], x[:, 1], x[:, 2]).pvalue
        rej += p < ALPHA
    # independent permutation implementation on a few panels
    for r in range(200):
        x = rng.standard_normal((59, 3))
        stat = stats.friedmanchisquare(x[:, 0], x[:, 1], x[:, 2]).statistic
        null = []
        for _ in range(300):
            perm = np.array([rng.permutation(3) for _ in range(59)])
            y = np.take_along_axis(x, perm, axis=1)
            null.append(stats.friedmanchisquare(y[:, 0], y[:, 1], y[:, 2]).statistic)
        p_perm = (np.sum(np.array(null) >= stat) + 1) / (len(null) + 1)
        p_scipy = stats.friedmanchisquare(x[:, 0], x[:, 1], x[:, 2]).pvalue
        perm_agree += abs(p_perm - p_scipy) < 0.08
    k = int(rej)
    lo, hi = wilson(k, reps)
    return pd.DataFrame([{"check": "Friedman on iid exchangeable 59x3 panels", "reps": reps, "rejection_rate": k / reps,
                          "ci95_low": lo, "ci95_high": hi,
                          "share_of_200_panels_where_permutation_p_matches_scipy_p": perm_agree / 200}])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    n_size, n_pow = (16, 12) if a.quick else (800, 400)
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files; move them yourself first.")
    OUT.mkdir(parents=True, exist_ok=True)
    seeds = iter(np.random.SeedSequence(MASTER_SEED).spawn(100000))
    nxt = lambda: int(next(seeds).generate_state(1)[0])
    rng = np.random.default_rng(nxt())
    bias_table(rng, 20000 if a.quick else 200000).to_csv(OUT / "A_ln_rms_bias_by_sample_size.csv", index=False)
    implementation_check(rng, 2000 if a.quick else 20000).to_csv(OUT / "B_friedman_implementation_check.csv", index=False)
    rows = []
    with ProcessPoolExecutor() as pool:
        for mk in ["NSE", "US"]:
            for name in ["D1 gaussian, flat", "D2 fat tails (t4), flat", "D3 t4 + day volatility factor",
                         "D4 t4 + day factor + intraday regime + AR(0.1)",
                         "D5 t4 + day factor, EQUAL period RMS but uneven inside periods"]:
                kw = dgp_kwargs(name, mk)
                prof = kw["slot_vol"]
                df = pd.DataFrame(list(pool.map(one_sim, [(nxt(), mk, kw) for _ in range(n_size)], chunksize=4)))
                rows += summarise(df, name, mk, n_size, true_log_ratios(MARKETS[mk], prof),
                                  true_log_ratios_geometric(MARKETS[mk], prof))
                print(name, mk, "done", flush=True)
            for mult in [1.05, 1.10, 1.20, 1.50]:
                kw = power_kwargs(mk, mult)
                df = pd.DataFrame(list(pool.map(one_sim, [(nxt(), mk, kw) for _ in range(n_pow)], chunksize=4)))
                rows += summarise(df, f"POWER: open and close volatility x{mult} vs middle", mk, n_pow,
                                  true_log_ratios(MARKETS[mk], kw["slot_vol"]),
                                  true_log_ratios_geometric(MARKETS[mk], kw["slot_vol"]))
                print("power", mult, mk, "done", flush=True)
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "C_size_and_power_by_method.csv", index=False)
    pd.Series({"master_seed": MASTER_SEED, "quick": a.quick, "n_sims_size": n_size, "n_sims_power": n_pow,
               "n_days": N_DAYS, "stocks_per_market": N_STOCKS, "note": "ALL DATA SIMULATED"}).to_csv(
        OUT / "run_metadata.csv", header=["value"])
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(res[["scenario", "market", "method", "n_sims", "rejection_rate", "ci95_low", "ci95_high"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
