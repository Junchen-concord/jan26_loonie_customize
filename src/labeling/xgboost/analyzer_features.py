import re

import numpy as np
import pandas as pd

from config import config
from utils.decorators import timer

strong_loan_patterns = re.compile(r"\bloan\b|\bloans\b|\blend\b|lending\b|\bmortgage\b|carpay|\bmtg\b", re.IGNORECASE)
semi_loan_patterns = re.compile(r"cash|advance|financ|\bfin\b", re.IGNORECASE)
weak_loan_patterns = re.compile(r"credit|instant|borrow|money|fund", re.IGNORECASE)

strong_payroll_patterns = re.compile(r"payroll|salary|wage|income|direct deposit", re.IGNORECASE)
strong_transfer_patterns = re.compile(
    r"\bcash app\b|\bvenmo\b|\bpaypal\b|\bapple pay\b|\bcheck.*deposit\b|\bmobile.*deposit\b|\bcash.*deposit\b|\batm\b|\bonline deposit\b|\bedeposit\b|\bremote deposit\b|\bzelle\b|\bdeposit\s+atm[a-z]+[0-9]+\b|\bcheckMobile.*deposit\b|\bedeposit in branch\b|\bdeposit made in a branch\b",
    re.IGNORECASE,
)
bank_transfer_patterns = re.compile(
    r"\bto\b.*\bchecking\b|\bfrom.*\bchecking\b|\bfrom.*\bchk\b|\bshare\b|\bround up\b|\bsave as you go\b|\bfrom.*\bsav\b|\bbank\b",
    re.IGNORECASE,
)
semi_transfer_patterns = re.compile(r"\btransfer\b|\bdeposit\b|\bwithdraw\b|\bpayment\b|\bedeposit\b", re.IGNORECASE)


