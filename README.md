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
| H1 calibration investigation | Stage 0, Stage 1 (baseline diagnosis), Stage 2 (candidate development) and Stage 3 (locked validation of the sole candidate C3: 2,280,000 simulations, outcome PASS_CLEAR on its upper-limit gates) **Stage 4 (independent validation: all five preregistered criteria met)** and **Stage 5 (decision report: classification PARTIAL)** are complete. Real-data checks, the research protocol and everything after are **not started and need explicit approval**. | in progress |
| M5, H3 | not started | – |

Start with [docs/README.md](docs/README.md) for a guided index of all documents, and [docs/19](docs/19_quantlab_project_status_report.md) for the consolidated project status, findings, limitations and blockers.

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
  shasum -a 256 -c outputs/milestone4/h1_calibration/frozen_stage2_inputs_addendum.sha256 # 2 files
  shasum -a 256 -c outputs/milestone4/h1_calibration/stage2/c3_training/C3_TABLE.sha256   # 2 files
  shasum -a 256 -c outputs/milestone4/h1_calibration/frozen_stage3_inputs.sha256          # 12 files
  shasum -a 256 -c outputs/milestone4/h1_calibration/stage3/c3_intermediate/C3_INTERMEDIATE_TABLE.sha256   # 2 files
  shasum -a 256 -c outputs/milestone4/h1_calibration/frozen_stage4_inputs.sha256          # 21 files
  ```
  Because the manifests hash raw file bytes, **never move or rename files** referenced by them.
- Stage 1 (baseline only): `python scripts/milestone4/stage1_run_baseline.py`, then `stage1_summarise.py`. Report: [docs/16](docs/16_h1_calibration_stage1_report.md).
- Stage 2: design in [docs/17](docs/17_h1_calibration_stage2_plan.md), [docs/17b](docs/17b_h1_calibration_stage2_review_record.md) and [docs/17c](docs/17c_h1_calibration_stage2_d2_confirmation.md); results and all failures, violations and borderline flags in [docs/18](docs/18_h1_calibration_stage2_report.md); runners in `scripts/milestone4/stage2_*.py`. Neither candidate met every advancement criterion; the project owner designated C3 as the sole candidate for Stage 3.
- Stage 3: pre-run record [docs/20](docs/20_h1_calibration_stage3_prerun_record.md) (fill-ins, frozen before the run) and report [docs/21](docs/21_h1_calibration_stage3_report.md). C3 stayed within its upper limits in all 88 gated validation cells, including the 20 new ones. This does **not** show the rate is held near 5% (C3 is very conservative) and says nothing outside the simulated family. Runners: `scripts/milestone4/stage3_*.py`.
- Stage 4: preregistration [docs/22](docs/22_h1_calibration_stage4_preregistration.md), approvals [docs/22b](docs/22b_h1_calibration_stage4_approval_record.md), report [docs/23](docs/23_h1_calibration_stage4_report.md). On six alternative simulated processes (jumps, volatility clustering, period- and stock-specific tails, heavy-tailed day factor, Laplace shocks) C3 rejected at most 4.41% (limit 6.0%); the bar-level pipeline and an independent exact-arithmetic implementation agreed with the fast route and the main code. This is still simulated evidence: it does **not** show validity on real data or that C3's rate is near 5%. Runners: `scripts/milestone4/stage4_*.py`.
- Stage 5: decision report [docs/24](docs/24_h1_calibration_stage5_decision_report.md), documentation only. Classification **PARTIAL**: C3 stayed within its upper rejection-rate limits throughout the validated *simulated* domain (it is conservative, not near 5%); calibration on real market data is unverified. The report defines the domain, audits counts and seeds, and documents the gate-wording discrepancy between docs/13 and the v1.1 rule.
- Phase 6 (documentation only, **proposed and not approved; no real data accessed**): real-data descriptive validation protocol [docs/26](docs/26_real_data_descriptive_validation_protocol.md), decision register [docs/27](docs/27_quantlab_formal_decision_and_approval_register.md) (D1–D17 pending), Stage 0 Mode B layout check [docs/28](docs/28_stage0_mode_b_reference_layout_verification.md) and decision memo [docs/29](docs/29_stage0_d_tail_compatibility_decision_memo.md). Real-data work needs separate explicit authorisation.
- Real-data H1 test (existing Yahoo sample, frozen C3, one run): plan [docs/30](docs/30_real_data_h1_test_preregistration_plan.md), report [docs/31](docs/31_real_data_h1_test_report.md). US: reject (T = 22.59 against 3.30, driven by the open); NSE not testable (58 complete sessions). Same sample that informed the simulation design, so not independent confirmation; C3's size on real data remains unverified.

## Known limitations

- Simulation results describe the simulated family only. They do not establish validity on real market data.
- The corrected C2 procedure ("FDB-like", v1.1) is **unverified** against the original paper and is report-only.
- Yahoo data is for personal research use; do not treat it as a basis for long-term or commercial work.
- No official exchange holiday or early-close calendar is used yet (see `src/quantlab/calendars.py`).
- No licence has been chosen for this repository.
