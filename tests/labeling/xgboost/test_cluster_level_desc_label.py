import json

import pandas as pd

from labeling.xgboost.analyzer_features import IAFeatures

data = {
    "processed_n_gram": [
        "loan payment",
        "cash advance",
        "salary deposit",
        "venmo transfer",
        "credit score",
        "direct deposit",
        "mtg payment",
        "bank transfer",
        "payroll processing",
        "car loan",
    ],
    "type": ["CREDIT", "DEBIT", "CREDIT", "DEBIT", "CREDIT", "DEBIT", "CREDIT", "DEBIT", "CREDIT", "DEBIT"],
    "WHO": [None, "ORG", "Person", "None", "Person", "ORG", None, "Person", "ORG", "None"],
    "HOW": ["Online", "Branch", None, "Mobile", "ATM", "Online", "Branch", None, "ATM", "Mobile"],
    "WHAT": ["Loan", "Finance", None, "Transfer", "Credit", "Salary", "Mortgage", "Bank", "Payroll", "Car loan"],
    "target_col": ["Finance", "Loan", "Credit", "Transfer", "Credit", "Loan", "Finance", "Bank", "Salary", "Loan"],
}

cluster_output = [
    {
        "HOW": "Online Branch Mobile ATM",
        "WHO": "ORG Person",
        "WHY": "Loan Finance Transfer Credit Salary Mortgage Bank Payroll Car loan",
        "has_strong_loan_indicators": False,
        "has_semi_loan_indicators": False,
        "has_weak_loan_indicators": False,
        "has_strong_payroll_indicators": False,
        "has_strong_transfer_indicators": False,
        "has_bank_transfer_indicators": False,
        "has_semi_transfer_indicators": False,
        "has_who": True,
        "has_who_org": False,
        "has_who_person": False,
        "target_col": "Finance",
    }
]


def test_cluster_level_desc_label():
    df_cluster = pd.DataFrame(data)
    target_col = "target_col"
    original_output = IAFeatures.cluster_level_desc_label(df_cluster, target_col)
    original_output_json = original_output.to_json(orient="records")
    expected_output_json = json.dumps(cluster_output, sort_keys=True)
    original_output_json_sorted = json.dumps(json.loads(original_output_json), sort_keys=True)

    assert expected_output_json == original_output_json_sorted
