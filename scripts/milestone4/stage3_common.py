"""H1 calibration, STAGE 3: shared pieces (manifest checks, cell set-up with the two new shapes, one-simulation function).
Reads the frozen cells_validation.csv and the frozen manifests; writes nothing.   ALL DATA SIMULATED.   Candidate = C3 only; baseline = reference only.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage2_common as sc                                                 # noqa: E402
from quantlab.research import direct_sim as ds, h1_calibration as hc, h1_stage1 as s1, h1_stage3 as s3   # noqa: E402
from quantlab.research.h1_rms2 import bootstrap_t                          # noqa: E402
import run_h1_inference as ri                                             # noqa: E402
import run_h1_next as nx                                                  # noqa: E402

B = sc.BASE
S3 = B / "stage3"
VALIDATION_CELLS = B / "frozen_spec" / "cells_validation.csv"
C3_INTERMEDIATE_CELLS = B / "frozen_spec_v1_1" / "cells_c3_training_intermediate.csv"
STAGE3_INPUTS = B / "frozen_stage3_inputs.sha256"
STAGE2_C3_TABLE = B / "stage2" / "c3_training" / "c3_critical_values.csv"
C3I_TABLE = S3 / "c3_intermediate" / "c3_intermediate_values.csv"
verify_manifest, sha256 = sc.verify_manifest, sc.sha256


def verify_all(stage3_inputs: bool = True, c3_intermediate: bool = False) -> dict:
    """Frozen v1, v1.1, Stage 1, Stage 2 manifests (+ optional Stage 3 inputs and the frozen 90/180-day C3 table); also the free-disk check."""
    out = sc.verify_all(require_stage2_inputs=True)
    out["stage2_addendum"] = verify_manifest(B / "frozen_stage2_inputs_addendum.sha256")
    out["stage2_c3_table"] = verify_manifest(B / "stage2" / "c3_training" / "C3_TABLE.sha256", 2)
    if stage3_inputs:
        out["stage3_inputs"] = verify_manifest(STAGE3_INPUTS)
    if c3_intermediate:
        out["c3_intermediate_table"] = verify_manifest(S3 / "c3_intermediate" / "C3_INTERMEDIATE_TABLE.sha256", 2)
    return out


def load_validation_cells() -> pd.DataFrame:
    """The frozen 96-cell validation grid (row index = validation row, never modified)."""
    return pd.read_csv(VALIDATION_CELLS, keep_default_na=False)


def cell_setup(cell: dict, mult: float = 1.0) -> dict:
    """Market, used slots, profile (including the new D1.5 / D3.0 shapes), df, day-volatility and dependence for one cell."""
    mk, shape = cell["market"], cell["shape"]
    market = sc.MARKETS[mk]
    profile = nx.exp_profile(market, s3.EXP_TAU[shape], mult) if shape in s3.EXP_TAU else ri.profile_for(mk, shape, mult)
    dep = nx.EMP_DEP[mk] if cell["dependence"] == "estimated" else dict(share=0.0, phi=0.0, ret_corr=0.0)
    return dict(market=market, idx=ds.used_slot_index(market), profile=profile, df=s3.DF_CODE[cell["tail"]], day_vol_sd=float(cell["day_vol_sd"]),
                n_days=int(cell["n_days"]), share=dep["share"], phi=dep["phi"], ret_corr=dep["ret_corr"])


def simulate_one(setup: dict, seed_fn, crit_c3: float, B: int = 999) -> dict:
    """One dataset; the baseline bootstrap-t (reference) and C3 applied to it. A failing method is marked invalid, never dropped."""
    r2 = sc.generate(setup, np.random.default_rng(seed_fn("data")))
    M = ds.period_matrix(r2, setup["idx"])
    r2_used, groups = hc.to_used(r2, setup["idx"])
    out = {}
    try:
        out["T"] = float(hc.max_abs_t(M))
    except Exception:
        out["T"] = float("nan")
    try:
        res = bootstrap_t(M, np.random.default_rng(seed_fn("baseline")), "rom", B=B)
        ok = bool(np.isfinite(res["t"]).all() and np.isfinite(res["crit_max"]))
        out.update(valid_base=ok, reject_base=bool(res["reject_max"]) if ok else False, crit_base=float(res["crit_max"]))
    except Exception:
        out.update(valid_base=False, reject_base=False, crit_base=float("nan"))
    ok = bool(np.isfinite(out["T"]) and np.isfinite(crit_c3))
    out.update(valid_c3=ok, reject_c3=bool(out["T"] > crit_c3) if ok else False, crit_c3=float(crit_c3))
    try:
        out.update(s1.tail_diagnostics([r2_used[:, :, g] for g in groups], M))
    except Exception:
        out.update(kurt=float("nan"), maxshare=float("nan"), maxshare_open=float("nan"), maxshare_middle=float("nan"), maxshare_close=float("nan"))
    return out


def statistic_only(setup: dict, rng) -> float:
    """C3 training: T of one dataset (NaN on failure)."""
    return sc.statistic_only(setup, rng)
