import os
import warnings

import httpx
import joblib
import pandas as pd
from api.ApiClient import ApiClient
from app_utils import logger
from config import config, settings
from utils.utils import df_to_json
from xgboost import XGBClassifier

from postprocess.scores.deduplicate_list import deduplicate_list
from postprocess.scores.transform_score import transform_score

warnings.filterwarnings("ignore", message="Saving into deprecated binary model format")


def xgb_features(
    income_df_sorted: pd.DataFrame,
    balance_df: pd.DataFrame,
    loan_source_dict: dict,
    cash_flow_data: pd.DataFrame,
    summaryInfo: dict,
    atp_df: pd.DataFrame,
):
    all_account_ids = balance_df[[config.IA_ACCOUNT_ID]]
    loan_sources_df = pd.DataFrame.from_dict(loan_source_dict).transpose()
    loan_sources_df = loan_sources_df[loan_sources_df.errorCode == 000].rename(
        columns={"accountGuid": config.IA_ACCOUNT_ID}
    )
    loan_sources_df["numOfOrigination"] = loan_sources_df.numOfOrigination.astype(int)
    loan_sources_df["numOfPay"] = loan_sources_df.numOfPay.astype(int)

    income_df_sorted = income_df_sorted[~income_df_sorted["errorCode"].isin([101, 102, 103, 104, 105])].rename(
        columns={"accountGuid": config.IA_ACCOUNT_ID}
    )

    cash_flow_data["large_inflow"] = cash_flow_data.totalCredits > config.HIGH_TOTAL_CREDIT
    cash_flow_data["low_inflow"] = cash_flow_data.totalCredits < config.LOW_TOTAL_CREDIT

    summaryInfo = pd.DataFrame.from_dict(summaryInfo).rename(columns={"accountGuid": config.IA_ACCOUNT_ID})
    valid_income_sources = income_df_sorted
    # valid_income_sources = income_df_sorted.dropna(axis='monthlyIncome')
    valid_income_sources_other_transfer_removed = income_df_sorted[
        (income_df_sorted.sourceName != "other deposit") & (income_df_sorted.sourceName != "other transfer")
    ]
    count_income_sources = (
        valid_income_sources.groupby([config.IA_ACCOUNT_ID, "incomeType"])
        .agg(
            income_count1=("monthlyIncome", "count"),
            total_type_monthly1=("monthlyIncome", "sum"),
        )
        .reset_index()
    )
    count_income_sources2 = (
        valid_income_sources_other_transfer_removed.groupby([config.IA_ACCOUNT_ID, "incomeType"])
        .agg(
            income_count2=("monthlyIncome", "count"),
            total_type_monthly2=("monthlyIncome", "sum"),
        )
        .reset_index()
    )
    total_income1 = (
        count_income_sources.groupby(config.IA_ACCOUNT_ID)
        .agg(
            total_income_source1=("income_count1", "sum"),
            total_monthly1=("total_type_monthly1", "sum"),
        )
        .reset_index()
    )
    total_income2 = (
        count_income_sources2.groupby(config.IA_ACCOUNT_ID)
        .agg(
            total_income_source2=("income_count2", "sum"),
            total_monthly2=("total_type_monthly2", "sum"),
        )
        .reset_index()
    )
    count_income_sources = count_income_sources.pivot(
        index=config.IA_ACCOUNT_ID,
        columns="incomeType",
        values=["income_count1", "total_type_monthly1"],
    )
    count_income_sources.columns = ["_".join(col) for col in count_income_sources.columns]
    count_income_sources = count_income_sources.reset_index()
    count_income_sources2 = count_income_sources2.pivot(
        index=config.IA_ACCOUNT_ID,
        columns="incomeType",
        values=["income_count2", "total_type_monthly2"],
    )
    count_income_sources2.columns = ["_".join(col) for col in count_income_sources2.columns]
    count_income_sources2 = count_income_sources2.reset_index()

    count_loan_sources = (
        loan_sources_df.groupby(config.IA_ACCOUNT_ID)
        .agg(
            num_of_loans=("originationAmount", "count"),
            num_of_originations=("numOfOrigination", "sum"),
            num_of_pays=("numOfPay", "sum"),
        )
        .reset_index()
    )

    # active/recurring
    valid_income_sources["activeScore"] = valid_income_sources["activeScore"].astype(str)
    count_active_sources = (
        valid_income_sources.groupby(["accountGuid", "activeScore"])
        .agg(
            active_count=("monthlyIncome", "count"),
            active_monthly=("monthlyIncome", "sum"),
        )
        .reset_index()
    )
    count_active_sources = count_active_sources.pivot(
        index="accountGuid",
        columns="activeScore",
        values=["active_count", "active_monthly"],
    )
    count_active_sources.columns = ["_".join(col) for col in count_active_sources.columns]
    count_active_sources = count_active_sources.reset_index()
    valid_income_sources["recurringScore"] = valid_income_sources["recurringScore"].astype(str)
    count_recurring_sources = (
        valid_income_sources.groupby(["accountGuid", "recurringScore"])
        .agg(
            recurring_count=("monthlyIncome", "count"),
            recurring_monthly=("monthlyIncome", "sum"),
        )
        .reset_index()
    )
    count_recurring_sources = count_recurring_sources.pivot(
        index="accountGuid",
        columns="recurringScore",
        values=["recurring_count", "recurring_monthly"],
    )
    count_recurring_sources.columns = ["_".join(col) for col in count_recurring_sources.columns]
    count_recurring_sources = count_recurring_sources.reset_index()

    summary_info = summaryInfo.drop(columns=["currentBalanceDate"])
    customer_level_data = (
        all_account_ids.merge(summary_info, on=config.IA_ACCOUNT_ID, how="left")
        .merge(
            cash_flow_data.drop(columns="spending"),
            on=config.IA_ACCOUNT_ID,
            how="left",
        )
        .merge(count_income_sources, on=config.IA_ACCOUNT_ID, how="left")
        .merge(count_income_sources2, on=config.IA_ACCOUNT_ID, how="left")
        .merge(total_income1, on=config.IA_ACCOUNT_ID, how="left")
        .merge(total_income2, on=config.IA_ACCOUNT_ID, how="left")
        .merge(count_loan_sources, on=config.IA_ACCOUNT_ID, how="left")
        .merge(count_active_sources, on=config.IA_ACCOUNT_ID, how="left")
        .merge(count_recurring_sources, on=config.IA_ACCOUNT_ID, how="left")
        .merge(atp_df, on=config.IA_ACCOUNT_ID, how="left")
    )
    model_input = customer_level_data.fillna(0)
    return model_input


