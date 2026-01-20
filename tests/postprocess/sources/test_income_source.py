from datetime import datetime

import pandas as pd
import pytest
from data import PostProcessTestData
from test_benefit_source import expected_benefit_source_dict
from test_gig_source import expected_gig_source_dict
from test_transfer_source import expected_transf_source_dict

from postprocess.sources.helpers.rank_income import rank_income_sources
from postprocess.sources.income_source import IncomeSource


@pytest.fixture
def balance_df():
    return PostProcessTestData().balance_df


@pytest.fixture
def income_df_sorted():
    income_df_sorted, _ = rank_income_sources(
        expected_payroll_source_dict,
        expected_transf_source_dict,
        expected_benefit_source_dict,
        expected_gig_source_dict,
        PostProcessTestData().balance_df,
    )
    return income_df_sorted


expected_payroll_source_dict = {
    "KwO4y1ZoL8HDVZJV7763fBZ9XbJbm8CnpQvrz_payroll_211": {
        "accountGuid": "KwO4y1ZoL8HDVZJV7763fBZ9XbJbm8CnpQvrz",
        "sourceID": "I1_err_000",
        "sourceName": "TRUIST BANK DES:TRUIST PAY ID:XXXXX0277195 INDN:PETER WAYNE CO ID:XXXXX74313 PPD",
        "sourceType": "None",
        "sourceChannel": "None",
        "numOfPay": 24,
        "numOfPayMonthly": 2,
        "frequency": "S",
        "perPayCheck": 4101.85,
        "monthlyIncome": 8203.7,
        "regularPayDay": "15,lastday",
        "historicalPayDay": [
            "2022-09-30",
            "2022-10-14",
            "2022-10-31",
            "2022-11-15",
            "2022-11-30",
            "2022-12-15",
            "2022-12-30",
            "2023-01-13",
            "2023-01-31",
            "2023-02-28",
            "2023-03-10",
            "2023-03-15",
            "2023-03-31",
            "2023-04-14",
            "2023-04-28",
            "2023-05-15",
            "2023-05-31",
            "2023-06-15",
            "2023-06-30",
            "2023-07-14",
            "2023-07-31",
            "2023-08-15",
            "2023-08-31",
            "2023-09-15",
        ],
        "missingPayDay": [],
        "sameDayFreq": 0.7083333333333334,
        "lastPayDay": "2023-09-15",
        "incomeType": "Payroll",
        "depositMethod": "Direct Deposit",
        "errorCode": 0,
        "errorMessage": "NA",
    },
    "KwO4y1ZoL8HDVZJV7763fBZ9XbJbm8CnpQvrz_payroll_190": {
        "accountGuid": "KwO4y1ZoL8HDVZJV7763fBZ9XbJbm8CnpQvrz",
        "sourceID": "I1_err_401",
        "sourceName": "CAPGEMINI DES:REG.SALARY ID:CGA50481295 INDN:WAYNE PETER CO ID:XXXXX75929 PPD",
        "sourceType": "None",
        "sourceChannel": "None",
        "numOfPay": 2,
        "numOfPayMonthly": 2,
        "frequency": "S",
        "perPayCheck": 2549.15,
        "monthlyIncome": 5098.3,
        "regularPayDay": "15,lastday",
        "historicalPayDay": ["2022-09-15", "2022-09-30"],
        "missingPayDay": [],
        "sameDayFreq": 1.0,
        "lastPayDay": "2022-09-30",
        "incomeType": "Payroll",
        "depositMethod": "Direct Deposit",
        "errorCode": 401,
        "errorMessage": "Income not seen within 18 days",
    },
}
expected_income_source_trans_columns = [
    "accountGuid",
    "transGUID",
    "sourceName",
    "description",
    "date",
    "amount",
    "transCategory",
    "cluster_label",
    "type",
    "fromModel",
    "WHO",
    "HOW",
    "WHAT",
    "whoCat",
    "dayOfWeek",
    "sourceID",
]


def test_categorize_income_source():
    df = PostProcessTestData().arg_for_categorize_income
    as_of_date = pd.to_datetime(datetime(2023, 9, 15))
    _, income_source_trans, sourceID = IncomeSource.categorize_income_source(df, as_of_date, 0)
    assert len(income_source_trans) == 184
    assert len(income_source_trans.columns) == 16
    assert income_source_trans.columns.to_list() == expected_income_source_trans_columns
    assert sourceID == 1


def test_income_by_month(income_df_sorted, balance_df):
    income_source_cnt = IncomeSource.income_by_month(income_df_sorted, balance_df)
    assert len(income_source_cnt) == 4
    assert income_source_cnt.columns.to_list() == [
        "accountGuid",
        "all_time",
        "three_month",
        "six_month",
    ]
    assert income_source_cnt.iloc[0]["all_time"] == 3
    assert income_source_cnt.iloc[0]["three_month"] == 2
    assert income_source_cnt.iloc[0]["six_month"] == 2


def test_income_history(balance_df):
    df = PostProcessTestData().arg_for_categorize_income
    as_of_date = pd.to_datetime(datetime(2023, 9, 15))
    _, income_source_trans, _ = IncomeSource.categorize_income_source(df, as_of_date, 0)
    income_history_output = IncomeSource.income_history(income_source_trans, balance_df)
    assert len(income_history_output) == 4
    assert income_history_output.columns.to_list() == [
        "accountGuid",
        "incomeHistoryAllTime",
        "incomeHistoryThreeMonth",
        "incomeHistorySixMonth",
    ]
    assert income_history_output.iloc[0]["incomeHistoryAllTime"] == 19614
    assert income_history_output.iloc[0]["incomeHistoryThreeMonth"] == 0
    assert income_history_output.iloc[0]["incomeHistorySixMonth"] == 0


def test_averageMonthlyIncome_by_month(balance_df):
    df = PostProcessTestData().arg_for_categorize_income
    as_of_date = pd.to_datetime(datetime(2023, 9, 15))
    _, income_source_trans, _ = IncomeSource.categorize_income_source(df, as_of_date, 0)
    monthly_income = IncomeSource.averageMonthlyIncome_by_month(income_source_trans, balance_df)
    assert len(monthly_income) == 4
    assert monthly_income.columns.to_list() == [
        "accountGuid",
        "allTimeMonthlyIncome",
        "threeMonthMonthlyIncome",
        "sixMonthMonthlyIncome",
    ]
    assert int(monthly_income.iloc[0]["allTimeMonthlyIncome"]) == 7
    assert int(monthly_income.iloc[0]["threeMonthMonthlyIncome"]) == 0
    assert int(monthly_income.iloc[0]["sixMonthMonthlyIncome"]) == 0
