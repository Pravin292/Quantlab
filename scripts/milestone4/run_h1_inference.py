"""M4b, H1.  ALL DATA SIMULATED (fast direct generator, src/quantlab/research/direct_sim.py).  Working estimand: RMS volatility.

Parts (new folders under outputs/milestone4/m4b/):
  diag  Task A  factor isolation for rom_t / diff_t (max-|t| rule, B=999): tails x within-period shape grid, a scan of the
                NSE/US close-spike scale, open-only / close-only shapes, a no-day-factor ablation, and a diagnostic that
                replaces the 1 or 5 largest squared returns. Saves estimate, SE, t and critical values per simulation.
  cand  Task B  candidate methods on identical datasets (n_days = 59): rom_t, diff_t (baselines), rom_jack (jackknife-SE
                bootstrap-t), diff_wildR / diff_wildM (wild bootstrap-t), diff_el (empirical likelihood). Type I error and power.
  size  Task D  the same candidates with 125 and 250 trading days.
Scenario names: <tail> <shape> [nodayfactor] [dep] [x<mult>], tail in G,T10,T6,T4; shape in flat,E,D5,R2,Eopen,Eclose,Etau<v>.
Usage: python scripts/milestone4/run_h1_inference.py --part diag|cand|size [--quick]
"""
import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))

from quantlab.calendars import NSE, US                                       # noqa: E402
from quantlab.research import dependence as dep, direct_sim as ds, h1_rms2, h1_robust as rb   # noqa: E402
import run_h1_next as nx                                                     # noqa: E402

OUT_ROOT = ROOT / "outputs" / "milestone4" / "m4b"
SEEDS = {"diag": 20261070, "cand": 20261071, "size": 20261072}
MARKETS = {"NSE": NSE, "US": US}
N_STOCKS, ALPHA = 3, 0.05
DF = {"G": 1000.0, "T10": 10.0, "T6": 6.0, "T4": 4.0}


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def profile_for(mk, shape, mult):
    m, e = MARKETS[mk], nx.EMP[mk]
    if shape == "flat":
        return dep.shaped_profile(m, 0, 1, 0, 1, mult=mult)
    if shape == "D5":
        return nx.exp_profile(m, 2.0, mult)
    if shape == "R2":
        return dep.shaped_profile(m, 2.0, 2.0, 2.0, 2.0, mult=mult)
    kw = dict(open_amp=e["open_amp"], open_tau=e["open_tau"], close_amp=e["close_amp"], close_tau=e["close_tau"])
    if shape == "Eopen":
        kw["close_amp"] = 0.0
    elif shape == "Eclose":
        kw["open_amp"] = 0.0
    elif shape.startswith("Etau"):
        kw["close_tau"] = float(shape[4:])
    elif shape != "E":
        raise ValueError(shape)
    return dep.shaped_profile(m, mult=mult, **kw)


def parse(name, mk, n_days):
    tok = name.split()
    mult = 1.0
    flags = set()
    for t in tok[2:]:
        if t.startswith("x"):
            mult = float(t[1:])
        else:
            flags.add(t)
    spec = dict(profile=profile_for(mk, tok[1], mult), df=DF[tok[0]], day_vol_sd=0.0 if "nodayfactor" in flags else 0.3,
                share=0.0, phi=0.0, ret_corr=0.0, n_days=n_days)
    if "dep" in flags:
        e = nx.EMP_DEP[mk]
        spec.update(share=e["share"], phi=e["phi"], ret_corr=e["ret_corr"])
    return spec


def gen(seed, mk, spec):
    rng = np.random.default_rng(seed)
    r2 = ds.simulate_returns_sq(MARKETS[mk], N_STOCKS, spec["n_days"], rng, profile=spec["profile"], df=spec["df"],
                                day_vol_sd=spec["day_vol_sd"], share=spec["share"], phi=spec["phi"], ret_corr=spec["ret_corr"])
    return r2, rng


