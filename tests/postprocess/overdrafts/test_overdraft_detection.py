import pytest
from data import PostProcessTestData

from postprocess.overdrafts import overdraft_detection


@pytest.fixture
def balance_df():
    return PostProcessTestData().balance_df


def test_overdraft_detection(balance_df):
    transactions_df = PostProcessTestData().transactions_df
    on_cnt, incidents, _, _ = overdraft_detection(transactions_df, balance_df)
    assert len(on_cnt) == 4
    assert on_cnt.columns.to_list() == ["accountGuid", "odAll", "od3m", "od6m", "nsfAll", "nsf3m", "nsf6m", "odfAll", "odf3m", "odf6m"] 
    assert int(on_cnt.iloc[0]["odAll"]) == 0
    assert int(on_cnt.iloc[0]["od3m"]) == 0
    assert int(on_cnt.iloc[0]["od6m"]) == 0
    assert incidents.columns.to_list() == [
        "accountGuid",
        "date",
        "amount",
        "description"
    ]
