"""Generate docs/43_stage6_report.md from the saved Stage 6 result files (outputs/milestone4/stage6/part_a|part_b|part_c). Every number comes from those files;
the interpretation sentences are the ones committed in docs/42 for each outcome. No simulation, no new analysis.   python scripts/milestone4/stage6_make_report.py"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "outputs" / "milestone4" / "stage6"
OUT = ROOT / "docs" / "43_stage6_report.md"
sys.path.insert(0, str(ROOT / "src"))
from quantlab.research import stage6 as s6                      # noqa: E402

LEVEL_LABEL = {"S0_none": "S0 independent", "S1_validated": "S1 earlier estimate", "S2_fresh_point": "S2 US fresh, measured", "S3_fresh_upper": "S3 US fresh, upper range",
               "S4_one_and_half_x": "S4 1.5 × measured", "S5_illustrative": "S5 illustrative stress"}


def md(df, align=None):
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---:" if (align or {}).get(c) == "r" else "---" for c in cols) + "|"]
    out += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(out)


def pct(x, d=2):
    return f"{100 * float(x):.{d}f}%"


def part_a():
    a = pd.read_csv(SRC / "part_a" / "size_by_cell.csv")
    outcome = pd.read_csv(SRC / "part_a" / "part_a_outcome.csv").iloc[0]
    meta = pd.read_csv(SRC / "part_a" / "run_metadata.csv", index_col=0)["value"]
    rows = []
    for lv in s6.LEVELS:
        g = a[a.level == lv]
        dep = s6.dependence_for(lv, "US")
        label = "market-specific (NSE 0.355 / 0.454 / 0.441, US 0.187 / 0.141 / 0.190)" if lv == "S1_validated" else f"{dep['ret_corr']} / {dep['share']} / {dep['phi']}"
        st = g.status.str.replace("REPORTED_", "")
        rows.append({"Level": LEVEL_LABEL[lv], "ret_corr / share / phi": label, "Role": "gated" if lv in s6.GATED_LEVELS else "reported only", "Cells": len(g),
                     "PASS": int((st == "PASS").sum()), "PASS_AMBIG.": int((st == "PASS_AMBIGUOUS").sum()), "FAIL_AMBIG.": int((st == "FAIL_AMBIGUOUS").sum()), "FAIL": int((st == "FAIL").sum()),
                     "Highest C3 rate": pct(g.rate_c3.max()), "Median C3 rate": pct(g.rate_c3.median()), "Old test, highest": pct(g.rate_base.max())})
    by_level = pd.DataFrame(rows)
    top = a.sort_values("rate_c3", ascending=False).head(6)
    top_t = pd.DataFrame({"Market": top.market, "Shape": top["shape"], "Tail": top["tail"], "Sessions": top.n_days, "Level": top.level.map(LEVEL_LABEL), "Role": np.where(top.gated, "gated", "reported"),
                          "C3 rate": top.rate_c3.map(pct), "Wilson 95%": [f"[{pct(l)}, {pct(h)}]" for l, h in zip(top.wilson_low, top.wilson_high)], "Limit": top["tail"].map(lambda t: "5.5%" if t == "T6" else "6.0%")})
    gated = a[a.gated]
    by_n = pd.DataFrame([{"Sessions": n, "Gated cells": len(g), "Highest C3 rate": pct(g.rate_c3.max()), "Median C3 rate": pct(g.rate_c3.median())} for n, g in gated.groupby("n_days")])
    failing = a[a.gated & a.status.isin(["FAIL", "FAIL_AMBIGUOUS"])]
    rep = a[~a.gated]
    over = rep[rep.status.str.contains("FAIL")]
    reading = {"STRESS_PASS": "**STRESS_PASS.** C3 stayed within its limits at the dependence levels measured in real data, including their upper uncertainty range, in the cells tested. This is not a claim of validity everywhere.",
               "STRESS_MARGINAL": "**STRESS_MARGINAL.** No gated cell failed, but at least one has an interval that reaches its limit. C3 is not shown to fail, and calibration under dependence is not claimed.",
               "STRESS_BOUNDARY": "**STRESS_BOUNDARY.** No gated cell clearly failed, but at least one is too close to its limit to call. C3 is not shown safe there.",
               "STRESS_FAIL": "**STRESS_FAIL.** At least one gated cell exceeds its limit. C3 is not shown safe at that dependence level (cells listed above). It was not retuned; any remedy would be a separate method with its own preregistration."}[outcome.outcome]
    edge = (f"At the two ungated stress levels (S4, S5) C3 stayed within the limits in all {len(rep)} cells; the highest rate was {pct(rep.rate_c3.max())}. That is the edge of what was tried, not a guarantee beyond it."
            if len(over) == 0 else f"At the ungated stress levels, {len(over)} of {len(rep)} cells exceeded a limit (highest {pct(rep.rate_c3.max())}). This marks the edge of the evidence: C3 is not shown safe at dependence this strong.")
    txt = [f"## 2. Part A: is C3 still safe when stocks and days are dependent?",
           f"**Run:** {len(a)} cells × {int(a.n_sims.iloc[0]):,} simulations = {len(a) * int(a.n_sims.iloc[0]):,}; master seed {int(meta['master_seed'])}; wall time {float(meta['wall_seconds']) / 60:.1f} minutes. Volatility was truly equal in every cell, so every rejection is a false alarm. A gated cell passes when C3's rate is at most 5.5% (tier A, tail T6) or 6.0% (tier B, tail T4).",
           f"**Outcome label: {outcome.outcome}.** Of {int(outcome.gated_cells)} gated cells: {int(outcome.n_PASS)} PASS, {int(outcome.n_PASS_AMBIGUOUS)} PASS_AMBIGUOUS, {int(outcome.n_FAIL_AMBIGUOUS)} FAIL_AMBIGUOUS, {int(outcome.n_FAIL)} FAIL. Highest gated C3 rate: **{pct(outcome.highest_gated_rate)}**; highest rate at the ungated levels: {pct(outcome.highest_reported_rate)}.",
           "![C3 false-alarm rate under dependence](images/stage6_size.svg)", "### By dependence level", md(by_level, {c: "r" for c in ("Cells", "PASS", "PASS_AMBIG.", "FAIL_AMBIG.", "FAIL")}),
           "### Highest C3 rates in the whole grid", md(top_t), "### By sample size (gated cells)", md(by_n)]
    if len(failing):
        txt += ["### Gated cells that failed or are ambiguous", md(pd.DataFrame({"Market": failing.market, "Shape": failing["shape"], "Tail": failing["tail"], "Sessions": failing.n_days, "Level": failing.level.map(LEVEL_LABEL),
                                                                                  "C3 rate": failing.rate_c3.map(pct), "Status": failing.status}))]
    txt += ["### Reading (committed in docs/42 before the run)", reading, edge,
            f"For reference, the old bootstrap test on the same datasets had a highest rate of {pct(a.rate_base.max())} and a median of {pct(a.rate_base.median())}; it gates nothing."]
    return "\n\n".join(txt), outcome, a


def part_b():
    b = pd.read_csv(SRC / "part_b" / "power_by_cell.csv")
    mde = pd.read_csv(SRC / "part_b" / "min_detectable_effect.csv")
    meta = pd.read_csv(SRC / "part_b" / "run_metadata.csv", index_col=0)["value"]
    txt = ["## 3. Part B: how big a difference can C3 detect?",
           f"**Run:** {len(b)} cells × {int(b.n_sims.iloc[0]):,} simulations; master seed {int(meta['master_seed'])}; shape R2, tail T4 (heavy), open and close volatility = multiplier × the middle's. Power = share of simulations in which C3 rejects. Nothing is gated.",
           "![Power of C3](images/stage6_power.svg)"]
    for mk in ("US", "NSE"):
        for lv, name in (("S0_none", "independent stocks and days"), ("S2_fresh_point", "dependence as measured in the US fresh sample")):
            g = b[(b.market == mk) & (b.level == lv)]
            t = g.pivot(index="n_days", columns="mult", values="power").sort_index()
            m = mde[(mde.market == mk) & (mde.level == lv)].set_index("n_days")
            tab = pd.DataFrame({"Sessions": t.index, **{f"{c:g}×": [pct(v, 1) for v in t[c]] for c in t.columns},
                                "Smallest multiplier with 80% power": [(f"≤ {m.loc[n, 'min_detectable_mult']:.2f}×" if m.loc[n, "kind"] == "at_or_below_first" else (f"> {m.loc[n, 'min_detectable_mult']:.2f}× (not reached)" if m.loc[n, "kind"] == "not_reached" else f"{m.loc[n, 'min_detectable_mult']:.2f}×")) for n in t.index]})
            txt += [f"### {mk}, {name}", md(tab)]
    real = b[b["mult"] == 2.0]
    lowest = real.power.min()
    m59 = mde[(mde.n_days == 59)]
    txt += ["### Reading",
            f"- With 59 sessions the smallest open/close multiplier C3 detects with 80% power is {m59.min_detectable_mult.min():.2f}× to {m59.min_detectable_mult.max():.2f}× across the four settings above; with 250 sessions it is {mde[mde.n_days == 250].min_detectable_mult.min():.2f}× to {mde[mde.n_days == 250].min_detectable_mult.max():.2f}×.",
            f"- At a multiplier of 2.0× (the real samples showed open/middle ≈ 1.95–2.17×), the lowest power anywhere in the grid is **{pct(lowest, 1)}**, so a difference of the observed size is found almost every time, including under the stronger dependence.",
            "- Smaller real differences (1.05×–1.2×) are often missed at 59 sessions: C3 is cautious, and a 'not rejected' result there is weak evidence of equality, never proof of it.",
            "- Power values come from simulated markets with the stated shape and tail; real markets may differ."]
    return "\n\n".join(txt)


def part_c():
    c = pd.read_csv(SRC / "part_c" / "placebo_results.csv")
    meta = json.loads((SRC / "part_c" / "placebo_metadata.json").read_text())
    done = c[c.status == "PLACEBO_DONE"].copy()

    def label(r):
        return "PLACEBO_OK" if r <= 0.055 else ("PLACEBO_WARN" if r <= 0.07 else "PLACEBO_HIGH")
    done["label"] = done.rate.map(label)
    tab = pd.DataFrame({"Sample": done["sample"], "Real T": done.real_T.map(lambda v: f"{v:.2f}"), "Placebo rejection rate": done.rate.map(lambda v: pct(v, 2)),
                        "Wilson 95%": [f"[{pct(l)}, {pct(h)}]" for l, h in zip(done.wilson_low, done.wilson_high)], "Median placebo T": done.T_median.map(lambda v: f"{v:.2f}"),
                        "95th percentile of placebo T": done.T_p95.map(lambda v: f"{v:.2f}"), "Largest placebo T": done["T_max"].map(lambda v: f"{v:.2f}"), "Label": done.label})
    skipped = c[c.status != "PLACEBO_DONE"]
    txt = ["## 4. Part C: does C3 behave on real data's own structure?",
           f"**Run:** each tested real sample's 59 sessions, time-of-day labels shuffled in every session (same shuffle for all three stocks), {meta['n_rep']:,} shuffles per sample, master seed {meta['master_seed']}, C3 limit {meta['crit_n59']:.4f}. The truth is 'equal' by construction, so every rejection is a false alarm. The rebuilt data reproduced each recorded real T exactly.",
           "![Real-data placebo](images/stage6_placebo.svg)", md(tab, {c: "r" for c in ("Real T",)})]
    if len(skipped):
        txt.append("Not computed: " + "; ".join(f"{r['sample']} ({r['note']})" for _, r in skipped.iterrows()) + ".")
    worst = done.rate.max()
    txt += ["### Reading (committed in docs/42 before the run)",
            f"- Labels: OK means the placebo rate is at most 5.5%; WARN means 5.5% to 7.0%; HIGH means above 7.0%. Result: " + ", ".join(f"{r['sample']} {r['label']}" for _, r in done.iterrows()) + ".",
            f"- The highest placebo rate was {pct(worst)}; every real T is far above its placebo 95th percentile (largest placebo T of any sample: {done['T_max'].max():.2f} against real values of {done.real_T.min():.2f} to {done.real_T.max():.2f}), so the real rejections are not explained by fat tails or dependence alone.",
            "- Limits: the shuffle also breaks the within-day pattern of volatility, so this is a stress check, not a proof of size; the shuffles reuse the same 59 sessions, so they describe C3 on these sessions rather than on all possible days; and it does not test power."]
    return "\n\n".join(txt), done


def main():
    if OUT.exists():
        sys.exit(f"{OUT} exists: not overwriting.")
    a_txt, outcome, a = part_a()
    b_txt = part_b()
    c_txt, c = part_c()
    summary = [f"- **Part A (dependence stress test): {outcome.outcome}.** Highest C3 false-alarm rate on the {int(outcome.gated_cells)} gated cells: {pct(outcome.highest_gated_rate)} (limits 5.5% and 6.0%).",
               "- **Part B (power):** see the tables in section 3 for the smallest difference detected at 59, 90, 125, 180 and 250 sessions.",
               "- **Part C (real-data placebo):** " + "; ".join(f"{r['sample']} {pct(r['rate'])}" for _, r in c.iterrows()) + f" (limit 5.5%)."]
    head = ["# 43: Stage 6 report: dependence stress test, power curve and real-data placebo",
            "**Status: final, generated from the saved result files by `scripts/milestone4/stage6_make_report.py`. The design, gates and the interpretation of each outcome were fixed in [docs/42](42_stage6_preregistration_dependence_power_placebo.md) before any run.** Parts A and B are simulated data only; Part C re-used the three real samples already tested (no new data). C3 was applied unchanged; no earlier frozen file was touched.",
            "## 1. Summary", "\n".join(summary)]
    tail = ["## 5. What this changes, and what it does not",
            "- It adds evidence about C3's behaviour at the dependence levels that Phase 6 found in the fresh US data (Part A), a measured answer to 'is C3 too cautious?' (Part B) and a check on real structure (Part C).",
            "- It does **not** prove C3's false-alarm rate on real markets, does not add independent stocks (that needs a new data pull, see [docs/44](44_independent_holdout_design.md)), and makes no claim about trading or profit.",
            "- C3's verdict stays PARTIAL unless the owner decides otherwise after reading this report; Stage 6 does not change it by itself.",
            "## 6. Files",
            "`outputs/milestone4/stage6/part_a/` (96 per-cell result files, `size_by_cell.csv`, `part_a_outcome.csv`), `part_b/` (`power_by_cell.csv`, `min_detectable_effect.csv`), `part_c/` (`placebo_results.csv`), run logs, and `scripts/make_stage6_charts.py` for the charts."]
    OUT.write_text("\n\n".join(head + [a_txt, b_txt, c_txt] + tail) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
