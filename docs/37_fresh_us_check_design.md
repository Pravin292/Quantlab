# 37 — Fresh-US check design, frozen before any fetch (addendum to docs/33 §7; PROPOSED, not run)

**Status:** written 2026-11-14. `docs/33` is not edited (its hash is in `frozen_p2_inputs.sha256`); this document supplements it. No data fetched, no keys exist, nothing run.

Prepared on the owner's instruction "do the further step"; **no data was fetched and no keys exist yet**. Window and rules are fixed here so nothing can be chosen after seeing data.
- **Source and cost:** Alpaca free plan, `feed=sip`, `adjustment=raw`; keys come from the owner's own free sign-up, are passed only through the environment variables `ALPACA_KEY_ID` and `ALPACA_SECRET_KEY`, and are never stored in files, printed or committed. No paid endpoint is called.
- **Stocks:** AAPL, MSFT, NVDA. **Calendar window:** 2026-04-13 to 2026-08-05 inclusive (entirely before the tested US sample, which begins 2026-08-06). **Scheduled sessions:** weekdays in the window excluding 2026-05-25, 2026-06-19 and 2026-07-03 (frozen in `scripts/milestone4/p2_us.py`). A scheduled session with no data for a stock is **unusable**, not dropped.
- **Rules:** exactly those of `docs/30` (first 59 usable complete sessions in time order; every used slot present for every stock; fewer than 59 means NOT TESTABLE; T against the frozen C3 value 3.298658; one pull, one run, write-once outputs; aggregates only). Cleaning is the project's existing cleaner (`quantlab.clean`) into `data/clean_p2_us`; the existing samples are not touched.
- **Outcome rules:** as `docs/33` §5. A fresh US rejection or non-rejection is reported beside `docs/31` without merging or reinterpreting either.
- **Tests:** `tests/test_p2_us.py` (offline: scheduled list, timestamp conversion). The frozen manifest is `outputs/milestone4/frozen_p2_us_inputs.sha256`.
- **Still needed from the owner:** free Alpaca sign-up, keys exported in the terminal session, and the explicit instruction to pull once. The free plan's SIP history depth and terms of use are unverified; if the free plan refuses `feed=sip` for these dates or asks for payment, the step stops and the US part is dropped.
