import pandas as pd

from utils.utils import df_to_json


def recommend_account(summary_info: pd.DataFrame, income_sources: pd.DataFrame):
    """
    Recommends an account to debit from the customer's savings and checking accounts based off monthlyIncome and riskScore.

    Args:
        summary_info: A DataFrame containing account summary information.
        income_sources: A list of income sources.

    Returns:
        Bank account recommendation (str).
    """

    # Create a copy to avoid chained assignment warnings
    summary_df = summary_info.copy()
    
    # Default empty accountType with CHECKING
    if "accountType" not in summary_df.columns:
        summary_df["accountType"] = "CHECKING"
    else:
        summary_df["accountType"] = summary_df["accountType"].replace(0, "CHECKING")
        
    # Replace the original dataframe reference with our modified copy
    summary_info = summary_df

    # The account recommendation for now will only consider savings and checking account as this is 99% of accounts provided to speedy.
    filtered_summary = summary_info[summary_info.accountType.str.contains("savings|checking", case=False)]
    if len(filtered_summary) == 0:
        return "No Checking or Savings Account Provided"

    # Create a copy of income_sources to avoid chained assignment warnings
    income_sources_copy = income_sources.copy()
    
    valid_incomes = income_sources_copy[
        (income_sources_copy.activeScore >= 3)
        & (income_sources_copy.errorCode == 000)
        & (income_sources_copy.incomeType.isin(["Payroll", "Benefit"]) | income_sources_copy.frequency.isin(["M", "B", "S", "W"]))
    ]

    income_summary = valid_incomes.groupby("accountGuid").agg(
        n_incomes=("monthlyIncome", "count"),
        ## TODO, add income_history
        total_monthly_income=("monthlyIncome", "sum"),
    )
    
    # Create merged dataframe as a new object
    merged_summary = filtered_summary.merge(income_summary, on="accountGuid", how="left")
    merged_summary = merged_summary.fillna(0)

    with_income = merged_summary[merged_summary.n_incomes > 0]
    without_income = merged_summary[merged_summary.n_incomes == 0]

    if len(with_income):
        return with_income.sort_values(by="riskScore", ascending=False).accountGuid.iloc[0]
    else:
        return without_income.sort_values(by="riskScore", ascending=False).accountGuid.iloc[0]


def append_additional_info(extracted_features: dict[str, list[dict]]):
    summary_info = pd.DataFrame(extracted_features["summaryInfo"])
    income_sources = pd.DataFrame.from_dict(extracted_features["incomeSources"])
    rec_acc = recommend_account(summary_info, income_sources)
    extracted_features["additionalInfo"] = {
        "redZoneBehaviorCustomer": df_to_json(summary_info[["riskBehavior", "riskScore"]]),
        "alertsAndInsightsCustomer": df_to_json(summary_info[["alerts", "insights", "assessmentReasonsBad","assessmentReasonsGood"]]),
        "recommendedBankAccount": rec_acc,
    }
    return extracted_features
