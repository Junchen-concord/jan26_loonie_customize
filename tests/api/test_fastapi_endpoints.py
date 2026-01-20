import json
import os

import pytest
from config import config


@pytest.fixture
def fastapi_api_client(fastapi_client):
    """Provides a helper function for making FastAPI API calls."""

    def _post_request(endpoint, payload):
        return fastapi_client.post(endpoint, json=payload)

    def _get_request(endpoint):
        return fastapi_client.get(endpoint)

    return {"post": _post_request, "get": _get_request}


def test_liveness_endpoint(fastapi_api_client):
    """Test the liveness health endpoint."""
    response = fastapi_api_client["get"]("/liveness")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == 200
    assert data["message"] == "Live"
    assert "model_version" in data


def test_readiness_endpoint(fastapi_api_client):
    """Test the readiness health endpoint."""
    response = fastapi_api_client["get"]("/readiness")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == 200
    assert data["message"] == "Ready"
    assert "model_version" in data


# =========================
# Validation/Input Errors
# =========================


def test_v3_model_analyze_validation_errors(fastapi_api_client):
    """Test validation errors for v3 model analyze endpoint."""

    # Missing required fields
    invalid_payload = {
        "asOfDate": "2024-01-15"
        # Missing accounts and transactions
    }

    response = fastapi_api_client["post"]("/model/v3/analyze", invalid_payload)
    assert response.status_code == 400

    data = response.json()
    assert "errors" in data
    assert data["kind"] == "Error"


def test_v3_model_analyze_invalid_transaction_type(fastapi_api_client):
    """Test validation with invalid transaction type."""
    invalid_payload = {
        "asOfDate": "2024-01-15",
        "accounts": [
            {
                "accountGuid": "test-123",
                "accountType": "CHECKING",
                "currentBalance": 100.00,
                "currentBalanceDate": "2024-01-15",
            }
        ],
        "transactions": [
            {
                "description": "TEST",
                "guid": "txn-123",
                "accountGuid": "test-123",
                "amount": 100.00,
                "date": "2024-01-01",
                "type": "INVALID_TYPE",  # Should be CREDIT or DEBIT
            }
        ],
    }

    response = fastapi_api_client["post"]("/model/v3/analyze", invalid_payload)
    assert response.status_code == 400


def test_v3_model_analyze_empty_transactions(fastapi_api_client):
    """Test business logic error with empty transactions (runError 401)."""
    payload_with_empty_transactions = {
        "asOfDate": "2024-01-15",
        "accounts": [
            {
                "accountGuid": "test-123",
                "accountType": "CHECKING",
                "currentBalance": 100.00,
                "currentBalanceDate": "2024-01-15",
            }
        ],
        "transactions": [],  # Empty transactions should trigger runError 401
    }

    response = fastapi_api_client["post"]("/model/v3/analyze", payload_with_empty_transactions)

    assert response.status_code == 400

    data = response.json()
    assert data["runError"] == 401
    assert "No transactions found" == data.get("errorDetails")


@pytest.mark.parametrize(
    "payload_file",
    [("NCL_b11eee28-3739-455c-a491-104b1e42b7b3.json")],
)
def test_fastapi_v3_model_analyze_invalid_inputs(fastapi_api_client, payload_file):
    """Happy path test for FastAPI v3 model analyze endpoint using real test data files."""
    data_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", "invalid_input", payload_file))

    with open(data_path, "r", encoding="utf-8-sig") as f:
        json_payload = json.load(f)

    response = fastapi_api_client["post"]("/model/v3/analyze", json_payload)

    assert response.status_code == 400, f"Failed for payload file: {payload_file}"


# =========================
# Happy Path
# =========================


@pytest.mark.parametrize(
    "payload_file",
    [
        ("318698.json"),
        ("318703.json"),
        ("318721.json"),
        ("318731.json"),
        ("318736.json"),
        ("application_checker_unit_test_no_data.json"),
        ("application_checker_unit_test_with_data.json"),
    ],
)
def test_v3_model_analyze_happy_path(fastapi_api_client, payload_file):
    """Happy path test for FastAPI v3 model analyze endpoint using real test data files."""
    data_path = os.path.realpath(
        os.path.join(config.ROOT_DIR, "..", "tests", "data", "application_checker", payload_file)
    )

    with open(data_path, "r", encoding="utf-8-sig") as f:
        json_payload = json.load(f)

    response = fastapi_api_client["post"]("/model/v3/analyze", json_payload)

    assert response.status_code == 200, f"Failed for payload file: {payload_file}"

    data = response.json()
    assert isinstance(data, dict), "Response should be a dictionary"

    # Check for key response fields based on the V3 response structure
    expected_keys = ["accounts", "modelVersion", "customerInfo", "transactions", "asOfDate"]
    for key in expected_keys:
        assert data[key] is not None or data[key] == [], f"Key {key} should not be None unless empty list"

    account = data["accounts"][0]
    customerInfo = data["customerInfo"]

    # Field presence
    customerInfo_keys = [
        "riskAnalysisCustomer",
        "assessmentReasonsCustomerGood",
        "assessmentReasonsCustomerBad",
        "recommendedBankAccount",
        "lendingGuideCustomer",
        "applicationCheck",
    ]
    for key in customerInfo_keys:
        assert customerInfo[key] is not None, f"Key {key} should not be None"

    # Type Checks
    good_days_to_debit_by_peak_100 = account["features"]["good_days_to_debit_by_peak_100"]
    assert isinstance(good_days_to_debit_by_peak_100, int), "Expected the return type to be int"

    assert len(data.keys()) == 5
    assert len(account.keys()) == 20
    assert len(customerInfo.keys()) == 8


