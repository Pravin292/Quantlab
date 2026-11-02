"""The planted H2 effects start AFTER the event bar, last k bars, stay inside the day, and the null world is untouched."""
import numpy as np
import pytest

from quantlab.calendars import US
from quantlab.research.h2_volume import K_DEFAULT, L_DEFAULT, MIN_VALID, THR_DEFAULT
from quantlab.research.nulls import simulate_raw
from quantlab.research.panel import past_baseline

N_DAYS, N = 14, US.bars_per_day


def run(seed=5, **kw):
    return simulate_raw(US, N_DAYS, np.random.default_rng(seed), df=4.0, day_vol_sd=0.0,
                        slot_vol=np.full(N, 0.001), volume_edge_boost=0.0, **kw)


def returns_and_events(raw):
    lc = np.log(raw["close"].to_numpy()).reshape(N_DAYS, N)
    r = np.diff(np.concatenate([np.full((N_DAYS, 1), np.log(100.0)), lc], axis=1), axis=1)
    V = raw["volume"].to_numpy().reshape(N_DAYS, N)
    with np.errstate(invalid="ignore", divide="ignore"):
        ev = np.nan_to_num(V / past_baseline(V, L_DEFAULT, MIN_VALID), nan=0.0) >= THR_DEFAULT
    return r, ev, V


def n_prior_events(ev, k=K_DEFAULT):
    out = np.zeros(ev.shape, int)
    for j in range(1, k + 1):
        out[:, j:] += ev[:, :-j]
    return out


def test_null_arguments_reproduce_the_default_world_exactly_and_volume_never_depends_on_effects():
    base = run()
    assert base.equals(run(fwd_vol_mult=1.0, continuation=0.0))
    eff = run(fwd_vol_mult=3.0, continuation=0.2)
    assert np.array_equal(base["volume"].to_numpy(), eff["volume"].to_numpy())      # volume drawn before, independent


def test_forward_volatility_multiplier_acts_only_on_the_k_bars_after_each_event_and_never_across_days():
    m = 3.0
    r0, ev, _ = returns_and_events(run())
    r1, ev1, _ = returns_and_events(run(fwd_vol_mult=m))
    assert ev.sum() >= 10 and (ev == ev1).all()
    q = r1 / r0
    expected = m ** n_prior_events(ev)
    assert np.allclose(q, expected, rtol=1e-8)
    assert (q[:, 0] == 1).all()                                    # nothing carries over from the previous day
    assert np.allclose(q[ev & (n_prior_events(ev) == 0)], 1.0)    # the event bar itself is untouched


def test_continuation_drift_has_event_direction_starts_after_the_event_and_lasts_k_bars():
    c = 0.5
    r0, ev, _ = returns_and_events(run())
    r1, _, _ = returns_and_events(run(continuation=c))
    n_prior = n_prior_events(ev)
    checked = 0
    for d in range(N_DAYS):
        for s in range(N):
            if n_prior[d, s] != 1:
                continue
            e = [s - j for j in range(1, K_DEFAULT + 1) if s - j >= 0 and ev[d, s - j]][0]
            if n_prior[d, e] != 0:
                continue                                           # event bar itself unaffected -> clean sign reference
            assert np.isclose(r1[d, s] - r0[d, s], c * 0.001 * np.sign(r0[d, e]), atol=1e-12)
            checked += 1
    assert checked >= 10
    untouched = n_prior == 0
    assert np.allclose(r1[untouched], r0[untouched])               # no effect before an event or outside its window
