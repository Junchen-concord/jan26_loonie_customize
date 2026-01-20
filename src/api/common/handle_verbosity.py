from flask import jsonify

from api.config.config import RISK_SCORE, logger
from api.types.enums import IAResponseFields


def handle_verbosity(output_final_dict, verbosity, risk_score):
    logger.info(f"requested verbosity as: {verbosity}")
    if isinstance(verbosity, str):
        verbosity = verbosity.lower()
        if verbosity == "true":
            return output_final_dict, 200
        elif verbosity == "false":
            return jsonify({RISK_SCORE: risk_score}), 200
        elif verbosity == "summary":
            return jsonify(
                {
                    IAResponseFields.summaryInfo.value: output_final_dict[IAResponseFields.summaryInfo.value],
                    RISK_SCORE: risk_score,
                }
            ), 200
    # Handle verbosity as a list
    elif isinstance(verbosity, list):
        filtered_output = {}

        for field in verbosity:
            if field in IAResponseFields.__members__:
                field_value = IAResponseFields[field].value
                if field_value in output_final_dict:
                    filtered_output[field_value] = output_final_dict[field_value]
            else:
                logger.error(f"Field {field} is not a valid field")
                return (
                    jsonify(
                        {
                            "status": 400,
                            "message": f"Field {field} is not a valid field. Please only pass fields present in the output",
                        }
                    ),
                    400,
                )

        return filtered_output, 200
    else:
        return jsonify({"status": 400, "message": "Invalid verbosity parameter."}), 400


def handle_verbosity_v2(output_final_dict, verbosity):
    # Can implement later if needed
    return
