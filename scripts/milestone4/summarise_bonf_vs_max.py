"""Paired comparison of the Bonferroni and max-|t| multiplicity rules on the SAME simulated datasets (h1_calib, h1_dep).
Writes next_round/h1_{calib,dep}/..._bonf_vs_max_paired.csv.  Also writes the analytic D5 bias arithmetic."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))
import run_diagnostics_h1 as base, run_h1_next as nx
from quantlab.calendars import NSE, US
NR = ROOT / "outputs" / "milestone4" / "next_round"
for part, cfgs in (("calib", [(1999, 1), (499, 1), (199, 1)]), ("dep", [(999, 1), (999, 5)])):
    d = pd.read_csv(NR / f"h1_{part}" / f"h1_{part}_per_simulation.csv")
    rows = []
    for (sc, mk), g in d.groupby(["scenario", "market"], sort=False):
        for kind in ("rom", "diff"):
            for B, blk in cfgs:
                a = g[f"{kind}|B{B}|blk{blk}|bonf"].astype(bool).to_numpy()
                m = g[f"{kind}|B{B}|blk{blk}|max"].astype(bool).to_numpy()
                n = len(g); b = int((a & ~m).sum()); c = int((~a & m).sum())
                lo1, hi1 = base.wilson(int(a.sum()), n); lo2, hi2 = base.wilson(int(m.sum()), n)
                rows.append({"scenario": sc, "market": mk, "test": kind, "B": B, "block_days": blk, "n_sims": n,
                             "bonf_rate": a.mean(), "bonf_lo": lo1, "bonf_hi": hi1, "max_rate": m.mean(), "max_lo": lo2, "max_hi": hi2,
                             "only_bonf_rejects": b, "only_max_rejects": c, "paired_diff_bonf_minus_max": (b - c) / n,
                             "paired_diff_se": float(np.sqrt(max(b + c - (b - c) ** 2 / n, 0)) / n)})
    pd.DataFrame(rows).to_csv(NR / f"h1_{part}" / f"h1_{part}_bonf_vs_max_paired.csv", index=False)
rows = []
for m, mk in ((NSE, "NSE"), (US, "US")):
    p = nx.exp_profile(m, 2.0)
    for per in ("open", "middle", "close"):
        v = p[base.used_slots(m, per)] ** 2
        n = len(v); rel = np.sum(v ** 2) / np.sum(v) ** 2
        rows.append({"market": mk, "period": per, "n_bars": n, "sum_v2_over_sum_v_squared": rel, "equal_variance_value_1_over_n": 1 / n,
                     "gaussian_second_order_bias_of_half_ln_ms_actual_weights": -(3 - 1) * rel / 4,
                     "same_if_bars_had_equal_variance": -(3 - 1) / n / 4})
pd.DataFrame(rows).to_csv(NR / "h1_d5" / "h1_d5_analytic_bias_arithmetic.csv", index=False)
print("ok")
