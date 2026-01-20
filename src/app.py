import os
from datetime import datetime

import orjson
import requests
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import Flask, jsonify, request
from flask_apispec import FlaskApiSpec, doc, marshal_with, use_kwargs
from flask_cors import CORS
from marshmallow import fields
from webargs.flaskparser import parser
from werkzeug.exceptions import BadRequest, HTTPException

from api.blueprints import register_blueprints
from api.common import handle_error, handle_model_request, handle_timeframe
from api.common.handle_model_request import handle_model_request_v3
from api.config.config import logger
from api.label.routes import label_v2
from api.schemas.error import ErrorResponse, ValidationErrorResponse
from api.schemas.health_check import HealthCheckResponse
from api.schemas.model_analyze_schemas import ModelAnalyzeRequest, ModelAnalyzeRequestV3, ModelAnalyzeResponseV1
from api.schemas.v2_output_schemas import ModelAnalyzeResponseV2, ModelAnalyzeResponseV3
from api.transactions.routes import transactions_analyze
from app_utils import run
from config import config, settings
from utils.utils import TimeFrame


def handle_request(timeframe: TimeFrame, version="v2"):
    try:
        start_time = datetime.now()
        data = orjson.loads(request.data)
        result = handle_model_request(data, timeframe, version)
        end_time = datetime.now()
        elapsed = end_time - start_time
        logger.info(f"Model execution time: {elapsed}")
        return result
    except Exception as e:
        return handle_error(e)


def handle_request_v3(data: dict, timeframe: TimeFrame):
    """Handle V3 requests with direct dict input."""
    try:
        start_time = datetime.now()
        result = handle_model_request_v3(data, timeframe)
        end_time = datetime.now()
        elapsed = end_time - start_time
        logger.info(f"Model execution time: {elapsed}")
        return result
    except Exception as e:
        return handle_error(e)


