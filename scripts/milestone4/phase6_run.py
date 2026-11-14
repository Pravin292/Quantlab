"""Phase 6, exploratory descriptive placement under Option A (docs/40, revision 6 of docs/26). Run ONCE.

Samples (the exposed stocks, exploratory only, never pooled; D7): the four existing real-data samples. Block = the first 59
scheduled sessions of each sample (docs/26 4.1; for the Yahoo samples the scheduled list is the provider's session list, as
no official calendar is available, docs/40 R6.2). A block with any unusable session is INSUFFICIENT and is not measured.
No random numbers, no simulation, no H1 statistic. Output is write-once: outputs/milestone4/phase6/ (aggregates only).
Usage: python scripts/milestone4/phase6_run.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))

from quantlab.calendars import NSE, US, expected_slots, market_for_symbol      # noqa: E402
from quantlab.research import dependence as dep, direct_sim as ds, h1_calibration as hc, phase6 as p6   # noqa: E402
from quantlab.research.panel import load_tables                                # noqa: E402
import run_h1_inference as inf                                                  # noqa: E402
import run_h1_next as nx                                                        # noqa: E402

OUT = ROOT / "outputs" / "milestone4" / "phase6"
MANIFEST = ROOT / "outputs" / "milestone4" / "frozen_phase6_inputs.sha256"
MAIN = ["open", "middle", "close"]
N_BLOCK = 59
STRICT_Z, STRICT_MIN = 8.0, 54               # docs/26 7.3 S2, S4 (n_s >= ceil(0.9 * 59))
ROUNDING_SHARE = 0.05                        # docs/26 8.9
SAMPLES = [  # (id, label, folder, market)
    ("nse_first", "NSE · first Yahoo sample", "data/clean", NSE),
    ("us_first", "US · first Yahoo sample", "data/clean", US),
    ("nse_fresh", "NSE · fresh Yahoo pull", "data/clean_p2", NSE),
    ("us_fresh", "US · fresh Alpaca pull", "data/clean_p2_us", US),
]
ALWAYS = ["D-TAIL-UNAVAILABLE-OPTION-A", "D-ALT-NO-PER-STOCK-REFERENCE", "LAPLACE-UNEVALUATED"]
ALWAYS_FLAGS = ["SHAPE-THRESHOLDS-UNCHECKED", "EXPLORATORY-EXPOSED-STOCKS", "NOT-INDEPENDENT-OF-DOMAIN"]
WORDING = ("The measured dimensions of this block are reported against simulated worlds in which C3 stayed within its "
           "pre-specified upper limit; features listed in docs/26 section 8.9 as unmapped are not covered. Reference: Option A "
           "(docs/29, docs/38): D-tail unavailable, no per-stock and no Laplace reference; no coverage label is assigned.")


def verify(manifest):
    import hashlib
    bad = 0
    for line in Path(manifest).read_text().splitlines():
        h, _, rel = line.partition("  ")
        if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != h:
            bad += 1
            print("MISMATCH", rel)
    return bad


def library(market, mk):
    used = np.concatenate(ds.used_slot_index(market))
    lib = {s: inf.profile_for(mk, s, 1.0)[used] for s in ("flat", "E", "D5", "R2")}
    lib["D1.5"] = nx.exp_profile(market, 1.5)[used]
    lib["D3.0"] = nx.exp_profile(market, 3.0)[used]
    return lib, used


def arrays(folder, market):
    tabs = load_tables(ROOT / folder)
    labels = list(expected_slots(market, "2026-08-03").strftime("%H:%M"))
    syms = sorted(s for s in tabs if market_for_symbol(s).name == market.name)
    dates = sorted(set().union(*[set(tabs[s]["date"]) for s in syms]))
    shp = (len(syms), len(dates), len(labels))
    ret, vol, close = np.full(shp, np.nan), np.full(shp, np.nan), np.full(shp, np.nan)
    for i, s in enumerate(syms):
        t = tabs[s]
        t = t[(t["status"] == "ok") & t["period"].isin(MAIN) & np.isfinite(t["ret"])]
        di = pd.Index(dates).get_indexer(t["date"])
        si = pd.Index(labels).get_indexer(t["slot"])
        k = (di >= 0) & (si >= 0)
        ret[i, di[k], si[k]] = t["ret"].to_numpy()[k]
        vol[i, di[k], si[k]] = t["volume"].to_numpy(float)[k]
        close[i, di[k], si[k]] = t["close"].to_numpy(float)[k]
    idx = ds.used_slot_index(market)
    ret_u, groups = hc.to_used(ret, idx)
    vol_u, _ = hc.to_used(vol, idx)
    close_u, _ = hc.to_used(close, idx)
    return syms, [str(d) for d in dates], ret_u, vol_u, close_u, groups


def summaries(full, mi, mj):
    return {k: p6.jackknife_summary(full[k], mi[k], mj[k]) for k in full}


def map_block(r2, ret, groups, market, mk, lib, used):
    """Measurements, intervals and the Option A mapping for one complete block."""
    full, mi, mj = p6.jackknife_all(r2, ret, groups, market, mk, lib, dep.shaped_profile, used)
    js = summaries(full, mi, mj)
    n = r2.shape[1]
    h = (n + 1) // 2
    halves = [p6.measure(r2[:, sl], ret[:, sl], groups, market, mk, lib, dep.shaped_profile, used)
              for sl in (slice(0, h), slice(h, n))]
    s_half = p6.half_min_distance(lib)
    dims = {"D-daysd": p6.dimension_daysd(js["M10_day_sd"], mi["M10_day_sd"], tuple(x["M10_day_sd"] for x in halves))}
    dims["D-dep"] = p6.dimension_dep({c: (js[f"M11_{c}" if c == "phi" else f"M12_{c}"], mi[f"M11_{c}" if c == "phi" else f"M12_{c}"],
                                          tuple(x[f"M11_{c}" if c == "phi" else f"M12_{c}"] for x in halves)) for c in ("phi", "s", "rho")}, mk)
    def shape_dimension(prefix):
        units = {}
        for u in ("panel", "stock0", "stock1", "stock2"):
            dj = {s: js[f"{prefix}_{u}_d_{s}"] for s in p6.SHAPE_ORDER}
            dmi = {s: mi[f"{prefix}_{u}_d_{s}"] for s in p6.SHAPE_ORDER}
            hq = []
            for x in halves:
                dd = {s: x[f"{prefix}_{u}_d_{s}"] for s in p6.SHAPE_ORDER}
                s1, _ = p6.nearest(dd)
                hq.append(dd[s1] / s_half[s1])
            units[u] = p6.dimension_shape_unit(dj, dmi, s_half, tuple(hq))
        res = [v["result"] for v in units.values()]
        flags = sorted({f for v in units.values() for f in v["flags"]})
        if any(units[u]["nearest"] != units["panel"]["nearest"] for u in ("stock0", "stock1", "stock2")):
            flags.append("STOCK-SHAPE-DIFFERS")
        return {"result": "U" if "U" in res else max(res), "why": [f"{u}:{w}" for u, v in units.items() for w in v["why"]],
                "flags": flags, "units": units}
    dims["D-shape"] = shape_dimension("M8")                     # primary (docs/40 R6.5)
    dims["D-tail"] = {"result": "U", "why": ["D-TAIL-UNAVAILABLE-OPTION-A"]}
    dims["D-alt"] = {"result": "U", "why": ["D-ALT-NO-PER-STOCK-REFERENCE"]}
    lab = p6.label_option_a(dims)
    dims["D-shape-literal (report only)"] = shape_dimension("M8L")   # secondary, never enters the label
    return full, js, dims, lab


def rounding(ret_close, market_close):
    """M17: tick inferred as the smallest positive price step in the block; ratio to the median |5-minute price change|."""
    c = market_close
    steps = np.abs(np.diff(c, axis=2))
    steps = steps[np.isfinite(steps)]
    pos = np.round(steps[steps > 0], 6)
    tick = float(pos.min()) if len(pos) else np.nan
    med = float(np.median(steps))
    return tick, med, float(np.nanmedian(c)), (tick / med if med > 0 else np.nan)


def main():
    if OUT.exists() and any(OUT.iterdir()):
        sys.exit(f"{OUT} already has files: single-run rule.")
    if verify(MANIFEST):
        sys.exit("freeze manifest mismatch: stop.")
    blocks, meas_rows, dim_rows, shape_rows = [], [], [], []
    for sid, label, folder, market in SAMPLES:
        mk = market.name
        syms, dates, ret, vol, close, groups = arrays(folder, market)
        sched = dates                      # docs/40 R6.2: the provider's session list (us_fresh: equals the frozen 80-session list)
        bdates = sched[:N_BLOCK]
        pos = [dates.index(d) if d in dates else -1 for d in bdates]
        ok = [p >= 0 and bool(np.isfinite(ret[:, p, :]).all()) for p in pos]
        row = {"sample": sid, "label": label, "market": mk, "symbols": " ".join(syms), "sessions_in_sample": len(dates),
               "block_first": bdates[0], "block_last": bdates[-1], "block_n": len(bdates),
               "unusable_in_block": int(len(ok) - sum(ok)), "unusable_dates": " ".join(d for d, o in zip(bdates, ok) if not o),
               "M16_unusable_share_sample": float(np.mean([not np.isfinite(ret[:, i, :]).all() for i in range(len(dates))]))}
        if len(bdates) < N_BLOCK or not all(ok):
            row.update(status="INSUFFICIENT", label_final="INSUFFICIENT", reasons="BLOCK-HAS-UNUSABLE-SESSION")
            blocks.append(row)
            print(sid, "INSUFFICIENT", row["unusable_dates"], flush=True)
            continue
        lib, used = library(market, mk)
        p = np.array(pos)
        r_b, v_b, c_b = ret[:, p], vol[:, p], close[:, p]
        r2_b = r_b ** 2
        tick, med_step, price, tick_ratio = rounding(r_b, c_b)
        full, js, dims, lab = map_block(r2_b, r_b, groups, market, mk, lib, used)
        # strict variant (docs/26 7.3 S1-S6): one detection pass on the baseline standardisation
        e2 = hc.fit_bar_model(r2_b, groups).e2
        flagged = np.sqrt(e2) > STRICT_Z
        zero_vol = (v_b == 0)
        removed = sorted(set(np.flatnonzero(flagged.any(axis=(0, 2)))) | set(np.flatnonzero(zero_vol.any(axis=(0, 2)))))
        n_s = N_BLOCK - len(removed)
        if n_s >= STRICT_MIN:
            keep = np.setdiff1d(np.arange(N_BLOCK), removed)
            _, js_s, dims_s, lab_s = map_block(r2_b[:, keep], r_b[:, keep], groups, market, mk, lib, used)
            strict = lab_s["label"]
        else:
            js_s, dims_s, strict = None, None, "NOT-EVALUABLE (CLEANING-HEAVY)"
        reasons = list(ALWAYS)
        for d, v in dims.items():
            if "literal" in d:
                continue
            if v["result"] != 1:
                reasons.append(f"{d}={v['result']}")
            reasons += [str(x) for x in v.get("why", []) if x not in ALWAYS]
            if v.get("reason"):
                reasons.append(v["reason"])
            reasons += v.get("reasons", [])
        flags = list(ALWAYS_FLAGS) + dims["D-shape"]["flags"]
        if np.isfinite(tick_ratio) and tick_ratio > ROUNDING_SHARE:
            reasons.append("ROUNDING-MATERIAL")
        row.update(status="ANALYSED", label_baseline=lab["label"], label_strict=strict, label_final=lab["label"],
                   strict_removed_sessions=len(removed), strict_n=n_s, strict_flagged_bars=int(flagged.sum()),
                   strict_zero_volume_bars=int(zero_vol.sum()), M17_median_price=price, M17_tick=tick,
                   M17_median_abs_price_step=med_step, M17_tick_over_median_step=tick_ratio,
                   reasons=" | ".join(dict.fromkeys(reasons)), flags=" | ".join(dict.fromkeys(flags)), wording=WORDING)
        blocks.append(row)
        for variant, jss in (("baseline", js), ("strict", js_s)):
            if jss is None:
                continue
            for k, j in jss.items():
                meas_rows.append({"sample": sid, "variant": variant, "measure": k, **j,
                                  "unreliable": " | ".join(p6.generic_unreliable(j))})
        for variant, dd in (("baseline", dims), ("strict", dims_s)):
            if dd is None:
                continue
            for d, v in dd.items():
                dim_rows.append({"sample": sid, "variant": variant, "dimension": d, "result": v["result"],
                                 "why": " | ".join(map(str, v.get("why", []))), "reason": v.get("reason") or " | ".join(v.get("reasons", []))})
            for method, key in (("primary", "D-shape"), ("literal", "D-shape-literal (report only)")):
                for u, uv in dd[key]["units"].items():
                    shape_rows.append({"sample": sid, "variant": variant, "method": method, "unit": u, "result": uv["result"],
                                       "nearest": uv["nearest"], "second": uv["second"], "q_nearest": uv["q_nearest"],
                                       "K": " ".join(uv["K"]), "flags": " ".join(uv["flags"]), "why": " | ".join(uv["why"])})
        print(sid, "baseline", lab["label"], "| strict", strict, flush=True)
    OUT.mkdir(parents=True)
    pd.DataFrame(blocks).to_csv(OUT / "phase6_blocks.csv", index=False)
    pd.DataFrame(meas_rows).to_csv(OUT / "phase6_measurements.csv", index=False)
    pd.DataFrame(dim_rows).to_csv(OUT / "phase6_dimensions.csv", index=False)
    pd.DataFrame(shape_rows).to_csv(OUT / "phase6_shape_units.csv", index=False)
    (OUT / "phase6_metadata.json").write_text(json.dumps({
        "protocol": "docs/26 revision 5 as amended by docs/40 (revision 6, exploratory, Option A)", "block_n": N_BLOCK,
        "jackknife_groups": p6.G_GROUPS, "strict_z": STRICT_Z, "strict_min_sessions": STRICT_MIN,
        "manifest": str(MANIFEST.relative_to(ROOT)), "random_numbers": "none", "h1_statistic": "not computed"}, indent=2))


if __name__ == "__main__":
    main()
