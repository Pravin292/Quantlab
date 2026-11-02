# Validation and Cleaning Rules (Milestone 2)

Code: `src/quantlab/validate.py` and `clean.py`. Tests: `tests/test_validate.py`, `tests/test_pipeline.py` (each rule is tested for both NSE and US data). Bar timestamps mean the bar START, in the exchange's local time.

## Principles
1. Raw snapshots (`data/raw/`) are written once, read-only, with timestamp + SHA-256 in the name and in `data/manifest.csv`. The code cannot overwrite them (file mode `"xb"`).
2. Cleaning writes a *separate* Parquet file to `data/clean/`, which records the raw file's hash.
3. Nothing is filled. Nothing suspicious is deleted. Bars are labelled with flags.
4. Where the correct answer is unknowable (conflicting duplicates), the code stops with an error.

## Rules (flags)
| Flag | Meaning | Blocks price use (`usable`=False)? | Marks volume unreliable? |
|---|---|---|---|
| duplicate_timestamp | Same bar start appears twice | yes | no |
| missing_ohlc | An OHLC value is empty (NaN) | yes | yes |
| missing_volume | Prices present, volume empty | no | yes |
| zero_volume | Prices present, volume exactly 0 | no | yes |
| invalid_ohlc | high<low, high<open/close, low>open/close, price ≤ 0, volume < 0 | yes | yes |
| unexpected_session_bar | Outside session hours or not on the 5-minute grid | yes | yes |
| forming_bar | Bar not finished at the time of the snapshot | yes | yes |
| nse_open_zero_volume | NSE only: 09:15 bar, real prices, volume 0 (see docs/04) | no | yes |
| nse_close_window_empty | NSE only: empty bar at 15:15 or later (see docs/04) | yes (it is empty) | yes |

Other checks
- **Timezone:** naive timestamps or the wrong zone raise an error; nothing is silently converted.
- **Missing candles:** expected 5-minute slots with no row at all are listed in `missing_slots` (checked per day that has data).
- **Duplicates in cleaning:** exact duplicate rows are dropped; same timestamp with different values raises an error.

## Known limits
- No holiday or early-close calendar: a holiday just has no data, and an early close would show later slots as missing.
- Rules are checked against synthetic data and one limited sample pull; the NSE quirk rules encode the observations in docs/04, whose causes are unconfirmed.
- Yahoo is an unofficial, personal-use source whose history is revised between pulls. This pipeline does not make it suitable for reliable long-term research.
- Prices are not checked for split/dividend adjustment.
- No cross-check against official exchange data was possible.
