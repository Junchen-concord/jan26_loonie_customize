import warnings

import numpy as np
import pandas as pd
import shap
from config import config
from utils.decorators import timer
from xgboost import XGBClassifier

warnings.filterwarnings("ignore", message="Saving into deprecated binary model format")


@timer
def binary_shap_explain(
    model_input: pd.DataFrame,
    xgb_model: XGBClassifier,
    account_list: list[str],
    model_name="redzone",
    n=5,
) -> pd.DataFrame:
    # Use shap values to give explanation of the red zone model
    # Note that shap here only provides which features are most important to the decision and what are their values,
    # The feature values to insight of the decision is still inferred by user's prior on the business
    # Only works for tree based models as well

    # output
    accountGuids = []
    features = []
    impacts = []
    importance_level = []
    feature_values = []
    feature_contributions = []
    explanations = []

    binary_model = xgb_model.get_booster()
    binary_explainer = shap.TreeExplainer(binary_model)
    binary_shap_values = binary_explainer.shap_values(model_input)

    for i in range(len(model_input)):
        account_id = account_list[i]
        account_shap_values = binary_shap_values[i, :]
        (
            topn_pos_features,
            topn_pos_values,
            topn_neg_features,
            topn_neg_values,
        ) = get_topn_features(account_shap_values.flatten(), np.array(model_input.columns))
        accountGuids = accountGuids + [account_id] * 2 * n
        features = features + list(topn_pos_features) + list(topn_neg_features)
        impacts = impacts + ["positive"] * n + ["negative"] * n
        importance_level = importance_level + list(range(1, n + 1)) + list(range(1, n + 1))
        feature_contributions = feature_contributions + list(topn_pos_values) + list(topn_neg_values)
        feature_values = (
            feature_values
            + list(np.array(model_input[topn_pos_features].iloc[i]))
            + list(np.array(model_input[topn_neg_features].iloc[i]))
        )
    if model_name == "redzone":
        feature_explanation = red_zone_feature_explain(features, impacts, feature_values)
        explanations = explanations + feature_explanation
    else:
        # Other model explanation is not ready yet as we need to intepret between feature names and business understandable reasons
        explanations = explanations + ["None"] * len(features)
    return pd.DataFrame(
        {
            "accountGuid": accountGuids,
            "feature": features,
            "impact": impacts,
            "importance_level": importance_level,
            "feature_contribution": feature_contributions,
            "feature_values": feature_values,
            "explanation": explanations,
        }
    )


