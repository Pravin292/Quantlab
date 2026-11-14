"""Draw the README charts as SVG files in docs/images/, from saved aggregate results only (no market data, no new analysis).

Inputs: dashboard/datasets/*.csv (copies of saved project outputs) and outputs/milestone4/phase6/phase6_measurements.csv.
Plain Python, no plotting library. Usage: python scripts/make_readme_charts.py
"""
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DS = ROOT / "dashboard" / "datasets"
OUT = ROOT / "docs" / "images"
FONT = "font-family:-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
INK, MUTED, GRID, AXIS = "#1f2328", "#59636e", "#e6e8eb", "#9198a1"
C3, OLD, LIMIT = "#4f46e5", "#a8acb3", "#1f2328"
SAMPLE = {"US · first Yahoo sample": "#4f46e5", "US · fresh Alpaca pull": "#d97706", "NSE · fresh Yahoo pull": "#0f9d8f"}


def rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.parts = w, h, []
        self.parts.append(f'<rect width="{w}" height="{h}" fill="#ffffff" rx="12"/>')
        self.text(24, 34, title, size=17, weight=650)

    def text(self, x, y, s, size=12, color=INK, anchor="start", weight=400):
        self.parts.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}" text-anchor="{anchor}" '
                          f'font-weight="{weight}" style="{FONT}">{esc(s)}</text>')

    def line(self, x1, y1, x2, y2, color=AXIS, width=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{width}"{d}/>')

    def rect(self, x, y, w, h, color, rx=4):
        self.parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{h:.1f}" rx="{rx}" fill="{color}"/>')

    def circle(self, x, y, r, color, stroke="#ffffff"):
        self.parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" stroke="{stroke}" stroke-width="1"/>')

    def legend(self, x, y, items):
        for label, color, kind in items:
            if kind == "dash":
                self.line(x, y - 4, x + 18, y - 4, color, 2, "5 4")
            else:
                self.rect(x, y - 10, 12, 12, color, 6)
            self.text(x + 24, y, label, 12, MUTED)
            x += 24 + 7.2 * len(label) + 22

    def save(self, name):
        OUT.mkdir(parents=True, exist_ok=True)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" '
               f'role="img">' + "".join(self.parts) + "</svg>\n")
        (OUT / name).write_text(svg)


def xaxis(svg, x0, x1, y, lo, hi, ticks, fmt, top):
    for t in ticks:
        x = x0 + (t - lo) / (hi - lo) * (x1 - x0)
        svg.line(x, top, x, y, GRID)
        svg.text(x, y + 18, fmt(t), 11, MUTED, "middle")
    svg.line(x0, y, x1, y, AXIS)


def chart_real_data():
    data = rows(DS / "real_tests.csv")
    s = Svg(820, 300, "Real data: test statistic T against the C3 limit (higher than the line = reject)")
    x0, x1, top = 230, 760, 64
    hi = 25.0
    X = lambda v: x0 + v / hi * (x1 - x0)                                   # noqa: E731
    crit = float(data[0]["crit"])
    y = top
    for r in data:
        s.text(x0 - 12, y + 19, r["test"], 13, INK, "end")
        if r["status"] == "TESTED":
            t = float(r["T"])
            s.rect(X(0), y + 4, X(t) - X(0), 22, SAMPLE.get(r["test"], C3), 5)
            s.text(X(t) + 8, y + 20, f"{t:.2f}  reject", 12, INK, weight=600)
        else:
            s.text(X(crit) + 10, y + 20, f"not testable: {r['usable_market_sessions']} of {r['n_required']} complete days", 12, MUTED)
        y += 44
    xaxis(s, x0, x1, y + 6, 0, hi, [0, 5, 10, 15, 20, 25], lambda v: f"{v:g}", top - 4)
    s.line(X(crit), top - 6, X(crit), y + 6, LIMIT, 2, "6 4")
    s.text(X(crit) + 6, top - 10, f"C3 limit {crit:.2f}", 12, INK, weight=600)
    s.save("real_data_T.svg")


