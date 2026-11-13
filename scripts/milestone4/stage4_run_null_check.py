"""H1 calibration, STAGE 4, part A: NULL CHECK of the alternative processes BEFORE their use (docs/22 section 3, approved as D1). ALL DATA SIMULATED. No candidate is evaluated.
  a, b, e, f : ratios open/middle and close/middle of period mean squares from 5e7 bars in the open period (days: NSE 2,083,333, US 1,515,151; 3 stocks); literal tolerance 0.5%.
  c, d       : truncated second moment E[e^2 1{|e|<=c}] (c = 99.9% two-sided quantile) of each shock component against its exact value, 1e7 bars per component; tolerance 0.5%.
  all        : the exact analytic unit-variance factors (a, b, e, f) are re-computed and listed.
Seeds: SeedSequence(20261206, spawn_key=(100 + idx, batch)); idx 0-7 = a, b, e, f x (NSE, US); idx 8-11 = c (NSE, US), d (NSE, US). Batches of 20,000 days.
Outcome file null_check_outcome.csv (passed = all checks within 0.5%): the alternative-process run refuses to start unless it says passed.
Output: outputs/milestone4/h1_calibration/stage4/null_check/     Usage: python scripts/milestone4/stage4_run_null_check.py  (--smoke --scale 0.002 --out <scratch>)
"""
import argparse
import math
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage4_common as c4                                                 # noqa: E402
from quantlab.research import direct_sim as ds, h1_calibration_v11 as v11, h1_stage4 as s4   # noqa: E402
import run_h1_inference as ri                                             # noqa: E402

OUT = c4.S4 / "null_check"
ABEF = ["a_intraday_volatility_clustering", "b_jumps", "e_heavy_tailed_day_factor", "f_laplace_shocks"]
COMBOS = [(i, p, mk) for i, (p, mk) in enumerate([(p, mk) for p in ABEF for mk in ("NSE", "US")])]
TRUNC = [(8, "c_period_specific_tails", "NSE"), (9, "c_period_specific_tails", "US"), (10, "d_stock_specific_tails", "NSE"), (11, "d_stock_specific_tails", "US")]
BATCH, TOL, N_OPEN_BARS, N_TRUNC = 20_000, 0.005, 5e7, 1e7
MASTER = c4.MASTER["alt"]


def ratio_job(a):
    """Period-mean ratios of one process and market over `days` days, generated in independent batches."""
    idx, proc, mk, days, batch = a
    m = c4.MARKETS[mk]; prof = ri.profile_for(mk, "E", 1.0); used = ds.used_slot_index(m); nb = np.array([len(i) for i in used])
    sums, br, nbatch = np.zeros(3), [], math.ceil(days / batch)
    for b in range(nbatch):
        d = min(batch, days - b * batch)
        r2 = s4.simulate_alt_returns_sq(proc, m, 3, d, np.random.default_rng(np.random.SeedSequence(MASTER, spawn_key=(100 + idx, b))), prof)
        ps = np.array([r2[:, :, i].sum() for i in used]); sums += ps
        per = ps / (3 * d * nb); br.append([per[0] / per[1], per[2] / per[1]])
    mean = sums / (3 * days * nb); br = np.array(br)
    se = br.std(ddof=1, axis=0) / math.sqrt(nbatch) if nbatch > 1 else np.full(2, np.nan)
    return dict(idx=idx, process=proc, market=mk, days=days, bars_open=int(3 * days * nb[0]), bars_middle=int(3 * days * nb[1]), bars_close=int(3 * days * nb[2]),
                ratio_open=mean[0] / mean[1], ratio_close=mean[2] / mean[1], se_open=float(se[0]), se_close=float(se[1]), batches=nbatch)


