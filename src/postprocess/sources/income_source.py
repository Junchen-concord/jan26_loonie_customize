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


class IncomeSource:
    """Class for functions related to determining information about income sources, frequency, and amounts."""

    @staticmethod
    @timer
    def categorize_income_source(
        result: pd.DataFrame, as_of_date: pd.Timestamp, sourceID=0
    ) -> tuple[dict, pd.DataFrame, int]:
        """Returns the income source categories given the transactions."""

        # Load holidays for payday prediction
        holidays = config.HOLIDAYS

        income_source_dict = {}

        # Create a copy of the result DataFrame to avoid SettingWithCopyWarning
        result = result.copy()

        result = result[result.type == "CREDIT"]

        # We define this explicitly because its part of the final output the income_source_trans
        income_source_trans = result[
            [
                config.PS_ACCOUNT_ID,
                config.PS_TXN_ID,
                config.PS_TXN_SHORT,
                config.PS_TXN_DESCRIPTION,
                config.PS_TXN_DATE,
                config.PS_TXN_AMOUNT,
                config.TRANS_CATEGORY,
                config.CLUSTER_LABEL,
                config.IA_TYPE,
                config.FROM_MODEL,
                config.WHO_COL,
                config.HOW_COL,
                config.WHAT_COL,
                config.WHO_CAT_COL,
            ]
        ].copy()
        income_source_trans.columns = [
            config.IA_ACCOUNT_ID,
            config.TRANS_GUID,
            config.SOURCE_NAME,
            config.IA_TXN_SHORT,
            config.IA_TXN_DATE,
            config.IA_TXN_AMOUNT,
            config.TRANS_CATEGORY,
            config.CLUSTER_LABEL,
            config.IA_TYPE,
            config.FROM_MODEL,
            config.WHO_COL,
            config.HOW_COL,
            config.WHAT_COL,
            "whoCat",
        ]
        # Use loc for assignments to avoid SettingWithCopyWarning
        income_source_trans.loc[:, config.IA_TXN_AMOUNT] = income_source_trans[config.IA_TXN_AMOUNT].round(2)
        income_source_trans.loc[:, "dayOfWeek"] = pd.to_datetime(
            income_source_trans["date"], errors="coerce"
        ).dt.day_name()
        income_source_trans.loc[:, "sourceID"] = "None"
        customer_df = result[result[config.TRANS_CATEGORY] == 1]
        #
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
                    "errorCode": 101,
                    "errorMessage": "Direct deposit income not found",
                    "nextPayDay": "Not Applicable",
                    "paymentNearHoliday": "None",
                    "nextPayDayOnHoliday": "Not Applicable",
                }
            return income_source_dict, income_source_trans, sourceID

        if len(customer_df) > 0:
            # process separately for each account_guid
            for account_id in customer_df[config.PS_ACCOUNT_ID].unique():
                account_df = customer_df[customer_df[config.IA_ACCOUNT_ID] == account_id]
                for i in list(set(account_df.cluster_label)):
                    cluster = str(account_id) + "_" + str(i)
                    target = account_df[account_df.cluster_label == i].sort_values(config.PS_TXN_DATE)

                    # Group sameday transactions into one, this is for getting the historical payday
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
                    income_type = "Payroll"
                    historicalPayDay = list(
                        target[[config.PS_TXN_DATE, config.PS_TXN_AMOUNT]]
                        .groupby(config.PS_TXN_DATE)
                        .sum()
                        .reset_index()
                        .date
                    )

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
                    active_score = active_income_check(target, as_of_date, freq, "Payroll")
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
                            "errorCode": 301,
                            "errorMessage": "Per_paycheck lower than $" + str(config.PS_LOW_AMOUNT_CHECK),
                            "nextPayDay": "Not Applicable",
                            "paymentNearHoliday": "None",
                            "nextPayDayOnHoliday": "Not Applicable",
                        }
                        continue

                    # Same day/single trans check
                    if num_of_payday == 1:
                        sourceID += 1
                        income_source_dict[cluster] = {
                            "accountGuid": account_id,
                            "sourceID": "I" + str(sourceID) + "_err_201",
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
                            "errorCode": 201,
                            "errorMessage": "Payroll only occurred once/on the same day",
                            "nextPayDay": "Not Applicable",
                            "paymentNearHoliday": "None",
                            "nextPayDayOnHoliday": "Not Applicable",
                        }
                        income_source_trans.loc[
                            (income_source_trans.cluster_label == i) & (income_source_trans.accountGuid == account_id),
                            "sourceID",
                        ] = "I" + str(sourceID) + "_err_201"
                        continue

                    missing_payday = find_missing_payment(historicalPayDay, freq)

                    # Skip if the income not seen within a certain peirod of time
                    if freq == "W":
                        if recency > config.PS_RECENCY_CHECK_W:
                            sourceID += 1
                            income_source_dict[cluster] = {
                                "accountGuid": account_id,
                                "sourceID": "I" + str(sourceID) + "_err_401",
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
                                "errorCode": 401,
                                "errorMessage": "Income not seen within " + str(config.PS_RECENCY_CHECK_W) + " days",
                                "nextPayDay": "Not Applicable",
                                "paymentNearHoliday": "None",
                                "nextPayDayOnHoliday": "Not Applicable",
                            }
                            income_source_trans.loc[
                                (income_source_trans.cluster_label == i)
                                & (income_source_trans.accountGuid == account_id),
                                "sourceID",
                            ] = "I" + str(sourceID) + "_err_401"
                            continue

                    elif freq == "B":
                        if recency > config.PS_RECENCY_CHECK_B:
                            sourceID += 1
                            income_source_dict[cluster] = {
                                "accountGuid": account_id,
                                "sourceID": "I" + str(sourceID) + "_err_401",
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
                                "errorCode": 401,
                                "errorMessage": "Income not seen within " + str(config.PS_RECENCY_CHECK_B) + " days",
                                "nextPayDay": "Not Applicable",
                                "paymentNearHoliday": "None",
                                "nextPayDayOnHoliday": "Not Applicable",
                            }
                            income_source_trans.loc[
                                (income_source_trans.cluster_label == i)
                                & (income_source_trans.accountGuid == account_id),
                                "sourceID",
                            ] = "I" + str(sourceID) + "_err_401"
                            continue

                    elif freq == "S":
                        if recency > config.PS_RECENCY_CHECK_S:
                            sourceID += 1
                            income_source_dict[cluster] = {
                                "accountGuid": account_id,
                                "sourceID": "I" + str(sourceID) + "_err_401",
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
                                "errorCode": 401,
                                "errorMessage": "Income not seen within " + str(config.PS_RECENCY_CHECK_S) + " days",
                                "nextPayDay": "Not Applicable",
                                "paymentNearHoliday": "None",
                                "nextPayDayOnHoliday": "Not Applicable",
                            }
                            income_source_trans.loc[
                                (income_source_trans.cluster_label == i)
                                & (income_source_trans.accountGuid == account_id),
                                "sourceID",
                            ] = "I" + str(sourceID) + "_err_401"
                            continue

                    elif freq == "M":
                        if recency > config.PS_RECENCY_CHECK_M:
                            sourceID += 1
                            income_source_dict[cluster] = {
                                "accountGuid": account_id,
                                "sourceID": "I" + str(sourceID) + "_err_401",
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
                                "errorCode": 401,
                                "errorMessage": "Income not seen within " + str(config.PS_RECENCY_CHECK_M) + " days",
                                "nextPayDay": "Not Applicable",
                                "paymentNearHoliday": "None",
                                "nextPayDayOnHoliday": "Not Applicable",
                            }
                            income_source_trans.loc[
                                (income_source_trans.cluster_label == i)
                                & (income_source_trans.accountGuid == account_id),
                                "sourceID",
                            ] = "I" + str(sourceID) + "_err_401"
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

    @staticmethod
    @timer
    def income_by_month(
        income_df_sorted: pd.DataFrame,
        balance_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Income source of all time / 3 months / 6 months."""

        # Analytics on how many income sources within all/3 months/6 months
        all_account_ids = balance_df[[config.IA_ACCOUNT_ID]].rename(columns={config.IA_ACCOUNT_ID: "accountGuid"})
        income_df_sorted = income_df_sorted[
            income_df_sorted.errorCode.isin([000, 201, 202, 203, 205, 401, 402, 403, 405])
        ]
        end_date = balance_df.groupby("accountGuid").agg(end_date=("as_of_date", "max")).reset_index()
        income_df_sorted = income_df_sorted.merge(end_date, how="left", on="accountGuid")
        income_df_sorted["interval"] = (
            pd.to_datetime(income_df_sorted["end_date"]) - pd.to_datetime(income_df_sorted["lastPayDay"])
        ).dt.days
        income_df_sorted["in_three_month"] = income_df_sorted.interval <= 90
        income_df_sorted["in_six_month"] = income_df_sorted.interval <= 180

        income_all = income_df_sorted.groupby("accountGuid").agg(all_time=("sourceID", "count")).reset_index()
        income_three_month = (
            income_df_sorted[income_df_sorted.in_three_month]
            .groupby("accountGuid")
            .agg(three_month=("sourceID", "count"))
            .reset_index()
        )
        income_six_month = (
            income_df_sorted[income_df_sorted.in_six_month]
            .groupby("accountGuid")
            .agg(six_month=("sourceID", "count"))
            .reset_index()
        )
        income_source_cnt = (
            all_account_ids.merge(income_all, on="accountGuid", how="left")
            .merge(income_three_month, how="left", on="accountGuid")
            .merge(income_six_month, how="left", on="accountGuid")
        )
        income_source_cnt = income_source_cnt.fillna(0)
        income_source_cnt[["all_time", "three_month", "six_month"]] = income_source_cnt[
            ["all_time", "three_month", "six_month"]
        ].astype(int)

        income_all = income_df_sorted.groupby("accountGuid").agg(all_time=("sourceID", "count")).reset_index()
        income_three_month = (
            income_df_sorted[income_df_sorted.in_three_month]
            .groupby("accountGuid")
            .agg(three_month=("sourceID", "count"))
            .reset_index()
        )
        income_six_month = (
            income_df_sorted[income_df_sorted.in_six_month]
            .groupby("accountGuid")
            .agg(six_month=("sourceID", "count"))
            .reset_index()
        )
        income_source_cnt = (
            all_account_ids.merge(income_all, on="accountGuid", how="left")
            .merge(income_three_month, how="left", on="accountGuid")
            .merge(income_six_month, how="left", on="accountGuid")
        )
        income_source_cnt = income_source_cnt.fillna(0)
        income_source_cnt[["all_time", "three_month", "six_month"]] = income_source_cnt[
            ["all_time", "three_month", "six_month"]
        ].astype(int)

        return income_source_cnt

    @staticmethod
    @timer
    def income_history(income_source_trans: pd.DataFrame, balance_df: pd.DataFrame) -> pd.DataFrame:
        """incomeHistory of all time / 3 months / 6 months."""

        # Analytics on how many income sources within all/3 months/6 months
        all_account_ids = balance_df[[config.IA_ACCOUNT_ID]].rename(columns={config.IA_ACCOUNT_ID: "accountGuid"})
        income_source_trans = income_source_trans[income_source_trans.sourceID.str.contains("I")]
        end_date = balance_df.groupby("accountGuid").agg(end_date=("as_of_date", "max")).reset_index()
        income_source_trans = income_source_trans.merge(end_date, how="left", on="accountGuid")
        income_source_trans["interval"] = (
            pd.to_datetime(income_source_trans["end_date"]) - pd.to_datetime(income_source_trans["date"])
        ).dt.days
        income_source_trans["in_three_month"] = income_source_trans.interval <= 90
        income_source_trans["in_six_month"] = income_source_trans.interval <= 180

        first_end_date_all = (
            income_source_trans.groupby("accountGuid").agg(first_date_all=("date", "min")).reset_index()
        )
        first_end_date_three_month = (
            income_source_trans[income_source_trans.in_three_month]
            .groupby("accountGuid")
            .agg(first_date_three_month=("date", "min"))
            .reset_index()
        )
        first_end_date_six_month = (
            income_source_trans[income_source_trans.in_six_month]
            .groupby("accountGuid")
            .agg(first_date_six_month=("date", "min"))
            .reset_index()
        )

        end_date = end_date.merge(first_end_date_all, how="left", on="accountGuid")
        end_date = end_date.merge(first_end_date_three_month, how="left", on="accountGuid")
        end_date = end_date.merge(first_end_date_six_month, how="left", on="accountGuid")
        end_date["incomeHistoryAllTime"] = (
            pd.to_datetime(end_date["end_date"]) - pd.to_datetime(end_date["first_date_all"])
        ).dt.days
        end_date["incomeHistoryThreeMonth"] = (
            pd.to_datetime(end_date["end_date"]) - pd.to_datetime(end_date["first_date_three_month"])
        ).dt.days
        end_date["incomeHistorySixMonth"] = (
            pd.to_datetime(end_date["end_date"]) - pd.to_datetime(end_date["first_date_six_month"])
        ).dt.days

        income_history_output = all_account_ids.merge(
            end_date[
                [
                    "accountGuid",
                    "incomeHistoryAllTime",
                    "incomeHistoryThreeMonth",
                    "incomeHistorySixMonth",
                ]
            ],
            on="accountGuid",
            how="left",
        )
        income_history_output = income_history_output.fillna(0)
        income_history_output[
            [
                "incomeHistoryAllTime",
                "incomeHistoryThreeMonth",
                "incomeHistorySixMonth",
            ]
        ] = income_history_output[
            [
                "incomeHistoryAllTime",
                "incomeHistoryThreeMonth",
                "incomeHistorySixMonth",
            ]
        ].astype(int)

        return income_history_output

    @staticmethod
    @timer
    def averageMonthlyIncome_by_month(income_source_trans: pd.DataFrame, balance_df: pd.DataFrame) -> pd.DataFrame:
        """Average monthly income for all time / 3 months / 6 months."""

        all_account_ids = balance_df[[config.IA_ACCOUNT_ID]].rename(columns={config.IA_ACCOUNT_ID: "accountGuid"})
        income_source_trans = income_source_trans[income_source_trans.sourceID.str.contains("I")]
        end_date = balance_df.groupby("accountGuid").agg(end_date=("as_of_date", "max")).reset_index()
        income_source_trans = income_source_trans.merge(end_date, how="left", on="accountGuid")
        income_source_trans["start_date"] = income_source_trans.groupby("accountGuid").date.transform("min")
        income_source_trans["time_period"] = (
            pd.to_datetime(income_source_trans["end_date"]) - pd.to_datetime(income_source_trans["start_date"])
        ).dt.days
        income_source_trans["interval"] = (
            pd.to_datetime(income_source_trans["end_date"]) - pd.to_datetime(income_source_trans["date"])
        ).dt.days
        income_source_trans["in_three_month"] = income_source_trans.interval <= 90
        income_source_trans["in_six_month"] = income_source_trans.interval <= 180

        income_all = (
            income_source_trans.groupby("accountGuid")
            .agg(
                all_time_income=("amount", "sum"),
                time_period=("time_period", "first"),
            )
            .reset_index()
        )
        income_all["allTimeMonthlyIncome"] = income_all.all_time_income
        income_all.loc[income_all.time_period >= 30, "allTimeMonthlyIncome"] = (
            income_all[income_all.time_period >= 30].all_time_income
            / income_all[income_all.time_period >= 30].time_period
            * 30
        )

        income_three_month = (
            income_source_trans[income_source_trans.in_three_month]
            .groupby("accountGuid")
            .agg(
                all_time_income=("amount", "sum"),
                time_period=("time_period", "first"),
            )
            .reset_index()
        )
        income_three_month["threeMonthMonthlyIncome"] = income_three_month.all_time_income
        income_three_month.loc[income_three_month.time_period >= 30, "threeMonthMonthlyIncome"] = (
            income_three_month[income_three_month.time_period >= 30].all_time_income
            / np.minimum(
                income_three_month[income_three_month.time_period >= 30].time_period,
                90,
            )
            * 30
        )

        income_six_month = (
            income_source_trans[income_source_trans.in_six_month]
            .groupby("accountGuid")
            .agg(
                all_time_income=("amount", "sum"),
                time_period=("time_period", "first"),
            )
            .reset_index()
        )
        income_six_month["sixMonthMonthlyIncome"] = income_six_month.all_time_income
        income_six_month.loc[income_six_month.time_period >= 30, "sixMonthMonthlyIncome"] = (
            income_six_month[income_six_month.time_period >= 30].all_time_income
            / np.minimum(
                income_six_month[income_six_month.time_period >= 30].time_period,
                180,
            )
            * 30
        )

        avg_monthly_income = (
            all_account_ids.merge(
                income_all[["accountGuid", "allTimeMonthlyIncome"]],
                on=config.IA_ACCOUNT_ID,
                how="left",
            )
            .merge(
                income_three_month[["accountGuid", "threeMonthMonthlyIncome"]],
                how="left",
                on=config.IA_ACCOUNT_ID,
            )
            .merge(
                income_six_month[["accountGuid", "sixMonthMonthlyIncome"]],
                how="left",
                on="accountGuid",
            )
        )
        avg_monthly_income = avg_monthly_income.fillna(0)

        return avg_monthly_income

    # Calculate only recurring and active income source's monthly income. i.e., sum up all monthly income income source section which has a frequency and no error

    @staticmethod
    @timer
    def recurring_monthly_income(
        income_df_sorted: pd.DataFrame,
        balance_df: pd.DataFrame,
        payroll_only=True,
    ) -> pd.DataFrame:
        all_account_ids = balance_df[[config.IA_ACCOUNT_ID]]
        if payroll_only:
            valid_income = income_df_sorted[
                (income_df_sorted.errorCode == 000)
                & (income_df_sorted.activeScore >= 3)
                & (income_df_sorted.recurringScore >= 0)
                & (income_df_sorted.stabilityScore >= 0)
                & (income_df_sorted.incomeType.isin(["Payroll", "Benefit"]))
            ]
        else:
            valid_income = income_df_sorted[
                (income_df_sorted.errorCode == 000)
                & (income_df_sorted.activeScore >= 3)
                & (income_df_sorted.recurringScore >= 0)
                & (income_df_sorted.stabilityScore >= 0)
            ]
        if payroll_only:
            valid_income_monthly = valid_income.groupby(config.IA_ACCOUNT_ID).agg(
                recurringMonthlyIncome=("monthlyIncome", "sum")
            )
        else:
            valid_income_monthly = valid_income.groupby(config.IA_ACCOUNT_ID).agg(
                activeMonthlyIncome=("monthlyIncome", "sum")
            )
        valid_income_monthly = all_account_ids.merge(valid_income_monthly, how="left", on=config.IA_ACCOUNT_ID)

        return valid_income_monthly

        return valid_income_monthly
