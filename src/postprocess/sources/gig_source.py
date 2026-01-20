import numpy as np
import pandas as pd
from config import config
from utils.decorators import timer

from postprocess.sources.helpers.calculate_frequency_amount import (
    active_income_check,
    amount_stability_check,
    calculate_frequency_amount,
    recurring_income_check,
)


class GigSource:
    """Class for functions related to determining information about gig income sources, frequency, and amounts."""

    @staticmethod
    @timer
    def categorize_income_source(
        result: pd.DataFrame,
        income_source_trans: pd.DataFrame,
        as_of_date: pd.Timestamp,
        sourceID=0,
    ) -> tuple[dict, pd.DataFrame, int]:
        """Returns the gig income source categories given the transactions."""

        # Load holidays for payday prediction
        holidays = config.HOLIDAYS
        income_source_dict = {}

        # Only consider credit for now
        result = result[result.type == "CREDIT"]

        # Use simple rule for separating deposit and transfer for null
        # fee is a negative keyword for transfer but model does not pick it out
        result = result[result.type == "CREDIT"]

        # Output the income_source_trans
        customer_df = result[result["transCategory"] == 5]

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
                    "errorCode": 103,
                    "errorMessage": "Gig income not found",
                    "nextPayDay": "Not Applicable",
                    "paymentNearHoliday": "None",
                    "nextPayDayOnHoliday": "Not Applicable",
                }
            return income_source_dict, income_source_trans, sourceID

        if len(customer_df) > 0:
            # Process separately for each account_guid
            for account_id in customer_df[config.PS_ACCOUNT_ID].unique():
                target = customer_df[
                    (customer_df.transCategory == 5) & (customer_df[config.IA_ACCOUNT_ID] == account_id)
                ].sort_values(config.PS_TXN_DATE)
                if len(target) == 0:
                    continue
                income_type = "gig"
                source_name = "gig"
                cluster = str(account_id) + "_" + "gig"

                # Group sameday transactions into one, this is for getting the historical payday
                same_day_amount = (
                    target[[config.PS_TXN_DATE, config.PS_TXN_AMOUNT]].groupby(config.PS_TXN_DATE).sum().reset_index()
                )
                num_of_payday = len(same_day_amount)
                per_paycheck = same_day_amount[config.PS_TXN_AMOUNT].mean()
                last_payday = pd.to_datetime(target[config.PS_TXN_DATE]).max()
                historicalPayDay = list(same_day_amount[config.PS_TXN_DATE])
                total_days = (target[config.PS_TXN_DATE].max() - target[config.PS_TXN_DATE].min()) / np.timedelta64(
                    1, "D"
                )
                monthlyIncome = round(per_paycheck * num_of_payday / max((total_days / 30), 1), 2)

                (
                    freq,
                    _,
                    _,
                    regular_payday,
                    same_day_freq,
                    next_pay_day,
                    payment_near_holiday,
                    next_pay_day_on_holiday,
                ) = calculate_frequency_amount(same_day_amount, holidays)
                active_score = active_income_check(same_day_amount, as_of_date, freq, "Gig")
                recurring_score = recurring_income_check(same_day_amount, freq, regular_payday, same_day_freq)
                stability_score, std_mean_ratio = amount_stability_check(same_day_amount, freq)
                if stability_score != 3:
                    stable_monthly_income = monthlyIncome * (1 - std_mean_ratio)
                else:
                    stable_monthly_income = monthlyIncome
                if recurring_score != 3:
                    regular_payday, same_day_freq = "None", 0

                if num_of_payday == 1:
                    sourceID += 1
                    income_source_dict[cluster] = {
                        "accountGuid": account_id,
                        "sourceID": "I" + str(sourceID) + "_err_203",
                        "sourceName": source_name,
                        "sourceType": "None",
                        "sourceChannel": "None",
                        "numOfPay": num_of_payday,
                        "numOfPayMonthly": 0,
                        "frequency": "I",
                        "perPayCheck": round(per_paycheck, 2),
                        "monthlyIncome": round(monthlyIncome, 2),
                        "stableMonthlyIncome": round(stable_monthly_income, 2),
                        "regularPayDay": "None",
                        "historicalPayDay": historicalPayDay,
                        "missingPayDay": [],
                        "sameDayFreq": 0,
                        "lastPayDay": last_payday.strftime("%Y-%m-%d"),
                        "incomeType": income_type,
                        "depositMethod": "None",
                        "activeScore": active_score,
                        "recurringScore": recurring_score,
                        "stabilityScore": stability_score,
                        "errorCode": 203,
                        "errorMessage": "Gig only occurred once/on the same day",
                        "nextPayDay": "Not Applicable",
                        "paymentNearHoliday": "None",
                        "nextPayDayOnHoliday": "Not Applicable",
                    }
                    income_source_trans.loc[
                        (income_source_trans.transCategory == 5) & (income_source_trans.accountGuid == account_id),
                        "sourceID",
                    ] = "I" + str(sourceID) + "_err_203"
                    continue

                recency = (as_of_date - last_payday) / np.timedelta64(1, "D")

                if recency > config.PS_RECENCY_CHECK:
                    sourceID += 1
                    income_source_dict[cluster] = {
                        "accountGuid": account_id,
                        "sourceID": "I" + str(sourceID) + "_err_403",
                        "sourceName": source_name,
                        "sourceType": "None",
                        "sourceChannel": "None",
                        "numOfPay": num_of_payday,
                        "numOfPayMonthly": 0,
                        "frequency": freq,
                        "perPayCheck": round(per_paycheck, 2),
                        "monthlyIncome": round(monthlyIncome, 2),
                        "stableMonthlyIncome": round(stable_monthly_income, 2),
                        "regularPayDay": regular_payday,
                        "historicalPayDay": historicalPayDay,
                        "missingPayDay": [],
                        "sameDayFreq": same_day_freq,
                        "lastPayDay": last_payday.strftime("%Y-%m-%d"),
                        "incomeType": income_type,
                        "depositMethod": "None",
                        "activeScore": active_score,
                        "recurringScore": recurring_score,
                        "stabilityScore": stability_score,
                        "errorCode": 403,
                        "errorMessage": "GIG income not seen within " + str(config.PS_RECENCY_CHECK) + " days",
                        "nextPayDay": "Not Applicable",
                        "paymentNearHoliday": "None",
                        "nextPayDayOnHoliday": "Not Applicable",
                    }
                    income_source_trans.loc[
                        (income_source_trans.transCategory == 5) & (income_source_trans.accountGuid == account_id),
                        "sourceID",
                    ] = "I" + str(sourceID) + "_err_403"
                    continue
                sourceID += 1
                income_source_dict[cluster] = {
                    "accountGuid": account_id,
                    "sourceName": source_name,
                    "sourceID": "I" + str(sourceID) + "_err_000",
                    "sourceType": "None",
                    "sourceChannel": "None",
                    "numOfPay": num_of_payday,
                    "numOfPayMonthly": 0,
                    "frequency": freq,
                    "perPayCheck": round(per_paycheck, 2),
                    "monthlyIncome": round(monthlyIncome, 2),
                    "stableMonthlyIncome": round(stable_monthly_income, 2),
                    "regularPayDay": regular_payday,
                    "historicalPayDay": historicalPayDay,
                    "missingPayDay": [],
                    "sameDayFreq": same_day_freq,
                    "lastPayDay": last_payday.strftime("%Y-%m-%d"),
                    "incomeType": income_type,
                    "depositMethod": "None",
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
                    (income_source_trans.transCategory == 5) & (income_source_trans.accountGuid == account_id),
                    "sourceID",
                ] = "I" + str(sourceID) + "_err_000"

        return income_source_dict, income_source_trans, sourceID
