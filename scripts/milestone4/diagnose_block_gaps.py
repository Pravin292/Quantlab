"""M4a next round: do blocks of 5 CONSECUTIVE ROWS of the market matrix span gaps in the trading-day sequence?  DIAGNOSTIC.

The market matrix drops days on which any stock lacks a complete period value. The block bootstrap then treats
the remaining rows as consecutive. This script quantifies the exposure and checks sensitivity:

  Part 1  Exposure in the batches already run: how many simulations dropped any day (n_days_used < 59)?
  Part 2  Descriptive coverage of the REAL cleaned sample: which days would be dropped, how many 5-row blocks span
          a gap. (Coverage counting only; NO hypothesis test is run on real data.)
  Part 3  Sensitivity experiment on SIMULATED data: randomly remove 0 / 4 / 8 days from the simulated market matrix
          and compare (a) the method as run ("ignore": blocks of consecutive rows, gaps ignored) with
          (b) "aware": blocks only from runs of truly consecutive trading days, SE blocks built inside runs.
Outputs (new folder): outputs/milestone4/next_round/block_gap_diagnostic/
"""
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))

from quantlab.calendars import market_for_symbol                              # noqa: E402
from quantlab.research import h1_rms, h1_rms2                                  # noqa: E402
from quantlab.research.h1_rms import CONTRAST_IDX                              # noqa: E402
from quantlab.research.panel import load_tables                                # noqa: E402
import run_diagnostics_h1 as base                                              # noqa: E402
import run_h1_next as nx                                                       # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "next_round" / "block_gap_diagnostic"
BLOCK, ALPHA, B = 5, 0.05, 499
MASTER_SEED = 20261060


def kept_positions(panels):
    """Positions (in the sorted union of trading dates) of the complete days kept by the market matrix."""
    dates = sorted(set().union(*[set(p.index) for p in panels]))
    stack = np.stack([p.reindex(dates).to_numpy() for p in panels]).mean(axis=0)
    return np.where(~np.isnan(stack).any(axis=1))[0], len(dates)


def span_stats(pos, block=BLOCK):
    """Share of possible length-`block` windows of consecutive kept rows that span a calendar gap."""
    n = len(pos)
    starts = np.arange(n - block + 1)
    span = (pos[starts + block - 1] - pos[starts]) != block - 1
    return float(span.mean()), int(span.sum()), len(starts)


def sample_affected(pos, rng, B=2000, block=BLOCK):
    """Share of bootstrap samples (as run) that contain at least one gap-spanning block."""
    n = len(pos)
    nb = int(np.ceil(n / block))
    starts = rng.integers(0, n - block + 1, size=(B, nb))
    span = (pos[starts + block - 1] - pos[starts]) != block - 1
    return float(span.any(axis=1).mean()), float(span.mean())


