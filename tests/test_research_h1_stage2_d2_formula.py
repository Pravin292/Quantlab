"""D2 diagnostic flag: the CONFIRMED formula and its units (confirmed by the user on 2026-11-02; see docs/17c).

    flag  <=>  observed_spread - 1.25 * reference_spread  >=  0.02

Units: both spreads are FRACTIONS of simulations (max - min rejection rate across the 4 quartiles), so 0.02 means 2 percentage points
and a spread of 0.10 means 10 percentage points.  The reference spread is the same method and the same conditioning variable in the
df-infinity cell matched on shape, market and sample size.  This is a JUDGEMENT-BASED diagnostic threshold, not a statistical test.
The implementation compares with a 1e-12 tolerance (0.02 - 1e-12) so that a case that is exactly on the boundary in decimal arithmetic
is not missed because of floating-point rounding; the tolerance is about 1e-10 percentage points and never matters otherwise.

This file is NOT part of the frozen Stage 2 input manifest (it was added afterwards, see frozen_stage2_inputs_addendum.sha256).
"""
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))

from quantlab.research import h1_stage2 as s2                           # noqa: E402
import stage2_common as sc                                              # noqa: E402


def confirmed_formula(spread, reference):
    """The confirmed rule written independently of the implementation, in exact decimal arithmetic."""
    from decimal import Decimal
    return Decimal(str(spread)) - Decimal("1.25") * Decimal(str(reference)) >= Decimal("0.02")


def test_constants_and_units():
    assert s2.D2_RATIO == 1.25 and s2.D2_MIN_EXCESS == 0.02                # 0.02 = 2 percentage points when spreads are fractions
    assert s2.D2_MIN_EXCESS * 100 == 2.0


def test_implementation_equals_the_confirmed_formula_on_a_dense_grid_including_exact_boundaries():
    values = [round(x, 4) for x in np.arange(0.0, 0.31, 0.0025)]
    for spread, ref in itertools.product(values, values):
        assert s2.d2_flag(spread, ref) == confirmed_formula(spread, ref), (spread, ref)


def test_exact_boundary_cases():
    assert s2.d2_flag(0.100, 0.064)             # 0.100 - 0.080 = 0.020 exactly: flagged ("at least")
    assert not s2.d2_flag(0.0999, 0.064)         # 0.0199: not flagged
    assert s2.d2_flag(0.02, 0.0)                 # no reference gradient: 2 points of spread is enough
    assert not s2.d2_flag(0.0199, 0.0)
    assert not s2.d2_flag(0.0, 0.0)


def test_it_is_the_stricter_reading_not_the_difference_to_the_reference():
    # alternative reading 'spread - reference >= 0.02' would flag these; the confirmed formula must not
    assert not s2.d2_flag(0.090, 0.060) and (0.090 - 0.060) >= 0.02
    assert not s2.d2_flag(0.30, 0.25) and (0.30 - 0.25) >= 0.02                  # 0.30 - 0.3125 < 0.02
    # and it flags a large excess
    assert s2.d2_flag(0.30, 0.10)


def test_a_larger_reference_spread_makes_the_flag_harder_to_trigger():
    assert s2.d2_flag(0.12, 0.05) and not s2.d2_flag(0.12, 0.09)


def test_summariser_uses_this_function_and_reports_fractions():
    src = (ROOT / "scripts/milestone4/stage2_summarise.py").read_text()
    assert "s2.d2_flag(sp, sp_ref)" in src                                         # no second implementation of the rule
    assert "d2_flag_judgement_based" in src                                        # the output column keeps the 'judgement-based' label
    assert src.count("d2_flag(") == 1


def test_unmatched_reference_labels_are_preserved_for_exactly_the_12_cells():
    plan = sc.load_plan()
    label = plan.apply(lambda r: s2.reference_label(r.dependence, float(r.day_vol_sd)), axis=1)
    gated = plan["tier"] != "C"
    assert s2.UNMATCHED_LABEL == "reference not matched on dependence / day-volatility"
    assert (gated & (label != "")).sum() == 12 and set(label[gated & (label != "")]) == {s2.UNMATCHED_LABEL}
    assert plan[gated & (label != "") & plan.apply(lambda r: s2.in_advancement_scope(r["tier"], int(r.n_days)), axis=1)].dev_row.tolist() == list(range(44, 52))
    assert plan[gated & (label != "") & plan.apply(lambda r: not s2.in_advancement_scope(r["tier"], int(r.n_days)), axis=1)].dev_row.tolist() == [40, 41, 42, 43]
    assert (label[~gated] == "").all()                                              # df 3 cells: exact references


def test_flag_in_an_unmatched_cell_keeps_its_label_in_the_summary_output(tmp_path):
    import subprocess
    c3, dev, summ = tmp_path / "c3", tmp_path / "dev", tmp_path / "sum"
    def run(args):
        r = subprocess.run([sys.executable] + args, capture_output=True, text=True, cwd=ROOT)
        assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
    run(["scripts/milestone4/stage2_run_c3_training.py", "--smoke", "--out", str(c3)])
    run(["scripts/milestone4/stage2_run_development.py", "--smoke", "--out", str(dev), "--c3-table", str(c3 / "c3_critical_values.csv"), "--rows", "2,44,48", "--n", "40"])
    run(["scripts/milestone4/stage2_summarise.py", "--dev", str(dev), "--out", str(summ), "--rows", "2,44,48"])
    cc = pd.read_csv(summ / "stage2_conditional_calibration.csv", keep_default_na=False)
    assert (cc[cc.dev_row.isin([44, 48])].d2_label == s2.UNMATCHED_LABEL).all()
    assert (cc[cc.dev_row == 2].d2_label == "").all()
