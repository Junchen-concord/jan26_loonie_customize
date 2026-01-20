import numpy as np
import pandas as pd

from utils.decorators import timer


@timer
def find_missing_payment(
    historical_payday: list, freq: str
) -> list[pd.Timestamp]:
    """Missing payment detection."""

    historical_payday = pd.Series(historical_payday)
    missing_days = []
    if freq == "I" or freq == "S" or len(historical_payday) <= 1:
        return []
    intervals = (historical_payday.diff() / np.timedelta64(1, "D")).iloc[1:]
    if freq == "W":
        for i, interval in enumerate(intervals):
            current_date = historical_payday.iloc[i]
            if interval >= 9:  # Possible missing payment
                n_missing, interval_deviation = int(interval // 7), interval % 7
                if interval_deviation >= 6 or interval_deviation <= 1:
                    if interval_deviation <= 1:
                        n_missing -= 1
                    for j in range(n_missing):
                        new_date = current_date + pd.DateOffset(days=7)
                        missing_days.append(new_date)
                        current_date = new_date
    if freq == "B":
        for i, interval in enumerate(intervals):
            current_date = historical_payday.iloc[i]
            if interval >= 18:  # Possible missing payment
                n_missing, interval_deviation = (
                    int(interval // 14),
                    interval % 14,
                )
                if interval_deviation >= 12 or interval_deviation <= 2:
                    if interval_deviation <= 2:
                        n_missing -= 1
                    for j in range(n_missing):
                        new_date = current_date + pd.DateOffset(days=14)
                        missing_days.append(new_date)
                        current_date = new_date
    if freq == "M":
        for i, interval in enumerate(intervals):
            current_date = historical_payday.iloc[i]
            if interval >= 35:  # Possible missing payment
                n_missing, interval_deviation = (
                    int(interval // 30),
                    interval % 30,
                )
                if interval_deviation >= 25 or interval_deviation <= 5:
                    if interval_deviation <= 5:
                        n_missing -= 1
                    for j in range(n_missing):
                        new_date = current_date + pd.DateOffset(months=1)
                        missing_days.append(new_date)
                        current_date = new_date

    if len(missing_days) == 0:
        return []
    else:
        return missing_days
