"""Real-data H1 test with the frozen C3 critical value (docs/30). Pure functions, no random numbers, no simulation.

Rules fixed in docs/30 before any run: window = the first n usable complete sessions of the market in date order (R1); a session is
usable for a stock when every used slot has a finite squared return, and for the market when all stocks are usable (R7); fewer than n
usable sessions means the market is NOT TESTABLE and no statistic is computed (n is never shortened); the decision is T > crit (R3).
"""
from __future__ import annotations

import numpy as np

from . import h1_calibration as hc
from .h1_rms import CONTRAST_IDX

N_SESSIONS = 59


def complete_sessions(r2_used: np.ndarray) -> np.ndarray:
    """(stocks, days, used slots) -> boolean (days,) : True where every stock has every used slot finite."""
    return np.isfinite(r2_used).all(axis=(0, 2))


def usable_counts(r2_used: np.ndarray, dates) -> dict:
    ok_stock = np.isfinite(r2_used).all(axis=2)          # (stocks, days)
    ok = ok_stock.all(axis=0)
    return {"dates_in_sample": int(len(dates)), "usable_per_stock": [int(x) for x in ok_stock.sum(axis=1)], "usable_market_sessions": int(ok.sum())}


def analyse_market(r2_used: np.ndarray, groups: list[np.ndarray], dates, crit: float, n: int = N_SESSIONS) -> dict:
    """Counts first; the statistic is computed only when n usable complete sessions exist."""
    dates = list(dates)
    out = usable_counts(r2_used, dates)
    out.update({"n_required": int(n), "crit": float(crit)})
    ok = complete_sessions(r2_used)
    if int(ok.sum()) < n:
        out.update({"status": "NOT_TESTABLE", "T": None, "reject": None, "theta": None, "se": None, "first_date": None, "last_date": None})
        return out
    sel = np.flatnonzero(ok)[:n]
    M = hc.market_matrix_from_r2(r2_used[:, sel, :], groups)
    th, se = hc._parts(M)
    T = float(np.abs(th / se).max())
    res = hc.c3_test(M, crit)
    assert abs(res["T"] - T) < 1e-12
    out.update({"status": "TESTED", "T": res["T"], "reject": res["reject"], "theta": [float(x) for x in th], "se": [float(x) for x in se],
                "first_date": str(dates[int(sel[0])]), "last_date": str(dates[int(sel[-1])]), "selected_positions": [int(x) for x in sel],
                "contrasts": [list(map(int, c)) for c in CONTRAST_IDX]})
    return out
