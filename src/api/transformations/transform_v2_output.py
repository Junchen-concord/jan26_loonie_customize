import pandas as pd
from config.settings import OUTPUT_APPLICATION_CHECK, OUTPUT_FEATURES

from api.transformations.features_type_map import features_type_map


def find_corresponding_dict(output, field, account_guid):
    found = next(
        (obj for obj in output[field] if obj["accountGuid"] == account_guid),
        None,
    )
    return found


# Formats/Renames


def sameDayFreq_format(value: float):
    return int(value * 100)


income_sources_renames = {
    "historicalPayDay": "pastDeposits",
    "monthlyIncome": "estimatedMonthlyIncome",
    "sameDayFreq": sameDayFreq_format,
    "sourceName": "incomeSource",
}
loan_source_renames = {
    "originationAmount": "amountObserved",
    "paymentAmount": "monthlyPayment",
    "regularPayDay": "schedule",
    "lastPayDay": "latestTransaction",
    "sourceName": "lenderName",
}

rename_mapping = {"incomeSources": income_sources_renames, "loanSources": loan_source_renames}


def group_list_by_account(output, sources_field):
    sources_by_account = {}
    rename_map = rename_mapping.get(sources_field, {})
    for source in output.get(sources_field, []):
        account_guid = source.get("accountGuid", None)
        if account_guid is not None and account_guid not in sources_by_account:
            sources_by_account[account_guid] = []
        del source["accountGuid"]
        for rename_field in rename_map.keys():
            new_field_name = rename_map.get(rename_field, None)
            if not new_field_name or rename_field not in source:
                return sources_by_account
            if not isinstance(new_field_name, str):
                new_value = new_field_name(source[rename_field])
                source[rename_field] = new_value
            else:
                source[new_field_name] = source[rename_field]
                del source[rename_field]
        sources_by_account[account_guid].append(source)
    return sources_by_account


# Clean transactions
remove_txn_fields = []
renames = {"transCategory": "incomeType", "StackingPrediction": "stackingPrediction"}


def clean_txn_fields(txns):
    if txns is None or not isinstance(txns, list):
        return []
    cleaned_txns = []
    for txn in txns:
        # Skip transaction if both accountGuid and description are missing
        account_guid = txn["accountGuid"]
        if pd.isna(account_guid) or account_guid is None:
            continue
        cleaned_txn = txn.copy()
        # Remove fields
        for field in remove_txn_fields:
            if field in cleaned_txn:
                del cleaned_txn[field]
        # Rename fields
        for old_name, new_name in renames.items():
            if old_name in cleaned_txn:
                cleaned_txn[new_name] = cleaned_txn.pop(old_name)

        # Remove None or null values for specific fields
        fields_to_check = ["who", "how", "what", "whoCat"]
        for field in fields_to_check:
            if field in cleaned_txn and (
                cleaned_txn[field] is None or cleaned_txn[field] == "None" or pd.isna(cleaned_txn[field])
            ):
                del cleaned_txn[field]

        cleaned_txns.append(cleaned_txn)
    return cleaned_txns


# Scope flattening
timeframes = ["allTime", "threeMonth", "sixMonth"]
field_mappings = {
    "avgMonthlyBalance": ["averageMonthlyBalanceAll", "averageMonthlyBalance3Month", "averageMonthlyBalance6Month"],
    "overdraftIncidents": ["odAll", "od3m", "od6m"],
    "overdraftFeeIncidents": ["odfAll", "odf3m", "odf6m"],
    "nsfFeeIncidents": ["nsfAll", "nsf3m", "nsf6m"],
    "avgMonthlyIncome": ["allTimeMonthlyIncome", "threeMonthMonthlyIncome", "sixMonthMonthlyIncome"],
    "numIncomeSources": ["incomeSourceAllTime", "incomeSourceThreeMonth", "incomeSourceSixMonth"],
    "numMonthsIncomeHistory": ["incomeHistoryAllTime", "incomeHistoryThreeMonth", "incomeHistorySixMonth"],
    "amountPaidInLoans": ["loanPmtAllTime", "loanPmtThreeMonth", "loanPmtSixMonth"],
    "numLoans": ["loanIdentifiedAllTime", "loanIdentifiedThreeMonth", "loanIdentifiedSixMonth"],
    "cashflow": ["cashflowAllTime", "cashflowThreeMonth", "cashflowSixMonth"],
}


def cast_data_types(features):
    conversion_functions = {"int": int, "float": float}

    converted_row = {}

    for field, value in features.items():
        target_type = features_type_map.get(field)
        if target_type in conversion_functions:
            try:
                converted_value = conversion_functions[target_type](value)
                converted_row[field] = converted_value
            except ValueError:
                converted_row[field] = value
        else:
            converted_row[field] = value

    return converted_row