def xgboost_prediction(
    model_input: pd.DataFrame,
    model_path: str,
    account_list: list,
    predicting_positive: bool = False,
    score_name="riskScore",
    custom_model_base_url=None,
):
    """
    Predicting any kind of scores generated by xgboost
    model_input: input feature dataframe that should contain all the relevant features
    model_path: path to the xgboost model, either a .pkl or a .json file
    account_list: list of account ids
    predicting_positive: whether the dependent measure is a positive thing, used to maintain the fact that the higher the score, the better the customer should be.
    """
    # Check if we can convert from pkl to json if it's a pkl file
    if "pkl" in model_path and not model_path.endswith(".json"):
        # Create equivalent .json path
        json_path = model_path.replace(".pkl", ".json")

        # If JSON version already exists, use it
        if os.path.exists(json_path):
            model = XGBClassifier()
            model.load_model(json_path)
        else:
            # Load the PKL file
            model = joblib.load(model_path)

            # If it's a standard XGBClassifier, save it in JSON format for future
            if isinstance(model, XGBClassifier):
                try:
                    # Explicitly specify JSON format to avoid the warning
                    model.save_model(json_path, format="json")
                    logger.info(f"Converted model from {model_path} to {json_path}")
                except Exception as e:
                    logger.error(f"Could not convert model: {e}")
    elif "json" in model_path:
        model = XGBClassifier()
        model.load_model(model_path)
    else:
        raise NotImplementedError("Model type not supported")

    ## temp solutions for version disturbance caused by autogluon
    if not hasattr(model, "n_classes_"):
        model.n_classes_ = 2

    model_features = list(model.get_booster().feature_names)
    for feature in model_features:
        if feature not in model_input.columns:
            model_input.loc[:, feature] = 0
    features = model_input[model_features]

    # Use a custom model for prediction if provided
    if custom_model_base_url is not None:
        df_pred = use_custom_model(custom_model_base_url, features)
    else:
        df_pred = pd.DataFrame(model.predict_proba(features))

    df_pred.columns = ["pred_0", "pred_1"]
    od = 100
    if not predicting_positive:
        df_pred[score_name] = df_pred["pred_0"].apply(lambda x: transform_score(x, od))
    else:
        df_pred[score_name] = df_pred["pred_1"].apply(lambda x: transform_score(x, od))
    df_pred[config.IA_ACCOUNT_ID] = account_list
    df_pred = df_pred[[config.IA_ACCOUNT_ID, score_name]]
    return df_pred, model, features


