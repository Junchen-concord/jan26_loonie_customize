import json
import os

from config import config

v2_transactions_analyze_path = os.path.realpath(
    os.path.join(config.ROOT_DIR, "..", "tests", "api", "payloads", "v2-transactions-analyze.json")
)
with open(v2_transactions_analyze_path, encoding="utf-8-sig") as fp:
    v2_transactions_analyze_payload = json.load(fp)


def test_model_v2_transactions_analyze(client):
    response = client.post("/model/v2/transactions/analyze", json=v2_transactions_analyze_payload)
    assert response.status_code == 200
    response_dict = response.json
    account = response_dict["accounts"][0]
    customer = response_dict["customerInfo"]
    assert len(response_dict.keys()) == 5
    assert len(account.keys()) == 18
    assert len(customer.keys()) == 5
