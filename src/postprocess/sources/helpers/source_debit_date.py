import datetime

import numpy as np
import pandas as pd
from config import config
from config.preload import load_holidays
from postprocess.sources.helpers.enhanced_payday_prediction import (
    get_next_business_day,
    get_previous_business_day,
    is_business_day,
)


## This is TB deprecated because the next payday prediction has been moved to each source file
def debit_date_analysis(income_sources: pd.DataFrame, as_of_date: str):
    """
    This function returns 2 things:
    1. A predicted next payday for each valid income source
    2. Whether their's a payment shifted because of a holiday, if there is, how many days was it shifted
    """
    holidays = config.HOLIDAYS
    if holidays is None:
        holidays = load_holidays(config.HOLIDAYS_PATH)
    holidays.loc[:, "HolidayDate"] = pd.to_datetime(holidays.loc[:, "HolidayDate"], format="%m/%d/%y").dt.date
    holidays = holidays[
        (pd.to_datetime(holidays.HolidayDate) <= pd.to_datetime(as_of_date))
        & (pd.to_datetime(holidays.HolidayDate) >= pd.to_datetime(as_of_date) - pd.Timedelta(days=365))
    ]
    next_paydays = []
    payment_near_holiday_list = []
    next_payday_on_holiday_list = []
    for i in range(len(income_sources)):
        frequency = income_sources.iloc[i, :].loc["frequency"]
        last_payday = income_sources.iloc[i, :].loc["lastPayDay"]
        regular_payday = income_sources.iloc[i, :].loc["regularPayDay"]
        historical_paydays = income_sources.iloc[i, :].loc["historicalPayDay"]
        num_pays = income_sources.iloc[i, :].loc["numOfPay"]
        same_day_freq = income_sources.iloc[i, :].loc["sameDayFreq"]
        income_type = income_sources.iloc[i, :].loc["incomeType"]
        if income_type not in ["Payroll", "Benefit"] or frequency not in ["B", "W", "M", "S"]:
            next_paydays.append("Not Applicable")
            payment_near_holiday_list.append("None")
            next_payday_on_holiday_list.append("Not Applicable")
            continue
        # Run estimate next payday only if the source has a frequency
        next_pay_date, next_payday_on_holiday_flag = predict_next_payday(last_payday, frequency, regular_payday)
        if next_pay_date == "Not Applicable":
            next_paydays.append("Not Applicable")
            payment_near_holiday_list.append("None")
            next_payday_on_holiday_list.append("None")
            continue
        next_payday_on_holiday = str(next_payday_on_holiday_flag == 1)

        # Estimate if payment would show up on holiday
        if frequency in ["W", "B"] and regular_payday not in [
            "Friday",
            "Wednesday",
            "Thursday",
            "Tuesday",
            "Monday",
            "Saturday",
            "Sunday",
        ]:
            next_paydays.append(next_pay_date)
            payment_near_holiday_list.append("None")
            next_payday_on_holiday_list.append(next_payday_on_holiday)
            continue

        if frequency == "S" and (same_day_freq < 0.5 or num_pays < 4):
            next_paydays.append(next_pay_date)
            payment_near_holiday_list.append("None")
            next_payday_on_holiday_list.append(next_payday_on_holiday)
            continue
        if frequency == "M" and (same_day_freq < 0.5 or num_pays < 3):
            next_paydays.append(next_pay_date)
            payment_near_holiday_list.append("None")
            next_payday_on_holiday_list.append(next_payday_on_holiday)
            continue
        payment_near_holiday = check_weekly_income_on_holiday(
            pd.to_datetime(historical_paydays), regular_payday, holidays, frequency
        )
        next_paydays.append(next_pay_date)
        payment_near_holiday_list.append(payment_near_holiday)
        next_payday_on_holiday_list.append(next_payday_on_holiday)
    income_sources.loc[:, "nextPayDay"] = next_paydays
    income_sources.loc[:, "paymentNearHoliday"] = payment_near_holiday_list
    income_sources.loc[:, "nextPayDayOnHoliday"] = next_payday_on_holiday_list
    return income_sources


