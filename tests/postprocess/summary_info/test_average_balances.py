import pytest
from data import PostProcessTestData

from postprocess.summary_info.average_balances import AverageBalances


@pytest.fixture
def balance_df():
    return PostProcessTestData().balance_df


def test_avg_balances_all_accounts(balance_df):
    transactions_df = PostProcessTestData().transactions_df
    avg_balance = AverageBalances().avg_balances_all_accounts(
        balance_df, transactions_df
    )
    assert len(avg_balance) == 4
    assert avg_balance.columns.to_list() == [
        "accountGuid",
        "index",
        "averageMonthlyBalanceAll",
        "averageMonthlyBalance3Month",
        "averageMonthlyBalance6Month",
    ]
    assert int(avg_balance.iloc[0]["index"]) == 0
    assert int(avg_balance.iloc[0]["averageMonthlyBalanceAll"]) == -3082
    assert int(avg_balance.iloc[0]["averageMonthlyBalance3Month"]) == -2837
    assert int(avg_balance.iloc[0]["averageMonthlyBalance6Month"]) == -3082
