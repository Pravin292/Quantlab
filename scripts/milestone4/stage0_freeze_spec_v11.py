"""H1 calibration, SPEC v1.1: write the v1.1 addenda (A1-A6) as NEW files beside the untouched v1 files, and a new SHA-256 manifest.
Runs no calibration simulation. Refuses to run if the output folder already has files. Reads (never writes) the v1 files.
Output: outputs/milestone4/h1_calibration/frozen_spec_v1_1/
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from quantlab.research import h1_calibration_v11 as v11                       # noqa: E402

V1 = ROOT / "outputs" / "milestone4" / "h1_calibration" / "frozen_spec"
OUT = ROOT / "outputs" / "milestone4" / "h1_calibration" / "frozen_spec_v1_1"
BENCH = ROOT / "outputs" / "milestone4" / "h1_calibration" / "stage0" / "benchmark" / "single_core_timing.csv"
SPEEDUP = 4.0


def sha(path):
    """SHA-256 hex digest of a file."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def c3_training_cells():
    """The 24 C3 training cells at 90 and 180 days (12 per size) with 25,000 simulations each."""
    rows = [dict(tail=t, shape=s, market=m, n_days=nd, dependence="none", day_vol_sd=0.3, n_sims=v11.C3_TRAINING_INTERMEDIATE["sims_per_cell"],
                 purpose="C3 training only (never evaluated on)", seed_name="c3_training_intermediate")
            for nd in (90, 180) for t in ("G", "T6", "T4") for s in ("E", "D5") for m in ("NSE", "US")]
    return pd.DataFrame(rows)


def redundancy_table():
    """For each tier and n: do the Wilson-upper clause and the 7% ceiling ever change a decision? Exhaustive over every k."""
    rows = []
    for tier in ("A", "B", "ALT"):
        for n in (1_000, 2_000, 5_000, 10_000, 20_000, 25_000, 50_000, 100_000):
            k = np.arange(0, n + 1)
            full = v11.gate_pass(k, n, tier)
            pt = v11.gate_pass(k, n, tier, use_wilson=False, use_ceiling=False)
            no_w = v11.gate_pass(k, n, tier, use_wilson=False, use_ceiling=True)
            no_c = v11.gate_pass(k, n, tier, use_wilson=True, use_ceiling=False)
            rows.append(dict(tier=tier, n=n, k_values_checked=n + 1,
                             decisions_changed_by_wilson_clause=int((no_c != pt).sum()),
                             decisions_changed_by_ceiling=int((no_w != pt).sum()),
                             decisions_changed_by_both=int((full != pt).sum()),
                             clauses_redundant=bool((full == pt).all())))
    return pd.DataFrame(rows)


def c3_cost_hint(cells):
    """Rough data-generation-only wall hours for the C3 intermediate training (T statistic cost not included)."""
    t = pd.read_csv(BENCH)
    g = lambda nd: 1000 * float(t[(t.task == "generate data (fast generator)") & (t.n_days == nd)].median_s.iloc[0])
    inter = lambda nd: g(59) + (g(250) - g(59)) * (nd - 59) / 191
    ms = cells.n_days.map(inter) * cells.n_sims
    return float(ms.sum() / 1000 / SPEEDUP / 3600)


