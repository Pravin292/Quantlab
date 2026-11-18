"""Draw the Stage 6 charts (docs/43) as SVG files in docs/images/, from the saved Stage 6 result files only. Plain Python, no plotting library.

    python scripts/make_stage6_charts.py                      # reads outputs/milestone4/stage6, writes docs/images
    python scripts/make_stage6_charts.py --src DIR --out DIR  # (used by tests on tiny scratch results)
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import make_readme_charts as mc                                              # noqa: E402

LEVEL_NAME = {"S0_none": "S0  independent", "S1_validated": "S1  earlier estimate", "S2_fresh_point": "S2  US fresh (measured)", "S3_fresh_upper": "S3  US fresh, upper range",
              "S4_one_and_half_x": "S4  1.5 × measured", "S5_illustrative": "S5  illustrative stress"}
N_COLOR = {59: "#4f46e5", 90: "#0f9d8f", 125: "#d97706", 180: "#c2416b", 250: "#1f2328"}


def chart_size(src, out):
    data = mc.rows(src / "part_a" / "size_by_cell.csv")
    levels = list(LEVEL_NAME)
    s = mc.Svg(820, 120 + 62 * len(levels), "Stage 6A: C3 false-alarm rate under dependence (volatility truly equal)")
    x0, x1, top, hi, band = 250, 780, 70, 10.0, 62
    X = lambda v: x0 + v / hi * (x1 - x0)                                   # noqa: E731
    for gi, lv in enumerate(levels):
        cells = [r for r in data if r["level"] == lv]
        y0 = top + gi * band
        gated = cells[0]["gated"] in ("True", "true", "1")
        s.text(x0 - 12, y0 + band / 2 + 1, LEVEL_NAME[lv], 12, mc.INK, "end", 600)
        s.text(x0 - 12, y0 + band / 2 + 16, f"{len(cells)} cells · " + ("gated" if gated else "reported only"), 11, mc.MUTED, "end")
        for lim in (5.5, 6.0):
            s.line(X(lim), y0 + 4, X(lim), y0 + band - 6, mc.LIMIT, 1.5, "5 4")
        for i, r in enumerate(cells):
            jy = y0 + 12 + ((i * 37) % 17) / 16 * (band - 26)
            s.circle(X(100 * float(r["rate_base"])), jy, 3.5, mc.OLD)
            s.circle(X(100 * float(r["rate_c3"])), jy, 4, mc.C3)
    yb = top + len(levels) * band
    mc.xaxis(s, x0, x1, yb, 0, hi, [0, 2, 4, 6, 8, 10], lambda v: f"{v:g}%", top)
    s.legend(x0, yb + 44, [("C3 (the new test)", mc.C3, "dot"), ("Old bootstrap test", mc.OLD, "dot"), ("Limits 5.5% (tier A) and 6.0% (tier B)", mc.LIMIT, "dash")])
    s.save_to(out, "stage6_size.svg")


def chart_power(src, out):
    data = mc.rows(src / "part_b" / "power_by_cell.csv")
    s = mc.Svg(820, 660, "Stage 6B: power of C3 as open and close get more volatile than the middle")
    mults = sorted({float(r["mult"]) for r in data})
    ns = sorted({int(r["n_days"]) for r in data})
    panels = [(mk, lv) for mk in ("US", "NSE") for lv in ("S0_none", "S2_fresh_point")]
    pw, ph, gx, gy = 330, 190, 70, 90
    for pi, (mk, lv) in enumerate(panels):
        px, py = 60 + (pi % 2) * (pw + gx), gy + (pi // 2) * (ph + 80)
        s.text(px, py - 14, f"{mk} · " + ("independent stocks and days" if lv == "S0_none" else "dependence as measured in US fresh"), 12, mc.INK, weight=600)
        X = lambda m, px=px: px + mults.index(m) / (len(mults) - 1) * pw        # noqa: E731  (grid points evenly spaced)
        Y = lambda p, py=py: py + ph - p * ph                                # noqa: E731
        for t in (0, 0.25, 0.5, 0.75, 1.0):
            s.line(px, Y(t), px + pw, Y(t), mc.GRID)
            s.text(px - 8, Y(t) + 4, f"{t:.0%}", 10, mc.MUTED, "end")
        s.line(px, Y(0.8), px + pw, Y(0.8), mc.LIMIT, 1.5, "5 4")
        for m in mults:
            s.text(X(m), py + ph + 16, f"{m:g}×", 10, mc.MUTED, "middle")
        for n in ns:
            pts = sorted((float(r["mult"]), float(r["power"])) for r in data if r["market"] == mk and r["level"] == lv and int(r["n_days"]) == n)
            s.polyline([(X(m), Y(p)) for m, p in pts], N_COLOR[n])
    s.legend(60, 620, [(f"{n} sessions", N_COLOR[n], "dot") for n in ns] + [("80% power", mc.LIMIT, "dash")])
    s.text(60, 644, "x-axis: open and close volatility as a multiple of the middle's (grid points evenly spaced). Each point: 10,000 simulations.", 11, mc.MUTED)
    s.save_to(out, "stage6_power.svg")


def chart_placebo(src, out):
    data = [r for r in mc.rows(src / "part_c" / "placebo_results.csv") if r["status"] == "PLACEBO_DONE"]
    s = mc.Svg(820, 150 + 44 * len(data), "Stage 6C: real-data placebo (time-of-day labels shuffled, truth = equal)")
    x0, x1, top = 250, 780, 80
    hi = max(10.0, 2 * (int(max(100 * float(r["wilson_high"]) for r in data) / 2) + 2))
    X = lambda v: x0 + v / hi * (x1 - x0)                                   # noqa: E731
    y = top
    for r in data:
        s.text(x0 - 12, y + 6, r["sample"].replace("_", " "), 12, mc.INK, "end")
        lo, hi_, rate = 100 * float(r["wilson_low"]), 100 * float(r["wilson_high"]), 100 * float(r["rate"])
        s.line(X(lo), y, X(hi_), y, mc.C3, 2)
        s.circle(X(rate), y, 5, mc.C3)
        s.text(X(hi_) + 8, y + 4, f"{rate:.2f}%", 11, mc.MUTED)
        y += 44
    mc.xaxis(s, x0, x1, y - 10, 0, hi, list(range(0, int(hi) + 1, 2)), lambda v: f"{v:g}%", top - 20)
    for lim in (5.5, 7.0):
        s.line(X(lim), top - 20, X(lim), y - 10, mc.LIMIT, 1.5, "5 4")
    s.text(X(5.5) - 4, top - 26, "5.5%", 11, mc.INK, "end", 600)
    s.text(X(7.0) + 4, top - 26, "7.0% ceiling", 11, mc.INK, "start", 600)
    s.text(x0, y + 24, "Dot = placebo rejection rate over 10,000 shuffles of the same 59 sessions; line = Wilson 95% interval.", 11, mc.MUTED)
    s.save_to(out, "stage6_placebo.svg")


# small extensions of the shared drawing class (kept here so make_readme_charts.py stays unchanged)
def _polyline(self, pts, color, width=2):
    self.parts.append('<polyline fill="none" stroke="%s" stroke-width="%s" points="%s"/>' % (color, width, " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)))


def _save_to(self, out, name):
    out.mkdir(parents=True, exist_ok=True)
    (out / name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" role="img">' + "".join(self.parts) + "</svg>\n")


mc.Svg.polyline, mc.Svg.save_to = _polyline, _save_to


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(ROOT / "outputs" / "milestone4" / "stage6"))
    ap.add_argument("--out", default=str(ROOT / "docs" / "images"))
    a = ap.parse_args()
    src, out = Path(a.src), Path(a.out)
    for f in (chart_size, chart_power, chart_placebo):
        f(src, out)
    print("wrote", sorted(p.name for p in out.glob("stage6_*.svg")))
