"""H1 calibration, STAGE 0 addendum: implementation-defect check for C2 (fast double bootstrap). Compares the p-value AS IMPLEMENTED in
h1_calibration.fast_double_bootstrap (T** compared with the (1-p1) quantile of T**) with the variant derived from Beran's double-bootstrap
logic (T* compared with that quantile). 300 simulated Gaussian-gamma datasets; ONLY the relation between p-values is reported, no
rejection rate, so this is NOT a calibration experiment. Does not modify any frozen file.
Output: outputs/milestone4/h1_calibration/stage0/c2_defect_check/"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from quantlab.research import h1_calibration as hc                      # noqa: E402
from quantlab.research.inference import resample_days                    # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "h1_calibration" / "stage0" / "c2_defect_check"


def both(M, rng, B=999):
    n = len(M)
    th, _ = hc._parts(M)
    T = float(hc.max_abs_t(M))
    Xb = M[resample_days(n, B, rng)]
    thb, seb = hc._parts(Xb)
    Ts = np.abs((thb - th) / seb).max(-1)
    X2 = np.take_along_axis(Xb, rng.integers(0, n, (B, n))[:, :, None], axis=1)
    th2, se2 = hc._parts(X2)
    T2 = np.abs((th2 - thb) / se2).max(-1)
    p1 = float(np.mean(Ts >= T)); q = float(np.quantile(T2, 1 - p1))
    return p1, float(np.mean(T2 > q)), float(np.mean(Ts > q))


if __name__ == "__main__":
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit("exists")
    OUT.mkdir(parents=True, exist_ok=True)
    kids = hc.child_seeds(20261103, 600)
    rows = []
    for i in range(300):
        M = np.random.default_rng(kids[i]).gamma(2.0, 1.0, (59, 3))
        p1, p_impl, p_alt = both(M, np.random.default_rng(kids[300 + i]))
        rows.append(dict(p_first=p1, p_as_implemented=p_impl, p_variant_Tstar_vs_Q2=p_alt))
    d = pd.DataFrame(rows); d.to_csv(OUT / "p_values.csv", index=False)
    s = pd.Series({"datasets": len(d), "mean_abs_diff_implemented_vs_first": (d.p_as_implemented - d.p_first).abs().mean(),
                   "max_abs_diff_implemented_vs_first": (d.p_as_implemented - d.p_first).abs().max(),
                   "mean_abs_diff_variant_vs_first": (d.p_variant_Tstar_vs_Q2 - d.p_first).abs().mean(),
                   "max_abs_diff_variant_vs_first": (d.p_variant_Tstar_vs_Q2 - d.p_first).abs().max()})
    s.to_csv(OUT / "summary.csv", header=["value"]); print(s.round(4).to_string())