def main():
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files.")
    OUT.mkdir(parents=True, exist_ok=True)
    v1_spec = json.loads((V1 / "spec_v1.json").read_text())
    cells = c3_training_cells()
    red = redundancy_table()
    cells.to_csv(OUT / "cells_c3_training_intermediate.csv", index=False)
    red.to_csv(OUT / "gate_redundancy_check.csv", index=False)
    (OUT / "alt_dgp_parameters.json").write_text(json.dumps(v11.ALT_DGP_PARAMETERS, indent=2))

    spec = {
        "version": "v1.1", "supersedes_in_part": "v1 (all v1 files remain byte-identical and unchanged; see v1_manifest_sha256)",
        "status": "PROPOSED for review; NOT approved for any experiment. Stage 1 has not started.",
        "v1_manifest_sha256": sha(V1 / "FROZEN_v1.sha256"),
        "unchanged_from_v1": ["estimand", "statistic", "alpha", "C1 definition", "C3 definition at 59, 125, 250 days", "grids (cells_stage1/development/validation.csv)",
                              "gate bounds and tiers", "seeds of v1", "failure conditions", "fair-comparison rules", "environment"],
        "A1_C2": {
            "name": v11.C2_LABEL,
            "status": "UNVERIFIED. Derived from Beran's double-bootstrap logic and a search-tool recollection; the original paper has NOT been read. "
                      "It must not be attributed to Davidson and MacKinnon or to any paper until verified.",
            "definition": ("outer B=999 day-resamples give T*_b; one inner day-resample of each outer sample gives T**_b; p1 = mean(T* >= T); "
                           "Q = (1 - p1) quantile of {T**_b}; p_fdb = mean(T*_b > Q); reject iff p_fdb <= alpha"),
            "v1_defect": "v1 computed mean(T** > Q), which equals p1 up to rounding (300 of 300 datasets, max difference 0.0000). v1 code and text are left unchanged.",
            "code": "src/quantlab/research/h1_calibration_v11.py::fdb_like_test",
            "use_rules": "see A6"},
        "A2_ambiguity": {
            "per_cell": {
                "inputs": "k rejections in n valid simulations; p_hat = k/n; Wilson 95% interval [L, U] (z = 1.959964)",
                "point_pass": "v1 rule: lo <= p_hat <= hi, and (tier A/B) U <= Wilson limit, and p_hat <= 0.07; for C3 only p_hat <= hi",
                "ambiguous": "a point-rule bound that applies (lo and hi; hi only for C3) satisfies L <= bound <= U",
                "status": "PASS | PASS_AMBIGUOUS | FAIL | FAIL_AMBIGUOUS = point_pass x ambiguous"},
            "per_candidate": {
                "FAIL": "at least one gated cell is FAIL",
                "FAIL_BOUNDARY_ONLY": "no FAIL, at least one FAIL_AMBIGUOUS; decision stays 'not selected'",
                "MARGINAL_NOT_DEMONSTRATED": "every gated cell point-passes, at least one is PASS_AMBIGUOUS; no claim of calibration is made",
                "PASS_CLEAR": "every gated cell is PASS"},
            "replication_rule": {
                "who_decides": "only with the user's explicit approval; never automatic",
                "what": "the ambiguous cells only, 100,000 simulations, fresh seed (name ambiguity_replication, 20261210), same data process and method",
                "decision": "the point rule on the replication estimate ALONE (original estimate discarded, no pooling, to avoid optional stopping)",
                "after": "still ambiguous at n=100,000 -> final status MARGINAL_NOT_DEMONSTRATED; no further replication"},
            "code": "src/quantlab/research/h1_calibration_v11.py::classify_cell, classify_candidate"},
        "A3_redundant_clauses": {
            "statement": ("At 25,000 simulations per gated cell the Wilson-upper clause and the 7.0% ceiling never change a decision. Checked exhaustively at n = 10,000, 20,000, 25,000, 50,000 and 100,000 (all redundant). "
                      "At n = 1,000, 2,000 and 5,000 the Wilson clause DOES change 8-12 decisions per tier; a 500-step scan finds it first redundant at n = 8,500 (tier A) and 9,500 (tier B). "
                      "The 7.0% ceiling changed no decision at any n tested. Redundancy is not claimed for untested n."),
            "evidence": "gate_redundancy_check.csv: exhaustive over every k = 0..n, decisions with and without the clauses are identical",
            "why": "tier A: p_hat <= 0.055 implies Wilson U <= 0.058 < 0.060; tier B: p_hat <= 0.060 implies U <= 0.063 < 0.065; both p_hat bounds are below 0.07",
            "consequence": "the clauses stay in the spec text (harmless) but give no extra protection when a cell has at least 10,000 valid simulations; removing them would not change any decision at n = 25,000",
            "caveat": "the Wilson clause binds when a cell has fewer than about 10,000 valid simulations (e.g. after numerical failures in a reduced cell or in tier C-sized cells)"},
        "A4_alternative_processes": {
            "file": "alt_dgp_parameters.json",
            "common": "3 stocks, shape E, 59 days, NSE and US, 25,000 simulations, H0 true by construction, day factor f ~ N(0, 0.3^2) unless stated, unit-variance shocks",
            "null_check": "analytic E[(shock part)^2] = 1 within 1e-9 (tests) for a, b, e, f; unit-variance multipliers for c, d; THEN a Monte-Carlo period-mean check within 0.5% at 10^6 bars before use (Stage 4)",
            "DEVIATION_e": ("process e: v1 / docs/15 wording (log day scale Student-t(3)) has infinite E[exp(2f)] (a t variable has no moment-generating function), "
                            "so the expected squared return and the estimand do not exist. v1.1 uses a Gaussian scale mixture (5% of days with 3x the sd), overall sd 0.3. "
                            "THIS IS A CHANGE OF CONTENT, NOT ONLY A NORMALISATION: PENDING YOUR APPROVAL."),
            "cells_alternative_dgps.csv": "unchanged in v1; its text for process e is superseded by this file"},
        "A5_C3_intermediate_sizes": {**v11.C3_TRAINING_INTERMEDIATE, "cells_file": "cells_c3_training_intermediate.csv", "n_cells": len(cells),
                                     "n_simulations": int(cells.n_sims.sum()), "est_generation_only_wall_hours": c3_cost_hint(cells),
                                     "cost_note": "generation of the data only (benchmark / 4x speed-up); computing T adds a small amount; it is NOT part of the earlier resource table"},
        "A6_C2_use_restrictions": [
            "C2 results (including this corrected FDB-like procedure) are NOT used for any methodological conclusion",
            "C2 is NOT used in candidate selection or ranking, and is not described as validated, calibrated or as the Davidson-Mackinnon method",
            "C2 may be run and its gate outcomes reported, labelled 'FDB-like procedure, formula UNVERIFIED'",
            "these restrictions lapse only after the user records that the formula has been verified against the original paper",
            "a corrected C2 may be selected only on the user's explicit written approval of a 'procedure-defined, simulation-evidence-only' status"],
        "new_seeds": {"c3_training_intermediate": 20261209, "ambiguity_replication": 20261210,
                      "note": "20261209 and 20261210 are not used by any v1 seed; v1 seeds 20261201..20261208 unchanged"},
        "tests_note": "tests/test_research_h1_calibration_v11.py check code behaviour only; they are not evidence of statistical validity of any procedure",
        "unresolved_decisions": ["approve or reject the process e replacement (A4)", "approve the 12-cell C3 families at 90/180 days (A5)",
                                 "approve the wording of the ambiguity-replication rule (A2)",
                                 "how to treat C2 if the paper stays unavailable (A6 default: report only, never select)"],
    }
    (OUT / "spec_v1_1.json").write_text(json.dumps(spec, indent=2))

    files = sorted(OUT.glob("*")) + [ROOT / p for p in [
        "src/quantlab/research/h1_calibration_v11.py", "scripts/milestone4/stage0_freeze_spec_v11.py",
        "tests/test_research_h1_calibration_v11.py"]]
    lines = [f"{sha(p)}  {p.relative_to(ROOT)}" for p in files]
    (OUT / "FROZEN_v1_1.sha256").write_text("\n".join(lines) + "\n")
    print(red[red.n.isin([1000, 5000, 25000])].to_string())
    print(f"{len(lines)} files hashed; C3 intermediate generation-only hours: {spec['A5_C3_intermediate_sizes']['est_generation_only_wall_hours']:.2f}")


if __name__ == "__main__":
    main()
