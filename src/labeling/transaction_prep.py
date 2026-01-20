import pandas as pd
from config import config


def initialize_transaction_fields(labeled_transactions: pd.DataFrame, default="None"):
    for col in [config.WHO_COL, config.HOW_COL, config.WHAT_COL, config.WHO_CAT_COL]:
        if col in labeled_transactions.columns:
            labeled_transactions[col] = labeled_transactions[col].fillna(default)
        else:
            labeled_transactions[col] = default
    return labeled_transactions


def revert_transaction_labels_for_processing(labeled_transactions: pd.DataFrame):
    labeled_transactions = labeled_transactions.rename(
        columns={
            "clusterLabel": "cluster_label",
            "whoCat": config.WHO_CAT_COL,
            "who": config.WHO_COL,
            "how": config.HOW_COL,
            "what": config.WHAT_COL,
            "transGuid": "guid",
            "id": "guid",
            "stackingPrediction": config.STACKING_PREDICTION,
        }
    )

    if config.WHO_SOURCE not in labeled_transactions.columns:
        labeled_transactions[config.WHO_SOURCE] = labeled_transactions[config.WHO_COL]
    if config.IA_ORIGINAL_DESCRIPTION not in labeled_transactions.columns:
        labeled_transactions[config.IA_ORIGINAL_DESCRIPTION] = labeled_transactions["description"]
    if "description" not in labeled_transactions.columns:
        labeled_transactions["description"] = labeled_transactions["sourceName"]
    labeled_transactions.set_index(pd.Index(range(len(labeled_transactions))), inplace=True)
    prepped_transactions = labeled_transactions.reset_index()
    return prepped_transactions


def create_analysis_dfs(payload):
    labeled_transactions = pd.DataFrame(payload["labeled_transactions"])
    balance_df = pd.DataFrame(payload["balance_df"])
    labeled_transactions["date"] = pd.to_datetime(labeled_transactions["date"]).dt.date
    balance_df["currentBalanceDate"] = pd.to_datetime(balance_df["currentBalanceDate"]).dt.date
    return labeled_transactions, balance_df
