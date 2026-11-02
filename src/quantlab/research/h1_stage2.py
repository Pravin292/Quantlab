"""H1 calibration, STAGE 2 helpers (new file; nothing frozen is changed).   SIMULATED DATA ONLY.

Implements the approved design decisions of docs/17b (D1-D10) as small, testable functions:
  seeds            one SeedSequence per (cell, simulation, stream); streams never shared between methods or stages
  C3 table         0.95 quantile of T per training cell and the maximum per sample size
  D2               conditional-calibration flag (judgement-based, NOT a statistical test) with the "reference not matched" label
  D4               ambiguous-cell count against the yardstick of 10 (a judgement value)
  D6               numerical-failure blocking (gated cells only)
  D7               critical-value variability rule scope and CV
  plumbing / paired checks
There is NO C2 code here (D9: C2 is not run in Stage 2).  Passing unit tests show the code does what its docstrings say; they are
not evidence that any method is statistically valid.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import stats

# ------------------------------------------------------------------------------------------------ seeds
MASTER = {"c3_training": 20261202, "development": 20261203, "power_check": 20261212}
RESERVED_MASTERS = {  # every master seed registered in the project for this programme; none may be reused across purposes
    "stage1": 20261201, "c3_training": 20261202, "development": 20261203, "validation_cells": 20261204, "validation_intermediate": 20261205,
    "alternative_dgps": 20261206, "bar_pipeline_check": 20261207, "reference_implementation_check": 20261208, "c3_intermediate_sizes": 20261209,
    "ambiguity_replication": 20261210, "development_revision": 20261211, "power_check": 20261212}
STREAM = {"data": 0, "baseline": 1, "c1": 2}            # k in spawn_key=(row, i, k); k = 3 (C2) is reserved and unused (D9)


def c3_seed(dev_row: int, i: int) -> np.random.SeedSequence:
    """Seed of simulation i of C3-training cell dev_row (statistic T only, one stream)."""
    return np.random.SeedSequence(MASTER["c3_training"], spawn_key=(int(dev_row), int(i)))


def dev_seed(dev_row: int, i: int, stream: str) -> np.random.SeedSequence:
    """Seed of one stream ('data', 'baseline', 'c1') of simulation i of development cell dev_row."""
    return np.random.SeedSequence(MASTER["development"], spawn_key=(int(dev_row), int(i), STREAM[stream]))


def power_seed(power_cell: int, i: int, stream: str) -> np.random.SeedSequence:
    """Seed of one stream of simulation i of power-check cell power_cell (master 20261212)."""
    return np.random.SeedSequence(MASTER["power_check"], spawn_key=(int(power_cell), int(i), STREAM[stream]))


# ------------------------------------------------------------------------------------------------ small statistics
def cv(x) -> float:
    """Coefficient of variation: standard deviation (ddof 1) divided by the mean, as in Stage 1."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    return float(x.std(ddof=1) / x.mean())


def quartile_rates(values: np.ndarray, reject: np.ndarray) -> np.ndarray:
    """Rejection rate within each quartile of `values` (lowest first); NaN entries if the values cannot be split into 4 groups."""
    v = pd.Series(np.asarray(values, dtype=float))
    r = np.asarray(reject, dtype=float)
    try:
        q = pd.qcut(v, 4, labels=False, duplicates="drop")
    except ValueError:
        return np.full(4, np.nan)
    if q.nunique() < 4:
        return np.full(4, np.nan)
    return np.array([r[(q == k).to_numpy()].mean() for k in range(4)])


def spread(rates: np.ndarray) -> float:
    """Quartile spread = max - min of the four rejection rates."""
    return float(np.nanmax(rates) - np.nanmin(rates))


# ------------------------------------------------------------------------------------------------ D2
D2_RATIO, D2_MIN_EXCESS = 1.25, 0.02          # JUDGEMENT-BASED diagnostic threshold (not a statistical theorem or test)
UNMATCHED_LABEL = "reference not matched on dependence / day-volatility"


def d2_flag(method_spread: float, reference_spread: float) -> bool:
    """D2: flag when the spread exceeds 1.25 x the reference spread by at least 2 percentage points.

    INTERPRETATION (to be confirmed by the user before the main run): 'exceeds 1.25 x reference by at least 2 points' is read as
    spread - 1.25 * reference >= 0.02 (the excess over the 1.25x threshold), the stricter of the two possible readings.
    """
    return bool(method_spread - D2_RATIO * reference_spread >= D2_MIN_EXCESS - 1e-12)


