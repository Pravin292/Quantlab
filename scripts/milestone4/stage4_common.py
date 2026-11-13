"""H1 calibration, STAGE 4: shared pieces (manifest checks, the alternative-process one-simulation function, the bar-level route, truncated-moment helper).
Reads frozen files; writes nothing.   ALL DATA SIMULATED.   Candidate = C3 only (frozen values); the baseline bootstrap-t is a reference.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import integrate, stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage2_common as sc                                                 # noqa: E402
import stage3_common as c3c                                                # noqa: E402
from quantlab.research import direct_sim as ds, h1_calibration as hc, h1_calibration_v11 as v11, h1_rms, h1_stage1 as s1, h1_stage4 as s4   # noqa: E402
from quantlab.research.h1_rms2 import bootstrap_t                          # noqa: E402
import run_h1_inference as ri                                             # noqa: E402
import run_h1_next as nx                                                  # noqa: E402

B = c3c.B
S4 = B / "stage4"
PREREG = B / "stage4_prereg"
STAGE4_INPUTS = B / "frozen_stage4_inputs.sha256"
ALT_CELLS = B / "frozen_spec" / "cells_alternative_dgps.csv"
MARKETS = sc.MARKETS
MASTER = {"alt": 20261206, "bar_level": 20261207, "reference": 20261208}
BAR_ROWS = [2, 3, 4, 5, 26, 27, 28, 29]                 # Stage 3 validation rows used for the bar-level check (cell_index 0-7)
C3_59 = None


def verify_all(stage4_inputs: bool = True) -> dict:
    """All earlier manifests (v1, v1.1, Stage 1-3, C3 tables) plus, normally, the Stage 4 inputs manifest; also the free-disk check."""
    out = c3c.verify_all(stage3_inputs=True, c3_intermediate=True)
    if stage4_inputs:
        out["stage4_inputs"] = sc.verify_manifest(STAGE4_INPUTS)
    return out


def c3_value_59() -> float:
    """Frozen C3 critical value for 59 days (Stage 2 table)."""
    return float(pd.read_csv(c3c.STAGE2_C3_TABLE).set_index("n_days").loc[59, "c3_crit"])


def alt_setup(cell: dict) -> dict:
    """Market, used slots and the frozen shape-E profile for one alternative-process cell."""
    mk = cell["market"]
    return dict(market=MARKETS[mk], idx=ds.used_slot_index(MARKETS[mk]), profile=ri.profile_for(mk, cell["shape"], 1.0), n_days=int(cell["n_days"]))


def simulate_alt_one(setup: dict, process: str, seed_fn, crit_c3: float, Bboot: int = 999) -> dict:
    """One dataset of an alternative process; C3 (frozen value) and the baseline bootstrap-t (reference) applied to it. Failures are marked invalid, never dropped."""
    r2 = s4.simulate_alt_returns_sq(process, setup["market"], 3, setup["n_days"], np.random.default_rng(seed_fn("data")), setup["profile"])
    M = ds.period_matrix(r2, setup["idx"])
    r2_used, groups = hc.to_used(r2, setup["idx"])
    out = {}
    try:
        out["T"] = float(hc.max_abs_t(M))
    except Exception:
        out["T"] = float("nan")
    try:
        res = bootstrap_t(M, np.random.default_rng(seed_fn("baseline")), "rom", B=Bboot)
        ok = bool(np.isfinite(res["t"]).all() and np.isfinite(res["crit_max"]))
        out.update(valid_base=ok, reject_base=bool(res["reject_max"]) if ok else False, crit_base=float(res["crit_max"]))
    except Exception:
        out.update(valid_base=False, reject_base=False, crit_base=float("nan"))
    ok = bool(np.isfinite(out["T"]) and np.isfinite(crit_c3))
    out.update(valid_c3=ok, reject_c3=bool(out["T"] > crit_c3) if ok else False, crit_c3=float(crit_c3))
    try:
        out.update(s1.tail_diagnostics([r2_used[:, :, g] for g in groups], M))
    except Exception:
        out.update(kurt=float("nan"), maxshare=float("nan"), maxshare_open=float("nan"), maxshare_middle=float("nan"), maxshare_close=float("nan"))
    return out


def trunc_moments(df: float, q: float = 0.999):
    """Exact E[e^2 1{|e|<=c}] and Var of it for a unit-variance Student-t(df) shock, c = its two-sided q-quantile."""
    sc_ = v11.t_unit_scale(df)
    c = stats.t(df).ppf((1 + q) / 2) * sc_
    pdf = lambda x: stats.t(df).pdf(x / sc_) / sc_
    m1 = 2 * integrate.quad(lambda x: x ** 2 * pdf(x), 0, c, epsabs=1e-13, epsrel=1e-12)[0]
    m2 = 2 * integrate.quad(lambda x: x ** 4 * pdf(x), 0, c, epsabs=1e-13, epsrel=1e-12)[0]
    return float(c), float(m1), float(m2 - m1 ** 2)


def bar_level_setup(row: int) -> dict:
    """Setup of one bar-level cell from its Stage 3 validation row (tail df, shape profile, market)."""
    cells = c3c.load_validation_cells()
    c = cells.loc[row]
    return dict(row=row, market_name=c["market"], market=MARKETS[c["market"]], df=s1.DF_CODE[c["tail"]], profile=ri.profile_for(c["market"], c["shape"], 1.0),
                day_vol_sd=float(c["day_vol_sd"]), tail=c["tail"], shape=c["shape"])


def bar_level_matrix(setup: dict, rng: np.random.Generator) -> np.ndarray:
    """The REAL bar-level route: simulate_table (raw bars) -> clean -> bar table -> period mean squares -> day matrix, for 3 stocks and 59 days (M4b convention)."""
    quirks = setup["market_name"] == "NSE"
    tabs = [nx.simulate_table(setup["market"], f"S{i}", 59, rng, nse_feed_quirks=quirks, day_vol_sd=setup["day_vol_sd"], df=setup["df"], slot_vol=setup["profile"],
                              rho=0.0, intraday_regime_sd=0.0) for i in range(3)]
    return h1_rms.market_matrix([h1_rms.mean_square_panel(t, setup["market_name"]) for t in tabs])
