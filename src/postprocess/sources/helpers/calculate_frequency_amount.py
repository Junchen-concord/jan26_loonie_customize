from typing import Literal, Union

import numpy as np
import pandas as pd
from config import config
from postprocess.sources.helpers.enhanced_payday_prediction import (
    determine_biweekly_or_semimonthly,
    predict_monthly_regular_payday_enhanced,
)
from utils.decorators import timer

from .source_debit_date import check_weekly_income_on_holiday, predict_next_payday


def format_enhanced_payday_result(enhanced_result: dict, fallback_day_month: str) -> tuple[str, float]:
    """
    Convert enhanced payday prediction result to backward-compatible format.

    Args:
        enhanced_result: Result from predict_monthly_regular_payday_enhanced or predict_semi_monthly_regular_payday
        fallback_day_month: Fallback day of month string for unsupported patterns

    Returns:
        tuple: (regular_payday, same_day_freq) in backward-compatible format
    """
    predicted_pattern = enhanced_result.get("predicted_pattern")
    confidence = enhanced_result.get("confidence", 0.0)
    pattern_details = enhanced_result.get("pattern_details", {})
    is_fallback = enhanced_result.get("is_fallback_pattern", False)

    # For fallback patterns, return raw values without backward compatibility formatting
    if is_fallback:
        if predicted_pattern == "end_of_month_tendency":
            return "Near end of month", confidence
        elif predicted_pattern == "near_specific_day_tendency":
            target_day = pattern_details.get("target_day", "unknown")
            return f"Near day {target_day}", confidence
        else:
            return str(predicted_pattern), confidence

    # Handle semi-monthly patterns
    if predicted_pattern == "semi_monthly_two_days":
        day1 = pattern_details.get("day1", "")
        day2 = pattern_details.get("day2", "")
        return f"{day1},{day2}", confidence

    elif predicted_pattern == "semi_monthly_day_and_last":
        specific_day = pattern_details.get("specific_day", "")
        return f"{specific_day},lastday", confidence

    # For primary monthly patterns, apply backward compatibility formatting
    if predicted_pattern == "day_of_month":
        # Extract day from description like "Monthly payday on day 15 of month"
        description = pattern_details.get("description", "")
        words = description.split()
        try:
            day_index = words.index("day") + 1
            if day_index < len(words) and words[day_index].isdigit():
                return words[day_index], confidence
        except (ValueError, IndexError):
            pass
        return fallback_day_month, confidence

    elif predicted_pattern == "last_day":
        return "lastday", confidence

    elif predicted_pattern == "weekday_k_week":
        # Extract from description like "Monthly payday on Monday of week 2"
        description = pattern_details.get("description", "")
        words = description.split()
        try:
            on_index = words.index("on") + 1
            week_index = words.index("week") + 1
            if on_index < len(words) and week_index < len(words):
                weekday = words[on_index]
                week = words[week_index]
                return f"{weekday} in Week {week}", confidence
        except (ValueError, IndexError):
            pass
        return fallback_day_month, confidence

    elif predicted_pattern == "weekday_last_week":
        # Extract from description like "Monthly payday on Monday of last week"
        description = pattern_details.get("description", "")
        words = description.split()
        try:
            on_index = words.index("on") + 1
            if on_index < len(words):
                weekday = words[on_index]
                return f"{weekday} in Week last", confidence
        except (ValueError, IndexError):
            pass
        return fallback_day_month, confidence
    elif predicted_pattern is None:
        return fallback_day_month, confidence
    else:
        # Unknown pattern, return as-is
        return str(predicted_pattern), confidence