def reference_label(dependence: str, day_vol_sd: float) -> str:
    """'' when the df-infinity reference (no dependence, day-volatility 0.3) is fully matched; otherwise the required label."""
    return "" if (dependence == "none" and abs(day_vol_sd - 0.3) < 1e-12) else UNMATCHED_LABEL


def in_advancement_scope(tier: str, n_days: int) -> bool:
    """The 40 cells of D2 and D7: all 24 tier B cells plus the 16 tier A cells at 125 and 250 days."""
    return tier == "B" or (tier == "A" and n_days >= 125)


# ------------------------------------------------------------------------------------------------ D4 / D6
AMBIGUOUS_YARDSTICK = 10        # JUDGEMENT value: >= 10 ambiguous of the 44 tier A cells -> investigate (0.8% for an ideal method; assumes all cells at 5.0%, independent)
FAIL_RATE_LIMIT = 0.001


def failure_blocks(n_failed: int, n_total: int, gated: bool) -> bool:
    """D6: a gated method-cell is blocked when more than 0.1% of its simulations failed; ungated (df 3) cells are only flagged, never blocking."""
    return bool(gated and n_failed / n_total > FAIL_RATE_LIMIT + 1e-15)


def failure_flag(n_failed: int, n_total: int) -> bool:
    """D6: any cell (gated or not) above 0.1% failures is flagged."""
    return bool(n_failed / n_total > FAIL_RATE_LIMIT + 1e-15)


def ambiguous_flag(statuses: list[str]) -> bool:
    """D4: True when the number of ambiguous (PASS_AMBIGUOUS or FAIL_AMBIGUOUS) tier A cells reaches the yardstick."""
    return sum(s.endswith("_AMBIGUOUS") for s in statuses) >= AMBIGUOUS_YARDSTICK


def can_advance_cell_statuses(statuses: list[str]) -> bool:
    """D4: PASS and PASS_AMBIGUOUS are passes; any FAIL or FAIL_AMBIGUOUS blocks advancement."""
    return all(s in ("PASS", "PASS_AMBIGUOUS") for s in statuses)


# ------------------------------------------------------------------------------------------------ C3 table
def c3_cell_quantiles(T: np.ndarray) -> float:
    """0.95 quantile (linear interpolation) of the finite statistics of one training cell."""
    T = np.asarray(T, dtype=float)
    return float(np.quantile(T[np.isfinite(T)], 0.95))


def c3_table(cells: pd.DataFrame) -> pd.DataFrame:
    """Per sample size: the maximum over cells of the cell quantile q95 (columns: n_days, c3_crit, source_dev_row, n_cells)."""
    rows = []
    for nd, g in cells.groupby("n_days"):
        j = g["q95"].idxmax()
        rows.append({"n_days": int(nd), "c3_crit": float(g.loc[j, "q95"]), "source_dev_row": int(g.loc[j, "dev_row"]), "n_cells": len(g)})
    return pd.DataFrame(rows)


def quantile_se(T: np.ndarray, B: int = 200, seed: int = 0) -> float:
    """Bootstrap standard error of the 0.95 quantile of T (200 resamples; for reporting only)."""
    rng = np.random.default_rng(seed)
    T = np.asarray(T, dtype=float)
    T = T[np.isfinite(T)]
    return float(np.std([np.quantile(rng.choice(T, len(T)), 0.95) for _ in range(B)], ddof=1))


# ------------------------------------------------------------------------------------------------ checks
def plumbing_z(k1: int, n1: int, k2: int, n2: int) -> float:
    """Two-sample z statistic for the difference of two rejection rates (Stage 2 baseline vs Stage 1 baseline); 0 if both rates are equal."""
    p1, p2, p = k1 / n1, k2 / n2, (k1 + k2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return 0.0 if se == 0 else (p1 - p2) / se


def sign_test_p(b: int, c: int) -> float:
    """Exact two-sided sign test p-value for the discordant counts b and c of a paired comparison."""
    n = b + c
    return 1.0 if n == 0 else float(min(1.0, 2 * stats.binom.cdf(min(b, c), n, 0.5)))


def distance_to_bound_se(p_hat: float, n: int, lo: float, hi: float) -> float:
    """Distance of p_hat to the nearest gate bound in binomial standard errors (inf if p_hat is 0 or 1 and the bound is elsewhere)."""
    se = math.sqrt(max(p_hat * (1 - p_hat), 1e-12) / n)
    return min(abs(p_hat - lo), abs(p_hat - hi)) / se
