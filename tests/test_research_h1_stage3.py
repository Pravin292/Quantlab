"""Unit tests for the Stage 3 pieces (src/quantlab/research/h1_stage3.py, scripts/milestone4/stage3_*.py). Synthetic data only.
They check that the code does what its docstrings say and that the frozen validation grid is used as specified. They are NOT evidence of statistical validity."""
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))

from quantlab.research import h1_stage2 as s2, h1_stage3 as s3              # noqa: E402
import stage3_common as c3c                                                 # noqa: E402

CELLS = c3c.load_validation_cells()
PLAN = pd.read_csv(ROOT / "outputs/milestone4/h1_calibration/stage3_plan/stage3_cells_plan.csv", keep_default_na=False)


def run(args):
    r = subprocess.run([sys.executable] + args, capture_output=True, text=True, cwd=ROOT)
    return r


def test_seed_registry_is_distinct_and_the_new_power_seed_is_new():
    reg = s3.all_registered_masters()
    assert len(set(reg.values())) == len(reg) == 13
    assert s3.MASTER == {"validation_cells": 20261204, "validation_intermediate": 20261205, "c3_intermediate": 20261209, "validation_power": 20261213}
    assert 20261213 not in s2.RESERVED_MASTERS.values()
    assert [s3.val_master(r) for r in (0, 75, 76, 95)] == [20261204, 20261204, 20261205, 20261205]


def test_validation_streams_are_distinct_across_rows_simulations_streams_and_stages():
    draws = {}
    for row in range(0, 96, 5):
        for i in range(0, 200, 4):
            for k in ("data", "baseline"):
                draws[("val", row, i, k)] = s3.val_seed(row, i, k)
                draws[("pow", row % 6, i, k)] = s3.power_seed(row % 6, i, k)
                draws[("dev", row % 76, i, k)] = s2.dev_seed(row % 76, i, "data" if k == "data" else "baseline")        # Stage 2 development streams
            draws[("c3i", row % 24, i)] = s3.c3i_seed(row % 24, i)
    values = {key: tuple(np.random.default_rng(seed).integers(0, 2 ** 62, 2)) for key, seed in draws.items()}
    assert len(values) == len(set(values.values()))                         # distinct keys always give distinct random streams


def test_plan_is_the_frozen_validation_grid():
    assert len(CELLS) == 96 and int(CELLS.n_sims.sum()) == 2_280_000
    dev = pd.read_csv(ROOT / "outputs/milestone4/h1_calibration/frozen_spec/cells_development.csv", keep_default_na=False)
    cols = ["tail", "shape", "market", "n_days", "dependence", "day_vol_sd", "tier", "n_sims"]
    assert CELLS.iloc[:76][cols].reset_index(drop=True).equals(dev[cols])
    assert CELLS.groupby("tier").size().to_dict() == {"A": 54, "B": 34, "C": 8}
    new = CELLS.iloc[76:]
    assert set(new["tail"]) == {"T7", "T5"} and set(new.n_days) == {59, 90, 180} and set(new["shape"]) == {"E", "D1.5", "D3.0"}
    assert (PLAN.val_row == CELLS.index).all() and PLAN.master_seed.tolist() == [s3.val_master(r) for r in range(96)]


def test_d2_reference_availability_matches_the_grid():
    assert int((PLAN.d2_reference_row >= 0).sum()) == 80
    none = PLAN[PLAN.d2_reference_row < 0]
    assert len(none) == 16 and set(none.n_days) <= {59, 90, 180} and set(none["shape"]) <= {"E", "D1.5", "D3.0"}
    assert set(none[none.n_days == 59]["shape"]) == {"D1.5", "D3.0"} and set(none[none.n_days != 59].n_days) == {90, 180}
    assert s3.reference_row(CELLS, 76) is not None                       # T7 E NSE 59 has a matched df-infinity cell (row 2)
    assert CELLS.loc[s3.reference_row(CELLS, 76), "tail"] == "G"


def test_new_shapes_are_exponential_profiles_with_equal_period_rms():
    from quantlab.research import direct_sim as ds
    import run_h1_next as nx
    for mk in ("NSE", "US"):
        market = c3c.sc.MARKETS[mk]
        idx = ds.used_slot_index(market)
        for shape, tau in (("D1.5", 1.5), ("D3.0", 3.0)):
            setup = c3c.cell_setup(dict(tail="T7", shape=shape, market=mk, n_days=59, dependence="none", day_vol_sd=0.3))
            assert np.allclose(setup["profile"], nx.exp_profile(market, tau, 1.0))
            rms = [float(np.sqrt(np.mean(setup["profile"][i] ** 2))) for i in idx]
            assert np.allclose(rms, rms[0], rtol=1e-9)                   # the null (equal period RMS) holds by construction
        d5 = c3c.cell_setup(dict(tail="T7", shape="D5", market=mk, n_days=59, dependence="none", day_vol_sd=0.3))["profile"]
        assert not np.allclose(d5, c3c.cell_setup(dict(tail="T7", shape="D1.5", market=mk, n_days=59, dependence="none", day_vol_sd=0.3))["profile"])
    assert s3.DF_CODE["T7"] == 7.0 and s3.DF_CODE["T5"] == 5.0 and s3.DF_CODE["G"] == 1000.0