@timer
def calculate_frequency_amount(
    target: pd.DataFrame,
    holidays: pd.DataFrame = None,
    ignore_small_amounts: bool = False,
) -> tuple[
    Literal["I", "W", "B", "S", "M"],
    float,
    Union[float, int],
    str,
    Union[float, int],
    str,  # nextPayDay
    str,  # paymentNearHoliday
    int,  # nextPayDayOnHoliday
]:
    """Returns the income frequency and amounts.

    Args:
        target: Input transactions for the cluster.
        holidays: Calendar of holidays for payday adjustments.
        ignore_small_amounts: Drop small/irregular payments before frequency calc.
    """

    # target = target.copy() # THIS LINE CAUSES MULTIPLE TESTS TO FAIL (?)
    target[config.PS_TXN_DATE] = pd.to_datetime(target[config.PS_TXN_DATE], errors="coerce")

    # Sort earliest to latest
    target = target.sort_values(config.PS_TXN_DATE)

    if ignore_small_amounts:
        target_filtered = target[target[config.PS_TXN_AMOUNT] > 50].copy()

        if target_filtered.empty:
            return "I", 0.0, 0, "None", 0.0, "Not Applicable", "None", 0

        if len(target_filtered) >= config.MINIMUM_N_PAYS_AMOUNT_TWEAK_M:
            median_amount = target_filtered[config.PS_TXN_AMOUNT].median()
            if pd.notna(median_amount) and median_amount > 0:
                lower_bound = 0.3 * median_amount
                # upper_bound = 2.0 * median_amount
                target_trimmed = target_filtered[
                    (
                        target_filtered[config.PS_TXN_AMOUNT] >= lower_bound
                        # & (target_filtered[config.PS_TXN_AMOUNT] <= upper_bound)
                    )
                ].copy()
                if not target_trimmed.empty:
                    target_filtered = target_trimmed

        target = target_filtered

    # Add up payroll amounts on the same day
    df_freq = target[[config.PS_TXN_DATE, config.PS_TXN_AMOUNT]].groupby(config.PS_TXN_DATE).sum().reset_index()

    # Number of days with a payroll
    num_of_payday = len(df_freq)

    # Number of paychecks on a payday
    num_of_pay_pp = 1

    # Average amount received on a payday
    average_amount = df_freq[config.PS_TXN_AMOUNT].mean()

    # Days between latest and earliest
    total_days = (df_freq[config.PS_TXN_DATE].max() - df_freq[config.PS_TXN_DATE].min()) / np.timedelta64(1, "D")

    # Interval calculates the days between two payrolls
    df_freq["interval"] = df_freq[config.PS_TXN_DATE].diff() / np.timedelta64(1, "D")

    # day_month is the day of payroll date
    df_freq["day_month"] = df_freq[config.PS_TXN_DATE].dt.day

    # day_week is the weekday of payroll date
    df_freq["day_week"] = df_freq[config.PS_TXN_DATE].dt.day_name()

    # month_start indicates whether the date is the start of a month, 1 yes, 0 no
    df_freq["month_start"] = df_freq[config.PS_TXN_DATE].dt.is_month_start.astype(int)

    # month_end indicates whether the date is the end of a month, 1 yes, 0 no
    df_freq["month_end"] = df_freq[config.PS_TXN_DATE].dt.is_month_end.astype(int)

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
    pay_day_month = df_freq["day_month"].value_counts().index

    # Calculate the ratio of payrolls occurs on the most frequent weekday
    same_weekday_ratio = df_freq["day_week"].value_counts().values[0] / num_of_payday

    # Get the most frequent weekday_weekmonth
    df_freq["weekday_weekmonth"].value_counts().index[0]

    day_month_counts = df_freq["day_month"].value_counts()

    # Assign initial values
    freq = "I"
    regular_payday = "None"
    same_day_freq = 0
    enhanced_result = None  # Initialize for later use
    if total_days >= 30:
        monthly_num_pay = (num_of_pay_pp * num_of_payday) / (total_days / 30)
        monthly_income = average_amount * num_of_payday / (total_days / 30)
    else:
        monthly_num_pay = num_of_pay_pp * num_of_payday
        monthly_income = average_amount * num_of_payday

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
        monthly_num_pay = num_of_pay_pp * 52 / 12
        monthly_income = average_amount * (52 / 12)
        if same_day_freq > ratio:
            regular_payday = pay_weekday
        else:
            freq = "I"
            regular_payday = "None"

    # If more than half intervals are biweekly, determine it is semi-monthly or bi-weekly
    # based on whether they show up on the same week day or day of the month
    elif interval_B_ratio > ratio:
        # Convert pandas dates to datetime.date objects for enhanced prediction
        observed_paydays = [date.date() for date in df_freq[config.PS_TXN_DATE]]

        # Use enhanced logic to determine biweekly vs semi-monthly
        pattern_result = determine_biweekly_or_semimonthly(observed_paydays)

        if pattern_result.get("pattern_type") == "B":
            # Biweekly pattern detected
            freq = "B"
            monthly_income = average_amount * (26 / 12)
            monthly_num_pay = num_of_pay_pp * 26 / 12
            regular_payday = pattern_result.get("regular_payday", "None")
            same_day_freq = pattern_result.get("confidence", 0.0)

            # Store for later use in holiday adjustment
            if pattern_result.get("pattern_details"):
                enhanced_result = pattern_result

            if same_day_freq <= ratio:
                regular_payday = "None"
                freq = "I"

        elif pattern_result.get("pattern_type") == "S":
            # Semi-monthly pattern detected
            freq = "S"
            monthly_income = average_amount * 2
            monthly_num_pay = num_of_pay_pp * 2

            # Format the semi-monthly regular payday
            semi_details = pattern_result.get("pattern_details", {})
            if semi_details:
                # Create a result dict compatible with format_enhanced_payday_result
                semi_enhanced_result = {
                    "predicted_pattern": semi_details.get("pattern_type"),
                    "confidence": pattern_result.get("confidence", 0.0),
                    "pattern_details": semi_details,
                }

                regular_payday, same_day_freq = format_enhanced_payday_result(
                    semi_enhanced_result,
                    f"{pay_day_month[0]},{pay_day_month[1]}" if len(pay_day_month) >= 2 else str(pay_day_month[0]),
                )

                # Store for later use in holiday adjustment
                enhanced_result = semi_enhanced_result
            else:
                regular_payday = "None"
                same_day_freq = 0.0

            if same_day_freq <= ratio:
                regular_payday = "None"
                freq = "I"
        else:
            # No clear pattern - fall back to old logic
            same_day_month_ratio = np.sum(df_freq["day_month"].value_counts().values[:2]) / num_of_payday

            if same_weekday_ratio > same_day_month_ratio:
                # Biweekly pattern
                freq = "B"
                same_day_freq = same_weekday_ratio
                monthly_income = average_amount * (26 / 12)
                monthly_num_pay = num_of_pay_pp * 26 / 12
                if same_day_freq > ratio:
                    regular_payday = pay_weekday
                else:
                    regular_payday = "None"
                    freq = "I"
            else:
                # Semi-monthly pattern - use old fallback logic
                freq = "S"
                monthly_income = average_amount * 2
                monthly_num_pay = num_of_pay_pp * 2

                if len(pay_day_month) >= 2 and same_day_month_ratio > ratio:
                    # Calculate ratio variations for near-end-of-month scenarios
                    most_frequent_day = pay_day_month[0]
                    is_near_end_of_month = most_frequent_day >= 28

                    if is_near_end_of_month and len(pay_day_month) >= 2:
                        same_day_month_ratio_2 = (
                            df_freq["day_month"].value_counts().values[1] + df_freq["month_end"].sum()
                        ) / num_of_payday
                    else:
                        same_day_month_ratio_2 = (
                            df_freq["day_month"].value_counts().values[0] + df_freq["month_end"].sum()
                        ) / num_of_payday

                    if max(same_day_month_ratio, same_day_month_ratio_2) > ratio:
                        # Find two days at least 7 days apart
                        first_day = pay_day_month[0]
                        second_day = None

                        for candidate_day in df_freq["day_month"].value_counts().index[1:]:
                            if abs(first_day - candidate_day) >= 7:
                                second_day = candidate_day
                                break

                        if second_day is None:
                            second_day = pay_day_month[1] if len(pay_day_month) > 1 else first_day

                        # Check if pairing with lastday
                        if is_near_end_of_month and second_day < 28:
                            regular_payday = f"{second_day},lastday"
                        elif first_day < second_day:
                            regular_payday = f"{first_day},{second_day}"
                        else:
                            regular_payday = f"{second_day},{first_day}"

                        same_day_freq = max(same_day_month_ratio, same_day_month_ratio_2)
                    else:
                        regular_payday = "None"
                        freq = "I"
                else:
                    regular_payday = "None"
                    freq = "I"

    # If more than half intervals are monthly,
    # Use enhanced payday prediction algorithm to determine regular_payday and same_day_freq
    elif interval_M_ratio > ratio:
        freq = "M"
        monthly_income = average_amount
        monthly_num_pay = num_of_pay_pp * 1

        # Convert pandas dates to datetime.date objects for enhanced prediction
        observed_paydays = [date.date() for date in df_freq[config.PS_TXN_DATE]]

        # Use enhanced payday prediction
        enhanced_result = predict_monthly_regular_payday_enhanced(observed_paydays)

        # Fallback values for backward compatibility
        same_day_month_ratio = np.sum(df_freq["day_month"].value_counts().values[0]) / num_of_payday
        fallback_day_month = str(day_month_counts.index[0])

        # Convert enhanced result to backward-compatible format
        regular_payday, same_day_freq = format_enhanced_payday_result(enhanced_result, fallback_day_month)

    # Loosen the criteria for missing payments, only if num_of_payday>3, and only W/B
    elif multiple_of_7_ratio > ratio and num_of_payday > 3:
        if interval_W_ratio > interval_B_ratio:
            freq = "W"
            monthly_income = average_amount * (52 / 12)
            monthly_num_pay = num_of_pay_pp * 52 / 12
            regular_payday = pay_weekday
            same_day_freq = same_weekday_ratio
        elif interval_B_ratio > interval_W_ratio:
            freq = "B"
            monthly_income = average_amount * (26 / 12)
            monthly_num_pay = num_of_pay_pp * 26 / 12
            regular_payday = pay_weekday
            same_day_freq = same_weekday_ratio

    # Try to give a regular payday for frequency I:
    if freq == "I" and len(df_freq) > config.MINIMUM_N_PAYDAYS_FOR_FREQ_I_HAVE_REGULAR_PAYDAY:
        if same_weekday_ratio > ratio:
            regular_payday = pay_weekday
            same_day_freq = same_weekday_ratio
        elif len(pay_day_month) >= 2:
            regular_payday = str(pay_day_month[0]) + "," + str(pay_day_month[1])
            same_day_freq = np.sum(df_freq["day_month"].value_counts().values[:2]) / num_of_payday
        else:
            regular_payday = str(pay_day_month[0])
            same_day_freq = np.sum(df_freq["day_month"].value_counts().values[:2]) / num_of_payday

    # New functionality: Calculate nextPayDay, paymentNearHoliday, nextPayDayOnHoliday
    nextPayDay = "Not Applicable"
    paymentNearHoliday = "None"
    nextPayDayOnHoliday = 0

    # Get last payday for prediction
    last_payday = df_freq[config.PS_TXN_DATE].max()

    # Predict next payday
    if freq != "I":
        # First calculate paymentNearHoliday
        if holidays is not None and len(holidays) > 0:
            if freq in ["W", "B"] and regular_payday in [
                "Friday",
                "Wednesday",
                "Thursday",
                "Tuesday",
                "Monday",
                "Saturday",
                "Sunday",
            ]:
                historical_paydays = df_freq[config.PS_TXN_DATE].tolist()
                paymentNearHoliday = check_weekly_income_on_holiday(
                    pd.to_datetime(historical_paydays), regular_payday, holidays, freq
                )
                if paymentNearHoliday is None:
                    paymentNearHoliday = "None"
            elif freq in ["M", "S"]:
                # For monthly and semi-monthly frequency, use enhanced prediction result
                if enhanced_result is not None:
                    pattern_details = enhanced_result.get("pattern_details", {})
                    paymentNearHoliday = (
                        pattern_details.get("adjustment_direction", "None")
                        if isinstance(pattern_details, dict)
                        else "None"
                    )
                else:
                    paymentNearHoliday = "None"
            else:
                paymentNearHoliday = "None"
        else:
            paymentNearHoliday = "None"

        # Now predict next payday with holiday adjustment
        next_pay_date, nextPayDayOnHoliday = predict_next_payday(last_payday, freq, regular_payday, paymentNearHoliday)
        if next_pay_date != "Not Applicable" and next_pay_date is not None:
            nextPayDay = str(next_pay_date.date()) if hasattr(next_pay_date, "date") else str(next_pay_date)

    return (
        freq,
        monthly_income,
        monthly_num_pay,
        regular_payday,
        same_day_freq,
        nextPayDay,
        paymentNearHoliday,
        nextPayDayOnHoliday,
    )


