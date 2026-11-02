"""M4a next round, Task C: DESCRIPTIVE quantities from the existing cleaned sample, used ONLY to
choose realistic simulation parameters. No hypothesis test is run; no between-period comparison is
reported (only the SHAPE inside a period, relative to that period's own average).

Outputs (new folder): outputs/milestone4/next_round/descriptive/
  slot_variance_profile.csv       per market and slot: mean r^2 relative to the stock's overall mean r^2
  within_period_shape.csv         per market and period: raw max/min of sqrt(slot variance) and the fitted smooth shape
  dependence_descriptives.csv     cross-stock correlation of standardised returns, cross-stock correlation of
                                  day log-volatility, lag-1 autocorrelation of day log-volatility, spread of day log-vol
CAUTION recorded in the files: with ~59 days and heavy tails, raw slot variances are noisy, so the raw max/min
ratio overstates the true heterogeneity; the fitted shape is the smoother summary used for the simulation.
"""
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from quantlab.calendars import market_for_symbol                    # noqa: E402
from quantlab.research.panel import load_tables                    # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "next_round" / "descriptive"
MAIN = ["open", "middle", "close"]


def fit_decay(v, from_start):
    """Fit v_j = a * (1 + b*exp(-j/tau)) to slot variances inside a period (j counted from the period edge
    that touches the open/close of the session). Returns (b, tau, rms_of_residual_in_logs)."""
    j = np.arange(len(v)) if from_start else np.arange(len(v))[::-1]
    y = np.log(v)

    def res(p):
        a, b, tau = p
        return a + np.log1p(np.exp(b) * np.exp(-j / np.exp(tau))) - y
    f = least_squares(res, x0=[y.mean(), 0.0, 1.0])
    a, lb, ltau = f.x
    return float(np.exp(lb)), float(np.exp(ltau)), float(np.sqrt(np.mean(f.fun ** 2)))


def main():
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files.")
    OUT.mkdir(parents=True, exist_ok=True)
    tabs = load_tables(ROOT / "data" / "clean")
    prof_rows, shape_rows, dep_rows = [], [], []
    for mk in ("NSE", "US"):
        syms = [s for s in tabs if market_for_symbol(s).name == mk]
        slot_var, day_lv, zs = {}, {}, {}
        for s in syms:
            t = tabs[s]
            ok = t[(t["status"] == "ok") & t["period"].isin(MAIN)].copy()
            ok["r2"] = ok["ret"] ** 2
            ok = ok[ok["r2"] > 0]
            overall = ok["r2"].mean()
            sv = ok.groupby("slot")["r2"].mean() / overall
            slot_var[s] = sv
            lv = 0.5 * np.log(ok.groupby("date")["r2"].mean())
            day_lv[s] = lv
            ok["z"] = ok["ret"] / np.sqrt(ok["slot"].map(sv) * overall)
            zs[s] = ok.set_index(["date", "slot"])["z"]
        first = slot_var[syms[0]]
        per = tabs[syms[0]].drop_duplicates("slot").set_index("slot")["period"]
        prof = pd.concat(slot_var, axis=1).mean(axis=1).reindex(first.index)
        for slot, v in prof.items():
            prof_rows.append({"market": mk, "slot": slot, "period": per.get(slot), "mean_r2_relative": v})
        for p in MAIN:
            sl = [s for s in prof.index if per.get(s) == p]
            v = prof.loc[sl].to_numpy()
            row = {"market": mk, "period": p, "n_slots_used": len(v),
                   "raw_max_over_min_of_sqrt_variance": float(np.sqrt(v.max() / v.min())),
                   "raw_note": "overstated by sampling noise (59 days, heavy tails)"}
            if p in ("open", "close"):
                b, tau, rr = fit_decay(v, from_start=(p == "open"))
                fitted = 1 + b * np.exp(-(np.arange(len(v)) if p == "open" else np.arange(len(v))[::-1]) / tau)
                row.update(fit_amplitude_b=b, fit_scale_tau_bars=tau, fit_log_resid_rms=rr,
                           fitted_max_over_min_of_sqrt_variance=float(np.sqrt(fitted.max() / fitted.min())))
            shape_rows.append(row)
        # dependence descriptives
        pairs = list(combinations(syms, 2))
        zc = [pd.concat([zs[a], zs[b]], axis=1, join="inner").corr().iloc[0, 1] for a, b in pairs]
        lvc = [pd.concat([day_lv[a], day_lv[b]], axis=1, join="inner").corr().iloc[0, 1] for a, b in pairs]
        ac1 = [day_lv[s].autocorr(1) for s in syms]
        ac2 = [day_lv[s].autocorr(2) for s in syms]
        sd = [day_lv[s].std() for s in syms]
        n_days = [len(day_lv[s]) for s in syms]
        dep_rows.append({"market": mk, "n_stocks": len(syms), "n_days": int(np.mean(n_days)),
                         "mean_pairwise_corr_standardised_returns": float(np.mean(zc)),
                         "mean_pairwise_corr_day_log_vol": float(np.mean(lvc)),
                         "min_max_pairwise_corr_day_log_vol": f"{min(lvc):.3f}..{max(lvc):.3f}",
                         "mean_lag1_autocorr_day_log_vol": float(np.mean(ac1)),
                         "mean_lag2_autocorr_day_log_vol": float(np.mean(ac2)),
                         "mean_sd_day_log_vol": float(np.mean(sd)),
                         "note": "approx. SE of an autocorrelation with ~59 days is ~0.13 per stock; sd includes "
                                 "estimation noise from a finite number of bars, so it overstates the true day-factor sd"})
    pd.DataFrame(prof_rows).to_csv(OUT / "slot_variance_profile.csv", index=False)
    pd.DataFrame(shape_rows).to_csv(OUT / "within_period_shape.csv", index=False)
    pd.DataFrame(dep_rows).to_csv(OUT / "dependence_descriptives.csv", index=False)
    pd.set_option("display.width", 220, "display.max_columns", 30)
    print(pd.DataFrame(shape_rows).round(3).to_string(index=False))
    print(pd.DataFrame(dep_rows).round(3).T.to_string())


if __name__ == "__main__":
    main()
