import pytest
from data import PostProcessTestData

from postprocess.summary_info.bank_card import BankCard


@pytest.fixture
def balance_df():
    return PostProcessTestData().balance_df


@pytest.fixture
def result():
    return PostProcessTestData().arg_for_categorize_income


def test_match_card(result, balance_df):
    bank_card_info = BankCard().match_card(result, balance_df)
    assert len(bank_card_info) == 4
    assert bank_card_info.columns.to_list() == ["accountGuid", "card"]
    assert bank_card_info.iloc[0]["card"] == []
    assert bank_card_info.iloc[1]["card"] == []
    assert bank_card_info.iloc[2]["card"] == []
    assert bank_card_info.iloc[3]["card"] == []
