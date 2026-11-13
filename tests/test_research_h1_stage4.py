"""Tests for the Stage 4 pieces: the six alternative generators (h1_stage4.py) and the independent reference implementation (h1_stage4_reference.py).
Implementation checks only (not statistical validation). Scratch seeds only; no frozen Stage 4 seed is used here."""
import math
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))

from quantlab.calendars import NSE, US                                       # noqa: E402
from quantlab.research import direct_sim as ds, h1_calibration as hc, h1_calibration_v11 as v11, h1_stage4 as s4, h1_stage4_reference as ref   # noqa: E402
import run_h1_inference as ri                                                # noqa: E402

MK = {"NSE": NSE, "US": US}


def prof(mk):
    return ri.profile_for(mk, "E", 1.0)


# ------------------------------------------------------------------------------------------------ generators
def test_all_six_processes_run_deterministically_and_give_nonnegative_squares():
    assert len(s4.PROCESSES) == 6
    for mk in ("NSE", "US"):
        for p in s4.PROCESSES:
            a = s4.simulate_alt_returns_sq(p, MK[mk], 3, 12, np.random.default_rng(5), prof(mk))
            b = s4.simulate_alt_returns_sq(p, MK[mk], 3, 12, np.random.default_rng(5), prof(mk))
            assert a.shape == (3, 12, MK[mk].bars_per_day) and np.array_equal(a, b) and (a >= 0).all() and np.isfinite(a).all()


def test_analytic_null_normalisation_of_the_four_finite_moment_processes_is_exact():
    for p in ("a_intraday_volatility_clustering", "b_jumps", "e_heavy_tailed_day_factor", "f_laplace_shocks"):
        assert v11.alt_dgp_second_moment_factor(p) == pytest.approx(1.0, abs=1e-9)
    for df in (3, 4, 5, 6, 8, 10):
        assert stats.t(df).var() * v11.t_unit_scale(df) ** 2 == pytest.approx(1.0)


def test_process_c_uses_t4_in_open_and_close_and_t8_in_the_middle():
    m = NSE
    eps = s4.alt_components("c_period_specific_tails", m, 3, 6000, np.random.default_rng(11))["eps"]
    per = s4.slot_periods(m)
    for name, df in (("open", 4), ("middle", 8), ("close", 4)):
        x = np.abs(eps[:, :, per == name]).ravel()
        thr = 3.0
        p0 = 2 * stats.t(df).sf(thr / v11.t_unit_scale(df))
        se = math.sqrt(p0 * (1 - p0) / x.size)
        assert abs((x > thr).mean() - p0) < 5 * se                           # tail probability matches the intended df in each period
    assert 2 * stats.t(4).sf(3 / v11.t_unit_scale(4)) != pytest.approx(2 * stats.t(8).sf(3 / v11.t_unit_scale(8)), rel=0.2)


def test_process_d_uses_t3_t5_t8_for_stocks_1_2_3():
    eps = s4.alt_components("d_stock_specific_tails", US, 3, 6000, np.random.default_rng(12))["eps"]
    for s, df in enumerate((3, 5, 8)):
        x = np.abs(eps[s]).ravel(); thr = 2.5
        p0 = 2 * stats.t(df).sf(thr / v11.t_unit_scale(df))
        assert abs((x > thr).mean() - p0) < 5 * math.sqrt(p0 * (1 - p0) / x.size)


def test_process_e_day_factor_is_the_approved_scale_mixture():
    f = s4.alt_components("e_heavy_tailed_day_factor", NSE, 3, 40000, np.random.default_rng(13))["f"].ravel()
    assert abs(f.std() - 0.3) < 0.01 and abs(f.mean()) < 0.01
    thr = 0.913                                                                  # 1.2 x the large-component sd
    p0 = 0.05 * 2 * stats.norm.sf(thr / v11.E_LARGE_SD) + 0.95 * 2 * stats.norm.sf(thr / v11.E_SMALL_SD)
    assert abs((np.abs(f) > thr).mean() - p0) < 5 * math.sqrt(p0 * (1 - p0) / f.size)       # mixture weights and scales as approved
    assert v11.day_factor_second_moment_e() == pytest.approx(np.exp(2 * f).mean(), rel=0.1)


def test_process_a_log_volatility_is_stationary_with_phi_09():
    h = s4.alt_components("a_intraday_volatility_clustering", NSE, 3, 3000, np.random.default_rng(14))["h"]
    assert h.std() == pytest.approx(0.25, rel=0.03)
    assert np.corrcoef(h[:, :, 1:-1].ravel(), h[:, :, 2:].ravel())[0, 1] == pytest.approx(0.9, abs=0.01)