def filter_and_select_closest_candidate(candidates, last_payday, next_payday_estimate):
    """
    Filter candidates to only keep those at least 3 days after last payday,
    then return the one closest to the estimate.

    Returns tuple of (selected_candidate, or None if no valid candidates)
    """
    min_date = last_payday + datetime.timedelta(days=3)
    candidates = [c for c in candidates if c > min_date]
    if not candidates:
        return None
    distances = [np.abs((candidate - next_payday_estimate).days) for candidate in candidates]
    return candidates[np.argmin(distances)]


# Next payday prediction
def predict_next_payday(last_payday, freq, regular_payday, paymentNearHoliday="None"):
    """
    Returns tuple of (next_payday, nextPayDayOnHoliday)
    """
    regular_payday = str(regular_payday)
    week_day_encoding = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6,
    }
    if last_payday == "None" or last_payday == "Not Applicable":
        return "Not Applicable", 0
    last_payday = pd.Timestamp(last_payday)
    if regular_payday == "None" or regular_payday is None:
        return "Not Applicable", 0
    if freq == "I":
        return "Not Applicable", 0

    # Calculate base next payday
    next_pay_date = None

    if freq == "W":
        # Find the occurrence of regular payday weekday closest to 7 days from last payday
        if regular_payday in week_day_encoding:
            expected_weekday = week_day_encoding[regular_payday]
            target_date = last_payday + datetime.timedelta(days=7)
            target_weekday = target_date.weekday()

            # Calculate days to adjust from target to get to the expected weekday
            days_diff = (expected_weekday - target_weekday) % 7
            if days_diff > 3:
                # Closer to go backward (e.g., if diff is 6, going back 1 day is closer)
                days_diff -= 7

            next_pay_date = target_date + datetime.timedelta(days=days_diff)
        else:
            # Regular payday is not a valid weekday, just add 7 days
            next_pay_date = last_payday + datetime.timedelta(days=7)
    elif freq == "B":
        # Find the occurrence of regular payday weekday closest to 14 days from last payday
        if regular_payday in week_day_encoding:
            expected_weekday = week_day_encoding[regular_payday]
            target_date = last_payday + datetime.timedelta(days=14)
            target_weekday = target_date.weekday()

            # Calculate days to adjust from target to get to the expected weekday
            days_diff = (expected_weekday - target_weekday) % 7
            if days_diff > 3:
                # Closer to go backward (e.g., if diff is 6, going back 1 day is closer)
                days_diff -= 7

            next_pay_date = target_date + datetime.timedelta(days=days_diff)
        else:
            # Regular payday is not a valid weekday, just add 14 days
            next_pay_date = last_payday + datetime.timedelta(days=14)
    elif freq == "M":
        last_payment_month = last_payday.month
        last_payment_year = last_payday.year
        next_month = (last_payment_month) % 12 + 1
        next_year = last_payment_year if last_payment_month + 1 <= 12 else last_payment_year + 1
        next_2_month = (next_month) % 12 + 1
        next_2_year = next_year if next_month + 1 <= 12 else next_year + 1
        if "in Week" in regular_payday:
            day_week = week_day_encoding[regular_payday.split()[0]]
            week_part = regular_payday.split()[-1]
            if week_part == "last":
                # For "last" week, we need to find the last occurrence of that weekday in the month
                week_month = -1  # Special marker for last week
            else:
                week_month = int(week_part)
            next_pay_date = get_date_from_week_month(next_month, next_year, day_week, week_month)
        elif "lastday" in regular_payday:
            next_payday_estimate = last_payday + datetime.timedelta(days=30)

            candidate1 = pd.Timestamp(next_year, next_month, 1) + pd.offsets.MonthEnd()
            candidate2 = pd.Timestamp(last_payment_year, last_payment_month, 1) + pd.offsets.MonthEnd()
            candidate3 = pd.Timestamp(next_2_year, next_2_month, 1) + pd.offsets.MonthEnd()
            candidates = [candidate1, candidate2, candidate3]
            next_pay_date = filter_and_select_closest_candidate(candidates, last_payday, next_payday_estimate)
            if next_pay_date is None:
                return "Not Applicable", 0
        elif "near end of month" in regular_payday.lower():
            next_payday_estimate = last_payday + datetime.timedelta(days=30)

            # Use the actual end of month
            candidate1 = pd.Timestamp(next_year, next_month, 1) + pd.offsets.MonthEnd()
            candidate2 = pd.Timestamp(last_payment_year, last_payment_month, 1) + pd.offsets.MonthEnd()
            candidate3 = pd.Timestamp(next_2_year, next_2_month, 1) + pd.offsets.MonthEnd()
            candidates = [candidate1, candidate2, candidate3]
            next_pay_date = filter_and_select_closest_candidate(candidates, last_payday, next_payday_estimate)
            if next_pay_date is None:
                return "Not Applicable", 0
        elif "near day" in regular_payday.lower():
            next_payday_estimate = last_payday + datetime.timedelta(days=30)

            # Extract target day from "near day {target_day}"
            target_day = int(regular_payday.split()[-1])
            candidate1 = pd.Timestamp(
                next_year, next_month, min(target_day, pd.Timestamp(next_year, next_month, 1).days_in_month)
            )
            candidate2 = pd.Timestamp(
                last_payment_year,
                last_payment_month,
                min(target_day, pd.Timestamp(last_payment_year, last_payment_month, 1).days_in_month),
            )
            candidate3 = pd.Timestamp(
                next_2_year, next_2_month, min(target_day, pd.Timestamp(next_2_year, next_2_month, 1).days_in_month)
            )
            candidates = [candidate1, candidate2, candidate3]
            next_pay_date = filter_and_select_closest_candidate(candidates, last_payday, next_payday_estimate)
            if next_pay_date is None:
                return "Not Applicable", 0
        elif regular_payday.isnumeric():
            next_payday_estimate = last_payday + datetime.timedelta(days=30)
            candidate1 = pd.Timestamp(
                next_year, next_month, min(int(regular_payday), pd.Timestamp(next_year, next_month, 1).days_in_month)
            )
            candidate2 = pd.Timestamp(
                last_payment_year,
                last_payment_month,
                min(int(regular_payday), pd.Timestamp(last_payment_year, last_payment_month, 1).days_in_month),
            )
            candidate3 = pd.Timestamp(
                next_2_year,
                next_2_month,
                min(int(regular_payday), pd.Timestamp(next_2_year, next_2_month, 1).days_in_month),
            )
            candidates = [candidate1, candidate2, candidate3]
            next_pay_date = filter_and_select_closest_candidate(candidates, last_payday, next_payday_estimate)
            if next_pay_date is None:
                return "Not Applicable", 0
        else:
            return "Not Applicable", 0

    elif freq == "S":
        if "," not in regular_payday:
            return "Not Applicable", 0
        last_payment_month = last_payday.month
        last_payment_year = last_payday.year
        next_month = (last_payment_month) % 12 + 1
        next_year = last_payment_year if last_payment_month + 1 <= 12 else last_payment_year + 1
        regular_payday_1, regular_payday_2 = regular_payday.split(",")[0], regular_payday.split(",")[1]
        next_payday_estimate = last_payday + datetime.timedelta(days=15)
        if "lastday" in regular_payday_1:
            candidate1 = pd.Timestamp(next_year, next_month, 1) + pd.offsets.MonthEnd()
            candidate2 = pd.Timestamp(last_payment_year, last_payment_month, 1) + pd.offsets.MonthEnd()
        else:
            candidate1 = pd.Timestamp(
                next_year, next_month, min(int(regular_payday_1), pd.Timestamp(next_year, next_month, 1).days_in_month)
            )
            candidate2 = pd.Timestamp(
                last_payment_year,
                last_payment_month,
                min(int(regular_payday_1), pd.Timestamp(last_payment_year, last_payment_month, 1).days_in_month),
            )

        if "lastday" in regular_payday_2:
            candidate3 = pd.Timestamp(next_year, next_month, 1) + pd.offsets.MonthEnd()
            candidate4 = pd.Timestamp(last_payment_year, last_payment_month, 1) + pd.offsets.MonthEnd()
        else:
            candidate3 = pd.Timestamp(
                next_year, next_month, min(int(regular_payday_2), pd.Timestamp(next_year, next_month, 1).days_in_month)
            )
            candidate4 = pd.Timestamp(
                last_payment_year,
                last_payment_month,
                min(int(regular_payday_2), pd.Timestamp(last_payment_year, last_payment_month, 1).days_in_month),
            )
        candidates = [candidate1, candidate2, candidate3, candidate4]
        next_pay_date = filter_and_select_closest_candidate(candidates, last_payday, next_payday_estimate)
        if next_pay_date is None:
            return "Not Applicable", 0
    else:
        return "Not Applicable", 0

    if next_pay_date is None:
        return "Not Applicable", 0

    # Check if original next payday is on holiday/weekend
    next_pay_date_obj = next_pay_date.date() if hasattr(next_pay_date, "date") else next_pay_date
    nextPayDayOnHoliday = 0 if is_business_day(next_pay_date_obj) else 1

    # Apply holiday adjustments based on paymentNearHoliday
    if not is_business_day(next_pay_date_obj):
        if paymentNearHoliday == "A":  # After (forward adjustment)
            adjusted_date = get_next_business_day(next_pay_date_obj)
            return pd.Timestamp(adjusted_date), nextPayDayOnHoliday
        elif paymentNearHoliday == "B":  # Before (backward adjustment)
            adjusted_date = get_previous_business_day(next_pay_date_obj)
            return pd.Timestamp(adjusted_date), nextPayDayOnHoliday
        else:
            # Default to previous business day (same as "B" case)
            adjusted_date = get_previous_business_day(next_pay_date_obj)
            return pd.Timestamp(adjusted_date), nextPayDayOnHoliday

    return next_pay_date, nextPayDayOnHoliday


