import pytest
from data import PostProcessTestData

from postprocess.sources.loan_source import LoanSource


@pytest.fixture
def balance_df():
    return PostProcessTestData().balance_df


@pytest.fixture
def result():
    return PostProcessTestData().arg_for_categorize_income


expected_loan_source_dict_keys = [
    "accountGuid",
    "sourceID",
    "sourceName",
    "numOfOrigination",
    "numOfPay",
    "frequency",
    "originationAmount",
    "paymentAmount",
    "interestRate",
    "regularPayDay",
    "lastPayDay",
    "loanType",
    "debitType",
    "errorCode",
    "errorMessage",
]
expected_loan_source_trans_columns = [
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


def test_categorize_loan_source():
    df = PostProcessTestData().arg_for_categorize_income
    loan_source_dict, loan_source_trans = LoanSource.categorize_loan_source(df, sourceID=0)
    loan_source_dict_keys = list(loan_source_dict[list(loan_source_dict.keys())[0]].keys())
    assert loan_source_dict_keys == expected_loan_source_dict_keys
    assert len(loan_source_trans) == 2053
    assert len(loan_source_trans.columns) == 16
    assert loan_source_trans.columns.to_list() == expected_loan_source_trans_columns


def test_loan_by_month(result, balance_df):
    _, loan_source_trans = LoanSource.categorize_loan_source(result, sourceID=0)
    loan_source_cnt = LoanSource.loan_by_month(loan_source_trans, balance_df)
    assert len(loan_source_cnt) == 4
    assert loan_source_cnt.columns.to_list() == [
        "accountGuid",
        "loanIdentifiedAllTime",
        "loanIdentifiedThreeMonth",
        "loanIdentifiedSixMonth",
    ]
    # the number is inflated because these loans are predicted by xgb
    assert int(loan_source_cnt.iloc[0]["loanIdentifiedAllTime"]) == 3
    assert int(loan_source_cnt.iloc[0]["loanIdentifiedThreeMonth"]) == 0
    assert int(loan_source_cnt.iloc[0]["loanIdentifiedSixMonth"]) == 0


def test_averageMonthlyLoanPmt_by_month(result, balance_df):
    _, loan_source_trans = LoanSource.categorize_loan_source(result, sourceID=0)
    avg_monthly_loan_payment = LoanSource.averageMonthlyLoanPmt_by_month(loan_source_trans, balance_df)
    assert len(avg_monthly_loan_payment) == 4
    assert avg_monthly_loan_payment.columns.to_list() == [
        "accountGuid",
        "loanPmtAllTime",
        "loanPmtThreeMonth",
        "loanPmtSixMonth",
    ]
    assert int(avg_monthly_loan_payment.iloc[0]["loanPmtAllTime"]) == 9
    assert int(avg_monthly_loan_payment.iloc[0]["loanPmtThreeMonth"]) == 0
    assert int(avg_monthly_loan_payment.iloc[0]["loanPmtSixMonth"]) == 0
