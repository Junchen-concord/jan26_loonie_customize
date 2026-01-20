import warnings
from datetime import datetime
from typing import Union

import pandas as pd
from api.config import config as apiConfig
from labeling import label_transactions
from labeling.label_transactions import label_transactions_dict
from postprocess import analyze_transactions
from utils.decorators import timer
from utils.utils import TimeFrame
from utils.validate import ModelProcessingError

warnings.filterwarnings("ignore")
pd.set_option("mode.copy_on_write", True)


@timer
def run_model(input_data: Union[str, dict], timeframe: TimeFrame = TimeFrame.ALL) -> str:
    """
    Run model with input data (supports both string and dict for backward compatibility).

    Args:
        input_data: Either a JSON string (V1/V2) or a dictionary (V3)
        timeframe: TimeFrame for analysis

    Returns:
        JSON string with analysis results
    """
    try:
        start_time = datetime.now()
        if isinstance(input_data, str):
            # Existing V1/V2 behavior
            result, transactions_df, balance_df, application_info, IBV_auth_data, is_error = label_transactions(
                input_data, timeframe
            )
        else:
            # New V3 behavior
            result, transactions_df, balance_df, application_info, IBV_auth_data, is_error = label_transactions_dict(
                input_data, timeframe
            )

        if is_error:
            apiConfig.logger.error(f"Error labeling transactions: {result}")
            return str(result)
        end_time = datetime.now()
        elapsed = end_time - start_time
        apiConfig.logger.info("label_transactions:")
        apiConfig.logger.info(elapsed)

        start_time = datetime.now()

        out = analyze_transactions(result, transactions_df, balance_df, application_info, IBV_auth_data)

        end_time = datetime.now()
        elapsed = end_time - start_time
        apiConfig.logger.info("analyze_transactions:")
        apiConfig.logger.info(elapsed)

        return out

    except ModelProcessingError as e:
        apiConfig.logger.error(f"ModelProcessingError: {e}")
        return str(e)
