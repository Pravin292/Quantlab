"""H1 calibration, STAGE 4 PREREGISTRATION ANALYSES (no Stage 4 result is produced here).   ALL DATA SIMULATED.
Everything the preregistration (docs/22) cites is computed here and saved to outputs/milestone4/h1_calibration/stage4_prereg/:
  null_check_precision.csv          per process (a, b, e, f) and market: standard error of the period-mean ratios from independent batches, sqrt(N) scaling check,
                                    pass probability of the literal 0.5% tolerance at the frozen 1e6 bars and at 5e7 bars, and the minimum sample size for a stated false-failure rate
  null_check_design.csv             the resulting days / bars per period per (process, market) and the generation cost
  truncated_moment_design.csv       exact truncated second moments and required sample sizes for the infinite-fourth-moment processes c and d
  bar_level_ztest_calibration.csv   null behaviour of the two-proportion z-test for the 8 planned cells (2,000 vs 25,000), family-wise false-flag rate, power
  reference_selection.csv           the 10 cells and 100 datasets for the second-implementation check, chosen by a rule fixed here BEFORE any result exists
Scratch seed 20261215 (registered as an analysis seed; NOT a Stage 4 validation seed). Refuses to overwrite.
"""
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import integrate, stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage3_common as c3c                                                # noqa: E402
from quantlab.calendars import NSE, US                                     # noqa: E402
from quantlab.research import direct_sim as ds, h1_calibration_v11 as v11, h1_stage4 as s4   # noqa: E402
import run_h1_inference as ri                                             # noqa: E402

OUT = c3c.B / "stage4_prereg"
SEED = 20261215
MK = {"NSE": NSE, "US": US}
PROC = ["a_intraday_volatility_clustering", "b_jumps", "e_heavy_tailed_day_factor", "f_laplace_shocks"]
TOL = 0.005
DB, KB = 4000, 300                                    # days per batch, number of batches
Q_ALL = 0.99                                          # target probability that ALL 16 ratios pass for a correct generator
Z_RATIO = stats.norm.isf((1 - Q_ALL ** (1 / 16)) / 2)  # per-ratio multiple of the standard error implied by Q_ALL


def batch_ratios(args):
    """K independent batches for one (process, market); returns arrays of the open/middle and close/middle period-mean ratios."""
    ci, proc, mk = args
    m = MK[mk]; prof = ri.profile_for(mk, "E", 1.0); idx = ds.used_slot_index(m)
    ro, rc = [], []
    for b in range(KB):
        rng = np.random.default_rng(np.random.SeedSequence(SEED, spawn_key=(ci, b)))
        r2 = s4.simulate_alt_returns_sq(proc, m, 3, DB, rng, prof)
        pm = [r2[:, :, i].mean() for i in idx]
        ro.append(pm[0] / pm[1]); rc.append(pm[2] / pm[1])
    return ci, np.array(ro), np.array(rc)


def trunc_moments(df, q=0.999):
    """Exact E[e^2 1{|e|<=c}] and Var[e^2 1{|e|<=c}] of a unit-variance Student-t(df) shock, c = its q-quantile (two-sided mass 2q-1 ... c = ppf((1+q)/2))."""
    sc = v11.t_unit_scale(df)
    c = stats.t(df).ppf((1 + q) / 2) * sc
    pdf = lambda x: stats.t(df).pdf(x / sc) / sc
    m1 = 2 * integrate.quad(lambda x: x ** 2 * pdf(x), 0, c, epsabs=1e-13, epsrel=1e-12)[0]
    m2 = 2 * integrate.quad(lambda x: x ** 4 * pdf(x), 0, c, epsabs=1e-13, epsrel=1e-12)[0]
    return c, m1, m2 - m1 ** 2


