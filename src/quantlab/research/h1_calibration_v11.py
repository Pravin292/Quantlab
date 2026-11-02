"""H1 calibration, SPECIFICATION v1.1 additions (new file; the frozen v1 module h1_calibration.py is NOT changed).   SIMULATED DATA ONLY.

What is here (addenda A1-A5 of docs/15; A6 is a rule recorded in the spec, not code):
  A1  fdb_p_value / fdb_like_test   corrected fast-double-bootstrap-like procedure.  FORMULA UNVERIFIED against any paper.
  A2  classify_cell / classify_candidate   exact PASS / ambiguous / FAIL / MARGINAL rules (point rule stays the decision).
  A3  gate_pass / wilson_interval   the v1 gate, written so the Wilson clause and the 7% ceiling can be switched off and compared.
  A4  ALT_DGP_PARAMETERS / alt_dgp_second_moment_factor   exact alternative-process parameters and null-preserving normalisations.
  A5  C3_TRAINING_INTERMEDIATE   how C3 critical values are trained at 90 and 180 days.

Passing unit tests for this file show that the code does what its docstrings say. They are NOT evidence that any procedure is
statistically valid; that can only come from the pre-specified simulation stages.
"""
from __future__ import annotations

import math

import numpy as np

from .h1_calibration import ALPHA, _parts, max_abs_t
from .inference import resample_days

Z95 = 1.959964

# ------------------------------------------------------------------------------------------------ A1: corrected C2
C2_LABEL = "FDB-like procedure, formula UNVERIFIED (not attributed to any paper)"


def fdb_p_value(T: float, Tstar: np.ndarray, T2: np.ndarray) -> tuple[float, float]:
    """Return (p1, p_fdb): p1 = share of first-level T* >= T; p_fdb = share of first-level T* above the (1 - p1) quantile of second-level T**."""
    p1 = float(np.mean(Tstar >= T))                      # ordinary bootstrap p-value
    q = float(np.quantile(T2, 1.0 - p1))                 # critical value read from the SECOND-level statistics
    p_fdb = float(np.mean(Tstar > q))                    # first-level statistics compared with that value (v1 wrongly used T2 here)
    return p1, p_fdb


def fdb_like_test(M: np.ndarray, rng: np.random.Generator, B: int = 999, alpha: float = ALPHA) -> dict:
    """Corrected fast-double-bootstrap-like test of H0 on a day matrix M (n,3); same random draws as the v1 function, different p-value."""
    n = len(M)
    th, _ = _parts(M)
    T = float(max_abs_t(M))
    Xb = M[resample_days(n, B, rng)]                                                     # outer resamples (B, n, 3)
    thb, seb = _parts(Xb)
    Tstar = np.abs((thb - th) / seb).max(axis=-1)                                        # first-level statistics
    idx2 = rng.integers(0, n, (B, n))                                                    # one inner resample per outer one
    X2 = np.take_along_axis(Xb, idx2[:, :, None], axis=1)
    th2, se2 = _parts(X2)
    T2 = np.abs((th2 - thb) / se2).max(axis=-1)                                          # second-level statistics
    p1, p_fdb = fdb_p_value(T, Tstar, T2)
    return {"T": T, "p_first": p1, "p_fdb": p_fdb, "reject": bool(p_fdb <= alpha), "label": C2_LABEL}


# ------------------------------------------------------------------------------------------------ A2 / A3: gates
# tier -> (lower bound, upper bound, Wilson upper limit).  None = clause absent.  ALT has no Wilson clause in v1.
GATES = {"A": (0.045, 0.055, 0.060), "B": (0.040, 0.060, 0.065), "ALT": (0.040, 0.060, None)}
CEILING = 0.07                                           # v1: no validated gated cell above 7.0%


