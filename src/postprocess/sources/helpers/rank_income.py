import pandas as pd

from config import config
from utils.decorators import timer


@timer
def rank_income_sources(
    payroll_source_dict: dict,
    transfer_source_dict: dict,
    benefit_source_dict: dict,
    gig_source_dict: dict,
    balance_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ranks the sources by monthly income and flags the dominant."""

    all_account_ids = balance_df[[config.IA_ACCOUNT_ID]]

    # Convert income_source_dict to df
    payroll_df = pd.DataFrame.from_dict(payroll_source_dict).transpose()
    transfer_df = pd.DataFrame.from_dict(transfer_source_dict).transpose()
    benefit_df = pd.DataFrame.from_dict(benefit_source_dict).transpose()
    gig_df = pd.DataFrame.from_dict(gig_source_dict).transpose()

    # Filter out empty dataframes to avoid warning about concatenation with empty entries
    dfs_to_concat = [df for df in [payroll_df, transfer_df, benefit_df, gig_df] if not df.empty]

    if dfs_to_concat:
        income_df = pd.concat(dfs_to_concat, ignore_index=True)
    else:
        # Create an empty DataFrame with the expected columns if all input DataFrames are empty
        income_df = pd.DataFrame(columns=["accountGuid", "incomeType", "monthlyIncome", "errorCode"])
    income_df["isDominant"] = 0

    # Sort the sources by monthly_income
    income_df_con = income_df[(income_df["errorCode"] == 000)].sort_values(by="monthlyIncome", ascending=False)
    income_df_con["max_amount"] = income_df_con.groupby("accountGuid").monthlyIncome.transform("max")

    # Need to consider the case where two source have the same amount
    income_df_con["isDominant"] = (income_df_con.monthlyIncome == income_df_con.max_amount).astype(int)

    # Append sources with error code
    error_sources = income_df[(income_df["errorCode"] != 000)]

    # Filter out empty dataframes to avoid warning about concatenation with empty entries
    dfs_to_concat = [df for df in [income_df_con, error_sources] if not df.empty]

    if dfs_to_concat:
        income_df_sorted = pd.concat(dfs_to_concat)
    else:
        # If both are empty, maintain the same structure
        income_df_sorted = income_df_con.copy() if not income_df_con.empty else error_sources.copy()

    income_df_sorted = income_df_sorted.reset_index(drop=True)

    # Only drop max_amount column if it exists
    if "max_amount" in income_df_sorted.columns:
        income_df_sorted = income_df_sorted.drop(columns="max_amount")

    dominant_incomes = (
        income_df_sorted[income_df_sorted.isDominant == 1]
        .groupby("accountGuid")
        .first()
        .reset_index()
        .rename(columns={"accountGuid": config.IA_ACCOUNT_ID})
    )
    dominant_incomes = (
        all_account_ids.merge(dominant_incomes, how="left", on=config.IA_ACCOUNT_ID)
        .fillna("No Income Detected")
        .infer_objects(copy=False)[[config.IA_ACCOUNT_ID, "incomeType"]]
    )

    return income_df_sorted, dominant_incomes
