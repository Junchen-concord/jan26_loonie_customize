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


@pytest.mark.parametrize(
    "payload_file",
    [
        ("343167_S.json"),
        ("343183_B.json"),
        ("343191_B.json"),
        ("343224_B.json"),
        ("343230_M.json"),
        ("343232_S.json"),
        ("343238_M.json"),
    ],
)
def test_v3_model_analyze_regular_payday_files(fastapi_api_client, payload_file):
    """Test FastAPI v3 model analyze endpoint with regular payday test files."""
    data_path = os.path.realpath(
        os.path.join(
            config.ROOT_DIR, "..", "tests", "data", "application_checker", "regular_payday_test_files", payload_file
        )
    )

    with open(data_path, "r", encoding="utf-8-sig") as f:
        json_payload = json.load(f)

    response = fastapi_api_client["post"]("/model/v3/analyze", json_payload)

    assert response.status_code == 200, f"Failed for payload file: {payload_file}"


@pytest.mark.parametrize(
    "payload_file, expected_value",
    [
        ("343147_M.json", ["Tuesday in Week 3"]),
        ("343155_S.json", ["10,25", "3,17"]),
        ("343179_M.json", ["3"]),
        ("343232_B.json", ["Friday"]),
    ],
)
def test_regular_payday_ouptut(fastapi_api_client, payload_file, expected_value):
    """Test FastAPI v3 model analyze endpoint with regular payday test files."""
    data_path = os.path.realpath(
        os.path.join(
            config.ROOT_DIR, "..", "tests", "data", "application_checker", "regular_payday_test_files", payload_file
        )
    )

    with open(data_path, "r", encoding="utf-8-sig") as f:
        json_payload = json.load(f)

    response = fastapi_api_client["post"]("/model/v3/analyze", json_payload)

    assert response.status_code == 200, f"Failed for payload file: {payload_file}"

    response_json = response.json()

    accounts = response_json["accounts"]
    regular_pay_days = []
    for account in accounts:
        income_sources = account["incomeSources"]
        for source in income_sources:
            pay_day = source["regularPayDay"]
            if pay_day != "None":
                regular_pay_days.append(pay_day)

    for value in expected_value:
        assert value in regular_pay_days, (
            f"For {payload_file}, expected {value} for regularPayDay"
            f"to be found in regular pay days: {regular_pay_days}"
        )
