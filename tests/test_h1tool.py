"""Tests for the QuantLab H1 tool (src/quantlab/h1tool.py). Synthetic bars only: no real market data."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "milestone4"))
from quantlab import h1tool                                              # noqa: E402
from quantlab.calendars import NSE, US                                    # noqa: E402
from quantlab.clean import clean                                          # noqa: E402
from quantlab.eda.masks import build_bar_table                            # noqa: E402
from quantlab.research import nulls                                       # noqa: E402
import real_h1_run as r1                                                  # noqa: E402

B = ROOT / "outputs" / "milestone4" / "h1_calibration"


def synthetic_csv(path, symbols, market, n_days, seed=1, naive=False, boost=0.0):
    """Write a CSV in the tool's input format from the project's synthetic generator."""
    frames = []
    for i, s in enumerate(symbols):
        raw = nulls.simulate_raw(market, n_days, np.random.default_rng(seed + i), vol_edge_boost=boost)
        idx = raw.index.tz_localize(None) if naive else raw.index
        frames.append(pd.DataFrame({"Symbol": s, "Timestamp": [t.isoformat() for t in idx], "open": raw["open"].to_numpy(), "high": raw["high"].to_numpy(),
                                    "low": raw["low"].to_numpy(), "close": raw["close"].to_numpy(), "volume": raw["volume"].to_numpy()}))
    pd.concat(frames).to_csv(path, index=False)
    return path


def test_embedded_critical_values_equal_the_frozen_files():
    t2 = pd.read_csv(B / "stage2" / "c3_training" / "c3_critical_values.csv").set_index("n_days")["c3_crit"].to_dict()
    ti = pd.read_csv(B / "stage3" / "c3_intermediate" / "c3_intermediate_values.csv").set_index("n_days")["c3_crit"].to_dict()
    assert h1tool.C3_CRIT == {**t2, **ti}


def test_tool_array_equals_the_projects_real_data_array(tmp_path):
    """The tool's cleaning and array building must give exactly what the frozen real-data runner builds from the same bars."""
    p = synthetic_csv(tmp_path / "us.csv", ["AAA", "BBB", "CCC"], US, 64)
    bars = h1tool.read_bars(p)
    tabs = {}
    for s, b in bars.items():
        ann, _ = clean(b, US, as_of=b.index.max().normalize() + pd.Timedelta(days=1))
        tabs[s] = build_bar_table(ann, US, s)
    a1, syms1, dates1 = h1tool._real_array(tabs, US)
    a2, syms2, dates2 = r1.real_array(tabs, US)
    assert syms1 == syms2 and dates1 == dates2
    assert np.array_equal(a1, a2, equal_nan=True)


def test_tested_result_and_report_us(tmp_path):
    p = synthetic_csv(tmp_path / "us.csv", ["AAA", "BBB", "CCC"], US, 64, boost=2.0)
    r = h1tool.analyse(h1tool.read_bars(p), 59)
    assert r["status"] == "TESTED" and r["market"] == "US" and r["crit_C3"] == h1tool.C3_CRIT[59]
    assert r["usable_market_sessions"] >= 59 and r["T"] > 0 and isinstance(r["reject"], bool)
    assert set(r["contrasts"]) == {"open_vs_middle", "close_vs_middle", "open_vs_close"}
    c = r["contrasts"]["open_vs_middle"]
    assert c["ratio_low_95"] < c["volatility_ratio"] < c["ratio_high_95"]
    assert c["volatility_ratio"] == pytest.approx(np.exp(c["log_ratio_of_mean_squares"] / 2))
    text = h1tool.format_report(r)
    assert "T =" in text and "limitations" in text and r["reading"] in text


def test_data_with_a_strong_open_close_effect_is_rejected(tmp_path):
    boosted = h1tool.analyse(h1tool.read_bars(synthetic_csv(tmp_path / "b.csv", ["A", "B", "C"], US, 64, boost=3.0)), 59)
    assert boosted["reject"] is True and boosted["contrasts"]["open_vs_middle"]["volatility_ratio"] > 1.3


