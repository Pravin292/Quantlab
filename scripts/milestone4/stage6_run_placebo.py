"""STAGE 6 part C (docs/42): real-data placebo of the frozen C3. For each real sample that was TESTED (docs/31, 35, 39) the same 59 sessions are used; in every session the used slots
are randomly permuted (same permutation for all stocks), so open, middle and close have the same expected variance while the real tails, day-to-day dependence and cross-stock dependence
stay. 10,000 permutations per sample; the share of placebo T above the frozen critical value estimates how often C3 raises a false alarm on that sample's own structure.
No new data is pulled or read: only the already-cleaned files. Master seed 20261403. Write-once output: outputs/milestone4/stage6/part_c/."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage6_common as sc6                                                # noqa: E402
import real_h1_run as r1                                                   # noqa: E402
import p2_us                                                               # noqa: E402
from quantlab.calendars import NSE, US                                      # noqa: E402
from quantlab.research import direct_sim as ds, h1_calibration as hc, real_h1 as rh, stage6 as s6   # noqa: E402
from quantlab.research.panel import load_tables                             # noqa: E402

ROOT = sc6.ROOT
# (name, folder, market, recorded results file, session list) in fixed order; the sample index is the seed spawn key.
SAMPLES = [("us_first_yahoo", "data/clean", US, "outputs/milestone4/real_h1/real_h1_results.csv", None),
           ("nse_first_yahoo", "data/clean", NSE, "outputs/milestone4/real_h1/real_h1_results.csv", None),
           ("nse_fresh_yahoo", "data/clean_p2", NSE, "outputs/milestone4/p2_nse/p2_nse_results.csv", None),
           ("us_fresh_alpaca", "data/clean_p2_us", US, "outputs/milestone4/p2_us/p2_us_results.csv", "scheduled")]


def build(folder, market, sessions):
    """(used-slot squared returns, groups, dates) exactly as the real tests built them."""
    tabs = load_tables(ROOT / folder)
    full, syms, dates = r1.real_array(tabs, market)
    if sessions == "scheduled":                                            # as p2_us.run: re-index on the frozen scheduled-session list
        pos = {str(d): i for i, d in enumerate(dates)}
        sched = p2_us.scheduled_sessions()
        arr = np.full((len(syms), len(sched), full.shape[2]), np.nan)
        for j, d in enumerate(sched):
            if d in pos:
                arr[:, j, :] = full[:, pos[d], :]
        full, dates = arr, sched
    r2, groups = hc.to_used(full, ds.used_slot_index(market))
    return r2, groups, dates


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--n", type=int, default=s6.N_PLACEBO)
    a = ap.parse_args()
    out = Path(a.out) if a.out else sc6.OUT / "part_c"
    if a.smoke and (a.out is None or out.resolve() == (sc6.OUT / "part_c").resolve()):
        sys.exit("--smoke needs --out (scratch)")
    n = a.n if a.smoke else s6.N_PLACEBO
    sc6.verify_all(smoke=a.smoke)
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} already has files: single-run rule.")
    crit = sc6.c3_crit(rh.N_SESSIONS)
    rows, meta = [], {"crit_n59": crit, "n_rep": n, "master_seed": s6.MASTER["placebo"]}
    for idx, (name, folder, market, recorded, sessions) in enumerate(SAMPLES):
        r2, groups, dates = build(folder, market, sessions)
        res = rh.analyse_market(r2, groups, dates, crit)
        if res["status"] != "TESTED":
            rows.append({"sample": name, "market": market.name, "status": res["status"], "usable_market_sessions": res["usable_market_sessions"], "note": "not testable under the frozen rule (docs/30 R1); no placebo computed"})
            print(name, res["status"], flush=True)
            continue
        rec = pd.read_csv(ROOT / recorded)
        rec = rec[(rec.market == market.name) & (rec.status == "TESTED")]
        assert len(rec) == 1 and abs(float(rec["T"].iloc[0]) - res["T"]) < 1e-9, f"{name}: rebuilt data does not reproduce the recorded T"
        sel = np.asarray(res["selected_positions"])
        T = s6.placebo_statistics(r2[:, sel, :], groups, s6.placebo_rng(idx), n)
        s = s6.placebo_summary(T, crit)
        rows.append({"sample": name, "market": market.name, "status": "PLACEBO_DONE", "usable_market_sessions": res["usable_market_sessions"], "real_T": res["T"], **s, "note": ""})
        print(f"{name}: real T={res['T']:.3f}  placebo reject rate={s['rate']:.4f} [{s['wilson_low']:.4f}, {s['wilson_high']:.4f}]  median T={s['T_median']:.3f}", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "placebo_results.csv", index=False)
    (out / "placebo_metadata.json").write_text(json.dumps(meta, indent=2))
    print("COMPLETE")


if __name__ == "__main__":
    main()
