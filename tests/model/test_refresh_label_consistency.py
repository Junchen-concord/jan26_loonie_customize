import json
import os

import numpy as np
import pandas as pd

from config import config
from model.run_model import run_model

data_path_1000 = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", "1000.json"))


def test_label_consistency():
    with open(data_path_1000, "r") as fp:
        data = json.load(fp)

    # add a guid to match the transactions
    transactions_df = pd.DataFrame.from_dict(data["transactions"])
    transactions_df.loc[:, "guid"] = transactions_df.index
    # transactions_df.loc[:, "accountGuid"] = "1234"
    dict = transactions_df.to_dict(orient="index")
    data["transactions"] = [i for i in dict.values()]

    # expected output of the whole json run
    output = run_model(json.dumps(data))
    assert bool(output)
    output = json.loads(output)

    # format schema of output into the format of input
    credit_trans = pd.DataFrame.from_dict(output["creditTrans"])
    debit_trans = pd.DataFrame.from_dict(output["debitTrans"])

    # Ensure dataframes are not empty before concatenation to avoid warning
    frames_to_concat = []
    if not credit_trans.empty:
        frames_to_concat.append(credit_trans)
    if not debit_trans.empty:
        frames_to_concat.append(debit_trans)
        
    labeled_transactions = pd.concat(frames_to_concat, axis=0).reset_index(drop=True)
    
    # Create a mapping dictionary for category to name
    category_mapping = {
        0: "other",
        1: "payroll",
        2: "benefit",
        3: "transfer",
        4: "transfer",
        5: "gig",
        6: "loan"
    }
    
    # Use map function instead of chained assignments to avoid SettingWithCopyWarning
    labeled_transactions["StackingPrediction"] = labeled_transactions["transCategory"].map(
        lambda x: category_mapping.get(x, None)
    )

    labeled_transactions = labeled_transactions.rename(
        columns={
            "transGuid": "guid",
            "who": "WHO",
            "how": "HOW",
            "what": "WHAT",
            "whoCat": "WHO_cat",
            "sourceName": "description",
            "description": "originalDescription",
            "ibvCategory": "category",
        }
    )
    labeled_transactions = labeled_transactions[
        [
            "accountGuid",
            "guid",
            "description",
            "originalDescription",
            "amount",
            "type",
            "date",
            "category",
            "StackingPrediction",
            "WHO",
            "HOW",
            "WHAT",
            "WHO_cat",
        ]
    ]

    # remove the predicted categories of last 15 days
    labeled_transactions.loc[labeled_transactions.date >= "2024-03-10", "StackingPrediction"] = None

    new_data = data
    dict = labeled_transactions.to_dict(orient="index")
    new_data["transactions"] = [i for i in dict.values()]

    # expected output of the refresh run
    refresh_output = run_model(json.dumps(new_data))
    assert bool(refresh_output)
    refresh_output = json.loads(refresh_output)

    # compare outputs
    # Note that this might no longer holds if we want to change the refresh relabeling logic that takes into account of frequency per cluster in the future
    # Will likely need rework once new knowledgebase is ready
    credit_trans = pd.DataFrame.from_dict(output["creditTrans"])
    debit_trans = pd.DataFrame.from_dict(output["debitTrans"])
    # Ensure dataframes are not empty before concatenation to avoid warning
    frames_to_concat = []
    if not credit_trans.empty:
        frames_to_concat.append(credit_trans)
    if not debit_trans.empty:
        frames_to_concat.append(debit_trans)
        
    transactions_original = pd.concat(frames_to_concat, axis=0).reset_index(drop=True)

    credit_trans_refresh = pd.DataFrame.from_dict(refresh_output["creditTrans"])
    debit_trans_refresh = pd.DataFrame.from_dict(refresh_output["debitTrans"])
    
    # Ensure dataframes are not empty before concatenation
    frames_to_concat_refresh = []
    if not credit_trans_refresh.empty:
        frames_to_concat_refresh.append(credit_trans_refresh)
    if not debit_trans_refresh.empty:
        frames_to_concat_refresh.append(debit_trans_refresh)
        
    transactions_relabeled = pd.concat(frames_to_concat_refresh, axis=0).reset_index(drop=True)

    transactions_relabeled = transactions_relabeled.sort_values("transGuid").reset_index()
    transactions_original = transactions_original.sort_values("transGuid").reset_index()

    assert len(transactions_relabeled) == len(transactions_original)
    # after careful debugging, there will be a few (5 in this test) new transactions labeled differently by the xgboost (labeling model) because the frequency and
    # vocabulary of n gram changed, results in slight inconsistency, but overall it will be consistent.
    assert (
        np.sum(transactions_original.transCategory == transactions_relabeled.transCategory) / len(transactions_original)
        >= 0.99
    )
