"""H1: does per-bar volatility differ between the opening, middle and closing periods?

Unit of analysis: one number per DAY and period (never one per candle).

    sigma_{d,p} = sqrt( mean over m randomly chosen valid returns of r^2 )
    y_{d,p}     = ln sigma_{d,p}, averaged over repeated random draws of the m bars

Returns are uncentred (their means are about zero) and averaged per bar. Every
period is measured on the same number m of bars (see period_panel for why).
A day-period counts only if at least MIN_COVERAGE of its expected returns exist.

Primary test per market: Friedman test on the 3 paired values per day.
Post-hoc: Wilcoxon signed-rank on the three paired contrasts.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from ..eda.masks import MAIN_PERIODS
from .inference import percentile_ci, resample_days

MIN_COVERAGE = 0.90
# Number of close-to-close returns expected in each period. The opening candle
# has no previous bar, so the open period has one return fewer than bars.
EXPECTED_RETURNS = {"NSE": {"open": 8, "middle": 54, "close": 9},
                    "US": {"open": 11, "middle": 54, "close": 12}}
CONTRASTS = [("open", "middle"), ("close", "middle"), ("open", "close")]


SEED = 20261030
SUBSAMPLE_DRAWS = 25


def _level(vals: np.ndarray, measure: str) -> float:
    """ln of per-bar volatility from a set of returns."""
    if measure == "rms":
        return 0.5 * np.log(np.mean(vals ** 2))
    if measure == "abs":
        return float(np.log(np.mean(np.abs(vals)) * np.sqrt(np.pi / 2)))
    raise ValueError(measure)


def period_panel(table: pd.DataFrame, market_name: str, min_coverage: float = MIN_COVERAGE,
                 measure: str = "rms", subsample: bool = True, draws: int = SUBSAMPLE_DRAWS,
                 seed: int = SEED) -> pd.DataFrame:
    """days x [open, middle, close] of ln(per-bar volatility); NaN if coverage is too low.

    WHY SUBSAMPLE: ln(volatility) estimated from 8 bars is biased differently from
    one estimated from 54 bars, especially for fat-tailed returns, so periods with
    different bar counts would differ even if their true volatility were equal
    (found in the M4a calibration: 80-90% false positives). With subsample=True
    every day-period is measured on the SAME number m of randomly chosen bars
    (m = floor(0.9 * smallest expected count): 7 NSE, 9 US), repeated `draws`
    times and averaged. The random choice is seeded by (seed, date, period), so
    the result is reproducible. subsample=False (all bars) is an exploratory sensitivity."""
    ok = table[(table["status"] == "ok") & table["period"].isin(MAIN_PERIODS)]
    expected = EXPECTED_RETURNS[market_name]
    m_eq = int(np.floor(min_coverage * min(expected.values())))
    rows = []
    for (date, period), g in ok.groupby(["date", "period"]):
        vals = g["ret"].to_numpy()
        if len(vals) / expected[period] < min_coverage:
            continue
        if subsample:
            if len(vals) < m_eq:
                continue
            rng = np.random.default_rng([seed, date.toordinal(), MAIN_PERIODS.index(period)])
            lvl = np.mean([_level(vals[rng.choice(len(vals), m_eq, replace=False)], measure)
                           for _ in range(draws)])
        else:
            lvl = _level(vals, measure)
        rows.append((date, period, lvl))
    if not rows:
        return pd.DataFrame(columns=MAIN_PERIODS, dtype=float)
    long = pd.DataFrame(rows, columns=["date", "period", "level"])
    return long.pivot(index="date", columns="period", values="level").reindex(columns=MAIN_PERIODS)


def market_panel(panels: list[pd.DataFrame]) -> pd.DataFrame:
    """Mean of ln-volatility over stocks; NaN unless every stock has the value."""
    dates = sorted(set().union(*[set(p.index) for p in panels]))
    stack = np.stack([p.reindex(dates).to_numpy() for p in panels])
    return pd.DataFrame(stack.mean(axis=0), index=dates, columns=MAIN_PERIODS)


def kendalls_w(chi2: float, n_days: int, n_periods: int = 3) -> float:
    """Kendall's W effect size from the Friedman statistic (0 = no agreement, 1 = perfect)."""
    return chi2 / (n_days * (n_periods - 1))


def omnibus(panel: pd.DataFrame) -> dict:
    """Friedman test across the three periods, using complete days only."""
    d = panel.dropna()
    chi2, p = stats.friedmanchisquare(*[d[c] for c in MAIN_PERIODS])
    return {"n_days": len(d), "chi2": chi2, "p": p, "kendalls_w": kendalls_w(chi2, len(d))}


def pairwise(panel: pd.DataFrame, rng: np.random.Generator, B: int = 2000,
             block: int = 1) -> pd.DataFrame:
    """Wilcoxon signed-rank on each contrast, with median log-ratio and a
    day-block bootstrap percentile interval. p-values are RAW; the caller
    applies Holm within the market's post-hoc family."""
    d = panel.dropna()
    rows = []
    idx = resample_days(len(d), B, rng, block)
    for a, b in CONTRASTS:
        diff = (d[a] - d[b]).to_numpy()
        w = stats.wilcoxon(diff)
        boot = np.median(diff[idx], axis=1)
        lo, hi = percentile_ci(boot)
        rows.append({"contrast": f"{a}-{b}", "n_days": len(d), "median_log_ratio": np.median(diff),
                     "ratio": float(np.exp(np.median(diff))), "ci_low_ratio": float(np.exp(lo)),
                     "ci_high_ratio": float(np.exp(hi)), "wilcoxon_p": w.pvalue})
    return pd.DataFrame(rows)


def difference_autocorrelation(panel: pd.DataFrame, lags: int = 5) -> pd.DataFrame:
    """Ljung-Box on each paired difference series (checks that days are not
    serially dependent, which would call for block bootstrapping)."""
    from statsmodels.stats.diagnostic import acorr_ljungbox
    d = panel.dropna()
    rows = []
    for a, b in CONTRASTS:
        lb = acorr_ljungbox((d[a] - d[b]).to_numpy(), lags=[lags])
        rows.append({"contrast": f"{a}-{b}", "lags": lags,
                     "lb_stat": float(lb["lb_stat"].iloc[0]), "lb_p": float(lb["lb_pvalue"].iloc[0])})
    return pd.DataFrame(rows)
