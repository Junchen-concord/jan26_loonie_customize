from flask import Flask, jsonify
from waitress import serve

from api.config.config import logger
from config import settings
from config.settings import PORT, STAGE


def get_env_var_as_bool(value: str):
    return value.lower() in ["true", "1", "t", "yes", "y"]


def validate_boolean_string(data, key):
    value = data.get(key)
    if value is not None:
        if not isinstance(value, str) or value.lower() not in ["true", "false"]:
            return jsonify({"status": 400, "message": f"{key} must be a boolean string ('true' or 'false')."}), 400
        settings.settings_dict[key] = value.lower() == "true"
    else:
        settings.settings_dict[key] = False
    return None


def run(app):
    if STAGE == "beta":
        logger.info("Running Flask development server")
        run_flask_beta_server(app, PORT)
    elif STAGE == "prod":
        logger.info("Running Flask production server")
        run_flask_production_server(app, PORT)
    else:
        logger.error("Invalid/empty stage. Exiting.")
        exit(1)


def run_flask_production_server(app: Flask, port):
    serve(app, host="0.0.0.0", port=port)


def run_flask_beta_server(app: Flask, port):
    app.run(threaded=True, host="0.0.0.0", debug=True, port=port)