def use_custom_model(custom_model_base_url: str, features: pd.DataFrame) -> pd.DataFrame:
    client = ApiClient(base_url=custom_model_base_url)
    payload = features.to_dict()
    try:
        response = client.post(endpoint="/predict", data=payload)
        response_json = response.json()
        df_response = pd.DataFrame(response_json["probabilities"])
        return df_response
    except httpx.HTTPStatusError as e:
        logger.error(
            f"\nFailed to make request after retries. Status: {e.response.status_code}, Detail: {e.response.text}"
        )
    except httpx.RequestError as e:
        logger.error(f"\nNetwork or request error: {e}")
    except Exception as e:
        logger.error(f"\nAn unexpected error occurred: {e}")
    finally:
        client.close()


def make_scores(df_pred: pd.DataFrame, model_reasons: pd.DataFrame):
    output = {}
    output["accountLevel"] = {}
    output["accountLevel"]["modelScore"] = df_to_json(df_pred)
    if len(model_reasons) > 0:
        output["accountLevel"]["modelReasons"] = df_to_json(model_reasons)
    return output


def get_universal_reasons(
    account_id: str,
    income_df_sorted: pd.DataFrame,
    transactions_df: pd.DataFrame,
    as_of_date: pd.Timestamp | str | None,
) -> tuple[list, list]:
    """
    Generate universal reasons regardless of prediction scores.
    Returns tuple of (red_reasons, green_reasons)
    """
    red_reasons = []
    green_reasons = []

    if income_df_sorted is None or transactions_df is None or as_of_date is None:
        return red_reasons, green_reasons

    # Get account-specific data
    account_income = income_df_sorted[income_df_sorted["accountGuid"] == account_id]
    account_transactions = transactions_df[transactions_df["accountGuid"] == account_id]

    # Convert as_of_date to datetime
    as_of_date = pd.to_datetime(as_of_date)

    seven_days_ago = as_of_date - pd.Timedelta(days=7)

    # Convert transaction dates to datetime
    if not account_transactions.empty:
        account_transactions = account_transactions.copy()
        account_transactions["date"] = pd.to_datetime(account_transactions["date"])
        recent_transactions = account_transactions[account_transactions["date"] >= seven_days_ago]
    else:
        recent_transactions = pd.DataFrame()

    # 1. Check errorCode 401 or 402 in income_df_sorted
    if not account_income.empty:
        error_codes = account_income["errorCode"].values
        if any(code in [401, 402] for code in error_codes):
            red_reasons.append("Recent Payroll Absent - Job Loss Risk")

    # 2. Check loan deposits (transCategory=6, credit) within 7 days
    if not recent_transactions.empty:
        loan_deposits = recent_transactions[
            (recent_transactions["transCategory"] == 6) & (recent_transactions["type"].str.upper() == "CREDIT")
        ]
        if not loan_deposits.empty:
            red_reasons.append(f"{len(loan_deposits)} Loan(s) Funded within the week")

    # 3. Check loan payments (transCategory=6, debit) within 7 days
    if not recent_transactions.empty:
        loan_payments = recent_transactions[
            (recent_transactions["transCategory"] == 6) & (recent_transactions["type"].str.upper() == "DEBIT")
        ]
        if not loan_payments.empty:
            green_reasons.append(f"{len(loan_payments)} Loan Payment(s) made this week")

    # 4. Check overdrafts/NSF within 7 days using regex keywords
    if not recent_transactions.empty:
        # Keywords from overdraft_detection.py
        nsf_keywords = [
            r"\bnsf",
            r"\binsufficient funds\b",
            r"\binsufficient\b",
            r"\bnonsufficient\b",
            r"\bnon-sufficient\b",
            r"\bnon sufficient\b",
            r"\breturned item\b",
            r"\bunpaid item\b",
            r"\breturned check\b",
            r"\bret(urned)? ?chk\b",
            r"\bchargeback\b",
            r"\bdebit return\b",
            r"\bach return\b",
            r"\bpos return\b",
        ]
        overdraft_keywords = [
            r"\boverdraft\b",
            r"\boverdraft fee\b",
            r"\bod fee\b",
            r"\bpaid overdraft item\b",
            r"\bfee withdrawal overdrawn\b",
        ]
        all_keywords = nsf_keywords + overdraft_keywords

        overdraft_mask = recent_transactions["description"].str.contains("|".join(all_keywords), case=False, na=False)
        if overdraft_mask.any():
            red_reasons.append("Recent Overdraft Identified")

    # 5. Payroll spending analysis
    if not account_income.empty and not account_transactions.empty:
        spending_days = calculate_payroll_spending_days(account_id, account_income, account_transactions, as_of_date)
        if spending_days is not None:
            if spending_days <= 3:
                red_reasons.append("Unfavorable Spending Ratio - High Risk")
            elif spending_days >= 7:
                green_reasons.append("Good Spending Ratio - Low Risk")

    return red_reasons, green_reasons


