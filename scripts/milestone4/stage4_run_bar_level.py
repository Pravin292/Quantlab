"""H1 calibration, STAGE 4, part C: BAR-LEVEL PIPELINE CHECK (docs/22 section 5; D2/D3 approved: 8,000 simulations per cell, acceptance |z| <= 3, matrices within 1e-9).   ALL SIMULATED.
--part sims   : 8 cells (Stage 3 validation rows 2, 3, 4, 5, 26, 27, 28, 29 = df inf and T4 x shapes E, D5 x NSE, US; 59 days) x 8,000 NEW bar-level simulations through the real route
                simulate_table -> clean -> bar table -> period mean squares -> day matrix; C3 (frozen value) and the baseline bootstrap-t (B = 999) are applied. Seeds
                SeedSequence(20261207, spawn_key=(cell_index, i, 0)) for the bar-level data and (cell_index, i, 2) for the bootstrap. The comparison with the Stage 3 fast-route results is made by stage4_make_report.py.
--part matrix : 10 datasets per cell (80): the SAME returns through the fast route and through direct_bridge.returns_to_table; seeds (cell_index, i, 1); pass if identical shape and max relative difference <= 1e-9.
Output: outputs/milestone4/h1_calibration/stage4/bar_level/
"""
import argparse
import os
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage4_common as c4                                                 # noqa: E402
from quantlab.research import direct_sim as ds, h1_calibration as hc, h1_rms   # noqa: E402
from quantlab.research.direct_bridge import returns_to_table              # noqa: E402
from quantlab.research.h1_rms2 import bootstrap_t                         # noqa: E402

OUT = c4.S4 / "bar_level"
CHUNK = 100
_CRIT = None


def _init(crit):
    """Worker start-up."""
    global _CRIT
    _CRIT = crit


def sim_work(job):
    """Bar-level simulations [start, stop) of one cell."""
    ci, start, stop = job
    st = c4.bar_level_setup(c4.BAR_ROWS[ci])
    rows = []
    for i in range(start, stop):
        M = c4.bar_level_matrix(st, np.random.default_rng(np.random.SeedSequence(c4.MASTER["bar_level"], spawn_key=(ci, i, 0))))
        r = {"cell_index": ci, "sim": i, "n_days_used": len(M)}
        try:
            T = float(hc.max_abs_t(M)); res = bootstrap_t(M, np.random.default_rng(np.random.SeedSequence(c4.MASTER["bar_level"], spawn_key=(ci, i, 2))), "rom", B=999)
            ok = bool(np.isfinite(T) and np.isfinite(res["t"]).all() and np.isfinite(res["crit_max"]))
            r.update(T=T, valid=ok, reject_c3=bool(T > _CRIT) if ok else False, reject_base=bool(res["reject_max"]) if ok else False, crit_base=float(res["crit_max"]))
        except Exception:
            r.update(T=float("nan"), valid=False, reject_c3=False, reject_base=False, crit_base=float("nan"))
        rows.append(r)
    return rows


