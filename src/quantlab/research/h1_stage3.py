"""H1 calibration, STAGE 3 helpers (locked validation of the single candidate C3).   SIMULATED DATA ONLY.   New file; nothing frozen is changed.

Stage 3 = the frozen 96-cell validation grid (cells_validation.csv): the 76 development cells re-run with FRESH seeds (master 20261204) plus 20 new
intermediate cells (master 20261205). The candidate is C3 only (a fixed critical value per sample size, never retuned); the M4b baseline is run on the same
datasets as a reference. C1 is not run (the user designated C3 as the sole candidate). C2 is not run.

Fill-ins that the frozen text leaves open (all recorded in docs/20 BEFORE the run):
  * D1.5 and D3.0 are exp(-j/tau) profiles with tau = 1.5 and 3.0 (D5 uses tau = 2.0), same normalisation as D5.
  * T7 = Student-t(7).
  * C3 at 90 and 180 days is trained as in v1.1 A5: seed 20261209, SeedSequence(20261209, spawn_key=(row, i)), row = row of cells_c3_training_intermediate.csv.
  * Per-simulation seeds: SeedSequence(master, spawn_key=(validation_row, i, stream)), stream 0 = data, 1 = baseline bootstrap.
  * Power cells (run only if calibration passes): new master seed 20261213.
"""
from __future__ import annotations

import numpy as np

from . import h1_stage1 as s1
from . import h1_stage2 as s2

MASTER = {"validation_cells": 20261204, "validation_intermediate": 20261205, "c3_intermediate": 20261209, "validation_power": 20261213}
NEW_FIRST_ROW = 76                                         # rows 0-75 = development cells re-run; rows 76-95 = new intermediate cells
STREAM = {"data": 0, "baseline": 1}
DF_CODE = {**s1.DF_CODE, "T7": 7.0}
EXP_TAU = {"D1.5": 1.5, "D3.0": 3.0}                       # decay scales of the two new shapes (D5 is 2.0)


def all_registered_masters() -> dict:
    """Every master seed of the programme, Stage 1-2 plus the one new Stage 3 seed."""
    return {**s2.RESERVED_MASTERS, "validation_power": MASTER["validation_power"]}


def val_master(row: int) -> int:
    """Master seed of validation row `row`: 20261204 for the 76 re-run development cells, 20261205 for the 20 new cells."""
    return MASTER["validation_cells"] if int(row) < NEW_FIRST_ROW else MASTER["validation_intermediate"]


def val_seed(row: int, i: int, stream: str) -> np.random.SeedSequence:
    """Seed of one stream ('data' or 'baseline') of simulation i of validation row `row`."""
    return np.random.SeedSequence(val_master(row), spawn_key=(int(row), int(i), STREAM[stream]))


def c3i_seed(row: int, i: int) -> np.random.SeedSequence:
    """Seed of simulation i of row `row` of the 90/180-day C3 training cells (statistic T only)."""
    return np.random.SeedSequence(MASTER["c3_intermediate"], spawn_key=(int(row), int(i)))


def power_seed(power_cell: int, i: int, stream: str) -> np.random.SeedSequence:
    """Seed of one stream of simulation i of Stage 3 power cell `power_cell` (master 20261213)."""
    return np.random.SeedSequence(MASTER["validation_power"], spawn_key=(int(power_cell), int(i), STREAM[stream]))


def c3_value(n_days: int, stage2_table: dict, intermediate_table: dict) -> float:
    """Frozen C3 critical value for a sample size: 59/125/250 from the Stage 2 table, 90/180 from the intermediate training table."""
    n = int(n_days)
    if n in stage2_table:
        return float(stage2_table[n])
    if n in intermediate_table:
        return float(intermediate_table[n])
    raise KeyError(f"no frozen C3 value for {n} days")


def reference_row(cells, row: int):
    """Row of the df-infinity cell with the same shape, market and sample size (dependence none, day-volatility 0.3) in the validation grid, or None."""
    c = cells.iloc[row]
    m = cells[(cells["tail"] == "G") & (cells["shape"] == c["shape"]) & (cells["market"] == c["market"]) & (cells["n_days"] == c["n_days"])
              & (cells["dependence"] == "none") & (cells["day_vol_sd"].astype(float) == 0.3)]
    return None if m.empty else int(m.index[0])
