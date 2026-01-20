import json
import os

import pytest

from config import config


@pytest.fixture
def api_client(client):
    """Provides a helper function for making API calls."""

    def _post_request(endpoint, payload):
        return client.post(endpoint, json=payload)

    return _post_request


@pytest.mark.parametrize(
    "payload_file",
    [
        ("agent-label.json"),
        ("agent-label-2.json"),
    ],
)
def test_model_v2_agentLabel(api_client, payload_file):
    data_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "api", "payloads", payload_file))
    with open(data_path, encoding="utf-8-sig") as fp:
        json_payload = json.load(fp)
    response = api_client("/model/v2/analyze", json_payload)
    assert response.status_code == 200
    response_dict = response.json
    all_trans = response_dict["transactions"]
    assert any(trans.get("fromModel") == "LiveAgentEdit" for trans in all_trans)
    if payload_file == "agent-label.json":
        for trans in all_trans:
            if trans["transGuid"] == "3exN7KMVQLsEZVvZ00ywF90oBZ9J7wi0E8eDw":
                assert trans["stackingPrediction"] == "transfer"
                assert trans["incomeType"] == 3