def matrix_work(job):
    """Same-returns check of dataset i of cell ci."""
    ci, i = job
    st = c4.bar_level_setup(c4.BAR_ROWS[ci]); m = st["market"]
    rng = np.random.default_rng(np.random.SeedSequence(c4.MASTER["bar_level"], spawn_key=(ci, i, 1)))
    r2 = ds.simulate_returns_sq(m, 3, 59, rng, profile=st["profile"], df=st["df"], day_vol_sd=st["day_vol_sd"])
    Md = ds.period_matrix(r2, ds.used_slot_index(m))
    tabs = [returns_to_table(m, np.sqrt(r2[s]), f"S{s}", rng, nse_feed_quirks=True) for s in range(3)]          # M4b convention (quirks on for both markets)
    Mp = h1_rms.market_matrix([h1_rms.mean_square_panel(t, st["market_name"]) for t in tabs])
    same = Md.shape == Mp.shape
    rel = float(np.max(np.abs(Mp - Md) / Md)) if same else float("nan")
    return {"cell_index": ci, "val_row": c4.BAR_ROWS[ci], "market": st["market_name"], "dataset": i, "days_fast": len(Md), "days_pipeline": len(Mp), "same_shape": same, "max_relative_difference": rel}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True, choices=["sims", "matrix"])
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--cells", default=None)
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    out = Path(a.out) if a.out else OUT
    if a.smoke and (a.out is None or Path(a.out).resolve() == OUT.resolve()):
        sys.exit("--smoke needs --out pointing to a scratch folder")
    checks = c4.verify_all(stage4_inputs=not a.smoke)
    out.mkdir(parents=True, exist_ok=True)
    cells = [int(x) for x in a.cells.split(",")] if a.cells else list(range(8))
    t0, wall0 = time.perf_counter(), time.time()
    if a.part == "matrix":
        f = out / "same_returns_matrix_check.csv"
        if f.exists():
            sys.exit(f"{f.name} already exists")
        n = a.n if a.smoke and a.n else 10
        with ProcessPoolExecutor() as pool:
            d = pd.DataFrame(list(pool.map(matrix_work, [(ci, i) for ci in cells for i in range(n)])))
        d.to_csv(f, index=False)
        ok = bool(d.same_shape.all() and (d.max_relative_difference <= 1e-9).all())
        pd.DataFrame([{"criterion": "all matrices same shape and max relative difference <= 1e-9", "met": ok, "matrices": len(d), "max_rel_diff": float(d.max_relative_difference.max())}]).to_csv(out / "same_returns_matrix_outcome.csv", index=False)
        print("matrices:", len(d), "max relative difference:", d.max_relative_difference.max(), "PASS:", ok, flush=True); print("COMPLETE", flush=True)
        return
    crit, done, skipped = c4.c3_value_59(), 0, 0
    if any((out / f"cell_{c:02d}.parquet").exists() for c in cells) and not a.resume:
        sys.exit("bar-level cell files already exist (use --resume only to continue an interrupted run)")
    with ProcessPoolExecutor(initializer=_init, initargs=(crit,)) as pool:
        for ci in cells:
            n = a.n if a.smoke and a.n else 8000
            f = out / f"cell_{ci:02d}.parquet"
            if f.exists():
                d = pd.read_parquet(f, columns=["sim"])
                if len(d) == n and d["sim"].tolist() == list(range(n)):
                    skipped += 1
                    continue
                sys.exit(f"{f.name} exists but is incomplete; stop and report")
            d = pd.DataFrame([r for part in pool.map(sim_work, [(ci, s, min(s + CHUNK, n)) for s in range(0, n, CHUNK)]) for r in part]).sort_values("sim")
            assert len(d) == n and d["sim"].tolist() == list(range(n))
            tmp = out / f"cell_{ci:02d}.tmp"; d.to_parquet(tmp, index=False); tmp.rename(f)
            done += n
            v = d[d.valid]
            print(f"bar-level cell {ci} (val row {c4.BAR_ROWS[ci]}) n={n} days_used min/max {int(d.n_days_used.min())}/{int(d.n_days_used.max())} c3={v.reject_c3.mean():.4f} base={v.reject_base.mean():.4f} "
                  f"invalid={int((~d.valid).sum())} done={done} elapsed={time.perf_counter() - t0:.0f}s", flush=True)
    pd.Series({"master_seed": c4.MASTER["bar_level"], "seed_rule": "SeedSequence(20261207, spawn_key=(cell_index, i, stream)); 0 data, 1 matrix check, 2 bootstrap", "sims_per_cell": 8000 if not a.smoke else a.n,
               "c3_crit_59": crit, "simulations_this_session": done, "smoke": a.smoke, "wall_seconds": round(time.perf_counter() - t0, 1), "started_unix": round(wall0), "logical_cpus": os.cpu_count(),
               "python": platform.python_version(), "manifests_verified": str({k: v for k, v in checks.items() if k != "free_gib"}), "note": "ALL DATA SIMULATED; bar-level route"}).to_csv(out / f"run_metadata_{int(wall0)}.csv", header=["value"])
    print("COMPLETE", done, "simulations this session;", skipped, "cells already complete", flush=True)


if __name__ == "__main__":
    main()