def get_date_from_week_month(month, year, weekday, nweekday):
    first_day = pd.Timestamp(year, month, 1)
    first_day_weekday = first_day.weekday()

    if nweekday == -1:  # Handle "last" week
        # Find the last occurrence of the weekday in the month
        last_day = pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd()
        last_day_weekday = last_day.weekday()

        # Calculate days back from end of month to get to the target weekday
        if weekday <= last_day_weekday:
            days_back = last_day_weekday - weekday
        else:
            days_back = 7 - (weekday - last_day_weekday)

        return last_day - pd.Timedelta(days=days_back)
    else:
        # Original logic for numbered weeks
        if weekday < first_day_weekday:
            day = (first_day + pd.Timedelta(days=7 - first_day_weekday + weekday + (nweekday - 1) * 7)).day
        else:
            day = (first_day + pd.Timedelta(days=weekday - first_day_weekday + (nweekday - 1) * 7)).day
        return pd.Timestamp(year, month, day)


# Check whether income would show up on holiday
def check_weekly_income_on_holiday(dates, regular_payday, holidays, frequency):
    income_shifted_near_holiday_index = []
    income_shifted_days = []
    for i, date in enumerate(dates):
        if date.date() in list(pd.to_datetime(holidays.HolidayDate).dt.date):
            # return "payment shows up on holiday"
            return None
        if not date_on_regular_payday(regular_payday, date.date(), frequency):
            near_holiday, dates_to_holiday, _ = check_income_would_show_up_on_holiday(
                date.date(), frequency, regular_payday, holidays.HolidayDate
            )
            if near_holiday:
                income_shifted_near_holiday_index.append(i)
                income_shifted_days.append(dates_to_holiday)
    if len(income_shifted_near_holiday_index) > 0:
        if len(np.unique(income_shifted_days)) > 1:
            # Choose mode with lowest abs value
            payment_near_holiday = get_mode_with_smallest_abs_value(income_shifted_days)
        else:
            payment_near_holiday = income_shifted_days[0]
        if payment_near_holiday > 0:
            # return "{} business day(s) before holiday".format(int(payment_near_holiday))
            return "B"
        else:
            # return "{} business day(s) after holiday".format(-int(payment_near_holiday))
            return "A"
    else:
        # return "No payment date changed due to holidays found"
        return "None"


