from datetime import datetime

import orjson
from app_utils import validate_boolean_string
from config import settings
from flask import jsonify
from model.run_model import run_model
from utils.utils import TimeFrame

from api.common.check_run_error import check_run_error
from api.common.handle_verbosity import handle_verbosity
from api.config.config import REDZONE_BEHAVIOR_CUSTOMER, RISK_SCORE, logger

# from api.transformations.model_postprocessor import ModelPostProcessor
from api.transformations.transform_v2_output import transform_v2_output
from api.types.enums import IAResponseFields


def get_model_results(input_data, timeframe):
    model_output_str = run_model(input_data, timeframe)
    output_final_dict = orjson.loads(model_output_str)
    return output_final_dict


def handle_model_request(data, timeframe: TimeFrame, version="v2"):
    verbosity = data.get("verbosity", "true")
    threshold = data.get("threshold")
    input_data = data.get("input")

    # Validate threshold
    if threshold is not None:
        if not isinstance(data["threshold"], int) or data["threshold"] <= 0:
            return (
                jsonify({"status": 400, "message": "Threshold must be a positive integer."}),
                400,
            )
        settings.settings_dict["LOW_REDZONE_SCORE_CM"] = data["threshold"]
    else:
        settings.settings_dict["LOW_REDZONE_SCORE_CM"] = settings.LOW_REDZONE_SCORE_CM

    # Validate and set OUTPUT_ATP_FEATURES
    error_response = validate_boolean_string(data, "OUTPUT_ATP_FEATURES")
    if error_response:
        return error_response

    # Validate and set OUTPUT_REDZONE_EXPLANATION
    error_response = validate_boolean_string(data, "OUTPUT_REDZONE_EXPLANATION")
    if error_response:
        return error_response

    # Run model
    start_time = datetime.now()
    output_final_dict = get_model_results(input_data, timeframe)
    end_time = datetime.now()
    elapsed = end_time - start_time
    output_final_dict["executionTime"] = str(elapsed)

    # Check for runError
    run_error = check_run_error(output_final_dict, version)
    if run_error:
        return run_error, 400
    risk_score = output_final_dict[IAResponseFields.additionalInfo.value][REDZONE_BEHAVIOR_CUSTOMER][0][RISK_SCORE]

    # Check for v2
    if version == "v2":
        logger.info("handling v2 request")
        v2_output = transform_v2_output(output_final_dict)
        return v2_output, 200

    # Handle verbosity
    handled_output, status_code = handle_verbosity(output_final_dict, verbosity, risk_score)
    return handled_output, status_code


def handle_model_request_v3(data: dict, timeframe: TimeFrame):
    """
    Handle V3 model requests with direct dict input (no nested 'input' field).

    Args:
        data (dict): Direct bank transaction data (like 100.json format)
        timeframe (TimeFrame): Analysis timeframe

    Returns:
        tuple: (response_data, status_code)
    """
    threshold = data.get("threshold")
    # V3 endpoint doesn't support verbosity, threshold, or other optional parameters
    # It uses the direct data structure for maximum performance
    if threshold is not None:
        if not isinstance(data["threshold"], int) or data["threshold"] <= 0:
            return (
                jsonify({"status": 400, "message": "Threshold must be a positive integer."}),
                400,
            )
        settings.settings_dict["LOW_REDZONE_SCORE_CM"] = data["threshold"]
    else:
        settings.settings_dict["LOW_REDZONE_SCORE_CM"] = settings.LOW_REDZONE_SCORE_CM

    # Validate and set OUTPUT_ATP_FEATURES
    error_response = validate_boolean_string(data, "OUTPUT_ATP_FEATURES")
    if error_response:
        return error_response

    # Validate and set OUTPUT_REDZONE_EXPLANATION
    error_response = validate_boolean_string(data, "OUTPUT_REDZONE_EXPLANATION")
    if error_response:
        return error_response

    # Run model with dict input
    output_final_dict = get_model_results(data, timeframe)

    # Check for runError
    run_error = check_run_error(output_final_dict, "v2")
    if run_error:
        return run_error, 400

    # V3 always returns v2-style output (transformed)
    logger.info("handling v3 request")
    v3_output = transform_v2_output(output_final_dict)
    return v3_output, 200
