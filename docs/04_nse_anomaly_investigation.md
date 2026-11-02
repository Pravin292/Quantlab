# NSE Anomaly Investigation (read-only)

Method: analysed the 5-minute Yahoo pulls for RELIANCE.NS, TCS.NS, INFY.NS (60 days) taken on 2026-10-30, then pulled the same data a second time later that day and compared. No raw data was edited. Scripts: `nse_investigate.py`, `chg.py` (in the session scratchpad, to be copied to `scripts/milestone2/` if you approve). Today's partial session was excluded.

**Limitation:** I have no official NSE intraday data to compare against (NSE does not publish free 5-minute history). Anything that would need the exchange's own figures is marked UNVERIFIED. Also, the first pull was not saved as raw JSON, only as parsed CSV.

## Correction to Milestone 1
I wrote that empty bars occur "at about 11:45–11:50 and 15:15–15:25". More precisely, they sit almost entirely at the **end of the session**. Counts for the 59 full days:

| Ticker | 15:15 | 15:20 | 15:25 | 11:45 / 11:50 |
|---|---|---|---|---|
| RELIANCE | 6 | 59 | 46 | 1 / 1 |
| TCS | 16 | 59 | 46 | 1 / 1 |
| INFY | 12 | 59 | 46 | 1 / 1 |

## Confirmed findings (observed in the data)
1. **The 15:20 bar is empty on all 59 days and the 15:25 bar on 46 of 59, for all three stocks.** So on most days the last two bars of the NSE session are missing, even though the timestamps exist. The same bars are empty in both pulls.
2. **The NaN positions are stable and shared:** 107 timestamps are empty in all three stocks, and pairwise overlap is 82–87%. This points to a feed-wide pattern, not a company-specific one.
3. **The 09:15 bar shows zero volume on 57–58 of 59 days, but prices are real** (open/high/low/close are not flat on any of those bars). Median volume on the few days it is non-zero is large (e.g. RELIANCE 564k vs a typical 09:20 median of 224k). So the opening bar did trade, but its volume is usually missing or zero.
4. **Data is not stable between pulls.** Comparing two pulls on the same day, the NaN set was identical, but values differed on some bars: RELIANCE 25 of 4,330, TCS 21 of 4,320, **INFY 773 of 4,324** (mostly small price changes, 20 volume changes). The examples checked show the 09:15 volume changing from 0 to a real number (INFY 2026-08-11: 0 → 366,638), and the 15:15 volume changing from a real number to 0 (INFY 2026-08-07: 255,820 → 0). So Yahoo revises its history between requests.
5. **Volume totals fall short of Yahoo's own daily volume:** summed intraday volume is 78–100% of the daily bar (median 93–95%). The shortfall is consistent with the missing opening-bar volume and the empty final bars.

## Assumptions (plausible, not confirmed)
- A: the missing 15:20/15:25 bars and zero 09:15 volume come from how Yahoo's feed handles the closing session and opening call auction. NSE has a pre-open session and a closing window, but I have not confirmed the mechanism.
- B: the 09:15 and 15:15 volume swaps between pulls may be the feed assigning auction/closing volume to different bars on different days. This is a hypothesis only.
- C: the INFY price changes may be revisions, but I did not determine the cause.

## Consequences and proposed rules (for your approval, nothing applied)
- Never trust a single pull. Keep every pull as a timestamped raw snapshot, with a hash, and record which snapshot a clean file came from.
- **Do not forward-fill the end-of-day NaN bars.** Mark them `missing` and keep them. Any analysis using the last two bars (or the closing price) must say so. Using the 15:15 bar's close as "the close" would be wrong on most days.
- **Do not use 09:15 volume for H2** (volume spike analysis) until the feed is understood. Prices from 09:15 appear usable, with a flag.
- Flag, not delete, zero-volume bars. Every rule goes into a validation report with counts so we can see its effect.
- H1/H3 results for NSE in the last 15 minutes of the session will be unreliable. State this when reporting.
- This favours finding a better NSE source (see doc 03).
