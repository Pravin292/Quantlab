# 32 — Decision sheet and the three possible next paths (documentation only; nothing here is approved)

**Status:** written 2026-11-13 after `docs/31`. Documentation only: no data read, no simulation, no random number, no statistic, no change to C3, frozen files, manifests or earlier documents. "Recommended" means my suggestion for you to accept, change or reject; **silence is not approval**, and no item below is decided.

## 1. Where the project stands after `docs/31`
- C3 calibration on simulated data: complete, **PARTIAL** (`docs/24`, `docs/25`).
- First real-data H1 look (existing Yahoo sample, `docs/30`–`31`): **US reject** (T = 22.59 against 3.30, open-driven; expected pattern, not independent); **NSE not testable** (58 of 59 required complete sessions).
- Phase 6 descriptive placement (`docs/26`–`docs/29`): proposed, unapproved; D1–D17 pending; Mode B not ready as written.
- Blocked for any further real-data work: provider and licence (D2), data-access authorisation, and for the large protocol the full decision set.

## 2. Three paths (choose one; they are not additive by default)
| Path | What it is | Needs | Effort | What you get |
|---|---|---|---|---|
| **P1 Stop and consolidate** | Treat `docs/31` as the real-data result; keep Phase 6 shelved | Nothing new | Smallest | A coherent project record: simulated calibration plus one limited real-data check |
| **P2 Complete the H1 check** | Obtain a sample with 59 complete NSE sessions (and ideally a fresh US sample) and repeat the same pre-registered test once, as a new plan (`docs/33`) | D2 (provider, licence, written confirmation that aggregate results may be published), data-access authorisation, span and calendar (D4), new pre-registration | Medium | An NSE result and, with a fresh US sample, a result not used in the design |
| **P3 Full Phase 6** | The descriptive placement protocol `docs/26` | All of D1–D17, mode declaration (and D6 if Mode A), the D-tail decision of `docs/29`, freeze manifest, tests | Largest | Block-level placement labels; per `docs/29`, Mode B gives no coverage label |

**My recommendation:** P2 if you want a real-data answer for NSE, otherwise P1. P3 costs the most and, as written, answers a narrower question (how real data resemble the simulated grid) than "does C3 work on real data". This is advice; the choice is yours.

## 3. D1–D17 with a suggested response per path
"Not needed" means the decision is not required for that path as I understand it from `docs/26` §14; confirm before relying on it.

| ID | Subject | Default in `docs/26` | P1 | P2 (suggested) | P3 |
|---|---|---|---|---|---|
| D1 | Approve protocol r5 and freeze | after review | not needed | not needed (a new plan, `docs/33`, replaces it) | required |
| D2 | Provider, budget, licence, written confirmation | licensed vendor; not Yahoo | not needed | **required first** | required |
| D3 | Universe and membership source | NIFTY 50 / S&P 500 at block start | not needed | not needed if the same six stocks are kept (suggested) | required |
| D4 | Span and calendar source | at least two years | not needed | required (must yield 59 complete NSE sessions) | required |
| D5 | Thresholds and conventions | as proposed | not needed | not needed | required |
| D6 | Reference simulation, Mode A | authorise separately | not needed | not needed | required (Mode A) or declined (Mode B) |
| D7 | Six exposed stocks | exploratory, never pooled | not needed | meaning must be recorded; suggested: no pooling across markets | required |
| D8 | Sector information | record only | not needed | not needed | required |
| D9 | Cleaning variants | baseline and strict | not needed | not needed (baseline only, as in `docs/30`) | required |
| D10 | Report all panels and blocks | yes | not needed | not needed | required |
| D11 | Aggregates in the repository | aggregates only | already followed | accept default | required |
| D12 | Identifiers in reports | per licence | not needed | after D2 | required |
| D13 | Stop rules | as proposed | not needed | accept the `docs/30` R7 rule | required |
| D14 | Calendar and membership source acceptability | user to confirm | not needed | calendar part only | required |
| D15 | Jackknife estimator | approve | not needed | not needed | required |
| D16 | Feed and liquidity characteristics | as proposed | not needed | not needed | required |
| D17 | Lenient-variant conflict | no recommendation | not needed | not needed (no lenient variant) | required; **my suggestion: option (i), drop lenient** |

For P3 the earlier suggestions stand: accept the defaults for D8, D10, D11, D13, D16; D-tail per `docs/29` (A, B or C) and D6 remain real choices.

## 4. Questions only you can answer
1. Which path (P1, P2 or P3)?
2. For P2: which provider and budget, and will you read the licence and obtain the written confirmation? I cannot create accounts, enter credentials or accept terms on your behalf; the earlier research (`docs/03`, `docs/26` §10) found no confirmed provider and left the NSE terms unread.
3. For P2: keep the same six stocks, and is a 2-year span acceptable?

## 5. What I can do next without new authorisation
Draft the P2 pre-registration (`docs/33`, same rules as `docs/30`, new data) or a provider comparison from the documented sources, **documentation only**. Neither would read data or run anything.
