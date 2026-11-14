# 36 — QuantLab in plain language: what was done, what was found (final, 2026-11-14)

**Purpose:** one readable summary for anyone. It adds no new analysis; every number comes from the reports named in brackets. The project's front page ([README](../README.md)) has the flowcharts and charts.

## 1. The question
Does a stock's volatility (the size of its price moves) differ between the **open**, **middle** and **close** of the trading day? This is tested on 5-minute data for three NSE stocks (RELIANCE, TCS, INFY) and three US stocks (AAPL, MSFT, NVDA), and the project calls it **H1**. The hard part is having a test you can trust on short samples (about 59 days) with fat tails and uneven intraday shapes.

## 2. What was built, step by step
1. **Data pipeline (M1–M3):** free 5-minute data is pulled once, hashed, validated and cleaned, with nothing silently filled or deleted ([docs/05](05_validation_rules.md), [06](06_eda_findings.md)).
2. **Diagnosis (M4):** in simulated markets where the truth is known, the standard bootstrap test said "different" **7–9% of the time instead of 5%** when tails were heavy ([docs/12](12_m4b_h1_inference_and_h2_power_report.md)).
3. **A better test (Stages 0–5):** a fixed cut-off called **C3** was developed and then checked on **8,024,000 simulations** with frozen rules and registered seeds. C3 never exceeded its limit in any of the 88 gated scenarios or the 6 harder alternative worlds. Verdict: **PARTIAL**. It is safe and conservative in the simulated domain, but not shown to be exactly 5% or valid on real data ([docs/24](24_h1_calibration_stage5_decision_report.md)).

## 3. The answer on real data (each sample run once, rules fixed first)
| Sample | Source | Days | T (limit 3.30) | Result |
|---|---|---|---|---|
| US, first | Yahoo | 2026-08-06 to 2026-10-28 | 22.59 | **reject** ([docs/31](31_real_data_h1_test_report.md)) |
| NSE, fresh | Yahoo | 2026-08-18 to 2026-11-13 | 17.31 | **reject** ([docs/35](35_nse_h1_check_report.md)) |
| US, fresh | Alpaca (SIP feed) | 2026-04-13 to 2026-07-07 | 17.75 | **reject** ([docs/39](39_fresh_us_check_report.md)) |
| NSE, first | Yahoo | 58 complete days only | — | not testable ([docs/31](31_real_data_h1_test_report.md)) |

In every sample the open is about **2× as volatile** as the middle of the day. This is the well-known intraday pattern, so the result confirms it rather than discovers it.

## 4. Phase 6: do the real samples look like the simulations? (exploratory)
- **What it compared:** each sample's tail weight, intraday shape, day-to-day volatility and cross-stock dependence against the simulated scenarios ([docs/40](40_phase6_protocol_revision6_exploratory.md), [41](41_phase6_exploratory_report.md)).
- **Results:**
  - Both NSE blocks: **INSUFFICIENT** (one incomplete day, 2026-10-15).
  - US first sample: **CANNOT BE CLASSIFIED**.
  - US fresh sample: **OUTSIDE**. Its day-to-day volatility was more persistent (0.42 against 0.19) and more shared across the three stocks (0.30 against 0.14) than the simulations assumed.
- **What that means:** for that period, C3 has no simulation evidence either way.
- **A finding about the earlier work:** the simulated shape "E" was fitted to variances but simulated as volatility. The real intraday shape is closest to the validated shape R2.

## 5. What these results do not show
- **C3's 5% rate on real data:** it cannot be proven, because the truth is unknown on real data.
- **Independence is only partial:** the same six stocks shaped the simulations. The fresh US sample adds a new period and source, but not new stocks.
- **Scope:** nothing is claimed about other stocks, markets or years, and nothing about trading or profit.

## 6. Status of every item
Everything planned is **done, decided or closed** ([docs/38](38_closing_decisions_and_status.md)).
- **Not done:** the full-universe Phase 6 or a 90–250-day study. Both need data that free sources do not provide, and they have not been approved.

## 7. Cost, safety and reproducibility
- **Cost:** ₹0. Only free data tiers were used; the Alpaca account and keys belong to the owner, and the keys were never stored.
- **Integrity:** 413 tests pass; 13 hash manifests verify; frozen files, seeds and C3 were never edited; every outcome (including "not testable" and "insufficient") is kept.
- **Data handling:** raw market data stays on the owner's computer (git-ignored); only aggregates are on GitHub.
- **Repository:** https://github.com/Pravin292/Quantlab, branch `main`. Dashboard: https://claude.ai/artifact/JyiVESsrnCvSjoXpwpdARw
