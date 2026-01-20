from api.config.config import logger


def handle_error(e):
    logger.exception(f"Error occurred: {e}")
    if isinstance(e, KeyError):
        return ({"status": 500, "message": f"Missing key: {e}"}), 500
    elif isinstance(e, ValueError):
        return ({"status": 400, "message": f"Invalid value: {e}"}), 400
    else:
        return ({"status": 500, "message": f"Unknown error occurred: {e}"}), 500
