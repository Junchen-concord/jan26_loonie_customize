import json
import os
from datetime import datetime

import pandas as pd
from config import config


class PostProcessTestData:
    """Test data class for use in test classes."""

    def __init__(self):
        sample_data_path = os.path.realpath(
            os.path.join(
                config.ROOT_DIR,
                "..",
                "tests",
                "data",
                "arg_for_categorize_income_source.json",
            )
        )
        with open(sample_data_path, "r") as fp:
            data1 = json.load(fp)
        self.arg_for_categorize_income = pd.DataFrame.from_dict(data1)
        sample_data_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", "2000.json"))
        with open(sample_data_path, "r") as fp:
            data2 = json.load(fp)
        balance_df = pd.DataFrame.from_dict(data2["accounts"])
        balance_df["currentBalanceDate"] = pd.to_datetime(balance_df["currentBalanceDate"]).dt.date
        balance_df["as_of_date"] = datetime(2023, 9, 15)
        balance_df["as_of_date"] = pd.to_datetime(balance_df.as_of_date)
        self.balance_df = balance_df
        transactions_df = pd.DataFrame.from_dict(data2["transactions"])
        transactions_df[config.IA_DATE] = pd.to_datetime(transactions_df[config.IA_DATE]).dt.date
        transactions_df[config.IA_TYPE] = transactions_df[config.IA_TYPE].str.upper()
        transactions_df.loc[:, config.IA_ORIGINAL_DESCRIPTION] = transactions_df[config.IA_ORIGINAL_DESCRIPTION].fillna(
            "NO DESCRIPTION"
        )
        transactions_df.loc[:, config.IA_TXN_SHORT] = transactions_df[config.IA_TXN_SHORT].fillna("NO DESCRIPTION")
        transactions_df = transactions_df.rename(columns={"guid": "GUID"})
        self.transactions_df = transactions_df
