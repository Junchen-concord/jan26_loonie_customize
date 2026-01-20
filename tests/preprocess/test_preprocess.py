from labeling.preprocessing.preprocess import (
    clean_description_clustering,
    clean_description_n_gram,
    find_payroll,
    group_transactions,
    remove_duplicates,
)
from preprocess_data import PreProcessTestData


def test_clean_description_n_gram():
    description1 = "Deposit-ACH-20199 zirtue (2AQ7NP"
    description2 = "POS Deposit  Cash App*Cash Out  San Francisco  CAUS"
    description3 = "Deposit-ACH-13199 COMMONSPIRIT H"
    description4 = "Transfer 808257 1 Funds Transfer"
    assert clean_description_n_gram(description1) == "deposit ach LongDigits zirtue 2aq7np"
    assert clean_description_n_gram(description2) == "pos deposit cash app cash out san francisco caus"
    assert clean_description_n_gram(description3) == "deposit ach LongDigits commonspirit"
    assert clean_description_n_gram(description4) == "transfer LongDigits funds transfer"


def test_clean_description_clustering():
    description1 = "deposit ach LongDigits zirtue 2aq7np"
    description2 = "pos deposit cash app cash out san CITYABBR caus"
    description3 = "deposit ach LongDigits commonspirit"
    description4 = "transfer LongDigits funds transfer"
    assert clean_description_clustering(description1) == "zirtue 2aq7np"
    assert clean_description_clustering(description2) == "cash out caus"
    assert clean_description_clustering(description3) == "commonspirit"
    assert clean_description_clustering(description4) == "transfer LongDigits funds transfer"


def test_remove_duplicates():
    description1 = "deposit deposit ACH credit"
    description2 = "Zelle payment from QP- Zelle"
    description3 = "Deposit  @ NetBranch  Trace #139"
    assert remove_duplicates(description1) == "deposit ACH credit"
    assert remove_duplicates(description2) == "Zelle payment from QP-"
    assert remove_duplicates(description3) == "Deposit @ NetBranch Trace #139"


def test_find_payroll():
    description1 = "deposit ACH credit"
    description2 = "AYX Payroll - 9/29/23"
    description3 = "Deposit  @ NetBranch  Trace #139"
    description4 = "salary bonus payment"
    description5 = "UBREATS paycheck"
    description6 = "company payrol"
    assert find_payroll(description1) == "deposit ACH credit"
    assert find_payroll(description2) == "AYX Payroll - 9/29/23"
    assert find_payroll(description3) == "Deposit @ NetBranch Trace #139"
    assert find_payroll(description4) == "payroll bonus payment"
    assert find_payroll(description5) == "UBREATS payroll"
    assert find_payroll(description6) == "company payroll"


def test_group_transactions():
    transactions_df = PreProcessTestData().transactions_df
    assert len(transactions_df.columns) == 8
    assert "cluster_label" not in transactions_df.columns
    grouped_df = group_transactions(transactions_df, "original_description", 0.3)
    assert len(grouped_df.columns) == 9
    assert "cluster_label" in grouped_df.columns


def test_find_loan():
    description1 = "loan ACH credit"
    description2 = "payment for mortgage - 9/29/23"
    description3 = "duplicate duplicate cashlen"
    description4 = "Withdrawal cashlen"
    description5 = "Deposit  @ NetBranch  Trace #139"
    assert find_payroll(description1) == "loan ACH credit"
    assert find_payroll(description2) == "payment for mortgage - 9/29/23"
    assert find_payroll(description3) == "duplicate duplicate cashlen"
    assert find_payroll(description4) == "Withdrawal cashlen"
    assert find_payroll(description5) == "Deposit @ NetBranch Trace #139"
