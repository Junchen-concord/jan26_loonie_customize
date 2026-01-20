import json
import os

import pandas as pd
from config import config
from errors import error_1_json
from list_equals_check import check_lists_equal
from model.run_model import run_model

sample_data_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", "2000.json"))
data_path_1000 = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", "1000.json"))
data_path_single_account = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", "accountGuid575.json"))


def test_run_model_2000():
    with open(sample_data_path, "r") as fp:
        data = json.load(fp)
    output = run_model(json.dumps(data))
    assert bool(output)
    output_json = json.loads(output)
    actual_output_fields = list(output_json.keys())
    recommend_account = output_json["additionalInfo"]["recommendedBankAccount"]
    redzone_behavior = output_json["additionalInfo"]["redZoneBehaviorCustomer"][0]
    scores = output_json["scores"]
    # Red Zone
    assert pd.DataFrame.from_dict(scores["redZone"]["accountLevel"]["modelScore"]).riskScore.max() == 261
    assert scores["redZone"]["customerLevel"]["modelScore"][0]["riskScore"] == 253
    # Repeat
    assert pd.DataFrame.from_dict(scores["repeat"]["accountLevel"]["modelScore"]).repeatScore.max() == 141
    assert scores["repeat"]["customerLevel"]["modelScore"][0]["repeatScore"] == 131
    # Loan Paid Off
    assert (
        pd.DataFrame.from_dict(scores["loanPaidOff"]["accountLevel"]["modelScore"]).totalLoanPaidOffScore.max() == 238
    )
    assert scores["loanPaidOff"]["customerLevel"]["modelScore"][0]["totalLoanPaidOffScore"] == 221
    # IsBad
    assert pd.DataFrame.from_dict(scores["isBad"]["accountLevel"]["modelScore"]).isBadScore.max() == 213
    assert scores["isBad"]["customerLevel"]["modelScore"][0]["isBadScore"] == 202
    risk_score = redzone_behavior["riskScore"]
    # account_guid = redzone_behavior["accountGuid"]
    expected_output_fields = [
        "summaryInfo",
        "incomeSources",
        "loanSources",
        "overdraftIncidents",
        "overdraftFeeIncidents",
        "nsfFeeIncidents",
        "cashFlow",
        "majorIncomeSource",
        "creditTrans",
        "debitTrans",
        "additionalInfo",
        "modelVersion",
        "lendingGuide",
        "accounts",
        "scores",
    ]
    assert recommend_account == "yx3EvQLkOjhPZD7ZKKpytynr9dMdOJfr4OomM"
    assert risk_score == 253
    assert check_lists_equal(expected_output_fields, actual_output_fields)


def test_run_model_1000():
    with open(data_path_1000, "r") as fp:
        data = json.load(fp)
    output = run_model(json.dumps(data))
    assert bool(output)
    output_json = json.loads(output)
    recommend_account = output_json["additionalInfo"]["recommendedBankAccount"]
    redzone_behavior = output_json["additionalInfo"]["redZoneBehaviorCustomer"][0]
    scores = output_json["scores"]
    # Red Zone
    assert pd.DataFrame.from_dict(scores["redZone"]["accountLevel"]["modelScore"]).riskScore.max() == 233
    assert scores["redZone"]["customerLevel"]["modelScore"][0]["riskScore"] == 133
    # Repeat
    assert pd.DataFrame.from_dict(scores["repeat"]["accountLevel"]["modelScore"]).repeatScore.max() == 133
    assert scores["repeat"]["customerLevel"]["modelScore"][0]["repeatScore"] == 127
    # Loan Paid Off
    assert (
        pd.DataFrame.from_dict(scores["loanPaidOff"]["accountLevel"]["modelScore"]).totalLoanPaidOffScore.max() == 101
    )
    assert scores["loanPaidOff"]["customerLevel"]["modelScore"][0]["totalLoanPaidOffScore"] == 58
    # IsBad
    assert pd.DataFrame.from_dict(scores["isBad"]["accountLevel"]["modelScore"]).isBadScore.max() == 116
    assert scores["isBad"]["customerLevel"]["modelScore"][0]["isBadScore"] == 64
    risk_score = redzone_behavior["riskScore"]
    # account_guid = redzone_behavior["accountGuid"]
    assert recommend_account == "6538dd3b-1c1d-484c-abb8-4525ed3ac779"
    # assert account_guid == "3d15c341-d4dc-4624-8a76-2f6cddc28a33"
    assert risk_score == 133

    # This is a Chirp account btw

    assert "creditTrans" in output_json, "'creditTrans' key is missing from output_json"
    assert "debitTrans" in output_json, "'debitTrans' key is missing from output_json"

    def assert_columns_exist(transactions, required_columns):
        for transaction in transactions:
            for column in required_columns:
                assert column in transaction, f"'{column}' is missing in a transaction."
        print("All cols exist")

    required_columns = [
        "accountGuid",
        "transGuid",
        "sourceName",
        "description",
        "date",
        "amount",
        "transCategory",
        "clusterLabel",
        "who",
        "how",
        "what",
        "fromModel",
        "type",
        "dayOfWeek",
        "sourceID",
        "ibvCategory",
    ]

    assert_columns_exist(output_json["creditTrans"], required_columns)
    assert_columns_exist(output_json["debitTrans"], required_columns)


def test_run_model_single_account():
    # test function to make sure single account inputs has the same schema as multiple account inputs
    with open(data_path_single_account, "r") as fp:
        data = json.load(fp)
    output = run_model(json.dumps(data))
    output_json = json.loads(output)
    actual_output_fields = list(output_json.keys())
    expected_output_fields = [
        "summaryInfo",
        "incomeSources",
        "loanSources",
        "overdraftIncidents",
        "overdraftFeeIncidents",
        "nsfFeeIncidents",
        "cashFlow",
        "majorIncomeSource",
        "creditTrans",
        "debitTrans",
        "additionalInfo",
        "modelVersion",
        "lendingGuide",
        "accounts",
        "scores",
    ]
    assert check_lists_equal(expected_output_fields, actual_output_fields)
    scores = output_json["scores"]
    for value in scores.values():
        assert "accountLevel" in value.keys()
        assert "customerLevel" in value.keys()


def test_run_model_ignores_transactions_after_asOfDate():
    output = run_model(error_1_json)
    output_dict = json.loads(output)
    assert output_dict["runError"] == 401
    assert output_dict["summaryInfo"][0]["runMsg"] == "No transactions found in the given timeframe"


def test_run_model_errors_empty_json():
    empty_json = "{}"
    output = run_model(empty_json)
    output_dict = json.loads(output)
    assert output_dict["runError"] == 401


def test_run_model_errors_empty_string():
    output = run_model("")
    output_dict = json.loads(output)
    assert output_dict["runError"] == 501
