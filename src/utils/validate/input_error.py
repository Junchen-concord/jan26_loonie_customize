import pandas as pd
from dateutil.parser import ParserError

from config import config
from utils.validate.raise_error import raise_error


class InputError:
    """
    Class for input validation errors. This class runs after the JSON validation and is used to check if the input data is valid as an input to the model.
    It currently checks:
    - if the transactions DataFrame is empty
    - if `as_of_date` is present or is formatted incorrectly
    - if there are no credit transactions
    - if there is only one record of credit or debit
    """

    @classmethod
    def validate_model_input(cls, transactions_df: pd.DataFrame, balance_df: pd.DataFrame):
        """Run all validation checks required for model processing."""
        cls.validate_balance(balance_df)
        cls.validate_transactions(transactions_df)

    @staticmethod
    def validate_transactions(transactions_df: pd.DataFrame):
        """Validate the transactions DataFrame."""
        if transactions_df.empty:
            raise_error(401, "No transactions found")
        if transactions_df[transactions_df[config.IA_TYPE] == "CREDIT"].empty:
            raise_error(401, "No Credit Transactions")
        if (
            len(transactions_df[transactions_df[config.IA_TYPE] == "CREDIT"]) == 1
            or len(transactions_df[transactions_df[config.IA_TYPE] == "DEBIT"]) == 1
        ):
            raise_error(301, "JSON file contains only one record of credit or debit")

    @staticmethod
    def validate_balance(balance_df: pd.DataFrame):
        """Validate the balance DataFrame."""
        if balance_df.empty:
            raise_error(401, "Empty JSON file or no credit transactions")

    @staticmethod
    def check_as_of_date(data):
        """Validate the 'as_of_date' in the input data."""
        try:
            return pd.to_datetime(data[config.IA_AS_OF_DATE]).date()
        except KeyError as e:
            raise_error(501, "as_of_date not found", e)
        except ParserError as e:
            raise_error(501, "Invalid as_of_date format", e)
