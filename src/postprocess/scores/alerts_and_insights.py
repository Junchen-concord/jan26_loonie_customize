import pandas as pd
from config import config, settings
from utils.decorators import timer
from utils.utils import df_to_json

from postprocess.scores.auto_gluon_scoring import Calibrator, auto_gluon_prediction
from postprocess.scores.redzone_explain import binary_shap_explain
from postprocess.scores.xgboost_scoring import (
    make_scores,
    parse_model_reasons,
    xgb_features,
    xgboost_prediction,
)


@timer
def alerts_and_insights(
    income_df_sorted: pd.DataFrame,
    balance_df: pd.DataFrame,
    loan_source_dict: dict,
    cash_flow_data: pd.DataFrame,
    summaryInfo: dict,
    atp_df: pd.DataFrame,
    transactions_df: pd.DataFrame = None,
    as_of_date: pd.Timestamp | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # load IA output table
    all_account_ids = balance_df[[config.IA_ACCOUNT_ID]]
    loan_sources_df = pd.DataFrame.from_dict(loan_source_dict).transpose()
    loan_sources_df = loan_sources_df[loan_sources_df.errorCode == 000].rename(
        columns={"accountGuid": config.IA_ACCOUNT_ID}
    )
    summaryInfo = pd.DataFrame.from_dict(summaryInfo).rename(columns={"accountGuid": config.IA_ACCOUNT_ID})
    income_df_sorted = income_df_sorted[~income_df_sorted["errorCode"].isin([101, 102, 103, 104, 105])].rename(
        columns={"accountGuid": config.IA_ACCOUNT_ID}
    )

    # alert and insights features
    n_income = income_df_sorted.groupby(config.IA_ACCOUNT_ID).agg(
        n_income=("errorCode", "count"),
        total_monthly_income=("monthlyIncome", "sum"),
    )
    n_income = all_account_ids.merge(n_income, how="left", on=config.IA_ACCOUNT_ID).fillna(0)
    n_loan_pmt = (
        loan_sources_df.groupby(config.IA_ACCOUNT_ID)
        .agg(
            n_loan_pmt=("errorCode", "count"),
            num_of_pays=("numOfPay", "sum"),
            num_of_originations=("numOfOrigination", "sum"),
        )
        .reset_index()
    )
    n_loan_pmt = all_account_ids.merge(n_loan_pmt, how="left", on=config.IA_ACCOUNT_ID).fillna(0)
    cash_flow_data["large_inflow"] = cash_flow_data.totalCredits > config.HIGH_TOTAL_CREDIT
    cash_flow_data["low_inflow"] = cash_flow_data.totalCredits < config.LOW_TOTAL_CREDIT
    summaryInfo["No_overdraft"] = summaryInfo["odAll"] == 0
    summaryInfo["good_income_history"] = summaryInfo.incomeHistoryAllTime <= config.GOOD_INCOME_HISTORY
    behaviorial_data = (
        all_account_ids.merge(
            n_income[[config.IA_ACCOUNT_ID, "total_monthly_income"]],
            how="left",
            on=config.IA_ACCOUNT_ID,
        )
        .merge(
            n_loan_pmt[
                [
                    config.IA_ACCOUNT_ID,
                    "n_loan_pmt",
                    "num_of_pays",
                    "num_of_originations",
                ]
            ],
            how="left",
            on=config.IA_ACCOUNT_ID,
        )
        .merge(
            cash_flow_data[
                [
                    config.IA_ACCOUNT_ID,
                    "large_inflow",
                    "low_inflow",
                    "totalDebits",
                ]
            ],
            how="left",
            on=config.IA_ACCOUNT_ID,
        )
        .merge(
            summaryInfo[
                [
                    config.IA_ACCOUNT_ID,
                    "No_overdraft",
                    "good_income_history",
                    "activeMonthlyIncome",
                ]
            ],
            how="left",
            on=config.IA_ACCOUNT_ID,
        )
        .merge(
            summaryInfo[[config.IA_ACCOUNT_ID, "loanPmtAllTime"]],
            how="left",
            on=config.IA_ACCOUNT_ID,
        )
        .fillna(0)
        .infer_objects(copy=False)
    )
    # output format
    behaviorial_data["alerts"] = [list() for x in range(len(behaviorial_data))]
    behaviorial_data["insights"] = [list() for x in range(len(behaviorial_data))]
    behaviorial_data["greenZoneReasons"] = [list() for x in range(len(behaviorial_data))]

    # alerts and insights
    # behaviorial_data.loc[(behaviorial_data.loanPmtAllTime <= config.LOW_LOAN_PAYMENT) | (behaviorial_data.num_of_pays <= config.LOW_NUM_PAYMENT), 'alerts'] = behaviorial_data[(behaviorial_data.loanPmtAllTime <= config.LOW_LOAN_PAYMENT) | (behaviorial_data.num_of_pays <= config.LOW_NUM_PAYMENT)
    #                                                                                                                                                                            ].alerts.apply(
    #                                                                                                                                                                                lambda x: x + ["Increased Default Risk: Limited Loan History"])
    behaviorial_data.loc[behaviorial_data.good_income_history == 1, "alerts"] = behaviorial_data[
        behaviorial_data.good_income_history == 1
    ].alerts.apply(lambda x: x + ["Increased Default Risk: Income Detected for < 30 Consecutive Days"])

    behaviorial_data.loc[
        behaviorial_data.activeMonthlyIncome <= config.LOW_MONTHLY_INCOME,
        "alerts",
    ] = behaviorial_data[behaviorial_data.activeMonthlyIncome <= config.LOW_MONTHLY_INCOME].alerts.apply(
        lambda x: x + ["Increased Default Risk: No Active Income Detected"]
    )
    behaviorial_data.loc[behaviorial_data.totalDebits >= config.HIGH_TOTAL_DEBITS, "insights"] = behaviorial_data[
        behaviorial_data.totalDebits >= config.HIGH_TOTAL_DEBITS
    ].insights.apply(lambda x: x + ["High Repeat Opportunity: High Monthly Expenses "])
    # behaviorial_data.loc[(behaviorial_data.No_overdraft == 1) | (behaviorial_data.num_of_originations <= config.LOW_NUM_ORIGINATIONS), 'insights'] = behaviorial_data[(behaviorial_data.No_overdraft == 1) | (behaviorial_data.num_of_originations <= config.LOW_NUM_ORIGINATIONS)].insights.apply(
    #     lambda x: x+["Lack Of Essential Transactions Detected: 16% more likely to default"])

    # Redzone
    # create red zone features
    model_input = xgb_features(
        income_df_sorted,
        balance_df,
        loan_source_dict,
        cash_flow_data,
        summaryInfo,
        atp_df,
    )
    account_list = model_input[config.IA_ACCOUNT_ID].tolist()

    # run red zone model and predict score
    red_zone_df_pred, redzone_xgb_model, redzone_features = xgboost_prediction(
        model_input,
        config.REDZONE_MODEL_FILE_PATH,
        account_list,
        score_name="riskScore",
    )

    new_red_zone_pred = auto_gluon_prediction(
        model_input,
        config.REDZONE_MODEL_FILE_PATH_V2,
        account_list,
        score_name="riskScore",
        calibrator=Calibrator(config.CALIBRATOR_DATA_PATH),
    )

    # Provide explanation for red zone model (basically top3 contributing features)
    red_zone_explanation = binary_shap_explain(redzone_features, redzone_xgb_model, list(all_account_ids.accountGuid))

    # run repeat model
    repeat_df_pred, repeat_xgb_model, repeat_features = xgboost_prediction(
        model_input,
        config.REPEAT_MODEL_FILE_PATH,
        account_list,
        predicting_positive=True,
        score_name="repeatScore",
    )
    repeat_explanation = binary_shap_explain(repeat_features, repeat_xgb_model, list(all_account_ids.accountGuid))

    # run totalloanpaidoff model
    totalloanpaidoff_df_pred, totalloanpaidoff_xgb_model, totalloanpaidoff_features = xgboost_prediction(
        model_input,
        config.TOTALLOANPAIDOFF_MODEL_FILE_PATH,
        account_list,
        predicting_positive=True,
        score_name="totalLoanPaidOffScore",
    )
    totalloanpaidoff_explanation = binary_shap_explain(
        totalloanpaidoff_features,
        totalloanpaidoff_xgb_model,
        list(all_account_ids.accountGuid),
    )

    # run isBad model
    isbad_df_pred, isbad_xgb_model, isbad_features = xgboost_prediction(
        model_input, config.ISBAD_MODEL_FILE_PATH, account_list, score_name="isBadScore"
    )
    isbad_explanation = binary_shap_explain(isbad_features, isbad_xgb_model, list(all_account_ids.accountGuid))

    # red_zone_explanation.loc[:, "impact"] = red_zone_explanation.impact.replace(
    #     "positive", "positive (contribute to be in the redzone)"
    # )
    # red_zone_explanation.loc[:, "impact"] = red_zone_explanation.impact.replace(
    #     "negative", "negative (contribute to not be in the redzone)"
    # )

    # Add accountGuid back for future analysis
    redzone_features.loc[:, config.IA_ACCOUNT_ID] = list(all_account_ids.accountGuid)

    scores = {}
    red_zone_scores = make_scores(red_zone_df_pred, red_zone_explanation)
    repeat_scores = make_scores(repeat_df_pred, repeat_explanation)
    totalloanpaidoff_scores = make_scores(totalloanpaidoff_df_pred, totalloanpaidoff_explanation)
    isbad_scores = make_scores(isbad_df_pred, isbad_explanation)
    red_zone_scores_v2 = make_scores(new_red_zone_pred, pd.DataFrame())
    scores["redZone"] = red_zone_scores
    scores["repeat"] = repeat_scores
    scores["redZoneV2"] = red_zone_scores_v2
    scores["loanPaidOff"] = totalloanpaidoff_scores
    scores["isBad"] = isbad_scores
    scores["features"] = {}
    scores["features"]["accountLevel"] = df_to_json(redzone_features)

    behaviorial_data["riskBehavior"] = "NO"
    behaviorial_data = behaviorial_data.merge(
        red_zone_df_pred[[config.IA_ACCOUNT_ID, "riskScore"]],
        on=config.IA_ACCOUNT_ID,
        how="left",
    )
    # for CashMax
    LOW_REDZONE_SCORE_CM = settings.settings_dict["LOW_REDZONE_SCORE_CM"]
    behaviorial_data.loc[
        (behaviorial_data.riskScore <= LOW_REDZONE_SCORE_CM),
        "riskBehavior",
    ] = "YES"

    # add red reasons to alerts
    assessment_reason = parse_model_reasons(
        red_zone_explanation,
        red_zone_df_pred,
        behaviorial_data,
        redzone_features,
        income_df_sorted=income_df_sorted,
        transactions_df=transactions_df,
        as_of_date=as_of_date,
    )
    behaviorial_data = behaviorial_data.merge(
        assessment_reason[["accountGuid", "assessmentReasonsGood", "assessmentReasonsBad"]],
        how="left",
        on=config.IA_ACCOUNT_ID,
    )

    # for backward compatibility only
    behaviorial_data.loc[behaviorial_data.riskBehavior == "YES", "alerts"] = behaviorial_data.loc[
        behaviorial_data.riskBehavior == "YES", "assessmentReasonsBad"
    ]

    r1 = [config.IA_ACCOUNT_ID, "riskBehavior", "riskScore"]
    r2 = [config.IA_ACCOUNT_ID, "alerts", "insights", "assessmentReasonsBad", "assessmentReasonsGood"]

    return (
        behaviorial_data[r1],
        behaviorial_data[r2],
        red_zone_explanation,
        scores,
    )
