"""H1 calibration, STAGE 2: pieces shared by the Stage 2 scripts that need the M4b script helpers (profiles, dependence settings).
Reads : outputs/milestone4/h1_calibration/stage2_plan/stage2_cells_plan.csv and the frozen manifests.   Writes nothing.
Provides: manifest verification, cell set-up, the dataset generator and the one-simulation function that applies the baseline, C1 and C3
to the SAME dataset with independent random streams.  NO C2 (decision D9).   ALL DATA SIMULATED, NULL (or planted-effect power cells) ONLY.
"""
import hashlib
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))

from quantlab.calendars import NSE, US                                    # noqa: E402
from quantlab.research import direct_sim as ds, h1_calibration as hc, h1_stage1 as s1   # noqa: E402
from quantlab.research.h1_rms2 import bootstrap_t                         # noqa: E402
import run_h1_inference as ri                                             # noqa: E402
import run_h1_next as nx                                                  # noqa: E402

BASE = ROOT / "outputs" / "milestone4" / "h1_calibration"
PLAN = BASE / "stage2_plan" / "stage2_cells_plan.csv"
MANIFESTS = {"v1": (BASE / "frozen_spec" / "FROZEN_v1.sha256", 23), "v1.1": (BASE / "frozen_spec_v1_1" / "FROZEN_v1_1.sha256", 7),
             "stage1_code": (BASE / "stage1" / "STAGE1_CODE.sha256", 8)}
STAGE2_INPUTS = BASE / "frozen_stage2_inputs.sha256"
MARKETS = {"NSE": NSE, "US": US}
MIN_FREE_GIB = 2.0


def sha256(path: Path) -> str:
    """SHA-256 hex digest of a file."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_manifest(path: Path, expected: int | None = None) -> int:
    """Check every 'sha256  relative_path' line against the files; stop the program on any mismatch or unexpected count."""
    n = 0
    for line in Path(path).read_text().splitlines():
        if line.strip():
            digest, rel = line.split("  ", 1)
            if sha256(ROOT / rel) != digest:
                sys.exit(f"HASH MISMATCH in {Path(path).name}: {rel}")
            n += 1
    if expected is not None and n != expected:
        sys.exit(f"{Path(path).name}: expected {expected} entries, found {n}")
    return n


def verify_all(require_stage2_inputs: bool = True) -> dict:
    """E0 check used by every runner: frozen v1, v1.1, Stage 1 code and (normally) the Stage 2 input manifest; also the free disk space."""
    out = {name: verify_manifest(p, n) for name, (p, n) in MANIFESTS.items()}
    if require_stage2_inputs:
        out["stage2_inputs"] = verify_manifest(STAGE2_INPUTS)
    free = shutil.disk_usage(ROOT).free / 2 ** 30
    if free < MIN_FREE_GIB:
        sys.exit(f"only {free:.1f} GiB free; need at least {MIN_FREE_GIB} GiB")
    out["free_gib"] = round(free, 2)
    return out


def load_plan() -> pd.DataFrame:
    """The 76 development cells with their roles, seed rows and tiers (never modified)."""
    return pd.read_csv(PLAN, keep_default_na=False)


def cell_setup(cell: dict, mult: float = 1.0) -> dict:
    """Everything needed to simulate one cell: market, used-slot index, profile, df, day-volatility, dependence parameters."""
    mk = cell["market"]
    dep = nx.EMP_DEP[mk] if cell["dependence"] == "estimated" else dict(share=0.0, phi=0.0, ret_corr=0.0)
    return dict(market=MARKETS[mk], idx=ds.used_slot_index(MARKETS[mk]), profile=ri.profile_for(mk, cell["shape"], mult),
                df=s1.DF_CODE[cell["tail"]], day_vol_sd=float(cell["day_vol_sd"]), n_days=int(cell["n_days"]),
                share=dep["share"], phi=dep["phi"], ret_corr=dep["ret_corr"])


def generate(setup: dict, rng: np.random.Generator) -> np.ndarray:
    """One dataset of squared returns (stocks, days, slots) from the validated M4b generator."""
    return ds.simulate_returns_sq(setup["market"], 3, setup["n_days"], rng, profile=setup["profile"], df=setup["df"],
                                  day_vol_sd=setup["day_vol_sd"], share=setup["share"], phi=setup["phi"], ret_corr=setup["ret_corr"])


def statistic_only(setup: dict, rng: np.random.Generator) -> float:
    """C3 training: generate one dataset and return T = max |t| (NaN if it cannot be computed)."""
    try:
        return float(hc.max_abs_t(ds.period_matrix(generate(setup, rng), setup["idx"])))
    except Exception:
        return float("nan")


def simulate_all(setup: dict, seed_fn, c3_crit: float, B: int = 999, R: int = 499) -> dict:
    """One dataset; the baseline, C1 and C3 applied to it with independent streams. seed_fn(stream_name) -> SeedSequence. A failing method is
    marked invalid (never dropped) and cannot affect the others."""
    r2 = generate(setup, np.random.default_rng(seed_fn("data")))
    M = ds.period_matrix(r2, setup["idx"])
    r2_used, groups = hc.to_used(r2, setup["idx"])
    out = {}
    try:
        out["T"] = float(hc.max_abs_t(M))
    except Exception:
        out["T"] = float("nan")
    # baseline (M4b bootstrap-t, rom, max rule)
    try:
        res = bootstrap_t(M, np.random.default_rng(seed_fn("baseline")), "rom", B=B)
        ok = bool(np.isfinite(res["t"]).all() and np.isfinite(res["crit_max"]))
        out.update(valid_base=ok, reject_base=bool(res["reject_max"]) if ok else False, crit_base=float(res["crit_max"]))
    except Exception:
        out.update(valid_base=False, reject_base=False, crit_base=float("nan"))
    # C1 (frozen v1 implementation, unchanged)
    try:
        r = hc.c1_test(r2_used, groups, np.random.default_rng(seed_fn("c1")), R=R)
        ok = bool(np.isfinite([r["T"], r["crit"], r["p_mc"]]).all())
        out.update(valid_c1=ok, reject_c1=bool(r["reject"]) if ok else False, crit_c1=float(r["crit"]), p_c1=float(r["p_mc"]), T_c1=float(r["T"]))
    except Exception:
        out.update(valid_c1=False, reject_c1=False, crit_c1=float("nan"), p_c1=float("nan"), T_c1=float("nan"))
    # C3 (fixed critical value from the frozen training table)
    ok = bool(np.isfinite(out["T"]) and np.isfinite(c3_crit))
    out.update(valid_c3=ok, reject_c3=bool(out["T"] > c3_crit) if ok else False, crit_c3=float(c3_crit))
    # conditioning variables (data only): kurtosis and leverage
    try:
        out.update(s1.tail_diagnostics([r2_used[:, :, g] for g in groups], M))
    except Exception:
        out.update(kurt=float("nan"), maxshare=float("nan"), maxshare_open=float("nan"), maxshare_middle=float("nan"), maxshare_close=float("nan"))
    return out
