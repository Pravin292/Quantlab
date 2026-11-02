"""H2: does unusually high volume carry information about LATER returns or volatility?

Timeline for an event candle t (start time tau):
    candle t     : tau .. tau+5   its volume is only final at tau+5
    candle t+1   : first candle we could act in. PRIMARY ENTRY = its OPEN  O_{t+1}
    candles t+1..t+k : the hypothetical holding window (k = 3 -> 15 minutes)
    PRIMARY EXIT = close of candle t+k, C_{t+k}

Volume event (past-only baseline):
    B_{d,s} = median volume of the same stock over the previous L = 10 trading
              days in slots s-1, s, s+1  (needs >= MIN_VALID of those 30 values)
    ratio   = V_{d,s} / B_{d,s}        event = ratio >= 2.0   (fixed)

Outcomes (all start AFTER the event candle is complete):
    f_open  = ln(C_{t+k} / O_{t+1})                    forward return
    g_open  = sign(r_t) * f_open                       > 0 => the move continued
    FV_open = sqrt( (1/k) * [ ln(C_{t+1}/O_{t+1})^2 + sum_{j=2..k} r_{t+j}^2 ] )
              The FIRST holding candle is measured open-to-close, because we
              enter at its open: the gap from C_t to O_{t+1} is not part of the
              exposure. Later candles are ordinary close-to-close returns
              r = ln(C_t / C_{t-1}), because we hold across those boundaries.
    y_fv    = ln( FV / past-only baseline of FV in the same slot )

Optimistic secondary comparison (entry at the event close, as if the volume
were known early): f_close = ln(C_{t+k}/C_t), FV_close = sqrt(mean r_{t+1..t+k}^2).

Controls (volume spikes coincide with big moves and volatility clusters):
    c1 = |r_t| / past-only baseline of |r| in the slot
    c2 = ln( RV6_t / past-only baseline of RV6 ),  RV6 = rms of the last 6 returns
    c3 = ln( RVday_t / past-only baseline of RVday ), RVday = rms of all returns
         from the open up to and including t ("how volatile has today been?")
c3 was added after the M4a calibration showed that, when volume and volatility
share a day-level regime, c1 and c2 alone let the event dummy stand in for it.
The baselines use past days only, so no future information enters any control or event.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..eda.masks import CLOSING_WINDOW
from .inference import demean_two_way, demean_within, ols_cluster, wild_cluster_p
from .panel import WIDTH, past_baseline, to_matrix

L_DEFAULT, THR_DEFAULT, K_DEFAULT = 10, 2.0, 3
MIN_VALID = 20                      # of the 3*L = 30 baseline values
MIN_EVENTS, MIN_EVENT_DAYS = 30, 15
PRICE_COLUMNS = {"open", "high", "low", "close", "ret", "ret_oc", "ret_closing"}


def _shift(M: np.ndarray, j: int) -> np.ndarray:
    """M shifted so that out[:, s] = M[:, s + j] (NaN beyond the day's end)."""
    out = np.full_like(M, np.nan)
    if j == 0:
        return M.copy()
    out[:, :M.shape[1] - j] = M[:, j:]
    return out


def _window_allowed(allowed: np.ndarray, first: int, last: int) -> np.ndarray:
    """True where candles s+first .. s+last all exist and are allowed."""
    ok = np.ones_like(allowed, dtype=bool)
    for j in range(first, last + 1):
        ok &= _shift(allowed.astype(float), j) == 1.0
    return ok


def _trailing_rms(R: np.ndarray, width: int, min_valid: int) -> np.ndarray:
    """rms of the last `width` returns up to and INCLUDING the current candle (all complete by the
    end of that candle); NaN when fewer than min_valid are available."""
    past = np.stack([np.concatenate([np.full((R.shape[0], j), np.nan), R[:, :R.shape[1] - j]], axis=1)
                     for j in range(width)])
    valid = (~np.isnan(past)).sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(valid >= min_valid, np.sqrt(np.nansum(past ** 2, axis=0) / np.maximum(valid, 1)), np.nan)


def _flatten(table: pd.DataFrame, market_name: str, mats: dict[str, np.ndarray],
             dates: np.ndarray) -> pd.DataFrame:
    nd, ns = next(iter(mats.values())).shape
    di, si = np.indices((nd, ns))
    df = pd.DataFrame({"date": dates[di.ravel()], "slot_idx": si.ravel(),
                       "symbol": table["symbol"].iloc[0]})
    for name, M in mats.items():
        df[name] = M.ravel()
    return df


def event_features(table: pd.DataFrame, L: int = L_DEFAULT, thr: float = THR_DEFAULT,
                   k: int = K_DEFAULT, delay: int = 0) -> pd.DataFrame:
    """Per-candle event flags and window availability. Uses ONLY volume and
    candle availability columns; price columns are never read here (the H2
    feasibility report relies on this and a test enforces it)."""
    m = table["market"].iloc[0]
    vol = table["volume"].where(table["volume_ok"])
    V, dates = to_matrix(table, vol, m)
    base = past_baseline(V, L, MIN_VALID)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = V / base
    allowed = to_matrix(table, (table["usable"] & (table["period"] != CLOSING_WINDOW)).astype(float), m)[0]
    allowed = np.nan_to_num(allowed) == 1.0
    ret_ok = np.nan_to_num(to_matrix(table, (table["status"] == "ok").astype(float), m)[0]) == 1.0
    window = _window_allowed(allowed, 1, k + delay)
    event = np.nan_to_num(ratio, nan=0.0) >= thr
    eligible = event & window & ret_ok
    return _flatten(table, m, {"volume": V, "baseline": base, "ratio": ratio,
                               "event": event.astype(float), "window_valid": window.astype(float),
                               "ret_ok": ret_ok.astype(float), "eligible": eligible.astype(float)}, dates)


def feasibility(table: pd.DataFrame, **kw) -> dict:
    """Outcome-blind counts for one stock: events, distinct event days, usable events."""
    cols = [c for c in table.columns if c not in PRICE_COLUMNS]
    f = event_features(table[cols], **kw)
    ev = f[f["event"] == 1.0]
    use = f[f["eligible"] == 1.0]
    return {"symbol": table["symbol"].iloc[0], "bars_with_baseline": int(f["ratio"].notna().sum()),
            "n_events": len(ev), "n_event_days": ev["date"].nunique(),
            "n_usable_events": len(use), "n_usable_event_days": use["date"].nunique()}


def adequacy(n_events: int, n_event_days: int) -> str:
    return "ADEQUATE" if (n_events >= MIN_EVENTS and n_event_days >= MIN_EVENT_DAYS) else "UNDERPOWERED"


def outcome_features(table: pd.DataFrame, L: int = L_DEFAULT, thr: float = THR_DEFAULT,
                     k: int = K_DEFAULT, delay: int = 0) -> pd.DataFrame:
    """Event features plus outcomes and controls (reads prices; real-data use
    is reserved for the frozen protocol runs)."""
    m = table["market"].iloc[0]
    feats = event_features(table, L, thr, k, delay)
    O, dates = to_matrix(table, table["open"].where(table["usable"]), m)
    C, _ = to_matrix(table, table["close"].where(table["usable"]), m)
    R, _ = to_matrix(table, "ret", m)                           # close-to-close, status == ok only
    e, x = 1 + delay, k + delay                                  # entry / exit candle offsets
    with np.errstate(divide="ignore", invalid="ignore"):
        f_open = np.log(_shift(C, x) / _shift(O, e))
        f_close = np.log(_shift(C, k) / C)
        gap = np.log(_shift(O, 1) / C)
        first = np.log(_shift(C, e) / _shift(O, e)) ** 2          # open-to-close of the first holding candle
        rest = sum(_shift(R, j) ** 2 for j in range(e + 1, x + 1)) if x >= e + 1 else 0.0
        fv_open = np.sqrt((first + rest) / k)
        fv_close = np.sqrt(sum(_shift(R, j) ** 2 for j in range(1, k + 1)) / k)
        sign = np.sign(R)
        sign[sign == 0] = np.nan
    rv6 = _trailing_rms(R, 6, 3)
    rv12 = _trailing_rms(R, 12, 6)
    rv24 = _trailing_rms(R, 24, 12)
    # RVday: rms of every return from the open up to and including t, needs >= 3 valid
    cnt = np.cumsum(~np.isnan(R), axis=1)
    cum = np.cumsum(np.where(np.isnan(R), 0.0, R ** 2), axis=1)
    rvday = np.where(cnt >= 3, np.sqrt(cum / np.maximum(cnt, 1)), np.nan)
    # previous trading day's rms (a PAST day), relative to the median of the previous L days' rms
    day_rms = np.where((~np.isnan(R)).sum(axis=1) >= 20, np.sqrt(np.nanmean(R ** 2, axis=1)), np.nan)
    prev_ratio = np.full(R.shape[0], np.nan)
    for i in range(L, R.shape[0]):
        prev_ratio[i] = day_rms[i - 1] / np.nanmedian(day_rms[i - L:i])
    with np.errstate(invalid="ignore", divide="ignore"):
        base_fv_open = past_baseline(fv_open, L, MIN_VALID)
        base_fv_close = past_baseline(fv_close, L, MIN_VALID)
        c1 = np.abs(R) / past_baseline(np.abs(R), L, MIN_VALID)
        c2 = np.log(rv6 / past_baseline(rv6, L, MIN_VALID))
        c3 = np.log(rvday / past_baseline(rvday, L, MIN_VALID))
        c3_12 = np.log(rv12 / past_baseline(rv12, L, MIN_VALID))
        c3_24 = np.log(rv24 / past_baseline(rv24, L, MIN_VALID))
        c4 = np.log(prev_ratio)[:, None] * np.ones_like(R)
        y_open = np.log(fv_open / base_fv_open)
        y_close = np.log(fv_close / base_fv_close)
    mats = {"f_open": f_open, "g_open": sign * f_open, "f_close": f_close, "g_close": sign * f_close,
            "gap": gap, "fv_open": fv_open, "fv_close": fv_close, "y_fv_open": y_open, "y_fv_close": y_close, "c1": c1, "c2": c2, "c3": c3,
            "c3_12": c3_12, "c3_24": c3_24, "c4": c4}
    outs = _flatten(table, m, mats, dates).drop(columns=["date", "slot_idx", "symbol"])
    return pd.concat([feats, outs], axis=1)


DEFAULT_CONTROLS = ("c1", "c2", "c3")


def regression_sample(feat: pd.DataFrame, outcome: str, controls=DEFAULT_CONTROLS) -> pd.DataFrame:
    """Candles with a baseline, a valid window and complete outcome and controls."""
    need = [outcome, *controls, "ratio"]
    d = feat[(feat["window_valid"] == 1.0) & (feat["ret_ok"] == 1.0)].dropna(subset=need)
    return d.replace([np.inf, -np.inf], np.nan).dropna(subset=need)


def event_regression(feat: pd.DataFrame, outcome: str, B: int, rng: np.random.Generator,
                     day_fe: bool = True, controls=DEFAULT_CONTROLS) -> dict:
    """outcome ~ event + c1 + c2 + c3 with stock x slot effects absorbed and
    standard errors clustered by day. Primary p-value: wild cluster bootstrap.

    day_fe=True ALSO absorbs stock x day effects, so an event is compared with
    other candles of the SAME stock on the SAME day. This removes any day-level
    activity regime shared by volume and volatility (the M4a calibration showed
    the controls alone cannot: they measure that regime with noise)."""
    controls = list(controls)
    d = regression_sample(feat, outcome, controls).copy()
    d["event_f"] = d["event"]
    d["_fe"] = d["symbol"] + "|" + d["slot_idx"].astype(str)
    cols = [outcome, "event_f", *controls]
    if day_fe:
        d["_fd"] = d["symbol"] + "|" + d["date"].astype(str)
        d = demean_two_way(d, cols, "_fe", "_fd")
    else:
        d = demean_within(d, cols, "_fe")
    X = d[["event_f", *controls]].to_numpy()
    y = d[outcome].to_numpy()
    fit = ols_cluster(y, X, d["date"])
    p_wild = wild_cluster_p(y, X, d["date"], 0, B, rng) if B else np.nan
    n_ev = int(d["event"].sum())
    n_days = int(d.loc[d["event"] == 1.0, "date"].nunique())
    return {"outcome": outcome, "beta": fit["beta"][0], "se": fit["se"][0], "t": fit["t"][0],
            "p_cr1": fit["p"][0], "p_wild": p_wild, "n_obs": fit["n"], "n_days": fit["n_clusters"],
            "n_events": n_ev, "n_event_days": n_days, "adequacy": adequacy(n_ev, n_days)}


def shuffle_volume_days(table: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Null device: re-pair whole days of VOLUME with other days' prices (same
    stock, same slots). Keeps each series' internal structure and breaks only
    the volume-return link."""
    m = table["market"].iloc[0]
    vol = table["volume"].where(table["volume_ok"])
    V, dates = to_matrix(table, vol, m)
    Vp = V[rng.permutation(len(dates))]
    out = table.copy()
    mins = out["mins_since_open"].to_numpy()
    slot = mins // 5
    on_grid = (mins % 5 == 0) & (slot >= 0) & (slot < WIDTH[m])
    day_pos = pd.Series(np.arange(len(dates)), index=dates)
    di = day_pos.loc[out["date"]].to_numpy()
    newv = np.full(len(out), np.nan)
    newv[on_grid] = Vp[di[on_grid], slot[on_grid]]
    out["volume"] = np.where(np.isnan(newv), out["volume"], newv)
    out["volume_ok"] = np.where(on_grid, ~np.isnan(newv), out["volume_ok"]).astype(bool)
    return out
