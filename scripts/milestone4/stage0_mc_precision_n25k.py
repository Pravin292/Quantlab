"""H1 calibration, STAGE 0: gate pass probabilities at the proposed n = 25,000 per gated cell (arithmetic only, no simulation)."""
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))
from stage0_mc_precision import pass_prob                                      # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "h1_calibration" / "stage0" / "mc_precision"
rows = []
for tier, (lo, hi, up, rates) in {"A [4.5,5.5], Wilson upper<=6.0": (0.045, 0.055, 0.060, (0.040, 0.045, 0.050, 0.052, 0.054, 0.055, 0.056, 0.058, 0.060, 0.065)),
                                  "B [4.0,6.0], Wilson upper<=6.5": (0.040, 0.060, 0.065, (0.035, 0.038, 0.040, 0.050, 0.058, 0.060, 0.062, 0.065, 0.070))}.items():
    for p in rates:
        rows.append({"tier": tier, "n": 25000, "true_rejection_rate": p, "P_gate_passes": pass_prob(p, 25000, lo, hi, up)})
d = pd.DataFrame(rows); d.to_csv(OUT / "gate_pass_probability_n25000.csv", index=False); print(d.round(4).to_string())