# Income activeness check based on the underwritable income requirement.


@timer
def active_income_check(
    target: pd.DataFrame, as_of_date: pd.Timestamp, freq: str, income_type: str
) -> Literal[0, 1, 2, 3]:
    # Input: target income source dataframe with date, amount as column
    # Output: Income source activeness rating
    # 0: Grey (not enough income history)
    # 1: failed the recency check
    # 2: There's a gap between payments/income drop in the last config.LATEST_INCOME_DATE days
    # 3: passed all checks and is determined active
    target_amount_check = (
        target[[config.PS_TXN_DATE, config.PS_TXN_AMOUNT]].groupby(config.PS_TXN_DATE).sum().reset_index()
    )

    if income_type not in ["Payroll", "Benefit"] and len(target_amount_check) < config.MINIMUM_N_PAYS_I:
        return 0

    if len(target_amount_check) <= 1:
        return 0
    if freq == "M":
        if len(target_amount_check) < config.MINIMUM_N_PAYS_M:
            return 0
    if freq == "S" or freq == "B":
        if len(target_amount_check) < config.MINIMUM_N_PAYS_B:
            return 0
    if freq == "W":
        if len(target_amount_check) < config.MINIMUM_N_PAYS_B:
            return 0
    if freq == "I":
        # If income type is payroll or benefit, still require only 2 transactions (for demo purpose only)
        if len(target_amount_check) < config.MINIMUM_N_PAYS_M:
            return 0

    # Recency check
    recency = (as_of_date - target.date.max()).days
    if freq == "M":
        income_active = 1 if recency <= config.PS_RECENCY_CHECK_M else 0
    if freq == "S" or freq == "B":
        income_active = 1 if recency <= config.PS_RECENCY_CHECK_B else 0
    if freq == "W":
        income_active = 1 if recency <= config.PS_RECENCY_CHECK_W else 0
    if freq == "I":
        income_active = 1 if recency <= config.PS_RECENCY_CHECK else 0

    if income_active != 1:
        return 1

    # check gap between incomes
    gaps = target.date.diff().dt.days.dropna()
    if income_type in ("Benefit", "Payroll") and freq in ("M", "I"):
        no_significant_missing_payments = (gaps >= config.MISSING_PAYMENT_DAY_TOLERANCE_M).sum() == 0
    else:
        no_significant_missing_payments = (gaps >= config.MISSING_PAYMENT_DAY_TOLERANCE).sum() == 0

    # # check if there's income drop in recent time
    # recent_payments = target[(as_of_date - target.date).dt.days <= config.LATEST_INCOME_DATE]
    # remote_payments = target[(as_of_date - target.date).dt.days > config.LATEST_INCOME_DATE]

    # if len(recent_payments) == 0:
    #     no_income_drop = 0
    # elif len(remote_payments) == 0:
    #     no_income_drop = 1
    # else:
    #     recent_per_paycheck = recent_payments.amount.mean()
    #     remote_per_paycheck = remote_payments.amount.mean()
    #     no_income_drop = recent_per_paycheck/remote_per_paycheck >= config.INCOME_DROP_TOLERANCE

    # if no_income_drop and no_significant_missing_payments:
    if no_significant_missing_payments:
        return 3
    else:
        return 2