def calculate_payroll_spending_days(
    account_id: str, account_income: pd.DataFrame, account_transactions: pd.DataFrame, as_of_date: pd.Timestamp
) -> float:
    """
    Calculate average days to spend payroll/benefit income
    """
    try:
        # Filter income sources with errorCode = 0 (stable income)
        stable_income = account_income[account_income["errorCode"] == 0]
        if stable_income.empty:
            return None

        spending_periods = []

        # Convert transaction dates to datetime and sort
        account_transactions = account_transactions.copy()
        account_transactions["date"] = pd.to_datetime(account_transactions["date"])
        account_transactions = account_transactions.sort_values("date")

        for _, income_source in stable_income.iterrows():
            if "historicalPayDay" not in income_source or not income_source["historicalPayDay"]:
                continue

            historical_paydays = income_source["historicalPayDay"]

            per_paycheck = income_source.get("perPayCheck", 0)
            if per_paycheck <= 0:
                continue

            # Process each payday
            for i, payday_str in enumerate(historical_paydays):
                payday = pd.to_datetime(payday_str)

                # Find next payday or use as_of_date if it's the last one
                if i < len(historical_paydays) - 1:
                    next_payday = pd.to_datetime(historical_paydays[i + 1])
                else:
                    next_payday = as_of_date

                # Calculate days to spend this paycheck
                days_to_spend = calculate_days_to_spend_paycheck(
                    account_transactions, payday, next_payday, per_paycheck
                )

                if days_to_spend is not None:
                    spending_periods.append(days_to_spend)

        if spending_periods:
            return sum(spending_periods) / len(spending_periods)
        else:
            return None

    except Exception as e:
        # Log error but don't fail the entire function
        logger.warning(f"Error calculating payroll spending days for account {account_id}: {str(e)}")
        return None


