import json
import os

from config import config
from model.run_model import run_model

test_file_with_app_data = os.path.realpath(
    os.path.join(
        config.ROOT_DIR, "..", "tests", "data", "application_checker", "application_checker_unit_test_with_data.json"
    )
)
test_file_with_empty_app_data = os.path.realpath(
    os.path.join(
        config.ROOT_DIR, "..", "tests", "data", "application_checker", "application_checker_unit_test_no_data.json"
    )
)

test_file_auth_info_blank = os.path.realpath(
    os.path.join(
        config.ROOT_DIR, "..", "tests", "data", "application_checker", "application_checker_unit_test_empty_data.json"
    )
)


# Test with applicationInformation: {} and IBVAuth with data.


def test_auth_info_blank():
    with open(test_file_auth_info_blank, "r") as fp:
        data = json.load(fp)
    output = run_model(json.dumps(data))
    assert bool(output)
    output_json = json.loads(output)
    assert "ApplicationChecker" not in output_json


def test_check_application_with_data():
    with open(test_file_with_app_data, "r") as fp:
        data = json.load(fp)
    output = run_model(json.dumps(data))
    assert bool(output)
    output_json = json.loads(output)
    app_verification_result = output_json["ApplicationChecker"]["appVerificationResult"]
    assert app_verification_result["appFrequencyMatch"] == 1
    assert app_verification_result["appFrequencyMatchBS"] == 1
    assert app_verification_result["IBVSuggestsInconsistent"] == 0
    assert app_verification_result["IBVSuggestsBiweekly"]
    assert not app_verification_result["IBVSuggestsWeekly"]
    assert not app_verification_result["IBVSuggestsSemiMonthly"]
    assert not app_verification_result["IBVSuggestsMonthly"]
    assert app_verification_result["IBVSuggestsBS"]
    assert app_verification_result["appPaydayMatch"] == 0
    assert app_verification_result["IBVMonthlyIncome"] == 627.46
    assert int(app_verification_result["reportedIncomeMinusActiveIncome"]) == 4789
    assert round(app_verification_result["requestedAmountRatio"], 2) == 0.80
    assert app_verification_result["fnameMatchRate"] == 100
    assert app_verification_result["lnameMatchRate"] == 100
    assert not app_verification_result["IBVFromChase"]
    assert not app_verification_result["appFromChase"]
    assert app_verification_result["accountNumberMatch"]
    assert app_verification_result["accountNumberLastFourMatchAuth"]
    assert app_verification_result["accountNumberFirstFourMatchAuth"]
    assert app_verification_result["routingNumberMatch"]
    assert app_verification_result["cityMatch"]
    assert app_verification_result["stateMatch"]
    assert app_verification_result["zipMatch"]
    assert app_verification_result["phoneMatch"]
    assert app_verification_result["emailMatch"]
    assert app_verification_result["fnameInTransactions"]
    assert app_verification_result["lnameInTransactions"]
    assert app_verification_result["accountNumberInTransactions"]
    assert app_verification_result["cityInTransactions"]
    assert app_verification_result["stateInTransactions"]
    assert app_verification_result["zipInTransactions"]

    model_score = output_json["ApplicationChecker"]["agentWithdrawnModel"]["score"]
    assert int(model_score) == 36


def test_check_application_with_no_data():
    with open(test_file_with_empty_app_data, "r") as fp:
        data = json.load(fp)
    output = run_model(json.dumps(data))
    assert bool(output)
    output_json = json.loads(output)
    app_verification_result = output_json["ApplicationChecker"]["appVerificationResult"]
    assert app_verification_result["appFrequencyMatch"] == 1
    assert app_verification_result["appFrequencyMatchBS"] == 1
    assert app_verification_result["IBVSuggestsInconsistent"] == 0
    assert app_verification_result["IBVSuggestsBiweekly"]
    assert not app_verification_result["IBVSuggestsWeekly"]
    assert not app_verification_result["IBVSuggestsSemiMonthly"]
    assert not app_verification_result["IBVSuggestsMonthly"]
    assert app_verification_result["IBVSuggestsBS"]
    assert app_verification_result["appPaydayMatch"] == 0
    assert app_verification_result["IBVMonthlyIncome"] == 627.46
    assert int(app_verification_result["reportedIncomeMinusActiveIncome"]) == 4789
    assert round(app_verification_result["requestedAmountRatio"], 2) == 0.80
    assert app_verification_result["fnameMatchRate"] is None
    assert app_verification_result["lnameMatchRate"] is None
    assert app_verification_result["IBVFromChase"] is None
    assert app_verification_result["appFromChase"] is None
    assert app_verification_result["accountNumberMatch"]
    assert app_verification_result["accountNumberLastFourMatchAuth"] is None
    assert app_verification_result["accountNumberFirstFourMatchAuth"] is None
    assert app_verification_result["routingNumberMatch"] is None
    assert app_verification_result["cityMatch"]
    assert app_verification_result["stateMatch"]
    assert app_verification_result["zipMatch"]
    assert app_verification_result["phoneMatch"] is None
    assert app_verification_result["emailMatch"] is None
    assert app_verification_result["fnameInTransactions"]
    assert app_verification_result["lnameInTransactions"]
    assert app_verification_result["accountNumberInTransactions"]
    assert app_verification_result["cityInTransactions"]
    assert app_verification_result["stateInTransactions"]
    assert app_verification_result["zipInTransactions"]
