"""M4a DIAGNOSTICS for the H2 calibration failure.   ALL DATA SIMULATED.

Why the original model rejects when it should not
-------------------------------------------------
Suppose volume and volatility both rise on "active" days (a shared day-level factor) and
the simulated truth contains NO effect of a volume spike on later volatility BEYOND that
shared level. The model tries to remove the shared level with controls (recent and
day-so-far volatility), but these measure the hidden level with error, so some of it
leaks into the event dummy, which is correlated with the same hidden level.

WHAT COUNTS AS A "NULL" HERE (this corrects an earlier mislabelling)
  H2 asks whether volume carries INFORMATION about later volatility or returns beyond what past
  prices already show. So a true null is a world where volume is unrelated to future volatility
  given past data. If volume merely shares a hidden volatility regime with returns, volume IS
  informative about the future (it proxies the regime), so rejecting there is a correct detection,
  not a false positive. What it cannot do is prove that volume has an incremental effect BEYOND the
  regime itself, and the regime is unobservable. We therefore label every scenario:
    TRUE NULL       volume independent of returns (returns may have any volatility regime)
    SHARED REGIME   volume loads on a hidden volatility regime (information via a proxy)

Models compared (outcomes: forward volatility y_fv_open; continuation g_open):
  M0   stock x slot effects, controls c1 c2                                (original)
  M1   + c3 (volatility so far today)
  M5   + c3 + c4 (previous day's volatility vs recent norm)                 [primary candidate]
  S1   c1 c2 c3_12 | S2 c1 c2 c3_24 | S3 c1 c2 c4          control definitions
  DFE  stock x slot AND stock x day effects, c1 c2 c3   (compares an event only with other candles
       of the SAME day: a different, "within-day" question, and it removes real day-level information)
p-values: day-clustered t (CR1). The proposed model M3 also gets the wild-cluster-bootstrap p.
Outputs (new folder): outputs/milestone4/diagnostics/h2/
Usage: python scripts/milestone4/run_diagnostics_h2.py [--quick]
"""
import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from quantlab.calendars import NSE, US                       # noqa: E402
from quantlab.research import h2_volume as h2                # noqa: E402
from quantlab.research.nulls import simulate_table           # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "diagnostics" / "h2"
MASTER_SEED = 20261032
MARKETS = {"NSE": NSE, "US": US}
N_DAYS, N_STOCKS, ALPHA = 59, 3, 0.05

DGPS = {   # name: (truth label, simulator kwargs)
    "A day factor in returns, volume independent": ("TRUE NULL", dict(day_vol_sd=0.3)),
    "F day factor + intraday regime in returns, volume independent": (
        "TRUE NULL", dict(day_vol_sd=0.3, intraday_regime_sd=0.25)),
    "B volume loads on day factor (0.8)": ("SHARED REGIME", dict(day_vol_sd=0.3, volume_day_loading=0.8)),
    "C volume loads on day factor + intraday regime (0.8)": (
        "SHARED REGIME", dict(day_vol_sd=0.3, volume_day_loading=0.8, intraday_regime_sd=0.25,
                              volume_intraday_loading=0.8)),
    "D volume loads on intraday regime only (1.0)": (
        "SHARED REGIME", dict(day_vol_sd=0.0, intraday_regime_sd=0.3, volume_intraday_loading=1.0)),
    "E stress: day factor sd 0.5, loading 1.5": ("SHARED REGIME", dict(day_vol_sd=0.5, volume_day_loading=1.5)),
}
MODELS = {   # name: (day_fe, controls)
    "M0 original (c1 c2)": (False, ("c1", "c2")),
    "M1 + c3": (False, ("c1", "c2", "c3")),
    "M5 + c3 + c4 [primary candidate]": (False, ("c1", "c2", "c3", "c4")),
    "S1 c3_12 instead of c3": (False, ("c1", "c2", "c3_12")),
    "S2 c3_24 instead of c3": (False, ("c1", "c2", "c3_24")),
    "S3 c4 only (prior day)": (False, ("c1", "c2", "c4")),
    "DFE day effects + c3 (within-day question)": (True, ("c1", "c2", "c3")),
}
WILD = ("M5 + c3 + c4 [primary candidate]", "DFE day effects + c3 (within-day question)")
RET_MODELS = ("M0 original (c1 c2)", "M5 + c3 + c4 [primary candidate]", "DFE day effects + c3 (within-day question)")


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def one(args):
    seed, market, kw, wild_B = args
    rng = np.random.default_rng(seed)
    tabs = [simulate_table(MARKETS[market], f"S{i}", N_DAYS, rng, nse_feed_quirks=(market == "NSE"), **kw)
            for i in range(N_STOCKS)]
    feat = pd.concat([h2.outcome_features(t) for t in tabs])
    out = {}
    for mname, (fe, controls) in MODELS.items():
        for oname, col in [("vol", "y_fv_open"), ("ret", "g_open")]:
            if oname == "ret" and mname not in RET_MODELS:
                continue
            r = h2.event_regression(feat, col, wild_B if mname in WILD else 0, rng, day_fe=fe, controls=controls)
            out[f"{mname}|{oname}|p"] = r["p_cr1"]
            out[f"{mname}|{oname}|beta"] = r["beta"]
            if mname in WILD and wild_B:
                out[f"{mname}|{oname}|p_wild"] = r["p_wild"]
            if mname.startswith("M5") and oname == "vol":
                out["n_events"], out["n_event_days"] = r["n_events"], r["n_event_days"]
    return out


