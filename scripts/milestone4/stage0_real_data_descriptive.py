"""H1 calibration, STAGE 0: DESCRIPTIVE tail-weight and shape summaries of the cleaned sample (data/clean, read-only).

NO hypothesis test is run and NO between-period comparison of volatility is made. Standardised bar shocks (each return divided
by a slot scale and a robust day scale) are summarised by tail statistics, and the SAME statistics are computed on simulated worlds
with KNOWN Student-t tails pushed through the SAME standardisation, so that the observed numbers can be read against a reference
(the Hill estimator is biased at this sample size, and volatility clustering inside a day or price rounding can also fatten tails).
These are descriptive estimates of a ~59-day sample, NOT statistical conclusions about market tails.
Output: outputs/milestone4/h1_calibration/stage0/real_data_descriptive/
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from quantlab.calendars import NSE, US, expected_slots, market_for_symbol     # noqa: E402
from quantlab.eda.masks import assign_period                                  # noqa: E402
from quantlab.research import direct_sim as ds, h1_calibration as hc          # noqa: E402
from quantlab.research.panel import load_tables                               # noqa: E402
from quantlab.research.tail_descriptives import tail_summary                  # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "h1_calibration" / "stage0" / "real_data_descriptive"
MAIN = ["open", "middle", "close"]
SEED = 20261102
DFS = [3, 4, 5, 6, 8, 10, 20, 1000]
REPS = 200
STATS = ["kurtosis", "max_abs_z", "share_abs_z_gt_3_per_1000", "share_abs_z_gt_4_per_1000", "share_abs_z_gt_5_per_1000",
         "hill_alpha_top1pct", "hill_alpha_top2pct", "hill_alpha_top5pct", "hill_alpha_top10pct"]


def real_array(tabs, market):
    labels = list(expected_slots(market, "2026-08-03").strftime("%H:%M"))
    syms = sorted(s for s in tabs if market_for_symbol(s).name == market.name)
    dates = sorted(set().union(*[set(tabs[s]["date"]) for s in syms]))
    arr = np.full((len(syms), len(dates), len(labels)), np.nan)
    for i, s in enumerate(syms):
        t = tabs[s]
        t = t[(t["status"] == "ok") & t["period"].isin(MAIN) & np.isfinite(t["ret"])]
        di = pd.Index(dates).get_indexer(t["date"])
        si = pd.Index(labels).get_indexer(t["slot"])
        keep = (di >= 0) & (si >= 0)
        arr[i, di[keep], si[keep]] = t["ret"].to_numpy()[keep] ** 2
    return arr, syms, dates


def by_scope(model):
    out = {"all": tail_summary(model.e2)}
    for name, gp in zip(MAIN, model.groups):
        out[name] = tail_summary(model.e2[:, :, gp])
    return out


def main():
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files.")
    OUT.mkdir(parents=True, exist_ok=True)
    tabs = load_tables(ROOT / "data" / "clean")
    kids = iter(hc.child_seeds(SEED, 100000))
    real_rows, ref_rows, match_rows = [], [], []
    for market in (NSE, US):
        idx = ds.used_slot_index(market)
        full, syms, dates = real_array(tabs, market)
        r2, groups = hc.to_used(full, idx)
        miss = float(np.mean(~np.isfinite(r2)))
        model = hc.fit_bar_model(r2, groups)
        real = by_scope(model)
        lg = np.log(model.g)
        meta = {"market": market.name, "symbols": ",".join(syms), "days": len(dates), "used_slots": r2.shape[2],
                "share_used_bars_missing": miss, "sd_log_day_scale": float(np.nanstd(lg))}
        for scope, d in real.items():
            for k, v in d.items():
                real_rows.append({"market": market.name, "scope": scope, "statistic": k, "value": v, **meta})
        order = np.concatenate(idx)
        profile = np.full(market.bars_per_day, np.sqrt(np.nanmean(model.v2)))
        profile[order] = np.sqrt(model.v2)
        for df in DFS:
            res = {sc: [] for sc in real}
            for _ in range(REPS):
                rng = np.random.default_rng(next(kids))
                sim = ds.simulate_returns_sq(market, len(syms), len(dates), rng, profile=profile, df=float(df), day_vol_sd=0.3)
                sr2, sg = hc.to_used(sim, idx)
                for sc, d in by_scope(hc.fit_bar_model(sr2, sg)).items():
                    res[sc].append(d)
            for sc, lst in res.items():
                f = pd.DataFrame(lst)
                for k in STATS:
                    q = f[k].quantile([.05, .5, .95])
                    ref_rows.append({"market": market.name, "scope": sc, "true_df": df, "statistic": k, "ref_mean": f[k].mean(),
                                     "ref_q05": q.iloc[0], "ref_q50": q.iloc[1], "ref_q95": q.iloc[2], "reps": REPS})
                    obs = real[sc][k]
                    match_rows.append({"market": market.name, "scope": sc, "statistic": k, "true_df": df, "observed": obs,
                                       "inside_ref_5_95": bool(q.iloc[0] <= obs <= q.iloc[2]),
                                       "observed_percentile_in_ref": float((f[k] < obs).mean())})
        print(market.name, "done", flush=True)
    pd.DataFrame(real_rows).to_csv(OUT / "real_tail_statistics.csv", index=False)
    pd.DataFrame(ref_rows).to_csv(OUT / "reference_known_df_distribution.csv", index=False)
    m = pd.DataFrame(match_rows)
    m.to_csv(OUT / "observed_vs_reference.csv", index=False)
    summ = (m[m.scope == "all"].groupby(["market", "statistic"]).apply(
        lambda x: ",".join(str(d) for d in x[x.inside_ref_5_95].true_df)).rename("true_df_values_whose_5_95_range_contains_observed"))
    summ.reset_index().to_csv(OUT / "df_equivalence_summary_all_periods.csv", index=False)
    pd.Series({"master_seed": SEED, "reps_per_df": REPS, "dfs": str(DFS), "day_vol_sd_in_reference": 0.3,
               "note": "descriptive only; no hypothesis test; reference worlds have no volatility clustering inside a day, "
                       "no price rounding, no cross-stock dependence of shocks"}).to_csv(OUT / "run_metadata.csv", header=["value"])
    print("COMPLETE", flush=True)


if __name__ == "__main__":
    main()
