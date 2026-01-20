import pandas as pd
import pytest

from postprocess.lending_guide import filter_income, recommend_debit_date

income_sources_data = {
    "activeScore": [3, 3, 3, 0, 0],
    "errorCode": [000, 000, 205, 205, 205],
    "incomeType": ["Payroll", "Transfer", "Transfer", "Transfer", "Deposit"],
    "frequency": ["S", "I", "I", "I", "I"],
    "monthlyIncome": [937.48, 606.95, 145, 145, 145],
    "regularPayDay": ["Friday", "None", "None", "None", "None"],
    "sourceName": [
        "CAPGEMINI DES:REG.SALARY ID:CGA50481295 INDN:W...",
        "Balance Transfer",
        "Venmo",
        "Other Transfer",
        "Mobile Deposit",
    ],
}


@pytest.fixture
def income_sources():
    return pd.DataFrame(income_sources_data)


def test_filter_income_regular(income_sources):
    filtered_income = filter_income(income_sources, active_score=3, no_error=True, regular=True)

    # Should include only 'Payroll' type (with frequency S), which has activeScore >= 1
    assert len(filtered_income) == 1
    assert filtered_income.iloc[0]["incomeType"] == "Payroll"
    assert filtered_income.iloc[0]["frequency"] == "S"


def test_filter_income_irregular(income_sources):
    filtered_income = filter_income(income_sources, active_score=3, no_error=True, regular=False)

    # Should include only Transfer/Deposit types with frequency "I" that don't contain "other" in the source name
    assert len(filtered_income) == 1
    assert all(filtered_income["incomeType"].isin(["Transfer", "Deposit"]))
    assert all(filtered_income["frequency"] == "I")


def test_filter_income_active_score(income_sources):
    filtered_income = filter_income(income_sources, active_score=4, no_error=True, regular=True)

    assert filtered_income.empty


def test_filter_income_no_error(income_sources):
    filtered_income = filter_income(income_sources, active_score=0, no_error=False, regular=False)

    assert len(filtered_income) == 3


def test_recommend_debit_date_no_income(income_sources):
    customer_income_type, debit_frequency, debit_date = recommend_debit_date(income_sources)
    assert customer_income_type == "Payroll"
    assert debit_frequency == "S"
    assert debit_date == "Friday"


def test_recommend_debit_date_irregular(income_sources):
    # Remove the 'Payroll' income source
    income_sources = income_sources[income_sources["incomeType"] != "Payroll"]
    customer_income_type, debit_frequency, debit_date = recommend_debit_date(income_sources)
    assert customer_income_type == "irregular"
    assert debit_frequency == "W"
    assert debit_date == "ask customer"


def test_recommend_debit_date_no_income_sources(income_sources):
    # Make each income source have an error code so that no income sources are valid
    income_sources["errorCode"] = [201, 301, 205, 205, 205]
    customer_income_type, debit_frequency, debit_date = recommend_debit_date(income_sources)
    assert customer_income_type == "No Income"
    assert debit_frequency == "None"
    assert debit_date == "None"