def test_c3_value_lookup_uses_the_right_frozen_table():
    t2, t3 = {59: 3.3, 125: 2.9, 250: 2.8}, {90: 3.0, 180: 2.85}
    assert [s3.c3_value(n, t2, t3) for n in (59, 90, 125, 180, 250)] == [3.3, 3.0, 2.9, 2.85, 2.8]
    with pytest.raises(KeyError):
        s3.c3_value(100, t2, t3)
    frozen = pd.read_csv(c3c.STAGE2_C3_TABLE).set_index("n_days").c3_crit.to_dict()
    assert abs(frozen[59] - 3.298658000460969) < 1e-12


def _setup(row):
    return c3c.cell_setup({k: CELLS.loc[row, k] for k in CELLS.columns})


def test_simulate_one_is_deterministic_with_independent_streams_and_no_other_candidates():
    f = lambda k: s3.val_seed(76, 3, k)
    a = c3c.simulate_one(_setup(76), f, 3.0, B=99)
    assert a == c3c.simulate_one(_setup(76), f, 3.0, B=99)
    assert a["reject_c3"] == (a["T"] > 3.0) and a["valid_c3"] and a["valid_base"]
    b = c3c.simulate_one(_setup(76), f, 3.0, B=199)                       # change only the baseline's B: data, T and C3 unchanged
    assert (b["T"], b["reject_c3"], b["kurt"], b["maxshare"]) == (a["T"], a["reject_c3"], a["kurt"], a["maxshare"])
    assert not any(("c1" in k.lower()) or ("c2" in k.lower()) or ("fdb" in k.lower()) for k in a)
    bad = c3c.simulate_one(_setup(2), lambda k: s3.val_seed(2, 1, k), float("nan"), B=49)
    assert bad["valid_c3"] is False and bad["reject_c3"] is False and bad["valid_base"]


def test_frozen_inputs_are_intact_before_stage3():
    counts = c3c.verify_all(stage3_inputs=False)
    assert counts["v1"] == 23 and counts["v1.1"] == 7 and counts["stage1_code"] == 8 and counts["stage2_inputs"] == 18 and counts["stage2_addendum"] == 2 and counts["stage2_c3_table"] == 2


def test_scripts_end_to_end_in_scratch_including_the_power_refusal_rule(tmp_path):
    c3i, val, summ, pw = tmp_path / "c3i", tmp_path / "val", tmp_path / "sum", tmp_path / "pow"
    assert run(["scripts/milestone4/stage3_run_c3_intermediate.py", "--smoke", "--out", str(c3i)]).returncode == 0
    tab = pd.read_csv(c3i / "c3_intermediate_values.csv")
    assert sorted(tab.n_days) == [90, 180] and np.isfinite(tab.c3_crit).all() and (tab.n_cells == 12).all()
    assert pd.read_csv(c3i / "c3_intermediate_criteria.csv").met.all()
    args = ["scripts/milestone4/stage3_run_validation.py", "--smoke", "--out", str(val), "--c3-table-59-250", str(c3c.STAGE2_C3_TABLE), "--c3-table-90-180", str(c3i / "c3_intermediate_values.csv"),
            "--rows", "2,77,79,86", "--n", "40"]
    r = run(args); assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
    d = pd.read_parquet(val / "cell_77.parquet")                          # T7 E NSE 90 days uses the 90-day table
    assert len(d) == 40 and abs(d.crit_c3.iloc[0] - float(tab.set_index("n_days").loc[90, "c3_crit"])) < 1e-12
    assert abs(pd.read_parquet(val / "cell_79.parquet").crit_c3.iloc[0] - 3.298658000460969) < 1e-12   # D1.5 at 59 days uses the frozen 59-day value
    again = run(args)
    assert again.returncode != 0 and "already has files" in (again.stdout + again.stderr)             # no silent re-run of locked cells
    assert run(args + ["--resume"]).returncode == 0 and "0 simulations this session" in run(args + ["--resume"]).stdout
    r = run(["scripts/milestone4/stage3_summarise.py", "--val", str(val), "--out", str(summ), "--rows", "2,77,79,86"]); assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
    cc = pd.read_csv(summ / "stage3_conditional_calibration.csv", keep_default_na=False)
    assert cc[cc.val_row.isin([77, 79])].d2_label.str.startswith("NO MATCHED").all() and not cc[cc.val_row.isin([77, 79])].d2_computable.any()
    out = pd.read_csv(summ / "stage3_candidate_outcome.csv")
    assert set(out["method"]) == {"baseline", "c3"}
    # power refusal rule: FAIL outcome -> refuses; allowed outcome -> runs
    fail_file = tmp_path / "fail.csv"; pd.DataFrame([{"method": "c3", "v1_1_candidate_outcome": "FAIL"}]).to_csv(fail_file, index=False)
    ok_file = tmp_path / "ok.csv"; pd.DataFrame([{"method": "c3", "v1_1_candidate_outcome": "PASS_CLEAR"}]).to_csv(ok_file, index=False)
    r = run(["scripts/milestone4/stage3_run_power.py", "--smoke", "--out", str(pw), "--outcome-file", str(fail_file), "--c3-table", str(c3c.STAGE2_C3_TABLE)])
    assert r.returncode != 0 and "reported only after calibration passes" in (r.stdout + r.stderr) and not pw.exists()
    r = run(["scripts/milestone4/stage3_run_power.py", "--smoke", "--out", str(pw), "--outcome-file", str(ok_file), "--c3-table", str(c3c.STAGE2_C3_TABLE), "--n", "40"])
    assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
    assert len(pd.read_csv(pw / "power_ratio_and_flag.csv")) == 6
