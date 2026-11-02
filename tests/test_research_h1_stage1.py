"""Unit tests for the Stage 1 helpers (src/quantlab/research/h1_stage1.py). Synthetic data only; baseline method only.
They check that the code does what its docstrings say, not that any statistical conclusion is right."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))

from quantlab.calendars import NSE, US                                  # noqa: E402
from quantlab.research import direct_sim as ds, h1_stage1 as s1         # noqa: E402
import run_h1_inference as ri                                           # noqa: E402

MARKETS = {"NSE": NSE, "US": US}


def prof(mk, shape):
    return ri.profile_for(mk, shape, 1.0)


@pytest.mark.parametrize("mk", ["NSE", "US"])
@pytest.mark.parametrize("shape", ["flat", "E", "D5"])
def test_signed_returns_squared_equal_the_m4b_generator(mk, shape):
    m, p = MARKETS[mk], prof(mk, shape)
    a = s1.simulate_returns(m, 3, 20, np.random.default_rng(7), profile=p, df=4.0, day_vol_sd=0.3)
    b = ds.simulate_returns_sq(m, 3, 20, np.random.default_rng(7), profile=p, df=4.0, day_vol_sd=0.3)
    assert np.array_equal(a * a, b)


@pytest.mark.parametrize("mk", ["NSE", "US"])
def test_merge_one_equals_the_m4b_period_matrix(mk):
    m, p = MARKETS[mk], prof(mk, "E")
    idx = ds.used_slot_index(m)
    r = s1.simulate_returns(m, 3, 15, np.random.default_rng(8), profile=p, df=6.0)
    M = s1.matrix_from_squares(s1.merged_squares(r, idx, 1), s1.null_scale(p, idx, 1))
    assert np.allclose(M, ds.period_matrix(r * r, idx), rtol=1e-12)


def test_merge_groups_cover_every_slot_once():
    for n in (7, 20, 25):
        for g in (1, 2, 3):
            allpos = np.concatenate(s1.merge_groups(n, g))
            assert sorted(allpos) == list(range(n)) and all(len(x) <= g for x in s1.merge_groups(n, g))


def test_close_period_groups_are_anchored_at_the_session_end():
    assert [list(x) for x in s1.merge_groups(9, 2, from_end=True)] == [[0], [1, 2], [3, 4], [5, 6], [7, 8]]
    assert [list(x) for x in s1.period_groups(0, 9, 2)] == [[0, 1], [2, 3], [4, 5], [6, 7], [8]]
    assert [list(x) for x in s1.period_groups(2, 9, 2)][-1] == [7, 8]
    for n in (7, 20, 25):
        for g in (1, 2, 3):
            assert sorted(np.concatenate(s1.merge_groups(n, g, from_end=True))) == list(range(n))


def test_null_scale_is_one_without_merging_and_for_full_groups():
    for mk in ("NSE", "US"):
        idx = ds.used_slot_index(MARKETS[mk])
        assert np.allclose(s1.null_scale(prof(mk, "E"), idx, 1), 1.0)
        flat = prof(mk, "flat")
        for g in (2, 3):
            assert np.allclose(s1.null_scale(flat, idx, g), 1.0 + 0 * flat[:3], atol=0.05)   # close to 1 even with a short last group


@pytest.mark.parametrize("mk", ["NSE", "US"])
@pytest.mark.parametrize("shape", ["E", "D5"])
@pytest.mark.parametrize("g", [2, 3])
def test_merged_period_means_stay_equal_under_the_null(mk, shape, g):
    # analytic: expected merged period mean times the constant equals the g = 1 expected period mean, which is equal across periods
    m, p = MARKETS[mk], prof(mk, shape)
    idx = ds.used_slot_index(m)
    v = p ** 2
    sc = s1.null_scale(p, idx, g)
    exp_merged = [np.mean([v[s[gr]].sum() / len(gr) for gr in s1.period_groups(i, len(s), g)]) * c for i, (s, c) in enumerate(zip(idx, sc))]
    base = [v[s].mean() for s in idx]
    assert np.allclose(exp_merged, base, rtol=1e-12) and np.allclose(base, base[0], rtol=1e-9)


def test_merged_period_means_equal_in_a_large_gaussian_sample():
    m, p = NSE, prof("NSE", "D5")
    idx = ds.used_slot_index(m)
    r = s1.simulate_returns(m, 3, 3000, np.random.default_rng(9), profile=p, df=1000.0, day_vol_sd=0.0)
    M = s1.matrix_from_squares(s1.merged_squares(r, idx, 3), s1.null_scale(p, idx, 3))
    means = M.mean(axis=0)
    assert np.allclose(means, means.mean(), rtol=0.02)


def test_sim_seed_equals_spawned_child_and_is_unique():
    kids = np.random.SeedSequence(20261201, spawn_key=(5,)).spawn(10)
    for i in (0, 3, 9):
        assert np.array_equal(np.random.default_rng(kids[i]).random(4), np.random.default_rng(s1.sim_seed(20261201, 5, i)).random(4))
    draws = {tuple(np.random.default_rng(s1.sim_seed(20261201, r, i)).integers(0, 2 ** 62, 2)) for r in range(20) for i in range(200)}
    assert len(draws) == 4000


def test_baseline_on_returns_deterministic_and_complete():
    m, p = NSE, prof("NSE", "E")
    idx = ds.used_slot_index(m)
    r = s1.simulate_returns(m, 3, 59, np.random.default_rng(10), profile=p, df=4.0)
    a = s1.baseline_on_returns(r, idx, p, 1, np.random.default_rng(11), 199)
    assert a == s1.baseline_on_returns(r, idx, p, 1, np.random.default_rng(11), 199)
    assert a["valid"] and np.isfinite(a["T"]) and a["crit"] > 0 and a["kurt"] > 1 and 0 < a["maxshare"] < 1
    assert a["reject"] == (a["T"] > a["crit"])


def test_baseline_matches_m4b_function_on_same_matrix():
    from quantlab.research.h1_rms2 import bootstrap_t
    m, p = US, prof("US", "D5")
    idx = ds.used_slot_index(m)
    r = s1.simulate_returns(m, 3, 59, np.random.default_rng(12), profile=p, df=6.0)
    ref = bootstrap_t(ds.period_matrix(r * r, idx), np.random.default_rng(13), "rom", B=199)
    out = s1.baseline_on_returns(r, idx, p, 1, np.random.default_rng(13), 199)
    assert out["reject"] == ref["reject_max"] and out["crit"] == pytest.approx(ref["crit_max"], rel=1e-12)


def test_gaussian_kurtosis_near_three_and_effective_bars_of_flat_profile():
    m, p = NSE, prof("NSE", "flat")
    idx = ds.used_slot_index(m)
    r = s1.simulate_returns(m, 3, 800, np.random.default_rng(14), profile=p, df=1000.0, day_vol_sd=0.0)
    q = s1.merged_squares(r, idx, 1)
    assert s1.tail_diagnostics(q, s1.matrix_from_squares(q, np.ones(3)))["kurt"] == pytest.approx(3.0, abs=0.1)
    eff = s1.effective_bar_counts(p, idx, 1)
    assert all(eff[n] == pytest.approx(len(s)) for n, s in zip(ds.PERIOD_NAMES, idx))
