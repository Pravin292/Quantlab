# 41 — Phase 6 exploratory descriptive placement: report (run once, 2026-11-14)

**Status:** results of the exploratory Phase 6 run under `docs/40` (revision 6 of `docs/26`, Option A). The protocol, code and tests were frozen in `outputs/milestone4/frozen_phase6_inputs.sha256` (11 files, all OK) before the run. It ran once (about 7 seconds); outputs are under `outputs/milestone4/phase6/`. No random numbers, no simulation, and no H1 statistic were computed.

## 1. Block outcomes

| Sample | Block (first 59 scheduled sessions) | Status | Final label |
|---|---|---|---|
| NSE · first Yahoo sample | 2026-08-05 to 2026-10-29 | 2026-10-15 unusable | **INSUFFICIENT** |
| US · first Yahoo sample | 2026-08-06 to 2026-10-28 | complete | **CANNOT BE CLASSIFIED** |
| NSE · fresh Yahoo pull | 2026-08-18 to 2026-11-12 | 2026-10-15 unusable | **INSUFFICIENT** |
| US · fresh Alpaca pull | 2026-04-13 to 2026-07-07 | complete | **OUTSIDE** |

As `docs/40` R6.3 sets out, Option A allows no coverage rank. These labels say whether a measured dimension is clearly outside the simulated settings (OUTSIDE), or whether the evidence is insufficient to place the block (CANNOT BE CLASSIFIED). The strict cleaning variant gave the same label in both US blocks: it removed 4 sessions in the first sample (5 zero-volume bars) and 1 in the fresh sample (1 bar with |z| > 8).

## 2. What drives each label

**US fresh: OUTSIDE (dependence).** All three dependence components are stronger than the US "estimated dependence" setting the simulations used (φ 0.190, s 0.141, ρ 0.187). The rank-4 cut is 1.5 × each value.

| Component | Point estimate | Stability interval (± 2 SE_J) | Rank-4 cut | Zone |
|---|---|---|---|---|
| φ, day-volatility lag-1 autocorrelation | **0.425** | 0.240 to 0.609 | 0.285 | rank 4 |
| s, cross-stock day-volatility correlation | **0.300** | 0.104 to 0.496 | 0.211 | rank 4 |
| ρ, cross-stock return correlation | 0.240 | 0.185 to 0.295 | 0.281 | interval reaches rank 4 |

The φ and s point estimates themselves are above the cut, not only the upper ends of their intervals. All three measures passed the reliability checks. In April–July 2026, day-to-day volatility was more persistent and more shared across AAPL, MSFT and NVDA than in the simulated settings.

**US first: CANNOT BE CLASSIFIED.**
- D-tail and D-alt are unavailable under Option A.
- D-dep is unreliable: the φ interval is wider than 0.4, and deleting one session moves s across a zone boundary.
- D-shape is rank 2 and D-daysd is rank 2 (M10 = 0.230; its interval [0.199, 0.260] touches the 0.15–0.20 fringe zone).
- This sample's dependence point estimates (φ 0.195, s 0.177, ρ 0.187) are almost exactly the simulation settings, as expected: the settings were estimated from this sample (circularity, `docs/26` §3.3).

## 3. Measurements (baseline; point estimate and stability interval)

| Measure | US first | US fresh |
|---|---|---|
| M2 kurtosis, pooled | 4.55 (3.85–5.25) | 4.91 (3.92–5.90) |
| M2 kurtosis, open / middle / close | 3.67 / 4.76 / 4.42 | 3.42 / 5.12 / 5.32 |
| M3 Hill index, top 5% | 4.20 (3.63–4.77) | 4.48 (3.85–5.10) |
| M4 \|z\| > 4 per 1,000 | 1.92 | 1.92 |
| M10 day-volatility sd | 0.230 (0.199–0.260) | 0.273 (0.235–0.311) |
| M11 φ | 0.195 (−0.083–0.473) | 0.425 (0.240–0.609) |
| M12 s | 0.177 (−0.004–0.358) | 0.300 (0.104–0.496) |
| M12 ρ | 0.187 (0.146–0.227) | 0.240 (0.185–0.295) |
| M13 within-day squared-return autocorrelation, lags 1–5 | 0.085 | 0.070 |
| M15 day-volatility kurtosis | 3.68 | 3.37 |
| M17 tick / median price step | 0.04% | 0.04% |

The tail measures are not mapped under Option A. For context only (not a placement): a kurtosis of about 4.5–4.9 and a Hill index of about 4.2–4.5 are heavier-tailed than a Gaussian, in line with the df 4–8 range the earlier descriptives reported (`docs/14`).

## 4. Shape: primary and literal methods (`docs/40` §3 and R6.5)

| Sample | Primary (data's volatility shape): nearest, q | Literal (as E was built): nearest, q |
|---|---|---|
| US first | **R2**, q = 1.11 (rank 2) | E, q = 0.17 |
| US fresh | **R2**, q = 0.81 (unreliable: delete-block ratio and pseudo-value skew) | E, q = 2.91 |

- **Primary method:** both US samples' real volatility shape is nearest to R2, a validated shape, not to E. This agrees with the finding recorded in `docs/40` §3: E as simulated is steeper than the real fitted shape.
- **Literal method:** the first sample comes out near E because E was built from that sample by this same route. The fresh sample is further from E (q = 2.91).
- In both samples every stock's nearest shape matched the panel's.

## 5. What this does and does not show

- **Does show:**
  - Fresh 2026 US data had stronger volatility persistence and cross-stock co-movement than the simulated US dependence setting.
  - The real US intraday shape resembles R2 more than E.
  - Both NSE samples fail the strict completeness rule, because of one session (2026-10-15).
- **Does not show:**
  - It assigns no placement: under Option A no block can be REPRESENTED, NEAR BOUNDARY or PARTIALLY REPRESENTED.
  - It does not say whether C3 holds its rate on these data.
  - Exceeding the simulated dependence setting does **not** mean C3 fails there. The simulations validated C3 at that one setting; stronger dependence is untested territory.
- **Independence:** these are the exposed stocks (D7). The fresh sample adds a new period and source but not new stocks. Two blocks are reported as counts, with no pooling and no tests.

## 6. Integrity

| Check | Result |
|---|---|
| Phase 6 freeze manifest (11 files) | verified before the run |
| Test suite | 413 passed (362 earlier + 51 Phase 6) |
| All hash manifests | 13 verified, 0 mismatches |
| Raw data | stays in `data/` (git-ignored); only aggregates in `outputs/milestone4/phase6/` |
