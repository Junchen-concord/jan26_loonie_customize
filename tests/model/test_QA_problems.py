import json
import os

import pandas as pd
from config import config
from model.run_model import run_model

test_model_crash_jsons = [
    "model_crush_8K0S1W.json",
    "model_crush_empty_trans.json",
]
test_income_source_jsons = ["income_source_07LNEQ.json"]
test_general_output_field_jsons = [
    "output_check_575.json",
    "output_check_127332.json",
    "output_check_131507.json",
    "output_check_138115.json",
    "output_check_dasd.json",
]

expected_income_sources = {
    "income_source_07LNEQ.json": [{"sourceName": "Tpusa Inc Direct Deposit", "frequency": "None"}]
}

# expected_fields = {'output_check_575.json': {"summaryInfo": {'recurringMonthlyIncome': [0]}, 'atpFeatures': {
#     'good_days_to_debit_by_peak_500': [6]}},
#     'output_check_127332.json': {"summaryInfo": {'recurringMonthlyIncome': [5193.35]}, 'atpFeatures':
#                                                 {'good_days_to_debit_by_peak_500': [155]}},
#     'output_check_131507.json': {"summaryInfo": {'recurringMonthlyIncome': [3877.6]}, 'atpFeatures': {
#         'good_days_to_debit_by_peak_500': [42]}},
#     'output_check_138115.json': {"summaryInfo": {'recurringMonthlyIncome': [2212.15, 0, 0, 0]}, 'atpFeatures': {
#         'good_days_to_debit_by_peak_500': [47, 16, 24, 0]}},
#     'output_check_dasd.json': {"summaryInfo": {'recurringMonthlyIncome': [0]}, 'atpFeatures': {
#         'good_days_to_debit_by_peak_500': [84]}}}

expected_fields = {
    "output_check_575.json": {"summaryInfo": {"recurringMonthlyIncome": [0]}},
    "output_check_127332.json": {"summaryInfo": {"recurringMonthlyIncome": [5181.54]}},
    "output_check_131507.json": {"summaryInfo": {"recurringMonthlyIncome": [4005.1]}},
    "output_check_138115.json": {"summaryInfo": {"recurringMonthlyIncome": [2212.15, 0, 0, 0]}},
    "output_check_dasd.json": {"summaryInfo": {"recurringMonthlyIncome": [4452.08]}},
}

# Make previous test files work after the as of data change


def asOfDate_compatible(json_str):
    data = json.loads(json_str)
    if "asOfDate" not in data:
        transactions_df = pd.DataFrame.from_dict(data["transactions"])
        # New feature as of date
        transactions_df[config.IA_DATE] = pd.to_datetime(transactions_df[config.IA_DATE]).dt.date
        asOfDate = str(transactions_df[config.IA_DATE].max())
        data["asOfDate"] = asOfDate
    return json.dumps(data)


# Run previous jsons for model crashes
def test_model_crashes():
    for data_path in test_model_crash_jsons:
        abs_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", data_path))
        with open(abs_path) as f:
            json_str = f.read()
        json_str = asOfDate_compatible(json_str)
        output = run_model(json_str)
        output_dict = json.loads(output)
        assert output_dict["runError"] == 401


# Run QA cases where income is not found
def test_capturing_income_source_correctly():
    for data_path in test_income_source_jsons:
        abs_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", data_path))
        with open(abs_path) as f:
            json_str = f.read()
        json_str = asOfDate_compatible(json_str)
        output = run_model(json_str)
        income_source = pd.DataFrame.from_dict(json.loads(output)["incomeSources"])
        data_expected_incomes = expected_income_sources[data_path]
        for data_expected_income in data_expected_incomes:
            related_income_source = income_source[income_source.sourceName == data_expected_income["sourceName"]]
            assert len(related_income_source) > 0
            for key, value in data_expected_income.items():
                assert value in income_source.loc[:, key].iloc[0] == value


# Check certain field (red zone, active income etc.) displaying correctly
def test_general_output_field():
    for data_path in test_general_output_field_jsons:
        abs_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", data_path))
        with open(abs_path) as f:
            json_str = f.read()
        json_str = asOfDate_compatible(json_str)
        output = json.loads(run_model(json_str))
        expected_field_dict = expected_fields[data_path]
        for key in expected_field_dict.keys():
            output_section = pd.DataFrame.from_dict(output[key])
            for sub_key, sub_value in expected_field_dict[key].items():
                assert list(output_section.loc[:, sub_key]) == sub_value