# --------------------------------------------------------------- aware variant (diagnostic only)
def _se_runs(u, pos, block):
    """SE of mean(u) from non-overlapping blocks built inside runs of consecutive trading days."""
    sums, cut = [], np.where(np.diff(pos) != 1)[0] + 1
    for run in np.split(np.arange(len(pos)), cut):
        for k in range(len(run) // block):
            sums.append(u[run[k * block:(k + 1) * block]].sum())
    m = len(sums)
    return np.sqrt(np.var(sums, ddof=1) * m) / (m * block)


def boot_aware(M, pos, rng, kind, B=B, block=BLOCK):
    n = len(M)
    valid = np.where((pos[np.minimum(np.arange(n) + block - 1, n - 1)] - pos) == block - 1)[0]
    valid = valid[valid <= n - block]
    nb = int(np.ceil(n / block))
    starts = rng.choice(valid, size=(B, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(B, -1)[:, :n]
    return _bt(M, idx, kind, lambda u: _se_runs(u, pos, block))


def boot_ignore(M, rng, kind, B=B, block=BLOCK):
    r = h1_rms2.bootstrap_t(M, rng, kind, B=B, block=block)
    return r["reject_bonf"], r["reject_max"]


def _bt(M, idx, kind, se_obs, block=BLOCK):
    Xb = M[idx]
    th_l, t_l, ts_l = [], [], []
    for a, b in CONTRAST_IDX:
        th, u = h1_rms2._influence(M, a, b, kind)
        thb, ub = h1_rms2._influence(Xb, a, b, kind)
        sb = h1_rms2._se_blocks(ub, block)
        t_l.append(float(th / se_obs(u))); ts_l.append((thb - th) / sb)
    ts = np.abs(np.stack(ts_l, axis=1))
    crit = np.quantile(ts, 1 - ALPHA / 3, axis=0)
    cmax = np.quantile(ts.max(axis=1), 1 - ALPHA)
    t = np.abs(np.array(t_l))
    return bool((t > crit).any()), bool(t.max() > cmax)


def sens_sim(args):
    seed, market, scen = args
    s = nx.spec_for("dep", scen, market)
    tabs, rng = nx.make_tables(seed, market, s)
    panels = [h1_rms.mean_square_panel(t, market) for t in tabs]
    pos0, ndates = kept_positions(panels)
    M0 = h1_rms.market_matrix(panels)
    out = {"seed": seed, "n_rows_before_extra_drop": len(M0), "dropped_by_pipeline": ndates - len(M0)}
    drng = np.random.default_rng(seed + 1)
    for drop in (0, 4, 8):
        keep = np.sort(drng.choice(len(M0), len(M0) - drop, replace=False)) if drop else np.arange(len(M0))
        M, pos = M0[keep], pos0[keep]
        out[f"drop{drop}_share_windows_spanning"] = span_stats(pos)[0]
        out[f"drop{drop}_share_boot_samples_affected"], out[f"drop{drop}_share_blocks_spanning"] = sample_affected(pos, drng)
        for kind in ("rom", "diff"):
            bonf, mx = boot_ignore(M, rng, kind)
            out[f"drop{drop}|{kind}|ignore|bonf"], out[f"drop{drop}|{kind}|ignore|max"] = bonf, mx
            bonf, mx = boot_aware(M, pos, rng, kind)
            out[f"drop{drop}|{kind}|aware|bonf"], out[f"drop{drop}|{kind}|aware|max"] = bonf, mx
    return out


def main():
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files.")
    OUT.mkdir(parents=True, exist_ok=True)
    # ---- Part 1: exposure in batches already run
    rows = []
    for part in ("calib", "dep"):
        f = ROOT / "outputs" / "milestone4" / "next_round" / f"h1_{part}" / f"h1_{part}_per_simulation.csv"
        d = pd.read_csv(f)
        d["any_day_dropped"] = d["n_days_used"] < 59
        for (sc, mk), g in d.groupby(["scenario", "market"], sort=False):
            rows.append({"part": part, "scenario": sc, "market": mk, "n_sims": len(g),
                         "sims_with_any_day_dropped": int(g["any_day_dropped"].sum()),
                         "share": float(g["any_day_dropped"].mean()), "min_days_used": int(g["n_days_used"].min())})
    pd.DataFrame(rows).to_csv(OUT / "part1_exposure_in_completed_batches.csv", index=False)
    # ---- Part 2: real-sample coverage (counting only)
    tabs = load_tables(ROOT / "data" / "clean")
    r2 = []
    for mk in ("NSE", "US"):
        syms = [s for s in tabs if market_for_symbol(s).name == mk]
        panels = [h1_rms.mean_square_panel(tabs[s], mk) for s in syms]
        pos, nd = kept_positions(panels)
        share, ns, nw = span_stats(pos)
        pa, pb = sample_affected(pos, np.random.default_rng(MASTER_SEED))
        r2.append({"market": mk, "trading_dates_in_sample": nd, "complete_days_kept": len(pos),
                   "days_dropped": nd - len(pos), "dropped_positions": str(sorted(set(range(nd)) - set(pos.tolist()))),
                   "windows_spanning_gap": ns, "windows_total": nw, "share_windows_spanning": share,
                   "share_boot_samples_with_gap_block(as_run)": pa, "share_blocks_spanning": pb})
    pd.DataFrame(r2).to_csv(OUT / "part2_real_sample_coverage_counts.csv", index=False)
    # ---- Part 3: sensitivity experiment (simulated)
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    seeds = iter(np.random.SeedSequence(MASTER_SEED).spawn(100000))
    nxt = lambda: int(next(seeds).generate_state(1)[0])
    sims, rows3 = [], []
    with ProcessPoolExecutor() as pool:
        for mk in ("NSE", "US"):
            for scen in ("DEP X3", "DEP X4"):
                df = pd.DataFrame(list(pool.map(sens_sim, [(nxt(), mk, scen) for _ in range(n)], chunksize=4)))
                df.insert(0, "scenario", scen); df.insert(1, "market", mk)
                sims.append(df)
                for drop in (0, 4, 8):
                    for kind in ("rom", "diff"):
                        for variant in ("ignore", "aware"):
                            for rule in ("bonf", "max"):
                                k = int(df[f"drop{drop}|{kind}|{variant}|{rule}"].sum())
                                lo, hi = base.wilson(k, len(df))
                                rows3.append({"scenario": scen, "market": mk, "days_removed": drop, "test": kind,
                                              "gap_handling": variant, "rule": rule, "n_sims": len(df),
                                              "rejection_rate": k / len(df), "ci95_low": lo, "ci95_high": hi,
                                              "share_windows_spanning": df[f"drop{drop}_share_windows_spanning"].mean(),
                                              "share_boot_samples_affected": df[f"drop{drop}_share_boot_samples_affected"].mean()})
                print(mk, scen, "done", flush=True)
    pd.concat(sims).to_csv(OUT / "part3_sensitivity_per_simulation.csv", index=False)
    pd.DataFrame(rows3).to_csv(OUT / "part3_sensitivity_summary.csv", index=False)
    pd.Series({"master_seed": MASTER_SEED, "n_sims_per_cell": n, "B": B, "block": BLOCK,
               "note": "Part 3 ALL DATA SIMULATED; Part 2 is a coverage count of the real sample, no test run"}).to_csv(
        OUT / "run_metadata.csv", header=["value"])
    print("COMPLETE", flush=True)


if __name__ == "__main__":
    main()
