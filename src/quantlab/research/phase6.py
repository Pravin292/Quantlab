"""Phase 6, exploratory descriptive placement under Option A (docs/26 revision 5 as amended by docs/40, revision 6).

Pure functions: no random numbers, no simulation, no H1 statistic. The module never imports or calls the H1 statistic, a
bootstrap or a critical value (a test checks this). Measurements follow docs/26 section 7 on one panel of 3 stocks and one
block of n sessions; the mapping follows section 8 with the Option A rules of docs/40 (D-tail and D-alt unavailable, so every
block ends OUTSIDE or CANNOT BE CLASSIFIED).
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
from scipy.optimize import least_squares

from . import h1_calibration as hc
from .tail_descriptives import hill_alpha, tail_summary

SHAPE_ORDER = ["E", "D5", "R2", "flat", "D1.5", "D3.0"]          # fixed tie-break order (docs/26 8.2)
EST_DEP = {"NSE": {"phi": 0.441, "s": 0.454, "rho": 0.355},     # docs/26 8.2 D-dep; run_h1_next.EMP_DEP
           "US": {"phi": 0.190, "s": 0.141, "rho": 0.187}}
G_GROUPS = 10


# ------------------------------------------------------------------------------------------------- jackknife (7.2)
def group_sizes(n: int, g: int = G_GROUPS) -> list[int]:
    """g consecutive groups, sizes differing by at most one, larger groups first (n = 59: nine of 6, one of 5)."""
    base, rem = divmod(n, g)
    return [base + 1] * rem + [base] * (g - rem)


def group_bounds(n: int, g: int = G_GROUPS) -> list[np.ndarray]:
    out, start = [], 0
    for m in group_sizes(n, g):
        out.append(np.arange(start, start + m))
        start += m
    return out


def block_weights(n: int, g: int = G_GROUPS) -> np.ndarray:
    m = np.array(group_sizes(n, g), float)
    h = n / m
    return (h - 1) / ((g - 1) * h)


def se_block(theta_minus_j: np.ndarray, n: int, g: int = G_GROUPS) -> tuple[float, float]:
    """Unequal-group delete-block jackknife: weighted mean of deleted estimates and SE_B (docs/26 7.2)."""
    m = np.array(group_sizes(n, g), float)
    h = n / m
    w = block_weights(n, g)
    tw = float(np.sum(w * theta_minus_j))
    var = float(np.sum((h - 1) * (theta_minus_j - tw) ** 2) / g)
    return tw, float(np.sqrt(var))


def se_jack(theta_minus_i: np.ndarray) -> float:
    n = len(theta_minus_i)
    return float(np.sqrt((n - 1) / n * np.sum((theta_minus_i - theta_minus_i.mean()) ** 2)))


def skewness(x: np.ndarray) -> float:
    d = x - x.mean()
    m2 = np.mean(d ** 2)
    return float(np.mean(d ** 3) / m2 ** 1.5) if m2 > 0 else 0.0


def jackknife_summary(theta: float, minus_i: np.ndarray, minus_j: np.ndarray) -> dict:
    """Interval and reliability diagnostics 1-3 and 6 of docs/26 7.2 for one scalar."""
    n = len(minus_i)
    if not (np.isfinite(theta) and np.all(np.isfinite(minus_i)) and np.all(np.isfinite(minus_j))):
        return {"theta": theta, "se_j": np.nan, "lo": np.nan, "hi": np.nan, "se_b": np.nan, "ratio": np.nan,
                "influence_share": np.nan, "pseudo_skew": np.nan, "non_computable": True}
    sj = se_jack(minus_i)
    _, sb = se_block(minus_j, n)
    dev = np.abs(minus_i - theta)
    pseudo = n * theta - (n - 1) * minus_i
    return {"theta": float(theta), "se_j": sj, "lo": float(theta - 2 * sj), "hi": float(theta + 2 * sj), "se_b": sb,
            "ratio": float(sb / sj) if sj > 0 else np.nan, "influence_share": float(dev.max() / dev.sum()) if dev.sum() > 0 else 0.0,
            "pseudo_skew": skewness(pseudo), "non_computable": False}


def generic_unreliable(js: dict) -> list[str]:
    """Rules 1 (first part), 2, 3 and 6 of docs/26 7.2; zone-crossing, width and split-half are checked per dimension."""
    if js["non_computable"]:
        return ["NON-COMPUTABLE"]
    out = []
    if js["influence_share"] > 0.5:
        out.append("SINGLE-SESSION-INFLUENCE")
    if not np.isfinite(js["ratio"]) or js["ratio"] > 1.5 or js["ratio"] < 0.67:
        out.append("DEPENDENCE-INCONSISTENCY")
    if abs(js["pseudo_skew"]) > 2:
        out.append("PSEUDO-VALUE-SKEW")
    return out


# ------------------------------------------------------------------------------------------------- shape (M8)
def fit_decay(v: np.ndarray, from_start: bool) -> tuple[float, float, float]:
    """Same fit as scripts/milestone4/describe_next_round.fit_decay (a test checks equality)."""
    v = np.asarray(v, float)
    j = np.arange(len(v)) if from_start else np.arange(len(v))[::-1]
    y = np.log(v)

    def res(p):
        a, b, tau = p
        return a + np.log1p(np.exp(b) * np.exp(-j / np.exp(tau))) - y
    f = least_squares(res, x0=[y.mean(), 0.0, 1.0])
    a, lb, ltau = f.x
    return float(np.exp(lb)), float(np.exp(ltau)), float(np.sqrt(np.mean(f.fun ** 2)))


def norm_log(profile_used: np.ndarray) -> np.ndarray:
    p = np.asarray(profile_used, float)
    return np.log(p / p.mean())


def shape_distance(a_used: np.ndarray, b_used: np.ndarray) -> float:
    """RMS difference of natural logs of two profiles on the used slots, each divided by its mean (Appendix A)."""
    return float(np.sqrt(np.mean((norm_log(a_used) - norm_log(b_used)) ** 2)))


def half_min_distance(library: dict) -> dict:
    """s(sigma) = half the smallest distance from sigma to any other validated shape of the market."""
    out = {}
    for a in library:
        out[a] = 0.5 * min(shape_distance(library[a], library[b]) for b in library if b != a)
    return out


def nearest(dists: dict) -> tuple[str, str]:
    """sigma1, sigma2 with ties broken by the fixed order (|d_a - d_b| <= 1e-12 * max)."""
    def key(s):
        return dists[s]
    order = sorted(SHAPE_ORDER, key=lambda s: (key(s), SHAPE_ORDER.index(s)))
    first = order[0]
    ties = [s for s in SHAPE_ORDER if abs(dists[s] - dists[first]) <= 1e-12 * max(dists[s], dists[first])]
    s1 = ties[0]
    rest = [s for s in order if s != s1]
    return s1, rest[0]


def q_rank(q: float) -> int:
    if q <= 1:
        return 1
    if q <= 2:
        return 2
    if q <= 4:
        return 3
    return 4


def q_interval_rank(lo: float, hi: float, s: float) -> int:
    """Highest zone intersecting [max(0, lo)/s, hi/s] on q (touching an endpoint counts)."""
    return max(q_rank(max(0.0, lo) / s), q_rank(hi / s))


# ------------------------------------------------------------------------------------------------- zone tables (8.2)
DAYSD_ZONES = [  # (lo, lo_closed, hi, hi_closed, rank, reason)
    (-np.inf, False, 0.15, False, 4, "DAYSD-LOW"),
    (0.15, True, 0.20, False, 2, "DAYSD-FRINGE"),
    (0.20, True, 0.40, True, 1, None),
    (0.40, False, 0.50, False, 2, "DAYSD-FRINGE"),
    (0.50, True, 0.70, True, 3, "DAYSD-0.6"),
    (0.70, False, np.inf, False, 4, "DAYSD-HIGH"),
]


def _intersects(zlo, zlo_c, zhi, zhi_c, lo, hi) -> bool:
    above = (hi > zlo) or (zlo_c and hi == zlo)
    below = (lo < zhi) or (zhi_c and lo == zhi)
    return above and below


def zones_hit(zones, lo, hi) -> list:
    return [z for z in zones if _intersects(z[0], z[1], z[2], z[3], lo, hi)]


def point_zone(zones, x):
    hit = zones_hit(zones, x, x)
    return hit[0] if hit else None


def dep_zones(e: float) -> list:
    a, b = e / 2, 1.5 * e
    c0 = min(0.10, a)
    return [(-np.inf, False, c0, True, 1, None), (c0, False, a, True, 2, "DEP-FRINGE"),
            (a, False, b, True, 3, "E-ZONE-DEP"), (b, False, np.inf, False, 4, "DEP-HIGH")]


def classify_interval(zones, lo, hi) -> tuple[int, str | None]:
    hit = zones_hit(zones, lo, hi)
    z = max(hit, key=lambda t: t[4])
    return z[4], z[5]


# ------------------------------------------------------------------------------------------------- measurements (7.1)
def _corr(a: np.ndarray, b: np.ndarray) -> float:
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3:
        return np.nan
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def _lag1(x: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    return _corr(x[1:], x[:-1]) if len(x) > 3 else np.nan


def _kurt(x: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    d = x - x.mean()
    return float(np.mean(d ** 4) / np.mean(d ** 2) ** 2)


def slot_rel_var(r2_stock: np.ndarray) -> np.ndarray:
    """(days, K) -> (K,) slot mean of r2 / overall mean, zero squared returns treated as missing (as the M4b routine)."""
    x = np.where(r2_stock > 0, r2_stock, np.nan)
    return np.nanmean(x, axis=0) / np.nanmean(x)


def day_log_vol(r2_stock: np.ndarray) -> np.ndarray:
    x = np.where(r2_stock > 0, r2_stock, np.nan)
    return 0.5 * np.log(np.nanmean(x, axis=1))


def vol_consistent_profile(market, open_amp: float, open_tau: float, close_amp: float, close_tau: float) -> np.ndarray:
    """Volatility profile implied by a VARIANCE decay fit: sqrt(1 + b exp(-j/tau)) in open and close, flat middle, each
    period rescaled to the same RMS over its used slots, exactly as dependence.shaped_profile does for its volatility form.
    This is the primary M8 comparison of docs/40 R6.5 (shape E was built by feeding variance-fit parameters to the
    volatility form; see docs/40 section 3)."""
    from quantlab.calendars import expected_slots
    from quantlab.eda.masks import assign_period
    n = market.bars_per_day
    periods = assign_period(expected_slots(market, "2026-08-03"), market).to_numpy()
    prof = np.ones(n)
    for name, amp, tau in (("open", open_amp, open_tau), ("close", close_amp, close_tau)):
        idx = np.where(periods == name)[0]
        idx = idx[idx > 0]                 # j = 0 at the first USED slot, as in the fit (the first candle has no return)
        j = np.arange(len(idx))
        prof[idx] = np.sqrt(1 + amp * np.exp(-(j if name == "open" else j[::-1]) / tau))
    for name in ("open", "middle", "close"):
        u = np.where(periods == name)[0]
        u = u[u > 0]
        prof[u] = prof[u] / np.sqrt(np.mean(prof[u] ** 2))
    prof[0] = prof[1]
    return prof


def fitted_profile(v_used: np.ndarray, groups, market, shaped_profile, used_order) -> tuple[np.ndarray, np.ndarray, dict]:
    """Fit open and close decay to relative slot variances (used-slot positions, the M4b routine). Returns the primary
    (volatility-consistent) profile, the literal profile (parameters fed to shaped_profile, as shape E was built), both on
    the used slots, and the parameters."""
    bo, to, _ = fit_decay(v_used[groups[0]], from_start=True)
    bc, tc, _ = fit_decay(v_used[groups[2]], from_start=False)
    primary = vol_consistent_profile(market, bo, to, bc, tc)
    literal = shaped_profile(market, bo, to, bc, tc)
    return primary[used_order], literal[used_order], {"open_amp": bo, "open_tau": to, "close_amp": bc, "close_tau": tc}


def measure(r2: np.ndarray, ret: np.ndarray, groups, market, mk: str, library: dict, shaped_profile, used_order) -> dict:
    """All scalar measurements for one panel on the given sessions. r2, ret: (3, days, used slots), complete."""
    out = {}
    bm = hc.fit_bar_model(r2, groups)
    e2 = bm.e2
    ts = tail_summary(e2)
    out["M2_kurtosis"] = ts["kurtosis"]
    for f in (1, 2, 5, 10):
        out[f"M3_hill_top{f}"] = ts[f"hill_alpha_top{f}pct"]
    out["M4_exceed4_per_1000"] = ts["share_abs_z_gt_4_per_1000"]
    for p, g in zip(("open", "middle", "close"), groups):
        out[f"M2_kurtosis_{p}"] = tail_summary(e2[:, :, g])["kurtosis"]
    z = np.sqrt(e2.ravel())
    z = z[np.isfinite(z) & (z > 0)]
    out["HT_max_z4_share"] = float(np.max(z ** 4) / np.sum(z ** 4))
    zs = np.sort(z)[:-1]
    out["HT_hill5_without_max"] = hill_alpha(zs, max(2, int(0.05 * len(zs))))
    # shape (M8) and effective bars (M9)
    units = {"panel": np.nanmean(np.stack([slot_rel_var(r2[s]) for s in range(r2.shape[0])]), axis=0)}
    for s in range(r2.shape[0]):
        units[f"stock{s}"] = slot_rel_var(r2[s])
    for u, v in units.items():
        prof, lit, par = fitted_profile(v, groups, market, shaped_profile, used_order)
        for k, val in par.items():
            out[f"M8_{u}_{k}"] = val
        for sig in SHAPE_ORDER:
            out[f"M8_{u}_d_{sig}"] = shape_distance(prof, library[sig])
            out[f"M8L_{u}_d_{sig}"] = shape_distance(lit, library[sig])
        if u == "panel":
            for p, g in zip(("open", "middle", "close"), groups):
                w = prof[g] ** 2
                out[f"M9_effective_bars_{p}"] = float(w.sum() ** 2 / np.sum(w ** 2))
    # day volatility and dependence (M10-M12, M15), as the frozen describe_next_round estimators
    dl = [day_log_vol(r2[s]) for s in range(r2.shape[0])]
    out["M10_day_sd"] = float(np.mean([np.std(x[np.isfinite(x)], ddof=1) for x in dl]))
    out["M11_phi"] = float(np.mean([_lag1(x) for x in dl]))
    out["M12_s"] = float(np.mean([_corr(dl[a], dl[b]) for a, b in combinations(range(len(dl)), 2)]))
    zr = []
    for s in range(r2.shape[0]):
        sv = slot_rel_var(r2[s])
        overall = np.nanmean(np.where(r2[s] > 0, r2[s], np.nan))
        zz = ret[s] / np.sqrt(sv[None, :] * overall)
        zr.append(np.where(r2[s] > 0, zz, np.nan).ravel())
    out["M12_rho"] = float(np.mean([_corr(zr[a], zr[b]) for a, b in combinations(range(len(zr)), 2)]))
    out["M15_daylv_kurtosis"] = float(np.mean([_kurt(x) for x in dl]))
    # within-day clustering (M13): mean of lag 1-5 autocorrelations of squared standardised returns
    acs = []
    for s in range(e2.shape[0]):
        x = e2[s] - np.nanmean(e2[s])
        den = np.nanmean(x ** 2)
        acs.append([np.nanmean(x[:, :-k] * x[:, k:]) / den for k in range(1, 6)])
    out["M13_sqret_acf_mean_lag1to5"] = float(np.mean(acs))
    return out


def jackknife_all(r2, ret, groups, market, mk, library, shaped_profile, used_order) -> tuple[dict, dict, dict]:
    """theta, delete-one replicates and delete-block replicates for every scalar."""
    n = r2.shape[1]
    f = lambda keep: measure(r2[:, keep], ret[:, keep], groups, market, mk, library, shaped_profile, used_order)  # noqa: E731
    full = f(np.arange(n))
    minus_i = [f(np.delete(np.arange(n), i)) for i in range(n)]
    minus_j = [f(np.setdiff1d(np.arange(n), b)) for b in group_bounds(n)]
    keys = list(full)
    return full, {k: np.array([m[k] for m in minus_i]) for k in keys}, {k: np.array([m[k] for m in minus_j]) for k in keys}


# ------------------------------------------------------------------------------------------------- mapping, Option A
def dimension_daysd(js: dict, minus_i: np.ndarray, half_vals: tuple) -> dict:
    if js["non_computable"]:
        return {"result": "U", "why": ["NON-COMPUTABLE"]}
    why = generic_unreliable(js)
    z0 = point_zone(DAYSD_ZONES, js["theta"])
    if any(point_zone(DAYSD_ZONES, x) is not z0 for x in minus_i):
        why.append("ZONE-CROSSING-ON-DELETION")
    if js["hi"] - js["lo"] > 0.3:
        why.append("WIDTH")
    hz = [point_zone(DAYSD_ZONES, x)[4] for x in half_vals]
    if abs(hz[0] - hz[1]) >= 2:
        why.append("SPLIT-HALF")
    if why:
        return {"result": "U", "why": why}
    rank, reason = classify_interval(DAYSD_ZONES, js["lo"], js["hi"])
    if rank == 3:                      # DAYSD-0.6 needs 4 in Dreq; Dreq needs D-tail, unavailable under Option A (docs/40 R6.4)
        return {"result": "U", "why": ["DAYSD-0.6-UNEVALUABLE"], "reason": reason}
    return {"result": rank, "why": [], "reason": reason}


def dimension_dep(comp: dict, mk: str) -> dict:
    """comp: name -> (js, minus_i, (half1, half2)). Rank = highest over the three components; any U -> U."""
    ranks, reasons, why = [], [], []
    for name in ("phi", "s", "rho"):
        js, mi, halves = comp[name]
        zones = dep_zones(EST_DEP[mk][name])
        if js["non_computable"]:
            why.append(f"{name}:NON-COMPUTABLE")
            continue
        w = generic_unreliable(js)
        z0 = point_zone(zones, max(0.0, js["theta"]))
        if any(point_zone(zones, max(0.0, x)) is not z0 for x in mi):
            w.append("ZONE-CROSSING-ON-DELETION")
        if js["hi"] - js["lo"] > 0.4:
            w.append("WIDTH")
        hz = [point_zone(zones, max(0.0, x))[4] for x in halves]
        if abs(hz[0] - hz[1]) >= 2:
            w.append("SPLIT-HALF")
        why += [f"{name}:{x}" for x in w]
        r, reason = classify_interval(zones, max(0.0, js["lo"]), max(0.0, js["hi"]))
        ranks.append(r)
        if reason:
            reasons.append(f"{name}:{reason}")
    if why:
        return {"result": "U", "why": why, "reasons": reasons}
    if 3 in ranks and 4 not in ranks:   # E-ZONE-DEP needs Dreq; unavailable under Option A (docs/40 R6.4)
        return {"result": "U", "why": ["E-ZONE-DEP-UNEVALUABLE"], "reasons": reasons}
    return {"result": max(ranks), "why": [], "reasons": reasons}


def dimension_shape_unit(dist_js: dict, dist_minus_i: dict, s_half: dict, half_nearest_q: tuple) -> dict:
    """One unit (panel or stock). dist_js[sigma] = jackknife summary of d_sigma."""
    d_full = {s: dist_js[s]["theta"] for s in SHAPE_ORDER}
    s1, s2 = nearest(d_full)
    n = len(dist_minus_i[s1])
    s1_i = [nearest({s: dist_minus_i[s][i] for s in SHAPE_ORDER})[0] for i in range(n)]
    near_tie = d_full[s2] <= 1.15 * d_full[s1]
    unstable = any(x != s1 for x in s1_i)
    K = {s1} | ({s2} if near_tie else set()) | set(s1_i)
    flags = (["NEAR-TIE"] if near_tie else []) + (["SHAPE-UNSTABLE"] if unstable else [])
    why = []
    for sig in sorted(K, key=SHAPE_ORDER.index):
        w = generic_unreliable(dist_js[sig])
        why += [f"d_{sig}:{x}" for x in w]
    hr = [q_rank(q) for q in half_nearest_q]
    if abs(hr[0] - hr[1]) >= 2:
        why.append("SPLIT-HALF")
    ranks = {sig: q_interval_rank(dist_js[sig]["lo"], dist_js[sig]["hi"], s_half[sig]) for sig in K}
    rank = max(ranks.values())
    if rank == 1 and len(K) > 1:
        rank = 2
    return {"result": "U" if why else rank, "why": why, "nearest": s1, "second": s2, "K": sorted(K, key=SHAPE_ORDER.index),
            "flags": flags, "q_nearest": d_full[s1] / s_half[s1], "ranks_by_candidate": ranks}


def label_option_a(dims: dict) -> dict:
    """Phase 2 precedence with D-tail and D-alt unavailable (Option A): a reliable rank 4 -> OUTSIDE, else CANNOT."""
    results = {k: v["result"] for k, v in dims.items()}
    if any(r == 4 for r in results.values()):
        label = "OUTSIDE"
    else:
        label = "CANNOT BE CLASSIFIED"
    return {"label": label, "results": results}
