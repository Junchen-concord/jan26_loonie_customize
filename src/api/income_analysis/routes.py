from flask import Blueprint
from flask_apispec import doc, marshal_with, use_kwargs
from marshmallow import fields

from api.common import check_run_error, get_model_results, handle_error, handle_timeframe
from api.config.config import logger
from api.income_analysis.schemas import (
    AlertsAndInsightsResponse,
    IncomeAnalysisRequest,
    LendingGuideResponse,
    RedZoneResponse,
)
from api.schemas.error import ErrorResponse
from api.transformations.transform_key_by_account import key_by_account

income_analysis_blueprint = Blueprint("income_analysis", __name__, url_prefix="/model/v1/income_analysis")


@income_analysis_blueprint.route("/lending_guide", methods=["POST"])
@use_kwargs(IncomeAnalysisRequest)
@use_kwargs({"timeframe": fields.Str(required=False)}, location="query")
@use_kwargs({"accountGuid": fields.Str(required=False)}, location="query")
@marshal_with(LendingGuideResponse, code=200)
@marshal_with(ErrorResponse, code=400)
@marshal_with(ErrorResponse, code=500)
@doc(
    description="Generates customer-level lending recommendations based on income analysis, including suggested loan amounts, risk factors, and repayment capacity. Provides actionable insights for lending decisions.",
    tags=["Income Analysis"],
)
def income_analysis_lending_guide(input, accountGuid=None, timeframe="ALL"):
    logger.info("[POST] /model/v1/income_analysis/lending_guide")
    timeframe, timeframe_error = handle_timeframe(timeframe)
    if timeframe_error:
        return timeframe_error, 400
    logger.info(f"requested {timeframe.value} timeframe")
    try:
        output_final_dict = get_model_results(input, timeframe)
        run_error = check_run_error(output_final_dict, version="v2")
        if run_error:
            return run_error, 400

        output_final_dict = key_by_account(output_final_dict)

        if accountGuid:
            requested_data = output_final_dict["accountInfo"][accountGuid]["lendingGuide"]
        else:
            requested_data = output_final_dict["customerInfo"]["lendingGuide"]
        final_output = {"lendingGuide": requested_data}
        return final_output, 200
    except Exception as e:
        return handle_error(e)


@income_analysis_blueprint.route("/redZone", methods=["POST"])
@use_kwargs(IncomeAnalysisRequest)
@use_kwargs({"timeframe": fields.Str(required=False)}, location="query")
@use_kwargs({"accountGuid": fields.Str(required=False)}, location="query")
@marshal_with(RedZoneResponse, code=200)
@marshal_with(ErrorResponse, code=400)
@marshal_with(ErrorResponse, code=500)
@doc(
    description="Evaluates customer-level financial risk factors and generates a lending risk score.",
    tags=["Income Analysis"],
)
def income_analysis_redzone(input, accountGuid=None, timeframe="ALL"):
    logger.info("[POST] /model/v1/income_analysis/risk")
    timeframe, timeframe_error = handle_timeframe(timeframe)
    if timeframe_error:
        return timeframe_error, 400
    logger.info(f"requested {timeframe.value} timeframe")
    try:
        output_final_dict = get_model_results(input, timeframe)
        run_error = check_run_error(output_final_dict, version="v2")
        if run_error:
            return run_error, 400

        output_final_dict = key_by_account(output_final_dict)

        if accountGuid:
            requested_data = output_final_dict["accountInfo"][accountGuid]["scores"]["redZone"]
        else:
            requested_data = output_final_dict["customerInfo"]["scores"]["redZone"]
        final_output = {"redZone": requested_data}
        return final_output, 200
    except Exception as e:
        return handle_error(e)


@income_analysis_blueprint.route("/alerts_and_insights", methods=["POST"])
@use_kwargs(IncomeAnalysisRequest)
@use_kwargs({"timeframe": fields.Str(required=False)}, location="query")
@marshal_with(AlertsAndInsightsResponse, code=200)
@marshal_with(ErrorResponse, code=400)
@marshal_with(ErrorResponse, code=500)
@doc(
    description="Evaluates customer-level financial risk factors and generates a lending risk score.",
    tags=["Income Analysis"],
)
def income_analysis_alerts_and_insights(input, timeframe="ALL"):
    logger.info("[POST] /model/v1/income_analysis/alerts_and_insights")
    timeframe, timeframe_error = handle_timeframe(timeframe)
    if timeframe_error:
        return timeframe_error, 400
    logger.info(f"requested {timeframe.value} timeframe")
    try:
        output_final_dict = get_model_results(input, timeframe)
        run_error = check_run_error(output_final_dict, version="v2")
        if run_error:
            return run_error, 400

        output_final_dict = key_by_account(output_final_dict)

        requested_data = output_final_dict["customerInfo"]["alertsAndInsights"]
        final_output = {"alertsAndInsights": requested_data}
        return final_output, 200
    except Exception as e:
        return handle_error(e)
