"""H1 calibration, STAGE 0: Monte-Carlo precision and sample-size calculations for the proposed acceptance gates.
Pure arithmetic with exact binomial probabilities; NO simulation, no data.
Output: outputs/milestone4/h1_calibration/stage0/mc_precision/*.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "milestone4" / "h1_calibration" / "stage0" / "mc_precision"
Z = 1.959964


def wilson_upper(k, n):
    p = k / n
    d = 1 + Z * Z / n
    return ((p + Z * Z / (2 * n)) + Z * np.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n))) / d


def pass_prob(p_true, n, lo, hi, upper_max):
    """P(point estimate in [lo,hi] and Wilson upper <= upper_max) for k ~ Binomial(n, p_true)."""
    k = np.arange(0, n + 1)
    rate = k / n
    ok = (rate >= lo - 1e-12) & (rate <= hi + 1e-12) & (wilson_upper(k, n) <= upper_max + 1e-12)
    return float(stats.binom.pmf(k[ok], n, p_true).sum())


def main():
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files.")
    OUT.mkdir(parents=True, exist_ok=True)
    ns = [2000, 5000, 10000, 20000, 40000, 100000]
    t1 = pd.DataFrame([{"n_simulations": n, "mc_se_points_at_5pct": 100 * np.sqrt(.05 * .95 / n),
                        "wilson95_half_width_points_at_5pct": 100 * Z * np.sqrt(.05 * .95 / n),
                        "band_half_width_0.5pt_in_SE_units": 0.5 / (100 * np.sqrt(.05 * .95 / n))} for n in ns])
    t1.to_csv(OUT / "mc_se_by_n.csv", index=False)

    rows = []
    tiers = {"A core [4.5,5.5], Wilson upper<=6.0": (0.045, 0.055, 0.060),
             "B stress [4.0,6.0], Wilson upper<=6.5": (0.040, 0.060, 0.065)}
    for tier, (lo, hi, up) in tiers.items():
        for n in (10000, 20000, 40000):
            for p in (0.040, 0.045, 0.048, 0.050, 0.052, 0.055, 0.058, 0.060, 0.065, 0.070):
                rows.append({"tier": tier, "n": n, "true_rejection_rate": p, "P_gate_passes": pass_prob(p, n, lo, hi, up)})
    t2 = pd.DataFrame(rows)
    t2.to_csv(OUT / "gate_pass_probability.csv", index=False)

    rows = []
    for tier, (lo, hi, up) in tiers.items():
        for n in (10000, 20000, 40000, 80000):
            pf = 1 - pass_prob(0.05, n, lo, hi, up)
            for K in (1, 24, 48, 96, 192):
                rows.append({"tier": tier, "n": n, "cells_K": K, "P_false_fail_one_cell_at_true_5pct": pf,
                             "P_at_least_one_false_fail_in_K_cells": 1 - (1 - pf) ** K})
    t3 = pd.DataFrame(rows)
    t3.to_csv(OUT / "familywise_false_fail.csv", index=False)

    # smallest n (multiples of 5000) so that K independent cells at a true 5.0% all pass with prob >= 0.95
    rows = []
    for tier, (lo, hi, up) in tiers.items():
        for K in (24, 48, 96, 192):
            need = None
            for n in range(5000, 400001, 5000):
                if pass_prob(0.05, n, lo, hi, up) ** K >= 0.95:
                    need = n
                    break
            rows.append({"tier": tier, "cells_K": K, "n_needed_per_cell_for_95pct_joint_pass_at_true_5pct": need})
    t4 = pd.DataFrame(rows)
    t4.to_csv(OUT / "n_needed_for_joint_pass.csv", index=False)

    # power of the gate to detect a miscalibrated test (true rate p): P(fail) = 1 - P(pass)
    rows = []
    for n in (10000, 20000, 40000):
        for p in (0.055, 0.056, 0.058, 0.060, 0.065, 0.070):
            rows.append({"n": n, "true_rejection_rate": p,
                         "P_tier_A_gate_fails": 1 - pass_prob(p, n, 0.045, 0.055, 0.060)})
    pd.DataFrame(rows).to_csv(OUT / "gate_detection_power.csv", index=False)
    print(t1.round(4).to_string()); print(t3[t3.cells_K.isin([1, 96])].round(4).to_string()); print(t4.to_string())
    print(pd.DataFrame(rows).round(3).to_string())


if __name__ == "__main__":
    main()
