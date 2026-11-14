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
3. **Phase 6 (descriptive placement, `docs/26`):** **kept shelved** by the owner's choice. Not run, and not needed for the H1 results. *(Reversed later the same day: the owner asked for Phase 6, which ran as an exploratory check; see §3 and §5.)*

## 3. Final status of every planned item

| Item | Status |
|---|---|
| Tune and check C3 in simulation | Done. Verdict PARTIAL (`docs/24`) |
| Real-data H1 test, US | Done. T = 22.594, reject (`docs/31`) |
| Real-data H1 test, NSE | Done on the fresh free pull. T = 17.305, reject (`docs/35`); the first sample was not testable (58 of 59 days) |
| Fresh, independent US check | Done (`docs/39`, added 2026-11-14). Alpaca SIP, 2026-04-13 to 2026-07-07, T = 17.748, reject |
| Full-universe Phase 6 / larger 90–250-day study (`docs/26`) | Not done. Needs more data than free sources give without an account, and has not been approved |
| Phase 6 descriptive placement | Run as an exploratory check on 2026-11-14, after the owner reversed §2.3 (`docs/40`, `docs/41`). Under Option A no coverage label is possible: NSE blocks INSUFFICIENT, US first CANNOT BE CLASSIFIED, US fresh OUTSIDE (dependence) |
| D-tail option (`docs/29`) | Decided: Option A (§2.2) |
| C3's 5% rate on real data | Cannot be shown: the truth is unknown on real data. It stays a stated limitation |
| Dashboard | Done. Five pages (Overview, Real data, Simulation, Phase 6, Checks & limits), online and in `dashboard/` with an offline build |
| Project README | Rewritten 2026-11-14 as a full guide with flowcharts and charts (`scripts/make_readme_charts.py`) |

## 4. What remains

Nothing. The fresh-US check (`docs/39`) and the exploratory Phase 6 (`docs/41`) were completed later the same day. Every item is now done or decided. The full-universe Phase 6 and a larger 90–250-day study would each need a new plan, more data than free sources give, and their own approval.

## 5. Re-test after all work (2026-11-15)

| Check | Result |
|---|---|
| Test suite (`pytest`) | 413 passed, 0 failed (362 earlier + 51 Phase 6); 3 known warnings from `h2_volume.py`, unrelated to H1 |
| Hashed manifests (all 13 under `outputs/`) | 13 verified, 0 mismatches |
| Real-data outputs | `real_h1/`, `p2_nse/`, `p2_us/` and `phase6/` present; each run once (write-once) |
| Online dashboard self-check | passed (2026-11-14 18:24 UTC), no data-loading errors |
