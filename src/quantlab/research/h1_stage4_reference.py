"""H1 calibration, STAGE 4: INDEPENDENT SLOW REFERENCE IMPLEMENTATION of the H1 statistic and of the C3 critical-value derivation. Pure Python, exact arithmetic.
Written from the DOCUMENTED definitions (docs/15 section A.0 for the statistic, docs/06 section 3 for the clock-time period definitions), NOT from the vectorised code:
it imports nothing from h1_calibration, h1_rms, h1_rms2, direct_sim or numpy-based helpers. Inputs are plain nested lists of squared returns [stock][day][slot].
  * period slots: derived from the session clock times and the half-open period intervals (the opening candle has no return and is excluded);
  * period means: exact rationals (fractions.Fraction) of the float inputs;
  * T = max over the contrasts (open, middle), (close, middle), (open, close) of |ln(Xbar_a/Xbar_b) / se|, se = sqrt(s^2(u)/n), u_d = X_da/Xbar_a - X_db/Xbar_b,
    s^2 the sample variance with divisor n-1; logarithm and square root in 60-digit decimal arithmetic;
  * C3 critical value: the 0.95 quantile (linear interpolation between order statistics, position (n-1)p) computed exactly on the sorted float values.
"""
from __future__ import annotations

from decimal import Decimal, getcontext
from fractions import Fraction

getcontext().prec = 60

SESSIONS = {"NSE": {"start": "09:15", "bars": 75, "periods": {"open": ("09:15", "09:55"), "middle": ("10:00", "14:25"), "close": ("14:30", "15:10")}},
            "US": {"start": "09:30", "bars": 78, "periods": {"open": ("09:30", "10:25"), "middle": ("10:30", "14:55"), "close": ("15:00", "15:55")}}}
CONTRASTS = [(0, 1), (2, 1), (0, 2)]            # (open, middle), (close, middle), (open, close)


def _minutes(hhmm: str) -> int:
    """Minutes after midnight of an HH:MM string."""
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def period_slots(market: str) -> list[list[int]]:
    """Slot numbers (0-based, 5-minute bars) used for each period, from the documented clock-time intervals; the opening candle (slot 0) is excluded."""
    spec = SESSIONS[market]
    t0 = _minutes(spec["start"])
    out = []
    for name in ("open", "middle", "close"):
        lo, hi = (_minutes(x) for x in spec["periods"][name])
        out.append([j for j in range(1, spec["bars"]) if lo <= t0 + 5 * j <= hi])
    return out


def market_matrix(r2, market: str) -> list[list[Fraction]]:
    """X[d][p] = (1/S) sum_s (1/|K_p|) sum_{j in K_p} r2[s][d][j], exactly (Fractions)."""
    slots = period_slots(market)
    n_stocks, n_days = len(r2), len(r2[0])
    X = []
    for d in range(n_days):
        row = []
        for ks in slots:
            tot = Fraction(0)
            for s in range(n_stocks):
                tot += sum((Fraction(r2[s][d][j]) for j in ks), Fraction(0)) / len(ks)
            row.append(tot / n_stocks)
        X.append(row)
    return X


def _ln(x: Fraction) -> Decimal:
    """Natural logarithm of a positive Fraction in 60-digit decimal arithmetic."""
    return (Decimal(x.numerator) / Decimal(x.denominator)).ln()


def statistic_T(X: list[list[Fraction]], ddof: int = 1) -> float:
    """T = max_c |theta_c / se_c| from the day matrix X (n x 3); `ddof` is exposed only so a test can show the check is sensitive to it."""
    n = len(X)
    best = Decimal(0)
    for a, b in CONTRASTS:
        xa = sum((row[a] for row in X), Fraction(0)) / n
        xb = sum((row[b] for row in X), Fraction(0)) / n
        theta = _ln(xa / xb)
        u = [row[a] / xa - row[b] / xb for row in X]
        mu = sum(u, Fraction(0)) / n
        var = sum(((v - mu) ** 2 for v in u), Fraction(0)) / (n - ddof)
        se = (Decimal(var.numerator) / Decimal(var.denominator) / Decimal(n)).sqrt()
        t = abs(theta / se)
        if t > best:
            best = t
    return float(best)


def quantile_linear(values, p: float) -> float:
    """p-quantile by linear interpolation at position (n-1)p of the sorted values, computed exactly on the float inputs."""
    v = sorted(values)
    n = len(v)
    h = (n - 1) * Fraction(p)
    lo = int(h)                                              # floor, h >= 0
    frac = h - lo
    if lo + 1 >= n:
        return float(v[-1])
    return float(Fraction(v[lo]) + frac * (Fraction(v[lo + 1]) - Fraction(v[lo])))


def c3_value(training_T_by_cell: list[list[float]], p: float = 0.95) -> float:
    """C3 critical value for one sample size: the maximum over the training cells of the p-quantile of T (no margin)."""
    return max(quantile_linear(t, p) for t in training_T_by_cell)
