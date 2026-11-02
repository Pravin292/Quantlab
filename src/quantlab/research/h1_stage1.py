"""H1 calibration, STAGE 1 helpers (new file; nothing frozen is changed).   ALL USED ON SIMULATED DATA ONLY, BASELINE METHOD ONLY.

Stage 1 asks why the M4b baseline (iid-day bootstrap-t, B = 999, max rule) over-rejects. It uses the validated fast generator of
direct_sim.py and adds only what v1 leaves undefined:
  * signed returns (the "merge g bars" experiment must add returns before squaring); with g = 1 the squares equal
    direct_sim.simulate_returns_sq exactly (tested);
  * the merge operation and its null-preserving constant (see docs/15b section 3);
  * per-simulation seeds  SeedSequence(master, spawn_key=(cell_row, simulation_index));
  * the per-simulation diagnostics saved for hypothesis HC (kurtosis, largest day share).
No candidate method (C1, C2, C3) appears here.
"""
from __future__ import annotations

import numpy as np

from . import direct_sim as ds
from .dependence import day_factors
from .h1_rms2 import bootstrap_t

# df code -> degrees of freedom. "G" keeps the M4b convention t(1000) (practically Gaussian); the spec text writes "df infinity".
DF_CODE = {"G": 1000.0, "T20": 20.0, "T10": 10.0, "T8": 8.0, "T6": 6.0, "T5": 5.0, "T4": 4.0, "T3": 3.0}


def sim_seed(master: int, cell_row: int, sim_index: int) -> np.random.SeedSequence:
    """Full-width seed of one simulation; equals SeedSequence(master, spawn_key=(cell_row,)).spawn(n)[sim_index]."""
    return np.random.SeedSequence(master, spawn_key=(int(cell_row), int(sim_index)))


def simulate_returns(market, n_stocks: int, n_days: int, rng: np.random.Generator, *, profile: np.ndarray, df: float, day_vol_sd: float = 0.3) -> np.ndarray:
    """SIGNED returns (stocks, days, slots) with the same random draws, in the same order, as direct_sim.simulate_returns_sq (no dependence)."""
    n = market.bars_per_day
    f = day_factors(n_days, n_stocks, day_vol_sd, 0.0, 0.0, rng)                 # day log-volatility factors
    eps = rng.standard_t(df, (n_stocks, n_days, n)) * np.sqrt((df - 2) / df)     # unit-variance Student-t shocks
    return np.asarray(profile)[None, None, :] * np.exp(f)[:, :, None] * eps


def merge_groups(n_slots: int, g: int, from_end: bool = False) -> list[np.ndarray]:
    """Positions 0..n_slots-1 split into consecutive groups of g; one group (the last, or the first if from_end) may be shorter."""
    groups = [np.arange(s, min(s + g, n_slots)) for s in range(0, n_slots, g)]
    if from_end:                                                  # count groups from the end so the short one sits at the start
        groups = [np.arange(max(e - g, 0), e) for e in range(n_slots, 0, -g)][::-1]
    return groups


def period_groups(period: int, n_slots: int, g: int) -> list[np.ndarray]:
    """Groups of one period (0 open, 1 middle, 2 close). Anchored at the session edge (open: from its start, close: from the session
    end), so a short leftover group falls on the quiet inner side, not on the high-variance edge bars that the merging is meant to smooth."""
    return merge_groups(n_slots, g, from_end=(period == 2))


def merged_squares(r: np.ndarray, idx: list[np.ndarray], g: int) -> list[np.ndarray]:
    """Per period: squares of the sum of g consecutive used-slot returns, divided by the group size. List of (stocks, days, groups)."""
    out = []
    for p, slots in enumerate(idx):
        groups = period_groups(p, len(slots), g)
        out.append(np.stack([(r[:, :, slots[gr]].sum(axis=2) ** 2) / len(gr) for gr in groups], axis=2))
    return out


def null_scale(profile: np.ndarray, idx: list[np.ndarray], g: int) -> np.ndarray:
    """Constant per period that restores equal expected period means after merging (1.0 for g = 1 or when all groups have size g).

    The expected value of a merged square is (sum of the group's slot variances) / group size, so a short last group can make the
    period's expected mean differ slightly from the g = 1 value. The day-factor moment is common to all periods and cancels.
    """
    v = np.asarray(profile) ** 2
    scale = []
    for p, slots in enumerate(idx):
        groups = period_groups(p, len(slots), g)
        e_merged = np.mean([v[slots[gr]].sum() / len(gr) for gr in groups])
        scale.append(v[slots].mean() / e_merged)
    return np.array(scale)


def matrix_from_squares(q: list[np.ndarray], scale: np.ndarray) -> np.ndarray:
    """(days, 3) market matrix: period mean of the merged squares, averaged over stocks, times the null-preserving constants."""
    return np.stack([qp.mean(axis=2) for qp in q], axis=-1).mean(axis=0) * scale[None, :]


def tail_diagnostics(q: list[np.ndarray], M: np.ndarray) -> dict:
    """HC quantities from data only: kurtosis of slot-standardised squares E[e^2]/E[e]^2 (= kurtosis of standardised returns for g = 1),
    and for each period the largest single-day share of the period total."""
    e = np.concatenate([qp / qp.mean(axis=(0, 1), keepdims=True) for qp in q], axis=2)
    out = {"kurt": float((e ** 2).mean() / e.mean() ** 2)}
    share = M.max(axis=0) / M.sum(axis=0)
    out.update({"maxshare_open": float(share[0]), "maxshare_middle": float(share[1]), "maxshare_close": float(share[2]), "maxshare": float(share.max())})
    return out


def baseline_on_returns(r: np.ndarray, idx: list[np.ndarray], profile: np.ndarray, g: int, rng: np.random.Generator, B: int) -> dict:
    """Merge (g bars), build the day matrix and run the M4b baseline (bootstrap-t, 'rom', max rule, iid days, B resamples); one result row."""
    q = merged_squares(r, idx, g)
    M = matrix_from_squares(q, null_scale(profile, idx, g))
    try:
        res = bootstrap_t(M, rng, "rom", B=B)
        ok = bool(np.isfinite(res["t"]).all() and np.isfinite(res["crit_max"]))
        out = {"valid": ok, "reject": bool(res["reject_max"]) if ok else False, "T": float(np.abs(res["t"]).max()), "crit": float(res["crit_max"]),
               "t_open_mid": float(res["t"][0]), "t_close_mid": float(res["t"][1]), "t_open_close": float(res["t"][2])}
    except Exception as exc:                                        # a failed simulation is counted, never dropped silently
        out = {"valid": False, "reject": False, "T": np.nan, "crit": np.nan, "t_open_mid": np.nan, "t_close_mid": np.nan,
               "t_open_close": np.nan, "error": repr(exc)}
        M = np.nan_to_num(np.stack([qp.mean(axis=2) for qp in q], axis=-1).mean(axis=0), nan=1.0) + 1e-300
    out.update(tail_diagnostics(q, M))
    return out


def effective_bar_counts(profile: np.ndarray, idx: list[np.ndarray], g: int) -> dict:
    """Per period: (sum v)^2 / sum v^2 over the merged groups' expected variances v: how many bars carry the period's variance."""
    v = np.asarray(profile) ** 2
    out = {}
    for p, (name, slots) in enumerate(zip(ds.PERIOD_NAMES, idx)):
        w = np.array([v[slots[gr]].sum() for gr in period_groups(p, len(slots), g)])
        out[name] = float(w.sum() ** 2 / (w ** 2).sum())
    return out
