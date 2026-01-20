from datetime import datetime, timezone

import pandas as pd
import pytest

from utils.utils import standardize_date_format


@pytest.mark.parametrize(
    "input_series, expected_series",
    [
        (
            pd.Series(
                [
                    "2024-03-30T23:59:59Z",
                    "2024-03-30T23:59:59.500Z",
                    "2024-03-18T10:16:12Z",
                ]
            ),
            pd.Series(
                [
                    datetime(2024, 3, 30, 23, 59, 59, 999000, tzinfo=timezone.utc),
                    datetime(2024, 3, 30, 23, 59, 59, 500000, tzinfo=timezone.utc),
                    datetime(2024, 3, 18, 10, 16, 12, 999000, tzinfo=timezone.utc),
                ]
            ),
        ),
        (
            pd.Series(["2024-03-30", "2024-03-30T23:59:59"]),
            pd.Series(
                [
                    datetime(2024, 3, 30, 23, 59, 59, 999000, tzinfo=timezone.utc),
                    datetime(2024, 3, 30, 23, 59, 59, 999000, tzinfo=timezone.utc),
                ]
            ),
        ),
        (
            pd.Series(["2024-03-30T23:59:59.000Z"]),
            pd.Series([datetime(2024, 3, 30, 23, 59, 59, tzinfo=timezone.utc)]),
        ),
        (
            pd.Series(["2024-03-30T23:59:59.999Z"]),
            pd.Series([datetime(2024, 3, 30, 23, 59, 59, 999000, tzinfo=timezone.utc)]),
        ),
        (
            pd.Series(["2024-03-30Z"]),
            pd.Series([datetime(2024, 3, 30, 23, 59, 59, 999000, tzinfo=timezone.utc)]),
        ),
    ],
)
def test_standardize_date_format(input_series, expected_series):
    result_series = standardize_date_format(input_series)
    assert len(result_series) == len(expected_series), "Series lengths differ"
    for result, expected in zip(result_series, expected_series):
        if result.tzinfo is not None and expected.tzinfo is not None:
            result = result.astimezone(timezone.utc)
            expected = expected.astimezone(timezone.utc)
        assert result == expected, f"Elements differ: {result} != {expected}"
    assert all(result_series.index == expected_series.index), "Series indices differ"
