import numpy as np
import pandas as pd

from config import config
from postprocess.sources.helpers.calculate_frequency_amount import (
    active_income_check,
    amount_stability_check,
    calculate_frequency_amount,
    recurring_income_check,
)
from postprocess.sources.helpers.find_missing_payment import find_missing_payment
from utils.decorators import timer

# Benefit source is basically copied from payroll source


class BenefitSource:
    """Class for functions related to determining information about benefit sources, frequency, and amounts."""

    @staticmethod
    @timer
    def categorize_income_source(
        result: pd.DataFrame,
        income_source_trans: pd.DataFrame,
        as_of_date: pd.Timestamp,
        sourceID=0,
    ) -> tuple[dict, pd.DataFrame, int]:
        """Returns the benefit source categories given the transactions."""

        holidays = config.HOLIDAYS
        income_source_dict = {}

        # 1:payroll, 2:benefit, 3:transfer, 4:deposit, 5: gig, 6:loan
        result = result[result.type == "CREDIT"]

        customer_df = result[result["transCategory"] == 2]

        if len(customer_df) == 0:
            for account_id in result[config.PS_ACCOUNT_ID].unique():
                income_source_dict[account_id] = {
                    "accountGuid": account_id,
                    "sourceID": "None",
                    "sourceName": "None",
                    "sourceType": "None",
                    "sourceChannel": "None",
                    "numOfPay": 0,
                    "numOfPayMonthly": 0,
                    "frequency": "None",
                    "perPayCheck": 0,
                    "monthlyIncome": 0,
                    "stableMonthlyIncome": 0,
                    "regularPayDay": "None",
                    "historicalPayDay": [],
                    "missingPayDay": [],
                    "sameDayFreq": 0,
                    "lastPayDay": "None",
                    "incomeType": "None",
                    "depositMethod": "None",
                    "activeScore": 0,
                    "recurringScore": 0,
                    "stabilityScore": 0,
                    "errorCode": 102,
                    "errorMessage": "Benefit income not found",
                    "nextPayDay": "Not Applicable",
                    "paymentNearHoliday": "None",
                    "nextPayDayOnHoliday": "Not Applicable",
                }
            return income_source_dict, income_source_trans, sourceID

        if len(customer_df) > 0:
            # Process separately for each account_guid
            for account_id in customer_df[config.PS_ACCOUNT_ID].unique():
                account_df = customer_df[customer_df[config.IA_ACCOUNT_ID] == account_id]

                for i in list(set(account_df.cluster_label)):
                    cluster = str(account_id) + "_" + str(i)
                    target = account_df[account_df.cluster_label == i].sort_values(config.PS_TXN_DATE)
                    source_name = target[config.PS_TXN_SHORT].unique()[0]
                    same_day_amount = (
                        target[[config.PS_TXN_DATE, config.PS_TXN_AMOUNT]]
                        .groupby(config.PS_TXN_DATE)
                        .sum()
                        .reset_index()
                    )
                    num_of_payday = len(same_day_amount)
                    per_paycheck = same_day_amount[config.PS_TXN_AMOUNT].mean()
                    last_payday = pd.to_datetime(target[config.PS_TXN_DATE]).max()
                    income_type = "Benefit"
                    historicalPayDay = list(
                        target[[config.PS_TXN_DATE, config.PS_TXN_AMOUNT]]
                        .groupby(config.PS_TXN_DATE)
                        .sum()
                        .reset_index()
                        .date
                    )

                    # Same day/single trans check
                    (
                        freq,
                        monthly_income,
                        monthly_num_pay,
                        regular_payday,
                        same_day_freq,
                        next_pay_day,
                        payment_near_holiday,
                        next_pay_day_on_holiday,
                    ) = calculate_frequency_amount(target, holidays, ignore_small_amounts=True)
                    active_score = active_income_check(target, as_of_date, freq, "Benefit")
                    recurring_score = recurring_income_check(target, freq, regular_payday, same_day_freq)
                    stability_score, std_mean_ratio = amount_stability_check(target, freq)
                    if stability_score != 3:
                        stable_monthly_income = monthly_income * (1 - std_mean_ratio)
                    else:
                        stable_monthly_income = monthly_income
                    recency = (as_of_date - last_payday) / np.timedelta64(1, "D")

                    # Amount check
                    if per_paycheck < config.PS_LOW_AMOUNT_CHECK:
                        income_source_dict[cluster] = {
                            "accountGuid": account_id,
                            "sourceID": "None",
                            "sourceName": source_name,
                            "sourceType": "None",
                            "sourceChannel": "None",
                            "numOfPay": num_of_payday,
                            "numOfPayMonthly": int(monthly_num_pay),
                            "frequency": freq,
                            "perPayCheck": round(per_paycheck, 2),
                            "monthlyIncome": round(monthly_income, 2),
                            "stableMonthlyIncome": round(stable_monthly_income, 2),
                            "regularPayDay": regular_payday,
                            "historicalPayDay": historicalPayDay,
                            "missingPayDay": [],
                            "sameDayFreq": same_day_freq,
                            "lastPayDay": last_payday.strftime("%Y-%m-%d"),
                            "incomeType": income_type,
                            "depositMethod": "Direct Deposit",
                            "activeScore": active_score,
                            "recurringScore": recurring_score,
                            "stabilityScore": stability_score,
                            "errorCode": 302,
                            "errorMessage": "Benefit Per_paycheck lower than $" + str(config.PS_LOW_AMOUNT_CHECK),
                            "nextPayDay": "Not Applicable",
                            "paymentNearHoliday": "None",
                            "nextPayDayOnHoliday": "Not Applicable",
                        }
                        continue

                    if num_of_payday == 1:
                        sourceID += 1
                        income_source_dict[cluster] = {
                            "accountGuid": account_id,
                            "sourceID": "I" + str(sourceID) + "_err_202",
                            "sourceName": source_name,
                            "sourceType": "None",
                            "sourceChannel": "None",
                            "numOfPay": 1,
                            "numOfPayMonthly": 0,
                            "frequency": "None",
                            "perPayCheck": round(per_paycheck, 2),
                            "monthlyIncome": round(monthly_income, 2),
                            "stableMonthlyIncome": round(stable_monthly_income, 2),
                            "regularPayDay": "None",
                            "historicalPayDay": historicalPayDay,
                            "missingPayDay": [],
                            "sameDayFreq": 0,
                            "lastPayDay": last_payday.strftime("%Y-%m-%d"),
                            "incomeType": income_type,
                            "depositMethod": "Direct Deposit",
                            "activeScore": active_score,
                            "recurringScore": recurring_score,
                            "stabilityScore": stability_score,
                            "errorCode": 202,
                            "errorMessage": "Benefit only occurred once/on the same day",
                            "nextPayDay": "Not Applicable",
                            "paymentNearHoliday": "None",
                            "nextPayDayOnHoliday": "Not Applicable",
                        }
                        income_source_trans.loc[
                            (income_source_trans.cluster_label == i) & (income_source_trans.accountGuid == account_id),
                            "sourceID",
                        ] = "I" + str(sourceID) + "_err_202"
                        continue

                    missing_payday = find_missing_payment(historicalPayDay, freq)

                    # Skip if the income not seen within a certain peirod of time
                    if freq == "W":
                        if recency > config.PS_RECENCY_CHECK_W:
                            sourceID += 1
                            income_source_dict[cluster] = {
                                "accountGuid": account_id,
                                "sourceID": "I" + str(sourceID) + "_err_402",
                                "sourceName": source_name,
                                "sourceType": "None",
                                "sourceChannel": "None",
                                "numOfPay": num_of_payday,
                                "numOfPayMonthly": int(monthly_num_pay),
                                "frequency": freq,
                                "perPayCheck": round(per_paycheck, 2),
                                "monthlyIncome": round(monthly_income, 2),
                                "stableMonthlyIncome": round(stable_monthly_income, 2),
                                "regularPayDay": regular_payday,
                                "historicalPayDay": historicalPayDay,
                                "missingPayDay": missing_payday,
                                "sameDayFreq": same_day_freq,
                                "lastPayDay": last_payday.strftime("%Y-%m-%d"),
                                "incomeType": income_type,
                                "depositMethod": "Direct Deposit",
                                "activeScore": active_score,
                                "recurringScore": recurring_score,
                                "stabilityScore": stability_score,
                                "errorCode": 402,
                                "errorMessage": "Benefit income not seen within "
                                + str(config.PS_RECENCY_CHECK_W)
                                + " days",
                                "nextPayDay": "Not Applicable",
                                "paymentNearHoliday": "None",
                                "nextPayDayOnHoliday": "Not Applicable",
                            }
                            income_source_trans.loc[
                                (income_source_trans.cluster_label == i)
                                & (income_source_trans.accountGuid == account_id),
                                "sourceID",
                            ] = "I" + str(sourceID) + "_err_402"
                            continue

                    elif freq == "B":
                        if recency > config.PS_RECENCY_CHECK_B:
                            sourceID += 1
                            income_source_dict[cluster] = {
                                "accountGuid": account_id,
                                "sourceID": "I" + str(sourceID) + "_err_402",
                                "sourceName": source_name,
                                "sourceType": "None",
                                "sourceChannel": "None",
                                "numOfPay": num_of_payday,
                                "numOfPayMonthly": int(monthly_num_pay),
                                "frequency": freq,
                                "perPayCheck": round(per_paycheck, 2),
                                "monthlyIncome": round(monthly_income, 2),
                                "stableMonthlyIncome": round(stable_monthly_income, 2),
                                "regularPayDay": regular_payday,
                                "historicalPayDay": historicalPayDay,
                                "missingPayDay": missing_payday,
                                "sameDayFreq": same_day_freq,
                                "lastPayDay": last_payday.strftime("%Y-%m-%d"),
                                "incomeType": income_type,
                                "depositMethod": "Direct Deposit",
                                "activeScore": active_score,
                                "recurringScore": recurring_score,
                                "stabilityScore": stability_score,
                                "errorCode": 402,
                                "errorMessage": "Benefit income not seen within "
                                + str(config.PS_RECENCY_CHECK_B)
                                + " days",
                                "nextPayDay": "Not Applicable",
                                "paymentNearHoliday": "None",
                                "nextPayDayOnHoliday": "Not Applicable",
                            }
                            income_source_trans.loc[
                                (income_source_trans.cluster_label == i)
                                & (income_source_trans.accountGuid == account_id),
                                "sourceID",
                            ] = "I" + str(sourceID) + "_err_402"
                            continue

                    elif freq == "S":
                        if recency > config.PS_RECENCY_CHECK_S:
                            sourceID += 1
                            income_source_dict[cluster] = {
                                "accountGuid": account_id,
                                "sourceID": "I" + str(sourceID) + "_err_402",
                                "sourceName": source_name,
                                "sourceType": "None",
                                "sourceChannel": "None",
                                "numOfPay": num_of_payday,
                                "numOfPayMonthly": int(monthly_num_pay),
                                "frequency": freq,
                                "perPayCheck": round(per_paycheck, 2),
                                "monthlyIncome": round(monthly_income, 2),
                                "stableMonthlyIncome": round(stable_monthly_income, 2),
                                "regularPayDay": regular_payday,
                                "historicalPayDay": historicalPayDay,
                                "missingPayDay": missing_payday,
                                "sameDayFreq": same_day_freq,
                                "lastPayDay": last_payday.strftime("%Y-%m-%d"),
                                "incomeType": income_type,
                                "depositMethod": "Direct Deposit",
                                "activeScore": active_score,
                                "recurringScore": recurring_score,
                                "stabilityScore": stability_score,
                                "errorCode": 402,
                                "errorMessage": "Benefit income not seen within "
                                + str(config.PS_RECENCY_CHECK_S)
                                + " days",
                                "nextPayDay": "Not Applicable",
                                "paymentNearHoliday": "None",
                                "nextPayDayOnHoliday": "Not Applicable",
                            }
                            income_source_trans.loc[
                                (income_source_trans.cluster_label == i)
                                & (income_source_trans.accountGuid == account_id),
                                "sourceID",
                            ] = "I" + str(sourceID) + "_err_402"
                            continue

                    elif freq == "M":
                        if recency > config.PS_RECENCY_CHECK_M:
                            sourceID += 1
                            income_source_dict[cluster] = {
                                "accountGuid": account_id,
                                "sourceID": "I" + str(sourceID) + "_err_402",
                                "sourceName": source_name,
                                "sourceType": "None",
                                "sourceChannel": "None",
                                "numOfPay": num_of_payday,
                                "numOfPayMonthly": int(monthly_num_pay),
                                "frequency": freq,
                                "perPayCheck": round(per_paycheck, 2),
                                "monthlyIncome": round(monthly_income, 2),
                                "stableMonthlyIncome": round(stable_monthly_income, 2),
                                "regularPayDay": regular_payday,
                                "historicalPayDay": historicalPayDay,
                                "missingPayDay": missing_payday,
                                "sameDayFreq": same_day_freq,
                                "lastPayDay": last_payday.strftime("%Y-%m-%d"),
                                "incomeType": income_type,
                                "depositMethod": "Direct Deposit",
                                "activeScore": active_score,
                                "recurringScore": recurring_score,
                                "stabilityScore": stability_score,
                                "errorCode": 402,
                                "errorMessage": "Benefit income not seen within "
                                + str(config.PS_RECENCY_CHECK_M)
                                + " days",
                                "nextPayDay": "Not Applicable",
                                "paymentNearHoliday": "None",
                                "nextPayDayOnHoliday": "Not Applicable",
                            }
                            income_source_trans.loc[
                                (income_source_trans.cluster_label == i)
                                & (income_source_trans.accountGuid == account_id),
                                "sourceID",
                            ] = "I" + str(sourceID) + "_err_402"
                            continue

                    sourceID += 1
                    income_source_dict[cluster] = {
                        "accountGuid": account_id,
                        "sourceID": "I" + str(sourceID) + "_err_000",
                        "sourceName": source_name,
                        "sourceType": "None",
                        "sourceChannel": "None",
                        "numOfPay": num_of_payday,
                        "numOfPayMonthly": int(monthly_num_pay),
                        "frequency": freq,
                        "perPayCheck": round(per_paycheck, 2),
                        "monthlyIncome": round(monthly_income, 2),
                        "stableMonthlyIncome": round(stable_monthly_income, 2),
                        "regularPayDay": regular_payday,
                        "historicalPayDay": historicalPayDay,
                        "missingPayDay": missing_payday,
                        "sameDayFreq": same_day_freq,
                        "lastPayDay": last_payday.strftime("%Y-%m-%d"),
                        "incomeType": income_type,
                        "depositMethod": "Direct Deposit",
                        "activeScore": active_score,
                        "recurringScore": recurring_score,
                        "stabilityScore": stability_score,
                        "errorCode": 000,
                        "errorMessage": "NA",
                        "nextPayDay": next_pay_day,
                        "paymentNearHoliday": payment_near_holiday,
                        "nextPayDayOnHoliday": "True" if next_pay_day_on_holiday else "False",
                    }

                    # Add sourceID to income_trans

                    income_source_trans.loc[
                        (income_source_trans.cluster_label == i) & (income_source_trans.accountGuid == account_id),
                        "sourceID",
                    ] = "I" + str(sourceID) + "_err_000"

        return income_source_dict, income_source_trans, sourceID