def test_nse_symbols_are_detected_and_timestamps_without_offset_match_offsets(tmp_path):
    a = h1tool.analyse(h1tool.read_bars(synthetic_csv(tmp_path / "a.csv", ["X.NS", "Y.NS", "Z.NS"], NSE, 64, naive=False)), 59)
    b = h1tool.analyse(h1tool.read_bars(synthetic_csv(tmp_path / "b.csv", ["X.NS", "Y.NS", "Z.NS"], NSE, 64, naive=True)), 59)
    assert a["market"] == "NSE" and a["status"] == "TESTED"
    assert a["T"] == b["T"] and a["first_date"] == b["first_date"]


def test_not_testable_when_sessions_are_missing_and_never_shortened(tmp_path):
    r = h1tool.analyse(h1tool.read_bars(synthetic_csv(tmp_path / "s.csv", ["A", "B", "C"], US, 40)), 59)
    assert r["status"] == "NOT_TESTABLE" and "T" not in r and "never shortened" in r["reading"]


def test_only_the_first_sessions_are_used_when_more_exist(tmp_path):
    r = h1tool.analyse(h1tool.read_bars(synthetic_csv(tmp_path / "m.csv", ["A", "B", "C"], US, 75)), 59)
    assert r["status"] == "TESTED" and r["usable_market_sessions"] > 59 and any("FIRST 59" in w for w in r["warnings"])


@pytest.mark.parametrize("symbols,expect", [(["A", "B"], "exactly 3"), (["A", "B", "C", "D"], "exactly 3"), (["A", "B", "C.NS"], "more than one market")])
def test_unsupported_stock_sets_are_refused(tmp_path, symbols, expect):
    mk = NSE if symbols[0].endswith(".NS") else US
    p = tmp_path / "u.csv"
    frames = []
    for i, s in enumerate(symbols):
        m = NSE if s.endswith(".NS") else US
        raw = nulls.simulate_raw(m, 10, np.random.default_rng(i))
        frames.append(pd.DataFrame({"symbol": s, "timestamp": [t.isoformat() for t in raw.index], **{c: raw[c].to_numpy() for c in ("open", "high", "low", "close", "volume")}}))
    pd.concat(frames).to_csv(p, index=False)
    r = h1tool.analyse(h1tool.read_bars(p), 59)
    assert r["status"] == "NOT_SUPPORTED" and expect in r["reason"]


def test_session_count_without_a_frozen_critical_value_is_refused(tmp_path):
    r = h1tool.analyse(h1tool.read_bars(synthetic_csv(tmp_path / "s.csv", ["A", "B", "C"], US, 12)), 100)
    assert r["status"] == "NOT_SUPPORTED" and "frozen critical values" in r["reason"]


def test_bad_input_is_reported_clearly(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("symbol,timestamp,open\nA,2026-08-03T09:30:00-04:00,1\n")
    with pytest.raises(ValueError, match="missing column"):
        h1tool.read_bars(p)
    q = tmp_path / "mix.csv"
    q.write_text("symbol,timestamp,open,high,low,close,volume\nA,2026-08-03T09:30:00-04:00,1,1,1,1,1\nA,2026-08-03 09:35:00,1,1,1,1,1\n")
    with pytest.raises(ValueError, match="mix"):
        h1tool.read_bars(q)


def test_command_line_writes_json_and_returns_exit_codes(tmp_path, capsys):
    p = synthetic_csv(tmp_path / "us.csv", ["A", "B", "C"], US, 64)
    out = tmp_path / "r.json"
    assert h1tool.main([str(p), "--json", str(out)]) == 0
    saved = json.loads(out.read_text())
    assert saved["status"] == "TESTED" and "limitations" in saved
    assert "T =" in capsys.readouterr().out
    short = synthetic_csv(tmp_path / "short.csv", ["A", "B", "C"], US, 20)
    assert h1tool.main([str(short)]) == 2
    assert h1tool.main([str(tmp_path / "missing.csv")]) == 1
