import math

import numpy as np
import pandas as pd

from config import settings


def recommend_amount(
    redZoneBehavior: pd.DataFrame, min_amount_ratio: float, max_amount_ratio: float, amount_min: float, amount_max: float
) -> tuple:
    redzone_score = np.max(redZoneBehavior.riskScore.astype(float))
    min_amount = min(max(min_amount_ratio * redzone_score, amount_min), amount_max)
    max_amount = max(min(max_amount_ratio * redzone_score, amount_max), amount_min)
    # make sure max amount is at least min amount
    max_amount = max(min_amount, max_amount)
    # Round to nearest 10
    min_amount, max_amount = int(math.floor(min_amount / 10.0)) * 10.0, int(math.ceil(max_amount / 10.0)) * 10
    return min_amount, max_amount


def recommend_loan_amount(redZoneBehavior: pd.DataFrame) -> tuple:
    """
    Recommends a loan amount based on the risk scores of the customer's accounts.
    """
    return recommend_amount(
        redZoneBehavior,
        settings.LOAN_AMOUNT_TO_REDZONE_MIN,
        settings.LOAN_AMOUNT_TO_REDZONE_MAX,
        settings.LOAN_AMOUNT_MIN,
        settings.LOAN_AMOUNT_MAX,
    )


def recommend_debit_amount(redZoneBehavior: pd.DataFrame) -> tuple:
    """
    Recommends a debit amount based on the risk scores of the customer's accounts.
    """
    return recommend_amount(
        redZoneBehavior,
        settings.PAYMENT_TO_REDZONE_MIN,
        settings.PAYMENT_TO_REDZONE_MAX,
        settings.PAYMENT_AMOUNT_MIN,
        settings.PAYMENT_AMOUNT_MAX,
    )
