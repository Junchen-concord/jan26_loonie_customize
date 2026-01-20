# import json
# import os

# import pytest
# from config import config


# @pytest.fixture
# def api_client(client):
#     """Provides a helper function for making API calls."""

#     def _post_request(endpoint, payload):
#         return client.post(endpoint, json=payload)

#     return _post_request


# APPLICATION_CHECKER_PAYLOADS = [
#     "318698.json",
#     "318703.json",
#     "318731.json",
# ]


# @pytest.fixture(autouse=True)
# def enable_redis_kb(monkeypatch):
#     monkeypatch.setenv("REDIS_KB_ENABLED", "true")

#     redis_env = {
#         "REDIS_HOST": os.getenv("REDIS_HOST"),
#         "REDIS_PORT": os.getenv("REDIS_PORT"),
#     }

#     missing_required = [key for key, value in redis_env.items() if not value]
#     if missing_required:
#         pytest.skip(
#             "Redis KB credentials missing (set TEST_REDIS_* env vars to run this test)",
#             allow_module_level=True,
#         )

#     yield


# @pytest.mark.parametrize("payload_file", APPLICATION_CHECKER_PAYLOADS)
# def test_redis_kb_labels_transactions(api_client, payload_file):
#     data_path = os.path.realpath(
#         os.path.join(config.ROOT_DIR, "..", "tests", "data", "application_checker", payload_file)
#     )
#     with open(data_path, "r", encoding="utf-8-sig") as data_file:
#         raw_input = json.load(data_file)

#     request_payload = {"input": json.dumps(raw_input)}
#     response = api_client("/model/v2/analyze", request_payload)
#     assert response.status_code == 200

#     transactions = response.json["transactions"]
#     assert any(transaction.get("fromModel") == "RedisKnowledgeBase" for transaction in transactions)
