"""Build dashboard/index.html, a standalone copy of the published QuantLab H1 Results dashboard.

page.html is the page stored in the online dashboard; data/*.csv are the five aggregate files it reads. This script
embeds both, with d3 and a minimal stand-in for the dashboard runtime (dash.data, dash.calc, dash.draw), so the page
opens offline or from a local server. No raw market data is used: every CSV is an aggregate of saved project outputs.

Usage:  python dashboard/build_dashboard.py      then open dashboard/index.html
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATASETS = ["calibration_cells", "alt_processes", "real_tests", "simulation_ledger", "integrity_checks"]

THEME = """
:root{--color-fg:#1f1e1d;--color-fg-muted:#6b6a68;--color-bg:#f4f6fb;--color-panel:#ffffff;--color-border-line:#e3e6ee;
--color-ok:#2f7d4f;--color-warn:#b7791f;--color-bad:#c0392b;
--cds-chart-muted:#b9b6ae;--cds-chart-grid:#eceef3;--cds-chart-axis:#c9ccd4;--cds-chart-reference:#4b4d55;--cds-text-secondary:#5d5f66;
--cds-surface-popover:#ffffff;--cds-border:#dcdfe6;--cds-shadow-popover:0 6px 16px rgba(20,30,60,.12);
--c1:#d97757;--c2:#3b82c4;--c3:#7a6fd0;--c4:#2f9e8f}
@media (prefers-color-scheme:dark){:root{--color-fg:#ecebe8;--color-fg-muted:#a3a29e;--color-bg:#16181d;--color-panel:#20232a;--color-border-line:#30343d;
--color-ok:#5cbf85;--color-warn:#e0a84a;--color-bad:#e5685a;
--cds-chart-muted:#6e6c67;--cds-chart-grid:#2b2e36;--cds-chart-axis:#454953;--cds-chart-reference:#c9cbd2;--cds-text-secondary:#b1b3ba;
--cds-surface-popover:#2a2d35;--cds-border:#3a3e48;--cds-shadow-popover:0 6px 16px rgba(0,0,0,.4);--c1:#e58a6c;--c2:#6aa5e0}}
:root{--font-anthropic-sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;--font-anthropic-serif:Georgia,serif;
--cds-font-size-caption:12px;--cds-font-size-body:15px;--cds-font-size-heading:19px;--cds-font-size-title:28px;--cds-font-weight-medium:550;
--cds-gap-xs:4px;--cds-gap-sm:8px;--cds-gap-md:12px;--cds-gap-lg:16px;--cds-gap-xl:28px;
--cds-pad-xs:4px;--cds-pad-sm:8px;--cds-pad-md:12px;--cds-pad-lg:16px;--cds-pad-xl:24px;--cds-radius:10px}
body{margin:0;background:var(--color-bg);color:var(--color-fg);font-family:var(--font-anthropic-sans);font-size:15px;line-height:1.45}
#dash-root{padding:16px;max-width:1240px;margin:0 auto}
"""

RUNTIME = """
window.__errors = [];
window.addEventListener('error', (e) => window.__errors.push(String(e.message)));
(function () {
  const calcs = {}, draws = {};
  window.dash = {
    colors: ['var(--c1)', 'var(--c2)', 'var(--c3)', 'var(--c4)'],
    data(id) {
      if (window.__DATA__[id]) return { status: 'ok', data: window.__DATA__[id] };
      if (calcs[id]) { const c = calcs[id]; return { status: 'ok', data: c.fn(...c.inputs.map((i) => dash.data(i).data)) }; }
      return { status: 'missing', data: [] };
    },
    calc(id, spec) { calcs[id] = spec; },
    draw(name, fn) { draws[name] = fn; },
    setLink() {}, onData(fn) { fn(); }, params() { return {}; }, setParams() {}, resetParams() {}, refresh() {},
    __run() {
      for (const [n, fn] of Object.entries(draws))
        document.querySelectorAll('[data-draw="' + n + '"]').forEach((el) => { try { fn(el); } catch (e) { window.__errors.push(n + ': ' + e.message); } });
    }
  };
})();
"""


def load(name):
    with open(HERE / "data" / f"{name}.csv", newline="") as f:
        return [{k: (v if v != "" else None) for k, v in r.items()} for r in csv.DictReader(f)]


def main():
    page = (HERE / "page.html").read_text()
    data = {n: load(n) for n in DATASETS}
    html = (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>QuantLab H1 Results</title>\n"
        "<script src=\"https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js\"></script>\n"
        f"<style>{THEME}</style>\n"
        f"<script>window.__DATA__ = {json.dumps(data)};\n{RUNTIME}</script>\n"
        "</head><body><div id=\"dash-root\">\n" + page + "\n</div>\n"
        "<script>dash.__run(); let __rt; window.addEventListener('resize', () => { clearTimeout(__rt); __rt = setTimeout(() => dash.__run(), 120); });</script>\n"
        "</body></html>\n"
    )
    (HERE / "index.html").write_text(html)
    print(f"wrote {HERE / 'index.html'} ({len(html):,} bytes, {sum(len(v) for v in data.values())} rows)")


if __name__ == "__main__":
    main()
