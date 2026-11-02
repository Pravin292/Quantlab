"""Validate the fast generator (direct_sim.py) against the original bar-level pipeline.   ALL SIMULATED.

Part exact:   feed the SAME returns to both routes (direct_bridge.py) and compare the H1 market matrices.
              (Identical SEEDS cannot give identical numbers: the two generators consume random numbers differently.)
Part stat:    compare rejection rates of the SAME tests (B = 1999) on the SAME scenarios from the earlier bar-level runs
              (outputs/milestone4/next_round/h1_calib) with the fast-generator runs (outputs/milestone4/m4b/h1_cand):
              two-proportion z-tests. Different random streams, so only statistical agreement can be expected.
Writes outputs/milestone4/m4b/verification/.
Usage: python scripts/milestone4/validate_fast_simulator.py exact|stat
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))
from quantlab.research import direct_sim as ds, h1_rms                       # noqa: E402
from quantlab.research.direct_bridge import returns_to_table                  # noqa: E402
import run_h1_inference as ri                                                # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "m4b" / "verification"
OUT.mkdir(parents=True, exist_ok=True)


def exact():
    rows = []
    for mk in ("NSE", "US"):
        m = ri.MARKETS[mk]
        for name in ("T4 flat", "T4 E", "G E", "T4 D5", "T4 R2", "T4 E dep", "T4 E x1.2", "T6 Etau2.0"):
            spec = ri.parse(name, mk, 59)
            for seed in range(10):
                rng = np.random.default_rng(1000 + seed)
                r2 = ds.simulate_returns_sq(m, ri.N_STOCKS, 59, rng, profile=spec["profile"], df=spec["df"],
                                            day_vol_sd=spec["day_vol_sd"], share=spec["share"], phi=spec["phi"], ret_corr=spec["ret_corr"])
                Md = ds.period_matrix(r2, ds.used_slot_index(m))
                tabs = [returns_to_table(m, np.sqrt(r2[i]), f"S{i}", rng, nse_feed_quirks=True) for i in range(ri.N_STOCKS)]
                Mp = h1_rms.market_matrix([h1_rms.mean_square_panel(t, mk) for t in tabs])
                same_shape = Md.shape == Mp.shape
                rel = float(np.max(np.abs(Mp - Md) / Md)) if same_shape else np.nan
                rows.append({"market": mk, "scenario": name, "seed": 1000 + seed, "days_direct": len(Md), "days_pipeline": len(Mp),
                             "same_shape": same_shape, "max_relative_difference": rel})
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "fast_vs_bar_level_exact_matrix_comparison.csv", index=False)
    print(len(d), "comparisons; same shape:", int(d.same_shape.sum()), "; max rel diff:", d.max_relative_difference.max())


def stat():
    pipe = pd.read_csv(ROOT / "outputs/milestone4/next_round/h1_calib/h1_calib_per_simulation.csv")
    fast = pd.read_parquet(ROOT / "outputs/milestone4/m4b/h1_cand/h1_cand_per_simulation.parquet")
    pairs = [("E empirical-shape profile, t4", "T4 E"), ("D5 stress (exp decay tau=2), t4", "T4 D5"),
             ("D3 t4 + day factor, flat", "T4 flat"), ("R2 realistic strong (round 1), t4", "T4 R2"),
             ("POWER E x1.1", "T4 E x1.1"), ("POWER E x1.2", "T4 E x1.2")]
    cols = [("rom|B1999|blk1|max", "rom_t|max"), ("rom|B1999|blk1|bonf", "rom_t|bonf"),
            ("diff|B1999|blk1|max", "diff_t|max"), ("diff|B1999|blk1|bonf", "diff_t|bonf")]
    rows = []
    for mk in ("NSE", "US"):
        for sp, sf in pairs:
            for cp, cf in cols:
                a = pipe[(pipe.scenario == sp) & (pipe.market == mk)][cp].astype(bool)
                b = fast[(fast.scenario == sf) & (fast.market == mk)][cf].astype(bool)
                p1, p2, n1, n2 = a.mean(), b.mean(), len(a), len(b)
                pp = (a.sum() + b.sum()) / (n1 + n2)
                z = (p1 - p2) / np.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
                rows.append({"market": mk, "scenario_bar_level": sp, "scenario_fast": sf, "rule": cf, "n_bar_level": n1, "n_fast": n2,
                             "rate_bar_level": p1, "rate_fast": p2, "difference": p1 - p2, "z": z})
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "fast_vs_bar_level_rejection_rate_comparison.csv", index=False)
    pd.set_option("display.width", 220)
    print(d.round(3).to_string(index=False))
    print("cells:", len(d), "| |z|>2:", int((d.z.abs() > 2).sum()), "| |z|>3:", int((d.z.abs() > 3).sum()), "| mean diff:", round(d.difference.mean(), 4))


if __name__ == "__main__":
    {"exact": exact, "stat": stat}[sys.argv[1]]()
