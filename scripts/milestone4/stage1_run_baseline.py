"""H1 calibration, STAGE 1 (approved): mechanism diagnosis with the M4b BASELINE method ONLY (bootstrap-t, 'rom', max rule, iid days).
ALL DATA SIMULATED, NULL ONLY.  No C1, C2 or C3.  Grid = the frozen cells_stage1.csv (68 cells, 1,240,000 simulations).

Safety checks before anything runs: the 23 v1 hashes and the 7 v1.1 hashes must verify; the output folder must be empty.
Seeds: master seed from spec_v1.json (stage1 = 20261201); simulation i of cell row r uses SeedSequence(master, spawn_key=(r, i)),
full width, one generator per simulation (data first, then the bootstrap draws).
Output: outputs/milestone4/h1_calibration/stage1/   (one parquet per cell, run_metadata.csv, STAGE1_CODE.sha256)
Usage : python scripts/milestone4/stage1_run_baseline.py            (the real run)
        python scripts/milestone4/stage1_run_baseline.py --smoke    (20 simulations per cell into the scratch folder given by --out; NOT results)
"""
import argparse
import hashlib
import json
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))

from quantlab.calendars import NSE, US                                   # noqa: E402
from quantlab.research import direct_sim as ds, h1_stage1 as s1          # noqa: E402
import run_h1_inference as ri                                            # noqa: E402

SPEC_DIR = ROOT / "outputs" / "milestone4" / "h1_calibration" / "frozen_spec"
SPEC11_DIR = ROOT / "outputs" / "milestone4" / "h1_calibration" / "frozen_spec_v1_1"
OUT = ROOT / "outputs" / "milestone4" / "h1_calibration" / "stage1"
MARKETS = {"NSE": NSE, "US": US}
CHUNK = {999: 500, 9999: 50}                                              # simulations per worker task (larger bootstrap = smaller task)
_CELLS = None


def verify_manifest(path: Path) -> int:
    """Check every 'sha256  relative_path' line of a manifest against the files; stop the program on any mismatch."""
    n = 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != digest:
            sys.exit(f"HASH MISMATCH in {path.name}: {rel}")
        n += 1
    return n


def load_cells() -> pd.DataFrame:
    """Read the frozen Stage 1 cell file (never modified)."""
    return pd.read_csv(SPEC_DIR / "cells_stage1.csv", keep_default_na=False)


def cell_setup(row: pd.Series) -> dict:
    """Everything a worker needs for one cell: market, used-slot index, profile, df, merge, B, n_days."""
    mk = row["market"]
    return dict(market=MARKETS[mk], idx=ds.used_slot_index(MARKETS[mk]), profile=ri.profile_for(mk, row["shape"], 1.0),
                df=s1.DF_CODE[row["tail"]], merge=int(row["merge"]), B=int(row["B"]), n_days=int(row["n_days"]))


def _init(master):
    """Worker start-up: load the cells once."""
    global _CELLS, _MASTER
    _CELLS, _MASTER = load_cells(), master


def work(job):
    """One task = simulations [start, stop) of one cell; returns a list of per-simulation result rows."""
    row_i, start, stop = job
    c = cell_setup(_CELLS.iloc[row_i])
    rows = []
    for i in range(start, stop):
        rng = np.random.default_rng(s1.sim_seed(_MASTER, row_i, i))
        r = s1.simulate_returns(c["market"], 3, c["n_days"], rng, profile=c["profile"], df=c["df"], day_vol_sd=0.3)
        res = s1.baseline_on_returns(r, c["idx"], c["profile"], c["merge"], rng, c["B"])
        rows.append({"cell_row": row_i, "sim": i, **res})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = Path(a.out) if a.out else OUT
    if a.smoke and (a.out is None or Path(a.out).resolve() == OUT.resolve()):
        sys.exit("--smoke needs --out pointing to a scratch folder")
    n_v1 = verify_manifest(SPEC_DIR / "FROZEN_v1.sha256")
    n_v11 = verify_manifest(SPEC11_DIR / "FROZEN_v1_1.sha256")
    if (n_v1, n_v11) != (23, 7):
        sys.exit(f"unexpected manifest sizes {n_v1}, {n_v11}")
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} already has files.")
    out.mkdir(parents=True, exist_ok=True)
    cells = load_cells()
    master = int(json.loads((SPEC_DIR / "spec_v1.json").read_text())["seeds"]["stage1"])
    assert len(cells) == 68 and int(cells.n_sims.sum()) == 1_240_000, "cell file is not the frozen Stage 1 grid"
    if not a.smoke:
        code = [ROOT / p for p in ["scripts/milestone4/stage1_run_baseline.py", "src/quantlab/research/h1_stage1.py", "tests/test_research_h1_stage1.py",
                                   "src/quantlab/research/h1_rms2.py", "src/quantlab/research/direct_sim.py", "src/quantlab/research/dependence.py",
                                   "scripts/milestone4/run_h1_inference.py", "scripts/milestone4/run_h1_next.py"]]
        (out / "STAGE1_CODE.sha256").write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT)}\n" for p in code))
    t0, total, failures = time.time(), 0, 0
    with ProcessPoolExecutor(initializer=_init, initargs=(master,)) as pool:
        for row_i, row in cells.iterrows():
            n = 20 if a.smoke else int(row["n_sims"])
            step = CHUNK[int(row["B"])] if not a.smoke else 20
            jobs = [(row_i, s, min(s + step, n)) for s in range(0, n, step)]
            rows = [r for part in pool.map(work, jobs) for r in part]
            df = pd.DataFrame(rows).sort_values("sim")
            assert len(df) == n and df["sim"].tolist() == list(range(n)), f"cell {row_i}: wrong number of simulations"
            df.to_parquet(out / f"cell_{row_i:02d}.parquet", index=False)
            total += n
            failures += int((~df["valid"]).sum())
            print(f"cell {row_i:02d}/67 {row['experiment'][:2]} {row['tail']:>3} {row['shape']:>4} {row['market']:>3} merge={row['merge']} B={row['B']:>5} "
                  f"n={n} rej={df.loc[df.valid, 'reject'].mean():.4f} failed={int((~df.valid).sum())}  total={total} elapsed={time.time() - t0:.0f}s", flush=True)
    pd.Series({"master_seed": master, "seed_rule": "SeedSequence(master, spawn_key=(cell_row, sim_index)); one default_rng per simulation",
               "cells": len(cells), "simulations": total, "failed_simulations": failures, "smoke": a.smoke, "seconds": round(time.time() - t0, 1),
               "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "machine": platform.platform(),
               "v1_hashes_verified": n_v1, "v1_1_hashes_verified": n_v11, "method": "M4b baseline only (rom bootstrap-t, max rule, iid days)",
               "note": "ALL DATA SIMULATED, NULL ONLY"}).to_csv(out / "run_metadata.csv", header=["value"])
    print("COMPLETE", total, "simulations,", failures, "failed", flush=True)


if __name__ == "__main__":
    main()
