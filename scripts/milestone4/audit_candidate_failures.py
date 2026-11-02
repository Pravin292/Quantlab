"""Audit numerical failures of the H1 candidate methods and re-check reproducibility.   ALL SIMULATED.

For the cells of h1_cand / h1_size (per-simulation seeds are saved) the datasets are regenerated and
  (1) REPRODUCIBILITY: sim_cand is rerun on the first N_REPRO seeds of each cell and every saved decision/estimate is compared
      with the stored value (a mismatch would mean the saved results are not reproducible);
  (2) FAILURE ACCOUNTING on the first N_FAIL seeds of each cell, with an independent random stream:
      empirical likelihood   zero outside the convex hull (statistic = infinity -> counted as rejection), brentq exceptions,
                             non-converged roots (|score| > 1e-8), non-finite or negative statistics
      jackknife-t            non-finite or non-positive observed jackknife SE; share of bootstrap resamples with non-finite t*
      wild bootstrap-t       zero/non-finite observed SD of a contrast; share of resamples with non-finite t* (Rademacher, Mammen)
      baseline bootstrap-t   non-finite observed SE / t*; share of resamples with non-finite t*
  Nothing is discarded: this only COUNTS. Main runs used every simulation.
Output: outputs/milestone4/m4b/verification/candidate_failure_audit_{cand,size}.csv
"""
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))
from quantlab.research import direct_sim as ds, h1_rms2, h1_robust as rb      # noqa: E402
from quantlab.research.h1_rms import CONTRAST_IDX                              # noqa: E402
from quantlab.research.inference import resample_days                          # noqa: E402
import run_h1_inference as ri                                                  # noqa: E402

N_REPRO, N_FAIL = 300, 3000
OUT = ROOT / "outputs" / "milestone4" / "m4b" / "verification"


def el_audit(d):
    d = np.asarray(d, float); d = d / np.abs(d).max()
    if d.min() >= 0 or d.max() <= 0:
        return "hull"
    lo, hi = -1 / d.max() + 1e-10, -1 / d.min() - 1e-10
    try:
        lam = optimize.brentq(lambda l: np.sum(d / (1 + l * d)), lo, hi, xtol=1e-12, maxiter=200)
    except Exception:
        return "exception"
    if abs(np.sum(d / (1 + lam * d))) > 1e-8:
        return "nonconverged"
    stat = 2 * np.sum(np.log1p(lam * d))
    return "ok" if np.isfinite(stat) and stat >= -1e-9 else "invalid_stat"


def audit_one(args):
    seed, mk, spec, saved, do_repro = args
    out = {}
    if do_repro:
        new = ri.sim_cand((seed, mk, spec))
        diffs = [c for c in saved if c in new and not (np.isclose(new[c], saved[c], equal_nan=True) if isinstance(new[c], float) else new[c] == saved[c])]
        out["repro_mismatch"] = len(diffs)
    r2, _ = ri.gen(seed, mk, spec)
    M = ds.period_matrix(r2, ds.used_slot_index(ri.MARKETS[mk]))
    rng = np.random.default_rng(seed + 7)
    n = len(M)
    D = np.stack([M[:, a] - M[:, b] for a, b in CONTRAST_IDX], 1)
    cls = [el_audit(D[:, c]) for c in range(3)]
    for k in ("hull", "exception", "nonconverged", "invalid_stat"):
        out[f"el_{k}"] = sum(c == k for c in cls)
    out["el_any_problem"] = int(any(c != "ok" and c != "hull" for c in cls)); out["el_any_hull"] = int(any(c == "hull" for c in cls))
    se_obs = np.array([float(rb._jackknife_se(M, a, b)) for a, b in CONTRAST_IDX])
    out["jack_obs_bad"] = int((~np.isfinite(se_obs) | (se_obs <= 0)).any())
    Xb = M[resample_days(n, 999, rng)]
    bad = np.zeros(999, bool)
    for a, b in CONTRAST_IDX:
        s = rb._jackknife_se(Xb, a, b); bad |= ~np.isfinite(s) | (s <= 0)
    out["jack_resamples_bad_share"] = bad.mean()
    sd = D.std(axis=0, ddof=1)
    out["wild_obs_bad"] = int((~np.isfinite(sd) | (sd <= 0)).any())
    for tag, w in (("R", rng.integers(0, 2, (999, n)) * 2.0 - 1.0), ("M", rb._mammen(rng, 999, n))):
        Db = w[:, :, None] * D[None]
        s = Db.std(axis=1, ddof=1)
        out[f"wild{tag}_resamples_bad_share"] = float((~np.isfinite(s) | (s <= 0)).any(axis=1).mean())
    se_d = np.array([h1_rms2._se_blocks(h1_rms2._influence(M, a, b, "rom")[1], 1) for a, b in CONTRAST_IDX])
    out["delta_obs_bad"] = int((~np.isfinite(se_d) | (se_d <= 0)).any())
    return out


def main(part):
    d = pd.read_parquet(ROOT / "outputs/milestone4/m4b" / f"h1_{part}" / f"h1_{part}_per_simulation.parquet")
    rows = []
    with ProcessPoolExecutor() as pool:
        for (sc, mk, nd), g in d.groupby(["scenario", "market", "n_days"], sort=False):
            spec = ri.parse(sc, mk, nd)
            g = g.head(N_FAIL)
            keep = [c for c in g.columns if c.endswith("|max") or c.endswith("|bonf") or c.startswith("est_")]
            args = [(int(r["seed"]), mk, spec, {c: r[c] for c in keep}, i < N_REPRO) for i, (_, r) in enumerate(g.iterrows())]
            res = pd.DataFrame(list(pool.map(audit_one, args, chunksize=16)))
            row = {"scenario": sc, "market": mk, "n_days": nd, "n_audited": len(res), "n_repro_checked": int(res["repro_mismatch"].notna().sum()),
                   "repro_mismatching_sims": int((res["repro_mismatch"].fillna(0) > 0).sum())}
            for c in res.columns:
                if c == "repro_mismatch":
                    continue
                row[c] = float(res[c].sum()) if c.startswith(("el_", "jack_obs", "wild_obs", "delta_obs")) else float(res[c].mean())
            rows.append(row)
            print(part, mk, sc, nd, "audited", flush=True)
    pd.DataFrame(rows).to_csv(OUT / f"candidate_failure_audit_{part}.csv", index=False)
    print("COMPLETE", part)


if __name__ == "__main__":
    main(sys.argv[1])
