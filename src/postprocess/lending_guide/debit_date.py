import pandas as pd


def recommend_debit_date(income_sources: pd.DataFrame) -> tuple:
    """
    Recommends a debit date based on the customer's income sources.
    """
    # If the customer has regular income, output the frequency and regular payday of the highest regular income
    regular_income = filter_income(income_sources, regular=True)
    if regular_income.shape[0] > 0:
        regular_income = regular_income.sort_values("monthlyIncome", ascending=False)
        return regular_income.incomeType.iloc[0], regular_income.frequency.iloc[0], regular_income.regularPayDay.iloc[0]
    # If the customer has no regular income, suggest weekly debit date and encourage to ask the customer for a debit date.
    # TODO: Add irregular income breakdown by month and weekday so we can give better recommendation
    else:
        irregular_income = filter_income(income_sources, regular=False)
        if irregular_income.shape[0] > 0:
            return "irregular", "W", "ask customer"
        else:
            return "No Income", "None", "None"


def payment_near_holiday(income_sources):
    """
    Recommends whether to schedule payments near holidays.
    """
    # If the customer has regular income, output the frequency and regular payday of the highest regular income
    regular_income = filter_income(income_sources, regular=True)
    if regular_income.shape[0] > 0:
        regular_income = regular_income.sort_values("monthlyIncome", ascending=False)
        return regular_income.paymentNearHoliday.iloc[0], str(regular_income.nextPayDayOnHoliday.iloc[0])
    else:
        irregular_income = filter_income(income_sources, regular=False)
        if irregular_income.shape[0] > 0:
            irregular_income = irregular_income.sort_values("monthlyIncome", ascending=False)
            return irregular_income.paymentNearHoliday.iloc[0], str(irregular_income.nextPayDayOnHoliday.iloc[0])
        else:
            return "None", "Not Applicable"

    # If the customer has no regular income, suggest weekly debit date and encourage to ask the customer for a debit date.


def filter_income(income_sources: pd.DataFrame, active_score=3, no_error=True, regular=True) -> pd.DataFrame:
    """
    Filters income sources based on active score, error code, and regularity.
    """
    filtered_income = income_sources[income_sources.activeScore >= active_score]
    if no_error:
        filtered_income = filtered_income[filtered_income.errorCode == 000]
    if regular:
        filtered_income = filtered_income[
            filtered_income.incomeType.isin(["Payroll", "Benefit"])
            | (filtered_income.frequency.isin(["M", "B", "S", "W"]))
        ]
    else:
        filtered_income = filtered_income[
            (~filtered_income.incomeType.isin(["Payroll", "Benefit"]))
            & (filtered_income.frequency == "I")
            & (~filtered_income.sourceName.str.contains("other", case=False))
        ]
    return filtered_income
