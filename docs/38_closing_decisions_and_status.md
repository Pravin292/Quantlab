# 38 — Closing decisions and final status (2026-11-14)

**Status:** decision record. Written after a full re-test on 2026-11-14. It records the owner's answers to three open questions and the status of every item in the project plan. Nothing here changes a frozen file, seed, threshold, critical value or manifest.

## 1. Re-test on 2026-11-14

| Check | Result |
|---|---|
| Test suite (`pytest`) | 362 passed, 0 failed |
| Hashed manifests (`shasum -a 256 -c`, all 12 under `outputs/`) | 12 verified, 0 mismatches |
| Dashboard data against saved outputs | All 96 Stage 3 cells, all 12 Stage 4 rates, all 3 real-data results and the 8,024,000 simulation total match. The only difference: 12 Stage 3 cell names use "·" where the source uses a comma (display only) |

## 2. Owner decisions recorded

1. **Data access:** the owner will create a free Alpaca account and export the keys as `ALPACA_KEY_ID` and `ALPACA_SECRET_KEY`. The fresh-US check (`docs/37`) runs only after an explicit "pull once". A larger 90–250-day US study is **not** approved by this answer and would need its own plan and approval.
2. **D-tail (`docs/29`):** **Option A** — Mode B is report-only, and D-tail is unavailable at n = 59. No new reference simulation is run, and the 60-day Stage 0 reference is not reused for n = 59. As `docs/29` §2 states, this leads to a numbered revision of `docs/26` when Phase 6 is next taken up. That revision is not drafted here, because Phase 6 is shelved (decision 3).
3. **Phase 6 (descriptive placement, `docs/26`):** **kept shelved** by the owner's choice. Not run, and not needed for the H1 results.

## 3. Final status of every planned item

| Item | Status |
|---|---|
| Tune and check C3 in simulation | Done. Verdict PARTIAL (`docs/24`) |
| Real-data H1 test, US | Done. T = 22.594, reject (`docs/31`) |
| Real-data H1 test, NSE | Done on the fresh free pull. T = 17.305, reject (`docs/35`); the first sample was not testable (58 of 59 days) |
| Fresh, independent US check | Done (`docs/39`, added 2026-11-14). Alpaca SIP, 2026-04-13 to 2026-07-07, T = 17.748, reject |
| Larger 90–250-day study (`docs/26`) | Not done. Needs more data than free sources give without an account, and has not been approved |
| Phase 6 descriptive placement | Shelved by owner decision (§2.3) |
| D-tail option (`docs/29`) | Decided: Option A (§2.2) |
| C3's 5% rate on real data | Cannot be shown: the truth is unknown on real data. It stays a stated limitation |
| Dashboard | Done. Online, and in `dashboard/` with an offline build |

## 4. What remains

Nothing. The fresh-US check was completed later the same day (`docs/39`). Every item is now done, decided, or shelved by the owner's choice. A larger 90–250-day study would need a new plan and its own approval.
