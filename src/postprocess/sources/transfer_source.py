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


class TransferSource:
    """Class for functions related to determining information about transfer sources, frequency, and amounts."""

    @staticmethod
    @timer
    def categorize_income_source(
        result: pd.DataFrame,
        income_source_trans: pd.DataFrame,
        as_of_date: pd.Timestamp,
        sourceID=0,
    ) -> tuple[dict, pd.DataFrame, int]:
        """Returns the transfer source categories given the transactions."""

        # Load holidays for payday prediction
        holidays = config.HOLIDAYS

        income_source_dict = {}

        # Only consider credit for now
        result = result[result.type == "CREDIT"].copy()

        # Add subcategories for transfer and deposit
        result.loc[result.transCategory == 3, "subcategory"] = "Other Transfer"
        result.loc[result.transCategory == 4, "subcategory"] = "Other Deposit"

        # Balance transfer
        result.loc[
            result[config.IA_ORIGINAL_DESCRIPTION].str.contains(
                "|".join(
                    [
                        r"\bto\b.*\bchecking\b",
                        r"\bfrom.*\bchecking\b",
                        r"\bfrom.*\bchk\b",
                        r"\bshare\b",
                        r"\bround up\b",
                        r"\bsave as you go\b",
                        r"\bfrom.*\bsav",
                        r"\bbank",
                        r"\bcredit.*line.*transfer\b",
                        r"\breverse.*monthly.*service.*charge\b",
                    ]
                ),
                case=False,
            ),
            "subcategory",
        ] = "Balance Transfer"

        # Transfer
        result.loc[
            (result[config.IA_ORIGINAL_DESCRIPTION].str.contains(r"\bcash app\b", case=False))
            & (result.transCategory == 3),
            "subcategory",
        ] = "Cash App"
        result.loc[
            result[config.IA_ORIGINAL_DESCRIPTION].str.contains(r"\bvenmo\b", case=False) & (result.transCategory == 3),
            "subcategory",
        ] = "Venmo"
        result.loc[
            result[config.IA_ORIGINAL_DESCRIPTION].str.contains(r"\bpaypal\b", case=False)
            & (result.transCategory == 3),
            "subcategory",
        ] = "Paypal"
        result.loc[
            result[config.IA_ORIGINAL_DESCRIPTION].str.contains(r"\bapple pay\b", case=False)
            & (result.transCategory == 3),
            "subcategory",
        ] = "Apple Pay"
        result.loc[
            result[config.IA_ORIGINAL_DESCRIPTION].str.contains(
                r"\b" + r"|".join([r"\bzelle\b", r"\bzel\b"]) + r"\b",
                case=False,
            )
            & (result.transCategory == 3),
            "subcategory",
        ] = "Zelle"

        # Deposit
        result.loc[
            (result[config.IA_ORIGINAL_DESCRIPTION].str.contains(r"\b(?:cash|atm)\b", case=False))
            & (result.transCategory == 4),
            "subcategory",
        ] = "Cash Deposit"
        result.loc[
            result[config.IA_ORIGINAL_DESCRIPTION].str.contains(r"\b(?:mobile|edeposit|online|remote)\b", case=False)
            & (result.transCategory == 4),
            "subcategory",
        ] = "Mobile Deposit"
        result.loc[
            result[config.IA_ORIGINAL_DESCRIPTION].str.contains(r"\bcheck\b", case=False) & (result.transCategory == 4),
            "subcategory",
        ] = "Check Deposit"

        # Add information to income source
        income_source_trans["subcategory"] = result.subcategory
        customer_df = result[(result["transCategory"] == 3) | (result["transCategory"] == 4)]

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
                    "errorCode": 105,
                    "errorMessage": "Transfer/Deposit not found",
                    "nextPayDay": "Not Applicable",
                    "paymentNearHoliday": "None",
                    "nextPayDayOnHoliday": "Not Applicable",
                }
            return income_source_dict, income_source_trans, sourceID

        if len(customer_df) > 0:
            # process separately for each account_guid
            for account_id in customer_df[config.PS_ACCOUNT_ID].unique():
                account_df = customer_df[customer_df[config.IA_ACCOUNT_ID] == account_id]
                for i in account_df["transCategory"].unique():
                    target = account_df[account_df.transCategory == i].sort_values(config.PS_TXN_DATE)
                    if i == 3:  # Transfer
                        income_type = "Transfer"
                    else:
                        income_type = "Deposit"
                    for j in target["subcategory"].unique():
                        transfer_subcategory = target[target.subcategory == j].sort_values("date")
                        source_name = j
                        cluster = str(account_id) + "_" + str(j)

                        # Group sameday transactions into one, this is for getting the historical payday
                        same_day_amount = (
                            transfer_subcategory[[config.PS_TXN_DATE, config.PS_TXN_AMOUNT]]
                            .groupby(config.PS_TXN_DATE)
                            .sum()
                            .reset_index()
                        )
                        num_of_payday = len(same_day_amount)
                        per_paycheck = same_day_amount[config.PS_TXN_AMOUNT].mean()
                        last_payday = pd.to_datetime(transfer_subcategory[config.PS_TXN_DATE]).max()
                        historicalPayDay = list(same_day_amount[config.PS_TXN_DATE])
                        total_days = (
                            pd.to_datetime(transfer_subcategory[config.PS_TXN_DATE]).max()
                            - pd.to_datetime(transfer_subcategory[config.PS_TXN_DATE]).min()
                        ) / np.timedelta64(1, "D")
                        monthlyIncome = round(
                            per_paycheck * num_of_payday / max((total_days / 30), 1),
                            2,
                        )
                        deposit_type = "None"
                        if (j == "Check Deposit" or j == "Mobile Deposit") and i == 4:
                            deposit_type = "Check Deposit"
                        elif (j == "Cash Deposit") and i == 4:
                            deposit_type = "Cash Deposit"
                        else:
                            deposit_type = "Other"

                        # Don't handle other deposit and other transfer right now because they are all clustered together
                        if j == "Other Transfer" or j == "Other Deposit":
                            freq, regular_payday, same_day_freq = "I", "None", 0
                            active_score, recurring_score, stability_score = (
                                0,
                                0,
                                0,
                            )
                            next_pay_day, payment_near_holiday, next_pay_day_on_holiday = "None", "None", "None"
                        else:
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
                            active_score = active_income_check(same_day_amount, as_of_date, freq, "Transfer")
                            recurring_score = recurring_income_check(
                                same_day_amount,
                                freq,
                                regular_payday,
                                same_day_freq,
                            )
                        stability_score, std_mean_ratio = amount_stability_check(same_day_amount, freq)
                        if stability_score != 3:
                            stable_monthly_income = monthlyIncome * (1 - std_mean_ratio)
                        else:
                            stable_monthly_income = monthlyIncome

                        # Still try to be conservative on NDD incomes, if the updated freq calculation gives regular payday
                        # for NDD, it will only output it if the recurring score = 3 (i.e., same day freq >=0.75)
                        if recurring_score != 3:
                            regular_payday, same_day_freq = "None", 0

                        if num_of_payday == 1:
                            sourceID += 1
                            income_source_dict[cluster] = {
                                "accountGuid": account_id,
                                "sourceID": "I" + str(sourceID) + "_err_205",
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
                                "depositMethod": deposit_type,
                                "activeScore": active_score,
                                "recurringScore": recurring_score,
                                "stabilityScore": stability_score,
                                "errorCode": 205,
                                "errorMessage": "Transfer/Deposit only occurred once/on the same day",
                                "nextPayDay": "Not Applicable",
                                "paymentNearHoliday": "None",
                                "nextPayDayOnHoliday": "Not Applicable",
                            }
                            income_source_trans.loc[
                                (income_source_trans.subcategory == j)
                                & (income_source_trans.accountGuid == account_id)
                                & (income_source_trans.transCategory.isin([3, 4])),
                                "sourceID",
                            ] = "I" + str(sourceID) + "_err_205"
                            continue

                        recency = (as_of_date - last_payday) / np.timedelta64(1, "D")

                        if source_name == "Balance Transfer":
                            income_source_dict[cluster] = {
                                "accountGuid": account_id,
                                "sourceID": "None",
                                "sourceName": source_name,
                                "sourceType": "None",
                                "sourceChannel": "None",
                                "numOfPay": num_of_payday,
                                "numOfPayMonthly": 0,
                                "frequency": "I",
                                "perPayCheck": round(per_paycheck, 2),
                                "monthlyIncome": round(monthlyIncome, 2),
                                "stableMonthlyIncome": round(stable_monthly_income, 2),
                                "regularPayDay": regular_payday,
                                "historicalPayDay": historicalPayDay,
                                "missingPayDay": [],
                                "sameDayFreq": same_day_freq,
                                "lastPayDay": last_payday.strftime("%Y-%m-%d"),
                                "incomeType": income_type,
                                "depositMethod": deposit_type,
                                "activeScore": 0,
                                "recurringScore": recurring_score,
                                "stabilityScore": stability_score,
                                "errorCode": 305,
                                "errorMessage": "Balance Transfer between one's own account is not income",
                                "nextPayDay": "Not Applicable",
                                "paymentNearHoliday": "None",
                                "nextPayDayOnHoliday": "Not Applicable",
                            }
                            continue

                        if recency > config.PS_RECENCY_CHECK:
                            sourceID += 1
                            income_source_dict[cluster] = {
                                "accountGuid": account_id,
                                "sourceID": "I" + str(sourceID) + "_err_405",
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
                                "depositMethod": deposit_type,
                                "errorCode": 405,
                                "activeScore": active_score,
                                "recurringScore": recurring_score,
                                "stabilityScore": stability_score,
                                "errorMessage": "Transfer not seen within " + str(config.PS_RECENCY_CHECK) + " days",
                                "nextPayDay": "Not Applicable",
                                "paymentNearHoliday": "None",
                                "nextPayDayOnHoliday": "Not Applicable",
                            }
                            income_source_trans.loc[
                                (income_source_trans.subcategory == j)
                                & (income_source_trans.accountGuid == account_id),
                                "sourceID",
                            ] = "I" + str(sourceID) + "_err_405"
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
                            "depositMethod": deposit_type,
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
                            (income_source_trans.subcategory == j) & (income_source_trans.accountGuid == account_id),
                            "sourceID",
                        ] = "I" + str(sourceID) + "_err_000"

        return income_source_dict, income_source_trans, sourceID
