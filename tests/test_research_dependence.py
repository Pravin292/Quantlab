import hashlib

import numpy as np
import pytest

from quantlab.calendars import NSE, US
from quantlab.research import dependence as dep, h1_rms2
from quantlab.research.nulls import simulate_raw


@pytest.mark.parametrize("market,digest", [(NSE, "1d328a79dc2ccf1f"), (US, "e78e2d38c00bc84c")])
def test_default_simulator_output_is_unchanged_by_the_new_hooks(market, digest):
    r = simulate_raw(market, 4, np.random.default_rng(1), df=4.0, day_vol_sd=0.3, intraday_regime_sd=0.2)
    assert hashlib.sha256(r.round(8).to_csv().encode()).hexdigest()[:16] == digest


def test_day_factors_have_requested_sd_autocorrelation_and_cross_correlation():
    rng = np.random.default_rng(0)
    F = np.concatenate([dep.day_factors(60, 3, 0.3, 0.5, 0.6, rng) for _ in range(400)], axis=1)  # long stacked draws
    per = np.stack([dep.day_factors(2000, 3, 0.3, 0.5, 0.6, rng)]).squeeze(0)
    assert abs(per.std() - 0.3) < 0.02
    assert abs(np.corrcoef(per[0, :-1], per[0, 1:])[0, 1] - 0.6) < 0.05
    assert abs(np.corrcoef(per[0], per[1])[0, 1] - 0.5) < 0.06


def test_shared_shocks_give_requested_return_correlation_and_keep_t_tails():
    rng = np.random.default_rng(1)
    n_days = 400
    common = rng.standard_normal((n_days, 75))
    r = [simulate_raw(NSE, n_days, rng, df=4.0, day_vol_sd=0.0, common_z=common, shock_corr=dep.core_corr_for_pearson(0.4, 4.0),
                      slot_vol=np.full(75, 0.001)) for _ in range(2)]
    a = np.log(r[0]["close"] / r[0]["open"]).to_numpy()
    b = np.log(r[1]["close"] / r[1]["open"]).to_numpy()
    assert abs(np.corrcoef(a, b)[0, 1] - 0.4) < 0.06
    kurt = np.mean(a ** 4) / np.mean(a ** 2) ** 2
    assert kurt > 5                                       # heavy-tailed (Gaussian = 3)


def test_shaped_profile_has_equal_period_rms_and_multiplier():
    from quantlab.calendars import expected_slots
    from quantlab.eda.masks import assign_period
    periods = assign_period(expected_slots(NSE, "2026-08-03"), NSE).to_numpy()

    def rms(prof, name):
        u = np.where(periods == name)[0]
        u = u[u > 0]
        return np.sqrt(np.mean(prof[u] ** 2))
    p1 = dep.shaped_profile(NSE, 2.0, 2.0, 4.0, 0.4)
    assert np.allclose([rms(p1, "open"), rms(p1, "close")], rms(p1, "middle"))
    p2 = dep.shaped_profile(NSE, 2.0, 2.0, 4.0, 0.4, mult=1.1)
    assert np.isclose(rms(p2, "open") / rms(p2, "middle"), 1.1)


def test_market_tables_have_requested_cross_stock_structure():
    rng = np.random.default_rng(3)
    tabs = dep.simulate_market_tables(NSE, 3, 60, rng, day_vol_sd=0.3, day_share=0.8, day_phi=0.5, ret_corr=0.4, df=4.0)
    assert len(tabs) == 3 and all(len(t) > 0 for t in tabs)
    c = tabs[0].set_index(["date", "slot"])["ret"].dropna()
    d = tabs[1].set_index(["date", "slot"])["ret"].dropna()
    j = c.to_frame("a").join(d.rename("b"), how="inner")
    assert j.corr().iloc[0, 1] > 0.2


@pytest.mark.parametrize("kind", ["rom", "diff"])
def test_bootstrap_t_detects_difference_and_reports_both_rules(kind):
    rng = np.random.default_rng(2)
    M = np.exp(rng.normal(0, 0.3, (59, 1))) * rng.chisquare(5, (59, 3)) / 5 * np.array([2.0, 1.0, 1.0])
    r = h1_rms2.bootstrap_t(M, rng, kind, B=299)
    assert r["reject_bonf"] and r["reject_max"] and r["crit_max"] > 1.9
    assert set(r) >= {"theta", "se", "t", "crit_bonf"}


@pytest.mark.parametrize("kind", ["rom", "diff"])
def test_max_rule_is_not_more_liberal_than_a_per_contrast_5_percent_rule(kind):
    rng = np.random.default_rng(4)
    rej_max = 0
    for _ in range(100):
        M = np.exp(rng.normal(0, 0.3, (59, 1))) * rng.chisquare(5, (59, 3)) / 5
        rej_max += h1_rms2.bootstrap_t(M, rng, kind, B=199)["reject_max"]
    assert rej_max <= 16                                   # nominal 5%; loose bound for 100 reps


def test_block_se_reduces_to_iid_se_for_block_one_and_is_larger_for_persistent_series():
    rng = np.random.default_rng(5)
    u = rng.standard_normal(59)
    assert np.isclose(h1_rms2._se_blocks(u, 1), u.std(ddof=1) / np.sqrt(59))
    x = np.zeros(2000); x[0] = 1
    for i in range(1, 2000):
        x[i] = 0.8 * x[i - 1] + rng.standard_normal()
    assert h1_rms2._se_blocks(x, 10) > 1.5 * h1_rms2._se_blocks(x, 1)


def test_jackknife_log_ratio_is_returned_for_rom_only():
    rng = np.random.default_rng(6)
    M = rng.chisquare(5, (59, 3)) / 5
    assert "theta_jk" in h1_rms2.bootstrap_t(M, rng, "rom", B=99)
    assert "theta_jk" not in h1_rms2.bootstrap_t(M, rng, "diff", B=99)


def test_block_resampling_uses_runs_of_consecutive_days_and_keeps_each_days_cross_section_intact():
    from quantlab.research.inference import resample_days
    rng = np.random.default_rng(7)
    idx = resample_days(59, 50, rng, block=5)
    assert idx.shape == (50, 59) and idx.min() >= 0 and idx.max() <= 58
    blocks = idx[:, :55].reshape(50, 11, 5)                                # 11 full blocks of 5 days
    assert (np.diff(blocks, axis=2) == 1).all()                                                  # consecutive days within a block
    # a day's three period values (already averaged over stocks) always travel together
    day = np.arange(59.0)
    M = np.stack([day, 10 * day, 100 * day], axis=1)
    Mb = M[idx]
    assert np.allclose(Mb[..., 1], 10 * Mb[..., 0]) and np.allclose(Mb[..., 2], 100 * Mb[..., 0])
