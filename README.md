# QuantLab

An intraday quantitative **research** platform for NSE and US equities on 5-minute OHLCV bars.
Universe: `RELIANCE.NS`, `TCS.NS`, `INFY.NS`, `AAPL`, `MSFT`, `NVDA`.

QuantLab is a research tool. It makes **no profitability claims** and contains no trading strategy or backtest.

## Research questions

| ID | Question | State |
|---|---|---|
| H1 | Does volatility differ across the open, middle and close of the session? | Under investigation: the test's calibration is being studied on simulated data (see below). No real-market H1 test has been run. |
| H2 | Does volume carry predictive information? (predictive, not causal) | Diagnostic and power work done on simulated data. No real-market test has been run. |
| H3 | Serial dependence | Paused. |

## Standing rules

No fabricated data or results · beginner-readable explanations · modular, tested code · no look-ahead or leakage · documented assumptions · work milestone by milestone with approval before each next step · results from simulation are never described as market relationships.

## Status

| Milestone | Content | Status |
|---|---|---|
| M1 | Data availability and research spec | complete |
| M2 | Ingestion, validation and cleaning pipeline | complete |
| M3 | Exploratory data analysis | complete |
| M4a / M4b | H1 and H2 diagnostics and power, on simulated data | complete (diagnostic, not a frozen protocol) |
| H1 calibration investigation | Stage 0 (preparation) and Stage 1 (baseline mechanism diagnosis) complete. Stage 2: plan approved, C3 training table frozen; the main development run is awaiting approval. | in progress |
| M5, H3 | not started | – |

Start with [docs/README.md](docs/README.md) for a guided index of all documents.

## Repository layout

```
src/quantlab/          core pipeline: calendars, ingest, parse, validate, clean, eda/
src/quantlab/research/ research code: simulators, H1/H2/H3 methods, calibration candidates
scripts/milestone1-4/  command-line runners, one folder per milestone
tests/                 unit tests (synthetic data only)
docs/                  reports, specs, plans and review records (numbered in reading order)
outputs/               generated results; frozen specifications live in outputs/milestone4/h1_calibration/
data/                  NOT in the repository (see "Data" below)
```

## Setup

Requires Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
```

The test suite runs on synthetic data only and does not need the market data.

## Data

Market data comes from Yahoo Finance, an unofficial source whose terms do not allow redistribution
([docs/03_data_sources_and_licensing.md](docs/03_data_sources_and_licensing.md)). **It is not included in this repository** (`data/` is git-ignored),
and neither are the milestone 3 charts that embed bar-level data (`outputs/milestone3/`).
To rebuild them locally, one manual, limited pull at a time:

```bash
python scripts/milestone2/run_pipeline.py pull-test --confirm   # raw snapshot into data/raw (never overwritten)
python scripts/milestone2/run_pipeline.py process <raw file>    # parse, validate, clean -> data/clean
python scripts/milestone3/run_eda.py                            # EDA -> outputs/milestone3
```

Yahoo history is limited to about 60 days of 5-minute bars and is revised between pulls (docs 04), so a new pull will not reproduce the original sample byte for byte.

## H1 calibration investigation

Plan, decisions and results are in docs 13 to 17b. Everything runs on **simulated** data.

- Frozen specifications and manifests: `outputs/milestone4/h1_calibration/frozen_spec/` (v1) and `frozen_spec_v1_1/` (v1.1). Verify from the repository root:
  ```bash
  shasum -a 256 -c outputs/milestone4/h1_calibration/frozen_spec/FROZEN_v1.sha256        # 23 files
  shasum -a 256 -c outputs/milestone4/h1_calibration/frozen_spec_v1_1/FROZEN_v1_1.sha256 # 7 files
  shasum -a 256 -c outputs/milestone4/h1_calibration/stage1/STAGE1_CODE.sha256           # 8 files
  shasum -a 256 -c outputs/milestone4/h1_calibration/frozen_stage2_inputs.sha256         # 18 files
  ```
  Because the manifests hash raw file bytes, **never move or rename files** referenced by them.
- Stage 1 (baseline only): `python scripts/milestone4/stage1_run_baseline.py`, then `stage1_summarise.py`. Report: [docs/16](docs/16_h1_calibration_stage1_report.md).
- Stage 2: design in [docs/17](docs/17_h1_calibration_stage2_plan.md) and [docs/17b](docs/17b_h1_calibration_stage2_review_record.md); runners in `scripts/milestone4/stage2_*.py`.

## Known limitations

- Simulation results describe the simulated family only. They do not establish validity on real market data.
- The corrected C2 procedure ("FDB-like", v1.1) is **unverified** against the original paper and is report-only.
- Yahoo data is for personal research use; do not treat it as a basis for long-term or commercial work.
- No official exchange holiday or early-close calendar is used yet (see `src/quantlab/calendars.py`).
- No licence has been chosen for this repository.
