"""H1 calibration, STAGE 3 planning tables: row-by-row plan of the frozen validation grid with seeds, roles, C3 value source, D2 reference and runtime estimate.
Reads frozen files + the Stage 0 benchmark; runs NO simulation; writes only NEW files.   Output: outputs/milestone4/h1_calibration/stage3_plan/
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage3_common as c3c                                                # noqa: E402
from quantlab.research import h1_stage2 as s2, h1_stage3 as s3             # noqa: E402

OUT = c3c.B / "stage3_plan"


def main():
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files.")
    OUT.mkdir(parents=True, exist_ok=True)
    v = c3c.load_validation_cells()
    dev = pd.read_csv(c3c.B / "frozen_spec" / "cells_development.csv", keep_default_na=False)
    assert len(v) == 96 and int(v.n_sims.sum()) == 2_280_000
    p = v.copy()
    p.insert(0, "val_row", p.index)
    p["kind"] = np.where(p.val_row < s3.NEW_FIRST_ROW, "development cell re-run, fresh seeds", "new intermediate cell")
    p["master_seed"] = [s3.val_master(r) for r in p.val_row]
    p["stage2_dev_row"] = [r if r < s3.NEW_FIRST_ROW else -1 for r in p.val_row]
    p["role"] = np.where(p.tier == "C", "report_only_df3", "gated_c3_upper_limit")
    p["c3_value_source"] = np.where(p.n_days.isin([59, 125, 250]), "Stage 2 frozen table (c3_critical_values.csv)", "Stage 3 intermediate table (seed 20261209)")
    refs = [s3.reference_row(v, r) for r in p.val_row]
    p["d2_reference_row"] = [-1 if r is None else r for r in refs]
    p["d2_reference_matched_on_dependence_volatility"] = [(row.dependence == "none" and abs(float(row.day_vol_sd) - 0.3) < 1e-12) for row in p.itertuples()]
    p.drop(columns=["origin"]).to_csv(OUT / "stage3_cells_plan.csv", index=False)
    # C3 value usage and seeds
    pd.DataFrame([dict(purpose="validation, re-run development cells (rows 0-75)", master=s3.MASTER["validation_cells"], spawn_key="(val_row, i, stream)", streams="0 data, 1 baseline"),
                  dict(purpose="validation, new intermediate cells (rows 76-95)", master=s3.MASTER["validation_intermediate"], spawn_key="(val_row, i, stream)", streams="0 data, 1 baseline"),
                  dict(purpose="C3 training at 90 and 180 days (24 cells x 25,000)", master=s3.MASTER["c3_intermediate"], spawn_key="(row, i)", streams="T only"),
                  dict(purpose="validation power cells (only if calibration passes)", master=s3.MASTER["validation_power"], spawn_key="(power_cell, i, stream)", streams="0 data, 1 baseline")]
                 ).to_csv(OUT / "stage3_seed_scheme.csv", index=False)
    # runtime estimate: data + baseline bootstrap-t (C3 costs ~0); single-core benchmark / measured speed-up, plus the Stage 1 per-simulation overhead
    t = pd.read_csv(c3c.B / "stage0" / "benchmark" / "single_core_timing.csv")
    g = lambda task, nd: 1000 * float(t[(t.task == task) & (t.n_days == nd)].median_s.iloc[0])
    base = lambda nd: g("generate data (fast generator)", nd) + g("base bootstrap-t, B=999 (M4b method)", nd)
    f = lambda nd: base(nd) if nd in (59, 125, 250) else base(59) + (base(250) - base(59)) * (nd - 59) / 191
    p["ms_per_sim_single_core"] = [f(int(n)) + 2.0 for n in p.n_days]                 # + about 2 ms per-simulation overhead seen in Stage 1
    hours = float((p.n_sims * p.ms_per_sim_single_core).sum() / 1000 / 4.0 / 3600)
    inter = 24 * 25_000 * g("generate data (fast generator)", 125) / 1000 / 4.0 / 3600
    pd.DataFrame([dict(item="validation run (data + baseline reference + C3)", simulations=int(p.n_sims.sum()), est_wall_hours=hours),
                  dict(item="C3 training at 90/180 days (data + T only)", simulations=600_000, est_wall_hours=max(inter, 0.05)),
                  dict(item="validation power cells (6 x 5,000, baseline + C3)", simulations=30_000, est_wall_hours=30_000 * (base(59) + 2.0) / 1000 / 4.0 / 3600)]).to_csv(OUT / "stage3_runtime_estimate.csv", index=False)
    print(p.groupby(["kind", "role", "tier"]).agg(cells=("tail", "size"), sims=("n_sims", "sum")).to_string())
    print("D2 reference available for", int((p.d2_reference_row >= 0).sum()), "of 96 cells;", int((p.d2_reference_row < 0).sum()), "have none (90/180 days, D1.5/D3.0)")
    print(pd.read_csv(OUT / "stage3_runtime_estimate.csv").round(2).to_string(index=False))
    assert len({*s3.all_registered_masters().values()}) == len(s3.all_registered_masters())


if __name__ == "__main__":
    main()
