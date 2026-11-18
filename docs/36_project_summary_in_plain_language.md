# 36 — QuantLab in plain language: what was done, what was found (updated 2026-11-19 with Stage 6)

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

## 4b. Stage 6: was C3 stress-tested? (simulated data plus the real samples' own structure)
Because Phase 6 found stronger dependence in the fresh US sample than the simulations used, a new stage with frozen rules ([docs/42](42_stage6_preregistration_dependence_power_placebo.md), report [docs/43](43_stage6_report.md)) asked three questions:
- **Is C3 still safe when stocks and days move together as in the real data?** Yes in every scored setting: the highest false-alarm rate was **4.84%** over 64 cells (limits 5.5% and 6.0%), and 32 stronger, unscored settings also stayed within the limits. Label: **STRESS_PASS**.
- **How big a difference can C3 detect?** An open/close volatility multiple of about **1.2×** with 59 sessions and **1.1×** with 250 (80% power). The observed ≈2× is found 99.8% of the time or more.
- **Does it behave on real data's own structure?** With time-of-day labels shuffled inside each real sample (truth = equal), C3 raised false alarms **0.7% to 1.3%** of the time, far below 5.5%.
C3 is still rated PARTIAL: this is simulated evidence and a placebo, not proof on real markets.

## 5. What these results do not show
- **C3's 5% rate on real data:** it cannot be proven, because the truth is unknown on real data.
- **Independence is only partial:** the same six stocks shaped the simulations. The fresh US sample adds a new period and source, but not new stocks.
- **Scope:** nothing is claimed about other stocks, markets or years, and nothing about trading or profit.

## 6. Status of every item
Everything planned is **done, decided or closed** ([docs/38](38_closing_decisions_and_status.md)).
- **Not done:** the full-universe Phase 6 and an independent-stocks check. The independent check needs a new data pull that has not been approved ([docs/44](44_independent_holdout_design.md)); for the US, a longer 90–250-session study may be possible free through Alpaca (depth unverified), which corrects the earlier note that free sources cannot do it. The NSE side still needs an account only the owner can create.
- **Added since:** a reusable tool, `quantlab-h1`, that runs the frozen C3 test on anyone's 5-minute bars ([docs/45](45_h1_tool_guide.md)), and automatic checks on every GitHub push.

## 7. Cost, safety and reproducibility
- **Cost:** ₹0 (Stage 6 added 3,600,000 simulations on the owner's own computer). Only free data tiers were used; the Alpaca account and keys belong to the owner, and the keys were never stored.
- **Integrity:** 438 tests pass; 14 hash manifests verify; frozen files, seeds and C3 were never edited; every outcome (including "not testable" and "insufficient") is kept.
- **Data handling:** raw market data stays on the owner's computer (git-ignored); only aggregates are on GitHub.
- **Repository:** https://github.com/Pravin292/Quantlab, branch `main`. Dashboard: https://claude.ai/artifact/JyiVESsrnCvSjoXpwpdARw
