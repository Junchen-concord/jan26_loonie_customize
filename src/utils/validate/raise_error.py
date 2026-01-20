import json

from app_utils import logger
from config import config


class ModelProcessingError(Exception):
    """Custom exception for model errors."""

    pass


def raise_error(error_code, error_msg, e=None):
    """Returns a ModelProcessingError with the given error code and message."""
    if e is not None:
        logger.error("JSON error:")
        if hasattr(e, "msg"):
            logger.error(f"Message: {e.msg}")
        if hasattr(e, "pos"):
            logger.error(f"Position: {e.pos}")
            if e.pos < len(e.doc):
                logger.error(f"Character: {e.doc[e.pos]}")
            logger.error(f"Line: {e.lineno}, Column: {e.colno}")
        if hasattr(e, "doc") and len(e.doc) > 40:
            logger.error(f"Context: {e.doc[max(0, e.pos - 20):e.pos + 20]}")
    json_output_dict = {"runError": error_code, "runMsg": error_msg}
    output_json = {
        "summaryInfo": [json_output_dict],
        "incomeSources": [],
        "incomeTrans": [],
        "loanSources": [],
        "overdraftIncidents": [],
        "cashFlow": [],
        "redZoneBehavior": [],
        "majorIncomeSource": [],
        "alertsAndInsights": [],
        "creditTrans": [],
        "debitTrans": [],
        "additionalInfo": {},
        "lendingGuide": {},
        "accounts": [],
        "runError": error_code,
        "modelVersion": config.MODEL_VERSION,
    }
    output_final = json.dumps(output_json, default=str)
    raise ModelProcessingError(output_final)
