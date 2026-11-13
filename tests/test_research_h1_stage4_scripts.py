"""Tests for the Stage 4 runners (scripts/milestone4/stage4_*.py): smoke runs in temporary folders, the null-check gate, resume/overwrite rules, seed namespaces.
Implementation checks only (not statistical validation). Nothing here touches the real Stage 4 output folders."""
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))
import stage4_common as c4                                                  # noqa: E402


def run(args):
    return subprocess.run([sys.executable] + args, capture_output=True, text=True, cwd=ROOT)


def test_common_helpers_match_the_preregistration():
    c, m1, v = c4.trunc_moments(4)
    pre = pd.read_csv(ROOT / "outputs/milestone4/h1_calibration/stage4_prereg/truncated_moment_design.csv")
    row = pre[pre.component == "c: open and close (t4)"].iloc[0]
    assert abs(m1 - row.exact_truncated_E_e2) < 1e-9 and abs(c - row.cutoff_c) < 1e-9
    assert abs(c4.c3_value_59() - 3.298658000460969) < 1e-12
    expected = {2: ("G", "E", "NSE"), 3: ("G", "E", "US"), 4: ("G", "D5", "NSE"), 5: ("G", "D5", "US"), 26: ("T4", "E", "NSE"), 27: ("T4", "E", "US"), 28: ("T4", "D5", "NSE"), 29: ("T4", "D5", "US")}
    for row_, (tail, shape, mk) in expected.items():
        s = c4.bar_level_setup(row_)
        assert (s["tail"], s["shape"], s["market_name"]) == (tail, shape, mk) and s["df"] == (1000.0 if tail == "G" else 4.0)
    assert c4.BAR_ROWS == list(expected)


def test_seed_namespaces_are_disjoint_between_null_check_and_alternative_simulations():
    draws = {}
    for idx in range(12):
        for b in range(0, 40, 7):
            draws[("null", idx, b)] = np.random.SeedSequence(20261206, spawn_key=(100 + idx, b))
    for row in range(12):
        for i in range(0, 60, 11):
            for s in (0, 1):
                draws[("alt", row, i, s)] = np.random.SeedSequence(20261206, spawn_key=(row, i, s))
    vals = {k: tuple(np.random.default_rng(v).integers(0, 2 ** 62, 2)) for k, v in draws.items()}
    assert len(vals) == len(set(vals.values()))


def test_null_check_smoke_gate_alt_validation_resume_and_overwrite_rules(tmp_path):
    nc = tmp_path / "nc"
    assert run(["scripts/milestone4/stage4_run_null_check.py", "--scale", "0.01"]).returncode != 0                 # --scale only for smoke runs
    r = run(["scripts/milestone4/stage4_run_null_check.py", "--smoke", "--scale", "0.002", "--out", str(nc)])
    assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
    R, T, A = pd.read_csv(nc / "null_check_ratios_abef.csv"), pd.read_csv(nc / "null_check_truncated_cd.csv"), pd.read_csv(nc / "null_check_analytic.csv")
    assert len(R) == 8 and len(T) == 12 and len(A) == 4 and (A.abs_error < 1e-9).all()
    assert set(T.component) == {"open", "middle", "close", "stock 1", "stock 2", "stock 3"}
    assert pd.read_csv(nc / "null_check_outcome.csv").columns.tolist() == ["criterion", "met"]
    assert run(["scripts/milestone4/stage4_run_null_check.py", "--smoke", "--scale", "0.002", "--out", str(nc)]).returncode != 0   # no overwrite
    alt = tmp_path / "alt"
    fail_f, ok_f = tmp_path / "fail.csv", tmp_path / "ok.csv"
    pd.DataFrame([{"criterion": "x", "met": False}]).to_csv(fail_f, index=False); pd.DataFrame([{"criterion": "x", "met": True}]).to_csv(ok_f, index=False)
    r = run(["scripts/milestone4/stage4_run_alt_validation.py", "--smoke", "--out", str(alt), "--null-outcome", str(fail_f), "--rows", "0", "--n", "20"])
    assert r.returncode != 0 and "null check has not passed" in (r.stdout + r.stderr) and not alt.exists()
    args = ["scripts/milestone4/stage4_run_alt_validation.py", "--smoke", "--out", str(alt), "--null-outcome", str(ok_f), "--rows", "0,3,10", "--n", "40"]
    r = run(args); assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
    d = pd.read_parquet(alt / "cell_03.parquet")
    assert len(d) == 40 and d["sim"].tolist() == list(range(40)) and abs(d.crit_c3.iloc[0] - 3.298658000460969) < 1e-12 and not any("c1" in c or "c2" in c for c in d.columns)
    assert run(args).returncode != 0                                                                              # existing folder: no silent re-run
    assert "0 simulations this session" in run(args + ["--resume"]).stdout                                       # complete cells are skipped


def test_bar_level_and_reference_smoke(tmp_path):
    bl = tmp_path / "bl"
    r = run(["scripts/milestone4/stage4_run_bar_level.py", "--part", "sims", "--smoke", "--out", str(bl), "--cells", "0,4", "--n", "12"])
    assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
    d = pd.read_parquet(bl / "cell_04.parquet")
    assert len(d) == 12 and (d.n_days_used == 59).all() and d.valid.all()
    r = run(["scripts/milestone4/stage4_run_bar_level.py", "--part", "matrix", "--smoke", "--out", str(bl), "--cells", "0,1,4,5", "--n", "2"])
    assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
    m = pd.read_csv(bl / "same_returns_matrix_check.csv")
    assert len(m) == 8 and m.same_shape.all() and (m.max_relative_difference <= 1e-9).all()
    ref = tmp_path / "ref"
    r = run(["scripts/milestone4/stage4_run_reference.py", "--smoke", "--out", str(ref), "--per-cell", "1"])
    assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
    D, Q = pd.read_csv(ref / "reference_datasets.csv"), pd.read_csv(ref / "c3_value_rederivation.csv")
    assert len(D) == 10 and (D.rel_diff <= 1e-9).all() and (D.reject_vectorised == D.reject_reference).all()
    assert len(Q) == 5 and (Q.rel_diff <= 1e-12).all()
