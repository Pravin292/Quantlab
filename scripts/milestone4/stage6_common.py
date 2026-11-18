"""STAGE 6 shared pieces (docs/42): frozen-input checks, C3 critical values, one-cell set-up. Reads frozen files; writes nothing.   Parts A and B: ALL DATA SIMULATED."""
import hashlib
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage3_common as c3c                                                # noqa: E402
from quantlab.research import h1_stage3 as s3, stage6 as s6                 # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "milestone4" / "stage6"
STAGE6_INPUTS = ROOT / "outputs" / "milestone4" / "frozen_stage6_inputs.sha256"


def verify_stage6_inputs() -> None:
    """Every file listed in frozen_stage6_inputs.sha256 must still hash to its recorded value."""
    bad = 0
    for line in STAGE6_INPUTS.read_text().splitlines():
        h, _, rel = line.partition("  ")
        if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != h:
            bad += 1
            print("MISMATCH", rel)
    if bad:
        sys.exit("frozen_stage6_inputs.sha256 mismatch: stop.")


def verify_all(smoke: bool = False) -> None:
    """All earlier frozen manifests (v1, v1.1, Stages 1-4, C3 tables) and, unless smoke, the Stage 6 manifest."""
    c3c.verify_all(stage3_inputs=True, c3_intermediate=True)
    if not smoke:
        verify_stage6_inputs()


def c3_crit(n_days: int) -> float:
    """Frozen C3 critical value for a sample size (59/125/250 from Stage 2, 90/180 from the Stage 3 intermediate table)."""
    t2 = pd.read_csv(c3c.STAGE2_C3_TABLE).set_index("n_days")["c3_crit"].to_dict()
    ti = pd.read_csv(c3c.C3I_TABLE).set_index("n_days")["c3_crit"].to_dict()
    return s3.c3_value(n_days, t2, ti)


def cell_setup(cell: dict, mult: float = 1.0) -> dict:
    """Stage 3 cell set-up with the Stage 6 dependence values written over the 'none' defaults."""
    setup = c3c.cell_setup(dict(tail=cell["tail"], shape=cell["shape"], market=cell["market"], n_days=int(cell["n_days"]), dependence="none", day_vol_sd=0.3), mult=mult)
    setup.update(share=float(cell["share"]), phi=float(cell["phi"]), ret_corr=float(cell["ret_corr"]))
    return setup
