import numpy as np
import pandas as pd
from config import config
from dataset.loan_list import get_loan_list
from utils.decorators import timer

from postprocess.sources.helpers.calculate_frequency_amount import calculate_frequency_amount


class LoanSource:
    """Class for functions related to determing information about loan sources, frequency, and amounts."""

    @staticmethod
    @timer
    def categorize_loan_source(result: pd.DataFrame, sourceID=0) -> tuple[dict, pd.DataFrame]:
        """Returns the loan source categories given the transactions."""

        # Load holidays for payday prediction
        holidays = config.HOLIDAYS

        loan_source_dict = {}

        # 1:payroll, 2:benefit, 3:transfer, 4:deposit, 5: gig, 6:loan
        # We define this explicitly because its part of the final output the loan_source_trans
        loan_source_trans = result[
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
        loan_source_trans.columns = [
            config.IA_ACCOUNT_ID,
            config.TRANS_GUID,
            config.SOURCE_NAME,
            config.IA_TXN_SHORT,
            config.IA_DATE,
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
        loan_source_trans["amount"] = loan_source_trans["amount"].round(2)
        loan_source_trans["dayOfWeek"] = pd.to_datetime(loan_source_trans["date"], errors="coerce").dt.day_name()
        loan_source_trans["sourceID"] = "None"
        customer_df = result[result["transCategory"] == 6]
        #
        if len(customer_df) == 0:
            for account_id in result[config.PS_ACCOUNT_ID].unique():
                loan_source_dict[account_id] = {
                    "accountGuid": account_id,
                    "sourceID": "None",
                    "sourceName": "None",
                    "numOfOrigination": 0,
                    "numOfPay": 0,
                    "frequency": "None",
                    "originationAmount": 0,
                    "paymentAmount": 0,
                    "interestRate": 0,
                    "regularPayDay": "None",  # Regular payday is hardcoded to Friday, as discussed on 9/21/2023 meeting
                    "lastPayDay": "None",
                    "loanType": "Cash Advance",  # Every loan is hardcoded to cash adv
                    "debitType": "ACH",  # Hard coded to ach
                    "errorCode": 104,
                    "errorMessage": "Loan not found",
                }
            return loan_source_dict, loan_source_trans

        if len(customer_df) > 0:
            n_loans_identified = 0
            loan_list = get_loan_list()
            loan_list = loan_list + [
                r"\bloan",
                r"loan\b",
                r"\bloans",
                r"loans\b",
                r"\blend",
                r"lend\b",
                r"lending\b",
                r"\blending",
            ]
            # Process separately for each account_guid
            for account_id in customer_df[config.PS_ACCOUNT_ID].unique():
                account_df = customer_df[customer_df[config.IA_ACCOUNT_ID] == account_id]
                for i in list(set(account_df.cluster_label)):
                    cluster = str(account_id) + "_" + str(i)
                    target = account_df[account_df.cluster_label == i].sort_values(config.PS_TXN_DATE)

                    # Group sameday transactions into one, this is for getting the historical payday
                    source_name = target[config.PS_TXN_SHORT].unique()[0]
                    numOfOrigination = len(target[target.type == "CREDIT"])
                    numOfPay = len(target[target.type == "DEBIT"])
                    originated_amount = (
                        target.loc[target.type == "CREDIT", config.PS_TXN_AMOUNT]
                        .value_counts()
                        .reset_index()
                        .sort_values([config.PS_TXN_AMOUNT, "count"], ascending=False)["amount"]
                        .iloc[0]
                        if numOfOrigination > 0
                        else 0
                    )
                    paymentAmount = (
                        target.loc[target.type == "DEBIT", config.PS_TXN_AMOUNT]
                        .value_counts()
                        .reset_index()
                        .sort_values([config.PS_TXN_AMOUNT, "count"], ascending=False)["amount"]
                        .iloc[0]
                        if numOfPay > 0
                        else 0
                    )
                    interest_rate = paymentAmount / originated_amount if originated_amount > 10 else 0
                    last_payday = (
                        pd.to_datetime(target[target.type == "DEBIT"][config.PS_TXN_DATE]).max().strftime("%Y-%m-%d")
                        if numOfPay > 0
                        else "None"
                    )

                    # No longer needed because XGB is not predicting loan at all.
                    # # If the cluster only has debits, be very conservative and consider it as loan i.f.f. sourceName has one of the known loan brands
                    # if (
                    #     numOfPay > 0
                    #     and numOfOrigination == 0
                    #     and re.search("|".join(loan_list), source_name.lower()) is None
                    # ) or (
                    #     re.search(
                    #         "|".join(config.FS_LOAN_TO_OHTERS_CREDIT),
                    #         source_name.lower(),
                    #     )
                    #     is not None
                    # ):
                    #     continue

                    # Same day/single trans check
                    if numOfPay > 1:  # Frequency should only be debits
                        (
                            freq,
                            _,
                            _,
                            regular_payday,
                            _,
                            next_pay_day,
                            payment_near_holiday,
                            next_pay_day_on_holiday,
                        ) = calculate_frequency_amount(target[target.type == "DEBIT"], holidays)
                    elif numOfPay == 1:
                        freq, regular_payday = "I", "None"
                    else:
                        freq, regular_payday = "None", "None"
                    # Add a sanity check for minimum amount
                    if (originated_amount > 0 and originated_amount <= config.POS_LOAN_MIN_AMOUNT) and (
                        paymentAmount <= config.POS_LOAN_MIN_AMOUNT
                    ):
                        loan_source_dict[cluster] = {
                            "accountGuid": account_id,
                            "sourceID": "None",
                            "sourceName": source_name,
                            "numOfOrigination": numOfOrigination,
                            "numOfPay": numOfPay,
                            "frequency": freq,
                            "originationAmount": originated_amount,
                            "paymentAmount": paymentAmount,
                            "interestRate": interest_rate,
                            "regularPayDay": regular_payday,
                            "lastPayDay": last_payday,
                            "loanType": "None",
                            "debitType": "None",
                            "errorCode": 304,
                            "errorMessage": "Loan Origination and Payment amount lower than {}".format(
                                config.POS_LOAN_MIN_AMOUNT
                            ),
                        }
                        continue
                    if (paymentAmount > 0 and paymentAmount <= config.POS_LOAN_MIN_AMOUNT) and (
                        originated_amount <= config.POS_LOAN_MIN_AMOUNT
                    ):
                        loan_source_dict[cluster] = {
                            "accountGuid": account_id,
                            "sourceID": "None",
                            "sourceName": source_name,
                            "numOfOrigination": numOfOrigination,
                            "numOfPay": numOfPay,
                            "frequency": freq,
                            "originationAmount": originated_amount,
                            "paymentAmount": paymentAmount,
                            "interestRate": interest_rate,
                            "regularPayDay": regular_payday,
                            "lastPayDay": last_payday,
                            "loanType": "Cash Advance",
                            "debitType": "ACH",
                            "errorCode": 304,
                            "errorMessage": "Loan Origination and Payment amount lower than {}".format(
                                config.POS_LOAN_MIN_AMOUNT
                            ),
                        }
                        continue
                    sourceID += 1
                    loan_source_dict[cluster] = {
                        "accountGuid": account_id,
                        "sourceID": "L" + str(sourceID),
                        "sourceName": source_name,
                        "numOfOrigination": numOfOrigination,
                        "numOfPay": numOfPay,
                        "frequency": freq,
                        "originationAmount": originated_amount,
                        "paymentAmount": paymentAmount,
                        "interestRate": interest_rate,
                        "regularPayDay": regular_payday,
                        "lastPayDay": last_payday,
                        "loanType": "Cash Advance",
                        "debitType": "ACH",
                        "errorCode": 000,
                        "errorMessage": "NA",
                    }

                    # Add sourceID to income_trans
                    n_loans_identified += 1
                    loan_source_trans.loc[
                        (loan_source_trans.cluster_label == i) & (loan_source_trans.accountGuid == account_id),
                        "sourceID",
                    ] = "L" + str(sourceID)

        # If no loans identified, returns an error message
        if n_loans_identified == 0:
            for account_id in result[config.PS_ACCOUNT_ID].unique():
                loan_source_dict[account_id] = {
                    "accountGuid": account_id,
                    "sourceID": "None",
                    "sourceName": "None",
                    "numOfOrigination": 0,
                    "numOfPay": 0,
                    "frequency": "None",
                    "originationAmount": 0,
                    "paymentAmount": 0,
                    "interestRate": 0,
                    "regularPayDay": "None",
                    "lastPayDay": "None",
                    "loanType": "Cash Advance",
                    "debitType": "ACH",
                    "errorCode": 104,
                    "errorMessage": "Loan not found",
                }
            return loan_source_dict, loan_source_trans

        return loan_source_dict, loan_source_trans

    @staticmethod
    @timer
    def loan_by_month(loan_source_trans: pd.DataFrame, balance_df: pd.DataFrame) -> pd.DataFrame:
        """Loan source of all time / 3 months / 6 months."""

        # Analytics on how many loan sources within all/3 months/6 months
        all_account_ids = balance_df[[config.IA_ACCOUNT_ID]].rename(columns={config.IA_ACCOUNT_ID: "accountGuid"})
        loan_source_trans = loan_source_trans[loan_source_trans.sourceID != "None"]
        end_date = balance_df.groupby("accountGuid").agg(end_date=("as_of_date", "max")).reset_index()
        loan_source_trans = loan_source_trans.merge(end_date, how="left", on="accountGuid")
        loan_source_trans["interval"] = (
            pd.to_datetime(loan_source_trans["end_date"]) - pd.to_datetime(loan_source_trans["date"])
        ).dt.days
        loan_source_trans["in_three_month"] = loan_source_trans.interval <= 90
        loan_source_trans["in_six_month"] = loan_source_trans.interval <= 180

        loan_all = (
            loan_source_trans.groupby("accountGuid").agg(loanIdentifiedAllTime=("sourceID", "nunique")).reset_index()
        )
        loan_three_month = (
            loan_source_trans[loan_source_trans.in_three_month]
            .groupby("accountGuid")
            .agg(loanIdentifiedThreeMonth=("sourceID", "nunique"))
            .reset_index()
        )
        loan_six_month = (
            loan_source_trans[loan_source_trans.in_six_month]
            .groupby("accountGuid")
            .agg(loanIdentifiedSixMonth=("sourceID", "nunique"))
            .reset_index()
        )
        loan_source_cnt = (
            all_account_ids.merge(loan_all, on="accountGuid", how="left")
            .merge(loan_three_month, how="left", on="accountGuid")
            .merge(loan_six_month, how="left", on="accountGuid")
        )
        loan_source_cnt = loan_source_cnt.fillna(0)
        loan_source_cnt[
            [
                "loanIdentifiedAllTime",
                "loanIdentifiedThreeMonth",
                "loanIdentifiedSixMonth",
            ]
        ] = loan_source_cnt[
            [
                "loanIdentifiedAllTime",
                "loanIdentifiedThreeMonth",
                "loanIdentifiedSixMonth",
            ]
        ].astype(int)

        return loan_source_cnt

    @staticmethod
    @timer
    def averageMonthlyLoanPmt_by_month(loan_source_trans: pd.DataFrame, balance_df: pd.DataFrame) -> pd.DataFrame:
        """Average monthly loan payment for all time / 3 months / 6 months."""

        all_account_ids = balance_df[[config.IA_ACCOUNT_ID]].rename(columns={config.IA_ACCOUNT_ID: "accountGuid"})
        loan_source_trans = loan_source_trans[
            (loan_source_trans.sourceID != "None") & (loan_source_trans[config.IA_TYPE] == "DEBIT")
        ]
        end_date = balance_df.groupby("accountGuid").agg(end_date=("as_of_date", "max")).reset_index()
        loan_source_trans = loan_source_trans.merge(end_date, how="left", on="accountGuid")
        loan_source_trans["start_date"] = loan_source_trans.groupby("accountGuid").date.transform("min")
        loan_source_trans["time_period"] = (
            pd.to_datetime(loan_source_trans["end_date"]) - pd.to_datetime(loan_source_trans["start_date"])
        ).dt.days
        loan_source_trans["interval"] = (
            pd.to_datetime(loan_source_trans["end_date"]) - pd.to_datetime(loan_source_trans["date"])
        ).dt.days
        loan_source_trans["in_three_month"] = loan_source_trans.interval <= 90
        loan_source_trans["in_six_month"] = loan_source_trans.interval <= 180

        loan_all = (
            loan_source_trans.groupby("accountGuid")
            .agg(
                all_time_loan=("amount", "sum"),
                time_period=("time_period", "first"),
            )
            .reset_index()
        )
        loan_all["loanPmtAllTime"] = loan_all.all_time_loan
        loan_all.loc[loan_all.time_period >= 30, "loanPmtAllTime"] = (
            loan_all[loan_all.time_period >= 30].all_time_loan / loan_all[loan_all.time_period >= 30].time_period * 30
        )

        loan_three_month = (
            loan_source_trans[loan_source_trans.in_three_month]
            .groupby("accountGuid")
            .agg(
                all_time_loan=("amount", "sum"),
                time_period=("time_period", "first"),
            )
            .reset_index()
        )
        loan_three_month["loanPmtThreeMonth"] = loan_three_month.all_time_loan
        loan_three_month.loc[loan_three_month.time_period >= 30, "loanPmtThreeMonth"] = (
            loan_three_month[loan_three_month.time_period >= 30].all_time_loan
            / np.minimum(
                loan_three_month[loan_three_month.time_period >= 30].time_period,
                90,
            )
            * 30
        )

        loan_six_month = (
            loan_source_trans[loan_source_trans.in_six_month]
            .groupby("accountGuid")
            .agg(
                all_time_loan=("amount", "sum"),
                time_period=("time_period", "first"),
            )
            .reset_index()
        )
        loan_six_month["loanPmtSixMonth"] = loan_six_month.all_time_loan
        loan_six_month.loc[loan_six_month.time_period >= 30, "loanPmtSixMonth"] = (
            loan_six_month[loan_six_month.time_period >= 30].all_time_loan
            / np.minimum(
                loan_six_month[loan_six_month.time_period >= 30].time_period,
                180,
            )
            * 30
        )

        avg_monthly_loan_payment = (
            all_account_ids.merge(
                loan_all[["accountGuid", "loanPmtAllTime"]],
                on="accountGuid",
                how="left",
            )
            .merge(
                loan_three_month[["accountGuid", "loanPmtThreeMonth"]],
                how="left",
                on="accountGuid",
            )
            .merge(
                loan_six_month[["accountGuid", "loanPmtSixMonth"]],
                how="left",
                on="accountGuid",
            )
        )
        avg_monthly_loan_payment = avg_monthly_loan_payment.fillna(0)

        return avg_monthly_loan_payment
