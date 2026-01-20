import json
import os

from config import config

data_path_1000 = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", "1000.json"))
v1_label_change_path = os.path.realpath(
    os.path.join(config.ROOT_DIR, "..", "tests", "api", "payloads", "v1-label-change-payload.json")
)
with open(data_path_1000, encoding="utf-8-sig") as fp:
    input_payload = json.load(fp)
with open(v1_label_change_path, encoding="utf-8-sig") as fp:
    v1_label_change_payload = json.load(fp)


def test_model_v2_label(client):
    str_payload = {"input": json.dumps(input_payload)}
    response = client.post("/model/v2/label", json=str_payload)
    assert response.status_code == 200
    response_dict = response.json
    assert len(response_dict.keys()) == 1
    assert "labeledTransactions" in response_dict.keys()
