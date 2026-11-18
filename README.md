# QuantLab

**A research project that asks one question carefully: is a stock's volatility the same at the open, the middle and the close of the trading day?**

It works on 5-minute price bars for three Indian (NSE) and three US stocks. Most of the effort went into **building a test you can trust** on short, fat-tailed samples, checking that test on millions of simulated markets, and only then running it on real data, once per sample, with every rule fixed in advance.

> QuantLab is a research tool. It makes **no profitability claims** and contains no trading strategy or backtest.

| | |
|---|---|
| **Stocks** | NSE: `RELIANCE.NS`, `TCS.NS`, `INFY.NS` · US: `AAPL`, `MSFT`, `NVDA` |
| **Data** | 5-minute OHLCV bars from Yahoo Finance and the Alpaca Market Data API (free tiers) |
| **Simulations run** | **11,624,000**: 8,024,000 in the H1 calibration (Stages 1–4) + 3,600,000 in the Stage 6 stress test and power curve |
| **Answer** | In all **3 of 3** testable real samples, volatility is **not** equal: the open is about **2× as volatile** as the middle of the day |
| **Test verdict** | The new test (C3) is **PARTIAL**: safe in every simulated scenario with a pass limit, but not proven exactly right on real data |
| **Stress test (Stage 6)** | **STRESS_PASS**: with stocks and days as dependent as the fresh US sample (and its upper uncertainty range), C3's highest false-alarm rate was **4.84%** over 64 scored cells (limits 5.5% and 6.0%). It detects an open/close difference of 1.10× to 1.24× with 80% power, and a real-data placebo gave 0.73% to 1.30% false alarms |
| **Tests and integrity** | 438 automated tests pass · 14 hash manifests freeze every input · checks run automatically on GitHub · ₹0 spent |
| **Reusable tool** | `quantlab-h1 bars.csv` runs the frozen C3 test on your own 5-minute bars ([guide](docs/45_h1_tool_guide.md)); it reproduces the three real-data results exactly |
| **Live dashboard** | [QuantLab H1 Results](https://claude.ai/artifact/JyiVESsrnCvSjoXpwpdARw) (offline copy: [`dashboard/index.html`](dashboard/index.html)) |

---

## Contents
1. [The question in plain words](#1-the-question-in-plain-words)
2. [Results at a glance](#2-results-at-a-glance)
3. [The whole project in one flowchart](#3-the-whole-project-in-one-flowchart)
4. [Every phase: what it did and why it matters](#4-every-phase-what-it-did-and-why-it-matters)
5. [How the H1 test works](#5-how-the-h1-test-works)
6. [More charts](#6-more-charts)
7. [Data sources](#7-data-sources)
8. [Trust and reproducibility](#8-trust-and-reproducibility)
9. [What the results do not show](#9-what-the-results-do-not-show)
10. [Run it yourself](#10-run-it-yourself)
11. [Repository map and document index](#11-repository-map-and-document-index)
12. [Tech stack](#12-tech-stack)
13. [Glossary](#13-glossary)

---

## 1. The question in plain words

Traders often say markets are "busiest" at the open and the close. QuantLab splits each trading day into three periods (**open**, **middle**, **close**) and asks whether the size of 5-minute price moves is the same in all three. This is called **H1**.

Asking is easy; answering honestly is hard:

- **Short samples.** Free data gives only about 59 trading days of 5-minute bars.
- **Fat tails.** Big surprise moves happen far more often than a bell curve predicts.
- **Uneven shapes.** Volatility changes bar by bar *inside* each period.

Under these conditions the standard bootstrap test said "different!" too often (7–9% of the time instead of 5%). So before touching real data, the project **built and validated a better test** (C3) on simulated markets where the true answer is known.

| Research question | State |
|---|---|
| **H1** volatility across open, middle and close | **Answered for the approved scope**: real data rejects equal volatility in 3 of 3 testable samples |
| H2 does volume carry predictive information (not causal) | Diagnostic and power work on simulated data only; no real-market test |
| H3 serial dependence | Paused |

---

## 2. Results at a glance

### Real data: every testable sample rejects "equal volatility"

![Real data: test statistic T for each sample against the C3 limit](docs/images/real_data_T.svg)

The test statistic **T** is far above the C3 limit (3.30) in all three testable samples, so equal volatility is rejected. One NSE sample had only 58 of the required 59 complete days, so it was reported as **not testable** instead of being quietly shortened.

| Sample | Source | Days used | T | Result |
|---|---|---|---|---|
| US, first sample | Yahoo | 2026-08-06 to 2026-10-28 | 22.59 | Reject |
| US, fresh sample | Alpaca (SIP feed) | 2026-04-13 to 2026-07-07 | 17.75 | Reject |
| NSE, fresh sample | Yahoo | 2026-08-18 to 2026-11-13 | 17.31 | Reject |
| NSE, first sample | Yahoo | — | — | Not testable (58 of 59 days) |

### How big is the difference?

![Volatility ratio between periods for each sample](docs/images/volatility_ratios.svg)

In every sample the **open is about 1.9–2.2× as volatile as the middle** of the day. The close is closer to the middle: about equal in the first US sample, and moderately higher in the others. This is a well-known market pattern, so the result **confirms** it rather than discovers it. What is new is that the test behind it has been checked carefully.

---

## 3. The whole project in one flowchart

```mermaid
flowchart TD
    subgraph S1["1 · Data foundation"]
        M1["M1 · Data availability<br/>and research spec"] --> M2["M2 · Pipeline<br/>ingest, validate, clean"]
        M2 --> M3["M3 · Exploratory analysis<br/>(descriptive only)"]
    end
    subgraph S2["2 · Diagnose the problem (simulated data)"]
        M4["M4a / M4b · H1 and H2 diagnostics<br/>standard test over-rejects<br/>with fat tails"]
    end
    subgraph S3["3 · Build and validate a better test (simulated data)"]
        ST0["Stage 0 · Preparation<br/>frozen specification"] --> ST1["Stage 1 · Baseline diagnosis<br/>1,240,000 simulations"]
        ST1 --> ST2["Stage 2 · Develop candidates<br/>C3 chosen"]
        ST2 --> ST3["Stage 3 · Locked validation<br/>88 / 88 cells pass"]
        ST3 --> ST4["Stage 4 · Independent checks<br/>6 harder worlds, all pass"]
        ST4 --> ST5["Stage 5 · Decision<br/>verdict PARTIAL"]
    end
    subgraph S3b["3b · Stress-test the test (simulated + real structure)"]
        ST6["Stage 6 · dependence stress test,<br/>power curve, real-data placebo<br/>STRESS_PASS"]
    end
    subgraph S4["4 · Real data (each run once, rules fixed first)"]
        R1["US first sample<br/>T = 22.59 · reject"]
        R2["NSE fresh sample<br/>T = 17.31 · reject"]
        R3["US fresh sample (Alpaca)<br/>T = 17.75 · reject"]
    end
    subgraph S5["5 · Placement check and reporting"]
        P6["Phase 6 · Do real samples look<br/>like the simulations?<br/>(exploratory)"]
        D["Dashboard and reports"]
    end
    S1 --> S2 --> S3 --> S3b --> S4 --> S5
    P6 --> D
```

---

## 4. Every phase: what it did and why it matters

Each phase was approved before it started, and each one's rules were written down (and usually hashed) **before** its results existed.

### Phase M1 · Data availability and research specification
- **What:** checked which free sources give 5-minute bars for the six stocks, and wrote the research specification (periods, slots, questions).
- **Why it matters:** decides what can honestly be studied. Free Yahoo data gives only about 60 days of 5-minute history, which sets the sample size (59 days) used everywhere after.
- **Docs:** [01](docs/01_data_availability_report.md), [02](docs/02_research_spec.md), [03](docs/03_data_sources_and_licensing.md)

### Phase M2 · Ingestion, validation and cleaning pipeline
- **What:** pulls raw data once into write-once files with SHA-256 hashes, then parses, validates (missing bars, duplicates, invalid prices, zero volume) and cleans it. Every bar keeps a status flag; nothing is silently filled or deleted.
- **Why it matters:** every later number rests on this. It also found an NSE feed quirk: the 15:15–15:25 bars were empty or unreliable in Yahoo data.
- **Docs:** [04](docs/04_nse_anomaly_investigation.md), [05](docs/05_validation_rules.md) · **Code:** `src/quantlab/` (calendars, ingest, parse, validate, clean)

### Phase M3 · Exploratory data analysis
- **What:** descriptive look at volatility by time of day, volume, tails and data quality.
- **Why it matters:** showed the shapes and fat tails that make H1 hard to test. It is descriptive only; nothing is claimed from it.
- **Docs:** [06](docs/06_eda_findings.md)

### Phase M4a / M4b · Diagnostics on simulated data
- **What:** simulated markets where the true answer is known, to see how H1 and H2 tests behave (814,880 simulation rows in M4b).
- **Why it matters:** this is where the **main problem was found**. The standard H1 bootstrap test rejected **7–9% of the time instead of 5%** when tails were heavy and intraday shapes uneven. Without this, a real-data "reject" could have been a false alarm.
- **Docs:** [09](docs/09_m4a_h1_h2_diagnostic_report.md), [10](docs/10_m4a_h1_method_comparison_and_h2_validation.md), [11](docs/11_m4a_next_diagnostic_round.md), [12](docs/12_m4b_h1_inference_and_h2_power_report.md)

### H1 calibration, Stages 0–5 · Build a test that can be trusted
| Stage | What it did | Why it matters | Docs |
|---|---|---|---|
| **0 · Preparation** | Benchmarks, precision arithmetic, frozen specification v1 (23 hashed files) and v1.1 | Fixes every rule before results exist, so nothing can be tuned to a desired answer | [13](docs/13_h1_calibration_investigation_plan.md), [14](docs/14_h1_calibration_stage0_report.md), [15](docs/15_h1_calibration_decision_document.md), [15a](docs/15a_h1_calibration_spec_v1_1.md), [15b](docs/15b_h1_calibration_v1_1_review_record.md) |
| **1 · Baseline diagnosis** | 68 scenarios, 1,240,000 simulations of the old test | Measured exactly when it fails: false-alarm rate 4.6% to 10.9%, worst with heavy tails plus uneven shapes | [16](docs/16_h1_calibration_stage1_report.md) |
| **2 · Develop candidates** | Built candidates C1 and C3; 1.78 million development simulations | C3 (a fixed critical value per sample size) never exceeded its limit; it became the sole candidate | [17](docs/17_h1_calibration_stage2_plan.md), [18](docs/18_h1_calibration_stage2_report.md) |
| **3 · Locked validation** | 96 scenarios, 2,280,000 fresh simulations, run once | C3 stayed within its limit in **88 of 88** gated scenarios, including 20 it had never seen | [20](docs/20_h1_calibration_stage3_prerun_record.md), [21](docs/21_h1_calibration_stage3_report.md) |
| **4 · Independent checks** | 6 harder simulated worlds (jumps, volatility clustering, …), a bar-level pipeline check and an independent re-implementation | C3's worst rate was 4.41% (limit 6%); two separate code paths agree to about 10⁻¹³ | [22](docs/22_h1_calibration_stage4_preregistration.md), [23](docs/23_h1_calibration_stage4_report.md) |
| **5 · Decision** | Audit of counts, seeds and failures | Verdict **PARTIAL**: safe and conservative in the simulated domain; not shown to be exactly 5% or valid on real data | [24](docs/24_h1_calibration_stage5_decision_report.md), [25](docs/25_h1_calibration_stage5_errata.md) |

### Real-data H1 tests · Use the test, once per sample
- **What:** the frozen C3 test on real data. Rule: use the **first 59 complete trading days**; if there are fewer, report "not testable" instead of shortening.
  - **US first sample (Yahoo):** T = 22.59, reject. NSE first sample: not testable (58 days). [30](docs/30_real_data_h1_test_preregistration_plan.md), [31](docs/31_real_data_h1_test_report.md)
  - **NSE fresh pull (Yahoo):** T = 17.31, reject. [33](docs/33_complete_h1_check_preregistration_plan.md), [35](docs/35_nse_h1_check_report.md)
  - **US fresh pull (Alpaca, April–July 2026):** T = 17.75, reject. [37](docs/37_fresh_us_check_design.md), [39](docs/39_fresh_us_check_report.md)
- **Why it matters:** this is the actual answer to H1. The fresh US sample comes from a **different period and data source** that played no part in designing the simulations, so the result does not just echo the data the test was built around.

### Phase 6 · Do the real samples look like the simulations? (exploratory)
- **What:** measures each real sample's tail weight, intraday shape, day-to-day volatility and cross-stock dependence, and compares them with the simulated scenarios C3 was validated on. Run once under the approved "Option A" rules, which allow only the labels OUTSIDE, CANNOT BE CLASSIFIED or INSUFFICIENT.
- **Result:**

  | Sample | Phase 6 result | Main reason |
  |---|---|---|
  | NSE, first and fresh | INSUFFICIENT | 2026-10-15 is incomplete inside the 59-day block |
  | US, first | CANNOT BE CLASSIFIED | dependence measure too unstable to place |
  | US, fresh | OUTSIDE | volatility persistence (0.42) and shared volatility (0.30) are well above the simulated settings (0.19, 0.14) |

- **Why it matters:** it shows *where the simulation evidence stops*. The fresh US period had stronger dependence than any simulated setting, so for that period C3 has no simulation evidence either way. It also found that one simulated shape (E) was fitted to variances but simulated as volatility; the real intraday shape is actually closest to the validated shape R2.
- **Docs:** protocol [26](docs/26_real_data_descriptive_validation_protocol.md) to [29](docs/29_stage0_d_tail_compatibility_decision_memo.md), revision [40](docs/40_phase6_protocol_revision6_exploratory.md), report [41](docs/41_phase6_exploratory_report.md)

### Stage 6 · Stress-test C3 and measure its power (simulated data, plus the real samples' own structure)
- **What:** after Phase 6 showed that the fresh US sample had stronger day-to-day dependence than the simulations used, a new stage with **frozen rules and new registered seeds** asked three questions, each run once ([docs/42](docs/42_stage6_preregistration_dependence_power_placebo.md), report [docs/43](docs/43_stage6_report.md)):
  1. **Size under dependence:** 96 simulated settings × 25,000 simulations, with stocks and days moving together as in the real data (persistence, shared volatility, correlation), including the top of their uncertainty range and two stronger levels that were reported but not scored.
  2. **Power:** how large an open/close difference C3 detects with 80% power at 59, 90, 125, 180 and 250 sessions.
  3. **Real-data placebo:** shuffle the time-of-day labels inside each real session so the truth is "equal", keep the real tails and dependence, and count false alarms.
- **Result:**

  | Question | Result |
  |---|---|
  | Size under dependence | **STRESS_PASS.** All 64 scored cells within limit; highest rate **4.84%** (limits 5.5% and 6.0%). The 32 stronger, unscored cells also stayed within the limits (highest 4.61%). The old bootstrap test reached 7.96% on the same data |
  | Power | 80% power at an open/close multiple of **1.20×–1.24×** with 59 sessions, **1.16×–1.17×** with 125, **1.10×–1.11×** with 250. At the observed ≈2× the lowest power in the grid is 99.8% |
  | Real-data placebo | False alarms **0.73%** (US first), **1.30%** (NSE fresh), **0.85%** (US fresh) against a 5.5% limit; real T (17.3 to 22.6) is far above every placebo's 95th percentile (2.5 to 2.6) |

- **Why it matters:** it closes the gap Phase 6 opened. C3 was not shown unsafe where the real data sit, it is **cautious but not blind** (it finds differences of about 1.1×–1.25×), and on the real samples' own tails and dependence it raises few false alarms. It stays **PARTIAL**: this is still simulated evidence plus a placebo, not proof on real markets.
- **Code and charts:** `src/quantlab/research/stage6.py`, `scripts/milestone4/stage6_*.py`, `scripts/make_stage6_charts.py`.

### Reusable tool · `quantlab-h1`
- **What:** a command-line program that applies the frozen C3 test to any three stocks of one market given as 5-minute bars (CSV), with plain-language output, data-quality counts and an explicit refusal when the input is outside what C3 was checked for ([docs/45](docs/45_h1_tool_guide.md)). Fed with the project's own bars it reproduces the three recorded real-data T values to 9 decimals.
- **Why it matters:** it turns a study into something another person can run, and it never shortens a sample or hides a limit.

### Reporting · Dashboard and summaries
- **What:** an interactive [dashboard](https://claude.ai/artifact/JyiVESsrnCvSjoXpwpdARw) built only from saved aggregate results (offline copy in [`dashboard/`](dashboard/)), a plain-language summary ([36](docs/36_project_summary_in_plain_language.md)) and a final status record ([38](docs/38_closing_decisions_and_status.md)).
- **Why it matters:** anyone can see every number, where it came from and what it does not mean, without running code.

---

## 5. How the H1 test works

```mermaid
flowchart LR
    A["5-minute bars<br/>3 stocks"] --> B["Keep the first 59<br/>complete trading days"]
    B --> C["Square each return<br/>(size of the move)"]
    C --> D["Average per day in<br/>open · middle · close"]
    D --> E["Compare periods in pairs<br/>log ratio ÷ standard error"]
    E --> F["T = the largest<br/>of the three"]
    F --> G{"T above the<br/>C3 limit 3.30?"}
    G -- yes --> H["Reject:<br/>volatility differs"]
    G -- no --> I["Not rejected:<br/>weak evidence of equality"]
```

- For each pair of periods (open vs middle, close vs middle, open vs close) the test computes the **log ratio** of average squared returns and divides it by its standard error.
- **T** is the largest of the three values (in absolute size).
- **C3** is a fixed cut-off chosen in advance from simulations: 3.30 for 59 days.
- Because C3 is conservative, a rejection is the more informative direction.

---

## 6. More charts

### C3 against the old test in every simulated scenario
![False-alarm rate in each of the 96 validation cells](docs/images/calibration_cells.svg)

Each dot is one simulated scenario in which volatility was truly equal, so every rejection there is a false alarm. **C3 (blue) stays left of its limit everywhere it is gated**; the old bootstrap test (grey) often crosses it.

### Harder simulated worlds
![False-alarm rate under six alternative processes](docs/images/alt_processes.svg)

Even with jumps, volatility clustering, period- and stock-specific tails, a heavy-tailed day factor and Laplace shocks, C3 stayed at or below 4.41% (limit 6%). The old test exceeded the limit in most of them.

### Where the simulations went
![Simulations per stage](docs/images/simulations_by_stage.svg)

### Phase 6: real dependence against the simulated setting
![US dependence measured vs the simulated level](docs/images/phase6_dependence.svg)

Dots are estimates and lines are ± 2 standard errors from a jackknife. The fresh US sample (orange) lies beyond the 1.5× "outside" line for persistence and shared volatility.

### Stage 6: false-alarm rate when stocks and days are dependent
![C3 false-alarm rate under dependence](docs/images/stage6_size.svg)

Every dot is a simulated market where volatility truly was equal. C3 (blue) stays well left of the limits at every dependence level, including the two stronger ones that were not scored.

### Stage 6: power of C3
![Power of C3 by sample size](docs/images/stage6_power.svg)

### Stage 6: real-data placebo
![Real-data placebo false-alarm rate](docs/images/stage6_placebo.svg)

All charts are drawn by [`scripts/make_readme_charts.py`](scripts/make_readme_charts.py) and [`scripts/make_stage6_charts.py`](scripts/make_stage6_charts.py) from the saved result files. No number in them is typed by hand.

---

## 7. Data sources

| Source | Used for | Access | Terms and handling |
|---|---|---|---|
| **Yahoo Finance** (public chart endpoint, fetched with Python's `urllib`) | NSE and US 5-minute bars: first sample (2026-10-30 pull) and fresh NSE pull | Free, no account; about 60 days of 5-minute history; data is revised between pulls | Personal use only, no redistribution ([docs/03](docs/03_data_sources_and_licensing.md)). **Not in this repository** |
| **Alpaca Market Data API**, free paper-trading account | Fresh US sample: AAPL, MSFT, NVDA, 2026-04-13 to 2026-08-05, `feed=sip`, `adjustment=raw` | Free account and API keys created by the owner; keys used only as terminal environment variables, never stored | Raw data kept locally only; only aggregates committed ([docs/37](docs/37_fresh_us_check_design.md), [39](docs/39_fresh_us_check_report.md)) |
| Simulated data | All calibration work (Stages 1–4, M4) | Generated by project code with registered seeds | Fully in the repository and reproducible |

- **Providers that were researched but not used** (they needed payment, or are not free for NSE) are listed in [docs/34](docs/34_provider_research_for_p2.md).
- **Total spent: ₹0.**
- Raw market data stays in `data/` on the owner's computer, which is git-ignored. Only aggregate results (test statistics, rates, summaries) are in GitHub.

---

## 8. Trust and reproducibility

```mermaid
flowchart LR
    A["Write the plan<br/>and rules"] --> B["Hash code, specs<br/>and inputs"]
    B --> C["Owner approves"]
    C --> D["Run once"]
    D --> E["Save write-once<br/>outputs"]
    E --> F["Report every result,<br/>including failures"]
```

- **Rules fixed first.** Every stage has a plan written before its results existed. Changes need a new, numbered document.
- **Frozen inputs.** 14 SHA-256 manifests (132 file entries) cover specifications, code, critical values and data-derived inputs, including the Stage 6 plan and code. If a single byte changes, verification fails.
- **Run once.** Validation runs and real-data tests are run a single time; outputs are write-once.
- **Nothing hidden.** Failures, "not testable" results and unexpected findings (like the shape-E mismatch) are kept and reported.
- **Registered seeds.** Every simulation uses a registered master seed, so results can be regenerated exactly.
- **Tests.** 438 automated tests, all on synthetic data, pass; GitHub Actions runs them and the manifest check on every push.
- **Reproducible.** Re-running part of a Stage 6 cell from its registered seeds reproduced the saved results exactly.

Verify everything from the repository root:

```bash
make check        # = python scripts/verify_manifests.py  +  python -m pytest -q
```

Because the manifests hash raw file bytes, **never move or rename files** listed in them.

---

## 9. What the results do not show

- **C3's real-data error rate is unverified.** On real data nobody knows the true answer, so a 5% false-alarm rate cannot be proven there.
- **Partly independent only.** All real samples use the same six stocks that shaped the simulations. The fresh US sample adds a new period and source, but not new stocks.
- **Expected pattern.** Higher volatility at the open is well known; these results confirm it.
- **Limited scope.** Three stocks per market, about 59 days per sample, liquid large caps only. Nothing is claimed about other stocks, markets or years.
- **C3 is cautious.** It has less power than the old test: it detects an open/close difference of about 1.2× at 59 sessions and about 1.1× at 250 (Stage 6). A "not rejected" result is weak evidence of equality. None of the real results was close.
- **Phase 6 is exploratory.** Under Option A it cannot place any sample *inside* the simulated domain. The full version (all NIFTY 50 and S&P 500 stocks over two years) needs data that free sources do not provide.
- **The Stage 6 stress test covers the levels tried.** C3 passed at every dependence level up to the illustrative stress value, but that is simulated evidence in the settings tested; the placebo breaks the within-day volatility pattern and reuses the same 59 sessions, so it is a stress check, not a proof of size.
- **No independent stocks yet.** A holdout on stocks that played no part in the design needs a new data pull, which needs your approval ([docs/44](docs/44_independent_holdout_design.md)). For the US, Alpaca's free plan may also allow a longer 90–250-session study at no cost (depth unverified until a small test pull); earlier notes that said free sources cannot do this are corrected there.
- **No trading claims.** Nothing here supports a trading, profitability or performance statement.

---

## 10. Run it yourself

Requires Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
```

The tests use synthetic data only and do not need market data.

| Task | Command |
|---|---|
| Check everything (manifests + all tests) | `make check` |
| Run the C3 test on your own bars | `pip install .` then `quantlab-h1 your_bars.csv` (try `make demo` first; [docs/45](docs/45_h1_tool_guide.md)) |
| Rebuild the README and Stage 6 charts | `make charts` |
| Rebuild the offline dashboard | `python dashboard/build_dashboard.py` |
| View the dashboard locally | `python -m http.server 8765 --directory dashboard`, then open http://127.0.0.1:8765/ |
| Pull and clean Yahoo data (one limited pull) | `python scripts/milestone2/run_pipeline.py pull-test --confirm`, then `process <raw file>` |
| Calibration stages | `scripts/milestone4/stage1_*.py` … `stage4_*.py` (full list and run times in [docs/19](docs/19_quantlab_project_status_report.md) §9) |

The real-data scripts (`real_h1_run.py`, `p2_nse.py`, `p2_us.py`, `phase6_run.py`) **refuse to run twice**: their outputs already exist and are write-once.

---

## 11. Repository map and document index

```
src/quantlab/            core pipeline: calendars, ingest, parse, validate, clean, eda/
src/quantlab/research/   simulators, H1/H2 methods, calibration, real-data test, Phase 6, Stage 6
src/quantlab/h1tool.py   the reusable C3 test: `quantlab-h1 bars.csv` (guide: docs/45)
scripts/milestone1-4/    command-line runners, one folder per milestone
scripts/verify_manifests.py     checks every frozen manifest (used by CI and `make check`)
scripts/make_readme_charts.py, make_stage6_charts.py   draw the charts in this README and the Stage 6 report
examples/                synthetic demo bars for the tool (no market data)
.github/workflows/ci.yml        automatic checks on every push
Makefile                 `make check`, `make demo`, `make charts`
tests/                   438 unit tests (synthetic data only)
docs/                    reports, plans and decision records, numbered in reading order
docs/images/             README charts (generated)
dashboard/               offline dashboard: page, aggregate datasets, build script
outputs/                 saved results and frozen manifests (aggregates only)
data/                    NOT in the repository (raw market data, git-ignored)
```

| Want to… | Read |
|---|---|
| Understand the project in 5 minutes | [docs/36](docs/36_project_summary_in_plain_language.md) plain-language summary |
| See the final status of every item | [docs/38](docs/38_closing_decisions_and_status.md) |
| Browse every document | [docs/README.md](docs/README.md) guided index |
| See the full technical status and simulation ledger | [docs/19](docs/19_quantlab_project_status_report.md) |

---

## 12. Tech stack

| Layer | Tools | Used for |
|---|---|---|
| **Language** | Python 3.12 | everything except the dashboard page |
| **Numbers and data** | NumPy 2.5, pandas 3.1, SciPy 1.18 | returns, simulations, test statistics, the intraday shape fit |
| **Statistics** | statsmodels 0.15 | models in the H2 work |
| **Storage** | PyArrow 26 (Parquet files), CSV, JSON | cleaned data and saved results |
| **Exploratory charts** | Plotly 7.1 | M3 charts (kept locally, not in the repository) |
| **Testing** | pytest 9.2 | 438 tests on synthetic data |
| **Data access** | Python `urllib` | Yahoo Finance public chart endpoint; Alpaca Market Data API (keys read from environment variables) |
| **Integrity** | `hashlib` / `shasum` (SHA-256) | raw-file hashes and the 13 frozen manifests |
| **Dashboard** | HTML, CSS, JavaScript, D3.js v7 | the five-page dashboard, hosted as a Claude Artifact; offline copy built by `dashboard/build_dashboard.py` and served with Python's `http.server` |
| **Docs and charts** | Markdown, Mermaid, SVG | this README, 49 numbered documents, flowcharts, and charts drawn by `scripts/make_readme_charts.py` and `scripts/make_stage6_charts.py` with plain Python |
| **Packaging** | `pyproject.toml` (setuptools) | installable package and the `quantlab-h1` command ([docs/45](docs/45_h1_tool_guide.md)) |
| **Automation** | GitHub Actions, Make | on every push: verify all frozen manifests, run all tests; `make check` does the same locally |
| **Version control** | Git, GitHub | [Pravin292/Quantlab](https://github.com/Pravin292/Quantlab) |

Exact versions are pinned in [`requirements.txt`](requirements.txt). There is no database, no web framework, no machine-learning library and no paid service.

---

## 13. Glossary

| Term | Meaning |
|---|---|
| **Volatility** | How big price moves are; here, the root-mean-square of 5-minute returns |
| **H1** | The hypothesis that volatility is equal in the open, middle and close periods |
| **T** | The test statistic: the largest of the three period differences divided by its standard error |
| **C3** | The fixed cut-off for T, chosen from simulations (3.30 at 59 days). Above it, H1 is rejected |
| **False-alarm rate** (size) | How often a test says "different" when volatility is truly equal. The target is 5% |
| **Fat tails** | Big surprise moves happen more often than a bell curve predicts |
| **Gated cell** | A simulated scenario with a pass limit (5.5% for tier A, 6.0% for tier B) |
| **PARTIAL** | The verdict on C3: within its limits in the simulated domain, not proven exactly right everywhere |
| **Jackknife** | Re-computing a measure while leaving out one day at a time, to see how stable it is |
| **Manifest** | A list of file hashes; if any file changes, verification fails |
