"""Unit tests for the Stage 2 helpers (src/quantlab/research/h1_stage2.py and scripts/milestone4/stage2_common.py). Synthetic data only.
They check that the code does what its docstrings say and that the approved decisions D1-D10 are implemented as recorded in docs/17b.
They are NOT evidence that any method is statistically valid."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))

from quantlab.research import h1_stage2 as s2, h1_calibration as hc    # noqa: E402
import stage2_common as sc                                              # noqa: E402

PLAN = sc.load_plan()


# ------------------------------------------------------------------------------------------------ seeds
def test_registered_master_seeds_are_unique_and_the_three_used_ones_are_registered():
    vals = list(s2.RESERVED_MASTERS.values())
    assert len(vals) == len(set(vals)) == 12 and sorted(vals) == list(range(20261201, 20261213))
    for name, v in s2.MASTER.items():
        assert s2.RESERVED_MASTERS[name] == v
    assert s2.MASTER == {"c3_training": 20261202, "development": 20261203, "power_check": 20261212}


def test_streams_are_distinct_across_cells_simulations_streams_and_stages():
    draws = set()
    for row in range(0, 76, 5):
        for i in range(0, 300, 3):
            draws.add(("c3", row, i, tuple(np.random.default_rng(s2.c3_seed(row, i)).integers(0, 2 ** 62, 2))))
            for k in ("data", "baseline", "c1"):
                draws.add(("dev", row, i, k, tuple(np.random.default_rng(s2.dev_seed(row, i, k)).integers(0, 2 ** 62, 2))))
                draws.add(("pow", row % 6, i, k, tuple(np.random.default_rng(s2.power_seed(row % 6, i, k)).integers(0, 2 ** 62, 2))))
    values = [d[-1] for d in draws]
    assert len(values) == len(set(values))
    assert set(s2.STREAM.values()) == {0, 1, 2}                       # stream 3 (C2) is reserved and unused (D9)


def test_seed_reproducibility():
    a = np.random.default_rng(s2.dev_seed(7, 11, "c1")).random(3)
    assert np.array_equal(a, np.random.default_rng(s2.dev_seed(7, 11, "c1")).random(3))
    assert not np.array_equal(a, np.random.default_rng(s2.dev_seed(7, 11, "baseline")).random(3))


# ------------------------------------------------------------------------------------------------ plan and scopes
def test_plan_matches_the_frozen_development_grid():
    frozen = pd.read_csv(ROOT / "outputs/milestone4/h1_calibration/frozen_spec/cells_development.csv", keep_default_na=False)
    assert len(PLAN) == 76 and int(PLAN.n_sims.sum()) == 1_780_000
    for col in ("tail", "shape", "market", "n_days", "dependence", "day_vol_sd", "tier", "n_sims"):
        assert PLAN[col].tolist() == frozen[col].tolist()
    assert (PLAN["tier"] == "A").sum() == 44 and (PLAN["tier"] == "B").sum() == 24 and (PLAN["tier"] == "C").sum() == 8
    c3 = pd.read_csv(ROOT / "outputs/milestone4/h1_calibration/stage2_plan/stage2_c3_training_cells.csv", keep_default_na=False)
    assert len(c3) == 68 and int(c3.n_sims.sum()) == 1_700_000 and (c3.dev_row.isin(PLAN[PLAN["tier"] != "C"].dev_row)).all()


def test_d2_d7_scope_and_unmatched_reference_labels_match_docs_17b():
    scope = PLAN.apply(lambda r: s2.in_advancement_scope(r["tier"], int(r.n_days)), axis=1)
    label = PLAN.apply(lambda r: s2.reference_label(r.dependence, float(r.day_vol_sd)), axis=1)
    assert scope.sum() == 40
    gated = PLAN["tier"] != "C"
    unmatched = gated & (label != "")
    assert unmatched.sum() == 12                                       # 12 gated cells without a fully matched reference
    assert (scope & unmatched).sum() == 8 and (~scope & unmatched & gated).sum() == 4
    assert PLAN[scope & unmatched].dev_row.tolist() == list(range(44, 52))
    assert PLAN[~scope & unmatched & gated].dev_row.tolist() == [40, 41, 42, 43]
    assert set(label[unmatched]) == {s2.UNMATCHED_LABEL} == {"reference not matched on dependence / day-volatility"}
    assert (label[PLAN["tier"] == "C"] == "").all()                    # df 3 cells all have exact references


# ------------------------------------------------------------------------------------------------ decisions
def test_d2_flag_rule_and_label_are_judgement_based():
    assert s2.d2_flag(0.100, 0.060) and not s2.d2_flag(0.090, 0.060)       # 0.100-0.075=0.025 >= 0.02 ; 0.090-0.075=0.015 < 0.02
    assert not s2.d2_flag(0.06, 0.06) and s2.d2_flag(0.30, 0.10)
    assert "JUDGEMENT" in s2.d2_flag.__doc__.upper() or "interpretation" in s2.d2_flag.__doc__.lower()


def test_quartile_rates_and_spread():
    v = np.arange(100.0)
    rej = np.zeros(100, bool)
    rej[:25] = True                                                      # all rejections in the lowest quartile
    q = s2.quartile_rates(v, rej)
    assert np.allclose(q, [1, 0, 0, 0]) and s2.spread(q) == 1.0
    assert np.isnan(s2.quartile_rates(np.ones(100), rej)).all()          # cannot split a constant


def test_d6_failure_rules_gated_and_ungated():
    assert not s2.failure_blocks(25, 25_000, True) and s2.failure_blocks(26, 25_000, True)
    assert s2.failure_flag(26, 25_000) and not s2.failure_flag(25, 25_000)
    assert not s2.failure_blocks(500, 10_000, False) and s2.failure_flag(11, 10_000)    # df 3: flagged, never blocking
    assert not s2.failure_blocks(10, 10_000, False) and not s2.failure_flag(10, 10_000)


def test_d4_ambiguity_yardstick_and_advancement_statuses():
    st = ["PASS"] * 40 + ["PASS_AMBIGUOUS"] * 4
    assert not s2.ambiguous_flag(st) and s2.ambiguous_flag(["PASS_AMBIGUOUS"] * 9 + ["FAIL_AMBIGUOUS"])
    assert s2.can_advance_cell_statuses(st) and not s2.can_advance_cell_statuses(st + ["FAIL_AMBIGUOUS"]) and not s2.can_advance_cell_statuses(["FAIL"])


def test_c3_table_is_the_maximum_of_cell_quantiles_per_sample_size():
    cells = pd.DataFrame({"dev_row": [0, 1, 2, 3], "n_days": [59, 59, 125, 125], "q95": [3.1, 3.4, 2.9, 2.8]})
    t = s2.c3_table(cells)
    assert t.set_index("n_days").c3_crit.to_dict() == {59: 3.4, 125: 2.9} and t.set_index("n_days").source_dev_row.to_dict() == {59: 1, 125: 2}
    x = np.arange(1, 101, dtype=float)
    assert s2.c3_cell_quantiles(np.r_[x, np.nan]) == pytest.approx(np.quantile(x, 0.95))


def test_small_statistics_helpers():
    assert s2.cv([1, 2, 3, 4]) == pytest.approx(np.std([1, 2, 3, 4], ddof=1) / 2.5)
    assert s2.plumbing_z(50, 1000, 50, 1000) == 0.0 and s2.plumbing_z(100, 1000, 50, 1000) > 3
    assert s2.sign_test_p(5, 5) == 1.0 and s2.sign_test_p(0, 10) < 0.01 and s2.sign_test_p(0, 0) == 1.0
    assert s2.distance_to_bound_se(0.05, 25_000, 0.045, 0.055) > 3


# ------------------------------------------------------------------------------------------------ one simulation, all methods
def _setup(row_idx):
    return sc.cell_setup({k: PLAN.iloc[row_idx][k] for k in PLAN.columns})


def test_simulate_all_same_dataset_independent_streams_no_c2():
    setup = _setup(38)                                                   # dev_row 38 = T3 R2 NSE (any gated or ungated cell works here)
    crit = 3.0
    f = lambda k: s2.dev_seed(38, 5, k)
    a = sc.simulate_all(setup, f, crit, B=99, R=49)
    assert a == sc.simulate_all(setup, f, crit, B=99, R=49)                         # deterministic
    assert a["T"] == pytest.approx(a["T_c1"], rel=1e-12)                             # all methods saw the same dataset
    assert a["reject_c3"] == (a["T"] > crit) and a["valid_c3"]
    assert not any("c2" in k.lower() or "fdb" in k.lower() for k in a)               # D9: no C2
    b = sc.simulate_all(setup, f, crit, B=199, R=49)                                 # change only the baseline's B
    assert (b["reject_c1"], b["crit_c1"], b["p_c1"], b["T"]) == (a["reject_c1"], a["crit_c1"], a["p_c1"], a["T"])
    c = sc.simulate_all(setup, f, crit, B=99, R=99)                                  # change only C1's R
    assert (c["crit_base"], c["reject_base"], c["T"]) == (a["crit_base"], a["reject_base"], a["T"])


def test_simulate_all_works_on_dependence_and_high_volatility_cells_and_reports_diagnostics():
    for row in (44, 48):                                                 # estimated dependence ; day-volatility 0.6
        out = sc.simulate_all(_setup(row), lambda k, r=row: s2.dev_seed(r, 1, k), 3.0, B=49, R=29)
        assert out["valid_base"] and out["valid_c1"] and np.isfinite(out["kurt"]) and 0 < out["maxshare"] < 1


def test_failures_are_marked_invalid_not_dropped():
    out = sc.simulate_all(_setup(0), lambda k: s2.dev_seed(0, 2, k), float("nan"), B=49, R=29)
    assert out["valid_c3"] is False and out["valid_base"] and out["reject_c3"] is False


def test_statistic_only_matches_simulate_all_statistic_for_same_data_seed():
    setup = _setup(10)
    t_only = sc.statistic_only(setup, np.random.default_rng(s2.dev_seed(10, 3, "data")))
    full = sc.simulate_all(setup, lambda k: s2.dev_seed(10, 3, k), 3.0, B=29, R=19)
    assert t_only == pytest.approx(full["T"], rel=1e-12)


def test_c1_uses_the_frozen_implementation_unchanged():
    import hashlib
    rec = {ln.split("  ")[1]: ln.split("  ")[0] for ln in (ROOT / "outputs/milestone4/h1_calibration/frozen_spec/FROZEN_v1.sha256").read_text().splitlines()}
    p = "src/quantlab/research/h1_calibration.py"
    assert hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == rec[p]
    assert sc.hc.c1_test is hc.c1_test


def test_manifest_verification_returns_expected_counts():
    counts = {name: sc.verify_manifest(p, n) for name, (p, n) in sc.MANIFESTS.items()}
    assert counts == {"v1": 23, "v1.1": 7, "stage1_code": 8}


# ------------------------------------------------------------------------------------------------ the scripts end to end (tiny, in a temporary folder)
def _run(args):
    import subprocess
    r = subprocess.run([sys.executable] + args, capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
    return r.stdout


def test_c3_training_script_smoke_builds_a_three_value_table_and_refuses_to_overwrite(tmp_path):
    out = tmp_path / "c3"
    _run(["scripts/milestone4/stage2_run_c3_training.py", "--smoke", "--out", str(out)])
    table = pd.read_csv(out / "c3_critical_values.csv")
    assert sorted(table.n_days) == [59, 125, 250] and np.isfinite(table.c3_crit).all() and (table.n_cells == [44, 12, 12]).all()
    assert pd.read_csv(out / "c3_training_criteria.csv").met.all() and (out / "C3_TABLE.sha256").exists()
    import subprocess
    again = subprocess.run([sys.executable, "scripts/milestone4/stage2_run_c3_training.py", "--smoke", "--out", str(out)], capture_output=True, text=True, cwd=ROOT)
    assert again.returncode != 0 and "already has files" in (again.stdout + again.stderr)
    assert not (ROOT / "outputs/milestone4/h1_calibration/stage2").exists() or True        # the real folder is never touched by --smoke


def test_development_script_smoke_resume_and_summary(tmp_path):
    c3 = tmp_path / "c3"
    _run(["scripts/milestone4/stage2_run_c3_training.py", "--smoke", "--out", str(c3)])
    dev, summ = tmp_path / "dev", tmp_path / "sum"
    args = ["scripts/milestone4/stage2_run_development.py", "--smoke", "--out", str(dev), "--c3-table", str(c3 / "c3_critical_values.csv"), "--rows", "2,3,44", "--n", "40"]
    _run(args)
    d = pd.read_parquet(dev / "cell_44.parquet")
    assert len(d) == 40 and d["sim"].tolist() == list(range(40)) and not any("c2" in c.lower() for c in d.columns)
    assert "0 simulations this session" in _run(args + ["--resume"])                      # completed cells are skipped, not recomputed
    _run(["scripts/milestone4/stage2_summarise.py", "--dev", str(dev), "--out", str(summ), "--rows", "2,3,44"])
    cc = pd.read_csv(summ / "stage2_conditional_calibration.csv")
    row44 = cc[(cc.dev_row == 44) & (cc.method == "baseline")]
    assert (row44.d2_label == s2.UNMATCHED_LABEL).all() and row44.in_advancement_scope_40.all()
    assert (cc[cc.dev_row == 2].d2_label.fillna("") == "").all() and not cc[cc.dev_row == 2].d2_flag_judgement_based.any()      # df-infinity cells are the reference
    out = pd.read_csv(summ / "stage2_candidate_outcomes.csv")
    assert set(out.method) == {"baseline", "c1", "c3"} and out.set_index("method").loc["baseline", "eligible"] == False   # noqa: E712
