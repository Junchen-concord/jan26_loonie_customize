import pandas as pd
from config import config
from utils.utils import df_to_json

from postprocess.applicationCheck.auth_feature_check import auth_feature_check
from postprocess.applicationCheck.income_check import income_feature_check
from postprocess.scores.xgboost_scoring import xgboost_prediction


def application_checker(application_info, IBV_auth_data, analyze_transactions_output):
    """
    This capability does 2 things:
    1. Compare what is claimed on application page v.s. what is found in IBV
    2. Give an score prediction on whether the application is to be approved by the agent or not.

    Args:
        - application_info (dict): application info
        - IBV_auth_data (dict): IBV auth data
        - analyze_transactions_output (str): output from analyze transactions,
            - uses the red zone features returned by the function
            - uses the income found by analyze transactions

    Returns:
        - output_final: IAResponse as str
    """
    output = {}
    output["ApplicationChecker"] = {}
    output["ApplicationChecker"]["agentWithdrawnModel"] = {}

    credit_trans = pd.DataFrame.from_dict(analyze_transactions_output["creditTrans"])
    debit_trans = pd.DataFrame.from_dict(analyze_transactions_output["debitTrans"])

    # Handle empty dataframe concatenation to avoid warnings
    frames_to_concat = []
    if not credit_trans.empty:
        frames_to_concat.append(credit_trans)
    if not debit_trans.empty:
        frames_to_concat.append(debit_trans)

    if frames_to_concat:
        labeled_transactions = pd.concat(frames_to_concat, axis=0).reset_index(drop=True)
    else:
        # Create an empty dataframe with the correct structure
        labeled_transactions = pd.DataFrame(
            columns=credit_trans.columns if not credit_trans.empty else debit_trans.columns
        )

    income_sources = pd.DataFrame.from_dict(analyze_transactions_output["incomeSources"])
    auth_features = auth_feature_check(
        application_info,
        IBV_auth_data,
        labeled_transactions,
    )
    income_features = income_feature_check(application_info, income_sources)

    redzone_features = pd.DataFrame.from_dict(analyze_transactions_output["scores"]["features"]["customerLevel"])
    model_features = pd.DataFrame(income_features | auth_features, index=[0])

    # Create a copy to avoid SettingWithCopyWarning
    model_features = model_features.copy()

    # Calculate all match conditions at once
    model_features["fnameMatch"] = (model_features.fnameMatchRate >= 75) | (model_features.fnameInTransactions == 1)
    model_features["lnameMatch"] = (model_features.lnameMatchRate >= 75) | (model_features.lnameInTransactions == 1)
    model_features["accountNumberMatch"] = (model_features.accountNumberMatchAuth.fillna(0).astype(bool)) | (
        model_features.accountNumberInTransactions == 1
    )
    model_features["stateMatch"] = (model_features.stateMatchAuth.fillna(0).astype(bool)) | (
        model_features.stateInTransactions == 1
    )
    model_features["zipMatch"] = (model_features.zipMatchAuth.fillna(0).astype(bool)) | (
        model_features.zipInTransactions == 1
    )
    model_features["cityMatch"] = (model_features.cityMatchAuth.fillna(0).astype(bool)) | (
        model_features.cityInTransactions == 1
    )

    output["ApplicationChecker"]["appVerificationResult"] = df_to_json(model_features)[0]
    # Check if redzone_features is not empty before concatenating
    if not redzone_features.empty:
        # Handle case where both dataframes have rows
        if not model_features.empty:
            model_features = pd.concat([model_features, redzone_features], axis=1).reset_index(drop=True)
        else:
            # Just use redzone_features if model_features is empty
            model_features = redzone_features.copy()
    # No need to handle the case where redzone_features is empty,
    # as we'll just keep using model_features

    formatted_model_features = data_type_adjustment(feature_renaming(model_features))
    (
        withdrawn_pred,
        withdrawn_model,
        withdrawn_features,
    ) = xgboost_prediction(
        formatted_model_features,
        config.WITHDRAWN_MODEL_PATH,
        "customer",
        score_name="agent_withdrawn_chance",
    )

    # not run for now because it can be time consuming
    # withdrawn_explanation = binary_shap_explain(withdrawn_features, withdrawn_features, ["customer"])

    # Extract the withdrawn chance value
    withdrawn_chance = withdrawn_pred.loc[:, "agent_withdrawn_chance"].iloc[0]

    # Set it in model_features (which is a copy)
    model_features["agent_withdrawn_chance"] = withdrawn_chance

    # Also set it in the output dict
    output["ApplicationChecker"]["agentWithdrawnModel"]["score"] = withdrawn_chance
    return output