class IAFeatures:
    """Income analyzer features."""

    @staticmethod
    @timer
    def time_intervals_binning(time_interval_days: int) -> str:
        """Bin the time intervals for payroll frequency check, help solving the 13,14,15 intervals problem."""

        if time_interval_days == 1:
            return "1"
        elif time_interval_days > 1 and time_interval_days <= 5:
            return "2-5"
        elif time_interval_days >= 6 and time_interval_days <= 8:
            return "6-8"
        elif time_interval_days >= 9 and time_interval_days <= 12:
            return "9-12"
        elif time_interval_days >= 13 and time_interval_days <= 17:
            return "13-17"
        elif time_interval_days >= 18 and time_interval_days <= 24:
            return "18-24"
        elif time_interval_days >= 25 and time_interval_days <= 35:
            return "24-35"
        else:
            return "36+"

    @staticmethod
    @timer
    def cluster_level_desc_label(df_cluster: pd.DataFrame, target_col: str) -> pd.DataFrame:
        """Concat all different descriptions in one cluster together."""

        # Vectorized string operations
        processed_n_gram = df_cluster.processed_n_gram

        has_strong_loan_indicators = processed_n_gram.str.contains(strong_loan_patterns).sum() / len(df_cluster) >= 0.5
        has_semi_loan_indicators = processed_n_gram.str.contains(semi_loan_patterns).sum() / len(df_cluster) >= 0.5
        has_weak_loan_indicators = processed_n_gram.str.contains(weak_loan_patterns).sum() / len(df_cluster) >= 0.5

        has_strong_payroll_indicators = (
            processed_n_gram.str.contains(strong_payroll_patterns).sum() / len(df_cluster) >= 0.5
        )
        has_strong_transfer_indicators = (
            processed_n_gram.str.contains(strong_transfer_patterns).sum() / len(df_cluster) >= 0.5
        )
        has_bank_transfer_indicators = (
            processed_n_gram.str.contains(bank_transfer_patterns).sum() / len(df_cluster) >= 0.5
        )
        has_semi_transfer_indicators = (
            (processed_n_gram.str.contains(semi_transfer_patterns))
            & (~processed_n_gram.str.contains(strong_payroll_patterns))
            & (~processed_n_gram.str.contains(strong_loan_patterns))
            & (~processed_n_gram.str.contains(semi_loan_patterns))
        ).sum() / len(df_cluster) >= 0.5

        # Check type of who, if it exists
        has_a_who_row = (~df_cluster.loc[:, config.WHO_COL].isnull()) & (df_cluster.loc[:, config.WHO_COL] != "None")
        has_who_org_row = has_a_who_row & (df_cluster.loc[:, config.WHO_COL] == "ORG")
        has_who_person_row = has_a_who_row & (df_cluster.loc[:, config.WHO_COL] == "Person")

        has_a_who = has_a_who_row.sum() / len(df_cluster) >= 0.5
        has_who_org = has_who_org_row.sum() / len(df_cluster) >= 0.5
        has_who_person = has_who_person_row.sum() / len(df_cluster) >= 0.5

        # Concatenate unique values
        how_values = df_cluster.loc[
            (~df_cluster[config.HOW_COL].isnull()) & (df_cluster[config.HOW_COL] != "None"), config.HOW_COL
        ].unique()
        who_concat = " ".join(df_cluster.loc[has_a_who_row, config.WHO_COL].unique())
        why_concat = " ".join(
            df_cluster.loc[
                ~df_cluster[config.WHAT_COL].isnull() & (df_cluster[config.WHAT_COL] != "None"), config.WHAT_COL
            ].unique()
        )

        how_concat = " ".join(how_values) if how_values.size > 0 else "No How"
        who_concat = who_concat if who_concat else "No Who"
        why_concat = why_concat if why_concat else "No Why"

        result = {
            "HOW": [how_concat],
            "WHO": [who_concat],
            "WHY": [why_concat],
            "has_strong_loan_indicators": [has_strong_loan_indicators],
            "has_semi_loan_indicators": [has_semi_loan_indicators],
            "has_weak_loan_indicators": [has_weak_loan_indicators],
            "has_strong_payroll_indicators": [has_strong_payroll_indicators],
            "has_strong_transfer_indicators": [has_strong_transfer_indicators],
            "has_bank_transfer_indicators": [has_bank_transfer_indicators],
            "has_semi_transfer_indicators": [has_semi_transfer_indicators],
            "has_who": [has_a_who],
            "has_who_org": [has_who_org],
            "has_who_person": [has_who_person],
        }

        if target_col in df_cluster.columns:
            credits_ = df_cluster[df_cluster.type == "CREDIT"]
            if len(credits_) > 0:
                label_cnts = credits_[target_col].value_counts()
                label = label_cnts.idxmax()
            else:
                label_cnts = df_cluster[target_col].value_counts()
                label = label_cnts.idxmax()
            result[target_col] = [label]

        return pd.DataFrame(result)

    @staticmethod
    @timer
    def calculate_intervals(grouped_df: pd.DataFrame, txn_date: str, counts: int):
        """
        Calculate the time intervals between transactions, bin them, and identify the most common intervals.

        Args:
            grouped_df (pd.DataFrame): DataFrame containing grouped transaction data with dates and amounts.
            txn_date (str): The name of the transaction date column.
            counts (int): Total number of transactions in the original cluster.

        Returns:
            tuple: A tuple containing:
                - i1 (str): The most common time interval (binned) between transactions.
                - i2 (str): The second most common time interval (binned) between transactions.
                - f1 (int): The frequency of the most common time interval.
                - f2 (int): The frequency of the second most common time interval.
                - p1 (float): The percentage of the most common time interval relative to the total intervals.
                - p2 (float): The percentage of the second most common time interval relative to the total intervals.
        """
        if len(grouped_df) > 1:
            # Calculate the time intervals between consecutive transactions
            grouped_df["time_intervals"] = (grouped_df[txn_date] - grouped_df[txn_date].shift(1)).dt.days

            # Bin the time intervals
            grouped_df["time_intervals_binned"] = grouped_df["time_intervals"].apply(IAFeatures.time_intervals_binning)

            # Create a frequency table of the time intervals
            time_intervals_freq = grouped_df["time_intervals_binned"].value_counts()

            if len(time_intervals_freq) >= 2:
                # Get the top 2 most common time intervals and their frequencies
                top_intervals = time_intervals_freq.iloc[:2]
                i1, i2 = top_intervals.index
                f1, f2 = top_intervals.values

                # Calculate the percentages of these intervals
                p1, p2 = f1 / (counts - 1), f2 / (counts - 1)
            else:
                # If there's only one interval, handle accordingly
                i1, f1 = time_intervals_freq.index[0], time_intervals_freq.values[0]
                i2, f2, p1, p2 = "NA", np.nan, np.nan, np.nan
        else:
            # If there are no intervals (less than 2 transactions), handle accordingly
            i1, f1, i2, f2, p1, p2 = "NA", np.nan, "NA", np.nan, np.nan, np.nan

        return i1, i2, f1, f2, p1, p2

    @staticmethod
    @timer
    def time_amount_features(df_cluster: pd.DataFrame, txn_date: str, txn_amount: str) -> pd.DataFrame:
        """
        Generate time and amount-based features from a cluster of transactions.
        """
        # Ensure the date column is in datetime format
        df_cluster[txn_date] = pd.to_datetime(df_cluster[txn_date], errors="coerce")

        # Separate credits and debits
        credits_ = df_cluster[df_cluster.type == "CREDIT"]
        debits = df_cluster[df_cluster.type == "DEBIT"]

        counts = len(df_cluster)
        n_debits = len(debits)
        n_credits = len(credits_)

        # Group by date and sum amounts
        credits_grouped = credits_.groupby(txn_date)[txn_amount].sum().reset_index()
        debits_grouped = debits.groupby(txn_date)[txn_amount].sum().reset_index()

        # Calculate intervals for credits and debits
        credit_i1, credit_i2, credit_f1, credit_f2, credit_p1, credit_p2 = IAFeatures.calculate_intervals(
            credits_grouped, txn_date, counts
        )
        debit_i1, debit_i2, debit_f1, debit_f2, debit_p1, debit_p2 = IAFeatures.calculate_intervals(
            debits_grouped, txn_date, counts
        )

        # Mode and frequency of mode of transaction amount
        amount_mode, amount_mode_freq = (
            df_cluster[txn_amount].mode().iloc[0],
            df_cluster[txn_amount].value_counts().iloc[0],
        )

        credit_only = len(credits_) > 0 and len(debits) == 0
        debit_only = len(debits) > 0 and len(credits_) == 0
        credit_and_debit = len(credits_) > 0 and len(debits) > 0
        multiple_of_5 = int((df_cluster[txn_amount] % 5 == 0).all())
        dict_stats = {
            "counts": [counts],
            "credit_time_interval_1": [credit_i1],
            "credit_time_interval_2": [credit_i2],
            "credit_time_interval_1_freq": [credit_f1],
            "credit_time_interval_2_freq": [credit_f2],
            "credit_time_interval_1_percentage": [credit_p1],
            "credit_time_interval_2_percentage": [credit_p2],
            "debit_time_interval_1": [debit_i1],
            "debit_time_interval_2": [debit_i2],
            "debit_time_interval_1_freq": [debit_f1],
            "debit_time_interval_2_freq": [debit_f2],
            "debit_time_interval_1_percentage": [debit_p1],
            "debit_time_interval_2_percentage": [debit_p2],
            "payment_amount_mean": [debits_grouped[txn_amount].mean() if len(debits_grouped) > 0 else np.nan],
            "payment_amount_min": [debits_grouped[txn_amount].min() if len(debits_grouped) > 0 else np.nan],
            "payment_amount_max": [debits_grouped[txn_amount].max() if len(debits_grouped) > 0 else np.nan],
            "payment_amount_std": [debits_grouped[txn_amount].std() if len(debits_grouped) > 0 else np.nan],
            "originated_amount_mean": [credits_grouped[txn_amount].mean() if len(credits_grouped) > 0 else np.nan],
            "originated_amount_min": [credits_grouped[txn_amount].min() if len(credits_grouped) > 0 else np.nan],
            "originated_amount_max": [credits_grouped[txn_amount].max() if len(credits_grouped) > 0 else np.nan],
            "originated_amount_std": [credits_grouped[txn_amount].std() if len(credits_grouped) > 0 else np.nan],
            "recent_originated_amount": [credits_grouped[txn_amount].iloc[-1] if len(credits_grouped) > 0 else np.nan],
            "recent_payment_amount": [debits_grouped[txn_amount].iloc[-1] if len(debits_grouped) > 0 else np.nan],
            "amount_mode": [amount_mode],
            "amount_mode_freq": [amount_mode_freq],
            "multiple_of_5": [multiple_of_5],
            "credit_only": [credit_only],
            "debit_only": [debit_only],
            "credit_and_debit": [credit_and_debit],
            "n_credits": [n_credits],
            "n_debits": [n_debits],
        }

        return pd.DataFrame(dict_stats)

    @staticmethod
    @timer
    def build_cluster_level_features(
        df_customer: pd.DataFrame,
        start_date: str,
        end_date: str,
        transaction_date: str,
        target: str,
    ) -> pd.DataFrame:
        # Sort by transaction date
        df_customer = df_customer.sort_values(by=transaction_date)

        # Build numeric and categorical features for a given customer (one row per cluster)
        # Numeric features that are generated from the transaction amount and
        # time interval between transactions

        df_num_vars = df_customer.groupby("cluster_label").apply(
            lambda x: IAFeatures.time_amount_features(x, config.IA_DATE, config.IA_AMOUNT)
        )

        # Edge case handling for only one transaction inside one accountGuid
        if isinstance(df_num_vars.index, pd.core.indexes.multi.MultiIndex):
            df_num_vars = df_num_vars.reset_index(level=1, drop=True)
        else:
            df_num_vars = df_num_vars.reset_index(drop=True)
            # Circumvent weird behaviors when only one group in dataframe
            df_num_vars.index.names = ["cluster_label"]

        df_customer[end_date] = pd.to_datetime(df_customer[end_date], errors="coerce")
        df_customer[start_date] = pd.to_datetime(df_customer[start_date], errors="coerce")
        len_txn_hist = (df_customer[end_date].iloc[0] - df_customer[start_date].iloc[0]).days + 1
        df_num_vars["frequency"] = df_num_vars["counts"] / len_txn_hist

        # Keep the processed column for count vectorizer
        df_cate_vars = df_customer.groupby("cluster_label").apply(
            lambda x: IAFeatures.cluster_level_desc_label(x, target)
        )

        if isinstance(df_cate_vars.index, pd.core.indexes.multi.MultiIndex):
            df_cate_vars = df_cate_vars.reset_index(level=1, drop=True)
        else:
            df_cate_vars = df_cate_vars.reset_index(drop=True)
            df_cate_vars.index.names = ["cluster_label"]
        # Combine numeric and categorical features
        # Handle empty dataframe concatenation
        if not df_num_vars.empty and not df_cate_vars.empty:
            df_vars = pd.concat([df_num_vars, df_cate_vars], axis=1)
        elif not df_num_vars.empty:
            df_vars = df_num_vars.copy()
        elif not df_cate_vars.empty:
            df_vars = df_cate_vars.copy()
        else:
            # Create an empty dataframe if both inputs are empty
            df_vars = pd.DataFrame()

        return df_vars