def trunc_job(a):
    """Truncated second moments of the shock components of process c (periods) or d (stocks), against the exact values."""
    idx, proc, mk, days, batch = a
    m = c4.MARKETS[mk]; used = ds.used_slot_index(m)
    comps = ([("open", 4, used[0]), ("middle", 8, used[1]), ("close", 4, used[2])] if proc.startswith("c") else
             [(f"stock {s + 1}", df, np.concatenate(used)) for s, df in enumerate((3, 5, 8))])
    cut = {df: c4.trunc_moments(df) for _, df, _ in comps}
    acc = {k: [0.0, 0, []] for k, _, _ in comps}
    nbatch = math.ceil(days / batch)
    for b in range(nbatch):
        d = min(batch, days - b * batch)
        eps = s4.alt_components(proc, m, 3, d, np.random.default_rng(np.random.SeedSequence(MASTER, spawn_key=(100 + idx, b))))["eps"]
        for name, df, sl in comps:
            x = eps[:, :, sl] if proc.startswith("c") else eps[int(name.split()[1]) - 1][:, sl]
            v = np.where(np.abs(x) <= cut[df][0], x * x, 0.0)
            acc[name][0] += float(v.sum()); acc[name][1] += v.size; acc[name][2].append(float(v.mean()))
    rows = []
    for name, df, _ in comps:
        s_, n_, bm = acc[name]
        mean = s_ / n_; exact = cut[df][1]
        rows.append(dict(idx=idx, process=proc, market=mk, component=name, df=df, cutoff=cut[df][0], bars=n_, empirical=mean, exact=exact, rel_dev=mean / exact - 1,
                         se_rel=(np.std(bm, ddof=1) / math.sqrt(len(bm)) / exact) if len(bm) > 1 else float("nan"), tail_variance_share_beyond_cutoff=1 - exact))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--scale", type=float, default=1.0)
    a = ap.parse_args()
    out = Path(a.out) if a.out else OUT
    if a.smoke and (a.out is None or Path(a.out).resolve() == OUT.resolve()):
        sys.exit("--smoke needs --out pointing to a scratch folder")
    if not a.smoke and a.scale != 1.0:
        sys.exit("--scale is for smoke tests only")
    checks = c4.verify_all(stage4_inputs=not a.smoke)
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} already has files.")
    out.mkdir(parents=True, exist_ok=True)
    batch = 50 if a.smoke else BATCH
    floor = 2 * batch
    t0 = time.perf_counter()
    jobs = []
    for idx, p, mk in COMBOS:
        nb_open = len(ds.used_slot_index(c4.MARKETS[mk])[0])
        jobs.append((idx, p, mk, max(int(math.ceil(N_OPEN_BARS / (3 * nb_open)) * a.scale), floor), batch))
    tj = []
    for idx, p, mk in TRUNC:
        used = ds.used_slot_index(c4.MARKETS[mk])
        need = N_TRUNC / (3 * len(used[0])) if p.startswith("c") else N_TRUNC / sum(len(u) for u in used)
        tj.append((idx, p, mk, max(int(math.ceil(need) * a.scale), floor), batch))
    with ProcessPoolExecutor() as pool:
        rr = list(pool.map(ratio_job, jobs)); tr = [r for rows in pool.map(trunc_job, tj) for r in rows]
    R = pd.DataFrame(rr)
    for c_, nm in (("ratio_open", "open"), ("ratio_close", "close")):
        R[f"dev_{nm}_%"] = 100 * (R[c_] - 1)
        R[f"pass_{nm}"] = (R[c_] - 1).abs() <= TOL
    R["dev_open_in_SE"] = (R["ratio_open"] - 1) / R["se_open"]; R["dev_close_in_SE"] = (R["ratio_close"] - 1) / R["se_close"]
    T = pd.DataFrame(tr); T["pass"] = T.rel_dev.abs() <= TOL
    A = pd.DataFrame([{"process": p, "analytic_E[shock part^2]": v11.alt_dgp_second_moment_factor(p), "abs_error": abs(v11.alt_dgp_second_moment_factor(p) - 1)} for p in ABEF])
    R.to_csv(out / "null_check_ratios_abef.csv", index=False); T.to_csv(out / "null_check_truncated_cd.csv", index=False); A.to_csv(out / "null_check_analytic.csv", index=False)
    passed = bool(R.pass_open.all() and R.pass_close.all() and T["pass"].all() and (A.abs_error < 1e-9).all())
    pd.DataFrame([{"criterion": "a, b, e, f: all 16 period-mean ratios within 0.5%", "met": bool(R.pass_open.all() and R.pass_close.all())},
                  {"criterion": "c, d: all 12 truncated second moments within 0.5% of the exact value", "met": bool(T["pass"].all())},
                  {"criterion": "analytic unit-variance factors equal 1 to 1e-9", "met": bool((A.abs_error < 1e-9).all())},
                  {"criterion": "NULL CHECK PASSED (all of the above)", "met": passed}]).to_csv(out / "null_check_outcome.csv", index=False)
    pd.Series({"master_seed": MASTER, "seed_rule": "SeedSequence(20261206, spawn_key=(100 + idx, batch))", "batch_days": batch, "smoke": a.smoke, "scale": a.scale, "wall_seconds": round(time.perf_counter() - t0, 1),
               "python": platform.python_version(), "numpy": np.__version__, "manifests_verified": str({k: v for k, v in checks.items() if k != "free_gib"}), "note": "ALL DATA SIMULATED"}).to_csv(out / "run_metadata.csv", header=["value"])
    print(R[["process", "market", "days", "bars_open", "dev_open_%", "dev_close_%", "dev_open_in_SE", "dev_close_in_SE", "pass_open", "pass_close"]].round(4).to_string(index=False))
    print(T[["process", "market", "component", "bars", "rel_dev", "se_rel", "pass"]].round(5).to_string(index=False)); print("NULL CHECK PASSED:", passed, flush=True)
    print("COMPLETE", flush=True)


if __name__ == "__main__":
    main()