def data_type_adjustment(model_features):
    """
    Data Type Adjustment for features columns that can take three values, True, False and NA,
    as xgboost can handle NA values by default, it is useful to keep the NA values as is.
    """
    model_features["IBV_from_chase"] = model_features.IBV_from_chase.astype("float64")
    model_features["app_from_chase"] = model_features.app_from_chase.astype("float64")
    model_features["total_match"] = model_features.total_match.astype("float64")
    model_features["last_four_match"] = model_features.last_four_match.astype("float64")
    model_features["first_four_match"] = model_features.first_four_match.astype("float64")
    model_features["routing_match"] = model_features.routing_match.astype("float64")
    model_features["city_match"] = model_features.city_match.astype("float64")
    model_features["state_match"] = model_features.state_match.astype("float64")
    model_features["zip_match"] = model_features.zip_match.astype("float64")
    model_features["phone_match"] = model_features.phone_match.astype("float64")
    model_features["email_match"] = model_features.email_match.astype("float64")
    model_features["fname_match"] = model_features.fname_match.astype("float64")
    model_features["lname_match"] = model_features.lname_match.astype("float64")
    model_features["IBV_suggests_biweekly"] = (model_features.IBV_suggests_biweekly == "True").astype("float64")
    model_features["IBV_suggests_weekly"] = (model_features.IBV_suggests_weekly == "True").astype("float64")
    model_features["IBV_suggests_semi_monthly"] = (model_features.IBV_suggests_semi_monthly == "True").astype("float64")
    model_features["IBV_suggests_monthly"] = (model_features.IBV_suggests_monthly == "True").astype("float64")
    model_features["IBV_suggests_BS"] = (model_features.IBV_suggests_BS == "True").astype("float64")

    return model_features


def feature_renaming(model_features):
    # right now model is not using name and other info in transactions, but
    # this can be used for future improvement if we start some test in the front
    model_features = model_features.rename(
        columns={
            "fnameMatchRate": "fname_match_rate",
            "lnameMatchRate": "lname_match_rate",
            "IBVFromChase": "IBV_from_chase",
            "appFromChase": "app_from_chase",
            "accountNumberMatch": "total_match",
            "accountNumberLastFourMatchAuth": "last_four_match",
            "accountNumberFirstFourMatchAuth": "first_four_match",
            "routingNumberMatch": "routing_match",
            "cityMatchAuth": "city_match",
            "stateMatchAuth": "state_match",
            "zipMatchAuth": "zip_match",
            "phoneMatch": "phone_match",
            "emailMatch": "email_match",
            "fnameMatch": "fname_match",
            "lnameMatch": "lname_match",
            "appFrequencyMatch": "app_frequency_match",
            "appFrequencyMatchBS": "app_frequency_match_BS",
            "appPaydayMatch": "app_payday_match",
            "IBVSuggestsInconsistent": "IBV_suggests_inconsistent",
            "IBVSuggestsBiweekly": "IBV_suggests_biweekly",
            "IBVSuggestsWeekly": "IBV_suggests_weekly",
            "IBVSuggestsSemiMonthly": "IBV_suggests_semi_monthly",
            "IBVSuggestsMonthly": "IBV_suggests_monthly",
            "IBVSuggestsBS": "IBV_suggests_BS",
            "IBVMonthlyIncome": "IBV_monthly_income",
            "reportedIncomeMinusActiveIncome": "reported_minus_actual",
            "requestedAmountRatio": "requested_devides_actual",
        }
    )
    return model_features
