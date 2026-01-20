import json

import pandas as pd
from app_utils import logger
from config import config
from utils.utils import (
    TimeFrame,
    clean_dict_strings,
    clean_json_string_general,
    standardize_date_format,
    truncate_transactions,
)
from utils.validate import InputError, JsonError, raise_error

from labeling.predict_transaction import predict_transaction
from labeling.preprocessing.rename_columns_for_postprocessing import rename_columns_for_postprocessing
from labeling.transaction_prep import revert_transaction_labels_for_processing


def _process_validated_data(data: dict, timeframe: TimeFrame):
    """
    Core processing logic shared between string and dict input versions.

    Args:
        data (dict): Validated customer bank data
        timeframe (TimeFrame): the timeframe transactions should be truncated to

    Returns:
        tuple: Same as label_transactions functions
    """
    transactions_df = pd.DataFrame.from_dict(data["transactions"])
    balance_df = pd.DataFrame.from_dict(data["accounts"])
    try:
        InputError.validate_model_input(transactions_df, balance_df)
    except Exception as e:
        return e, None, None, None, None, True

    application_info = data.get("applicationInformation")
    if not isinstance(application_info, dict) or not application_info:
        application_info = None

    IBV_auth_data = data.get("IBVAuth")
    if not isinstance(IBV_auth_data, dict) or not IBV_auth_data:
        IBV_auth_data = None

    # Handle renaming description/originalDescription already labeled transactions
    if (config.STACKING_PREDICTION in transactions_df.columns or "stackingPrediction" in transactions_df.columns) and (
        config.IA_ORIGINAL_DESCRIPTION not in transactions_df.columns
    ):
        transactions_df = revert_transaction_labels_for_processing(transactions_df)

    transactions_df, balance_df, is_error = prepare_transactions(data, transactions_df, balance_df, timeframe)
    if is_error:
        return (
            transactions_df,
            None,
            None,
            None,
            None,
            is_error,
        )  # (currently, if there is an error, transactions_df will be the output of raise_error)
    result = predict_transaction(transactions_df)
    result = rename_columns_for_postprocessing(result)
    return (
        result,
        transactions_df,
        balance_df,
        application_info,
        IBV_auth_data,
        is_error,
    )


def label_transactions(json_str: str, timeframe: TimeFrame):
    """
    Validates json_str and labels transactions

    Args:
        json_str (str): stringified customer bank data
        timeframe (TimeFrame): the timeframe transactions should be truncated to

    Returns
        tuple: a tuple containing:
            - result (DataFrame): labeled transactions df (if no error) or JsonError (if error)
            - transactions_df (DataFrame)
            - balance_df (DataFrame)
            - is_error (bool): error flag

    """
    data, is_error = validate_input(json_str)

    if is_error:
        logger.error("(validate_input) There was an error validation the JSON.")
        return data, None, None, None, None, is_error

    return _process_validated_data(data, timeframe)


def label_transactions_dict(data: dict, timeframe: TimeFrame):
    """
    Validates dict and labels transactions (V3 endpoint version).

    Args:
        data (dict): customer bank data as dictionary
        timeframe (TimeFrame): the timeframe transactions should be truncated to

    Returns:
        tuple: a tuple containing:
            - result (DataFrame): labeled transactions df (if no error) or JsonError (if error)
            - transactions_df (DataFrame)
            - balance_df (DataFrame)
            - application_info (dict)
            - IBV_auth_data (dict)
            - is_error (bool): error flag
    """
    validated_data, is_error = validate_input_dict(data)

    if is_error:
        logger.error("(validate_input_dict) There was an error validating the data.")
        return validated_data, None, None, None, None, is_error

    return _process_validated_data(validated_data, timeframe)


def prepare_balance_df(balance_df_raw: pd.DataFrame, as_of_date):
    balance_df_raw["currentBalanceDate"] = pd.to_datetime(
        standardize_date_format(balance_df_raw["currentBalanceDate"])
    ).dt.date
    balance_df_raw["as_of_date"] = pd.to_datetime(as_of_date).date()
    balance_df = balance_df_raw.sort_values([config.IA_ACCOUNT_ID, "currentBalanceDate"]).drop_duplicates(
        subset=config.IA_ACCOUNT_ID, keep="last"
    )
    return balance_df


def prepare_transactions(data, transactions_df: pd.DataFrame, balance_df_raw: pd.DataFrame, timeframe: TimeFrame):
    """
    Preprocesses transactions_df and balance_df

    Args:
        data (Any): validated and JSONified customer bank data
        transactions_df (DataFrame): "transactions" slice of data
        balance_df (DataFrame): "accounts" slice of data
        timeframe (TimeFrame): the timeframe transactions should be truncated to

    Returns:
        tuple: A tuple containing:
            - transactions_df (if no error validating) or JsonError (if error)
            - balance_df or None
            - is_error (bool): error flag
    """
    is_error = False
    try:
        # Process the balance data
        as_of_date = InputError.check_as_of_date(data)
        balance_df = prepare_balance_df(balance_df_raw, as_of_date)

        # Truncate transaction list
        transactions_df = truncate_transactions(pd.DataFrame.from_dict(transactions_df), timeframe, as_of_date)
        if len(transactions_df) < 1:
            is_error = True
            return raise_error(401, "No transactions found in the given timeframe"), None, is_error
        transactions_df[config.IA_DATE] = pd.to_datetime(transactions_df[config.IA_DATE]).dt.date
        transactions_df[config.IA_TYPE] = transactions_df[config.IA_TYPE].str.upper()
        transactions_df[config.IA_ORIGINAL_DESCRIPTION] = transactions_df[config.IA_ORIGINAL_DESCRIPTION].fillna(
            "NO DESCRIPTION"
        )
        transactions_df[config.IA_TXN_SHORT] = transactions_df[config.IA_TXN_SHORT].fillna("NO DESCRIPTION")
        transactions_df.rename(columns={"guid": "GUID"}, inplace=True)
        if config.IA_ACCOUNT_ID in balance_df.columns and config.IA_ACCOUNT_ID in transactions_df.columns:
            # Remove accounts that have no more than five associated transactions
            txn_counts = transactions_df[config.IA_ACCOUNT_ID].dropna().value_counts()
            accounts_with_enough_activity = txn_counts[txn_counts > 0].index
            dropped_accounts = balance_df.loc[
                ~balance_df[config.IA_ACCOUNT_ID].isin(accounts_with_enough_activity), config.IA_ACCOUNT_ID
            ].tolist()
            if dropped_accounts:
                logger.info(
                    "(prepare_transactions) Dropping accounts with insufficient transactions: %s",
                    dropped_accounts,
                )
            balance_df = balance_df[balance_df[config.IA_ACCOUNT_ID].isin(accounts_with_enough_activity)].copy()

    except Exception as e:
        logger.error("(prepare_transactions) There was an error validating the input.")
        logger.error(e)
        return e, None, True

    return transactions_df, balance_df, is_error


def validate_input(json_str: str):
    try:
        cleaned_json_string = clean_json_string_general(json_str)
        data = json.loads(cleaned_json_string)
        return JsonError.validate_json(data)

    except json.JSONDecodeError as e:
        return raise_error(501, "Invalid JSON format and/or content found", e), True


def validate_input_dict(data: dict):
    try:
        # Clean all string values in the dict structure using same logic as string version
        cleaned_data = clean_dict_strings(data)
        return JsonError.validate_json(cleaned_data)
    except Exception as e:
        return raise_error(501, "Invalid data format and/or content found", e), True