def transform_v2_output(output: dict):
    income_sources_by_account = group_list_by_account(output, "incomeSources")
    loan_sources_by_account = group_list_by_account(output, "loanSources")
    od_incidents_by_account = group_list_by_account(output, "overdraftIncidents")  # TODO: Remove
    odf_incidents_by_account = group_list_by_account(output, "overdraftFeeIncidents")
    nsf_incidents_by_account = group_list_by_account(output, "nsfFeeIncidents")
    features_customer_level_clean = output["scores"]["features"]["customerLevel"][0].copy()
    if "accountGuid" in features_customer_level_clean:
        features_customer_level_clean.pop("accountGuid")

    # Modify the accounts field
    for account in output["accounts"]:
        account_guid = account["accountGuid"]

        summary_info = find_corresponding_dict(output, "summaryInfo", account_guid)
        cashflow = find_corresponding_dict(output, "cashFlow", account_guid)
        account_features = find_corresponding_dict(output["scores"]["features"], "accountLevel", account_guid)
        account["incomeSources"] = income_sources_by_account.get(account_guid, [])
        account["loanSources"] = loan_sources_by_account.get(account_guid, [])
        account["overdraftIncidents"] = od_incidents_by_account.get(account_guid, [])
        account["overdraftFeeIncidents"] = odf_incidents_by_account.get(account_guid, [])
        account["nsfFeeIncidents"] = nsf_incidents_by_account.get(account_guid, [])
        cashflow_clean = cashflow.copy()
        cashflow_clean.pop("accountGuid")
        account["cashFlow"] = cashflow_clean
        features_clean = account_features.copy()
        features_clean.pop("accountGuid")
        if OUTPUT_FEATURES:
            account["features"] = cast_data_types(features_clean)

        if summary_info:
            # allTime, threeMonth, and sixMonth
            for i, timeframe in enumerate(timeframes):
                account[timeframe] = {}
                for new_field, old_fields in field_mappings.items():
                    account[timeframe][new_field] = summary_info.get(old_fields[i], 0)

            account.update(
                {
                    "banking": {
                        "card": summary_info.get("card", []),
                        "accountType": summary_info.get("accountType", "CHECKING"),
                    },
                    "monthlyIncome": {
                        "recurringMonthlyIncome": summary_info.get("recurringMonthlyIncome", 0),
                        "activeMonthlyIncome": summary_info.get("activeMonthlyIncome", 0),
                        # API will add stableMonthlyIncome
                    },
                    "inflowExcludingLoans": summary_info.get("inflowExcludingLoans", 0),
                    "currentBalance": summary_info.get("currentBalance", 0),
                    "availableBalance": summary_info.get("availableBalance", 0),
                    "assessmentReasonsGood": summary_info.get("assessmentReasonsGood", []),
                    "assessmentReasonsBad": summary_info.get("assessmentReasonsBad", []),
                    "riskAnalysis": {
                        "riskBehavior": summary_info.get("riskBehavior", ""),
                        "riskScore": summary_info.get("riskScore", 0),
                    },
                }
            )
    additional_info = output["additionalInfo"]

    # Extract scores for customer level, excluding account level
    scores_customer_level = {}
    if "scores" in output:
        for model_name, model_data in output["scores"].items():
            if model_name != "features":  # Skip features as they're handled separately
                # Rename redZone to redZoneV1 for backward compatibility
                target_name = "redZoneV1" if model_name == "redZone" else model_name
                scores_customer_level[target_name] = {}
                if "customerLevel" in model_data:
                    scores_customer_level[target_name] = model_data["customerLevel"]
            else:
                scores_customer_level["features"] = model_data

    # Get the old riskScore from riskAnalysisCustomer (redZone V1)
    risk_analysis_customer = additional_info["redZoneBehaviorCustomer"][0].copy()

    # Update riskScore with redZoneV2 model score if available
    if "redZoneV2" in scores_customer_level:
        redzone_v2_customer_level = scores_customer_level.get("redZoneV2", {})
        model_scores = redzone_v2_customer_level.get("modelScore", [])
        if model_scores and len(model_scores) > 0:
            v2_risk_score = model_scores[0].get("riskScore", risk_analysis_customer.get("riskScore", 0))
            risk_analysis_customer["riskScore"] = int(v2_risk_score) if v2_risk_score is not None else 0

    customer_info = {
        "riskAnalysisCustomer": risk_analysis_customer,
        "assessmentReasonsCustomerGood": additional_info["alertsAndInsightsCustomer"][0]["assessmentReasonsGood"],
        "assessmentReasonsCustomerBad": additional_info["alertsAndInsightsCustomer"][0]["assessmentReasonsBad"],
        "recommendedBankAccount": additional_info["recommendedBankAccount"],
        "lendingGuideCustomer": output["lendingGuide"],
        "scores": scores_customer_level,
    }

    if OUTPUT_FEATURES:
        customer_info["features"] = cast_data_types(features_customer_level_clean)

    if "ApplicationChecker" in output and OUTPUT_APPLICATION_CHECK:
        customer_info["applicationCheck"] = output["ApplicationChecker"]

    output["customerInfo"] = customer_info
    output["transactions"] = clean_txn_fields(output["creditTrans"]) + clean_txn_fields(output["debitTrans"])
    output["asOfDate"] = summary_info["asOfDate"]
    # Remove old fields
    del output["summaryInfo"]
    del output["majorIncomeSource"]
    del output["incomeSources"]
    del output["loanSources"]
    del output["overdraftIncidents"]
    del output["overdraftFeeIncidents"]
    del output["nsfFeeIncidents"]
    del output["cashFlow"]
    del output["additionalInfo"]
    del output["lendingGuide"]
    del output["scores"]
    del output["creditTrans"]
    del output["debitTrans"]
    if "ApplicationChecker" in output:
        del output["ApplicationChecker"]

    return output