@timer
def get_topn_features(
    account_shap_values: np.ndarray, feature_names: np.ndarray, n=5
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    # Get top n positive and negative features for binary xgboost model
    # If the number of positive or negative features is less than n, pad the rest with 'None'
    pos_values = account_shap_values[account_shap_values > 0]
    neg_values = account_shap_values[account_shap_values < 0]
    pos_features = feature_names[account_shap_values > 0]
    neg_features = feature_names[account_shap_values < 0]

    if len(pos_features) >= 1:
        topn_pos_features = pos_features[pos_values.argsort()[::-1][:n]]
        topn_pos_values = pos_values[pos_values.argsort()[::-1][:n]]
        topn_pos_features = pad_to_n(topn_pos_features, n)
        topn_pos_values = pad_to_n(topn_pos_values, n)

    else:
        topn_pos_features = ["None"] * n
        topn_pos_values = [np.nan] * n

    if len(neg_features) >= 1:
        topn_neg_features = neg_features[neg_values.argsort()[:n]]
        topn_neg_values = neg_values[neg_values.argsort()[:n]]
        topn_neg_features = pad_to_n(topn_neg_features, n)
        topn_neg_values = pad_to_n(topn_neg_values, n)
    else:
        topn_neg_features = ["None"] * n
        topn_neg_values = [np.nan] * n
    return (
        topn_pos_features,
        topn_pos_values,
        topn_neg_features,
        topn_neg_values,
    )


@timer
def red_zone_feature_explain(features: list[str], impacts: list[str], feature_values: list[float]) -> list[str]:
    # Try to interpret the features in the red zone, because from the shap plot the features are usually are very linear
    # (higher value means higher default or the opposite), it is directly interpretting based on prediction and whether it is
    # positive and not.
    red_zone_feature_dict = redzone_feature_dictionary()
    feature_explanation = []
    for feature, impact, feature_value in zip(features, impacts, feature_values):
        if feature in red_zone_feature_dict.keys():
            if impact == "positive":
                if "positive_value_range" in red_zone_feature_dict[feature].keys():
                    if (
                        feature_value > red_zone_feature_dict[feature]["positive_value_range"][0]
                        and feature_value < red_zone_feature_dict[feature]["positive_value_range"][1]
                    ):
                        feature_explanation.append(red_zone_feature_dict[feature]["positive"])
                    else:
                        feature_explanation.append("None")
                else:
                    feature_explanation.append(red_zone_feature_dict[feature]["positive"])
            else:
                if "negative_value_range" in red_zone_feature_dict[feature].keys():
                    if (
                        feature_value > red_zone_feature_dict[feature]["negative_value_range"][0]
                        and feature_value < red_zone_feature_dict[feature]["negative_value_range"][1]
                    ):
                        feature_explanation.append(red_zone_feature_dict[feature]["negative"])
                    else:
                        feature_explanation.append("None")
                else:
                    feature_explanation.append(red_zone_feature_dict[feature]["negative"])
        else:
            feature_explanation.append("None")
    return feature_explanation


@timer
def pad_to_n(arr: np.ndarray, n: int, pad_value="None") -> np.ndarray:
    if len(arr) < n:
        pad_array = np.full(n - len(arr), pad_value)
        arr = np.concatenate([arr, pad_array], axis=0)
    return arr


# Cache the feature dictionary since it's expensive to create and never changes
_REDZONE_FEATURE_DICT_CACHE = None


@timer
def redzone_feature_dictionary() -> dict[str, str]:
    global _REDZONE_FEATURE_DICT_CACHE
    if _REDZONE_FEATURE_DICT_CACHE is not None:
        return _REDZONE_FEATURE_DICT_CACHE
    # some of the features will not be inside the dictionary because it is hard to explain
    # after version 16.9.8, limit will be added for feature value checks, if the feature value is outside the expected range
    # the assessment reason won't be popped
    # the range will be be (left, right) non inclusive
    red_zone_feature_dict = {}
    red_zone_feature_dict["incomeSourceAllTime"] = {
        "positive": "Limited Number of Income Sources",
        "negative": "Considerable Number of Income Sources",
        "positive_value_range": [-np.inf, config.REDZONE_INCOME_SOURCE_LIMIT],
        "negative_value_range": [0, np.inf],
    }
    # cashflow_features = ['allTimeMonthlyIncome', 'cashflowAllTime', 'inflowExcludingLoans', 'totalCredits', 'total_monthly1']
    # high total credits -> higher default in red zone, which doesn't make much sense, mask for now
    red_zone_feature_dict["allTimeMonthlyIncome"] = {
        "positive": "Limited Total Inflow",
        "negative": "Considerable Total Inflow",
        "positive_value_range": [-np.inf, config.ALL_TIME_MONTHLY_INCOME_POSITIVE_UPPER_LIMIT],
        "negative_value_range": [config.ALL_TIME_MONTHLY_INCOME_POSITIVE_LOWER_LIMIT, np.inf],
    }
    red_zone_feature_dict["inflowExcludingLoans"] = {
        "positive": "Limited Total Inflow",
        "negative": "Considerable Total Inflow",
        "positive_value_range": [-np.inf, config.INFLOW_UPPER_LIMIT],
        "negative_value_range": [config.INFLOW_LOWER_LIMIT, np.inf],
    }
    red_zone_feature_dict["odAll"] = {
        "positive": "High Number of Overdrafts/NSF",
        "negative": "Low Overdraft/NSF Count",
        "positive_value_range": [config.OD_ALL_NEGATIVE_LOWER_LIMIT, np.inf],
        "negative_value_range": [-np.inf, config.OD_ALL_NEGATIVE_UPPER_LIMIT],
    }
    red_zone_feature_dict["averageMonthlyBalanceAll"] = {
        "positive": "Low Average Balance",
        "negative": "High Average Balance",
        "positive_value_range": [-np.inf, config.AVERAGE_MONTHLY_BALANCE_ALL_POSITIVE_UPPER_LIMIT],
        "negative_value_range": [config.AVERAGE_MONTHLY_BALANCE_ALL_POSITIVE_LOWER_LIMIT, np.inf],
    }
    red_zone_feature_dict["incomeHistoryAllTime"] = {
        "positive": "Limited Income History",
        "negative": "Considerable Income History",
        "positive_value_range": [-np.inf, config.INCOME_HISTORY_ALL_TIME_POSITIVE_UPPER_LIMIT],
        "negative_value_range": [config.INCOME_HISTORY_ALL_TIME_POSITIVE_LOWER_LIMIT, np.inf],
    }
    red_zone_feature_dict["loanPmtAllTime"] = {
        "positive": "Limited Loan Payback History",
        "negative": "Considerable Loan Payback History",
        "positive_value_range": [-np.inf, config.LOAN_PMT_ALL_TIME_POSITIVE_UPPER_LIMIT],
        "negative_value_range": [config.LOAN_PMT_ALL_TIME_POSITIVE_LOWER_LIMIT, np.inf],
    }
    # red_zone_feature_dict['loanIdentifiedAllTime'] = {'positive': 'loan brands identified is low',
    #                                                   'negative': 'loan brands identified is high'}
    red_zone_feature_dict["recurringMonthlyIncome"] = {
        "positive": "Low Recurring Income",
        "negative": "High Recurring Income",
        "positive_value_range": [-np.inf, config.RECURRING_MONTHLY_INCOME_POSITIVE_UPPER_LIMIT],
        "negative_value_range": [config.RECURRING_MONTHLY_INCOME_POSITIVE_LOWER_LIMIT, np.inf],
    }
    red_zone_feature_dict["activeMonthlyIncome"] = {
        "positive": "Low Active Income",
        "negative": "High Active Income",
        "positive_value_range": [-np.inf, config.ACTIVE_MONTHLY_INCOME_POSITIVE_UPPER_LIMIT],
        "negative_value_range": [config.ACTIVE_MONTHLY_INCOME_POSITIVE_LOWER_LIMIT, np.inf],
    }
    red_zone_feature_dict["totalDebits"] = {
        "positive": "High Debit Activity",
        "negative": "Limited Debit Activity",
        "positive_value_range": [config.TOTAL_DEBITS_POSITIVE_LOWER_LIMIT, np.inf],
        "negative_value_range": [-np.inf, config.TOTAL_DEBITS_POSITIVE_UPPER_LIMIT],
    }
    # red_zone_feature_dict['income_count1_Deposit'] = {'positive': 'Number of deposit source is low',
    #                                                   'negative': 'Number of deposit sourceis high'}
    red_zone_feature_dict["income_count1_Payroll"] = {
        "positive": "Limited Payroll Income History",
        "negative": "Considerable Payroll Income History",
        "positive_value_range": [-np.inf, config.INCOME_COUNT1_PAYROLL_POSITIVE_UPPER_LIMIT],
        "negative_value_range": [config.INCOME_COUNT1_PAYROLL_POSITIVE_LOWER_LIMIT, np.inf],
    }
    red_zone_feature_dict["income_count1_Benefit"] = {
        "positive": "Limited Benefit Income History",
        "negative": "Considerable Benefit Income History",
        "positive_value_range": [-np.inf, config.INCOME_COUNT1_BENEFIT_POSITIVE_UPPER_LIMIT],
        "negative_value_range": [config.INCOME_COUNT1_BENEFIT_POSITIVE_LOWER_LIMIT, np.inf],
    }
    # red_zone_feature_dict['income_count1_Transfer'] = {'positive': 'Number of transfer source is low',
    #                                                    'negative': 'Number of benefit source is high'}
    # red_zone_feature_dict['income_count1_gig'] = {'positive': 'Number of gig source is low',
    #                                               'negative': 'Number of gig source is high'}
    # red_zone_feature_dict['total_type_monthly1_Deposit'] = {'positive': 'Deposit income is low',
    #                                                         'negative': 'Deposit income is high'}
    red_zone_feature_dict["total_type_monthly1_Payroll"] = {
        "positive": "Low Payroll Income",
        "negative": "High Payroll Income",
        "positive_value_range": [-np.inf, config.TOTAL_TYPE_MONTHLY1_PAYROLL_POSITIVE_UPPER_LIMIT],
        "negative_value_range": [config.TOTAL_TYPE_MONTHLY1_PAYROLL_POSITIVE_LOWER_LIMIT, np.inf],
    }
    red_zone_feature_dict["total_type_monthly1_Benefit"] = {
        "positive": "Low Benefit Income",
        "negative": "High Benefit Income",
        "positive_value_range": [-np.inf, config.TOTAL_TYPE_MONTHLY1_BENEFIT_POSITIVE_UPPER_LIMIT],
        "negative_value_range": [config.TOTAL_TYPE_MONTHLY1_BENEFIT_POSITIVE_LOWER_LIMIT, np.inf],
    }
    # red_zone_feature_dict['total_type_monthly1_Transfer'] = {'positive': 'Transfer income is low',
    #                                                          'negative': 'Transfer income is high'}
    # red_zone_feature_dict['total_type_monthly1_gig'] = {'positive': 'Gig income is low',
    #                                                     'negative': 'Gig income is high'}
    red_zone_feature_dict["num_of_originations"] = {
        "positive": "High Borrowing Activity",
        "negative": "Limited Borrowing Activity",
        "positive_value_range": [config.NUM_OF_ORIGINATIONS_POSITIVE_LOWER_LIMIT, np.inf],
        "negative_value_range": [-np.inf, config.NUM_OF_ORIGINATIONS_POSITIVE_UPPER_LIMIT],
    }
    red_zone_feature_dict["num_of_pays"] = {
        "positive": "Limited Loan Payback History",
        "negative": "Considerable Loan Payback History",
        "positive_value_range": [-np.inf, config.NUM_OF_PAYS_POSITIVE_UPPER_LIMIT],
        "negative_value_range": [config.NUM_OF_PAYS_POSITIVE_LOWER_LIMIT, np.inf],
    }

    # active recurring stable score is still in experiment, masking the feature explanation for now
    # active_score_features = ['active_count_0', 'active_count_1', 'active_count_2', 'active_count_3', 'active_monthly_0', 'active_monthly_1', 'active_monthly_2', 'active_monthly_3']
    # for active_score_feature in active_score_features:
    #     red_zone_feature_dict[active_score_feature] = {'positive': 'Not enough active income (no active income)',
    #                                                             'negative': 'Income is active'}
    red_zone_feature_dict["active_count_1"] = {
        "positive": "Inconsistent Income",
        "negative": "Consistent Income",
        "positive_value_range": [-np.inf, config.ACTIVE_COUNT_1_POSITIVE_UPPER_LIMIT],
        "negative_value_range": [config.ACTIVE_COUNT_1_POSITIVE_LOWER_LIMIT, np.inf],
    }
    red_zone_feature_dict["active_monthly_1"] = {
        "positive": "Inconsistent Income",
        "negative": "Consistent Income",
        "positive_value_range": [-np.inf, config.ACTIVE_MONTHLY_1_POSITIVE_UPPER_LIMIT],
        "negative_value_range": [config.ACTIVE_MONTHLY_1_POSITIVE_LOWER_LIMIT, np.inf],
    }
    # red_zone_feature_dict['recurring_count_1'] = {'positive': 'Income not showing recurring pattern (hard to time debit date)',
    #                                               'negative': 'Income showing recurring pattern'}
    # red_zone_feature_dict['recurring_monthly_1'] = {'positive': 'Income not showing recurring pattern (hard to time debit date)',
    #                                                 'negative': 'Income showing recurring pattern'}
    # red_zone_feature_dict['recurring_count_3'] = {'positive': 'Income not showing recurring pattern (hard to time debit date)',
    #                                               'negative': 'Income showing recurring pattern'}
    # red_zone_feature_dict['transation_period_lengths'] = {'positive': 'Low transaction history',
    #                                                       'negative': 'High transaction history'}
    """
    ## TODO There are too many ATP features for explain, and there is work to do to approximate those features with 
    easier business understandable goals, which will relates to creating surrogate features to approximate ATP.
    For now for the sake of time, will just differenciate between each feature's positive and negative contribution,
    if the feature is negative to FPD, it can't be 0 for explaining green zone, and if the feature is positive to FPD,
    it can't be 0 for explaining red zone.
    """
    # ATPs that should have a negative contribution to FPD
    # atp_features_peak_counts = [
    #     "n_peak_500",
    #     "n_peak_250",
    #     "n_peak_100",
    # ]
    # for atp_peak_count_feature in atp_features_peak_counts:
    #     red_zone_feature_dict[atp_peak_count_feature] = {
    #         "positive": "Bad Spending Behavior",
    #         "negative": "Good Spending Behavior",
    #         "positive_value_range": [-np.inf, config.PEAK_NUMBER_POSITIVE_UPPER_LIMIT],
    #         "negative_value_range": [config.PEAK_NUMBER_POSITIVE_LOWER_LIMIT, np.inf],
    #     }

    # atp_features_gtd_by_peaks = [
    #     "good_days_to_debit_by_peak_500",
    #     "good_days_to_debit_by_peak_250",
    #     "good_days_to_debit_by_peak_100",
    # ]

    # for atp_gtd_by_peak_feature in atp_features_gtd_by_peaks:
    #     red_zone_feature_dict[atp_gtd_by_peak_feature] = {
    #         "positive": "Bad Spending Behavior",
    #         "negative": "Good Spending Behavior",
    #         "positive_value_range": [-np.inf, config.GTD_BY_PEAK_POSITIVE_UPPER_LIMIT],
    #         "negative_value_range": [config.GTD_BY_PEAK_POSITIVE_LOWER_LIMIT, np.inf],
    #     }

    # # ATPs that should have a positive contribution to FPD
    # atp_features_valley_counts = [
    #     "n_valley_500",
    #     "n_valley_250",
    #     "n_valley_100",
    # ]
    # for atp_valley_count_feature in atp_features_valley_counts:
    #     red_zone_feature_dict[atp_valley_count_feature] = {
    #         "positive": "Bad Spending Behavior",
    #         "negative": "Good Spending Behavior",
    #         "positive_value_range": [config.VALLEY_NUMBER_POSITIVE_LOWER_LIMIT, np.inf],
    #         "negative_value_range": [-np.inf, config.VALLEY_NUMBER_POSITIVE_UPPER_LIMIT],
    #     }

    # atp_gtd_by_valleys = [
    #     "good_days_to_debit_by_valley_500",
    #     "good_days_to_debit_by_valley_250",
    #     "good_days_to_debit_by_valley_100",
    # ]
    # for atp_gtd_by_valley_feature in atp_gtd_by_valleys:
    #     red_zone_feature_dict[atp_gtd_by_valley_feature] = {
    #         "positive": "Bad Spending Behavior",
    #         "negative": "Good Spending Behavior",
    #         "positive_value_range": [config.GTD_BY_VALLEY_POSITIVE_LOWER_LIMIT, np.inf],
    #         "negative_value_range": [-np.inf, config.GTD_BY_VALLEY_POSITIVE_UPPER_LIMIT],
    #     }
    # negative_atp_features = [
    #      "n_peak_500",
    #      "good_days_to_debit_by_peak_500",
    #      "peak_trans_history_ratio_500",
    #      "peak_good_days_to_debit_trans_history_ratio500",
    #     "max_peak_prominence_500",
    #     "avg_peak_prominence_500",
    #      "max_peak_gtd_500",
    #      "avg_peak_gtd_500",
    #      "avg_peak_prominence_500",
    #      'n_peak_250',
    #      "good_days_to_debit_by_peak_250",
    #      "peak_trans_history_ratio_250",
    #      "peak_good_days_to_debit_trans_history_ratio250",
    #      "max_peak_gtd_250",
    #      "avg_peak_gtd_250",
    #     "n_peak_100",
    #     "good_days_to_debit_by_peak_100",
    #     'peak_trans_history_ratio_100',
    #     'peak_good_days_to_debit_trans_history_ratio100',
    #     "max_peak_gtd_100",
    #     "avg_peak_gtd_100",
    # ]

    # positive_atp_features = [
    #     "good_days_to_debit_by_valley_500",
    #     "valley_trans_history_ratio_500",
    #     "valley_good_days_to_debit_trans_history_ratio500",
    #     "avg_valley_prominence_500",
    #     "max_valley_gtd_500",
    #     "avg_valley_gtd_500",
    #     "n_valley_250",
    #     "good_days_to_debit_by_valley_250",
    #     "valley_trans_history_ratio_250",
    #     "valley_good_days_to_debit_trans_history_ratio250",
    #     "avg_valley_prominence_250",
    #     "max_valley_gtd_250",
    #     "avg_valley_gtd_250",
    #     "n_valley_100",
    #     "good_days_to_debit_by_valley_100",
    #     "valley_trans_history_ratio_100",
    #     "valley_good_days_to_debit_trans_history_ratio100",
    #     "max_valley_gtd_100",
    #     "avg_valley_gtd_100",
    # ]

    # other_atp_features = [
    #     "min_peak_prominence_500",
    #     "min_peak_prominence_250",
    #     'min_peak_gtd_500'
    #     "min_peak_gtd_250",
    #     "min_peak_gtd_100",
    #     "min_peak_prominence_100",
    #     "min_valley_prominence_500",
    #     "min_valley_gtd_500",
    #     "min_valley_prominence_250",
    #     "min_valley_gtd_250",
    #     "min_valley_prominence_100",
    #     "min_valley_gtd_100",
    #     "min_valley_prominence_100",

    # ]
    # for atp_feature in negative_atp_features:
    #     red_zone_feature_dict[atp_feature] = {
    #         "positive": "Bad Spending Behavior",
    #         "negative": "Good Spending Behavior",
    #         "positive_value_range": [-np.inf, config.ATP_NEGATIVE_UPPER_LIMIT],
    #         "negative_value_range": [config.ATP_NEGATIVE_LOWER_LIMIT, np.inf],
    #     }

    # for atp_feature in positive_atp_features:
    #     red_zone_feature_dict[atp_feature] = {
    #         "positive": "Bad Spending Behavior",
    #         "negative": "Good Spending Behavior",
    #         "positive_value_range": [config.ATP_POSITIVE_LOWER_LIMIT, np.inf],
    #         "negative_value_range": [-np.inf, config.ATP_POSITIVE_UPPER_LIMIT],
    #     }

    # for atp_feature in other_atp_features:
    #     red_zone_feature_dict[atp_feature] = {
    #         "positive": "Bad Spending Behavior",
    #         "negative": "Good Spending Behavior",
    #     }

    # positive_atp_features_cashflow = [
    #     "valley_most_recent_gtd_length_100",
    #     "valley_most_recent_gtd_length_250",
    #     "valley_most_recent_gtd_length_500",
    # ]

    # negative_atp_features_cashflow = [
    #     "peak_most_recent_gtd_length_250",
    #     "peak_most_recent_gtd_length_500",
    #     "peak_most_recent_gtd_length_100",
    # ]

    # for atp_feature in negative_atp_features_cashflow:
    #     red_zone_feature_dict[atp_feature] = {
    #         "positive": "Bad Spending Behavior before application",
    #         "negative": "Good Spending Behavior before application",
    #         "positive_value_range": [-np.inf, config.ATP_NEGATIVE_UPPER_LIMIT],
    #         "negative_value_range": [config.ATP_NEGATIVE_LOWER_LIMIT, np.inf],
    #     }

    # for atp_feature in positive_atp_features_cashflow:
    #     red_zone_feature_dict[atp_feature] = {
    #         "positive": "Bad Spending Behavior before application",
    #         "negative": "Good Spending Behavior before application",
    #         "positive_value_range": [config.ATP_POSITIVE_LOWER_LIMIT, np.inf],
    #         "negative_value_range": [-np.inf, config.ATP_POSITIVE_UPPER_LIMIT],
    #     }

    # Cache the result for future calls
    _REDZONE_FEATURE_DICT_CACHE = red_zone_feature_dict
    return red_zone_feature_dict
