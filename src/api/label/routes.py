import json

from flask import Blueprint, jsonify, request
from flask_apispec import doc, marshal_with, use_kwargs
from marshmallow import fields

from api.common import handle_error, handle_timeframe
from api.config.config import logger
from api.schemas.error import ErrorResponse, ValidationErrorResponse
from api.schemas.model_analyze_schemas import InputJson
from api.schemas.model_label import ModelLabelResponse
from labeling.label_transactions import label_transactions
from utils.utils import TimeFrame

allowed_category_list = ["payroll", "benefit", "transfer", "deposit", "gig", "loan"]

label_blueprint = Blueprint("Labeling", __name__, url_prefix="/model/v2/label")


def handle_labeling(timeframe: TimeFrame, input_data: str):
    try:
        labels, _, _, _, _, _ = label_transactions(input_data, timeframe)
        return jsonify({"labeledTransactions": json.loads(labels.to_json(orient="records"))})
    except Exception as e:
        return handle_error(e)


@label_blueprint.route("", methods=["POST"])
@use_kwargs(InputJson, location="json")
@use_kwargs({"timeframe": fields.Str(required=False)}, location="query")
@marshal_with(ModelLabelResponse, code=200)
@marshal_with(ValidationErrorResponse, code=400)
@marshal_with(ErrorResponse, code=500)
@doc(description="Applies labeling to a set of input transactions.", tags=["Labeling"])
def label_v2(input):
    logger.info("[POST] /model/v2/label")
    timeframe_str = request.args.get("timeframe", default="ALL").upper()
    timeframe, timeframe_error = handle_timeframe(timeframe_str)
    if timeframe_error:
        return timeframe_error, 400
    logger.info(f"requested {timeframe.value} timeframe")
    return handle_labeling(timeframe=timeframe, input_data=input)
