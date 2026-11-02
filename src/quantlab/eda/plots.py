"""Plotly chart builders for the EDA. Every function returns a Figure; saving
is done by the runner script.

Design choices (from the project's data-viz guidance)
* One y-axis per panel -- no dual axes. Different measures get separate panels.
* Colours come from a palette validated for colour-blind separation (blue,
  orange, aqua = slots 1-3). Inside one chart a stock keeps the same colour
  in every panel. NSE and US are compared as markets (blue = NSE, orange = US).
* The aqua slot is lighter than 3:1 on a light background, so every chart has
  a legend and hover values, and every number is also written to a CSV.
* The NSE 15:15-15:25 window is shaded grey and labelled as unreliable data.
"""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

from ..calendars import BAR_MINUTES, Market
from .masks import CLOSING_WINDOW, MAIN_PERIODS, PERIODS

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]          # validated slots 1-3
MARKET_COLOR = {"NSE": SERIES[0], "US": SERIES[1]}
SHADE = "rgba(120,120,120,0.18)"


def _base(fig: go.Figure, title: str, height: int = 450, note: str | None = None) -> go.Figure:
    """Shared look. Title and legend sit in fixed pixel rows above the plots;
    an optional note goes under the chart (so long text never collides)."""
    fig.update_layout(
        title=dict(text=title, x=0.01, y=1 - 12 / height, yref="container", yanchor="top",
                   font=dict(size=16, color=INK)),
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, height=height,
        font=dict(family="Helvetica, Arial, sans-serif", size=12, color=INK2),
        legend=dict(orientation="h", x=0, y=1 - 52 / height, yref="container", yanchor="top"),
        hovermode="x unified", margin=dict(l=60, r=20, t=125, b=110 if note else 60))
    if note:
        fig.add_annotation(text=note, xref="paper", yref="paper", x=0, y=0, yshift=-75,
                           showarrow=False, xanchor="left", yanchor="top", font=dict(size=11, color=INK2))
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    return fig


def _color_map(symbols) -> dict:
    return {s: SERIES[i % 3] for i, s in enumerate(symbols)}


def _ticks(market: Market, step: int = 30):
    n = (market.close_minutes - market.open_minutes)
    vals = list(range(0, n + 1, step))
    text = [f"{(market.open_minutes + v) // 60:02d}:{(market.open_minutes + v) % 60:02d}"
            for v in vals]
    return vals, text


def _decorate_session(fig, market: Market, row=None, col=None, periods=True):
    """x-axis in session-relative minutes, period boundaries, closing-window shade."""
    kw = dict(row=row, col=col) if row else {}
    vals, text = _ticks(market)
    fig.update_xaxes(tickvals=vals, ticktext=text, title_text="Bar start (exchange local time)", **kw)
    half = BAR_MINUTES / 2
    if periods:
        for name, start, end in PERIODS[market.name]:
            if name == CLOSING_WINDOW:
                fig.add_vrect(x0=start - market.open_minutes - half,
                              x1=end - market.open_minutes - half, fillcolor=SHADE,
                              line_width=0, layer="below", **kw)
                fig.add_annotation(x=(start + end) / 2 - market.open_minutes - half, y=1.0,
                                   yref="y domain" if not row else f"y{'' if row == 1 else row} domain",
                                   text="15:15-15:25<br>unreliable<br>(excluded)", showarrow=False,
                                   font=dict(size=10, color=INK2), yanchor="top",
                                   **({"xref": "x" if not row else f"x{'' if row == 1 else row}"}))
            elif start != market.open_minutes:
                fig.add_vline(x=start - market.open_minutes - half, line_width=1,
                              line_dash="dot", line_color=INK2, **kw)


