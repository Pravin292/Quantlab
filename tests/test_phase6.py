"""Tests for Phase 6 (docs/40). Constructed deterministic inputs only: no real data, no random numbers.
Implementation checks, not statistical validation."""
import re
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))
from quantlab.calendars import NSE, US                                  # noqa: E402
from quantlab.research import dependence as dep, direct_sim as ds, phase6 as p6   # noqa: E402
import describe_next_round as dnr                                       # noqa: E402
import phase6_run as run                                                # noqa: E402

APPENDIX_A = {  # docs/26 Appendix A, upper triangles (3 decimals)
    "NSE": {("flat", "E"): 0.273, ("flat", "D5"): 0.767, ("flat", "R2"): 0.158, ("flat", "D1.5"): 1.088, ("flat", "D3.0"): 0.469,
            ("E", "D5"): 0.593, ("E", "R2"): 0.174, ("E", "D1.5"): 0.903, ("E", "D3.0"): 0.329, ("D5", "R2"): 0.631,
            ("D5", "D1.5"): 0.329, ("D5", "D3.0"): 0.306, ("R2", "D1.5"): 0.955, ("R2", "D3.0"): 0.330, ("D1.5", "D3.0"): 0.634},
    "US": {("flat", "E"): 0.276, ("flat", "D5"): 1.231, ("flat", "R2"): 0.173, ("flat", "D1.5"): 1.744, ("flat", "D3.0"): 0.751,
           ("E", "D5"): 0.997, ("E", "R2"): 0.125, ("E", "D1.5"): 1.512, ("E", "D3.0"): 0.517, ("D5", "R2"): 1.093,
           ("D5", "D1.5"): 0.521, ("D5", "D3.0"): 0.492, ("R2", "D1.5"): 1.609, ("R2", "D3.0"): 0.609, ("D1.5", "D3.0"): 1.013},
}
S_HALF = {"NSE": {"flat": 0.079, "E": 0.087, "D5": 0.153, "R2": 0.079, "D1.5": 0.164, "D3.0": 0.153},
          "US": {"flat": 0.087, "E": 0.063, "D5": 0.246, "R2": 0.063, "D1.5": 0.261, "D3.0": 0.246}}


# ------------------------------------------------------------------ jackknife checks T1-T6 (docs/26 7.2)
@pytest.mark.parametrize("n", [50, 54, 59, 60, 61, 81, 90, 113, 125, 162, 180, 225, 250])
def test_T1_weights_sum_to_one(n):
    assert abs(p6.block_weights(n).sum() - 1) < 1e-14


def _mean_minus_groups(y):
    n = len(y)
    return np.array([np.delete(y, b).mean() for b in p6.group_bounds(n)])


@pytest.mark.parametrize("n", [50, 59, 60, 61, 90, 125])
def test_T2_weighted_mean_equals_estimate_for_sample_mean(n):
    y = np.sin(np.arange(n) * 0.7) + 0.01 * np.arange(n)
    tw, _ = p6.se_block(_mean_minus_groups(y), n)
    assert abs(tw - y.mean()) < 1e-12


@pytest.mark.parametrize("n", [50, 59, 61, 125])
def test_T3_block_pseudo_values_equal_group_means(n):
    y = np.cos(np.arange(n) * 1.3) + 0.02 * np.arange(n)
    m = np.array(p6.group_sizes(n), float)
    h = n / m
    pv = h * y.mean() - (h - 1) * _mean_minus_groups(y)
    gm = np.array([y[b].mean() for b in p6.group_bounds(n)])
    assert np.allclose(pv, gm, atol=1e-12)


@pytest.mark.parametrize("n", [50, 60, 90, 180, 250])
def test_T4_equal_sizes_reduce_to_standard_grouped_jackknife(n):
    y = np.sin(np.arange(n) * 0.37) ** 3
    tj = _mean_minus_groups(y)
    _, sb = p6.se_block(tj, n)
    g = p6.G_GROUPS
    std = np.sqrt((g - 1) / g * np.sum((tj - tj.mean()) ** 2))
    assert abs(sb - std) < 1e-14 * max(1.0, std) * 10


@pytest.mark.parametrize("n", [54, 59, 61, 81, 113, 125, 162, 225])
def test_T5_unequal_sizes_exactly_unbiased_for_iid_mean(n):
    g = p6.G_GROUPS
    m = np.array(p6.group_sizes(n), float)
    h = n / m
    w = p6.block_weights(n)
    C = np.zeros((g, n))
    for j, b in enumerate(p6.group_bounds(n)):
        C[j] = 1.0 / (n - m[j])
        C[j, b] = 0.0
    cbar = w @ C
    Q = sum((h[j] - 1) * np.outer(C[j] - cbar, C[j] - cbar) for j in range(g)) / g
    assert abs(np.trace(Q) - 1 / n) < 1e-14
    assert np.allclose(Q @ np.ones(n), 0, atol=1e-14)


