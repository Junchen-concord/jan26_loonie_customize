# TODO: Enable this test when Redis DB is set up


# import os
# import pandas as pd
# import json
# from config import config
# from labeling.knowledgebase.redis_knowledgebase import RedisKnowledgeBase

# redis_knowledge_base = RedisKnowledgeBase(None)


# sample_data_path = os.path.realpath(
#     os.path.join(config.ROOT_DIR, "..", "tests", "data", "sample_input_knowledgebase.csv")
# )


# def test_Redis_connection():
#     assert redis_knowledge_base is not None


# def test_input_and_get_from_redis():
#     df = pd.read_csv(sample_data_path)
#     df["WHAT"] = df["WHY"]
#     # Set some key here, and a time to live, so that it goes out of KB automatically
#     # boardwalk audi = WHO
#     key = json.dumps(["CREDIT", "boardwalk audi"])
#     redis_knowledge_base.redis_client.set(name=key, value="payroll", ex=200)
#     output = redis_knowledge_base.knowledge_base_prediction(df)
#     assert all(
#         output.loc[output["WHO"] == "boardwalk audi", "StackingPrediction"] == "payroll"
#     ), "There are rows where WHO is 'boardwalk audi' but StackingPrediction is not 'payroll'"
#     print("Assertion passed: All 'boardwalk audi' rows have 'payroll' as the StackingPrediction.")
#     assert all(
#         output.loc[output["WHO"] == "boardwalk audi", config.FROM_MODEL] == "RedisKnowledgeBase"
#     ), "There are rows where WHO is 'boardwalk audi' but fromModel is not 'RedisKnowledgeBase'"
#     print("Assertion passed: All 'boardwalk audi' rows have 'RedisKnowledgeBase' as the fromModel.")