def check_income_would_show_up_on_holiday(date, frequency, regular_payday, holidays):
    # 1. Loop through the list of holidays if there is a holiday within 3 business days of the current date
    # 2. Check if the holiday is a regular payday of the income
    for holiday in list(pd.to_datetime(holidays).dt.date):
        if abs(np.busday_count(date, holiday)) <= 3:
            hit_holiday = date_on_regular_payday(regular_payday, holiday, frequency)
            if hit_holiday:
                return True, np.busday_count(date, holiday), holiday
    return False, None, None


def date_on_regular_payday(regular_payday, date, frequency):
    if frequency in ["W", "B"]:
        return check_day_name_match(date, regular_payday)
    if frequency == "M":
        if "in Week" in regular_payday:
            day_name = regular_payday.split()[0]
            week_part = regular_payday.split()[-1]
            if week_part == "last":
                week_month = -1  # Special marker for last week
            else:
                week_month = int(week_part)
            return check_day_name_match(date, day_name) and check_week_month_match(date, week_month)
        elif "lastday" in regular_payday:
            return check_month_end_match(date)
        elif "near end of month" in regular_payday:
            return check_near_end_of_month_match(date)
        elif "near day" in regular_payday:
            target_day = int(regular_payday.split()[-1])
            return check_near_day_match(date, target_day)
        elif regular_payday.isnumeric():
            day_month = int(regular_payday)
            return check_day_month_match(date, day_month)
        else:
            return False
    if frequency == "S":
        ## TODO
        ## Semimonthly needs day_name in Week x as well
        if "," not in regular_payday:
            return False
        regular_payday_1, regular_payday_2 = regular_payday.split(",")[0], regular_payday.split(",")[1]
        if "in Week" in regular_payday_1:
            day_name_1 = regular_payday_1.split()[0]
            week_month_1 = int(regular_payday_1.split()[-1])
            if check_day_name_match(date, day_name_1) and check_week_month_match(date, week_month_1):
                return True
        elif regular_payday_1.isnumeric():
            day_month_1 = int(regular_payday_1)
            if check_day_month_match(date, day_month_1):
                return True
        if "in Week" in regular_payday_2:
            day_name_2 = regular_payday_2.split()[0]
            week_month_2 = int(regular_payday_2.split()[-1])
            if check_day_name_match(date, day_name_2) and check_week_month_match(date, week_month_2):
                return True
        elif regular_payday_2.isnumeric():
            day_month_2 = int(regular_payday_2)
            if check_day_month_match(date, day_month_2):
                return True
        elif "lastday" in regular_payday_2:
            if check_month_end_match(date):
                return True
        return False