def returns_histogram(ok, symbols_by_market: dict) -> go.Figure:
    """5-minute log returns (bps) per stock with a normal curve of the same mean/sd."""
    syms = [(m, s) for m, ss in symbols_by_market.items() for s in ss]
    fig = make_subplots(rows=2, cols=3, subplot_titles=[s for _, s in syms],
                        horizontal_spacing=0.06, vertical_spacing=0.18)
    for i, (m, s) in enumerate(syms):
        r, c = i // 3 + 1, i % 3 + 1
        x = ok.loc[ok.symbol == s, "ret"].dropna() * 1e4
        lo, hi = x.quantile(0.001), x.quantile(0.999)      # axis range only; no data removed
        fig.add_trace(go.Histogram(x=x, histnorm="probability density", nbinsx=80,
                                   marker=dict(color=SERIES[c - 1]), opacity=0.85,
                                   name="Observed", showlegend=(i == 0)), row=r, col=c)
        g = np.linspace(lo, hi, 200)
        fig.add_trace(go.Scatter(x=g, y=stats.norm.pdf(g, x.mean(), x.std(ddof=1)),
                                 mode="lines", line=dict(color=INK, width=1.5, dash="dash"),
                                 name="Normal, same mean/sd", showlegend=(i == 0)), row=r, col=c)
        fig.update_xaxes(range=[lo, hi], row=r, col=c, title_text="5-min log return (bps)")
    fig.update_layout(hovermode="closest")
    return _base(fig, "5-minute return distributions vs a normal curve", 680,
                 note="Top row NSE, bottom row US. The axis range hides the most extreme 0.1% tails of each "
                      "panel; no data was removed.")


