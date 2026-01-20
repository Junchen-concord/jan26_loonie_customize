import numpy as np
import pandas as pd
from api.config import config as apiConfig
from config import config, settings
from utils.decorators import timer


class Cashflow:
    @staticmethod
    @timer
    def cashflow(result: pd.DataFrame, balance_df: pd.DataFrame) -> pd.DataFrame:
        """Check total credits/debits."""

        all_account_ids = balance_df[[config.IA_ACCOUNT_ID]]
        credits_ = result[result.type == "CREDIT"]
        debits = result[result.type == "DEBIT"]
        end_date = balance_df.groupby("accountGuid").agg(end_date=("as_of_date", "max")).reset_index()
        result = result.merge(end_date, how="left", on="accountGuid")
        result["start_date"] = result.groupby(config.IA_ACCOUNT_ID).date.transform("min")
        result["time_period"] = (pd.to_datetime(result["end_date"]) - pd.to_datetime(result["start_date"])).dt.days
        total_credits = credits_.groupby(config.IA_ACCOUNT_ID).agg(totalCredits=("amount", "sum"))
        total_debits = debits.groupby(config.IA_ACCOUNT_ID).agg(totalDebits=("amount", "sum"))
        total_credit_debit = (
            all_account_ids.merge(total_credits, how="left", on=config.IA_ACCOUNT_ID)
            .merge(total_debits, how="left", on=config.IA_ACCOUNT_ID)
            .fillna(0)
        )

        # This has a potential issue for calculation, where total_credit_debit is one row per account while
        # result.time_period is one row per unique accountGuid in transactions.
        total_credit_debit[apiConfig.NET_CASH_FLOW] = (
            total_credit_debit.totalCredits - total_credit_debit.totalDebits
        ) / np.maximum(1, result.time_period / 30)
        total_credit_debit[apiConfig.NET_CASH_FLOW] = np.nan_to_num(
            total_credit_debit[apiConfig.NET_CASH_FLOW], nan=0.0
        )  # Replace NaN with 0.0

        total_credit_debit[apiConfig.SPENDING] = total_credit_debit.totalDebits / np.maximum(1, result.time_period / 30)
        total_credit_debit[apiConfig.SPENDING] = np.nan_to_num(
            total_credit_debit[apiConfig.SPENDING], nan=0.0
        )  # Replace NaN with 0.0

        return total_credit_debit

    @staticmethod
    @timer
    def net_cashflow(result: pd.DataFrame, balance_df: pd.DataFrame) -> pd.DataFrame:
        """Net cash flow in summary info."""

        all_account_ids = balance_df[[config.IA_ACCOUNT_ID]]
        end_date = balance_df.groupby("accountGuid").agg(end_date=("as_of_date", "max")).reset_index()
        result = result.merge(end_date, how="left", on="accountGuid")
        result["start_date"] = result.groupby(config.IA_ACCOUNT_ID).date.transform("min")
        result["time_period"] = (pd.to_datetime(result["end_date"]) - pd.to_datetime(result["start_date"])).dt.days
        result["interval"] = (pd.to_datetime(result["end_date"]) - pd.to_datetime(result["date"])).dt.days
        result["in_three_month"] = result.interval <= 90
        result["in_six_month"] = result.interval <= 180
        credits_ = result[result.type == "CREDIT"]
        debits = result[result.type == "DEBIT"]

        total_credits_all = (
            credits_.groupby(config.IA_ACCOUNT_ID)
            .agg(
                totalCredits=("amount", "sum"),
                time_period=("time_period", "first"),
            )
            .reset_index()
        )
        total_debits_all = debits.groupby(config.IA_ACCOUNT_ID).agg(totalDebits=("amount", "sum")).reset_index()
        total_credit_debit_all = total_credits_all.merge(total_debits_all, on=config.IA_ACCOUNT_ID, how="left")
        total_credit_debit_all["cashflowAllTime"] = (
            total_credit_debit_all.totalCredits - total_credit_debit_all.totalDebits
        ) / np.maximum(1, result.time_period / 30)

        total_credits_three_month = (
            credits_[credits_.in_three_month]
            .groupby(config.IA_ACCOUNT_ID)
            .agg(
                totalCredits=("amount", "sum"),
                time_period=("time_period", "first"),
            )
            .reset_index()
        )
        total_debits_three_month = (
            debits[debits.in_three_month].groupby(config.IA_ACCOUNT_ID).agg(totalDebits=("amount", "sum")).reset_index()
        )
        total_credit_debit_three_month = total_credits_three_month.merge(
            total_debits_three_month, on=config.IA_ACCOUNT_ID, how="left"
        )
        # Calculate the initial cashflow for all rows
        total_credit_debit_three_month["cashflowThreeMonth"] = (
            total_credit_debit_three_month.totalCredits - total_credit_debit_three_month.totalDebits
        )

        # For rows with time_period > 30, recalculate using a mask approach
        mask = total_credit_debit_three_month["time_period"] > 30
        if mask.any():
            # Get the filtered data without chained indexing
            filtered_df = total_credit_debit_three_month.loc[mask]

            # Calculate the numerator
            numerator = filtered_df.totalCredits - filtered_df.totalDebits

            # Calculate the denominator with minimum
            denominator = np.minimum(filtered_df.time_period, 90)

            # Calculate the adjusted value
            adjusted_values = (numerator / denominator) * 30

            # Apply back to the original DataFrame with .loc
            total_credit_debit_three_month.loc[mask, "cashflowThreeMonth"] = adjusted_values

        total_credits_six_month = (
            credits_[credits_.in_six_month]
            .groupby(config.IA_ACCOUNT_ID)
            .agg(
                totalCredits=("amount", "sum"),
                time_period=("time_period", "first"),
            )
            .reset_index()
        )
        total_debits_six_month = (
            debits[debits.in_six_month].groupby(config.IA_ACCOUNT_ID).agg(totalDebits=("amount", "sum")).reset_index()
        )
        total_credit_debit_six_month = total_credits_six_month.merge(
            total_debits_six_month, on=config.IA_ACCOUNT_ID, how="left"
        )
        # Calculate the initial cashflow for all rows
        total_credit_debit_six_month["cashflowSixMonth"] = (
            total_credit_debit_six_month.totalCredits - total_credit_debit_six_month.totalDebits
        )

        # For rows with time_period > 30, recalculate using a mask approach
        mask = total_credit_debit_six_month["time_period"] > 30
        if mask.any():
            # Get the filtered data without chained indexing
            filtered_df = total_credit_debit_six_month.loc[mask]

            # Calculate the numerator
            numerator = filtered_df.totalCredits - filtered_df.totalDebits

            # Calculate the denominator with minimum
            denominator = np.minimum(filtered_df.time_period, 180)

            # Calculate the adjusted value
            adjusted_values = (numerator / denominator) * 30

            # Apply back to the original DataFrame with .loc
            total_credit_debit_six_month.loc[mask, "cashflowSixMonth"] = adjusted_values

        total_credit_debit = (
            all_account_ids.merge(
                total_credit_debit_all[[config.IA_ACCOUNT_ID, "cashflowAllTime"]],
                how="left",
                on=config.IA_ACCOUNT_ID,
            )
            .merge(
                total_credit_debit_three_month[[config.IA_ACCOUNT_ID, "cashflowThreeMonth"]],
                how="left",
                on=config.IA_ACCOUNT_ID,
            )
            .merge(
                total_credit_debit_six_month[[config.IA_ACCOUNT_ID, "cashflowSixMonth"]],
                how="left",
                on=config.IA_ACCOUNT_ID,
            )
            .fillna(0)
        )

        return total_credit_debit

    # For NDD campaign, returns the total inflow excluding loans for the past 30 days.

    @staticmethod
    @timer
    def inflow_excluding_loans(balance_df: pd.DataFrame, credit_trans: pd.DataFrame) -> pd.DataFrame:
        refund_list = [r"\bfee\b", r"\breturn\b", r"\brefund\b", r"\breversal\b", r"\brebate\b"]
        all_account_ids = balance_df[[config.IA_ACCOUNT_ID]]
        end_date = balance_df.groupby("accountGuid").agg(end_date=("as_of_date", "max")).reset_index()
        credits_cashflow = credit_trans.merge(end_date, how="left", on=config.IA_ACCOUNT_ID)
        credits_cashflow["date_diff"] = (
            pd.to_datetime(credits_cashflow.end_date) - credits_cashflow[config.IA_DATE]
        ).dt.days

        # Find credit transactions within last 30 days, which is not a loan
        recent_inflow = credits_cashflow[credits_cashflow.date_diff <= 30]
        recent_inflow_excluding_loans = recent_inflow[recent_inflow.transCategory != 6]
        recent_inflow_excluding_loans = recent_inflow_excluding_loans[
            ~recent_inflow_excluding_loans.description.str.lower().str.contains(r"|".join(refund_list), na=False)
        ]

        if not settings.TREAT_BALANCE_TRANSFER_AS_INFLOW:
            balance_transfer_list = [
                r"\bto\b.*\bchecking\b",
                r"\bfrom.*\bchecking\b",
                r"\bfrom.*\bchk\b",
                r"\bshare\b",
                r"\bround up\b",
                r"\bsave as you go\b",
                r"\bfrom.*\bsav",
                r"\bbank",
                r"\bcredit.*line.*transfer\b",
                r"\breverse.*monthly.*service.*charge\b",
            ]
            recent_inflow_excluding_loans = recent_inflow_excluding_loans[
                ~recent_inflow_excluding_loans.description.str.lower().str.contains(
                    r"|".join(balance_transfer_list), na=False
                )
            ]

        # Agg total amount for each ID
        cust_inflow_excluding_loans = recent_inflow_excluding_loans.groupby(config.IA_ACCOUNT_ID).agg(
            inflowExcludingLoans=("amount", "sum")
        )
        cust_inflow_excluding_loans = all_account_ids.merge(
            cust_inflow_excluding_loans, how="left", on=config.IA_ACCOUNT_ID
        ).fillna(0)
        return cust_inflow_excluding_loans
