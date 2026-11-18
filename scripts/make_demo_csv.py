"""Write examples/synthetic_demo.csv: SYNTHETIC 5-minute bars of three made-up US stocks (64 sessions, open and close volatility boosted), in the input format of
`python -m quantlab.h1tool`. No real market data. Fixed seeds, so the file is reproducible."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from quantlab.calendars import US                       # noqa: E402
from quantlab.research import nulls                     # noqa: E402

frames = []
for i, sym in enumerate(["DEMOA", "DEMOB", "DEMOC"]):
    raw = nulls.simulate_raw(US, 64, np.random.default_rng(20261501 + i), vol_edge_boost=2.0)
    frames.append(pd.DataFrame({"symbol": sym, "timestamp": [t.isoformat() for t in raw.index], **{c: raw[c].round(4).to_numpy() for c in ("open", "high", "low", "close", "volume")}}))
out = ROOT / "examples" / "synthetic_demo.csv"
out.parent.mkdir(exist_ok=True)
pd.concat(frames).to_csv(out, index=False)
print("wrote", out, out.stat().st_size, "bytes")
