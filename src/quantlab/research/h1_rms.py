"""H1 CANDIDATE methods that keep the RMS-volatility estimand.   (M4a methodology research, not frozen)

Estimand: for each period p, the per-bar variance  v_p = E[r^2 | period p]  (its square root is
the RMS volatility). H1 asks whether v_open, v_middle, v_close differ. Every method below targets
this quantity; none subsamples bars or changes it.

Why the original Friedman-on-ln(RMS) failed: ln(mean r^2) is a biased estimate of ln v, with bias
about -(kappa-1)/(2n) for n bars and kurtosis kappa. n differs by period (8/54/9 bars), so the bias
differs by period and looks like a volatility difference. Two ways out are implemented:
  (1) CORRECT the bias of each day-period level, then rank-test (lnrms_jk, lnrms_an);
  (2) work with mean squares (linear in r^2, no logarithm per day) and do paired day-level
      inference on their market average (rom_* and diff_t), where the log is taken only once, on
      the average over ~59 days x 3 stocks, so the bias is tiny.

Day-level inference: the unit is the trading day. Inputs to the bootstrap tests are day x period
matrices of mean squares (averaged over stocks); days are resampled with replacement.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from ..eda.masks import MAIN_PERIODS
from .h1_volatility import EXPECTED_RETURNS, MIN_COVERAGE
from .inference import resample_days

CONTRAST_IDX = [(0, 1), (2, 1), (0, 2)]            # open/middle, close/middle, open/close
ALPHA = 0.05


def period_returns(table: pd.DataFrame, market_name: str, min_coverage: float = MIN_COVERAGE) -> dict:
    """{(date, period): array of close-to-close returns} for day-periods with enough coverage."""
    ok = table[(table["status"] == "ok") & table["period"].isin(MAIN_PERIODS)]
    expected = EXPECTED_RETURNS[market_name]
    out = {}
    for (date, period), g in ok.groupby(["date", "period"]):
        vals = g["ret"].to_numpy()
        if len(vals) / expected[period] >= min_coverage:
            out[(date, period)] = vals
    return out


def _to_panel(cells: dict) -> pd.DataFrame:
    if not cells:
        return pd.DataFrame(columns=MAIN_PERIODS, dtype=float)
    long = pd.DataFrame([(d, p, v) for (d, p), v in cells.items()], columns=["date", "period", "v"])
    return long.pivot(index="date", columns="period", values="v").reindex(columns=MAIN_PERIODS)


def mean_square_panel(table: pd.DataFrame, market_name: str, min_coverage: float = MIN_COVERAGE) -> pd.DataFrame:
    """days x [open, middle, close] of the mean of r^2 (NaN if coverage too low)."""
    cells = period_returns(table, market_name, min_coverage)
    return _to_panel({k: float(np.mean(v ** 2)) for k, v in cells.items()})


def pooled_kurtosis(table: pd.DataFrame, market_name: str) -> float:
    """kappa = E z^4 / (E z^2)^2 for returns divided by their own day's RMS (removes the day factor)."""
    cells = period_returns(table, market_name)
    by_day: dict = {}
    for (d, _), v in cells.items():
        by_day.setdefault(d, []).append(v)
    z = []
    for vs in by_day.values():
        r = np.concatenate(vs)
        z.append(r / np.sqrt(np.mean(r ** 2)))
    z = np.concatenate(z)
    return float(np.mean(z ** 4) / np.mean(z ** 2) ** 2)


def jackknife_ln_rms(x: np.ndarray) -> float:
    """Bar-level jackknife bias-corrected ln RMS:  n*theta - (n-1)*mean(theta_{-i})."""
    n = len(x)
    s2 = x ** 2
    ms = s2.mean()
    loo = (s2.sum() - s2) / (n - 1)
    if ms <= 0 or (loo <= 0).any():
        return float("nan")
    theta = 0.5 * np.log(ms)
    return float(n * theta - (n - 1) * np.mean(0.5 * np.log(loo)))


def corrected_level_panel(table: pd.DataFrame, market_name: str, how: str, kappa: float | None = None) -> pd.DataFrame:
    """days x periods of bias-corrected ln RMS. how = 'jackknife' | 'analytic'.
    analytic: 0.5*[ln ms + (kappa-1)/(2n)], kappa pooled over the stock's own returns (see pooled_kurtosis)."""
    cells = period_returns(table, market_name)
    if how == "jackknife":
        return _to_panel({k: jackknife_ln_rms(v) for k, v in cells.items()})
    if how == "analytic":
        kap = pooled_kurtosis(table, market_name) if kappa is None else kappa
        return _to_panel({k: 0.5 * (np.log(np.mean(v ** 2)) + (kap - 1) / (2 * len(v))) for k, v in cells.items()})
    raise ValueError(how)