def check_day_name_match(date, day_name):
    return pd.to_datetime(date).day_name() == day_name


def check_week_month_match(date, week_month):
    day = pd.to_datetime(date).day
    if week_month == -1:  # Handle "last" week
        # Check if this is the last occurrence of this weekday in the month
        date_obj = pd.to_datetime(date)
        # Check if adding 7 days would go into the next month
        next_week = date_obj + pd.Timedelta(days=7)
        return next_week.month != date_obj.month
    else:
        # Original logic for numbered weeks
        return ((day - 1) // 7 + 1) == week_month


def check_month_end_match(date):
    return pd.to_datetime(date).is_month_end


def check_day_month_match(date, day_month):
    return pd.to_datetime(date).day == day_month


def check_near_end_of_month_match(date):
    """Check if the date is the actual end of month"""
    return pd.to_datetime(date).is_month_end


def check_near_day_match(date, target_day):
    """Check if the date matches the target day of month (or last day if target exceeds month length)"""
    date_obj = pd.to_datetime(date)
    month_days = date_obj.days_in_month
    adjusted_target_day = min(target_day, month_days)
    return date_obj.day == adjusted_target_day


def get_mode_with_smallest_abs_value(array):
    value_counts = pd.Series(array).value_counts()
    mode = np.max(value_counts.values)
    indexes = np.array(value_counts[value_counts == mode].index)
    return indexes[np.argmin(np.abs(indexes))]
