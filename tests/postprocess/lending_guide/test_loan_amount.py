import pandas as pd

from postprocess.lending_guide import recommend_debit_amount, recommend_loan_amount
from config import settings

def test_recommend_loan_amount():
    redzone_behavior = pd.DataFrame({"riskScore": [165, 208, 160, 40], "riskBehavior": ["NO", "NO", "NO", "YES"]})
    min_loan, max_loan = recommend_loan_amount(redzone_behavior)

    assert min_loan == 620.0
    assert max_loan == 820

    # test some edge cases with min loan amount higher than loan amount allowed
    redzone_behavior = pd.DataFrame({"riskScore": [10000, 10000], "riskBehavior": ["YES", "YES"]})
    min_loan, max_loan = recommend_loan_amount(redzone_behavior)
    assert min_loan == settings.LOAN_AMOUNT_MAX
    assert max_loan == settings.LOAN_AMOUNT_MAX

    redzone_behavior = pd.DataFrame({"riskScore": [-500, -500], "riskBehavior": ["NO", "NO"]})
    min_loan, max_loan = recommend_loan_amount(redzone_behavior)
    assert min_loan == settings.LOAN_AMOUNT_MIN
    assert max_loan == settings.LOAN_AMOUNT_MIN


def test_recommend_loan_amount_zeroes():
    redzone_behavior = pd.DataFrame({"riskScore": [0, 0], "riskBehavior": ["YES", "YES"]})
    min_loan, max_loan = recommend_loan_amount(redzone_behavior)

    assert min_loan == 300.0
    assert max_loan == 300.0


def test_recommend_debit_amount():
    redzone_behavior = pd.DataFrame({"riskScore": [165, 208, 160, 40], "riskBehavior": ["NO", "NO", "NO", "YES"]})
    min_debit, max_debit = recommend_debit_amount(redzone_behavior)

    assert min_debit == 170.0
    assert max_debit == 250


def test_recommend_debit_amount_zeroes():
    redzone_behavior = pd.DataFrame({"riskScore": [0, 0], "riskBehavior": ["YES", "YES"]})
    min_debit, max_debit = recommend_debit_amount(redzone_behavior)

    assert min_debit == 90.0
    assert max_debit == 90.0
