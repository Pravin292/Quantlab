"""M4a NEXT ROUND, H1.  ALL DATA SIMULATED.  Working estimand: RMS volatility (day-volatility-weighted).

Parts (each writes a NEW folder under outputs/milestone4/next_round/):
  calib  Task A  rom_t / diff_t with B = 199, 499, 1999 and two multiplicity rules (Bonferroni, single max-|t|),
                 in Gaussian, heavy-tailed, realistic-heterogeneity, EMPIRICAL-profile (Task C) and D5 scenarios.
  dep    Task B  the same tests under cross-stock correlation, day-to-day volatility clustering, both, and an
                 illustrative strong version; iid-day bootstrap vs block bootstrap (blocks of 5 days).
  d5     Task D  D5 diagnosis: a within-period heterogeneity dose-response scan + a Gaussian D5 + raw ingredients
                 (estimate, SE, t, critical value, jackknife estimate) and the analytic bias-correction decomposition.
All per-simulation results and seeds are saved. Usage: python scripts/milestone4/run_h1_next.py --part calib|dep|d5 [--quick]
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

from quantlab.calendars import NSE, US, expected_slots                         # noqa: E402
from quantlab.eda.masks import assign_period                                   # noqa: E402
from quantlab.research import dependence as dep, h1_rms, h1_rms2               # noqa: E402
from quantlab.research.nulls import simulate_table                             # noqa: E402
import run_diagnostics_h1 as base                                              # noqa: E402

OUT_ROOT = ROOT / "outputs" / "milestone4" / "next_round"
SEEDS = {"calib": 20261050, "dep": 20261051, "d5": 20261052}
MARKETS = {"NSE": NSE, "US": US}
N_DAYS, N_STOCKS, ALPHA = 59, 3, 0.05
# EMPIRICAL shape parameters from describe_next_round.py (within_period_shape.csv), fitted decay 1 + b*exp(-j/tau)
EMP = {"NSE": dict(open_amp=2.031, open_tau=2.063, close_amp=4.581, close_tau=0.365),
       "US": dict(open_amp=5.695, open_tau=3.366, close_amp=3.174, close_tau=1.232)}
# EMPIRICAL dependence (descriptive, imprecise: ~59 days): Pearson corr of standardised returns, cross-stock corr of
# day log-vol, lag-1 autocorrelation of day log-vol (see dependence_descriptives.csv)
EMP_DEP = {"NSE": dict(ret_corr=0.355, share=0.454, phi=0.441),
           "US": dict(ret_corr=0.187, share=0.141, phi=0.190)}
ILLUSTRATIVE_DEP = dict(ret_corr=0.5, share=0.7, phi=0.7)          # NOT estimated: a stress value


def exp_profile(market, tau, mult=1.0, v=0.0012):
    """D5-type profile: exp(-j/tau) in the open, mirror in the close, equal RMS per period. tau=None -> flat."""
    n = market.bars_per_day
    if tau is None:
        return np.full(n, v)
    periods = assign_period(expected_slots(market, "2026-08-03"), market).to_numpy()
    prof = np.ones(n)
    for name in ("open", "close"):
        idx = np.where(periods == name)[0]
        j = np.arange(len(idx))
        prof[idx] = np.exp(-j / tau) if name == "open" else np.exp(j / tau)
    for name in ("open", "middle", "close"):
        u = base.used_slots(market, name)
        prof[u] = prof[u] / np.sqrt(np.mean(prof[u] ** 2))
        if name != "middle":
            prof[u] *= mult
    prof[0] = prof[1]
    return prof * v


def spec_for(part, name, mk):
    """Scenario -> dict of simulation settings."""
    m = MARKETS[mk]
    flat = base.flat_profile(m)
    emp = lambda mult=1.0: dep.shaped_profile(m, mult=mult, **EMP[mk])
    s = dict(df=4.0, day_vol_sd=0.3, rho=0.0, intraday_regime_sd=0.0, profile=flat, dep=None)
    if name == "D1 gaussian, flat":
        s.update(df=1000.0, day_vol_sd=0.0)
    elif name == "D2 t4, flat":
        s.update(day_vol_sd=0.0)
    elif name == "T6 t6 + day factor, flat":
        s.update(df=6.0)
    elif name == "D3 t4 + day factor, flat":
        pass
    elif name == "R1 realistic moderate (round 1), t4":
        s.update(profile=dep.shaped_profile(m, 1.0, 3.0, 1.0, 3.0))
    elif name == "R2 realistic strong (round 1), t4":
        s.update(profile=dep.shaped_profile(m, 2.0, 2.0, 2.0, 2.0))
    elif name == "R3 R2 + regime + AR(0.1)":
        s.update(profile=dep.shaped_profile(m, 2.0, 2.0, 2.0, 2.0), rho=0.1, intraday_regime_sd=0.25)
    elif name == "E empirical-shape profile, t4":
        s.update(profile=emp())
    elif name == "D5 stress (exp decay tau=2), t4":
        s.update(profile=exp_profile(m, 2.0))
    elif name.startswith("POWER flat x"):
        s.update(profile=base.power_kwargs(mk, float(name.split("x")[-1]))["slot_vol"])
    elif name.startswith("POWER E x"):
        s.update(profile=emp(float(name.split("x")[-1])))
    elif name.startswith("DEP "):
        key = name.split()[1]
        e, ill = EMP_DEP[mk], ILLUSTRATIVE_DEP
        cfg = {"X0": dict(ret_corr=0, share=0, phi=0),
               "X1": dict(ret_corr=e["ret_corr"], share=e["share"], phi=0),
               "X2": dict(ret_corr=0, share=0, phi=e["phi"]),
               "X3": dict(ret_corr=e["ret_corr"], share=e["share"], phi=e["phi"]),
               "X4": ill}[key]
        s.update(profile=emp(float(name.split("x")[-1]) if " x" in name else 1.0), dep=cfg)
    elif name.startswith("SCAN "):                              # d5 part: SCAN tau=<v> | SCAN D5 gaussian
        if "gaussian" in name:
            s.update(df=1000.0, profile=exp_profile(m, 2.0))
        else:
            t = name.split("=")[-1]
            s.update(profile=exp_profile(m, None if t == "flat" else float(t)))
    else:
        raise ValueError(name)
    return s


def make_tables(seed, market, s):
    rng = np.random.default_rng(seed)
    kw = dict(df=s["df"], slot_vol=s["profile"], rho=s["rho"], intraday_regime_sd=s["intraday_regime_sd"])
    quirks = market == "NSE"
    if s["dep"] is None:
        tabs = [simulate_table(MARKETS[market], f"S{i}", N_DAYS, rng, nse_feed_quirks=quirks,
                               day_vol_sd=s["day_vol_sd"], **kw) for i in range(N_STOCKS)]
    else:
        d = s["dep"]
        tabs = dep.simulate_market_tables(
            MARKETS[market], N_STOCKS, N_DAYS, rng, day_vol_sd=s["day_vol_sd"], day_share=d["share"], day_phi=d["phi"],
            ret_corr=dep.core_corr_for_pearson(d["ret_corr"], s["df"]) if d["ret_corr"] > 0 else 0.0,
            nse_feed_quirks=quirks, **kw)
    return tabs, rng


def sim_calib(args):
    seed, market, s, plan = args
    tabs, rng = make_tables(seed, market, s)
    M = h1_rms.market_matrix([h1_rms.mean_square_panel(t, market) for t in tabs])
    out = {"seed": seed, "n_days_used": len(M)}
    for kind in ("rom", "diff"):
        for B, block in plan:
            r = h1_rms2.bootstrap_t(M, rng, kind, B=B, alpha=ALPHA, block=block)
            out[f"{kind}|B{B}|blk{block}|bonf"] = r["reject_bonf"]
            out[f"{kind}|B{B}|blk{block}|max"] = r["reject_max"]
        if kind == "rom":
            out["est_open_mid"], out["est_close_mid"] = float(r["theta"][0]), float(r["theta"][1])
    return out


def sim_d5(args):
    seed, market, s, _ = args
    tabs, rng = make_tables(seed, market, s)
    M = h1_rms.market_matrix([h1_rms.mean_square_panel(t, market) for t in tabs])
    out = {"seed": seed}
    for kind in ("rom", "diff"):
        r = h1_rms2.bootstrap_t(M, rng, kind, B=499)
        for c in range(3):
            out[f"{kind}_theta{c}"], out[f"{kind}_se{c}"], out[f"{kind}_t{c}"] = r["theta"][c], r["se"][c], r["t"][c]
            out[f"{kind}_crit{c}"] = r["crit_bonf"][c]
        out[f"{kind}_critmax"], out[f"{kind}_rej_bonf"], out[f"{kind}_rej_max"] = r["crit_max"], r["reject_bonf"], r["reject_max"]
        if kind == "rom":
            for c in range(3):
                out[f"rom_thetajk{c}"] = r["theta_jk"][c]
    # analytic bias-correction decomposition (levels averaged over stocks and days; differences vs middle)
    raw = h1_rms.market_matrix([0.5 * np.log(h1_rms.mean_square_panel(t, market)) for t in tabs])
    an = h1_rms.market_matrix([h1_rms.corrected_level_panel(t, market, "analytic") for t in tabs])
    jk = h1_rms.market_matrix([h1_rms.corrected_level_panel(t, market, "jackknife") for t in tabs])
    for nm, A in (("raw", raw), ("an", an), ("jk", jk)):
        out[f"lvl_{nm}_open_minus_mid"] = float((A[:, 0] - A[:, 1]).mean())
        out[f"lvl_{nm}_close_minus_mid"] = float((A[:, 2] - A[:, 1]).mean())
    out["kappa_hat"] = float(np.mean([h1_rms.pooled_kurtosis(t, market) for t in tabs]))
    from scipy import stats
    for nm, A in (("raw", raw), ("an", an)):
        out[f"fried_p_{nm}"] = float(stats.friedmanchisquare(A[:, 0], A[:, 1], A[:, 2]).pvalue)
    return out


def wilson(k, n):
    return base.wilson(k, n)


def summarise(df, scen, mk, true_ratio_note, cols):
    rows = []
    for c in cols:
        k, n = int(df[c].astype(bool).sum()), len(df)
        lo, hi = wilson(k, n)
        kind, B, blk, rule = c.split("|")
        rows.append({"scenario": scen, "market": mk, "test": kind, "B": int(B[1:]), "block_days": int(blk[3:]),
                     "multiplicity_rule": rule, "n_sims": n, "rejection_rate": k / n, "ci95_low": lo, "ci95_high": hi,
                     "mc_se": float(np.sqrt(max(k / n * (1 - k / n), 1e-12) / n))})
    return rows


def true_mc_bias(market, prof, period, reps=100000, df=4.0, seed=1):
    """Monte-Carlo E[0.5 ln(mean r^2)] - 0.5 ln(RMS^2) for one day-period, no day factor (used in the D5 decomposition)."""
    rng = np.random.default_rng(seed)
    v = prof[base.used_slots(market, period)]
    eps = rng.standard_t(df, (reps, len(v))) * np.sqrt((df - 2) / df)
    ms = (eps ** 2 * v ** 2).mean(axis=1)
    return float(np.mean(0.5 * np.log(ms)) - 0.5 * np.log(np.mean(v ** 2)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True, choices=["calib", "dep", "d5"])
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    q = a.quick
    out = OUT_ROOT / f"h1_{a.part}"
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} already has files.")
    out.mkdir(parents=True, exist_ok=True)
    seeds = iter(np.random.SeedSequence(SEEDS[a.part]).spawn(300000))
    nxt = lambda: int(next(seeds).generate_state(1)[0])
    rows, sims, diag = [], [], []

    if a.part == "calib":
        n_size, n_pow = (6, 4) if q else (1000, 300)
        plan = [(199, 1), (499, 1), (1999, 1)] if not q else [(49, 1), (99, 1)]
        scen = [("D1 gaussian, flat", n_size), ("D2 t4, flat", n_size), ("T6 t6 + day factor, flat", n_size),
                ("D3 t4 + day factor, flat", n_size), ("R1 realistic moderate (round 1), t4", n_size),
                ("R2 realistic strong (round 1), t4", n_size), ("R3 R2 + regime + AR(0.1)", n_size),
                ("E empirical-shape profile, t4", n_size), ("D5 stress (exp decay tau=2), t4", n_size),
                ("POWER flat x1.1", n_pow), ("POWER E x1.1", n_pow), ("POWER E x1.2", n_pow)]
        fn, tail = sim_calib, None
    elif a.part == "dep":
        n_size, n_pow = (6, 4) if q else (800, 300)
        plan = [(999, 1), (999, 5)] if not q else [(49, 1), (49, 5)]
        scen = [(f"DEP {k}", n_size) for k in ("X0", "X1", "X2", "X3", "X4")] + [("DEP X3 x1.1", n_pow), ("DEP X3 x1.2", n_pow)]
        fn = sim_calib
    else:
        n_size = 6 if q else 600
        plan = None
        scen = [(f"SCAN tau={t}", n_size) for t in ("flat", "8", "5", "3.5", "2")] + [("SCAN D5 gaussian", n_size)]
        fn = sim_d5

    with ProcessPoolExecutor() as pool:
        for mk in ("NSE", "US"):
            for name, n in scen:
                s = spec_for(a.part, name, mk)
                df = pd.DataFrame(list(pool.map(fn, [(nxt(), mk, s, plan) for _ in range(n)], chunksize=4)))
                df.insert(0, "scenario", name); df.insert(1, "market", mk)
                sims.append(df)
                if fn is sim_calib:
                    cols = [c for c in df.columns if c.endswith("|bonf") or c.endswith("|max")]
                    rows += summarise(df, name, mk, None, cols)
                print(mk, name, "done", flush=True)
    pd.concat(sims).to_csv(out / f"h1_{a.part}_per_simulation.csv", index=False)
    if rows:
        pd.DataFrame(rows).to_csv(out / f"h1_{a.part}_size_and_power.csv", index=False)
    pd.Series({"master_seed": SEEDS[a.part], "quick": q, "n_days": N_DAYS, "stocks_per_market": N_STOCKS,
               "n_sims_size": n_size, "empirical_shape_params": str(EMP), "empirical_dependence_params": str(EMP_DEP),
               "illustrative_dependence_params": str(ILLUSTRATIVE_DEP),
               "note": "ALL DATA SIMULATED; per-simulation seeds saved"}).to_csv(out / "run_metadata.csv", header=["value"])
    if a.part == "d5":
        allsims = pd.concat(sims)
        for (scen_name, mk), g in allsims.groupby(["scenario", "market"], sort=False):
            s = spec_for("d5", scen_name, mk)
            m = MARKETS[mk]
            for c, per in ((0, "open"), (1, "close")):
                row = {"scenario": scen_name, "market": mk, "contrast": f"{per}-middle", "n_sims": len(g)}
                for kind in ("rom", "diff"):
                    th, se, t, cr = g[f"{kind}_theta{c}"], g[f"{kind}_se{c}"], g[f"{kind}_t{c}"], g[f"{kind}_crit{c}"]
                    row[f"{kind}_bias"] = th.mean()
                    row[f"{kind}_sd_of_estimate"] = th.std()
                    row[f"{kind}_bias_over_sd"] = th.mean() / th.std()
                    row[f"{kind}_mean_se_over_true_sd"] = se.mean() / th.std()
                    row[f"{kind}_mean_boot_crit"] = cr.mean()
                    row[f"{kind}_oracle_crit_(1-a/3_quantile_of_|t|)"] = float(np.quantile(np.abs(t), 1 - ALPHA / 3))
                    row[f"{kind}_reject_per_contrast_as_run"] = float((np.abs(t) > cr).mean())
                    row[f"{kind}_reject_if_bias_removed"] = float((np.abs((th - th.mean()) / se) > cr).mean())
                    if kind == "rom":
                        tjk = g[f"rom_thetajk{c}"]
                        row["rom_jackknife_bias"] = tjk.mean()
                        row["rom_reject_with_jackknife_estimate"] = float((np.abs(tjk / se) > cr).mean())
                row["analytic_level_diff_corrected"] = g[f"lvl_an_{per}_minus_mid"].mean()
                row["raw_level_diff"] = g[f"lvl_raw_{per}_minus_mid"].mean()
                row["jackknife_level_diff"] = g[f"lvl_jk_{per}_minus_mid"].mean()
                row["mc_true_raw_level_bias_diff_(oracle)"] = (true_mc_bias(m, s["profile"], per, df=s["df"])
                                                              - true_mc_bias(m, s["profile"], "middle", df=s["df"]))
                row["mean_kappa_hat"] = g["kappa_hat"].mean()
                row["friedman_reject_raw"] = float((g["fried_p_raw"] < ALPHA).mean())
                row["friedman_reject_analytic"] = float((g["fried_p_an"] < ALPHA).mean())
                diag.append(row)
            r_all = {"scenario": scen_name, "market": mk, "contrast": "ANY (as run, bonferroni)",
                     "rom_reject_per_contrast_as_run": float(g["rom_rej_bonf"].mean()),
                     "diff_reject_per_contrast_as_run": float(g["diff_rej_bonf"].mean()), "n_sims": len(g)}
            diag.append(r_all)
        pd.DataFrame(diag).to_csv(out / "h1_d5_diagnosis.csv", index=False)
    print("COMPLETE", flush=True)


if __name__ == "__main__":
    main()