def one_power(args):
    seed, market, kw = args
    rng = np.random.default_rng(seed)
    tabs = [simulate_table(MARKETS[market], f"S{i}", N_DAYS, rng, nse_feed_quirks=(market == "NSE"), **kw)
            for i in range(N_STOCKS)]
    feat = pd.concat([h2.outcome_features(t) for t in tabs])
    out = {}
    for tag, fe, ctrl in [("M5", False, ("c1", "c2", "c3", "c4")), ("DFE", True, ("c1", "c2", "c3"))]:
        v = h2.event_regression(feat, "y_fv_open", 0, rng, day_fe=fe, controls=ctrl)
        r = h2.event_regression(feat, "g_open", 0, rng, day_fe=fe, controls=ctrl)
        out.update({f"{tag}_p_vol": v["p_cr1"], f"{tag}_beta_vol": v["beta"],
                    f"{tag}_p_ret": r["p_cr1"], f"{tag}_beta_ret_bps": r["beta"] * 1e4})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    n_us, n_nse, n_pow, wild = (6, 4, 4, 29) if a.quick else (240, 120, 100, 199)
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files; move them yourself first.")
    OUT.mkdir(parents=True, exist_ok=True)
    seeds = iter(np.random.SeedSequence(MASTER_SEED).spawn(100000))
    nxt = lambda: int(next(seeds).generate_state(1)[0])
    size_rows, pow_rows = [], []
    with ProcessPoolExecutor() as pool:
        for mk, n in [("US", n_us), ("NSE", n_nse)]:
            for dname, (truth, kw) in DGPS.items():
                res = pd.DataFrame(list(pool.map(one, [(nxt(), mk, kw, wild) for _ in range(n)], chunksize=2)))
                for col in [c for c in res.columns if c.endswith("|p") or c.endswith("|p_wild")]:
                    mname, oname, ptype = col.split("|")
                    pv = res[col].dropna()
                    k = int((pv < ALPHA).sum())
                    lo, hi = wilson(k, len(pv))
                    bcol = f"{mname}|{oname}|beta"
                    size_rows.append({"dgp": dname, "truth": truth, "market": mk, "model": mname, "outcome": oname,
                                      "p_type": ptype, "n_sims": len(pv), "rejection_rate": k / len(pv),
                                      "ci95_low": lo, "ci95_high": hi, "mean_beta": res[bcol].mean(),
                                      "median_events": res["n_events"].median()})
                print(mk, dname, "done", flush=True)
            for dname in ["F day factor + intraday regime in returns, volume independent",
                          "C volume loads on day factor + intraday regime (0.8)"]:
                base = DGPS[dname][1]
                for kind, setting in ([("fwd_vol_mult", f) for f in (1.10, 1.25, 1.50)]
                                      + [("continuation", c) for c in (0.05, 0.10, 0.20)]):
                    d = pd.DataFrame(list(pool.map(one_power, [(nxt(), mk, {**base, kind: setting}) for _ in range(n_pow)])))
                    for tag in ("M5", "DFE"):
                        col = f"{tag}_p_vol" if kind == "fwd_vol_mult" else f"{tag}_p_ret"
                        k = int((d[col] < ALPHA).sum()); lo, hi = wilson(k, len(d))
                        pow_rows.append({"dgp": dname, "market": mk, "model": tag,
                                         "test": "forward volatility" if kind == "fwd_vol_mult" else "return continuation",
                                         "true_effect": f"{kind}={setting}", "n_sims": len(d),
                                         "rejection_rate": k / len(d), "ci95_low": lo, "ci95_high": hi,
                                         "mean_beta": d[f"{tag}_beta_vol" if kind == "fwd_vol_mult" else f"{tag}_beta_ret_bps"].mean()})
                print(mk, "power", dname, "done", flush=True)
    size = pd.DataFrame(size_rows)
    size.to_csv(OUT / "size_by_model_and_dgp.csv", index=False)
    pd.DataFrame(pow_rows).to_csv(OUT / "power_proposed_model.csv", index=False)
    pd.Series({"master_seed": MASTER_SEED, "quick": a.quick, "n_sims_US": n_us, "n_sims_NSE": n_nse,
               "n_sims_power": n_pow, "wild_B": wild, "note": "ALL DATA SIMULATED"}).to_csv(
        OUT / "run_metadata.csv", header=["value"])
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 500)
    v = size[(size.outcome == "vol") & (size.p_type == "p")]
    print(v.pivot_table(index="model", columns=["market", "truth", "dgp"], values="rejection_rate").round(3).T.to_string())


if __name__ == "__main__":
    main()