def qq_plot(ok_z, symbols_by_market: dict) -> go.Figure:
    """Standardised returns against normal quantiles (points off the line = fat tails)."""
    syms = [(m, s) for m, ss in symbols_by_market.items() for s in ss]
    fig = make_subplots(rows=2, cols=3, subplot_titles=[s for _, s in syms],
                        horizontal_spacing=0.06, vertical_spacing=0.18)
    for i, (m, s) in enumerate(syms):
        r, c = i // 3 + 1, i % 3 + 1
        z = np.sort(ok_z.loc[ok_z.symbol == s, "z"].dropna().to_numpy())
        q = stats.norm.ppf((np.arange(1, len(z) + 1) - 0.5) / len(z))
        step = max(len(z) // 1500, 1)            # thin for plotting, but always keep the extremes
        keep = np.unique(np.r_[np.arange(0, len(z), step), np.arange(len(z) - 15, len(z)), np.arange(0, 15)])
        fig.add_trace(go.Scatter(x=q[keep], y=z[keep], mode="markers",
                                 marker=dict(size=4, color=SERIES[c - 1]),
                                 name="Standardised returns", showlegend=(i == 0)), row=r, col=c)
        lim = float(max(abs(q).max(), abs(z).max()))
        fig.add_trace(go.Scatter(x=[-lim, lim], y=[-lim, lim], mode="lines",
                                 line=dict(color=INK, width=1, dash="dash"),
                                 name="If normal", showlegend=(i == 0)), row=r, col=c)
        fig.update_xaxes(title_text="Normal quantile", row=r, col=c)
        fig.update_yaxes(title_text="Standardised return (z)", row=r, col=c)
    fig.update_layout(hovermode="closest")
    return _base(fig, "Q-Q plot of standardised returns", 680,
                 note="Points above/below the dashed line at the ends = fatter tails than a normal curve. "
                      "Middle of the data is thinned for plotting; the 15 most extreme points at each end are always shown.")


def mean_return_by_slot(mean_tbl, market: Market, symbols) -> go.Figure:
    fig = make_subplots(rows=len(symbols), cols=1, shared_xaxes=True, vertical_spacing=0.07,
                        subplot_titles=list(symbols))
    cmap = _color_map(symbols)
    for i, s in enumerate(symbols, start=1):
        d = mean_tbl[mean_tbl.symbol == s]
        x = d["mins_since_open"]
        fig.add_trace(go.Scatter(x=x, y=d["ci_high"] * 1e4, mode="lines", line=dict(width=0),
                                 showlegend=False, hoverinfo="skip"), row=i, col=1)
        fig.add_trace(go.Scatter(x=x, y=d["ci_low"] * 1e4, mode="lines", line=dict(width=0),
                                 fill="tonexty", fillcolor=cmap[s].replace("#", "#") + "33",
                                 name="95% CI (t)", showlegend=(i == 1), hoverinfo="skip"), row=i, col=1)
        fig.add_trace(go.Scatter(x=x, y=d["mean"] * 1e4, mode="lines+markers",
                                 line=dict(color=cmap[s], width=1.5), marker=dict(size=4),
                                 name=s, customdata=np.c_[d["slot"], d["n"]],
                                 hovertemplate="%{customdata[0]}  mean %{y:.2f} bps (n=%{customdata[1]})"
                                 "<extra>" + s + "</extra>"), row=i, col=1)
        fig.add_hline(y=0, line_width=1, line_color=INK2, row=i, col=1)
        fig.update_yaxes(title_text="Mean (bps)", row=i, col=1)
        _decorate_session(fig, market, row=i, col=1)
        if i < len(symbols):
            fig.update_xaxes(title_text="", row=i, col=1)
    return _base(fig, f"{market.name}: mean 5-minute return by time of day", 250 * len(symbols) + 180,
                 note="Shaded band = 95% Student-t confidence interval. Close-to-close returns; the opening "
                      "candle is analysed separately. Many slots are shown, so a few bands will miss 0 by chance.")


def volatility_by_slot(vol_tbl, market: Market, symbols) -> go.Figure:
    fig = go.Figure()
    cmap = _color_map(symbols)
    for s in symbols:
        d = vol_tbl[vol_tbl.symbol == s]
        fig.add_trace(go.Scatter(x=d["mins_since_open"], y=d["std_bps"], mode="lines+markers",
                                 line=dict(color=cmap[s], width=1.5), marker=dict(size=4), name=s,
                                 customdata=np.c_[d["slot"], d["n"]],
                                 hovertemplate="%{customdata[0]}: %{y:.1f} bps (n=%{customdata[1]})"
                                 "<extra>" + s + "</extra>"))
    fig.update_yaxes(title_text="Std of 5-min log return (bps)", rangemode="tozero")
    _decorate_session(fig, market)
    for name, start, end in PERIODS[market.name]:
        if name in MAIN_PERIODS:
            fig.add_annotation(x=(start + end) / 2 - market.open_minutes - BAR_MINUTES / 2, y=1.0,
                               yref="paper", text=name, showarrow=False, yanchor="bottom",
                               font=dict(size=11, color=INK2))
    return _base(fig, f"{market.name}: volatility by time of day", 500,
                 note="Dotted lines mark the period boundaries (open / middle / close).")


def volume_profile(vp_tbl, market: Market, symbols) -> go.Figure:
    fig = go.Figure()
    cmap = _color_map(symbols)
    for s in symbols:
        d = vp_tbl[vp_tbl.symbol == s]
        fig.add_trace(go.Scatter(x=d["mins_since_open"], y=d["relative_volume"], mode="lines+markers",
                                 line=dict(color=cmap[s], width=1.5), marker=dict(size=4), name=s,
                                 customdata=np.c_[d["slot"], d["n"], d["median_volume"]],
                                 hovertemplate="%{customdata[0]}: %{y:.2f}x typical (median %{customdata[2]:,.0f} "
                                 "shares, n=%{customdata[1]})<extra>" + s + "</extra>"))
    fig.update_yaxes(title_text="Median volume relative to typical slot (1.0 = typical)",
                     rangemode="tozero")
    _decorate_session(fig, market)
    if market.name == "NSE":
        fig.add_annotation(x=0, y=1.0, yref="y domain", text="09:15 volume excluded<br>(reliability unproven)",
                           showarrow=False, xanchor="left", yanchor="top", font=dict(size=10, color=INK2))
    return _base(fig, f"{market.name}: volume through the session", 500,
                 note="Reliable bars only: zero-volume, unusable and NSE 09:15 / 15:15-15:25 bars are excluded.")


def market_comparison(vol_rel, vp_rel) -> go.Figure:
    """Both markets on the same minutes-since-open axis. Two panels (not dual axis)."""
    fig = make_subplots(rows=1, cols=2, subplot_titles=[
        "Volatility relative to each stock's typical slot", "Volume relative to each stock's typical slot"],
        horizontal_spacing=0.08)
    for col, d in enumerate([vol_rel, vp_rel], start=1):
        for m in ["NSE", "US"]:
            g = d[d.market == m]
            fig.add_trace(go.Scatter(x=g["mins_since_open"], y=g["value"], mode="lines+markers",
                                     line=dict(color=MARKET_COLOR[m], width=1.5), marker=dict(size=4),
                                     name=f"{m} (mean of 3 stocks)", showlegend=(col == 1),
                                     hovertemplate="%{x} min after open: %{y:.2f}<extra>" + m + "</extra>"),
                          row=1, col=col)
        fig.add_vrect(x0=357.5, x1=372.5, fillcolor=SHADE, line_width=0, layer="below", row=1, col=col)
        fig.add_annotation(x=365, y=1, yref="y domain" if col == 1 else "y2 domain", text="NSE 15:15-15:25<br>unreliable",
                           showarrow=False, yanchor="top", font=dict(size=10, color=INK2),
                           xref="x" if col == 1 else "x2")
        fig.update_xaxes(title_text="Minutes after the open", row=1, col=col)
        fig.update_yaxes(rangemode="tozero", row=1, col=col)
    fig.update_layout(hovermode="closest")
    return _base(fig, "NSE vs US: intraday shape on a session-relative axis", 520,
                 note="1.0 = that stock's typical slot; lines are the mean of the 3 stocks in each market. "
                      "Shapes only: absolute levels are not comparable across markets.")


def quality_heatmap(table, symbols, category_series, market: Market) -> go.Figure:
    """Slot x day grid of data-quality categories for each stock."""
    cats = ["ok", "zero_or_missing_volume", "empty_bar", "other_excluded",
            "nse_0915_volume_excluded", "nse_closing_window_usable_but_excluded"]
    colors = ["#e6e5e1", "#eda100", "#2a78d6", "#6250d6", "#eb6834", "#1baf7a"]
    fig = make_subplots(rows=len(symbols), cols=1, shared_xaxes=True, vertical_spacing=0.07,
                        subplot_titles=list(symbols))
    t = table.assign(category=category_series)
    for i, s in enumerate(symbols, start=1):
        d = t[t.symbol == s]
        piv = d.pivot_table(index="date", columns="mins_since_open", values="category",
                            aggfunc="first")
        z = piv.apply(lambda col: col.map({c: k for k, c in enumerate(cats)}))
        colorscale = []
        for k, c in enumerate(colors):
            colorscale += [[k / len(cats), c], [(k + 1) / len(cats), c]]
        fig.add_trace(go.Heatmap(
            x=z.columns, y=[str(x) for x in z.index], z=z.to_numpy(), zmin=0, zmax=len(cats),
            colorscale=colorscale, showscale=False,
            customdata=np.array([[cats[int(v)] if v == v else "no bar" for v in row]
                                 for row in z.to_numpy()]),
            hovertemplate="day %{y}<br>%{x} min after open<br>%{customdata}<extra></extra>"),
            row=i, col=1)
        fig.update_yaxes(autorange="reversed", row=i, col=1)
    for k, (c, col) in enumerate(zip(cats, colors)):          # legend via dummy traces
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=c.replace("_", " "),
                                 marker=dict(size=10, color=col, symbol="square")))
    vals, text = _ticks(market)
    fig.update_xaxes(tickvals=vals, ticktext=text, title_text="Bar start (exchange local time)",
                     row=len(symbols), col=1)
    fig.update_layout(hovermode="closest")
    return _base(fig, f"{market.name}: data-quality map", 280 * len(symbols) + 180,
                 note="Each cell = one 5-minute bar on one day. Grey = fully usable.")

