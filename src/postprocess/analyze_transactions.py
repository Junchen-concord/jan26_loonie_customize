import numpy as np
import pandas as pd
import simplejson
from config import config
from labeling.clustering import NER_Clustering
from utils.utils import merge_duplicate_clusters

from postprocess.additional_info.additional_info import append_additional_info
from postprocess.application_checker import application_checker
from postprocess.feature_extraction import feature_extraction
from postprocess.lending_guide.lending_guide import (
    append_account_level_lending_guides,
    append_customer_level_lending_guide,
)


def analyze_transactions(
    labeled_transactions, transactions_df, balance_df, application_info=None, IBV_auth_data=None
) -> str:
    """
    Analyzes bank transactions and provides IA output

    Args:
        - labeled_transactions (DataFrame): labeled bank trans
        - transactions_df (DataFrame): unlabeled bank transactions (TODO: switch usages of transactions_df to labeled_transactions, remove transactions_df)
        - balance_df (DataFrame): account metadata associated w/ transactions
        - application_info (dict): application data provided by lender, default to None if not given
        - IBV_auth_data (dict): IBV data provided by IBV provider, default to None if not given

    Returns:
        - output_final: IAResponse as str
    """
    formatted_as_of_date = pd.to_datetime(balance_df["as_of_date"].max())
    labeled_transactions = cluster_loans(labeled_transactions)
    labeled_transactions = cluster_payrolls(labeled_transactions)
    labeled_transactions = create_boolean_category_columns(labeled_transactions)
    labeled_transactions[config.IA_DATE] = pd.to_datetime(labeled_transactions[config.IA_DATE])
    labeled_transactions = add_transaction_categories(labeled_transactions)

    labeled_transactions_1 = labeled_transactions.copy()
    balance_df_1 = balance_df.copy()
    transactions_df_1 = transactions_df.copy()

    # Source Level Features
    output_json_multi = feature_extraction(
        labeled_transactions, formatted_as_of_date, balance_df, transactions_df, True
    )
    output_json = feature_extraction(
        labeled_transactions_1,
        formatted_as_of_date,
        balance_df_1,
        transactions_df_1,
        False,
    )

    ## Application Checker result with comparing application data and IBV data
    ## TODO: This likely needs a bigger surgury as currently it is placed after "feature_extraction", because it requires the income sources which is part of
    ## it's output, however, the function also generate red zone scores which can also benefit from the results from application checker
    ## It's hard to just include this into the "feature_extraction" as well as it was run twice for account level and application level, results in unnecessary execution

    output_json = append_additional_info(output_json)

    if output_json_multi is not None:
        output_json["additionalInfo"]["redZoneBehaviorCustomer"] = output_json_multi["redZoneBehavior"]
        output_json["additionalInfo"]["alertsAndInsightsCustomer"] = output_json_multi["alertsAndInsights"]
        customer_level_scores = output_json_multi["scores"]
        for key, value in customer_level_scores.items():
            output_json["scores"][key]["customerLevel"] = value["accountLevel"]
        output_json["scores"]["features"]["customerLevel"] = output_json_multi["scores"]["features"]["accountLevel"]
    else:
        customer_level_scores = output_json["scores"]
        for key, value in customer_level_scores.items():
            output_json["scores"][key]["customerLevel"] = value["accountLevel"]
        output_json["scores"]["features"]["customerLevel"] = output_json["scores"]["features"]["accountLevel"]

    output_json = append_customer_level_lending_guide(output_json)
    output_json = append_account_level_lending_guides(output_json)

    ## I would propose to break the feature extraction into 2 parts:
    ## 1. Source level feature aggregation for all the existing features for red zone
    ## 2. Red Zone and other modeling tasks related to these features.

    ## This way, not only we can add other features to the existing red zone models, but also things in source level feature aggregation
    ## DO NOT NEED TO BE RUN TWICE except for the atp feautres as all other customer level features are a simple sum/count/aggregation of
    ## account level features.
    if application_info is not None and IBV_auth_data is not None:
        application_check_result = application_checker(application_info, IBV_auth_data, output_json)
    else:
        application_check_result = {}

    output_json["modelVersion"] = config.MODEL_VERSION
    output_json = output_json | application_check_result

    output_final = simplejson.dumps(output_json, ignore_nan=True, default=numpy_converter)
    return output_final


