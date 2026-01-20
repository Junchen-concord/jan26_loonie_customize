import pandas as pd
from config import config, settings
from utils.decorators import timer
from utils.utils import df_to_json, remove_account_guid

from postprocess.cashflow.atp.atp_features import ATP_features
from postprocess.cashflow.cashflow import Cashflow
from postprocess.overdrafts.overdraft_detection import overdraft_detection
from postprocess.scores.alerts_and_insights import alerts_and_insights
from postprocess.sources.benefit_source import BenefitSource
from postprocess.sources.gig_source import GigSource
from postprocess.sources.helpers.rank_income import rank_income_sources
from postprocess.sources.income_source import IncomeSource
from postprocess.sources.loan_source import LoanSource
from postprocess.sources.transfer_source import TransferSource
from postprocess.summary_info.average_balances import AverageBalances
from postprocess.summary_info.bank_card import BankCard


@timer
def feature_extraction(
    result: pd.DataFrame,
    formatted_as_of_date: pd.Timestamp,
    balance_df: pd.DataFrame,
    transactions_df: pd.DataFrame,  # TODO: is this actually needed?
    multi: bool,
) -> dict[str, list[dict]]:
    balance_df["currentBalance"] = balance_df["currentBalance"].apply(float)
    if multi:
        accs = balance_df[config.IA_ACCOUNT_ID].unique()
        if len(accs) <= 1:
            return None
        # change balance df
        first_row = balance_df.iloc[[0]].copy()
        fake_cust_id = first_row.iloc[0][config.IA_ACCOUNT_ID]
        b_sum = balance_df["currentBalance"].sum()
        first_row["currentBalance"] = b_sum
        balance_df = first_row
        # change result and transactions df
        result[config.IA_ACCOUNT_ID] = fake_cust_id
        transactions_df[config.IA_ACCOUNT_ID] = fake_cust_id
    # Run ATP features (not directly related to label identification)
    atp_features = ATP_features(transactions_df.copy())

    # High level features
    # -------------------
    # Aggregate income sources
    sourceID = 0

    payroll_source_dict, income_source_trans, sourceID = IncomeSource.categorize_income_source(
        result, as_of_date=formatted_as_of_date, sourceID=sourceID
    )
    transfer_source_dict, income_source_trans, sourceID = TransferSource.categorize_income_source(
        result,
        income_source_trans,
        as_of_date=formatted_as_of_date,
        sourceID=sourceID,
    )
    benefit_source_dict, income_source_trans, sourceID = BenefitSource.categorize_income_source(
        result,
        income_source_trans,
        as_of_date=formatted_as_of_date,
        sourceID=sourceID,
    )
    gig_source_dict, income_source_trans, sourceID = GigSource.categorize_income_source(
        result,
        income_source_trans,
        as_of_date=formatted_as_of_date,
        sourceID=sourceID,
    )

    # Aggregate loan sources
    sourceID = 0
    loan_source_dict, loan_source_trans = LoanSource.categorize_loan_source(result, sourceID=sourceID)

    income_df_sorted, dominant_income_type = rank_income_sources(
        payroll_source_dict,
        transfer_source_dict,
        benefit_source_dict,
        gig_source_dict,
        balance_df,
    )

    # Bank card detection
    bank_card_info = BankCard().match_card(result, balance_df)

    # Income source count

    income_source_cnt = IncomeSource.income_by_month(income_df_sorted, balance_df).rename(
        columns={
            "accountGUID": config.IA_ACCOUNT_ID,
            "all_time": "incomeSourceAllTime",
            "three_month": "incomeSourceThreeMonth",
            "six_month": "incomeSourceSixMonth",
        }
    )

    # Income history all time, 3 month, 6 month
    income_history_output = IncomeSource.income_history(income_source_trans, balance_df).rename(
        columns={"accountGUID": config.IA_ACCOUNT_ID}
    )

    # Monthly income of only counting recurring income
    monthly_income_recurring = IncomeSource.recurring_monthly_income(income_df_sorted, balance_df)
    active_income_recurring = IncomeSource.recurring_monthly_income(income_df_sorted, balance_df, payroll_only=False)

    # Monthly income by all time, 3 month, 6 month
    monthly_income = IncomeSource.averageMonthlyIncome_by_month(income_source_trans, balance_df).rename(
        columns={"accountGUID": config.IA_ACCOUNT_ID}
    )

    cash_flow_data = Cashflow.cashflow(result, balance_df).rename(columns={"accountGUID": config.IA_ACCOUNT_ID})
    net_cash_flow_data = Cashflow.net_cashflow(result, balance_df).rename(columns={"accountGUID": config.IA_ACCOUNT_ID})
    # Inflow within 30 days excluding loans
    inflow_excluding_loans = Cashflow.inflow_excluding_loans(balance_df, income_source_trans)

    # Monthly loan payment by all time, 3 month, 6 month
    avg_monthly_loan_payment = LoanSource.averageMonthlyLoanPmt_by_month(loan_source_trans, balance_df).rename(
        columns={"accountGUID": config.IA_ACCOUNT_ID}
    )

    # Number of loan sources by all time, 3 month, 6 month
    loan_source_cnt = LoanSource.loan_by_month(loan_source_trans, balance_df).rename(
        columns={"accountGUID": config.IA_ACCOUNT_ID}
    )

    # Overdrafts
    on_cnt, incidents, odf_incidents, nsf_incidents = overdraft_detection(transactions_df, balance_df)
    avg_balance = AverageBalances().avg_balances_all_accounts(balance_df, transactions_df)
    summary_info = (
        bank_card_info.merge(income_source_cnt, how="left", on=config.IA_ACCOUNT_ID)
        .merge(monthly_income, on=config.IA_ACCOUNT_ID, how="left")
        .merge(on_cnt, on=config.IA_ACCOUNT_ID, how="left")
        .merge(avg_balance, how="left", on=config.IA_ACCOUNT_ID)
        .merge(balance_df, how="left", on=config.IA_ACCOUNT_ID)
        .merge(income_history_output, on=config.IA_ACCOUNT_ID, how="left")
        .merge(avg_monthly_loan_payment, on=config.IA_ACCOUNT_ID, how="left")
        .merge(loan_source_cnt, on=config.IA_ACCOUNT_ID, how="left")
        .merge(net_cash_flow_data, on=config.IA_ACCOUNT_ID, how="left")
        .merge(inflow_excluding_loans, on=config.IA_ACCOUNT_ID, how="left")
        .merge(monthly_income_recurring, on=config.IA_ACCOUNT_ID, how="left")
        .merge(active_income_recurring, on=config.IA_ACCOUNT_ID, how="left")
    )

    summary_info["card"] = summary_info["card"].apply(lambda d: d if isinstance(d, list) else [])
    summary_info.fillna(0, inplace=True)
    summary_info["runError"] = 0
    summary_info["runMsg"] = "NA"

    # Force encode some of fields to certain type here
    summary_info["currentBalance"] = summary_info["currentBalance"].astype(float)
    summary_info = summary_info.rename(columns={"as_of_date": "asOfDate"})

    # Redzone/alerts and insights MODEL IS RUN HERE.
    redzone, alerts_insights, red_zone_explaination, scores = alerts_and_insights(
        income_df_sorted,
        balance_df,
        loan_source_dict,
        cash_flow_data,
        summary_info,
        atp_features,
        result,
        as_of_date=formatted_as_of_date,
    )

    if multi:
        remove_account_guid(scores)
    # Add loan source to credit
    income_source_trans.loc[
        (loan_source_trans[config.IA_TYPE] == "CREDIT") & (loan_source_trans.sourceID != "None"),
        ["sourceID", "transCategory"],
    ] = loan_source_trans.loc[
        (loan_source_trans[config.IA_TYPE] == "CREDIT") & (loan_source_trans.sourceID != "None"),
        ["sourceID", "transCategory"],
    ]
    income_source_trans = income_source_trans.rename(
        columns={"cluster_label": "clusterLabel", "transGUID": "transGuid"}
    )

    credits = income_source_trans.drop(columns="subcategory").copy()
    loan_source_trans = loan_source_trans.rename(columns={"cluster_label": "clusterLabel", "transGUID": "transGuid"})
    debits = loan_source_trans[loan_source_trans[config.IA_TYPE] == "DEBIT"].copy()

    # Add ibvCategory to credits and debits
    credits[config.IBV_CATEGORY] = result[config.IBV_CATEGORY]
    credits[config.STACKING_PREDICTION] = result[config.STACKING_PREDICTION]
    debits[config.IBV_CATEGORY] = result[config.IBV_CATEGORY]
    debits[config.STACKING_PREDICTION] = result[config.STACKING_PREDICTION]
    if "id" in result.columns:
        credits["id"] = result["id"]
        debits["id"] = result["id"]
        credits = credits.drop(columns=["transGuid"])
        debits = debits.drop(columns=["transGuid"])

    # Lowercase WHO, WHAT, HOW column names, just the names not the values
    credits = credits.rename(columns={config.WHO_COL: config.WHO_COL.lower()})
    debits = debits.rename(columns={config.WHO_COL: config.WHO_COL.lower()})
    credits = credits.rename(columns={config.WHAT_COL: config.WHAT_COL.lower()})
    debits = debits.rename(columns={config.WHAT_COL: config.WHAT_COL.lower()})
    credits = credits.rename(columns={config.HOW_COL: config.HOW_COL.lower()})
    debits = debits.rename(columns={config.HOW_COL: config.HOW_COL.lower()})

    # Change sourceID from "None" to "Other" as DMA team suggested (Whether
    # this change should be done on the backend is debateable and this change
    # might result in reverting the model version)
    credits.loc[credits.sourceID == "None", "sourceID"] = "Other"
    debits.loc[debits.sourceID == "None", "sourceID"] = "Other"

    if not multi:
        # add red zone and alerts and insights to summaryInfo
        summary_info = summary_info.merge(alerts_insights, on=config.IA_ACCOUNT_ID, how="left").merge(
            redzone, on=config.IA_ACCOUNT_ID, how="left"
        )
        summary_info = df_to_json(summary_info)

        output_json = {
            "summaryInfo": summary_info,
            "incomeSources": df_to_json(income_df_sorted),
            "loanSources": df_to_json(pd.DataFrame.from_dict(loan_source_dict).transpose()),
            "overdraftIncidents": df_to_json(incidents),
            "overdraftFeeIncidents": df_to_json(odf_incidents),
            "nsfFeeIncidents": df_to_json(nsf_incidents),
            "cashFlow": df_to_json(cash_flow_data.drop(columns=["large_inflow", "low_inflow"])),
            "majorIncomeSource": df_to_json(dominant_income_type),
            "creditTrans": df_to_json(credits),
            "debitTrans": df_to_json(debits),
            "scores": scores,
        }
    else:
        redzone_json = df_to_json(redzone)
        remove_account_guid(redzone_json)
        alerts_insights_json = df_to_json(alerts_insights)
        remove_account_guid(alerts_insights_json)
        summary_info = df_to_json(summary_info)
        output_json = {
            "summaryInfo": summary_info,
            "incomeSources": df_to_json(income_df_sorted),
            "loanSources": df_to_json(pd.DataFrame.from_dict(loan_source_dict).transpose()),
            "overdraftIncidents": df_to_json(incidents),
            "overdraftFeeIncidents": df_to_json(odf_incidents),
            "nsfFeeIncidents": df_to_json(nsf_incidents),
            "cashFlow": df_to_json(cash_flow_data.drop(columns=["large_inflow", "low_inflow"])),
            "redZoneBehavior": redzone_json,
            "alertsAndInsights": alerts_insights_json,
            "majorIncomeSource": df_to_json(dominant_income_type),
            "creditTrans": df_to_json(credits),
            "debitTrans": df_to_json(debits),
            "scores": scores,
        }

    if settings.settings_dict["OUTPUT_ATP_FEATURES"]:
        output_json["atpFeatures"] = df_to_json(atp_features)
    if settings.settings_dict["OUTPUT_REDZONE_EXPLANATION"]:
        output_json["redZoneExplanation"] = df_to_json(red_zone_explaination)

    return output_json
