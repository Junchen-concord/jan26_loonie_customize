from typing import Literal, Union

import numpy as np
import pandas as pd


def kb_time_intervals_binning(time_interval_days: int) -> str:
    """Bin the time intervals for payroll frequency check, help solving the 13,14,15 intervals problem."""

    if time_interval_days == 1:
        return "1"
    elif time_interval_days > 1 and time_interval_days <= 5:
        return "2-5"
    elif time_interval_days >= 6 and time_interval_days <= 8:
        return "6-8"
    elif time_interval_days >= 9 and time_interval_days <= 12:
        return "9-12"
    elif time_interval_days >= 13 and time_interval_days <= 17:
        return "13-17"
    elif time_interval_days >= 18 and time_interval_days <= 24:
        return "18-24"
    elif time_interval_days >= 25 and time_interval_days <= 35:
        return "25-35"
    else:
        return "36+"


def kb_cal_freq(target):
    target = target[["date", "amount"]].groupby("date").sum().reset_index()
    target.columns = ["date", "amount"]
    target["date"] = pd.to_datetime(target["date"], errors="coerce")
    if len(target) == 1:
        return "NA"
    target["time_intervals"] = (target["date"] - target["date"].shift(1)).dt.days
    target["time_intervals_binned"] = target.time_intervals.apply(kb_time_intervals_binning)
    time_intervals_freq = target.time_intervals_binned.value_counts()
    common_freq = time_intervals_freq.index[0]
    if common_freq == "6-8":
        return "Weekly"
    elif common_freq == "13-17":
        return "Biweekly"
    elif common_freq == "25-35":
        return "Monthly"
    else:
        return "NA"


