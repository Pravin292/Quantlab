import numpy as np
import pytest

from quantlab.calendars import NSE, US
from quantlab.research import dependence as dep, direct_sim as ds, h1_rms
from quantlab.research.direct_bridge import returns_to_table


@pytest.mark.parametrize("market,mk", [(NSE, "NSE"), (US, "US")])
def test_direct_period_matrix_equals_bar_level_pipeline_for_identical_returns(market, mk):
    prof = dep.shaped_profile(market, 2.0, 2.0, 4.0, 0.4)
    rng = np.random.default_rng(11)
    r2 = ds.simulate_returns_sq(market, 3, 40, rng, profile=prof, df=4.0, day_vol_sd=0.3, share=0.4, phi=0.5, ret_corr=0.3)
    M_direct = ds.period_matrix(r2, ds.used_slot_index(market))
    tabs = [returns_to_table(market, np.sqrt(r2[i]), f"S{i}", rng, nse_feed_quirks=True) for i in range(3)]
    M_pipe = h1_rms.market_matrix([h1_rms.mean_square_panel(t, mk) for t in tabs])
    assert M_pipe.shape == M_direct.shape
    assert np.allclose(M_pipe, M_direct, rtol=1e-9, atol=0)