def chart_volatility_ratios():
    data = [r for r in rows(DS / "real_tests.csv") if r["status"] == "TESTED"]
    s = Svg(820, 400, "How much more volatile? Volatility ratio between periods (1.0 = equal)")
    contrasts = [("open_middle", "Open vs middle"), ("close_middle", "Close vs middle"), ("open_close", "Open vs close")]
    x0, x1, top = 170, 780, 70
    lo, hi = 0.6, 2.4
    X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)                     # noqa: E731
    y = top
    for key, name in contrasts:
        s.text(x0 - 14, y + 30, name, 13, INK, "end", 600)
        for r in data:
            th, se = float(r[f"log_ratio_{key}"]), float(r[f"se_{key}"])
            v, a, b = math.exp(th / 2), math.exp((th - 2 * se) / 2), math.exp((th + 2 * se) / 2)
            col = SAMPLE[r["test"]]
            s.line(X(a), y + 12, X(b), y + 12, col, 2)
            s.circle(X(v), y + 12, 5, col)
            s.text(X(b) + 8, y + 16, f"{v:.2f}×", 11, MUTED)
            y += 18
        y += 26
    xaxis(s, x0, x1, y, lo, hi, [0.6, 1.0, 1.4, 1.8, 2.2], lambda v: f"{v:.1f}×", top - 4)
    s.line(X(1.0), top - 6, X(1.0), y, LIMIT, 1.5, "6 4")
    s.legend(x0, y + 44, [(k, c, "dot") for k, c in SAMPLE.items()])
    s.text(x0, y + 64, "Dot = estimate; line = ± 2 standard errors. Ratio of RMS volatility = exp(log ratio of mean squares / 2).", 11, MUTED)
    s.save("volatility_ratios.svg")


def chart_calibration():
    data = rows(DS / "calibration_cells.csv")
    s = Svg(820, 330, "Simulation check: false-alarm rate in each of the 96 validation cells (C3 vs the old test)")
    x0, x1, top = 190, 780, 70
    hi = 12.0
    X = lambda v: x0 + v / hi * (x1 - x0)                                   # noqa: E731
    groups = [("A", "Tier A (limit 5.5%)"), ("B", "Tier B (limit 6.0%)"), ("C", "Report-only (no limit)")]
    band = 62
    for gi, (key, name) in enumerate(groups):
        cells = [r for r in data if r["tier"] == key]
        y0 = top + gi * band
        s.text(x0 - 12, y0 + band / 2 + 4, f"{name} · {len(cells)}", 12, INK, "end")
        lim = cells[0]["gate_limit_pct"]
        if lim:
            s.line(X(float(lim)), y0 + 4, X(float(lim)), y0 + band - 6, LIMIT, 2, "5 4")
        for i, r in enumerate(cells):
            jy = y0 + 12 + ((i * 37) % 17) / 16 * (band - 26)
            s.circle(X(float(r["baseline_rate_pct"])), jy, 3.5, OLD)
            s.circle(X(float(r["c3_rate_pct"])), jy, 4, C3)
    yb = top + 3 * band
    xaxis(s, x0, x1, yb, 0, hi, [0, 2, 4, 6, 8, 10, 12], lambda v: f"{v:g}%", top)
    s.legend(x0, yb + 44, [("C3 (the new test)", C3, "dot"), ("Old bootstrap test", OLD, "dot"), ("Limit for the tier", LIMIT, "dash")])
    s.save("calibration_cells.svg")


