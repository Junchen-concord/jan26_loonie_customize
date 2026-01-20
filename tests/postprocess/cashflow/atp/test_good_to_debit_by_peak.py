import json
import os

import pandas as pd
import pytest

from config import config
from postprocess.cashflow.atp import good_to_debit_by_peak


@pytest.fixture
def time_series_data():
    sample_data_path = os.path.realpath(
        os.path.join(
            config.ROOT_DIR,
            "..",
            "tests",
            "data",
            "test_time_series.json",
        )
    )
    with open(sample_data_path, "r") as fp:
        data = json.load(fp)
    df = pd.DataFrame.from_dict(data)
    return df


def test_good_to_debit_by_peak(time_series_data):
    amount_due = 200
    minimum_days = 3
    prominence = 500
    peak_distance = 7
    time_series_data.loc[:, "date"] = pd.to_datetime(time_series_data.date)
    time_series_data = time_series_data.set_index("date")
    time_series_data.loc[:, "net"] = pd.to_numeric(time_series_data.net)
    result_df, peaks, peak_properties = good_to_debit_by_peak(
        time_series_data, amount_due, minimum_days, prominence, peak_distance
    )
    expected_enough_balance = [
        False,
        False,
        False,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
        False,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
        False,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
        False,
        False,
        True,
        True,
        True,
        True,
        True,
        False,
    ]

    assert "prominences" in peak_properties, "peak prominences do not exist"
    assert "left_bases" in peak_properties, "left_bases do not exist"
    assert "right_bases" in peak_properties, "right_bases do not exist"

    assert peaks.tolist() == [
        3,
        19,
        33,
        49,
        64,
        79,
        94,
    ], "peak values are incorrect"

    calculated_enough_balance = result_df["enough_balance"].tolist()

    assert (
        calculated_enough_balance == expected_enough_balance
    ), "enough_balance values are incorrect"

    expected_good_to_debit = expected_enough_balance
    calculated_good_to_debit = result_df["good_to_debit"].tolist()

    assert (
        calculated_good_to_debit == expected_good_to_debit
    ), "good_to_debit values are incorrect"
