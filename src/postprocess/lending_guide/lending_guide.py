import pandas as pd

from postprocess.lending_guide.debit_date import payment_near_holiday, recommend_debit_date
from postprocess.lending_guide.get_repeat_opportunity import get_repeat_opportunity
from postprocess.lending_guide.loan_amount import recommend_debit_amount, recommend_loan_amount


def append_customer_level_lending_guide(extracted_features: dict[str, list[dict]]):
    summary_info = pd.DataFrame(extracted_features["summaryInfo"])
    lending_guide = get_lending_guide(
        # pd.DataFrame.from_dict(extracted_features["redZoneBehavior"]),
        summary_info[["accountGuid", "riskBehavior", "riskScore"]],
        pd.DataFrame.from_dict(extracted_features["incomeSources"]),
        extracted_features["scores"],
    )
    extracted_features["lendingGuide"] = lending_guide
    return extracted_features


def append_account_level_lending_guides(extracted_features: dict[str, list[dict]]):
    summary_info = pd.DataFrame(extracted_features["summaryInfo"])
    account_level_lending_guide = get_lending_guide_account(
        summary_info[["accountGuid", "riskBehavior", "riskScore"]],
        pd.DataFrame.from_dict(extracted_features["incomeSources"]),
        extracted_features["scores"],
    )
    extracted_features["accounts"] = []
    for i in range(len(account_level_lending_guide)):
        lending_guide_dict = {}
        lending_guide_dict["accountGuid"] = account_level_lending_guide.loc[:, "accountGuid"].iloc[i]
        lending_guide_dict["lendingGuide"] = {}
        for column in account_level_lending_guide.columns:
            if column != "accountGuid":
                lending_guide_dict["lendingGuide"][column] = account_level_lending_guide.loc[:, column].iloc[i]
        extracted_features["accounts"].append(lending_guide_dict)
    return extracted_features


def get_lending_guide(redZoneBehavior: pd.DataFrame, income_sources: pd.DataFrame, scores: dict) -> dict:
    """
    Generates a lending guide based on the red zone behavior and income sources of a customer.
    """
    min_loan_amount, max_loan_amount = recommend_loan_amount(redZoneBehavior)
    min_debit_amount, max_debit_amount = recommend_debit_amount(redZoneBehavior)
    customer_income_type, debit_frequency, debit_date = recommend_debit_date(income_sources)
    payment_behavior_near_holiday, next_payment_on_holiday = payment_near_holiday(income_sources)
    lending_guide = dict()
    lending_guide["minLoanAmount"] = min_loan_amount
    lending_guide["maxLoanAmount"] = max_loan_amount
    lending_guide["minDebitAmount"] = min_debit_amount
    lending_guide["maxDebitAmount"] = max_debit_amount
    lending_guide["customerIncomeType"] = customer_income_type
    lending_guide["debitFrequency"] = debit_frequency
    lending_guide["debitDate"] = debit_date
    lending_guide["paymentNearHoliday"] = payment_behavior_near_holiday
    lending_guide["nextPaymentOnHoliday"] = next_payment_on_holiday
    lending_guide["repeatOpportunity"] = get_repeat_opportunity(
        pd.DataFrame.from_dict(scores["repeat"]["customerLevel"]["modelScore"]).repeatScore.iloc[0],
    )
    return lending_guide


def get_lending_guide_account(redZoneBehavior: pd.DataFrame, income_sources: pd.DataFrame, scores: dict) -> dict:
    """
    LendingGuide at account level
    """
    loan_amount_reccomendation = (
        redZoneBehavior.groupby("accountGuid")
        .apply(recommend_loan_amount)
        .reset_index()
        .rename(columns={0: "recommendedLoanAmount"})
    )
    loan_amount_reccomendation.loc[:, "minLoanAmount"] = loan_amount_reccomendation["recommendedLoanAmount"].apply(
        lambda x: x[0]
    )
    loan_amount_reccomendation.loc[:, "maxLoanAmount"] = loan_amount_reccomendation["recommendedLoanAmount"].apply(
        lambda x: x[1]
    )

    debit_amount_recommendation = (
        redZoneBehavior.groupby("accountGuid")
        .apply(recommend_debit_amount)
        .reset_index()
        .rename(columns={0: "recommendedDebitAmount"})
    )
    debit_amount_recommendation.loc[:, "minDebitAmount"] = debit_amount_recommendation["recommendedDebitAmount"].apply(
        lambda x: x[0]
    )
    debit_amount_recommendation.loc[:, "maxDebitAmount"] = debit_amount_recommendation["recommendedDebitAmount"].apply(
        lambda x: x[1]
    )

    debit_date_recommendation = (
        income_sources.groupby("accountGuid")
        .apply(recommend_debit_date)
        .reset_index()
        .rename(columns={0: "recommendedDebitDate"})
    )
    debit_date_recommendation.loc[:, "customerIncomeType"] = debit_date_recommendation["recommendedDebitDate"].apply(
        lambda x: x[0]
    )
    debit_date_recommendation.loc[:, "debitFrequency"] = debit_date_recommendation["recommendedDebitDate"].apply(
        lambda x: x[1]
    )
    debit_date_recommendation.loc[:, "debitDate"] = debit_date_recommendation["recommendedDebitDate"].apply(
        lambda x: x[2]
    )

    payment_near_holiday_recommendation = (
        income_sources.groupby("accountGuid")
        .apply(payment_near_holiday)
        .reset_index()
        .rename(columns={0: "recommendedPaymentNearHoliday"})
    )
    payment_near_holiday_recommendation.loc[:, "paymentNearHoliday"] = payment_near_holiday_recommendation[
        "recommendedPaymentNearHoliday"
    ].apply(lambda x: x[0])
    payment_near_holiday_recommendation.loc[:, "nextPaymentOnHoliday"] = payment_near_holiday_recommendation[
        "recommendedPaymentNearHoliday"
    ].apply(lambda x: x[1])

    # add account level repeat opportunity
    account_level_repeat_scores = pd.DataFrame.from_dict(scores["repeat"]["accountLevel"]["modelScore"])
    account_level_repeat_scores.loc[:, "repeatOpportunity"] = account_level_repeat_scores["repeatScore"].apply(
        lambda x: get_repeat_opportunity(x)
    )

    account_level_lending_guide = (
        loan_amount_reccomendation.merge(debit_amount_recommendation, on="accountGuid")
        .merge(debit_date_recommendation, on="accountGuid")
        .merge(payment_near_holiday_recommendation, on="accountGuid")
        .merge(
            account_level_repeat_scores[["accountGuid", "repeatOpportunity"]],
            on="accountGuid",
        )
        .reset_index(drop=True)
    )

    account_level_lending_guide = account_level_lending_guide.drop(
        columns=[
            "recommendedLoanAmount",
            "recommendedDebitAmount",
            "recommendedDebitDate",
            "recommendedPaymentNearHoliday",
        ]
    )

    # specify loan amount schema
    account_level_lending_guide = account_level_lending_guide.astype(
        dtype={
            "minLoanAmount": "float64",
            "maxLoanAmount": "float64",
            "minDebitAmount": "float64",
            "maxDebitAmount": "float64",
        }
    )
    return account_level_lending_guide
