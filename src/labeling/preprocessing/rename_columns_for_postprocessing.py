import pandas as pd


def rename_columns_for_postprocessing(labeled_transactions: pd.DataFrame):
    labeled_transactions = labeled_transactions.rename(columns={"GUID": "guid"})
    labeled_transactions["cluster_label"] = labeled_transactions.cluster_label.astype(str)
    # # If StackingPrediction is already there, don't do this
    # (
    #     labeled_transactions[["StackingPrediction", "cluster_label"]]
    #     .applymap(lambda v: isinstance(v, str) or pd.isna(v))
    #     .all(axis=1)
    # )
    # print(labeled_transactions["StackingPrediction"])

    # labeled_transactions["cluster_label"] = labeled_transactions[["StackingPrediction", "cluster_label"]].agg(
    #     "_".join, axis=1
    # )

    cols = labeled_transactions[["StackingPrediction", "cluster_label"]].fillna("").astype(str)
    labeled_transactions["cluster_label"] = cols.agg("_".join, axis=1)

    return labeled_transactions
