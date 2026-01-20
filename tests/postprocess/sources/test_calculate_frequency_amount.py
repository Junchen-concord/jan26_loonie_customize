import numpy as np
import pandas as pd

from postprocess.sources.helpers.calculate_frequency_amount import (
    active_income_check,
    amount_stability_check,
    recurring_income_check,
)


def test_calculate_frequency_amount():
    # TODO
    assert True


def test_active_income_check():
    # Create a DataFrame with test data
    data = {
        "date": pd.date_range(start="1/1/2020", periods=12, freq="1M"),
        "amount": [100.0] * 12,
    }
    df = pd.DataFrame(data)

    # Test parameters
    as_of_date = df.date.max()
    freq = "M"

    # Call the function with the test parameters
    result = active_income_check(df, as_of_date, freq, "Benefit")

    # Check if the function returns the expected result
    assert result == 3


def test_recurring_income_check():
    # Create a DataFrame with mock data
    data = {
        "date": pd.date_range(start="1/1/2020", periods=12, freq="1M"),
        "amount": [100.0] * 12,
    }
    df = pd.DataFrame(data)

    # Define the other parameters
    freq = "M"
    regular_payday = "1"
    same_day_freq = 0.8

    # Call the function with the test data
    result = recurring_income_check(df, freq, regular_payday, same_day_freq)

    # Assert that the output is as expected (replace 'expected_output' with the expected output)
    assert result == 3


def test_amount_stability_check():
    # Create a DataFrame with mock data
    data = {
        "date": pd.date_range(start="1/1/2020", periods=12, freq="1M"),
        "amount": np.linspace(100, 150, 12),
    }
    df = pd.DataFrame(data)

    # Define the other parameters
    freq = "M"

    # Call the function with the test data
    result = amount_stability_check(df, freq)

    # Assert that the output is as expected (replace 'expected_output' with the expected output)
    assert result[0], round(result[1]) == (3, 0.13)
    result = amount_stability_check(df, freq)

    # Assert that the output is as expected (replace 'expected_output' with the expected output)
    assert result[0], round(result[1]) == (3, 0.13)
