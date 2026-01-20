import json
import os

import pytest
from config import config
from model_analyze_payload import payload


@pytest.fixture
def api_client(client):
    """Provides a helper function for making API calls."""

    def _post_request(endpoint, payload):
        return client.post(endpoint, json=payload)

    return _post_request


def check_lists_equal(list_1: list, list_2: list) -> bool:
    """Check if two lists are equal."""
    return len(list_1) == len(list_2) and sorted(list_1) == sorted(list_2)


# runError cases
@pytest.mark.parametrize(
    "payload_file, expected_error_code, expected_error_details",
    [
        ("no-credit-transactions.json", 401, "No Credit Transactions"),
        # ("another-error-payload.json", 402, "Another Error Message"),  # Add more runError cases here
    ],
)
def test_v2_model_analyze_various_errors(api_client, payload_file, expected_error_code, expected_error_details):
    data_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "api", "payloads", payload_file))
    with open(data_path, "r", encoding="utf-8-sig") as f:
        error_payload = json.load(f)

    response = api_client("/model/v2/analyze", error_payload)
    assert response.status_code == 400
    assert response.json["errorDetails"] == expected_error_details
    assert response.json["runError"] == expected_error_code


ncl_data_path = os.path.realpath(
    os.path.join(config.ROOT_DIR, "..", "tests", "data", "NCL_b11eee28-3739-455c-a491-104b1e42b7b3_Request.json")
)
with open(ncl_data_path, encoding="utf-8-sig") as fp:
    ncl_input_payload = json.load(fp)


# Test source IDs - /v2/analyze
def test_v2_model_analyze_sourceIDs(api_client):
    str_payload = {"input": json.dumps(ncl_input_payload)}
    response = api_client("/model/v2/analyze", str_payload)
    assert response.status_code == 200
    response_dict = response.json
    account = response_dict["accounts"][0]
    loan_sources = account["loanSources"]
    source = next((item for item in loan_sources if item.get("lenderName") == "Brigit, Brigit via BRIGIT"), None)
    if source:
        sourceID = source["sourceID"]
        transactions = response_dict["transactions"]
        txn = next((item for item in transactions if item.get("id") == 252115), None)
        assert txn["sourceID"] == sourceID, "SourceIDs do not match"
    else:
        assert False, "Cannot find loan source with lenderName Brigit, Brigit, via BRIGIT"


# Happy path - /v2/analyze
def test_v2_model_analyze(api_client):
    response = api_client("/model/v2/analyze", payload)
    assert response.status_code == 200
    response_dict = response.json
    account = response_dict["accounts"][0]
    customer = response_dict["customerInfo"]
    good_days_to_debit_by_peak_100 = account["features"]["good_days_to_debit_by_peak_100"]
    assert isinstance(good_days_to_debit_by_peak_100, int), "Expected the return type to be int"
    assert "stackingPrediction" in response_dict["transactions"][0]
    assert len(response_dict.keys()) == 6
    assert len(account.keys()) == 20
    assert len(customer.keys()) == 7


@pytest.mark.parametrize(
    "payload_file",
    [
        ("318698.json"),
        ("318703.json"),
        ("318721.json"),
        ("318731.json"),
        ("318736.json"),
    ],
)
def test_application_checker_inputs(api_client, payload_file):
    data_path = os.path.realpath(
        os.path.join(config.ROOT_DIR, "..", "tests", "data", "application_checker", payload_file)
    )
    with open(data_path, "r", encoding="utf-8-sig") as f:
        raw_input = json.load(f)
    str_payload = {"input": json.dumps(raw_input)}
    response = api_client("/model/v2/analyze", str_payload)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "payload_file",
    [
        ("318698.json"),
        ("318703.json"),
        ("318721.json"),
        ("318731.json"),
        ("318736.json"),
    ],
)
def test_v3_model_analyze(api_client, payload_file):
    data_path = os.path.realpath(
        os.path.join(config.ROOT_DIR, "..", "tests", "data", "application_checker", payload_file)
    )
    with open(data_path, "r", encoding="utf-8-sig") as f:
        json_payload = json.load(f)
    response = api_client("/model/v3/analyze", json_payload)
    assert response.status_code == 200