def test_T6_group_sizes_for_59():
    assert p6.group_sizes(59) == [6] * 9 + [5]


def test_delete_one_jackknife_of_mean_is_classical_se():
    y = np.arange(59.0) ** 0.5
    mi = np.array([np.delete(y, i).mean() for i in range(59)])
    assert abs(p6.se_jack(mi) - y.std(ddof=1) / np.sqrt(59)) < 1e-12


# ------------------------------------------------------------------ shapes (Appendix A)
@pytest.mark.parametrize("mk,market", [("NSE", NSE), ("US", US)])
def test_library_reproduces_appendix_a_distances_and_s(mk, market):
    lib, _ = run.library(market, mk)
    for (a, b), d in APPENDIX_A[mk].items():
        assert abs(p6.shape_distance(lib[a], lib[b]) - d) < 0.0006, (mk, a, b)
    s = p6.half_min_distance(lib)
    for k, v in S_HALF[mk].items():
        assert abs(s[k] - v) < 0.0006, (mk, k)


def test_fit_decay_matches_frozen_m4b_routine():
    for v, fs in ((1 + 1.7 * np.exp(-np.arange(9) / 2.2), True), ((1 + 3.1 * np.exp(-np.arange(7) / 0.8))[::-1], False)):
        assert np.allclose(p6.fit_decay(v, fs), dnr.fit_decay(v, fs), rtol=1e-9, atol=1e-12)


def test_fitted_profile_recovers_variance_parameters_and_both_forms():
    market, mk = US, "US"
    lib, used = run.library(market, mk)
    groups = [np.arange(len(g)) + sum(len(x) for x in ds.used_slot_index(market)[:i]) for i, g in enumerate(ds.used_slot_index(market))]
    vol = p6.vol_consistent_profile(market, 0.9, 2.5, 1.5, 1.0)[used]
    prim, lit, par = p6.fitted_profile(vol ** 2 / np.mean(vol ** 2), groups, market, dep.shaped_profile, used)
    assert abs(par["open_amp"] - 0.9) < 1e-5 and abs(par["open_tau"] - 2.5) < 1e-4
    assert abs(par["close_amp"] - 1.5) < 1e-5 and abs(par["close_tau"] - 1.0) < 1e-4
    assert p6.shape_distance(prim, vol) < 1e-6                       # primary = the data's own volatility shape
    assert p6.shape_distance(lit, dep.shaped_profile(market, 0.9, 2.5, 1.5, 1.0)[used]) < 1e-6


def test_q_zones_and_nearest_tie_order():
    assert [p6.q_rank(q) for q in (0, 1, 1.0001, 2, 2.0001, 4, 4.0001)] == [1, 1, 2, 2, 3, 3, 4]
    d = {s: 1.0 for s in p6.SHAPE_ORDER}
    assert p6.nearest(d)[0] == "E"
    d["R2"] = 0.5
    assert p6.nearest(d) == ("R2", "E")


# ------------------------------------------------------------------ zone tables (docs/26 8.2)
def test_daysd_zone_endpoints():
    z = p6.DAYSD_ZONES
    cases = {0.1499: 4, 0.15: 2, 0.1999: 2, 0.20: 1, 0.40: 1, 0.4001: 2, 0.4999: 2, 0.50: 3, 0.70: 3, 0.7001: 4}
    for x, r in cases.items():
        assert p6.point_zone(z, x)[4] == r, x
    assert p6.classify_interval(z, 0.19, 0.21)[0] == 2
    assert p6.classify_interval(z, 0.45, 0.72)[0] == 4


def test_dependence_zone_endpoints_nse_phi():
    e = 0.441
    z = p6.dep_zones(e)
    a, b = e / 2, 1.5 * e
    assert p6.point_zone(z, 0.0)[4] == 1 and p6.point_zone(z, 0.10)[4] == 1 and p6.point_zone(z, 0.1001)[4] == 2
    assert p6.point_zone(z, a)[4] == 2 and p6.point_zone(z, a + 1e-9)[4] == 3
    assert p6.point_zone(z, b)[4] == 3 and p6.point_zone(z, b + 1e-9)[4] == 4


def _js(theta, lo, hi):
    return {"theta": theta, "se_j": (hi - lo) / 4, "lo": lo, "hi": hi, "se_b": (hi - lo) / 4, "ratio": 1.0,
            "influence_share": 0.05, "pseudo_skew": 0.0, "non_computable": False}


