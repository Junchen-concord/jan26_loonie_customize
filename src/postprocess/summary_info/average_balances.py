from datetime import date, timedelta
from typing import Union

import pandas as pd
from config import config
from utils.decorators import timer


class AverageBalances:
    @staticmethod
    @timer
    def assign_month(given_date: date, cur_date: date) -> Union[int, None]:
        for i in range(6):
            if given_date > cur_date - timedelta(days=(i + 1) * 30) and given_date <= cur_date - timedelta(days=i * 30):
                return i + 1

    @timer
    def avg_balances(self, trans_df: pd.DataFrame, cur_bal: str, cur_date: date, account: str) -> pd.DataFrame:
        # If the transaction history is short, we only use those valid data
        trans_df = trans_df.copy()
        start_date = min(min(trans_df["date"]), cur_date)
        date_df = pd.DataFrame({"date": pd.date_range(start=start_date, end=cur_date)})
        date_df["date"] = pd.to_datetime(date_df["date"]).dt.date
        trans_df.loc[:, "transactions"] = trans_df.apply(
            lambda x: -x["amount"] if x["type"] == "DEBIT" else x["amount"],
            axis=1,
        )
        trans_daily = trans_df[["transactions", "date"]].groupby(["date"], as_index=False).sum()  # daily net cashflow
        trans_everyday = pd.merge(trans_daily, date_df, on="date", how="right")
        # Assumption: if there is no transaction record, the daily cashflow is 0.
        trans_everyday = trans_everyday.fillna(0)
        trans_everyday = trans_everyday.sort_values(by="date", ascending=False)
        trans_everyday["balance"] = -trans_everyday["transactions"].cumsum() + float(cur_bal)
        trans_everyday["month"] = trans_everyday["date"].apply(
            lambda given_date: self.assign_month(given_date, cur_date)
        )
        avg_monthlybal_3m = (
            trans_everyday[trans_everyday["month"] <= 3][["balance", "month"]].groupby("month").mean()
        ).mean()
        avg_monthlybal_6m = (
            trans_everyday[trans_everyday["month"] <= 6][["balance", "month"]].groupby("month").mean()
        ).mean()
        avg_monthlybal_all = (trans_everyday[["balance", "month"]].groupby("month").mean()).mean()
        c_list = [
            config.IA_ACCOUNT_ID,
            "averageMonthlyBalanceAll",
            "averageMonthlyBalance3Month",
            "averageMonthlyBalance6Month",
        ]
        data = [
            [
                account,
                avg_monthlybal_all["balance"],
                avg_monthlybal_3m["balance"],
                avg_monthlybal_6m["balance"],
            ]
        ]
        balance_df = pd.DataFrame(data, columns=c_list)

        return balance_df

    @timer
    def avg_balances_all_accounts(self, balance_df: pd.DataFrame, transactions_df: pd.DataFrame) -> pd.DataFrame:
        avg_balance_account = []
        all_account_ids = balance_df[[config.IA_ACCOUNT_ID]]
        for i, account_id in enumerate(balance_df[config.IA_ACCOUNT_ID]):
            trans_df = transactions_df[transactions_df[config.IA_ACCOUNT_ID] == account_id]
            cur_bal, cur_date = balance_df[["currentBalance", "currentBalanceDate"]].iloc[i]
            all_account_ids = balance_df[[config.IA_ACCOUNT_ID]]
            if len(trans_df) > 0:
                avg_balance = self.avg_balances(trans_df, cur_bal, cur_date, account_id)
                avg_balance_account.append(avg_balance)

        # Handle empty dataframe concatenation
        if avg_balance_account:
            balance_account = pd.concat(avg_balance_account, axis=0).reset_index()
            balance_account = all_account_ids.merge(balance_account, how="left", on=config.IA_ACCOUNT_ID).fillna(0)
        else:
            # Create a DataFrame with expected columns if there are no balances to concatenate
            balance_account = pd.DataFrame(
                columns=[
                    config.IA_ACCOUNT_ID,
                    "averageMonthlyBalanceAll",
                    "averageMonthlyBalance3Month",
                    "averageMonthlyBalance6Month",
                    "index",
                ]
            )
            balance_account = all_account_ids.merge(balance_account, how="left", on=config.IA_ACCOUNT_ID).fillna(0)

        return balance_account
