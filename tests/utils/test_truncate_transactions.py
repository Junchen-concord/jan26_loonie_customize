import datetime

import pandas as pd
from pandas.testing import assert_frame_equal

from utils.utils import TimeFrame, truncate_transactions


def test_truncate_transactions_all_timeframe():
    """
    When timeframe is ALL, the function should only filter out transactions
    after the as_of_date.
    """
    data = {"date": ["2022-01-01", "2022-05-01", "2022-07-01", "2022-08-01"], "amount": [100, 200, 300, 400]}
    df = pd.DataFrame(data)
    as_of_date = datetime.date(2022, 7, 1)

    result = truncate_transactions(df, TimeFrame.ALL, as_of_date)

    # Only transactions on or before 2022-07-01 should be kept.
    expected_data = {"date": pd.to_datetime(["2022-01-01", "2022-05-01", "2022-07-01"]), "amount": [100, 200, 300]}
    expected_df = pd.DataFrame(expected_data)

    assert_frame_equal(result.reset_index(drop=True), expected_df.reset_index(drop=True))


def test_truncate_transactions_with_timeframe():
    """
    When a specific timeframe (e.g., THREE_MONTH) is provided, the function should:
      1. First, filter out transactions after as_of_date.
      2. Then, compute the cutoff based on the most recent transaction in the filtered data.
    """
    data = {
        "date": ["2022-01-15", "2022-03-10", "2022-05-05", "2022-06-20", "2022-08-10"],
        "amount": [50, 150, 250, 350, 450],
    }
    df = pd.DataFrame(data)
    # Set as_of_date such that the transaction on "2022-08-10" is removed.
    as_of_date = datetime.date(2022, 7, 1)

    # After as_of_date filtering, the remaining dates are:
    # "2022-01-15", "2022-03-10", "2022-05-05", "2022-06-20".
    # The most recent date here is "2022-06-20". For THREE_MONTH:
    # cutoff_date = ("2022-06-20" - 3 months) -> "2022-03-20", then .replace(day=1) -> "2022-03-01".
    # Thus, only transactions from "2022-03-10", "2022-05-05", "2022-06-20" should be returned.

    result = truncate_transactions(df, TimeFrame.THREE_MONTH, as_of_date)

    expected_data = {"date": pd.to_datetime(["2022-03-10", "2022-05-05", "2022-06-20"]), "amount": [150, 250, 350]}
    expected_df = pd.DataFrame(expected_data)

    assert_frame_equal(result.reset_index(drop=True), expected_df.reset_index(drop=True))


def test_as_of_date_edge():
    """
    Test that transactions occurring exactly on the as_of_date are retained,
    while those after are removed.
    """
    data = {"date": ["2022-06-30", "2022-07-01", "2022-07-02"], "amount": [10, 20, 30]}
    df = pd.DataFrame(data)
    as_of_date = datetime.date(2022, 7, 1)

    # Using TimeFrame.ALL here to focus solely on as_of_date filtering.
    result = truncate_transactions(df, TimeFrame.ALL, as_of_date)

    expected_data = {"date": pd.to_datetime(["2022-06-30", "2022-07-01"]), "amount": [10, 20]}
    expected_df = pd.DataFrame(expected_data)

    assert_frame_equal(result.reset_index(drop=True), expected_df.reset_index(drop=True))


def test_empty_dataframe():
    """
    An empty DataFrame should be returned as-is without error.
    """
    df = pd.DataFrame(columns=["date", "amount"])
    as_of_date = datetime.date(2022, 7, 1)

    result = truncate_transactions(df, TimeFrame.ALL, as_of_date)

    expected_df = pd.DataFrame(columns=["date", "amount"])
    # Ensure the expected "date" column is of datetime type.
    expected_df["date"] = pd.to_datetime(expected_df["date"])

    assert_frame_equal(result, expected_df)


def test_all_transactions_after_as_of_date():
    """
    If all transactions occur after as_of_date, the function should return an empty DataFrame.
    """
    data = {"date": ["2022-08-01", "2022-09-01"], "amount": [500, 600]}
    df = pd.DataFrame(data)
    as_of_date = datetime.date(2022, 7, 1)

    result = truncate_transactions(df, TimeFrame.ALL, as_of_date)

    expected_df = pd.DataFrame({"date": pd.to_datetime([]), "amount": pd.Series([], dtype=result["amount"].dtype)})

    assert_frame_equal(result, expected_df)
