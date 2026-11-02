"""H1 calibration, STAGE 1: summarise the baseline run (reads the per-cell parquet files; runs no simulation; writes new CSVs).
ALL DATA SIMULATED. Gate outcomes are INFORMATIONAL for the baseline (see docs/15b section 6, item 5).
Output (same folder as the run): stage1_cell_summary.csv, stage1_hc_quartiles.csv, stage1_hb_effective_bars.csv, stage1_he_bootstrap_size.csv,
                                 stage1_count_check.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))

from quantlab.calendars import NSE, US                                   # noqa: E402
from quantlab.research import direct_sim as ds, h1_calibration_v11 as v11, h1_stage1 as s1   # noqa: E402
import run_h1_inference as ri                                            # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "h1_calibration" / "stage1"
CELLS = ROOT / "outputs" / "milestone4" / "h1_calibration" / "frozen_spec" / "cells_stage1.csv"
TIER = {"G": "A", "T20": "A", "T10": "A", "T8": "A", "T6": "A", "T5": "B", "T4": "B", "T3": "C"}


def main():
    cells = pd.read_csv(CELLS, keep_default_na=False)
    rows, quart, counts = [], [], []
    for i, c in cells.iterrows():
        d = pd.read_parquet(OUT / f"cell_{i:02d}.parquet")
        v = d[d["valid"]]
        k, n = int(v["reject"].sum()), len(v)
        cl = v11.classify_cell(k, n, TIER[c["tail"]] if TIER[c["tail"]] != "C" else "B")
        crit_cv = float(v["crit"].std() / v["crit"].mean())
        rho = float(stats.spearmanr(v["T"], v["crit"])[0])
        rows.append({"cell_row": i, "experiment": c["experiment"], "tail": c["tail"], "shape": c["shape"], "market": c["market"], "n_days": c["n_days"],
                     "merge": c["merge"], "B": c["B"], "n_planned": int(c["n_sims"]), "n_run": len(d), "n_failed": int((~d["valid"]).sum()), "n_valid": n,
                     "rejections": k, "rejection_rate": k / n, "wilson_low": cl["wilson_low"], "wilson_high": cl["wilson_high"],
                     "tier_informational": TIER[c["tail"]], "gate_status_informational": "REPORT_ONLY" if TIER[c["tail"]] == "C" else cl["status"],
                     "crit_mean": float(v["crit"].mean()), "crit_median": float(v["crit"].median()), "crit_cv": crit_cv, "spearman_T_crit": rho,
                     "kurt_mean": float(v["kurt"].mean()), "maxshare_mean": float(v["maxshare"].mean())})
        q = pd.qcut(v["crit"], 4, labels=False, duplicates="drop")
        for b, g in v.groupby(q):
            quart.append({"cell_row": i, "tail": c["tail"], "shape": c["shape"], "market": c["market"], "merge": c["merge"], "B": c["B"],
                          "crit_quartile": int(b) + 1, "n": len(g), "rejection_rate": float(g["reject"].mean())})
        counts.append({"cell_row": i, "n_planned": int(c["n_sims"]), "n_run": len(d), "unique_sim_ids": d["sim"].nunique(), "n_failed": int((~d["valid"]).sum())})
    summ = pd.DataFrame(rows)
    summ.to_csv(OUT / "stage1_cell_summary.csv", index=False)
    pd.DataFrame(quart).to_csv(OUT / "stage1_hc_quartiles.csv", index=False)
    pd.DataFrame(counts).to_csv(OUT / "stage1_count_check.csv", index=False)

    # HB: effective bar counts per cell (from the profile) next to the observed rejection rate
    eb = []
    for _, r in summ[summ["experiment"].str.startswith("HB")].iterrows():
        m = {"NSE": NSE, "US": US}[r["market"]]
        e = s1.effective_bar_counts(ri.profile_for(r["market"], r["shape"], 1.0), ds.used_slot_index(m), int(r["merge"]))
        eb.append({**{k: r[k] for k in ("tail", "shape", "market", "merge", "n_valid", "rejection_rate", "wilson_low", "wilson_high", "crit_cv")},
                   **{f"eff_bars_{k}": v for k, v in e.items()}})
    pd.DataFrame(eb).to_csv(OUT / "stage1_hb_effective_bars.csv", index=False)

    # HE: B = 999 vs 9999 (independent datasets), difference with a two-sample normal 95% interval
    he = summ[summ["experiment"].str.startswith("HE")]
    out = []
    for (sh, mk), g in he.groupby(["shape", "market"]):
        a, b = g[g["B"] == 999].iloc[0], g[g["B"] == 9999].iloc[0]
        se = np.sqrt(a.rejection_rate * (1 - a.rejection_rate) / a.n_valid + b.rejection_rate * (1 - b.rejection_rate) / b.n_valid)
        d = b.rejection_rate - a.rejection_rate
        out.append({"shape": sh, "market": mk, "rate_B999": a.rejection_rate, "rate_B9999": b.rejection_rate, "difference": d,
                    "diff_ci_low": d - 1.96 * se, "diff_ci_high": d + 1.96 * se, "n_each": int(a.n_valid)})
    pd.DataFrame(out).to_csv(OUT / "stage1_he_bootstrap_size.csv", index=False)
    print(summ[["cell_row", "tail", "shape", "market", "merge", "B", "n_valid", "n_failed", "rejection_rate", "gate_status_informational"]].round(4).to_string())


if __name__ == "__main__":
    main()
