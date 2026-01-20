import os
from datetime import datetime
from typing import Optional

import httpx
import uvicorn
from api.common.exceptions import (
    common400Exception,
    common404Exception,
    common500Exception,
    register_exception_handlers,
)
from api.common.handle_error import handle_error
from api.common.handle_model_request import handle_model_request_v3
from api.common.handle_timeframe import handle_timeframe
from api.config.config import logger
from config import config
from config.settings import PORT
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from schemas.model_input import ModelAnalyzeRequestV3
from schemas.model_output import HealthCheckResponse, ModelAnalyzeResponseV3

load_dotenv()

tags_metadata = [
    {
        "name": "Health",
        "description": "Check the API's health, liveness, and readiness.",
    },
    {
        "name": "Model",
        "description": "Manage top-level entities that own golf clubs.",
    },
]

MODEL_VERSION = config.MODEL_VERSION

app = FastAPI(
    title="Model Service FastAPI",
    description="A RESTful API for the Bankuity Model",
    version=MODEL_VERSION,
    root_path_in_middle=True,
    openapi_tags=tags_metadata,
)

register_exception_handlers(app)


@app.on_event("startup")
async def startup_event():
    logger.info(f"Pre-onboarding service version ({MODEL_VERSION}) started on port {PORT}")


@app.exception_handler(common404Exception)
async def app_404_exception_handler(
    request: Request,
    exc: common404Exception,
):
    return JSONResponse(
        status_code=httpx.codes.NOT_FOUND,
        content={
            "kind": "Error",
            "kindVersion": "1.0.1",
            "errors": [
                {
                    "title": exc.title[0],
                    "detail": exc.detail[0],
                },
            ],
        },
    )


@app.exception_handler(common400Exception)
async def app_400_exception_handler(
    request: Request,
    exc: common400Exception,
):
    return JSONResponse(
        status_code=httpx.codes.BAD_REQUEST,
        content={
            "kind": "Error",
            "kindVersion": "1.0.1",
            "errors": [
                {
                    "title": exc.title[0],
                    "detail": exc.detail[0],
                },
            ],
        },
    )


@app.exception_handler(common500Exception)
async def app_500_exception_handler(
    request: Request,
    exc: common500Exception,
):
    return JSONResponse(
        status_code=httpx.codes.INTERNAL_SERVER_ERROR,
        content={
            "kind": "Error",
            "kindVersion": "1.0.1",
            "errors": [
                {
                    "title": exc.title[0],
                    "detail": exc.detail[0],
                },
            ],
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Exception handler for reformatting Pydantic validation errors into the expected response format"""
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append(
            {
                "title": f"Invalid input for {field_path}",
                "detail": f"{error['msg']} (input: {error.get('input', 'N/A')})",
            },
        )
    return JSONResponse(
        status_code=httpx.codes.BAD_REQUEST,
        content={
            "kind": "Error",
            "kindVersion": "1.0.1",
            "errors": errors,
        },
    )


# ===============================
# Health Endpoints
# ===============================


@app.get(
    "/liveness",
    response_model=HealthCheckResponse,
    tags=["Health"],
    summary="Liveness probe",
    description="Check if the service is alive",
)
async def liveness():
    return HealthCheckResponse(status=200, message="Live", model_version=MODEL_VERSION)


@app.get(
    "/readiness",
    response_model=HealthCheckResponse,
    tags=["Health"],
    summary="Readiness probe",
    description="Check if the service is ready to accept requests",
)
async def readiness():
    return HealthCheckResponse(status=200, message="Ready", model_version=MODEL_VERSION)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


# ===============================
# Model Analyze Endpoint
# ===============================
@app.post(
    "/model/v3/analyze",
    response_model=ModelAnalyzeResponseV3,  # Temporarily disabled for debugging
    tags=["Model"],
    summary="Analyze transactions v3",
    description="Runs full model execution with direct JSON input (no nested 'input' field)",
)
async def analyze_v3(
    request_data: ModelAnalyzeRequestV3,
    timeframe: Optional[str] = Query("ALL", description="Analysis timeframe (ALL, 3M, 6M)"),
):
    logger.info("[POST] /v3/model/analyze")

    try:
        start_time = datetime.now()
        timeframe_upper = timeframe.upper()
        timeframe_obj, timeframe_error = handle_timeframe(timeframe_upper)
        if timeframe_error:
            raise HTTPException(status_code=400, detail=timeframe_error)

        logger.info(f"requested {timeframe_obj.value} timeframe")
        data = request_data.model_dump()
        result = handle_model_request_v3(data, timeframe_obj)
        end_time = datetime.now()
        elapsed = end_time - start_time
        logger.info(f"Model execution time: {elapsed}")

        if isinstance(result, tuple):
            response_data = result[0]
            status_code = result[1] if len(result) > 1 else 200
            logger.info(f"Status code: {status_code}")
            
            if status_code >= 400:
                logger.error("runError detected")
                # Return the error response directly with proper status code
                return JSONResponse(
                    status_code=status_code,
                    content=response_data
                )
            return response_data
        else:
            return result

    except Exception as e:
        logger.exception(f"Error in analyze_v3: {e}")
        return handle_error(e)


def run_server():
    """Run the server in development or production mode based on STAGE environment variable."""
    stage = os.getenv("STAGE", "prod").lower()

    if stage == "dev":
        logger.info("Starting FastAPI in DEVELOPMENT mode")
        uvicorn.run("fastapi_app:app", host="0.0.0.0", port=int(PORT), reload=True, log_level="debug")
    else:
        logger.info("Starting FastAPI in PRODUCTION mode")
        uvicorn.run(app, host="0.0.0.0", port=int(PORT), reload=False, log_level="info")


if __name__ == "__main__":
    run_server()