def test_process_b_jump_frequency_size_and_sign():
    j = s4.alt_components("b_jumps", US, 3, 6000, np.random.default_rng(15))["jump"]
    nz = j[j != 0]
    assert abs(nz.size / j.size - 0.002) < 5 * math.sqrt(0.002 * 0.998 / j.size)
    assert (np.abs(nz) >= 4).all() and (np.abs(nz) <= 8).all() and abs((nz > 0).mean() - 0.5) < 0.08
    assert (j ** 2).mean() == pytest.approx(0.002 * v11.E_JUMP_SQ, rel=0.15)


def test_process_f_is_laplace_with_unit_variance():
    e = s4.alt_components("f_laplace_shocks", NSE, 3, 6000, np.random.default_rng(16))["eps"].ravel()
    assert e.var() == pytest.approx(1.0, rel=0.03) and stats.kurtosis(e) == pytest.approx(3.0, abs=0.6)


# ------------------------------------------------------------------------------------------------ independent reference implementation
def test_reference_period_slots_derived_from_clock_times_equal_the_library_slots():
    for mk, m in MK.items():
        lib = [list(map(int, i)) for i in ds.used_slot_index(m)]
        assert ref.period_slots(mk) == lib


def _data(mk, seed, n_days=40, df=4.0):
    rng = np.random.default_rng(seed)
    r2 = ds.simulate_returns_sq(MK[mk], 3, n_days, rng, profile=prof(mk), df=df, day_vol_sd=0.3)
    return r2


@pytest.mark.parametrize("mk", ["NSE", "US"])
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_reference_statistic_equals_the_vectorised_statistic_to_1e9(mk, seed):
    r2 = _data(mk, seed)
    t_vec = float(hc.max_abs_t(ds.period_matrix(r2, ds.used_slot_index(MK[mk]))))
    t_ref = ref.statistic_T(ref.market_matrix(r2.tolist(), mk))
    assert abs(t_ref - t_vec) <= 1e-9 * abs(t_vec)
    assert abs(t_ref - t_vec) <= 1e-12 * abs(t_vec)                            # in fact much closer (float rounding only)


def test_the_check_is_sensitive_to_realistic_errors(monkeypatch):
    r2 = _data("NSE", 7, n_days=59)
    X = ref.market_matrix(r2.tolist(), "NSE")
    t = ref.statistic_T(X)
    assert abs(ref.statistic_T(X, ddof=0) - t) > 1e-9 * t                       # a wrong variance divisor is caught
    good = ref.period_slots("NSE")
    monkeypatch.setattr(ref, "period_slots", lambda m: [[0] + good[0], good[1], good[2]])              # wrong boundary: opening candle included
    assert abs(ref.statistic_T(ref.market_matrix(r2.tolist(), "NSE")) - t) > 1e-9 * t
    monkeypatch.setattr(ref, "period_slots", lambda m: [good[0][:-1], good[1], good[2]])               # wrong boundary: open window one slot short
    assert abs(ref.statistic_T(ref.market_matrix(r2.tolist(), "NSE")) - t) > 1e-9 * t
    assert ref.statistic_T([[row[0], row[2], row[1]] for row in X]) == pytest.approx(t, rel=1e-12)      # T is symmetric in the period labels (documented property)


def test_reference_quantile_equals_numpy_linear_quantile_to_1e12_and_other_definitions_differ():
    rng = np.random.default_rng(21)
    v = rng.standard_t(4, 25000) ** 2
    for p in (0.5, 0.9, 0.95, 0.99):
        assert abs(ref.quantile_linear(v.tolist(), p) - float(np.quantile(v, p))) <= 1e-12 * abs(np.quantile(v, p))
    assert abs(float(np.quantile(v, 0.95, method="lower")) - float(np.quantile(v, 0.95))) > 1e-12 * 10          # another definition is detectable
    assert ref.c3_value([v.tolist(), (v * 1.1).tolist()]) == pytest.approx(float(np.quantile(v * 1.1, 0.95)), rel=1e-12)


def test_reference_module_is_independent_of_the_vectorised_code():
    src = (ROOT / "src/quantlab/research/h1_stage4_reference.py").read_text()
    code = "\n".join(l for l in src.splitlines() if l.strip().startswith(("import ", "from ")))
    for banned in ("numpy", "h1_calibration", "h1_rms", "direct_sim", "h1_stage3", "scipy", "pandas"):
        assert banned not in code, banned
