import pandas as pd
import pytest

from postprocess.cashflow.atp import make_time_series


@pytest.fixture
def sample_data():
    data = {
        "date": [
            "2021-01-01",
            "2021-01-01",
            "2021-01-02",
            "2021-01-02",
            "2021-01-03",
        ],
        "amount": [100, 50, 200, 150, 100],
        "type": ["CREDIT", "DEBIT", "CREDIT", "DEBIT", "CREDIT"],
    }
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    return df


def test_make_time_series(sample_data):
    result = make_time_series(sample_data)

    # Define expected results
    expected_dates = pd.date_range(
        "2020-12-31", "2021-01-04"
    )  # includes padding dates
    expected_net = [
        0,
        50,
        100,
        200,
        100,
    ]

    assert all(
        result.index == expected_dates
    ), "Dates do not match expected dates."
    print(result["net"])
    assert all(
        result["net"] == expected_net
    ), "Net calculations do not match expected results."
