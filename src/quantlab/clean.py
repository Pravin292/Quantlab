"""Cleaning: produce a separate, ANNOTATED copy of the bars.

What cleaning does (and does not do)
------------------------------------
* It never touches raw files and never modifies the DataFrame passed in.
* It NEVER fills missing values and NEVER deletes suspicious candles.
  Suspicious bars stay in the table and are labelled with flag columns.
* The only rows removed are EXACT duplicate rows (same timestamp and same
  values), because they carry no extra information. If two rows share a
  timestamp but disagree, we cannot know which is right, so we stop with an
  error instead of guessing.
* Two summary columns are added so later code can choose what to trust:
    usable           False for bars that must not be used for prices
                     (empty, impossible, outside session, still forming)
    volume_reliable  False when the volume is empty, zero, or an NSE bar
                     known to have untrustworthy volume
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .calendars import Market
from .validate import FLAG_COLUMNS, ValidationResult, validate

# A bar with any of these flags is not safe to use as a price observation.
PRICE_BLOCKING = ["missing_ohlc", "invalid_ohlc", "unexpected_session_bar",
                  "forming_bar", "duplicate_timestamp"]
# A bar with any of these flags has volume we should not trust.
VOLUME_SUSPECT = ["missing_ohlc", "missing_volume", "zero_volume",
                  "invalid_ohlc", "unexpected_session_bar", "forming_bar",
                  "nse_open_zero_volume"]


def drop_exact_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove repeated identical rows; raise if same timestamp has different values."""
    dup_mask = df.index.duplicated(keep=False)
    if not dup_mask.any():
        return df
    dups = df[dup_mask]
    # Treat NaN == NaN so two identical empty rows count as identical.
    for ts, group in dups.groupby(level=0):
        if len(group.drop_duplicates()) > 1:
            raise ValueError(f"conflicting duplicate rows at {ts}; "
                             "refusing to guess which is correct")
    return df[~df.index.duplicated(keep="first")]


@dataclass
class CleanResult(ValidationResult):
    """A ValidationResult that also records how many duplicate rows were dropped.

    Because it is a subclass, all existing code that uses the result as a
    ValidationResult keeps working unchanged."""
    n_duplicates_removed: int = 0

    def to_text(self) -> str:
        return (super().to_text()
                + f"\n  {'duplicates_removed':<24}{self.n_duplicates_removed:>6}")


def clean(df: pd.DataFrame, market: Market,
          as_of: pd.Timestamp | None = None) -> tuple[pd.DataFrame, CleanResult]:
    """Return (annotated_bars, result). Input is left unchanged."""
    deduped = drop_exact_duplicates(df.sort_index())
    n_removed = len(df) - len(deduped)       # exact duplicate rows dropped
    out = deduped.copy()
    base = validate(out, market, as_of)
    result = CleanResult(base.market, base.flags, base.missing_slots,
                         base.n_rows, base.n_days, n_duplicates_removed=n_removed)
    out = out.join(result.flags)
    out["usable"] = ~out[PRICE_BLOCKING].any(axis=1)
    out["volume_reliable"] = ~out[VOLUME_SUSPECT].any(axis=1)
    return out, result


def write_clean(df: pd.DataFrame, path: Path, *, raw_sha256: str,
                overwrite: bool = False) -> Path:
    """Save to Parquet, recording which raw snapshot it came from."""
    path = Path(path)
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    df = df.copy()
    df.attrs["raw_sha256"] = raw_sha256
    df.to_parquet(path)
    return path