def wilson_interval(k: int | np.ndarray, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Wilson 95% interval (lower, upper) for k successes in n trials; works on arrays of k."""
    k = np.asarray(k, dtype=float)
    p = k / n
    d = 1 + Z95 ** 2 / n
    centre = p + Z95 ** 2 / (2 * n)
    half = Z95 * np.sqrt(p * (1 - p) / n + Z95 ** 2 / (4 * n * n))
    return (centre - half) / d, (centre + half) / d


def gate_pass(k: int | np.ndarray, n: int, tier: str, use_wilson: bool = True, use_ceiling: bool = True) -> np.ndarray:
    """v1 point rule for a gated cell: estimate inside [lo, hi], plus (optionally) the Wilson-upper clause and the 7% ceiling."""
    lo, hi, up = GATES[tier]
    p = np.asarray(k, dtype=float) / n
    ok = (p >= lo - 1e-12) & (p <= hi + 1e-12)
    if use_wilson and up is not None:
        ok &= wilson_interval(k, n)[1] <= up + 1e-12
    if use_ceiling:
        ok &= p <= CEILING + 1e-12
    return ok


def classify_cell(k: int, n: int, tier: str, c3_mode: bool = False) -> dict:
    """A2: status of one gated cell: PASS / PASS_AMBIGUOUS / FAIL / FAIL_AMBIGUOUS, with the estimate and Wilson interval.

    point_pass  : the v1 rule (decision).  For C3 only the upper bounds count (c3_mode).
    ambiguous   : a point-rule boundary that applies to the cell lies inside the Wilson 95% interval [L, U].
    """
    lo, hi, _ = GATES[tier]
    L, U = (float(x) for x in wilson_interval(k, n))
    p = k / n
    point_pass = bool(gate_pass(k, n, tier)) if not c3_mode else bool(p <= hi + 1e-12)
    bounds = [hi] if c3_mode else [lo, hi]
    ambiguous = any(L <= b <= U for b in bounds)
    status = ("PASS" if point_pass else "FAIL") + ("_AMBIGUOUS" if ambiguous else "")
    return {"p_hat": p, "wilson_low": L, "wilson_high": U, "point_pass": point_pass, "ambiguous": ambiguous, "status": status}


def classify_candidate(cells: list[dict]) -> str:
    """A2: candidate outcome from its gated-cell statuses (see docs/15a section A2).

    FAIL                    : at least one cell is FAIL (clear failure).
    FAIL_BOUNDARY_ONLY      : no clear FAIL, at least one FAIL_AMBIGUOUS.  Decision stays 'not selected'; replication needs approval.
    MARGINAL_NOT_DEMONSTRATED: every cell point-passes, at least one PASS_AMBIGUOUS.  No claim of calibration.
    PASS_CLEAR              : every cell is PASS (no cell is boundary-ambiguous).
    """
    statuses = [c["status"] for c in cells]
    if "FAIL" in statuses:
        return "FAIL"
    if "FAIL_AMBIGUOUS" in statuses:
        return "FAIL_BOUNDARY_ONLY"
    if "PASS_AMBIGUOUS" in statuses:
        return "MARGINAL_NOT_DEMONSTRATED"
    return "PASS_CLEAR"


# ------------------------------------------------------------------------------------------------ A4: alternative processes
SIGMA_A = 0.25                      # stationary sd of the log-volatility in process a
PHI_A = 0.9                         # AR(1) coefficient of the log-volatility in process a
JUMP_P, JUMP_LOW, JUMP_HIGH = 0.002, 4.0, 8.0
E_JUMP_SQ = (JUMP_HIGH ** 3 - JUMP_LOW ** 3) / (3 * (JUMP_HIGH - JUMP_LOW))            # E[J^2] for J ~ U(4,8) with random sign = 37.33
JUMP_VAR_SHARE = JUMP_P * E_JUMP_SQ                                                      # 0.0747 of the variance comes from jumps
SHOCK_SCALE_B = math.sqrt(1.0 - JUMP_VAR_SHARE)                                          # 0.9619: shrinks the t10 shock to keep E r^2
E_MIX_WEIGHT, E_MIX_SD_RATIO, E_TARGET_SD = 0.05, 3.0, 0.3
E_SMALL_SD = E_TARGET_SD / math.sqrt((1 - E_MIX_WEIGHT) + E_MIX_WEIGHT * E_MIX_SD_RATIO ** 2)   # 0.2535
E_LARGE_SD = E_MIX_SD_RATIO * E_SMALL_SD                                                  # 0.7606


def t_unit_scale(df: float) -> float:
    """Multiplier that gives a Student-t(df) variable unit variance (df > 2)."""
    return math.sqrt((df - 2.0) / df)


ALT_DGP_PARAMETERS = {
    "a_intraday_volatility_clustering": {
        "log_vol": f"h_0 ~ N(0, {SIGMA_A}^2); h_j = {PHI_A} h_(j-1) + sqrt(1 - {PHI_A}^2) * {SIGMA_A} * eta_j, eta_j ~ N(0,1); new path for every stock-day",
        "return": "r = profile * exp(f) * exp(h_j - sigma^2) * eps, eps ~ Student-t(6) scaled to unit variance, f ~ N(0, 0.3^2)",
        "null_normalisation": "exp(-sigma^2) on the amplitude, because E[exp(2h)] = exp(2 sigma^2) for h ~ N(0, sigma^2); h is stationary so E is the same in every slot",
        "unit_variance_multiplier_eps": t_unit_scale(6)},
    "b_jumps": {
        "return": "r = profile * exp(f) * (0.9619 * eps + J), eps ~ Student-t(10) scaled to unit variance, f ~ N(0, 0.3^2)",
        "jump": f"per bar and stock, with probability {JUMP_P}: J = sign * U({JUMP_LOW}, {JUMP_HIGH}) (random sign); otherwise J = 0",
        "null_normalisation": f"E[J^2] = {E_JUMP_SQ:.4f}, jump share of variance = {JUMP_VAR_SHARE:.5f}; shock multiplier sqrt(1 - share) = {SHOCK_SCALE_B:.5f} keeps E[(...)^2] = 1",
        "unit_variance_multiplier_eps": t_unit_scale(10)},
    "c_period_specific_tails": {
        "return": "r = profile * exp(f) * eps; eps ~ Student-t(4) in open and close slots, Student-t(8) in middle slots, each scaled to unit variance",
        "null_normalisation": "each period's shock has unit variance, so E r^2 is profile-driven only",
        "unit_variance_multipliers": {"t4": t_unit_scale(4), "t8": t_unit_scale(8)}},
    "d_stock_specific_tails": {
        "return": "r = profile * exp(f) * eps; eps ~ Student-t(3), Student-t(5), Student-t(8) for stock 1, 2, 3, each scaled to unit variance",
        "null_normalisation": "unit variance per stock",
        "unit_variance_multipliers": {"t3": t_unit_scale(3), "t5": t_unit_scale(5), "t8": t_unit_scale(8)}},
    "e_heavy_tailed_day_factor": {
        "DEVIATION_FROM_V1_WORDING": ("v1 / docs/15 said 'log day scale Student-t(3)/sqrt(3) x 0.3'. A Student-t variable has no moment-generating function, so "
                                      "E[exp(2f)] is infinite: expected squared return, and with it the estimand, would not exist. Replaced by a Gaussian scale mixture "
                                      "with the same overall sd and heavy tails. PENDING YOUR APPROVAL."),
        "log_day_factor": f"f ~ N(0, {E_SMALL_SD:.5f}^2) with probability {1 - E_MIX_WEIGHT}, N(0, {E_LARGE_SD:.5f}^2) with probability {E_MIX_WEIGHT} (independent across stocks); overall sd = {E_TARGET_SD}",
        "return": "r = profile * exp(f) * eps, eps ~ Student-t(8) scaled to unit variance",
        "null_normalisation": "E[exp(2f)] is finite and the same in all periods (f is independent of the slot), so period variance ratios are unaffected; unit-variance shocks",
        "unit_variance_multiplier_eps": t_unit_scale(8)},
    "f_laplace_shocks": {
        "return": "r = profile * exp(f) * eps, eps ~ Laplace with scale 1/sqrt(2) (unit variance, excess kurtosis 3), f ~ N(0, 0.3^2)",
        "null_normalisation": "variance of Laplace(b) is 2 b^2 = 1",
        "laplace_scale": 1 / math.sqrt(2)},
}


def alt_dgp_second_moment_factor(name: str) -> float:
    """Analytic E[(shock part)^2] of one bar for an alternative process, excluding the common profile * day factor. Must equal 1 (the null check)."""
    from scipy import stats
    if name == "a_intraday_volatility_clustering":
        eps2 = (stats.t(6).var() * t_unit_scale(6) ** 2)
        # E[exp(2h - 2 sigma^2)] for h ~ N(0, sigma^2), by Gauss-Hermite quadrature (independent of the closed form used in the spec)
        nodes, weights = np.polynomial.hermite.hermgauss(60)
        h = math.sqrt(2.0) * SIGMA_A * nodes
        vol_factor = float(np.sum(weights * np.exp(2 * h - 2 * SIGMA_A ** 2)) / math.sqrt(math.pi))
        return float(eps2 * vol_factor)
    if name == "b_jumps":
        return float((stats.t(10).var() * t_unit_scale(10) ** 2) * SHOCK_SCALE_B ** 2 + JUMP_P * E_JUMP_SQ)
    if name == "e_heavy_tailed_day_factor":
        return float(stats.t(8).var() * t_unit_scale(8) ** 2)
    if name == "f_laplace_shocks":
        return float(stats.laplace(scale=1 / math.sqrt(2)).var())
    raise KeyError(name)


def day_factor_second_moment_e() -> float:
    """E[exp(2f)] for process e's Gaussian scale mixture (finite; shown to be the same for every slot, so it cancels in period ratios)."""
    return float((1 - E_MIX_WEIGHT) * math.exp(2 * E_SMALL_SD ** 2) + E_MIX_WEIGHT * math.exp(2 * E_LARGE_SD ** 2))


# ------------------------------------------------------------------------------------------------ A5: C3 at 90 and 180 days
C3_TRAINING_INTERMEDIATE = {
    "sample_sizes_days": [90, 180],
    "training_family_per_size": "tails G, T6, T4 x shapes E, D5 x markets NSE, US = 12 cells (the same family used for 125 and 250 days)",
    "sims_per_cell": 25_000,
    "seed_name": "c3_training_intermediate", "seed": 20261209,
    "rule": "crit_n = max over the 12 training cells of size n of the 0.95 quantile of T (no margin); reject when T > crit_n",
    "applies_to": "validation cells T7 and T5 (shape E) at 90 and 180 days; the 59-day cells use crit_59 from the 44-cell development family",
    "limitation": ("the family at 90 and 180 days has 12 cells (no estimated-dependence cells, no 0.6 day-volatility cells, no flat or R2 shapes), "
                   "like 125 and 250 days; C3 is therefore less conservative there than at 59 days and is valid only inside that family"),
}