def market_matrix(panels: list[pd.DataFrame]) -> np.ndarray:
    """Complete days x 3 matrix: average over stocks (days where any stock lacks a value are dropped)."""
    dates = sorted(set().union(*[set(p.index) for p in panels]))
    stack = np.stack([p.reindex(dates).to_numpy() for p in panels])
    m = stack.mean(axis=0)
    return m[~np.isnan(m).any(axis=1)]


# ------------------------------------------------------------------ tests on a days x 3 matrix of mean squares
def _log_ratio(means: np.ndarray, a: int, b: int):
    return np.log(means[..., a] / means[..., b])


def _influence_se(X: np.ndarray, a: int, b: int) -> np.ndarray:
    """Delta-method SE of ln(mean_a/mean_b) over days; X can be (n,3) or (B,n,3)."""
    n = X.shape[-2]
    ma, mb = X[..., a].mean(axis=-1, keepdims=True), X[..., b].mean(axis=-1, keepdims=True)
    u = X[..., a] / ma - X[..., b] / mb
    return u.std(axis=-1, ddof=1) / np.sqrt(n)


def rms_ratio_test(M: np.ndarray, rng: np.random.Generator, method: str, B: int = 499, alpha: float = ALPHA) -> dict:
    """Day-bootstrap test that the three period variances are equal.
    Reject if ANY of the three pairwise log-variance-ratio intervals (level 1 - alpha/3, Bonferroni)
    excludes 0.  method:
      pct   percentile interval of ln(mean_a/mean_b)
      t     bootstrap-t (studentised) interval, delta-method SE inside each resample
      bca   bias-corrected and accelerated percentile interval
      diff  bootstrap-t test of the LINEAR contrast E[ms_a - ms_b] = 0 (no logarithm in the test)
    Returns reject flag and the three point estimates of ln(v_a/v_b)."""
    n = len(M)
    idx = resample_days(n, B, rng)
    Xb = M[idx]                                            # B x n x 3
    mb = Xb.mean(axis=1)                                   # B x 3
    est_means = M.mean(axis=0)
    a_tail = alpha / 6
    rejects, ests = [], []
    for a, b in CONTRAST_IDX:
        theta = float(_log_ratio(est_means, a, b))
        ests.append(theta)
        if method == "pct":
            lo, hi = np.quantile(_log_ratio(mb, a, b), [a_tail, 1 - a_tail])
            rejects.append(lo > 0 or hi < 0)
        elif method == "t":
            se = float(_influence_se(M, a, b))
            tstar = (_log_ratio(mb, a, b) - theta) / _influence_se(Xb, a, b)
            crit = np.quantile(np.abs(tstar), 1 - alpha / 3)
            rejects.append(abs(theta / se) > crit)
        elif method == "bca":
            tb = _log_ratio(mb, a, b)
            z0 = stats.norm.ppf(np.clip(np.mean(tb < theta), 1 / (B + 1), B / (B + 1)))
            loo = np.array([_log_ratio(np.delete(M, i, axis=0).mean(axis=0), a, b) for i in range(n)])
            d = loo.mean() - loo
            acc = (d ** 3).sum() / (6 * ((d ** 2).sum() ** 1.5) + 1e-300)
            qs = []
            for za in (stats.norm.ppf(a_tail), stats.norm.ppf(1 - a_tail)):
                qs.append(stats.norm.cdf(z0 + (z0 + za) / (1 - acc * (z0 + za))))
            lo, hi = np.quantile(tb, qs)
            rejects.append(lo > 0 or hi < 0)
        elif method == "diff":
            D = M[:, a] - M[:, b]
            t = D.mean() / (D.std(ddof=1) / np.sqrt(n))
            Db = Xb[..., a] - Xb[..., b]
            tstar = (Db.mean(axis=1) - D.mean()) / (Db.std(axis=1, ddof=1) / np.sqrt(n))
            rejects.append(abs(t) > np.quantile(np.abs(tstar), 1 - alpha / 3))
        else:
            raise ValueError(method)
    return {"reject": bool(any(rejects)), "open_mid": ests[0], "close_mid": ests[1]}


def friedman_on_levels(panels: list[pd.DataFrame]) -> dict:
    """Friedman test on the market average of per-day levels (used for the bias-corrected ln RMS variants)."""
    M = market_matrix(panels)
    chi2, p = stats.friedmanchisquare(M[:, 0], M[:, 1], M[:, 2])
    return {"p": float(p), "open_mid": float((M[:, 0] - M[:, 1]).mean()), "close_mid": float((M[:, 2] - M[:, 1]).mean())}
