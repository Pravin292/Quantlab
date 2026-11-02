"""EDA statistics. Every function takes the bar table from `masks.build_bar_table`
and uses ONLY bars the masks allow. Nothing is removed from the data silently:
extreme values are reported by `largest_moves`, never dropped.

Definitions (also written up in docs/06_eda_findings.md)
--------------------------------------------------------
return            log return ln(close_t / close_{t-1}) between two consecutive,
                  usable 5-minute bars of the same day (column `ret`).
volatility        sample standard deviation (ddof=1) of those returns.
standardised z    ret / s_slot, where s_slot is that stock's own sample std of
                  returns in the same time-of-day slot. Returns are NOT
                  de-meaned (means are ~0). It uses the whole sample, so it is
                  a DESCRIPTIVE device, not something a strategy could use live.
mean CI (95%)     mean +/- t(0.975, n-1) * sd / sqrt(n): a Student-t interval
                  treating each day's observation in a slot as independent.
                  It ignores serial correlation and changing volatility, and
                  there are many slots, so some intervals exclude 0 by chance.
tail event        |z| > 3. Under a normal distribution the expected share is
                  2 * (1 - Phi(3)) = 0.27%.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .masks import CLOSING_WINDOW, MAIN_PERIODS

MIN_OBS = 5            # fewer observations than this -> statistics left as NaN
TAIL_K = 3.0
PCTS = [0.01, 0.05, 0.95, 0.99]


def main_returns(table: pd.DataFrame) -> pd.DataFrame:
    """Rows eligible for the main close-to-close analysis."""
    return table[table["status"] == "ok"]


def distribution_stats(x: pd.Series) -> dict:
    x = x.dropna()
    n = len(x)
    out = {"n": n}
    if n < MIN_OBS:
        return {**out, **{k: np.nan for k in
                ["mean", "std", "skew", "excess_kurtosis", "min", "max",
                 "p01", "p05", "p95", "p99"]}}
    out.update(mean=x.mean(), std=x.std(ddof=1),
               skew=stats.skew(x, bias=False),
               excess_kurtosis=stats.kurtosis(x, fisher=True, bias=False),
               min=x.min(), max=x.max())
    for p in PCTS:
        out[f"p{int(p * 100):02d}"] = x.quantile(p)
    return out


def add_standardised(ok: pd.DataFrame, min_obs: int = MIN_OBS) -> pd.DataFrame:
    """Add column `z` = ret / (std of ret in the same symbol and slot)."""
    ok = ok.copy()
    grp = ok.groupby(["symbol", "slot"])["ret"]
    sd = grp.transform(lambda s: s.std(ddof=1))
    n = grp.transform("count")
    ok["z"] = ok["ret"] / sd.where(n >= min_obs)
    return ok


def tail_stats(z: pd.Series, k: float = TAIL_K) -> dict:
    z = z.dropna()
    n = len(z)
    beyond = int((z.abs() > k).sum())
    expected = 2 * (1 - stats.norm.cdf(k))
    share = beyond / n if n else np.nan
    return {"n": n, "k": k, "n_beyond": beyond, "share": share,
            "expected_share_if_normal": expected,
            "ratio_to_normal": share / expected if n else np.nan}


def largest_moves(ok_with_z: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """The n largest |z| moves per symbol, with timestamps. REPORTED, never removed.
    Their cause is unknown: we do not attribute them to earnings or news."""
    d = ok_with_z.dropna(subset=["z"]).copy()
    d["abs_z"] = d["z"].abs()
    d = d.sort_values("abs_z", ascending=False).groupby("symbol").head(n)
    d = d.reset_index().rename(columns={d.index.name or "index": "bar_start"})
    return d[["symbol", "bar_start", "slot", "ret", "z", "abs_z"]].sort_values(
        ["symbol", "abs_z"], ascending=[True, False]).reset_index(drop=True)


def mean_by_slot(ok: pd.DataFrame, by: str = "slot", conf: float = 0.95) -> pd.DataFrame:
    """Mean return per slot with a Student-t confidence interval."""
    g = ok.groupby(by)["ret"]
    r = g.agg(n="count", mean="mean", sd=lambda s: s.std(ddof=1)).reset_index()
    r["se"] = r["sd"] / np.sqrt(r["n"])
    tcrit = stats.t.ppf(0.5 + conf / 2, (r["n"] - 1).clip(lower=1))
    r["ci_low"] = r["mean"] - tcrit * r["se"]
    r["ci_high"] = r["mean"] + tcrit * r["se"]
    small = r["n"] < MIN_OBS
    r.loc[small, ["mean", "sd", "se", "ci_low", "ci_high"]] = np.nan
    r["ci_excludes_zero"] = (r["ci_low"] > 0) | (r["ci_high"] < 0)
    return r


def volatility_by_slot(ok: pd.DataFrame, by: str = "slot") -> pd.DataFrame:
    g = ok.groupby(by)["ret"]
    r = g.agg(n="count", std=lambda s: s.std(ddof=1),
              mean_abs=lambda s: s.abs().mean()).reset_index()
    r.loc[r["n"] < MIN_OBS, ["std", "mean_abs"]] = np.nan
    r["std_bps"] = r["std"] * 1e4
    return r


def volatility_by_period(ok: pd.DataFrame) -> pd.DataFrame:
    """Pooled sample std of 5-minute returns inside each main period."""
    d = ok[ok["period"].isin(MAIN_PERIODS)]
    r = d.groupby("period")["ret"].agg(
        n="count", std=lambda s: s.std(ddof=1),
        mean_abs=lambda s: s.abs().mean()).reset_index()
    r["std_bps"] = r["std"] * 1e4
    r["period"] = pd.Categorical(r["period"], MAIN_PERIODS, ordered=True)
    return r.sort_values("period").reset_index(drop=True)


def volume_profile(table: pd.DataFrame, by: str = "slot") -> pd.DataFrame:
    """Median volume per slot (reliable bars only) and that median relative to
    the median of all slot medians for the same symbol (1.0 = typical)."""
    v = table[table["volume_ok"]]
    r = v.groupby(["symbol", by])["volume"].agg(n="count", median_volume="median").reset_index()
    r.loc[r["n"] < MIN_OBS, "median_volume"] = np.nan
    ref = r.groupby("symbol")["median_volume"].transform("median")
    r["relative_volume"] = r["median_volume"] / ref
    return r


def opening_candle_stats(table: pd.DataFrame) -> pd.DataFrame:
    """Open-to-close return of the first candle of the session, per symbol."""
    rows = []
    for sym, g in table.groupby("symbol"):
        rows.append({"symbol": sym, **distribution_stats(g["ret_oc"])})
    return pd.DataFrame(rows)


def closing_window_stats(table: pd.DataFrame) -> pd.DataFrame:
    """How much of the NSE 15:15-15:25 window is usable, and its returns (separate)."""
    w = table[table["period"] == CLOSING_WINDOW]
    rows = []
    for (sym, slot), g in w.groupby(["symbol", "slot"]):
        rows.append({"symbol": sym, "slot": slot, "n_bars": len(g),
                     "n_empty_or_excluded": int(g["status"].str.startswith("excluded").sum()),
                     "n_with_return": int(g["ret_closing"].notna().sum()),
                     **{f"ret_{k}": v for k, v in distribution_stats(g["ret_closing"]).items()
                        if k in ("mean", "std")}})
    return pd.DataFrame(rows)


def quality_category(table: pd.DataFrame) -> pd.Series:
    """One label per bar for the data-quality heatmap."""
    cat = pd.Series("ok", index=table.index, dtype=object)
    cat[table["status"].eq("nse_closing_window")] = "nse_closing_window_usable_but_excluded"
    cat[table["volume_status"].eq("excluded_nse_0915_volume")] = "nse_0915_volume_excluded"
    cat[table["volume_status"].eq("excluded_zero_missing_or_flagged_volume")] = "zero_or_missing_volume"
    cat[table["status"].eq("excluded_missing_ohlc")] = "empty_bar"
    cat[table["status"].isin(["excluded_forming_bar", "excluded_unexpected_session_bar",
                              "excluded_invalid_ohlc", "excluded_duplicate_timestamp"])] = "other_excluded"
    return cat


def quality_by_slot(table: pd.DataFrame) -> pd.DataFrame:
    t = table.assign(category=quality_category(table))
    ct = (t.groupby(["symbol", "slot"])["category"].value_counts(normalize=True)
          .unstack(fill_value=0).reset_index())
    ct["n_bars"] = t.groupby(["symbol", "slot"]).size().values
    return ct


def attach_mins_since_open(result: pd.DataFrame, table: pd.DataFrame) -> pd.DataFrame:
    """Add `mins_since_open` to a per-symbol, per-slot result.

    The mapping is looked up per SYMBOL because the same clock label means a
    different distance from the open in each market (10:00 is 45 minutes after
    the NSE open but 30 minutes after the US open)."""
    key = table[["symbol", "slot", "mins_since_open"]].drop_duplicates(["symbol", "slot"])
    return result.merge(key, on=["symbol", "slot"], how="left")
