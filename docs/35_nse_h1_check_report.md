# 35 — NSE H1 check report (zero-cost P2, one Yahoo pull, frozen C3)

**Status:** run once on 2026-11-13 under `docs/33` §7 (zero-cost version) after the owner's explicit authorisation "Yes, pull once". Frozen inputs: `outputs/milestone4/frozen_p2_inputs.sha256` (plan, runner, shared module, tests, C3 table; created and verified **before** the pull). Cost: none (no account, no subscription). Data: one Yahoo Finance 5-minute pull of RELIANCE.NS, TCS.NS and INFY.NS at 2026-11-13 18:11 UTC; raw files in `data/raw/yahoo/` (git-ignored, not published), cleaned into `data/clean_p2/` (the earlier `data/clean` was not touched). Outputs (aggregates and file hashes only): `outputs/milestone4/p2_nse/`. No random numbers, no simulation, no rule changed after the data were seen, C3 untouched.

## 1. Result
| Item | Value |
|---|---|
| Dates in the pull | 60 |
| Usable complete sessions (every stock, every used slot) | **59** for each stock and for the market (the minimum required) |
| Window used (first 59 usable) | 2026-08-18 to 2026-11-13 |
| T | **17.305** |
| Frozen C3 critical value, n = 59 | 3.298658 |
| Decision | **Reject** equal period volatility |

**Components (log ratio of period mean squares, standard error):** open versus middle 1.547 (0.089); close versus middle 0.645 (0.283); open versus close 0.902 (0.296). The open's mean square is about e^1.55 ≈ 4.7 times the middle's (volatility about 2.2 times), the close about 1.9 times (about 1.4 times in volatility), and the open exceeds the close.

## 2. How to read it (as pre-registered in `docs/30` §5 and `docs/33` §5)
- T is far above the critical value, so the rejection does not depend on C3's exact size or conservatism. In these 59 sessions of three NSE stocks, open and close volatility are clearly higher than the middle's. This is the well-known intraday pattern; it **confirms an expected pattern and is not a new finding**.
- Unlike the earlier US result, NSE shows a (less precisely estimated) close elevation; the close-versus-middle standard error is 0.28, so the size of that contrast is uncertain.
- **Limits:** the sample is the same source (Yahoo), the same three stocks that informed the simulation design, and its window (2026-08-18 to 2026-11-13) overlaps most of the earlier Yahoo window used for design. It is therefore **not an independent replication**, and says nothing about other stocks or periods. C3's size on real NSE tails is still unverified (NSE close tails may lie outside the gated domain, `docs/14`), but here the rejection is far from the margin.
- The result was **not at risk of the completeness failure** that stopped NSE in `docs/31`: this pull supplied exactly 59 complete sessions, and the rule to use only complete sessions and never shorten n was followed. A single missing bar would have made it NOT TESTABLE.
- Yahoo is personal-use only and revised; the result is kept aggregate-only.

## 3. What this completes and what stays open
- **Completed:** both markets now have one pre-registered C3 H1 check on real data: US (`docs/31`, T = 22.59) and NSE (this report, T = 17.31), both rejecting, at zero cost.
- **Not done, optional:** a fresh US sample on dates before 2026-08-06 (`docs/33` §7) needs your free Alpaca sign-up and keys and a separate authorisation; it would only add a non-overlapping US check.
- **Still unverified and unchanged:** C3's rejection rate on real data; independence from the design sample; any claim beyond these two samples. Phase 6 (`docs/26`–`29`) remains proposed and unapproved and is not required for this check.
- Nothing from this step is committed or pushed.

## 4. Integrity
All eleven manifests verify (nine earlier, `frozen_real_h1_inputs`, `frozen_p2_inputs`) with 0 mismatches; `tests/test_research_real_h1.py` passes (5); the pull ran once (marker `data/p2_nse_pull.done`), the runner refuses a second run, and no alternative windows or stocks were tried.
