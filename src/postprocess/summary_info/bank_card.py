import re

import pandas as pd

from config import config
from utils.decorators import timer

PAT_DIGITS_GROUP = re.compile(r"(\d+)")
PAT_NONALNUM = re.compile(r"[^a-zA-Z0-9\s]")
PAT_CARD_TAIL4 = re.compile(r"(?:card|crd) x*?\d{4}\b")


class BankCard:
    @staticmethod
    @timer
    def extract_digits_after_card(description: str) -> set[str]:
        def clean(description_str: str) -> str:
            t = PAT_DIGITS_GROUP.sub(r" \1 ", description_str)
            t = " ".join(t.split(" / "))
            t = " ".join(t.split(" *"))
            t = " ".join(t.split("*"))
            res1 = PAT_NONALNUM.sub(" ", t)
            words = res1.split()
            result_string = " ".join(words)
            return result_string

        if isinstance(description, str):
            s = clean(description).lower()
            matches = PAT_CARD_TAIL4.findall(s)
            res = []
            for i in matches:
                external_card_key = [
                    "wire transfer deposit card",
                    "banking advance from",
                    f"wire transfer fee {i}",
                    f"dbt {i}",
                    f"pmt {i}",
                    "payment to",
                    "pymt to",
                    " from ",
                    "eb to",
                    f"check{i}",
                ]
                flag = 0
                for key in external_card_key:
                    if key in s:
                        flag = 1
                        break
                if flag:
                    continue
                else:
                    res.append(i[-4:])
            res = set(res)
        else:
            res = set()
        return res

    @timer
    def match_card(self, df: pd.DataFrame, balance_df: pd.DataFrame) -> pd.DataFrame:
        all_account_ids = balance_df[[config.IA_ACCOUNT_ID]]
        df_card = df[[config.IA_ACCOUNT_ID, config.IA_ORIGINAL_DESCRIPTION]].copy()
        df_card["card"] = df_card[config.IA_ORIGINAL_DESCRIPTION].apply(self.extract_digits_after_card)
        output = (
            df_card[[config.IA_ACCOUNT_ID, "card"]]
            .groupby(config.IA_ACCOUNT_ID)
            .agg(lambda x: list(set().union(*x)))
            .reset_index()
        )
        output = all_account_ids.merge(output, on=config.IA_ACCOUNT_ID, how="left").fillna("None")

        return output
