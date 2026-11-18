# 45: The QuantLab H1 tool: run the C3 test on your own 5-minute bars

The tool takes 5-minute price bars for **three stocks of one market** and answers the project's question: *is volatility the same in the open, the middle and the close?* It applies the frozen C3 test exactly as the project did on its real samples. As a check, fed with the project's own cleaned bars it reproduces the three recorded real-data results to 9 decimal places (T = 22.594, 17.305, 17.748).

## 1. Install and run
```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install .                      # installs the quantlab-h1 command
quantlab-h1 examples/synthetic_demo.csv
```
Without installing, from the repository root: `python -m quantlab.h1tool examples/synthetic_demo.csv` (the project's virtual environment must be active). The demo file contains **synthetic** bars of three made-up stocks, not real market data.

## 2. Your input file
A CSV with these columns (any order, any capitalisation):

| Column | Meaning |
|---|---|
| `symbol` | stock name. A name ending in `.NS` is an NSE stock (09:15 to 15:30 India time); anything else is a US stock (09:30 to 16:00 New York time) |
| `timestamp` | the bar's **start** time, either with a UTC offset (`2026-08-06T09:30:00-04:00`) or as local exchange time without an offset. Do not mix the two styles |
| `open`, `high`, `low`, `close` | prices of the 5-minute bar |
| `volume` | shares traded in the bar |

Exactly **three** stocks, all from **one** market, are required: that is what C3 was calibrated for.

## 3. Options
| Option | Meaning |
|---|---|
| `--sessions N` | how many complete trading days to use: 59 (default), 90, 125, 180 or 250. These are the sizes with frozen C3 critical values |
| `--json FILE` | also save the full result for other programs to read |

## 4. What you get back
```
status: TESTED
market: US   stocks: AAPL, MSFT, NVDA
T = 22.5944   C3 limit = 3.2987   decision: REJECT
volatility ratios (RMS return, 95% interval):
  open vs middle     2.07x  [1.95, 2.21]
  close vs middle    0.99x  [0.91, 1.08]
  open vs close      2.09x  [1.93, 2.27]
```
- **T** is the test statistic; **C3 limit** is the frozen cut-off for that many sessions. T above the limit means *reject*: volatility is not equal.
- **Volatility ratios** show how much bigger the typical 5-minute move is in one period than another, with a 95% interval.
- **Data-quality counts** (in the JSON) list how many bars of each stock were used or set aside, and why.

## 5. Status values and exit codes
| Status | Exit code | Meaning |
|---|---|---|
| `TESTED` | 0 | the test ran, whether or not it rejected |
| `NOT_TESTABLE` | 2 | fewer complete sessions than requested. **The sample is never shortened to fit**, so no statistic is computed |
| `NOT_SUPPORTED` | 2 | outside what C3 was checked for: not exactly three stocks, more than one market, or a session count without a frozen value |
| (error message) | 1 | the file could not be read (missing column, mixed timestamp styles, ...) |

## 6. Limits you should know
- C3 was validated on **simulated** markets; its verdict is PARTIAL (safe and cautious there, not proven exact, not proven on real data). See [docs/24](24_h1_calibration_stage5_decision_report.md) and the Stage 6 results in [docs/43](43_stage6_report.md).
- A rejection means volatility differs between at least two periods. It does not say which period or why, and it is not a trading signal.
- A "not rejected" result is weak evidence of equality: C3 is cautious.
- If more complete sessions exist than requested, only the **first** ones in date order are used (the project's frozen rule).
- Markets other than NSE and US, or stocks that moved together far more strongly than the simulated range, are outside the evidence.