def kb_calculate_frequency_amount(
    target: pd.DataFrame,
) -> tuple[
    Literal["I", "W", "B", "S", "M"],
    float,
    Union[float, int],
    str,
    Union[float, int],
]:
    """Returns the income frequency and amounts."""

    # target = target.copy() # THIS LINE CAUSES MULTIPLE TESTS TO FAIL (?)
    target["date"] = pd.to_datetime(target["date"], errors="coerce")

    # Sort earliest to latest
    target = target.sort_values("date")

    # Add up payroll amounts on the same day
    df_freq = target[["date", "amount"]].groupby("date").sum().reset_index()

    # Number of days with a payroll
    num_of_payday = len(df_freq)

    # # Number of paychecks on a payday
    # num_of_pay_pp = 1

    # Average amount received on a payday
    average_amount = df_freq["amount"].mean()

    # # Days between latest and earliest
    # total_days = (df_freq["date"].max() - df_freq["date"].min()) / np.timedelta64(
    #     1, "D"
    # )

    # Interval calculates the days between two payrolls
    df_freq["interval"] = df_freq["date"].diff() / np.timedelta64(1, "D")

    # day_month is the day of payroll date
    df_freq["day_month"] = df_freq["date"].dt.day

    # day_week is the weekday of payroll date
    df_freq["day_week"] = df_freq["date"].dt.day_name()

    # month_start indicates whether the date is the start of a month, 1 yes, 0 no
    df_freq["month_start"] = df_freq["date"].dt.is_month_start.astype(int)

    # month_end indicates whether the date is the end of a month, 1 yes, 0 no
    df_freq["month_end"] = df_freq["date"].dt.is_month_end.astype(int)

    # month_mid indicates whether the date is the 15th of a month, 1 yes, 0 no
    df_freq["month_mid"] = df_freq["day_month"].apply(lambda x: 1 if x == 15 else 0)

    # week_month indicates in which week of the month the payroll occurs
    df_freq["week_month"] = df_freq["day_month"].apply((lambda x: (x - 1) // 7 + 1)).astype(str)

    # The sum of month_start, month_end, month_mid, which are semi_indicators
    df_freq["semi_indicator"] = df_freq[["month_start", "month_end", "month_mid"]].sum(axis=1)

    # interval_W indicates whether the interval is 7, 1 yes, 0 no
    df_freq["interval_W"] = df_freq["interval"].apply(lambda x: 1 if x == 7 else 0)

    # interval_B indicates whether the interval is >=13 and <=17 (so it is either a semi-monthly or biweekly), 1 yes, 0 no
    df_freq["interval_B"] = df_freq["interval"].apply(lambda x: 1 if x >= 13 and x <= 17 else 0)

    # interval_M indicates whether the interval is >=25 and <=35, 1 yes, 0 no
    df_freq["interval_M"] = df_freq["interval"].apply(lambda x: 1 if x >= 25 and x <= 35 else 0)

    # weekday in week x of a month
    df_freq["weekday_weekmonth"] = df_freq[["day_week", "week_month"]].agg(" in Week ".join, axis=1)

    # Interval is mutiple of 7
    df_freq["multiple_of_7"] = df_freq["interval"].apply(lambda x: 1 if x % 7 == 0 else 0)
    multiple_of_7_ratio = df_freq["multiple_of_7"].sum() / (num_of_payday - 1) if num_of_payday > 1 else 0

    # The ratio is number of W/B/S/M intervals over (num_of_payday-1)
    # (num_of_payday-1) is the total number of intervals since first one gets a null
    interval_W_ratio = df_freq["interval_W"].sum() / (num_of_payday - 1) if num_of_payday > 1 else 0
    interval_B_ratio = df_freq["interval_B"].sum() / (num_of_payday - 1) if num_of_payday > 1 else 0
    interval_M_ratio = df_freq["interval_M"].sum() / (num_of_payday - 1) if num_of_payday > 1 else 0

    # Get the most frequent weekday the payroll occurs
    pay_weekday = df_freq["day_week"].value_counts().index[0]

    # Get the most frequent day of the month the paroll occurs
    pay_day_month = df_freq["day_month"].value_counts().index[:2]

    # Calculate the ratio of payrolls occurs on the most frequent weekday
    same_weekday_ratio = df_freq["day_week"].value_counts().values[0] / num_of_payday

    # Get the most frequent weekday_weekmonth
    pay_weekday_weekmonth = df_freq["weekday_weekmonth"].value_counts().index[0]

    day_month_counts = df_freq["day_month"].value_counts()

    # Assign initial values
    freq = "I"
    regular_payday = "None"
    same_day_freq = 0
    freq_pattern = "inconsistent"
    # if total_days >= 30:
    #     monthly_num_pay = (num_of_pay_pp * num_of_payday) / (total_days / 30)
    #     monthly_income = average_amount * num_of_payday / (total_days / 30)
    # else:
    #     monthly_num_pay = num_of_pay_pp * num_of_payday
    #     monthly_income = average_amount * num_of_payday

    # If there are more than 2 intervals, then more than or equal to half should meet the criteria
    if num_of_payday > 3:
        ratio = 0.4999
    # Else strictly more than half should meet the criteria
    else:
        ratio = 0.5

    # If more than half intervals are weekly
    if interval_W_ratio > ratio:
        freq = "W"
        same_day_freq = same_weekday_ratio
        freq_pattern = frequency_pattern(interval_W_ratio)
        # monthly_num_pay = num_of_pay_pp * 52 / 12
        # monthly_income = average_amount * (52 / 12)
        if same_day_freq > ratio:
            regular_payday = pay_weekday
        else:
            freq = "I"
            regular_payday = "None"

    # If more than half intervals are biweekly, determine it is semi-monthly or bi-weekly
    # based on whether they show up on the same week day or day of the month
    elif interval_B_ratio > ratio:
        # Calculate the ratio of payrolls occurs on the same day of the month
        freq_pattern = frequency_pattern(interval_B_ratio)
        same_day_month_ratio_1 = np.sum(df_freq["day_month"].value_counts().values[:2]) / num_of_payday
        same_day_month_ratio_2 = (
            df_freq["day_month"].value_counts().values[0] + df_freq["month_end"].sum()
        ) / num_of_payday
        same_day_month_ratio = max(same_day_month_ratio_1, same_day_month_ratio_2)
        if same_weekday_ratio > same_day_month_ratio:
            freq = "B"
            same_day_freq = same_weekday_ratio
            # monthly_income = average_amount * (26 / 12)
            # monthly_num_pay = num_of_pay_pp * 26 / 12
            if same_day_freq > ratio:
                regular_payday = pay_weekday
            else:
                regular_payday = "None"
                freq = "I"
        elif len(pay_day_month) >= 2:
            freq = "S"
            same_day_freq = same_day_month_ratio
            # monthly_income = average_amount * 2
            # monthly_num_pay = num_of_pay_pp * 2
            if same_day_freq > ratio:
                if same_day_month_ratio_1 > same_day_month_ratio_2:
                    regular_payday = str(pay_day_month[0]) + "," + str(pay_day_month[1])
                else:
                    regular_payday = str(pay_day_month[0]) + "," + "lastday"
            else:
                regular_payday = "None"
                freq = "I"

    # If more than half intervals are monthly,
    # check if more than half of the payrolls occur on the same weekday in the same week of a month,
    # else get the most frequent day of month the payroll occurs on and choose the latter if there is a tie
    elif interval_M_ratio > ratio:
        freq_pattern = frequency_pattern(interval_M_ratio)
        same_day_month_ratio = np.sum(df_freq["day_month"].value_counts().values[0]) / num_of_payday
        same_day_week_day_month_ratio = np.sum(df_freq["weekday_weekmonth"].value_counts().values[0]) / num_of_payday
        same_month_end_ratio = np.sum(df_freq["month_end"]) / num_of_payday
        freq = "M"
        # monthly_income = average_amount
        # monthly_num_pay = num_of_pay_pp * 1
        if same_day_week_day_month_ratio > ratio:
            regular_payday = pay_weekday_weekmonth
            same_day_freq = same_day_week_day_month_ratio
        elif same_month_end_ratio > ratio:
            regular_payday = "lastday"
            same_day_freq = same_month_end_ratio
        else:
            regular_payday = str(day_month_counts.index[0])
            same_day_freq = same_day_month_ratio

    # Loosen the criteria for missing payments, only if num_of_payday>3, and only W/B
    elif multiple_of_7_ratio > ratio and num_of_payday > 3:
        if interval_W_ratio > interval_B_ratio:
            freq_pattern = frequency_pattern(interval_B_ratio)
            freq = "W"
            # monthly_income = average_amount * (52 / 12)
            # monthly_num_pay = num_of_pay_pp * 52 / 12
            regular_payday = pay_weekday
            same_day_freq = same_weekday_ratio
        elif interval_B_ratio > interval_W_ratio:
            freq_pattern = frequency_pattern(interval_B_ratio)
            freq = "B"
            # monthly_income = average_amount * (26 / 12)
            # monthly_num_pay = num_of_pay_pp * 26 / 12
            regular_payday = pay_weekday
            same_day_freq = same_weekday_ratio

    # Try to give a regular payday for frequency I:
    if freq == "I" and len(df_freq) > 4:
        freq_pattern = "inconsistent"
        if same_weekday_ratio > ratio:
            regular_payday = pay_weekday
            same_day_freq = same_weekday_ratio
        elif len(pay_day_month) >= 2:
            regular_payday = str(pay_day_month[0]) + "," + str(pay_day_month[1])
            same_day_freq = np.sum(df_freq["day_month"].value_counts().values[:2]) / num_of_payday
        else:
            regular_payday = str(pay_day_month[0])
            same_day_freq = np.sum(df_freq["day_month"].value_counts().values[:2]) / num_of_payday
    # amount classification
    cluster_level_amount_class = amount_classification(average_amount)
    target.loc[:, "amount_class"] = target.amount.apply(amount_classification)
    amount_type_count = target["amount_class"].value_counts().values[0]
    amount_pattern_ratio = amount_type_count / target.shape[0]
    cluster_amount_pattern = amount_pattern(amount_pattern_ratio) if len(target) > 1 else "inconsistent"

    return (
        freq,
        regular_payday,
        same_day_freq,
        freq_pattern,
        cluster_level_amount_class,
        cluster_amount_pattern,
    )


def frequency_pattern(freq_ratio):
    if freq_ratio >= 0.9:
        return "consistent"
    elif freq_ratio >= 0.7:
        return "mostly consistent"
    elif freq_ratio >= 0.5:
        return "somewhat consistent"
    else:
        return "inconsistent"


def amount_classification(average_amount):
    if average_amount < 10:
        amount_class = "minor"
    elif average_amount < 100:
        amount_class = "small"
    elif average_amount < 1000:
        amount_class = "medium"
    else:
        amount_class = "major"
    return amount_class


def amount_pattern(ratio):
    if ratio >= 0.9:
        return "consistent"
    elif ratio >= 0.7:
        return "mostly consistent"
    elif ratio >= 0.5:
        return "somewhat consistent"
    else:
        return "inconsistent"