def create_app():
    app = Flask(__name__)
    CORS(app)
    register_blueprints(app)
    DAPR_STATE_STORE = os.environ.get("DAPR_STATE_STORE", "redis-ia-kb")
    DAPR_HOST = os.environ.get("DAPR_HOST", "http://localhost:3500")
    model_version = config.MODEL_VERSION
    number_workers = int(os.environ.get("WORKERS", 2))

    logger.info(f"Started up pre-onboarding Model Service version {model_version} on port {settings.PORT}")
    logger.info(f"Using {number_workers} workers.")

    # ===============================
    # Global Error Handlers
    # ===============================
    @parser.error_handler
    def handle_request_parsing_error(err, req, schema, *, error_status_code, error_headers):
        """Parser to catch malformed requests and raise BadRequest"""
        logger.exception(f"Global parser error {error_status_code} with headers {error_headers}")
        logger.exception(err)
        logger.exception(req)
        logger.exception(schema)
        errors = err.messages.get("json", err.messages)
        raise BadRequest(description="Validation Error", response=jsonify(errors))

    @app.errorhandler(HTTPException)
    def handle_exception(e):
        """Global HTTP error handler that catches malformed (400) requests from above, returning JSON with detailed validation error message(s)."""
        response = e.get_response()
        if hasattr(e, "data") and e.data and "errors" in e.data:
            errors = e.data["errors"]
        elif hasattr(e, "response") and e.response and hasattr(e.response, "json") and e.response.json:
            errors = e.response.json
        else:
            errors = {}

        response.data = jsonify(
            {"code": e.code, "name": e.name, "description": e.description, "errors": errors}
        ).get_data(as_text=True)

        response.content_type = "application/json"
        return response

    # ===============================
    # Liveness/Readiness Endpoints
    # ===============================

    # TODO: Deprecate
    @marshal_with(HealthCheckResponse, code=200)
    @doc(description="Health probe.", tags=["Health"])
    @app.route("/health_check", methods=["GET"])
    def health_check():
        return jsonify(
            {
                "status": 200,
                "message": "health check succeeded",
                "model_version": model_version,
            }
        )

    @marshal_with(HealthCheckResponse, code=200)
    @doc(description="Liveness probe.", tags=["Health"])
    @app.route("/liveness", methods=["GET"])
    def liveness():
        return jsonify(
            {
                "status": 200,
                "message": "Live",
                "model_version": model_version,
            }
        )

    @marshal_with(HealthCheckResponse, code=200)
    @doc(description="Readiness probe.", tags=["Health"])
    @app.route("/readiness", methods=["GET"])
    def readiness():
        return jsonify(
            {
                "status": 200,
                "message": "Ready",
                "model_version": model_version,
            }
        )

    # ====================================
    # Redis Connection Test (using Dapr)
    # ====================================
    @app.route("/redisTest", methods=["GET"])
    def fetch_value():
        state = [{"key": "flask-key", "value": "Hello from Flask with Dapr!"}]
        postResponse = requests.post(f"{DAPR_HOST}/v1.0/state/{DAPR_STATE_STORE}", json=state)
        if postResponse.ok:
            logger.info(f"Redis value stored successfully! {state}")
        else:
            return jsonify({"error": "Failed to store data"}), 500
        getResponse = requests.get(f"{DAPR_HOST}/v1.0/state/{DAPR_STATE_STORE}/flask-key")
        if getResponse.ok:
            return jsonify({"value": getResponse.json()})
        return jsonify({"error": "Failed to fetch data"}), 500

    # =============================================
    # Production /model/<version>/analyze endpoints
    # =============================================
    @use_kwargs(ModelAnalyzeRequest)
    @use_kwargs({"timeframe": fields.Str(required=False)}, location="query")
    @marshal_with(ModelAnalyzeResponseV1, code=200)
    @marshal_with(ValidationErrorResponse, code=400)
    @marshal_with(ErrorResponse, code=500)
    @doc(description="Runs full model execution, returning v1 output.", tags=["Model"])
    @app.route("/model/v1/analyze", methods=["POST"])
    def analyze_v1():
        logger.info("[POST] /model/v1/analyze")
        timeframe_str = request.args.get("timeframe", default="ALL").upper()
        timeframe, timeframe_error = handle_timeframe(timeframe_str)
        if timeframe_error:
            return timeframe_error, 400
        logger.info(f"requested {timeframe.value} timeframe")
        return handle_request(timeframe=timeframe)

    @use_kwargs(ModelAnalyzeRequest)
    @use_kwargs({"timeframe": fields.Str(required=False)}, location="query")
    @marshal_with(ModelAnalyzeResponseV2, code=200)
    @marshal_with(ValidationErrorResponse, code=400)
    @marshal_with(ErrorResponse, code=500)
    @doc(description="Runs full model execution, returning v2 output.", tags=["Model"])
    @app.route("/model/v2/analyze", methods=["POST"])
    def analyze_v2():
        logger.info("[POST] /model/v2/analyze")
        timeframe_str = request.args.get("timeframe", default="ALL").upper()
        timeframe, timeframe_error = handle_timeframe(timeframe_str)
        if timeframe_error:
            return timeframe_error, 400
        logger.info(f"requested {timeframe.value} timeframe")
        return handle_request(timeframe=timeframe, version="v2")

    @use_kwargs(ModelAnalyzeRequestV3)
    @use_kwargs({"timeframe": fields.Str(required=False)}, location="query")
    @marshal_with(ModelAnalyzeResponseV3, code=200)
    @marshal_with(ValidationErrorResponse, code=400)
    @marshal_with(ErrorResponse, code=500)
    @doc(
        description="Runs full model execution with direct JSON input (no nested 'input' field)",
        tags=["Model"],
    )
    @app.route("/model/v3/analyze", methods=["POST"])
    def analyze_v3():
        logger.info("[POST] /model/v3/analyze")
        data = request.get_json()
        timeframe_str = request.args.get("timeframe", default="ALL").upper()
        timeframe, timeframe_error = handle_timeframe(timeframe_str)
        if timeframe_error:
            return timeframe_error, 400

        logger.info(f"requested {timeframe.value} timeframe")
        return handle_request_v3(data, timeframe)

    # ===============================
    # Docs
    # ===============================

    spec = APISpec(
        title="Pre-Onboarding Model Service",
        version=model_version,
        openapi_version="3.0.2",
        plugins=[MarshmallowPlugin()],
        serve=True,
        swagger_ui=True,
    )

    app.config.update(
        {
            "APISPEC_SPEC": spec,
            "APISPEC_SWAGGER_URL": "/swagger/",
            "APISPEC_SWAGGER_UI_URL": "/swagger-ui/",
        }
    )

    docs = FlaskApiSpec(app)
    docs.register(label_v2, blueprint="Labeling")
    docs.register(transactions_analyze, blueprint="Transaction Analysis")
    docs.register(health_check)
    docs.register(liveness)
    docs.register(readiness)
    docs.register(analyze_v1)
    docs.register(analyze_v2)

    return app


if __name__ == "__main__":
    app = create_app()
    run(app)