def recurring_income_check(
    target: pd.DataFrame, freq: str, regular_payday: str, same_day_freq: int
) -> Literal[0, 1, 2, 3]:
    # Input: target income source dataframe with date, amount as column, regular_payday, same_day_freq
    # Output: Income source recurring rating
    # 0: Grey (not enough income history)
    # 1: failed all 2 recurring checks
    # 2: succeeded at least on recurring checks
    # 3: succeeded all 2 recurring checks
    target_amount_check = (
        target[[config.PS_TXN_DATE, config.PS_TXN_AMOUNT]].groupby(config.PS_TXN_DATE).sum().reset_index()
    )

    if len(target_amount_check) <= 1:
        return 0
    if freq == "M":
        if len(target_amount_check) < config.MINIMUM_N_PAYS_M:
            return 0
    if freq == "S" or freq == "B":
        if len(target_amount_check) < config.MINIMUM_N_PAYS_B:
            return 0
    if freq == "W":
        if len(target_amount_check) < config.MINIMUM_N_PAYS_B:
            return 0
    if freq == "I":
        if len(target_amount_check) < config.MINIMUM_N_PAYS_I:
            return 0

    if regular_payday == "None":
        return 1

    if same_day_freq >= config.SAME_DAY_FREQ_TOLERANCE:
        return 3

    week_day_encoding = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6,
    }

    target_date_check = target.copy()
    if freq == "M":
        if "in Week" in regular_payday:
            day_week = week_day_encoding[regular_payday.split()[0]]
            week_part = regular_payday.split()[-1]
            if week_part == "last":
                # For "last" week, we need special handling
                week_month = -1  # Special marker for last week
            else:
                week_month = int(week_part)
            target_date_check["day_week"] = target_date_check[config.PS_TXN_DATE].dt.dayofweek
            target_date_check["day_month"] = target_date_check[config.PS_TXN_DATE].dt.day

            if week_month == -1:  # Handle "last" week case
                # For last week, check if the date is the last occurrence of that weekday in the month
                def is_last_week_occurrence(date):
                    date_obj = pd.to_datetime(date)
                    # Check if adding 7 days would go into the next month
                    next_week = date_obj + pd.Timedelta(days=7)
                    return next_week.month != date_obj.month

                target_date_check["is_last_week"] = target_date_check[config.PS_TXN_DATE].apply(is_last_week_occurrence)
                target_date_check["is_correct_day"] = target_date_check["day_week"] == day_week
                target_date_check["date_diff"] = (
                    ~(target_date_check["is_last_week"] & target_date_check["is_correct_day"])
                ).astype(int) * 999
            else:
                # Original logic for numbered weeks
                target_date_check["week_month"] = target_date_check["day_month"].apply((lambda x: (x - 1) // 7 + 1))
                target_date_check["date_diff"] = (
                    target_date_check.week_month * 7 + target_date_check.day_week - (week_month * 7 + day_week)
                )
        if "lastday" in regular_payday:
            target_date_check["date_diff"] = np.minimum(
                (
                    target_date_check.date
                    - target_date_check.date.apply(lambda x: pd.offsets.MonthEnd().rollforward(x))
                ).abs(),
                (
                    target_date_check.date - target_date_check.date.apply(lambda x: pd.offsets.MonthEnd().rollback(x))
                ).abs(),
            ).dt.days
        elif regular_payday.isnumeric():
            target_date_check["date_diff"] = np.minimum(
                (target_date_check.date.dt.day - int(regular_payday)) % 30,
                (-target_date_check.date.dt.day + int(regular_payday)) % 30,
            )
        # Unexpected return format
        else:
            return 1
    elif freq == "S":
        regular_payday_1, regular_payday_2 = (
            regular_payday.split(",")[0],
            regular_payday.split(",")[1],
        )
        if "lastday" in regular_payday_1:
            target_date_check["date_diff_1"] = np.minimum(
                (
                    target_date_check.date
                    - target_date_check.date.apply(lambda x: pd.offsets.MonthEnd().rollforward(x))
                ).abs(),
                (
                    target_date_check.date - target_date_check.date.apply(lambda x: pd.offsets.MonthEnd().rollback(x))
                ).abs(),
            ).dt.days
        elif regular_payday_1.isnumeric():
            target_date_check["date_diff_1"] = np.minimum(
                (target_date_check.date.dt.day - int(regular_payday_1)) % 30,
                (-target_date_check.date.dt.day + int(regular_payday_1)) % 30,
            )
        else:
            return 1

        if "lastday" in regular_payday_2:
            target_date_check["date_diff_2"] = np.minimum(
                (
                    target_date_check.date
                    - target_date_check.date.apply(lambda x: pd.offsets.MonthEnd().rollforward(x))
                ).abs(),
                (
                    target_date_check.date - target_date_check.date.apply(lambda x: pd.offsets.MonthEnd().rollback(x))
                ).abs(),
            ).dt.days
        elif regular_payday_2.isnumeric():
            target_date_check["date_diff_2"] = np.minimum(
                (target_date_check.date.dt.day - int(regular_payday_2)) % 30,
                (-target_date_check.date.dt.day + int(regular_payday_2)) % 30,
            )
        else:
            return 1
        target_date_check["date_diff"] = np.minimum(target_date_check.date_diff_1, target_date_check.date_diff_2)

    elif freq == "W" or freq == "B":
        if regular_payday in week_day_encoding.keys():
            target_date_check["date_diff"] = np.minimum(
                target_date_check.date.dt.dayofweek - week_day_encoding[regular_payday],
                -target_date_check.date.dt.dayofweek + week_day_encoding[regular_payday],
            )
        else:
            return 1
    elif freq == "I":
        if regular_payday in week_day_encoding.keys():
            target_date_check["date_diff"] = np.minimum(
                target_date_check.date.dt.dayofweek - week_day_encoding[regular_payday],
                -target_date_check.date.dt.dayofweek + week_day_encoding[regular_payday],
            )
        elif "," in regular_payday:
            regular_payday_1, regular_payday_2 = (
                regular_payday.split(",")[0],
                regular_payday.split(",")[1],
            )
            if regular_payday_1.isnumeric() and regular_payday_2.isnumeric():
                target_date_check["date_diff_1"] = np.minimum(
                    (target_date_check.date.dt.day - int(regular_payday_1)) % 30,
                    (-target_date_check.date.dt.day + int(regular_payday_1)) % 30,
                )
                target_date_check["date_diff_2"] = np.minimum(
                    (target_date_check.date.dt.day - int(regular_payday_2)) % 30,
                    (-target_date_check.date.dt.day + int(regular_payday_2)) % 30,
                )
                target_date_check["date_diff"] = np.minimum(
                    target_date_check.date_diff_1, target_date_check.date_diff_2
                )
            else:
                return 1

        elif regular_payday.isnumeric():
            target_date_check["date_diff"] = np.minimum(
                (target_date_check.date.dt.day - int(regular_payday)) % 30,
                (-target_date_check.date.dt.day + int(regular_payday)) % 30,
            )

        else:
            return 1

    if (target_date_check.date_diff <= config.DEBIT_DIFF_DATE_TOLERENCE).sum() / len(
        target_date_check
    ) >= config.CLOSE_DAY_DEBIT_TOLERANCE:
        return 2
    else:
        return 1


@timer
def amount_stability_check(target: pd.DataFrame, freq: str) -> tuple[Literal[0, 1, 2, 3], Union[float, int]]:
    # Input: target income source dataframe with date, amount as column, frequency identified
    # Output: Income source recurring rating
    # 0: Grey (not enough transactions observed)
    # 1: sd too large
    # 2: sd a bit close to mean
    # 3: sd small
    target_amount_check = (
        target[[config.PS_TXN_DATE, config.PS_TXN_AMOUNT]].groupby(config.PS_TXN_DATE).sum().reset_index()
    )

    mean = target_amount_check.amount.mean()
    std = target_amount_check.amount.std()
    std_mean_ratio = 0 if mean <= 0 else std / mean

    # Cases where std >= mean
    std_mean_ratio = min(1, std_mean_ratio)
    if len(target_amount_check) <= 1:
        return 0, std_mean_ratio
    if freq == "M":
        if len(target_amount_check) < config.MINIMUM_N_PAYS_M:
            return 0, std_mean_ratio
    if freq == "S" or freq == "B":
        if len(target_amount_check) < config.MINIMUM_N_PAYS_B:
            return 0, std_mean_ratio
    if freq == "W":
        if len(target_amount_check) < config.MINIMUM_N_PAYS_B:
            return 0, std_mean_ratio
    if freq == "I":
        if len(target_amount_check) < config.MINIMUM_N_PAYS_I:
            return 0, std_mean_ratio

    if std_mean_ratio <= config.LOW_STD:
        return 3, std_mean_ratio
    elif std_mean_ratio <= config.MEDIUM_STD:
        return 2, std_mean_ratio
    else:
        return 1, std_mean_ratio