def chart_alt_processes():
    data = rows(DS / "alt_processes.csv")
    s = Svg(820, 120 + 30 * len(data), "Harder simulated worlds: false-alarm rate under six alternative processes")
    x0, x1, top = 290, 780, 64
    hi = 10.0
    X = lambda v: x0 + v / hi * (x1 - x0)                                   # noqa: E731
    y = top
    for r in data:
        s.text(x0 - 12, y + 17, f"{r['process']} · {r['market']}", 12, INK, "end")
        s.rect(X(0), y + 4, X(float(r["c3_rate_pct"])) - X(0), 10, C3, 3)
        s.rect(X(0), y + 16, X(float(r["baseline_rate_pct"])) - X(0), 10, OLD, 3)
        y += 30
    xaxis(s, x0, x1, y + 4, 0, hi, [0, 2, 4, 6, 8, 10], lambda v: f"{v:g}%", top - 4)
    lim = float(data[0]["gate_limit_pct"])
    s.line(X(lim), top - 6, X(lim), y + 4, LIMIT, 2, "5 4")
    s.text(X(lim) + 6, top - 10, f"limit {lim:g}%", 12, INK, weight=600)
    s.legend(x0, y + 44, [("C3", C3, "dot"), ("Old bootstrap test", OLD, "dot")])
    s.save("alt_processes.svg")


def chart_simulations():
    data = rows(DS / "simulation_ledger.csv")
    total = sum(int(r["simulations"]) for r in data)
    s = Svg(820, 110 + 30 * len(data), f"Where the {total:,} simulations went")
    x0, x1, top = 290, 700, 60
    hi = max(int(r["simulations"]) for r in data)
    stage_col = {"1": "#4f46e5", "2": "#0f9d8f", "3": "#d97706", "4": "#c2416b"}
    y = top
    for r in data:
        n = int(r["simulations"])
        st = r["stage"].split()[1]
        s.text(x0 - 12, y + 16, r["stage"], 12, INK, "end")
        s.rect(x0, y + 4, max(2, n / hi * (x1 - x0)), 16, stage_col.get(st, C3), 4)
        s.text(x0 + max(2, n / hi * (x1 - x0)) + 8, y + 17, f"{n:,}", 12, MUTED)
        y += 30
    s.legend(x0, y + 24, [(f"Stage {k}", c, "dot") for k, c in stage_col.items()])
    s.save("simulations_by_stage.svg")


def chart_phase6():
    m = rows(ROOT / "outputs" / "milestone4" / "phase6" / "phase6_measurements.csv")
    get = {(r["sample"], r["measure"]): r for r in m if r["variant"] == "baseline"}
    comps = [("M11_phi", "Volatility persistence φ", 0.190), ("M12_s", "Shared volatility s", 0.141), ("M12_rho", "Return correlation ρ", 0.187)]
    samples = [("us_first", "US · first Yahoo sample"), ("us_fresh", "US · fresh Alpaca pull")]
    s = Svg(820, 330, "Phase 6: US dependence measured vs the level used in the simulations")
    x0, x1, top = 220, 780, 70
    lo, hi = -0.1, 0.7
    X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)                     # noqa: E731
    y = top
    for key, name, sim in comps:
        s.text(x0 - 14, y + 26, name, 13, INK, "end", 600)
        s.line(X(sim), y, X(sim), y + 46, LIMIT, 2, "5 4")
        s.line(X(1.5 * sim), y, X(1.5 * sim), y + 46, "#c0392b", 2, "2 3")
        yy = y + 12
        for sid, lab in samples:
            r = get[(sid, key)]
            th, a, b = float(r["theta"]), float(r["lo"]), float(r["hi"])
            col = SAMPLE[lab]
            s.line(X(a), yy, X(b), yy, col, 2)
            s.circle(X(th), yy, 5, col)
            s.text(X(b) + 8, yy + 4, f"{th:.2f}", 11, MUTED)
            yy += 20
        y += 66
    xaxis(s, x0, x1, y, lo, hi, [-0.1, 0.1, 0.3, 0.5, 0.7], lambda v: f"{v:.1f}", top - 6)
    s.legend(x0, y + 44, [("US first", SAMPLE["US · first Yahoo sample"], "dot"), ("US fresh", SAMPLE["US · fresh Alpaca pull"], "dot"),
                          ("simulated level", LIMIT, "dash"), ("1.5× = outside", "#c0392b", "dash")])
    s.save("phase6_dependence.svg")


if __name__ == "__main__":
    for f in (chart_real_data, chart_volatility_ratios, chart_calibration, chart_alt_processes, chart_simulations, chart_phase6):
        f()
    print("wrote", sorted(p.name for p in OUT.glob("*.svg")))