def test_option_a_special_rules_are_unevaluable_not_rank_4():
    d = p6.dimension_daysd(_js(0.6, 0.6, 0.6), np.full(59, 0.6), (0.6, 0.6))
    assert d["result"] == "U" and "DAYSD-0.6-UNEVALUABLE" in d["why"]
    comp = {"phi": (_js(0.3, 0.3, 0.3), np.full(59, 0.3), (0.3, 0.3)), "s": (_js(0.0, 0.0, 0.0), np.zeros(59), (0, 0)),
            "rho": (_js(0.0, 0.0, 0.0), np.zeros(59), (0, 0))}
    d = p6.dimension_dep(comp, "NSE")
    assert d["result"] == "U" and "E-ZONE-DEP-UNEVALUABLE" in d["why"]
    comp["s"] = (_js(0.9, 0.9, 0.9), np.full(59, 0.9), (0.9, 0.9))       # above b = 0.681 -> reliable rank 4
    assert p6.dimension_dep(comp, "NSE")["result"] == 4


def test_unreliable_rules():
    assert p6.dimension_daysd(_js(0.3, 0.1, 0.5), np.full(59, 0.3), (0.3, 0.3))["result"] == "U"      # width > 0.3
    assert p6.dimension_daysd(_js(0.3, 0.25, 0.35), np.r_[np.full(58, 0.3), 0.45], (0.3, 0.3))["result"] == "U"  # zone crossing
    assert p6.dimension_daysd(_js(0.3, 0.25, 0.35), np.full(59, 0.3), (0.3, 0.8))["result"] == "U"    # split-half 1 vs 4
    assert p6.dimension_daysd(_js(0.3, 0.25, 0.35), np.full(59, 0.3), (0.3, 0.3))["result"] == 1


def test_option_a_label_never_gives_a_coverage_rank():
    for others in (1, 2, 3):
        dims = {"D-tail": {"result": "U"}, "D-alt": {"result": "U"}, "D-shape": {"result": others},
                "D-daysd": {"result": 1}, "D-dep": {"result": 1}}
        assert p6.label_option_a(dims)["label"] == "CANNOT BE CLASSIFIED"
    dims["D-shape"] = {"result": 4}
    assert p6.label_option_a(dims)["label"] == "OUTSIDE"


def test_module_never_references_h1_statistic_bootstrap_or_critical_values():
    for path in (ROOT / "src/quantlab/research/phase6.py", ROOT / "scripts/milestone4/phase6_run.py"):
        src = path.read_text()
        for bad in ("max_abs_t", "c3_test", "c3_critical", "bootstrap_t", "fast_double_bootstrap", "c1_test", "real_h1"):
            assert not re.search(rf"\b{bad}\b", src), (path.name, bad)


# ------------------------------------------------------------------ end to end on a constructed block
def _constructed_block(market, n=59, same=False):
    used_idx = ds.used_slot_index(market)
    used = np.concatenate(used_idx)
    vol = p6.vol_consistent_profile(market, 1.2, 2.0, 2.0, 1.2)[used]
    d = np.arange(n)[None, :, None]
    k = np.arange(len(used))[None, None, :]
    s = np.zeros((3, 1, 1)) if same else np.arange(3)[:, None, None]
    day = np.exp(0.3 * np.sin(0.9 * d + 1.7 * s))
    shock = np.sign(np.sin(1.3 * k + 0.7 * d + 2.1 * s) + 0.01) * (1 + 0.6 * np.abs(np.sin(0.37 * k * (d + 1) + s)))
    ret = vol[None, None, :] * day * shock * 0.001
    groups, start = [], 0
    for g in used_idx:
        groups.append(np.arange(start, start + len(g)))
        start += len(g)
    return ret, groups


def test_identical_stocks_give_unit_cross_stock_correlations():
    lib, used = run.library(US, "US")
    ret, groups = _constructed_block(US, same=True)
    m = p6.measure(ret ** 2, ret, groups, US, "US", lib, dep.shaped_profile, used)
    assert abs(m["M12_rho"] - 1) < 1e-12 and abs(m["M12_s"] - 1) < 1e-12


def test_end_to_end_constructed_block_runs_and_labels_under_option_a():
    lib, used = run.library(US, "US")
    ret, groups = _constructed_block(US)
    full, js, dims, lab = run.map_block(ret ** 2, ret, groups, US, "US", lib, used)
    assert lab["label"] in ("OUTSIDE", "CANNOT BE CLASSIFIED")
    assert dims["D-tail"]["result"] == "U" and dims["D-alt"]["result"] == "U"
    assert "D-shape-literal (report only)" in dims and "D-shape-literal (report only)" not in lab["results"]
    for key in ("M2_kurtosis", "M3_hill_top5", "M4_exceed4_per_1000", "M10_day_sd", "M11_phi", "M12_s", "M12_rho",
                "M13_sqret_acf_mean_lag1to5", "M15_daylv_kurtosis", "M8_panel_d_E", "M8L_panel_d_E", "M9_effective_bars_open"):
        assert np.isfinite(full[key]), key
    assert dims["D-shape"]["units"]["panel"]["nearest"] in p6.SHAPE_ORDER
