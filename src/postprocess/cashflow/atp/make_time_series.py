from datetime import timedelta

import pandas as pd

from utils.decorators import timer


@timer
def make_time_series(df: pd.DataFrame) -> pd.DataFrame:
    df["date"] = pd.to_datetime(df.date)
    cashflow = df[["date", "amount", "type"]].sort_values("date").set_index(["date"])
    net_cashflow = cashflow.resample("1D").first()

    net_cashflow["net"] = 0

    # Calculate daily credits and debits outside the loop
    daily_credits = df[df["type"] == "CREDIT"].groupby("date")["amount"].sum()
    daily_debits = df[df["type"] == "DEBIT"].groupby("date")["amount"].sum()

    # Iterate over each day in the resampled frame
    for i, date in enumerate(net_cashflow.index):
        # Calculate net change for the day using precomputed sums
        credits_today = daily_credits.get(date, 0)
        debits_today = daily_debits.get(date, 0)
        amount_change = credits_today - debits_today

        if i == 0:
            actual_balance = amount_change
        else:
            actual_balance = net_cashflow.net.iloc[i - 1] + amount_change

        net_cashflow["net"] = net_cashflow["net"].astype(float)
        net_cashflow.loc[date, "net"] = actual_balance

    # Pad one day before beginning (0 padding to show the first day of inflow)
    net_cashflow.loc[net_cashflow.index[0] - timedelta(days=1), "net"] = 0
    net_cashflow = net_cashflow.resample("1D").first()
    # Pad one day after the end (reflection padding bc no information)
    net_cashflow.loc[net_cashflow.index[-1] + timedelta(days=1), "net"] = net_cashflow.loc[
        net_cashflow.index[-2], "net"
    ]
    net_cashflow = net_cashflow.resample("1D").first()

    return net_cashflow[["net"]]