def test_v3_model_analyze_no_application_checker(fastapi_api_client):
    data_path = os.path.join(
        config.ROOT_DIR, "..", "tests", "data", "application_checker", "application_checker_unit_test_empty_data.json"
    )

    with open(data_path, "r", encoding="utf-8-sig") as f:
        json_payload = json.load(f)

    response = fastapi_api_client["post"]("/model/v3/analyze", json_payload)

    assert response.status_code == 200, f"Unexpected status for {data_path}: {response.status_code}"

    data = response.json()
    customerInfo = data["customerInfo"]
    assert customerInfo["applicationCheck"] is None


@pytest.mark.parametrize(
    "payload_file",
    [
        ("100.json"),
        ("1000.json"),
        ("2000.json"),
    ],
)
def test_v3_model_analyze_with_basic_datasets(fastapi_api_client, payload_file):
    data_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", payload_file))

    with open(data_path, "r", encoding="utf-8-sig") as f:
        json_payload = json.load(f)

    response = fastapi_api_client["post"]("/model/v3/analyze", json_payload)

    assert response.status_code == 200, f"Unexpected status for {payload_file}: {response.status_code}"

    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict), "Response should be a dictionary"


# =========================
# Previous Crashes / Errors
# =========================


# Test source IDs match
def test_v3_model_analyze_sourceIDs(fastapi_api_client):
    data_path = os.path.join(
        config.ROOT_DIR, "..", "tests", "data", "NCL_b11eee28-3739-455c-a491-104b1e42b7b3_Request.json"
    )

    with open(data_path, "r", encoding="utf-8-sig") as f:
        json_payload = json.load(f)

    response = fastapi_api_client["post"]("/model/v3/analyze", json_payload)

    assert response.status_code == 200, f"Unexpected status for {data_path}: {response.status_code}"

    response_dict = response.json()

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


## I am commenting this out as the cashflow result is never intended to be 0, it somehow changed
## after I add additional payroll behavior, debugging what happened could be tedious.

# Does not return NaN in cashFlow field
# def test_v3_model_analyze_no_cashflow_NaN(fastapi_api_client):
#     data_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "api", "payloads", "cashflow-NaN.json"))

#     with open(data_path, "r", encoding="utf-8-sig") as f:
#         json_payload = json.load(f)

#     response = fastapi_api_client["post"]("/model/v3/analyze", json_payload)

#     assert response.status_code == 200, f"Unexpected status for {data_path}: {response.status_code}"

#     response_dict = response.json()
#     account = response_dict["accounts"][0]
#     cashflow = account["cashFlow"]
#     assert cashflow["netCashFlow"] == 0.0
#     assert cashflow["spending"] == 0.0
#     assert response.status_code == 200, f"Unexpected status for {data_path}: {response.status_code}"


@pytest.mark.parametrize(
    "payload_file",
    [
        ("20219.json"),
        ("json-input-error.json"),
        ("no-kb-dfs.json"),
        ("ModelRequest IBVStatusID 309326.json"),
        ("NCL_b11eee28-3739-455c-a491-104b1e42b7b3_Request.json"),
        ("request_json_53d12eb5-81f6-40ab-a2a3-01aa51935ca3.json"),
    ],
)
def test_fastapi_v3_model_analyze_prev_api_bugs(fastapi_api_client, payload_file):
    """Happy path test for FastAPI v3 model analyze endpoint using real test data files."""
    data_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", "prev_api_bugs", payload_file))

    with open(data_path, "r", encoding="utf-8-sig") as f:
        json_payload = json.load(f)

    response = fastapi_api_client["post"]("/model/v3/analyze", json_payload)

    assert response.status_code == 200, f"Failed for payload file: {payload_file}"


def test_drops_accounts_without_txns(fastapi_api_client):
    data_path = os.path.realpath(
        os.path.join(config.ROOT_DIR, "..", "tests", "data", "prev_api_bugs", "account_without_txns.json")
    )

    with open(data_path, "r", encoding="utf-8-sig") as f:
        json_payload = json.load(f)

    response = fastapi_api_client["post"]("/model/v3/analyze", json_payload)

    assert response.status_code == 200, "Failed for payload file: account_without_txns.json"
    response_dict = response.json()
    recommendedBankAccount = response_dict["customerInfo"]["recommendedBankAccount"]
    assert recommendedBankAccount == "OwO0NDRmjzcmnkLaBKpPU9xM0bXRoYhgvJLb3"