def numpy_converter(obj):
    """Custom converter for numpy types to native JSON types"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return str(obj)


def cluster_loans(labeled_transactions: pd.DataFrame):
    """
    Create clusters for loan transactions with the same WHO column.
    For non-loan transactions, keep them as they are.
    """
    # If we don't have the required columns, return dataframe as is
    if "StackingPrediction" not in labeled_transactions.columns:
        return labeled_transactions

    # Create explicit copies to avoid SettingWithCopyWarning
    # Post process clustering for loans
    loan_mask = labeled_transactions.StackingPrediction == "loan"

    # If no loans, return the original dataframe
    if not loan_mask.any():
        return labeled_transactions

    loan_transactions = labeled_transactions.loc[loan_mask].copy()
    non_loan_transactions = labeled_transactions.loc[~loan_mask].copy()

    # If clustering column doesn't exist, add it
    if "cluster_label" not in loan_transactions.columns:
        loan_transactions["cluster_label"] = None

    # Group loans by customer ID and apply clustering
    loan_new_clusters = (
        loan_transactions.groupby(config.IA_CUSTOMER_ID)
        .apply(
            lambda x: NER_Clustering(config.PS_MAX_DISTANCE).group_transactions(
                x,
                config.WHO_SOURCE,
                config.WHO_CAT_COL,
            )
        )
        .reset_index(drop=True)
    )

    # If clustering succeeded, replace the loan transactions
    if not loan_new_clusters.empty and "cluster_label" in loan_new_clusters.columns:
        # Drop old cluster label and merge with new ones
        if "cluster_label" in loan_transactions.columns:
            loan_transactions = loan_transactions.drop(columns="cluster_label")

        # Make sure index column exists for merging
        if "index" in loan_transactions.columns and "index" in loan_new_clusters.columns:
            loan_transactions = loan_transactions.merge(
                loan_new_clusters[["index", "cluster_label"]],
                how="left",
                on="index",
            )

    # Handle empty DataFrame case to avoid concatenation warnings
    if loan_transactions.empty and non_loan_transactions.empty:
        # Return empty DataFrame with same columns
        return labeled_transactions.iloc[0:0].copy()
    elif loan_transactions.empty:
        return non_loan_transactions.reset_index(drop=True)
    elif non_loan_transactions.empty:
        return loan_transactions.reset_index(drop=True)
    else:
        # Both DataFrames have data, concatenate them
        return pd.concat([loan_transactions, non_loan_transactions], axis=0, ignore_index=True)


def cluster_payrolls(labeled_transactions: pd.DataFrame):
    """
    Aggressively cluster payroll and benefit transactions based on processed_clustering column.

    Rules:
    1. All transactions with the same processed_clustering value get the same cluster label.
    2. Uses priority-based selection when multiple cluster labels exist: who_ > processed_desc_
    3. Merges clusters with duplicate patterns (e.g., "ABC" vs "ABC ABC")
    4. If payroll and benefit are clustered together, reclassify all as benefit.
    """
    # If we don't have the required columns, return dataframe as is
    if "StackingPrediction" not in labeled_transactions.columns:
        return labeled_transactions

    if config.PROCESSED_CLUSTERING not in labeled_transactions.columns:
        return labeled_transactions

    # Create explicit copies to avoid SettingWithCopyWarning
    payroll_mask = labeled_transactions.StackingPrediction.isin(["payroll", "benefit"])

    # If no payrolls/benefits, return the original dataframe
    if not payroll_mask.any():
        return labeled_transactions

    payroll_transactions = labeled_transactions.loc[payroll_mask].copy()
    non_payroll_transactions = labeled_transactions.loc[~payroll_mask].copy()

    # Reuse the same priority-based selection logic from NER_Clustering
    ner_clustering = NER_Clustering(config.PS_MAX_DISTANCE)

    # Apply basic clustering by processed_clustering
    payroll_transactions = (
        payroll_transactions.groupby(config.PROCESSED_CLUSTERING, group_keys=False)
        .apply(ner_clustering._select_cluster_label)
        .reset_index(drop=True)
    )

    # Merge clusters with duplicate patterns in processed_clustering column
    payroll_transactions = merge_duplicate_clusters(
        payroll_transactions, config.PROCESSED_CLUSTERING, "cluster_label", threshold=0.5
    )

    # Merge clusters with duplicate patterns in WHO column
    if config.WHO_SOURCE in payroll_transactions.columns:
        payroll_transactions = merge_duplicate_clusters(
            payroll_transactions, config.WHO_SOURCE, "cluster_label", threshold=0.5
        )

    # If payroll and benefit are in the same cluster, reclassify all as benefit
    def reclassify_mixed_clusters(group):
        """If a cluster has both payroll and benefit, make them all benefit."""
        predictions = group["StackingPrediction"].unique()

        if len(predictions) > 1 and "benefit" in predictions and "payroll" in predictions:
            group["StackingPrediction"] = "benefit"

        return group

    # Apply reclassification by cluster_label
    if "cluster_label" in payroll_transactions.columns:
        payroll_transactions = (
            payroll_transactions.groupby("cluster_label", group_keys=False)
            .apply(reclassify_mixed_clusters)
            .reset_index(drop=True)
        )

    # Concatenate payroll and non-payroll transactions
    if non_payroll_transactions.empty:
        return payroll_transactions
    else:
        return pd.concat([payroll_transactions, non_payroll_transactions], axis=0, ignore_index=True)


def create_boolean_category_columns(labeled_transactions: pd.DataFrame):
    categories = ["transfer", "payroll", "loan", "gig", "benefit"]
    for category in categories:
        labeled_transactions[f"is_{category}"] = labeled_transactions["StackingPrediction"] == category
    return labeled_transactions


def add_transaction_categories(labeled_transactions: pd.DataFrame):
    """Add transaction category values based on boolean category flags.

    This function creates a new column 'transCategory' with numeric values:
    0: other
    1: payroll
    2: benefit
    3: transfer (not fee)
    4: deposit or ATM transfer
    5: gig
    6: loan
    """
    deposit_lists = [r"\batm\b", r"\bdep"]

    # Create a copy to avoid chained assignment warnings
    df = labeled_transactions.copy()

    # Set initial value for all rows
    df["transCategory"] = 0

    # Create condition masks for each category
    payroll_mask = df.is_payroll.astype(bool).fillna(False)
    benefit_mask = df.is_benefit.astype(bool).fillna(False)
    transfer_mask = (df.is_transfer.astype(bool).fillna(False)) & (
        ~df[config.IA_ORIGINAL_DESCRIPTION].str.contains(r"\bfee\b", case=False).fillna(False)
    )
    deposit_mask = df[config.IA_ORIGINAL_DESCRIPTION].str.contains("|".join(deposit_lists), case=False).fillna(False)
    gig_mask = df.is_gig.astype(bool).fillna(False)
    loan_mask = df.is_loan.astype(bool).fillna(False)

    # Apply categories in order
    df.loc[payroll_mask, "transCategory"] = 1
    df.loc[benefit_mask, "transCategory"] = 2
    df.loc[transfer_mask, "transCategory"] = 3

    # For deposit transfers (must be done after setting transfer category)
    deposit_transfer_mask = deposit_mask & (df.transCategory == 3)
    df.loc[deposit_transfer_mask, "transCategory"] = 4

    df.loc[gig_mask, "transCategory"] = 5
    df.loc[loan_mask, "transCategory"] = 6

    return df