def sim_diag(args):
    seed, mk, spec = args
    r2, rng = gen(seed, mk, spec)
    idx = ds.used_slot_index(MARKETS[mk])
    out = {"seed": seed}
    variants = [("all", ds.period_matrix(r2, idx))] + [(f"minus{k}", ds.period_matrix(ds.replace_extremes(r2, idx, k), idx)) for k in (1, 5)]
    for tag, M in variants:
        for kind in ("rom", "diff"):
            r = h1_rms2.bootstrap_t(M, rng, kind, B=999)
            out[f"{kind}|{tag}|max"], out[f"{kind}|{tag}|bonf"] = r["reject_max"], r["reject_bonf"]
            if tag == "all":
                for c in range(3):
                    out[f"{kind}_theta{c}"], out[f"{kind}_se{c}"], out[f"{kind}_t{c}"] = r["theta"][c], r["se"][c], r["t"][c]
                out[f"{kind}_critmax"] = r["crit_max"]
    return out


def sim_cand(args):
    seed, mk, spec = args
    r2, rng = gen(seed, mk, spec)
    M = ds.period_matrix(r2, ds.used_slot_index(MARKETS[mk]))
    out = {"seed": seed}
    for name, kind in (("rom_t", "rom"), ("diff_t", "diff")):
        r = h1_rms2.bootstrap_t(M, rng, kind, B=1999)
        out[f"{name}|max"], out[f"{name}|bonf"] = r["reject_max"], r["reject_bonf"]
        if kind == "rom":
            out["est_open_mid"], out["est_close_mid"] = float(r["theta"][0]), float(r["theta"][1])
    r = rb.bootstrap_t_jackknife(M, rng, B=999)
    out["rom_jack|max"], out["rom_jack|bonf"] = r["reject_max"], r["reject_bonf"]
    for name, w in (("diff_wildR", "rademacher"), ("diff_wildM", "mammen")):
        r = rb.wild_bootstrap_t(M, rng, B=1999, weights=w)
        out[f"{name}|max"], out[f"{name}|bonf"] = r["reject_max"], r["reject_bonf"]
    out["diff_el|bonf"] = rb.empirical_likelihood_diff(M)["reject_bonf"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True, choices=list(SEEDS))
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    q = a.quick
    out = OUT_ROOT / f"h1_{a.part}"
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} already has files.")
    out.mkdir(parents=True, exist_ok=True)
    seeds = iter(np.random.SeedSequence(SEEDS[a.part]).spawn(1_000_000))
    nxt = lambda: int(next(seeds).generate_state(1)[0])
    jobs = []                                       # (name, n_days, n_sims)
    if a.part == "diag":
        n = 12 if q else 8000
        names = [f"{t} {s}" for t in ("G", "T10", "T6", "T4") for s in ("flat", "E", "D5")]
        names += [f"T4 Etau{v}" for v in ("0.37", "1.0", "2.0", "4.0")] + ["T4 Eopen", "T4 Eclose", "T4 E nodayfactor", "T4 D5 nodayfactor"]
        jobs = [(nm, 59, n) for nm in names]
        fn = sim_diag
    elif a.part == "cand":
        n_s, n_p = (12, 8) if q else (10000, 2000)
        jobs = [(nm, 59, n_s) for nm in ("G flat", "T4 flat", "G E", "T6 E", "T4 E", "T4 E nodayfactor", "T4 R2", "G D5", "T4 D5", "T4 E dep")]
        jobs += [(nm, 59, n_p) for nm in ("T4 E x1.1", "T4 E x1.2", "T4 E x1.3", "T4 flat x1.1", "T4 flat x1.2")]
        fn = sim_cand
    else:
        n_s, n_p = (12, 8) if q else (5000, 1000)
        jobs = [(nm, nd, n_s) for nd in (125, 250) for nm in ("T4 flat", "T4 E", "T4 D5", "T4 E dep", "G E")]
        jobs += [(nm, nd, n_p) for nd in (125, 250) for nm in ("T4 E x1.1", "T4 E x1.2")]
        fn = sim_cand
    rows, sims = [], []
    t0 = time.time()
    with ProcessPoolExecutor() as pool:
        for mk in ("NSE", "US"):
            for name, nd, n in jobs:
                spec = parse(name, mk, nd)
                df = pd.DataFrame(list(pool.map(fn, [(nxt(), mk, {k: v for k, v in spec.items()}) for _ in range(n)], chunksize=16)))
                df.insert(0, "scenario", name); df.insert(1, "market", mk); df.insert(2, "n_days", nd)
                sims.append(df)
                for c in [c for c in df.columns if c.endswith("|max") or c.endswith("|bonf")]:
                    parts = c.split("|")
                    meth, rule = (parts[0], parts[-1]) if fn is sim_cand else (parts[0] + ":" + parts[1], parts[-1])
                    k, N = int(df[c].sum()), len(df)
                    lo, hi = wilson(k, N)
                    rows.append({"scenario": name, "market": mk, "n_days": nd, "method": meth, "rule": rule, "n_sims": N,
                                 "rejection_rate": k / N, "ci95_low": lo, "ci95_high": hi, "mc_se": float(np.sqrt(max(k / N * (1 - k / N), 1e-12) / N))})
                print(mk, name, nd, f"done {time.time() - t0:.0f}s", flush=True)
    pd.concat(sims).to_parquet(out / f"h1_{a.part}_per_simulation.parquet", index=False)
    summ = pd.DataFrame(rows)
    summ.to_csv(out / f"h1_{a.part}_size_and_power.csv", index=False)
    if a.part == "diag":
        allsims = pd.concat(sims)
        drows = []
        for (sc, mk), g in allsims.groupby(["scenario", "market"], sort=False):
            for kind in ("rom", "diff"):
                th = np.stack([g[f"{kind}_theta{c}"] for c in range(3)], 1)
                se = np.stack([g[f"{kind}_se{c}"] for c in range(3)], 1)
                t = np.stack([g[f"{kind}_t{c}"] for c in range(3)], 1)
                crit = g[f"{kind}_critmax"].to_numpy()
                tmax = np.abs(t).max(1)
                oracle = float(np.quantile(tmax, 0.95))
                t_c = np.abs((th - th.mean(0)) / se).max(1)
                drows.append({"scenario": sc, "market": mk, "test": kind, "n_sims": len(g),
                              "reject_max_as_run": float((tmax > crit).mean()),
                              "reject_if_estimator_bias_removed": float((t_c > crit).mean()),
                              "mean_bootstrap_crit_max": float(crit.mean()), "oracle_crit_max_(0.95_quantile_of_max|t|)": oracle,
                              "reject_with_oracle_crit": float((tmax > oracle).mean()),
                              "mean_abs_bias_over_sd": float(np.mean(np.abs(th.mean(0) / th.std(0)))),
                              "mean_se_over_true_sd": float(np.mean(se.mean(0) / th.std(0))),
                              "t_skewness_mean": float(np.mean([stats.skew(t[:, c]) for c in range(3)])),
                              "t_excess_kurtosis_mean": float(np.mean([stats.kurtosis(t[:, c]) for c in range(3)])),
                              "reject_after_removing_1_extreme_obs": float(g[f"{kind}|minus1|max"].mean()),
                              "reject_after_removing_5_extreme_obs": float(g[f"{kind}|minus5|max"].mean())})
        pd.DataFrame(drows).to_csv(out / "h1_diag_factor_isolation.csv", index=False)
    pd.Series({"master_seed": SEEDS[a.part], "quick": q, "stocks_per_market": N_STOCKS,
               "empirical_shape_params": str(nx.EMP), "empirical_dependence_params": str(nx.EMP_DEP),
               "note": "ALL DATA SIMULATED (direct generator); per-simulation seeds saved"}).to_csv(out / "run_metadata.csv", header=["value"])
    print("COMPLETE", flush=True)


if __name__ == "__main__":
    main()
