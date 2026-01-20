import json
import os

from api.transformations.transform_key_by_account import key_by_account
from config import config
from model.run_model import run_model

input_data_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", "2000.json"))


def test_create_v2_output():
    with open(input_data_path, "r") as fp:
        data = json.load(fp)
    output = run_model(json.dumps(data))
    output_json = json.loads(output)
    streamlined_output = key_by_account(output_json)

    list_fields = ["incomeSources", "loanSources", "overdraftIncidents", "creditTrans", "debitTrans"]
    score_types = ["redZone", "repeat", "loanPaidOff", "isBad"]
    dict_fields = ["summary", "majorIncomeSource", "cashflow", "lendingGuide"]

    def validate_account_guid_in_list(account, field_name, records):
        for record in records:
            assert (
                record["accountGuid"] == account
            ), f"Record in {field_name} {record} has mismatched accountGuid for account {account}"

    def validate_account_guid_in_dict(account, field_name, record):
        if record:
            assert (
                record["accountGuid"] == account
            ), f"Record in {field_name} {record} has mismatched accountGuid for account {account}"

    for account, account_data in streamlined_output["accountInfo"].items():
        # Test list fields
        for field in list_fields:
            field_records = account_data.get(field, [])
            validate_account_guid_in_list(account, field, field_records)

        # Test dict fields
        for field in dict_fields:
            field_record = account_data.get(field, {})
            validate_account_guid_in_dict(account, field, field_record)

        score_data = account_data.get("scores", {})

        # Test scores field
        for score in score_types:
            model_reasons_list = score_data.get(score, {}).get("modelReasons", [])
            validate_account_guid_in_list(account, score, model_reasons_list)
