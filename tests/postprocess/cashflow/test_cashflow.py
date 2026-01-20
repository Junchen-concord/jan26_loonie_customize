import pytest
from data import PostProcessTestData

from postprocess.cashflow.cashflow import Cashflow


@pytest.fixture
def balance_df():
    return PostProcessTestData().balance_df


@pytest.fixture
def result():
    return PostProcessTestData().arg_for_categorize_income


def test_cashflow(result, balance_df):
    cash_flow_data = Cashflow.cashflow(result, balance_df)
    assert len(cash_flow_data) == 4
    assert cash_flow_data.columns.to_list() == [
        "accountGuid",
        "totalCredits",
        "totalDebits",
        "netCashFlow",
        "spending",
    ]
    assert int(cash_flow_data.iloc[0]["totalCredits"]) == 122022
    assert int(cash_flow_data.iloc[0]["totalDebits"]) == 124145
    assert int(cash_flow_data.iloc[0]["netCashFlow"]) == -3
    assert int(cash_flow_data.iloc[0]["spending"]) == 189


def test_net_cashflow(result, balance_df):
    net_cash_flow_data = Cashflow.net_cashflow(result, balance_df)
    assert len(net_cash_flow_data) == 4
    assert net_cash_flow_data.columns.to_list() == [
        "accountGuid",
        "cashflowAllTime",
        "cashflowThreeMonth",
        "cashflowSixMonth",
    ]
    assert int(net_cash_flow_data.iloc[0]["cashflowAllTime"]) == -3
    assert int(net_cash_flow_data.iloc[0]["cashflowThreeMonth"]) == 0
    assert int(net_cash_flow_data.iloc[0]["cashflowSixMonth"]) == 0