def main():
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files.")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    jobs = [(i, p, mk) for i, (p, mk) in enumerate([(p, mk) for p in PROC for mk in ("NSE", "US")])]
    with ProcessPoolExecutor() as pool:
        res = list(pool.map(batch_ratios, jobs))
    rng = np.random.default_rng(SEED)
    for (ci, proc, mk), (_, ro, rc) in zip(jobs, res):
        nb = [len(i) for i in ds.used_slot_index(MK[mk])]
        for name, x, nbars in (("open/middle", ro, nb[0]), ("close/middle", rc, nb[2])):
            sd = x.std(ddof=1)
            boot = np.array([rng.choice(x, KB).std(ddof=1) for _ in range(2000)])
            sd_hi = float(np.quantile(boot, 0.975))
            g4 = x[: KB // 4 * 4].reshape(-1, 4).mean(axis=1)                       # scaling check: means of 4 batches should have sd ~ sd/2
            rows.append({"process": proc, "market": mk, "ratio": name, "days_per_batch": DB, "batches": KB, "mean_ratio_minus_1_%": 100 * (x.mean() - 1), "sd_batch_%": 100 * sd,
                         "sd_batch_upper95_%": 100 * sd_hi, "scaling_check_sd4_over_sd1 (expect 0.5)": g4.std(ddof=1) / sd, "used_bars_numerator_period": nbars})
    t = pd.DataFrame(rows)
    # standard errors at a given number of days D: sd_batch * sqrt(DB / D)
    out = []
    for (proc, mk), g in t.groupby(["process", "market"], sort=False):
        nb_open = len(ds.used_slot_index(MK[mk])[0])
        for D_label, bars in (("frozen 1e6 bars", 1e6), ("proposed 5e7 bars", 5e7)):
            D = bars / (3 * nb_open)
            ses = [r["sd_batch_%"] / 100 * math.sqrt(DB / D) for _, r in g.iterrows()]
            p_pass = [math.erf(TOL / (s * math.sqrt(2))) for s in ses]
            out.append({"process": proc, "market": mk, "sample": D_label, "days": int(D), "SE_open_%": 100 * ses[0], "SE_close_%": 100 * ses[1],
                        "P_pass_open": p_pass[0], "P_pass_close": p_pass[1], "tolerance_in_SE_units_min": TOL / max(ses)})
    pp = pd.DataFrame(out)
    for sample in ("frozen 1e6 bars", "proposed 5e7 bars"):
        x = pp[pp["sample"] == sample]
        pp.loc[x.index, "P_all16_pass_(all_processes)"] = float(np.prod(x.P_pass_open) * np.prod(x.P_pass_close))
    pp.to_csv(OUT / "null_check_precision.csv", index=False)
    t.to_csv(OUT / "null_check_batch_statistics.csv", index=False)
    # minimum days for the literal 0.5% tolerance at Z_RATIO standard errors (upper 95% bound of the batch sd)
    des = []
    for (proc, mk), g in t.groupby(["process", "market"], sort=False):
        nb = [len(i) for i in ds.used_slot_index(MK[mk])]
        need = max(((r["sd_batch_upper95_%"] / 100) * math.sqrt(DB) / (TOL / Z_RATIO)) ** 2 for _, r in g.iterrows())
        D = int(math.ceil(need / 100_000) * 100_000)
        des.append({"process": proc, "market": mk, "z_per_ratio_for_Pall99": Z_RATIO, "min_days_required": int(math.ceil(need)), "days_rounded_up": D,
                    "bars_open_period": D * 3 * nb[0], "bars_close_period": D * 3 * nb[2], "bars_middle_period": D * 3 * nb[1], "elements_generated": D * 3 * MK[mk].bars_per_day})
    d = pd.DataFrame(des)
    d.to_csv(OUT / "null_check_design.csv", index=False)
    # truncated moments for processes c and d
    tm = []
    for lab, df in (("c: open and close (t4)", 4), ("c: middle (t8)", 8), ("d: stock 1 (t3)", 3), ("d: stock 2 (t5)", 5), ("d: stock 3 (t8)", 8)):
        c, m1, v = trunc_moments(df)
        for N in (1e7, 5e7):
            tm.append({"component": lab, "cutoff_c": c, "exact_truncated_E_e2": m1, "exact_truncated_var_e2": v, "N_bars": N, "relative_SE_%": 100 * math.sqrt(v / N) / m1,
                       "N_for_SE_tol/4": v / (m1 * TOL / 4) ** 2})
    pd.DataFrame(tm).to_csv(OUT / "truncated_moment_design.csv", index=False)
    # bar-level z-test calibration
    cm = pd.read_csv(c3c.S3 / "summary" / "stage3_cell_results.csv", keep_default_na=False)
    cells = [2, 3, 4, 5, 26, 27, 28, 29]
    zr, pw = [], []
    K = 200_000
    for r in cells:
        for method in ("c3", "baseline"):
            p = float(cm[(cm.val_row == r) & (cm["method"] == method)].p_hat.iloc[0])
            for n1 in (2000, 8000):
                n2 = 25000
                x1, x2 = rng.binomial(n1, p, K), rng.binomial(n2, p, K)
                pool = (x1 + x2) / (n1 + n2); se = np.sqrt(pool * (1 - pool) * (1 / n1 + 1 / n2)); z = np.where(se > 0, (x1 / n1 - x2 / n2) / np.where(se > 0, se, 1), 0)
                zr.append({"val_row": r, "method": method, "p_fast": p, "n_bar_level": n1, "n_fast": n2, "expected_successes_bar_level": n1 * p, "P(|z|>3)": float((np.abs(z) > 3).mean()),
                           "P(|z|>2)": float((np.abs(z) > 2).mean())})
                for delta in (0.005, 0.01, 0.02, 0.03):
                    x1d = rng.binomial(n1, min(p + delta, 0.999), K)
                    pool = (x1d + x2) / (n1 + n2); se = np.sqrt(pool * (1 - pool) * (1 / n1 + 1 / n2)); zd = (x1d / n1 - x2 / n2) / se
                    pw.append({"val_row": r, "method": method, "p_fast": p, "n_bar_level": n1, "true_difference_points": 100 * delta, "power_|z|>3": float((np.abs(zd) > 3).mean())})
    zdf, pdf_ = pd.DataFrame(zr), pd.DataFrame(pw)
    zdf.to_csv(OUT / "bar_level_ztest_calibration.csv", index=False); pdf_.to_csv(OUT / "bar_level_ztest_power.csv", index=False)
    # reference-implementation selection: 5 NSE + 5 US rows of the 96 validation cells, drawn with a rule fixed here
    vc = c3c.load_validation_cells()
    sel = []
    for mk in ("NSE", "US"):
        rr = np.random.default_rng(np.random.SeedSequence(20261208, spawn_key=(0, 0 if mk == "NSE" else 1)))
        pool_rows = vc.index[vc.market == mk].to_numpy()
        sel += sorted(int(x) for x in rr.choice(pool_rows, 5, replace=False))
    sd = pd.DataFrame([{"val_row": r, **{k: vc.loc[r, k] for k in ("tail", "shape", "market", "n_days", "dependence", "day_vol_sd", "tier")}, "datasets": "simulations i = 0..9",
                        "seed_rule": "SeedSequence(20261208, spawn_key=(val_row, i))"} for r in sel])
    sd.to_csv(OUT / "reference_selection.csv", index=False)
    pd.DataFrame([{"purpose": "Stage 4 alternative processes", "master": 20261206, "spawn_key": "(cell_row, i, stream)", "status": "frozen v1 seed"},
                  {"purpose": "Stage 4 bar-level check", "master": 20261207, "spawn_key": "(cell_index, i, stream)", "status": "frozen v1 seed"},
                  {"purpose": "Stage 4 reference implementation", "master": 20261208, "spawn_key": "(val_row, i)", "status": "frozen v1 seed"},
                  {"purpose": "Stage 4 Monte-Carlo null check (before use of the alternative processes)", "master": 20261206, "spawn_key": "(100 + process_market_index, batch)", "status": "frozen v1 seed, separate namespace: first key element >= 100, simulation streams use 0-11"},
                  {"purpose": "preregistration analyses only (this script)", "master": SEED, "spawn_key": "(combo, batch)", "status": "analysis seed, not a validation seed"}]).to_csv(OUT / "seeds.csv", index=False)
    print(pp.round(4).to_string(index=False)); print(d.to_string(index=False))
    print("scaling check (expect about 0.5):", t["scaling_check_sd4_over_sd1 (expect 0.5)"].round(2).tolist())
    print("selected reference rows:", sel)


if __name__ == "__main__":
    main()