def calculate_days_to_spend_paycheck(
    transactions: pd.DataFrame, payday: pd.Timestamp, next_payday: pd.Timestamp, per_paycheck: float
) -> float:
    """
    Calculate days from payday until balance goes down by per_paycheck amount
    """
    try:
        if next_payday <= payday:
            return 0

        # Get transactions from payday onwards (up to, but not including, next payday)
        period_transactions = transactions[
            (transactions["date"] >= payday) & (transactions["date"] < next_payday)
        ].copy()

        if period_transactions.empty:
            return (next_payday - payday).days

        # Prepare daily net change by aggregating credits and debits per day
        period_transactions["date_only"] = period_transactions["date"].dt.normalize()
        period_transactions["signed_amount"] = period_transactions.apply(
            lambda row: row["amount"] if row["type"].upper() == "CREDIT" else -row["amount"], axis=1
        )
        daily_change = period_transactions.groupby("date_only")["signed_amount"].sum().sort_index()

        running_balance_change = 0.0
        current_day = payday.normalize()
        end_day = (next_payday - pd.Timedelta(microseconds=1)).normalize()

        while current_day <= end_day:
            running_balance_change += daily_change.get(current_day, 0.0)

            if running_balance_change <= -per_paycheck:
                # Use end-of-day timestamp to approximate elapsed time relative to payday
                day_marker = current_day + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                days_spent = int((day_marker - payday) // pd.Timedelta(days=1))
                return max(days_spent, 0)

            current_day += pd.Timedelta(days=1)

        # If balance never went down by per_paycheck amount, use full period
        return (next_payday - payday).days

    except Exception as e:
        logger.warning(f"Error calculating days to spend paycheck: {str(e)}")
        return None


def parse_model_reasons(
    explanation: pd.DataFrame,
    df_pred: pd.DataFrame,
    behaviorial_data: pd.DataFrame,
    redzone_features: pd.DataFrame,
    score_name: str = "riskScore",
    income_df_sorted: pd.DataFrame = None,
    transactions_df: pd.DataFrame = None,
    as_of_date: pd.Timestamp | None = None,
):
    """
    parse the top 3 positive and negative reasons for the model score into a list
    """
    LOW_REDZONE_SCORE_CM = settings.settings_dict["LOW_REDZONE_SCORE_CM"]
    red_accounts = df_pred[df_pred.loc[:, score_name] < LOW_REDZONE_SCORE_CM].accountGuid.unique()
    green_accounts = df_pred[df_pred.loc[:, score_name] >= LOW_REDZONE_SCORE_CM].accountGuid.unique()

    red_account_reasons = pd.DataFrame(
        explanation[(explanation.impact == "positive") & explanation.accountGuid.isin(red_accounts)]
        .groupby("accountGuid")
        .explanation.unique()
    ).reset_index()
    red_account_reasons.loc[:, "assessmentReasonsBad"] = red_account_reasons.explanation.apply(lambda x: list(x))
    red_account_reasons = red_account_reasons.merge(
        behaviorial_data[["accountGuid", "alerts"]], on="accountGuid", how="left"
    )
    red_account_reasons_good = pd.DataFrame(
        explanation[(explanation.impact == "negative") & explanation.accountGuid.isin(red_accounts)]
        .groupby("accountGuid")
        .explanation.unique()
    ).reset_index()
    red_account_reasons_good.loc[:, "assessmentReasonsGoodSHAP"] = red_account_reasons_good.explanation.apply(
        lambda x: list(x)
    )
    red_reasons = red_account_reasons.merge(
        red_account_reasons_good[["accountGuid", "assessmentReasonsGoodSHAP"]], on="accountGuid", how="inner"
    )
    red_reasons.loc[:, "assessmentReasonsBad"] = red_reasons.apply(lambda x: x.assessmentReasonsBad + x.alerts, axis=1)
    if not red_reasons.empty:
        red_reasons.loc[:, "assessmentReasonsGood"] = red_reasons.apply(
            lambda x: assign_rule_based_reasons(x, redzone_features, type="Good"), axis=1
        )
    else:
        red_reasons.loc[:, "assessmentReasonsGood"] = []
    red_reasons = red_reasons.drop(columns=["assessmentReasonsGoodSHAP", "alerts"])

    green_account_reasons = pd.DataFrame(
        explanation[(explanation.impact == "negative") & (explanation.accountGuid.isin(green_accounts))]
        .groupby("accountGuid")
        .explanation.unique()
    ).reset_index()
    green_account_reasons.loc[:, "assessmentReasonsGood"] = green_account_reasons.explanation.apply(lambda x: list(x))
    green_account_reasons_bad = pd.DataFrame(
        explanation[(explanation.impact == "positive") & (explanation.accountGuid.isin(green_accounts))]
        .groupby("accountGuid")
        .explanation.unique()
    ).reset_index()
    green_account_reasons_bad.loc[:, "assessmentReasonsBadSHAP"] = green_account_reasons_bad.explanation.apply(
        lambda x: list(x)
    )
    green_reasons = green_account_reasons.merge(
        green_account_reasons_bad[["accountGuid", "assessmentReasonsBadSHAP"]], on="accountGuid", how="inner"
    )
    if not green_reasons.empty:
        green_reasons.loc[:, "assessmentReasonsBad"] = green_reasons.apply(
            lambda x: assign_rule_based_reasons(x, redzone_features, type="Bad"), axis=1
        )
    else:
        green_reasons.loc[:, "assessmentReasonsBad"] = []
    green_reasons = green_reasons.drop(columns="assessmentReasonsBadSHAP")

    # Handle empty dataframe concatenation to avoid warnings
    frames_to_concat = []
    if not red_reasons.empty:
        frames_to_concat.append(red_reasons)
    if not green_reasons.empty:
        frames_to_concat.append(green_reasons)

    if frames_to_concat:
        reasons = pd.concat(frames_to_concat, axis=0).reset_index(drop=True)
    else:
        # Create an empty DataFrame with expected columns
        # Create a list of columns that would be expected in the result
        expected_columns = ["accountGuid", "explanation", "assessmentReasonsGood", "assessmentReasonsBad"]

        # Create an empty DataFrame with those columns
        reasons = pd.DataFrame(columns=expected_columns)

    # Add universal reasons for all accounts
    if income_df_sorted is not None and transactions_df is not None and as_of_date is not None:
        all_accounts = df_pred["accountGuid"].unique()
        for account_id in all_accounts:
            universal_red, universal_green = get_universal_reasons(
                account_id,
                income_df_sorted,
                transactions_df,
                as_of_date=as_of_date,
            )

            # Find or create row for this account
            account_row_idx = reasons[reasons["accountGuid"] == account_id].index
            if len(account_row_idx) > 0:
                # Account exists, add universal reasons to existing lists
                idx = account_row_idx[0]
                current_bad = reasons.loc[idx, "assessmentReasonsBad"]
                current_good = reasons.loc[idx, "assessmentReasonsGood"]

                if isinstance(current_bad, list):
                    reasons.at[idx, "assessmentReasonsBad"] = current_bad + universal_red
                else:
                    reasons.at[idx, "assessmentReasonsBad"] = universal_red

                if isinstance(current_good, list):
                    reasons.at[idx, "assessmentReasonsGood"] = current_good + universal_green
                else:
                    reasons.at[idx, "assessmentReasonsGood"] = universal_green
            else:
                # Account doesn't exist, create new row
                new_row = pd.DataFrame(
                    {
                        "accountGuid": [account_id],
                        "explanation": [[]],
                        "assessmentReasonsBad": [universal_red],
                        "assessmentReasonsGood": [universal_green],
                    }
                )
                reasons = pd.concat([reasons, new_row], ignore_index=True)

    reasons.loc[:, "assessmentReasonsBad"] = reasons.loc[:, "assessmentReasonsBad"].apply(
        lambda alert_list: deduplicate_list(alert_list) if isinstance(alert_list, list) else []
    )

    reasons.loc[:, "assessmentReasonsGood"] = reasons.loc[:, "assessmentReasonsGood"].apply(
        lambda alert_list: deduplicate_list(alert_list) if isinstance(alert_list, list) else []
    )
    return reasons


def assign_rule_based_reasons(row, redzone_features, type="Good"):
    """
    Assign rule-based reasons based on the redzone features.
    This function checks specific conditions in the redzone_features DataFrame
    and returns a list of reasons if any condition is met.
    """
    reasons = []
    account_id = row[config.IA_ACCOUNT_ID]
    features = redzone_features[redzone_features[config.IA_ACCOUNT_ID] == account_id]
    if type == "Good":
        bad_reasons = row["assessmentReasonsBad"]
        good_reasons = row["assessmentReasonsGoodSHAP"]
        if "Considerable Loan Payback History" in good_reasons:
            # and "High Borrowing Activity" not in bad_reasons:
            reasons.append("Considerable Loan Payback History")

        # if features.recurringMonthlyIncome.iloc[0] >= 2000 and "Low Recurring Income" not in bad_reasons and "Limited Total Inflow" not in bad_reasons and "Low Active Income" not in bad_reasons:
        if (
            features.recurringMonthlyIncome.iloc[0] >= 2000
            and "Limited Total Inflow" not in bad_reasons
            and "Low Active Income" not in bad_reasons
        ):
            reasons.append("Considerable Recurring Income")

    if type == "Bad":
        bad_reasons = row["assessmentReasonsBadSHAP"]
        good_reasons = row["assessmentReasonsGood"]
        # if "High Borrowing Activity" in bad_reasons and "Considerable Loan Payback History" not in good_reasons:
        if "High Borrowing Activity" in bad_reasons:
            reasons.append("Multiple loan Credit Found, Possible Loan Stacker")

        if features.odAll.iloc[0] > 0 and "Low Overdraft/NSF Count" not in good_reasons:
            reasons.append("Overdrafts/NSF Found in Transactions")

    # Add more conditions as needed
    return reasons
