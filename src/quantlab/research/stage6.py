"""STAGE 6 helpers (docs/42): dependence stress test of the frozen C3, a power curve, and a real-data placebo. Pure functions.

Parts A and B use SIMULATED data only; part C reuses the three real samples already tested (no new data). Nothing frozen is changed: C3 critical values,
the H1 statistic, the gates and the seeds of earlier stages are only read. New master seeds (not in the earlier registry): 20261401 (A), 20261402 (B), 20261403 (C).

  A  size under dependence : H0 true (open = middle = close volatility), 96 cells = 2 markets x 2 shapes x 2 tails x 2 sample sizes x 6 dependence levels.
  B  power curve           : H1 true (open and close volatility = mult x middle), 120 cells = 2 markets x 5 sample sizes x 6 multipliers x 2 dependence levels.
  C  real-data placebo     : the slot labels of each real session are randomly permuted (group sizes kept), so every period has the same expected variance.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import h1_calibration as hc
from .h1_calibration_v11 import classify_cell, wilson_interval

MASTER = {"size": 20261401, "power": 20261402, "placebo": 20261403}
STREAM = {"data": 0, "baseline": 1}
TIER_OF_TAIL = {"T6": "A", "T4": "B"}                  # tier A: df 6 (limit 5.5%); tier B: df 4 (limit 6.0%)
MARKETS = ("NSE", "US")
SIZE_SHAPES = ("R2", "E")
SIZE_TAILS = ("T6", "T4")
SIZE_N = (59, 125)
POWER_N = (59, 90, 125, 180, 250)
POWER_MULTS = (1.05, 1.10, 1.20, 1.30, 1.50, 2.00)
POWER_DEPS = ("S0_none", "S2_fresh_point")
N_SIMS_SIZE = 25000
N_SIMS_POWER = 10000
N_PLACEBO = 10000
POWER_TARGET = 0.80

# (ret_corr, share, phi). S1 is the market's earlier "estimated" value (run_h1_next.EMP_DEP, used in the frozen validation grid).
# S2 and S3 are the US fresh sample measurements of Phase 6 (docs/41): point estimate and the upper end of its +-2 standard-error interval.
# S4 is 1.5 x S2 (the Phase 6 "outside" line). S5 is the earlier illustrative stress value (run_h1_next.ILLUSTRATIVE_DEP).
LEVELS = {
    "S0_none": dict(ret_corr=0.0, share=0.0, phi=0.0),
    "S1_validated": {"NSE": dict(ret_corr=0.355, share=0.454, phi=0.441), "US": dict(ret_corr=0.187, share=0.141, phi=0.190)},
    "S2_fresh_point": dict(ret_corr=0.24, share=0.30, phi=0.42),
    "S3_fresh_upper": dict(ret_corr=0.29, share=0.50, phi=0.61),
    "S4_one_and_half_x": dict(ret_corr=0.36, share=0.45, phi=0.63),
    "S5_illustrative": dict(ret_corr=0.5, share=0.7, phi=0.7),
}
GATED_LEVELS = ("S0_none", "S1_validated", "S2_fresh_point", "S3_fresh_upper")      # S4 and S5 are reported, never gated


def dependence_for(level: str, market: str) -> dict:
    """The three dependence parameters of a level in a market."""
    d = LEVELS[level]
    return dict(d[market]) if market in d else dict(d)


def size_cells() -> pd.DataFrame:
    """The 96 part-A cells, in fixed order (row index = cell row, used in the seed)."""
    rows = []
    for mk in MARKETS:
        for shape in SIZE_SHAPES:
            for tail in SIZE_TAILS:
                for n in SIZE_N:
                    for lv in LEVELS:
                        rows.append({"market": mk, "shape": shape, "tail": tail, "tier": TIER_OF_TAIL[tail], "n_days": n, "level": lv,
                                     **dependence_for(lv, mk), "gated": lv in GATED_LEVELS, "n_sims": N_SIMS_SIZE})
    df = pd.DataFrame(rows)
    df.insert(0, "row", range(len(df)))
    return df


def power_cells() -> pd.DataFrame:
    """The 120 part-B cells (shape R2, tail T4), in fixed order."""
    rows = []
    for mk in MARKETS:
        for n in POWER_N:
            for lv in POWER_DEPS:
                for m in POWER_MULTS:
                    rows.append({"market": mk, "shape": "R2", "tail": "T4", "n_days": n, "level": lv, **dependence_for(lv, mk), "mult": m, "n_sims": N_SIMS_POWER})
    df = pd.DataFrame(rows)
    df.insert(0, "row", range(len(df)))
    return df


def size_seed(row: int, i: int, stream: str) -> np.random.SeedSequence:
    return np.random.SeedSequence(MASTER["size"], spawn_key=(int(row), int(i), STREAM[stream]))


def power_seed(row: int, i: int) -> np.random.SeedSequence:
    return np.random.SeedSequence(MASTER["power"], spawn_key=(int(row), int(i)))


def placebo_rng(sample_index: int) -> np.random.Generator:
    return np.random.default_rng(np.random.SeedSequence(MASTER["placebo"], spawn_key=(int(sample_index),)))


def size_status(k: int, n: int, tail: str) -> dict:
    """Frozen v1.1 A2 status of one C3 cell (point rule: rate <= 5.5% for tier A, <= 6.0% for tier B)."""
    return classify_cell(int(k), int(n), TIER_OF_TAIL[tail], c3_mode=True)


def part_a_outcome(cells: pd.DataFrame) -> str:
    """Pre-registered label from the GATED cells only: STRESS_PASS (every one PASS), STRESS_MARGINAL (no FAIL, some PASS_AMBIGUOUS),
    STRESS_BOUNDARY (no clear FAIL, some FAIL_AMBIGUOUS), STRESS_FAIL (some FAIL)."""
    st = list(cells.loc[cells["gated"], "status"])
    if "FAIL" in st:
        return "STRESS_FAIL"
    if "FAIL_AMBIGUOUS" in st:
        return "STRESS_BOUNDARY"
    if "PASS_AMBIGUOUS" in st:
        return "STRESS_MARGINAL"
    return "STRESS_PASS"


def min_detectable(mults, powers, target: float = POWER_TARGET) -> dict:
    """Smallest open/close multiplier with power >= target on the grid: the first grid point, or a linear interpolation in log(mult) between the
    grid point below the target and the first one at or above it. Returns {'value', 'kind'} with kind in 'at_or_below_first', 'interpolated', 'not_reached'."""
    m, p = np.asarray(mults, float), np.asarray(powers, float)
    order = np.argsort(m)
    m, p = m[order], p[order]
    hit = np.flatnonzero(p >= target)
    if hit.size == 0:
        return {"value": float(m[-1]), "kind": "not_reached"}
    j = int(hit[0])
    if j == 0:
        return {"value": float(m[0]), "kind": "at_or_below_first"}
    f = (target - p[j - 1]) / (p[j] - p[j - 1])
    return {"value": float(np.exp(np.log(m[j - 1]) + f * (np.log(m[j]) - np.log(m[j - 1])))), "kind": "interpolated"}


def permute_slots(r2_used: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Part C: independently permute the used slots of every session (same permutation for all stocks of a session); NaN-free input expected."""
    s, d, k = r2_used.shape
    perms = np.argsort(rng.random((d, k)), axis=1)
    return np.take_along_axis(r2_used, perms[None, :, :], axis=2)


def placebo_statistics(r2_sel: np.ndarray, groups: list[np.ndarray], rng: np.random.Generator, n_rep: int = N_PLACEBO) -> np.ndarray:
    """T of the frozen H1 statistic for n_rep random slot relabelings of the selected (complete) sessions."""
    if not np.isfinite(r2_sel).all():
        raise ValueError("placebo needs complete sessions only")
    out = np.empty(n_rep)
    for r in range(n_rep):
        out[r] = float(hc.max_abs_t(hc.market_matrix_from_r2(permute_slots(r2_sel, rng), groups)))
    return out


def placebo_summary(T: np.ndarray, crit: float) -> dict:
    """Rejection rate of the placebo statistics at the frozen critical value, with its Wilson interval."""
    k, n = int((T > crit).sum()), int(len(T))
    lo, hi = (float(x) for x in wilson_interval(k, n))
    return {"n_rep": n, "n_reject": k, "rate": k / n, "wilson_low": lo, "wilson_high": hi, "T_median": float(np.median(T)), "T_p95": float(np.quantile(T, 0.95)),
            "T_max": float(T.max()), "crit": float(crit)}
