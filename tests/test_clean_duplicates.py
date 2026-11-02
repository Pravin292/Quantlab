"""Tests for the n_duplicates_removed counter added in Milestone 3."""
import pandas as pd

from quantlab.calendars import NSE, US
from quantlab.clean import clean
from quantlab.validate import ValidationResult

from conftest import make_day


def test_no_duplicates_counts_zero(market_day):
    market, day = market_day
    _, res = clean(make_day(market, day), market)
    assert res.n_duplicates_removed == 0


def test_counts_each_exact_duplicate_row_removed(market_day):
    market, day = market_day
    df = make_day(market, day)
    dup = pd.concat([df, df.iloc[[2, 2, 9]]])        # row 2 twice more, row 9 once
    out, res = clean(dup, market)
    assert res.n_duplicates_removed == 3
    assert len(out) == len(df)


def test_result_is_still_a_validation_result_and_reports_count():
    _, res = clean(make_day(NSE, "2026-10-12"), NSE)
    assert isinstance(res, ValidationResult)         # backward compatible
    assert "duplicates_removed" in res.to_text()
    assert res.counts()["duplicate_timestamp"] == 0  # original counts still work
