"""
Enhanced Regular Payday Pattern Prediction

This module contains the enhanced algorithm for predicting monthly regular payday patterns,
extracted from the research notebook improve_regular_payday_clean.ipynb.

The enhanced algorithm provides better detection of irregular patterns through fallback
analysis when primary patterns cannot be detected.
"""

import calendar
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from config import config

# Import holiday data loader if available
holidays = config.HOLIDAYS
holiday_dates = set(pd.to_datetime(holidays["HolidayDate"], format="%m/%d/%y", errors="coerce").dt.date)


def is_weekend(date):
    """Check if a date falls on weekend (Saturday=5, Sunday=6)"""
    return date.weekday() >= 5


def is_holiday(date):
    """Check if a date is a federal holiday"""
    return date in holiday_dates


def is_business_day(date):
    """Check if a date is a business day (not weekend or holiday)"""
    return not (is_weekend(date) or is_holiday(date))


def get_previous_business_day(date):
    """Get the previous business day"""
    prev_date = date - timedelta(days=1)
    while not is_business_day(prev_date):
        prev_date = prev_date - timedelta(days=1)
    return prev_date


def get_next_business_day(date):
    """Get the next business day"""
    next_date = date + timedelta(days=1)
    while not is_business_day(next_date):
        next_date = next_date + timedelta(days=1)
    return next_date


def get_last_day_of_month(year, month):
    """Get the last day of a given month"""
    return calendar.monthrange(year, month)[1]


def get_weekday_of_weekmonth(date):
    """Get weekday and week number within month

    Returns:
        tuple: (weekday_name, week_number) where week_number is 1-based
               or 'last' for last occurrence of weekday in month
    """
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_name = weekday_names[date.weekday()]

    # Calculate which week of the month this is
    week_number = ((date.day - 1) // 7) + 1

    # Check if this is the last occurrence of this weekday in the month
    last_day_of_month = get_last_day_of_month(date.year, date.month)
    days_remaining = last_day_of_month - date.day
    if days_remaining < 7:
        return (weekday_name, "last")
    else:
        return (weekday_name, week_number)


def get_weekday_of_k_week(date):
    """Get weekday and week number for k-week patterns (1-4, not 'last')

    Returns:
        tuple: (weekday_name, week_number) where week_number is 1-4
    """
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_name = weekday_names[date.weekday()]

    # Calculate which week of the month this is
    week_number = ((date.day - 1) // 7) + 1

    return (weekday_name, week_number)


def get_weekday_of_last_week(date):
    """Get weekday if it's the last occurrence in the month

    Returns:
        str: weekday_name if this is the last occurrence, None otherwise
    """
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_name = weekday_names[date.weekday()]

    # Check if this is the last occurrence of this weekday in the month
    last_day_of_month = get_last_day_of_month(date.year, date.month)
    days_remaining = last_day_of_month - date.day
    if days_remaining < 7:
        return weekday_name  # This is last week
    else:
        return None  # This is not last week


def analyze_day_of_month_pattern_hybrid(observed_paydays: List[datetime]) -> Dict[str, Any]:
    """Two-phase day-of-month analysis: raw pattern detection + outlier adjustment validation"""
    if len(observed_paydays) < 2:
        return {"is_valid": False, "score": 0.0}

    # Phase 1: Get raw consistency - find all tied most common days
    day_counts = Counter([date.day for date in observed_paydays])
    max_count = day_counts.most_common(1)[0][1]
    tied_days = [day for day, count in day_counts.items() if count == max_count]

    # Test each tied day and find the one with best adjustment performance
    best_score = 0.0
    best_result = None

    for candidate_day in tied_days:
        raw_count = day_counts[candidate_day]

        # Phase 2: For outliers, check if they're adjusted versions of candidate day
        adjusted_matches = raw_count  # Start with raw matches
        # Track adjustment direction counts
        adjustment_count_A = 0  # After adjustments (forward)
        adjustment_count_B = 0  # Before adjustments (backward)
        outliers = []

        for observed_date in observed_paydays:
            if observed_date.day != candidate_day:
                outliers.append(observed_date)

        for outlier_date in outliers:
            year, month = outlier_date.year, outlier_date.month

            # Construct intended payday for this month based on inferred pattern
            intended_date = None
            try:
                intended_date = datetime(year, month, candidate_day).date()
            except ValueError:
                # Day doesn't exist in this month (e.g., Feb 30) - skip this outlier
                continue

            # Only check adjustments if intended date falls on non-business day
            if not is_business_day(intended_date):
                prev_business_day = get_previous_business_day(intended_date)
                next_business_day = get_next_business_day(intended_date)

                if outlier_date == prev_business_day:
                    adjusted_matches += 1
                    adjustment_count_B += 1
                elif outlier_date == next_business_day:
                    adjusted_matches += 1
                    adjustment_count_A += 1

            # Handle cross-month adjustments more comprehensively
            # Check if outlier could be from previous month's adjustment
            if month > 1:
                prev_month_year, prev_month = year, month - 1
            else:
                prev_month_year, prev_month = year - 1, 12

            try:
                prev_month_intended = datetime(prev_month_year, prev_month, candidate_day).date()
                if not is_business_day(prev_month_intended):
                    # Check both directions of adjustment
                    prev_month_adjusted_back = get_previous_business_day(prev_month_intended)
                    prev_month_adjusted_forward = get_next_business_day(prev_month_intended)

                    if outlier_date == prev_month_adjusted_back:
                        adjusted_matches += 1
                        adjustment_count_B += 1
                    elif outlier_date == prev_month_adjusted_forward:
                        adjusted_matches += 1
                        adjustment_count_A += 1
            except ValueError:
                pass

            # Check if outlier could be from next month's adjustment
            if month < 12:
                next_month_year, next_month = year, month + 1
            else:
                next_month_year, next_month = year + 1, 1

            try:
                next_month_intended = datetime(next_month_year, next_month, candidate_day).date()
                if not is_business_day(next_month_intended):
                    # Check both directions of adjustment
                    next_month_adjusted_back = get_previous_business_day(next_month_intended)
                    next_month_adjusted_forward = get_next_business_day(next_month_intended)

                    if outlier_date == next_month_adjusted_back:
                        adjusted_matches += 1
                        adjustment_count_B += 1
                    elif outlier_date == next_month_adjusted_forward:
                        adjusted_matches += 1
                        adjustment_count_A += 1
            except ValueError:
                pass

        # Calculate consistency for this candidate
        final_consistency = adjusted_matches / len(observed_paydays)

        if final_consistency > best_score:
            best_score = final_consistency
            best_result = {
                "day": candidate_day,
                "raw_count": raw_count,
                "adjusted_matches": adjusted_matches,
                "consistency": final_consistency,
                "adjustment_count_A": adjustment_count_A,
                "adjustment_count_B": adjustment_count_B,
            }

    if best_result and best_score >= 0.6:  # At least 60% consistency
        # Determine adjustment direction
        adjustment_direction = "None"
        if best_result["adjustment_count_A"] > best_result["adjustment_count_B"]:
            adjustment_direction = "A"
        elif best_result["adjustment_count_B"] > best_result["adjustment_count_A"]:
            adjustment_direction = "B"
        elif (
            best_result["adjustment_count_A"] == best_result["adjustment_count_B"]
            and best_result["adjustment_count_A"] > 0
        ):
            adjustment_direction = "A"  # Default to A when tied and both > 0

        return {
            "is_valid": True,
            "pattern_type": "day_of_month",
            "consistency": best_result["consistency"],
            "score": best_result["consistency"],
            "description": f"Monthly payday on day {best_result['day']} of month",
            "raw_matches": best_result["raw_count"],
            "adjusted_matches": best_result["adjusted_matches"],
            "total_paydays": len(observed_paydays),
            "adjustment_direction": adjustment_direction,
            "adjustment_count_A": best_result["adjustment_count_A"],
            "adjustment_count_B": best_result["adjustment_count_B"],
        }

    return {"is_valid": False, "score": 0.0}


def analyze_last_day_pattern_hybrid(observed_paydays: List[datetime]) -> Dict[str, Any]:
    """Two-phase last-day analysis: raw pattern detection + outlier adjustment validation"""
    if len(observed_paydays) < 2:
        return {"is_valid": False, "score": 0.0}

    # Phase 1: Get raw consistency - count actual last day matches
    # Note: For last-day patterns, there's no tie scenario since there's only one last day per month
    raw_matches = 0
    for observed_date in observed_paydays:
        year, month = observed_date.year, observed_date.month
        last_day_of_month = get_last_day_of_month(year, month)
        if observed_date.day == last_day_of_month:
            raw_matches += 1

    # Phase 2: For outliers, check if they're adjusted versions of last day
    adjusted_matches = raw_matches  # Start with raw matches
    # Track adjustment direction counts
    adjustment_count_A = 0  # After adjustments (forward)
    adjustment_count_B = 0  # Before adjustments (backward)
    outliers = []

    for observed_date in observed_paydays:
        year, month = observed_date.year, observed_date.month
        last_day_of_month = get_last_day_of_month(year, month)
        if observed_date.day != last_day_of_month:
            outliers.append(observed_date)

    for outlier_date in outliers:
        year, month = outlier_date.year, outlier_date.month
        last_day_of_month = get_last_day_of_month(year, month)
        intended_date = datetime(year, month, last_day_of_month).date()

        # Only check adjustments if intended date falls on non-business day
        if not is_business_day(intended_date):
            prev_business_day = get_previous_business_day(intended_date)
            next_business_day = get_next_business_day(intended_date)

            if outlier_date == prev_business_day:
                adjusted_matches += 1
                adjustment_count_B += 1
            elif outlier_date == next_business_day:
                adjusted_matches += 1
                adjustment_count_A += 1

        # Handle cross-month adjustments for last-day patterns
        # Check if outlier could be from previous month's last-day adjustment
        if month > 1:
            prev_month_year, prev_month = year, month - 1
        else:
            prev_month_year, prev_month = year - 1, 12

        prev_month_last_day = get_last_day_of_month(prev_month_year, prev_month)
        prev_month_intended = datetime(prev_month_year, prev_month, prev_month_last_day).date()

        if not is_business_day(prev_month_intended):
            prev_month_adjusted = get_next_business_day(prev_month_intended)
            # Check if the adjustment crossed into the current month
            if prev_month_adjusted.month != prev_month and outlier_date == prev_month_adjusted:
                adjusted_matches += 1
                adjustment_count_A += 1

        # Check if outlier could be from next month's last-day adjustment moved backward
        if month < 12:
            next_month_year, next_month = year, month + 1
        else:
            next_month_year, next_month = year + 1, 1

        next_month_last_day = get_last_day_of_month(next_month_year, next_month)
        next_month_intended = datetime(next_month_year, next_month, next_month_last_day).date()

        if not is_business_day(next_month_intended):
            next_month_adjusted = get_previous_business_day(next_month_intended)
            # Check if the adjustment crossed into the current month
            if next_month_adjusted.month != next_month and outlier_date == next_month_adjusted:
                adjusted_matches += 1
                adjustment_count_B += 1

    # Calculate final consistency
    final_consistency = adjusted_matches / len(observed_paydays)

    if final_consistency >= 0.6:  # At least 60% consistency
        # Determine adjustment direction
        adjustment_direction = "None"
        if adjustment_count_A > adjustment_count_B:
            adjustment_direction = "A"
        elif adjustment_count_B > adjustment_count_A:
            adjustment_direction = "B"
        elif adjustment_count_A == adjustment_count_B and adjustment_count_A > 0:
            adjustment_direction = "A"  # Default to A when tied and both > 0

        return {
            "is_valid": True,
            "pattern_type": "last_day",
            "consistency": final_consistency,
            "score": final_consistency,
            "description": "Monthly payday on last day of month",
            "raw_matches": raw_matches,
            "adjusted_matches": adjusted_matches,
            "total_paydays": len(observed_paydays),
            "adjustment_direction": adjustment_direction,
            "adjustment_count_A": adjustment_count_A,
            "adjustment_count_B": adjustment_count_B,
        }

    return {"is_valid": False, "score": 0.0}


def analyze_weekday_pattern_k_week(observed_paydays: List[datetime]) -> Dict[str, Any]:
    """Two-phase k-week weekday analysis: specific week numbers (1-4), not 'last'"""
    if len(observed_paydays) < 2:
        return {"is_valid": False, "score": 0.0}

    # Phase 1: Get raw consistency - find all tied most common k-week patterns
    k_week_patterns = []
    for date in observed_paydays:
        weekday, week = get_weekday_of_k_week(date)
        if week <= 4:  # Only consider weeks 1-4, not 'last'
            k_week_patterns.append((weekday, week))

    if len(k_week_patterns) < 2:
        return {"is_valid": False, "score": 0.0}

    pattern_counts = Counter(k_week_patterns)
    max_count = pattern_counts.most_common(1)[0][1]
    tied_patterns = [pattern for pattern, count in pattern_counts.items() if count == max_count]

    # Test each tied pattern and find the one with best adjustment performance
    best_score = 0.0
    best_result = None

    for candidate_pattern in tied_patterns:
        candidate_weekday, candidate_week = candidate_pattern
        raw_count = pattern_counts[candidate_pattern]

        # Phase 2: For outliers, check if they're adjusted versions of candidate pattern
        adjusted_matches = raw_count  # Start with raw matches
        # Track adjustment direction counts
        adjustment_count_A = 0  # After adjustments (forward)
        adjustment_count_B = 0  # Before adjustments (backward)
        outliers = []

        for observed_date in observed_paydays:
            observed_pattern = get_weekday_of_k_week(observed_date)
            if observed_pattern != candidate_pattern and observed_pattern[1] <= 4:
                outliers.append(observed_date)

        for outlier_date in outliers:
            year, month = outlier_date.year, outlier_date.month
            weekday_num = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(
                candidate_weekday
            )

            # Find the k-th occurrence of this weekday in the month
            occurrence_count = 0
            intended_date = None

            for day in range(1, get_last_day_of_month(year, month) + 1):
                test_date = datetime(year, month, day).date()
                if test_date.weekday() == weekday_num:
                    occurrence_count += 1
                    if occurrence_count == candidate_week:
                        intended_date = test_date
                        break

            if intended_date:
                # Only check adjustments if intended date falls on non-business day
                if not is_business_day(intended_date):
                    prev_business_day = get_previous_business_day(intended_date)
                    next_business_day = get_next_business_day(intended_date)

                    if outlier_date == prev_business_day:
                        adjusted_matches += 1
                        adjustment_count_B += 1
                    elif outlier_date == next_business_day:
                        adjusted_matches += 1
                        adjustment_count_A += 1

        # Calculate consistency for this candidate
        final_consistency = adjusted_matches / len([p for p in k_week_patterns if p[1] <= 4])

        if final_consistency > best_score:
            best_score = final_consistency
            best_result = {
                "weekday": candidate_weekday,
                "week": candidate_week,
                "raw_count": raw_count,
                "adjusted_matches": adjusted_matches,
                "consistency": final_consistency,
                "adjustment_count_A": adjustment_count_A,
                "adjustment_count_B": adjustment_count_B,
            }

    if best_result and best_score >= 0.6:  # At least 60% consistency
        # Determine adjustment direction
        adjustment_direction = "None"
        if best_result["adjustment_count_A"] > best_result["adjustment_count_B"]:
            adjustment_direction = "A"
        elif best_result["adjustment_count_B"] > best_result["adjustment_count_A"]:
            adjustment_direction = "B"
        elif (
            best_result["adjustment_count_A"] == best_result["adjustment_count_B"]
            and best_result["adjustment_count_A"] > 0
        ):
            adjustment_direction = "A"  # Default to A when tied and both > 0

        return {
            "is_valid": True,
            "pattern_type": "weekday_k_week",
            "consistency": best_result["consistency"],
            "score": best_result["consistency"],
            "description": f"Monthly payday on {best_result['weekday']} of week {best_result['week']}",
            "raw_matches": best_result["raw_count"],
            "adjusted_matches": best_result["adjusted_matches"],
            "total_paydays": len(observed_paydays),
            "adjustment_direction": adjustment_direction,
            "adjustment_count_A": best_result["adjustment_count_A"],
            "adjustment_count_B": best_result["adjustment_count_B"],
        }

    return {"is_valid": False, "score": 0.0}


def analyze_weekday_pattern_last_week(observed_paydays: List[datetime]) -> Dict[str, Any]:
    """Two-phase last-week weekday analysis: last occurrence of weekday in month"""
    if len(observed_paydays) < 2:
        return {"is_valid": False, "score": 0.0}

    # Phase 1: Get raw consistency - find all tied most common last-week patterns
    last_week_patterns = [get_weekday_of_last_week(date) for date in observed_paydays]
    last_week_patterns = [p for p in last_week_patterns if p is not None]  # Filter out None (not last week)

    if len(last_week_patterns) < 2:
        return {"is_valid": False, "score": 0.0}

    pattern_counts = Counter(last_week_patterns)
    max_count = pattern_counts.most_common(1)[0][1]
    tied_patterns = [pattern for pattern, count in pattern_counts.items() if count == max_count]

    # Test each tied pattern and find the one with best adjustment performance
    best_score = 0.0
    best_result = None

    for candidate_weekday in tied_patterns:
        raw_count = pattern_counts[candidate_weekday]

        # Phase 2: For outliers, check if they're adjusted versions of candidate pattern
        adjusted_matches = raw_count  # Start with raw matches
        # Track adjustment direction counts
        adjustment_count_A = 0  # After adjustments (forward)
        adjustment_count_B = 0  # Before adjustments (backward)
        outliers = []

        for observed_date in observed_paydays:
            if get_weekday_of_last_week(observed_date) != candidate_weekday:
                outliers.append(observed_date)

        for outlier_date in outliers:
            year, month = outlier_date.year, outlier_date.month
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(candidate_weekday)

            # Construct intended payday for this month based on inferred pattern
            # Find last occurrence of this weekday in month
            last_day = get_last_day_of_month(year, month)
            intended_date = None

            for day in range(last_day, 0, -1):
                test_date = datetime(year, month, day).date()
                if get_weekday_of_last_week(test_date) == candidate_weekday:
                    intended_date = test_date
                    break

            if intended_date:
                # Only check adjustments if intended date falls on non-business day
                if not is_business_day(intended_date):
                    prev_business_day = get_previous_business_day(intended_date)
                    next_business_day = get_next_business_day(intended_date)

                    if outlier_date == prev_business_day:
                        adjusted_matches += 1
                        adjustment_count_B += 1
                    elif outlier_date == next_business_day:
                        adjusted_matches += 1
                        adjustment_count_A += 1

        # Calculate consistency for this candidate
        final_consistency = adjusted_matches / len(observed_paydays)

        if final_consistency > best_score:
            best_score = final_consistency
            best_result = {
                "weekday": candidate_weekday,
                "raw_count": raw_count,
                "adjusted_matches": adjusted_matches,
                "consistency": final_consistency,
                "adjustment_count_A": adjustment_count_A,
                "adjustment_count_B": adjustment_count_B,
            }

    if best_result and best_score >= 0.6:  # At least 60% consistency
        # Determine adjustment direction
        adjustment_direction = "None"
        if best_result["adjustment_count_A"] > best_result["adjustment_count_B"]:
            adjustment_direction = "A"
        elif best_result["adjustment_count_B"] > best_result["adjustment_count_A"]:
            adjustment_direction = "B"
        elif (
            best_result["adjustment_count_A"] == best_result["adjustment_count_B"]
            and best_result["adjustment_count_A"] > 0
        ):
            adjustment_direction = "A"  # Default to A when tied and both > 0

        return {
            "is_valid": True,
            "pattern_type": "weekday_last_week",
            "consistency": best_result["consistency"],
            "score": best_result["consistency"],
            "description": f"Monthly payday on {best_result['weekday']} of last week",
            "raw_matches": best_result["raw_count"],
            "adjusted_matches": best_result["adjusted_matches"],
            "total_paydays": len(observed_paydays),
            "adjustment_direction": adjustment_direction,
            "adjustment_count_A": best_result["adjustment_count_A"],
            "adjustment_count_B": best_result["adjustment_count_B"],
        }

    return {"is_valid": False, "score": 0.0}


def predict_monthly_regular_payday(observed_paydays: List[datetime]) -> Dict[str, Any]:
    """O(n) hybrid algorithm: raw consistency + outlier adjustment validation"""
    if len(observed_paydays) < 2:
        return {
            "predicted_pattern": None,
            "confidence": 0.0,
            "pattern_details": None,
            "algorithm": "hybrid_two_phase",
            "time_complexity": "O(n)",
        }

    # Test all pattern types in O(n) time each
    pattern_analyzers = [
        analyze_day_of_month_pattern_hybrid,
        analyze_last_day_pattern_hybrid,
        analyze_weekday_pattern_last_week,
        analyze_weekday_pattern_k_week,
    ]

    best_pattern = None
    best_score = 0.0

    for analyzer in pattern_analyzers:
        result = analyzer(observed_paydays)
        if result["is_valid"] and result["score"] >= best_score:
            best_score = result["score"]
            best_pattern = result

    if best_pattern:
        return {
            "predicted_pattern": best_pattern["pattern_type"],
            "confidence": best_pattern["score"],
            "pattern_details": best_pattern,
            "adjustment_accuracy": best_pattern["score"],
        }
    else:
        return {"predicted_pattern": None, "confidence": 0.0, "pattern_details": None, "adjustment_accuracy": 0.0}


def analyze_end_of_month_tendency(observed_paydays: List[datetime]) -> Dict[str, Any]:
    """Analyze if paydays tend to occur at the end of the month

    Args:
        observed_paydays: List of observed payday dates

    Returns:
        Dictionary with analysis results
    """
    if len(observed_paydays) < 2:
        return {"is_valid": False, "score": 0.0}

    end_of_month_count = 0
    month_stats = []

    for date in observed_paydays:
        year, month = date.year, date.month
        last_day_of_month = get_last_day_of_month(year, month)

        # Consider "end of month" as last 7 days of the month
        days_from_end = last_day_of_month - date.day

        # Also check if this could be an adjustment from the previous month's end
        # For dates in the first 7 days of the month, check if they could be
        # adjusted from the end of the previous month
        if date.day <= 7:
            days_from_end = date.day  # Adjusted to count from the start of the month

        month_stats.append(
            {"date": date, "day": date.day, "last_day": last_day_of_month, "days_from_end": days_from_end}
        )

        # Count as end-of-month if within last 7 days
        if days_from_end <= 3:
            end_of_month_count += 1

    consistency = end_of_month_count / len(observed_paydays)

    # Calculate average position within the end-of-month window
    end_of_month_positions = [stat["days_from_end"] for stat in month_stats if stat["days_from_end"] <= 6]
    avg_position = np.mean(end_of_month_positions) if end_of_month_positions else None

    if consistency >= 0.8:  # At least 80% of paydays are end-of-month
        return {
            "is_valid": True,
            "pattern_type": "end_of_month_tendency",
            "consistency": consistency,
            "score": consistency,
            "description": "Paydays tend to occur at end of month (last 3 days)",
            "matches": end_of_month_count,
            "total_paydays": len(observed_paydays),
            "avg_days_from_end": avg_position,
            "month_stats": month_stats,
        }

    return {"is_valid": False, "score": 0.0}


def analyze_near_specific_days_tendency(observed_paydays: List[datetime], tolerance: int = 3) -> Dict[str, Any]:
    """Analyze if paydays tend to occur near specific days of the month

    Args:
        observed_paydays: List of observed payday dates
        tolerance: Number of days tolerance around a specific day (default: 3)

    Returns:
        Dictionary with analysis results
    """
    if len(observed_paydays) < 2:
        return {"is_valid": False, "score": 0.0}

    # For each possible target day (1-31), count how many paydays fall within tolerance
    day_scores = {}

    for target_day in range(1, 32):
        matches = 0
        match_details = []

        for date in observed_paydays:
            year, month = date.year, date.month
            last_day_of_month = get_last_day_of_month(year, month)

            # Skip if target day doesn't exist in this month
            if target_day > last_day_of_month:
                continue

            # Calculate distance from target day
            distance = abs(date.day - target_day)

            if distance <= tolerance:
                matches += 1
                match_details.append(
                    {"date": date, "target_day": target_day, "actual_day": date.day, "distance": distance}
                )

        if matches > 0:
            consistency = matches / len(observed_paydays)
            day_scores[target_day] = {
                "target_day": target_day,
                "matches": matches,
                "consistency": consistency,
                "match_details": match_details,
            }

    # Find the best target day
    if day_scores:
        best_target_day = max(day_scores.keys(), key=lambda d: day_scores[d]["consistency"])
        best_score = day_scores[best_target_day]["consistency"]
        best_details = day_scores[best_target_day]

        # Calculate average distance from target day
        distances = [detail["distance"] for detail in best_details["match_details"]]
        avg_distance = np.mean(distances) if distances else 0

        if best_score >= 0.8:  # At least 80% of paydays fall within tolerance
            return {
                "is_valid": True,
                "pattern_type": "near_specific_day_tendency",
                "consistency": best_score,
                "score": best_score,
                "description": f"Paydays tend to occur near day {best_target_day} of month (±{tolerance} days)",
                "target_day": best_target_day,
                "tolerance": tolerance,
                "matches": best_details["matches"],
                "total_paydays": len(observed_paydays),
                "avg_distance": avg_distance,
                "match_details": best_details["match_details"],
            }

    return {"is_valid": False, "score": 0.0}


def _generate_candidate_day_pairs(observed_paydays: List[datetime]) -> List[tuple]:
    """Generate candidate day pairs from observed paydays

    Returns list of (day1, day2) tuples where day1 < day2 and they are at least 7 days apart

    For 3 or fewer observations, also includes candidate days that are ±1 or ±2 days
    from observed days if those offset days are non-business days (weekend/holiday).
    """
    days_seen = set(date.day for date in observed_paydays)

    # If 3 or fewer observations, add potential intended paydays based on nearby non-business days
    if len(observed_paydays) <= 3:
        additional_candidates = set()

        for observed_date in observed_paydays:
            # Check if days around the observed date are non-business days
            # If so, the observed date might be an adjustment, and the non-business day is the intended payday
            for offset in [-2, -1, 1, 2]:
                try:
                    potential_intended_day = observed_date.day + offset
                    # Keep within valid day range (1-31)
                    if potential_intended_day < 1 or potential_intended_day > 31:
                        continue

                    # Try to construct the date in the same month
                    potential_date = datetime(observed_date.year, observed_date.month, potential_intended_day).date()

                    # If this potential date is NOT a business day, add it as a candidate
                    if not is_business_day(potential_date):
                        additional_candidates.add(potential_intended_day)
                except ValueError:
                    # Day doesn't exist in this month (e.g., Feb 30)
                    continue

        # Add additional candidates to days_seen
        days_seen = days_seen.union(additional_candidates)

    candidates = []

    for day1 in sorted(days_seen):
        for day2 in sorted(days_seen):
            if day2 > day1 and day2 - day1 >= 7:
                candidates.append((day1, day2))

    return candidates


def analyze_semi_monthly_two_days_pattern(observed_paydays: List[datetime]) -> Dict[str, Any]:
    """Analyze semi-monthly pattern with two specific days

    Mimics the logic of predict_monthly_regular_payday:
    - Generate candidate pairs from observed days
    - Require at least 7 days between the two days
    - Apply business day adjustment logic
    - Return the pattern with highest consistency score
    """
    if len(observed_paydays) < 2:
        return {"is_valid": False, "score": 0.0}

    candidate_pairs = _generate_candidate_day_pairs(observed_paydays)
    if not candidate_pairs:
        return {"is_valid": False, "score": 0.0}

    best_score = 0.0
    best_result = None

    for day1, day2 in candidate_pairs:
        adjusted_matches = 0
        adjustment_count_A = 0
        adjustment_count_B = 0

        for observed_date in observed_paydays:
            year, month = observed_date.year, observed_date.month

            # Check if date matches either day (with adjustments)
            for target_day in [day1, day2]:
                try:
                    intended_date = datetime(year, month, target_day).date()
                except ValueError:
                    continue

                # Check raw match
                if observed_date == intended_date:
                    adjusted_matches += 1
                    break

                # Check business day adjustments
                if not is_business_day(intended_date):
                    prev_business_day = get_previous_business_day(intended_date)
                    next_business_day = get_next_business_day(intended_date)

                    if observed_date == prev_business_day:
                        adjusted_matches += 1
                        adjustment_count_B += 1
                        break
                    elif observed_date == next_business_day:
                        adjusted_matches += 1
                        adjustment_count_A += 1
                        break

        consistency = adjusted_matches / len(observed_paydays)

        if consistency > best_score:
            best_score = consistency
            best_result = {
                "day1": day1,
                "day2": day2,
                "adjusted_matches": adjusted_matches,
                "consistency": consistency,
                "adjustment_count_A": adjustment_count_A,
                "adjustment_count_B": adjustment_count_B,
            }

    if best_result and best_score >= 0.6:
        adjustment_direction = "None"
        if best_result["adjustment_count_A"] > best_result["adjustment_count_B"]:
            adjustment_direction = "A"
        elif best_result["adjustment_count_B"] > best_result["adjustment_count_A"]:
            adjustment_direction = "B"
        elif (
            best_result["adjustment_count_A"] == best_result["adjustment_count_B"]
            and best_result["adjustment_count_A"] > 0
        ):
            adjustment_direction = "A"

        return {
            "is_valid": True,
            "pattern_type": "semi_monthly_two_days",
            "consistency": best_result["consistency"],
            "score": best_result["consistency"],
            "description": f"Semi-monthly payday on day {best_result['day1']} and day {best_result['day2']}",
            "day1": best_result["day1"],
            "day2": best_result["day2"],
            "adjusted_matches": best_result["adjusted_matches"],
            "total_paydays": len(observed_paydays),
            "adjustment_direction": adjustment_direction,
            "adjustment_count_A": best_result["adjustment_count_A"],
            "adjustment_count_B": best_result["adjustment_count_B"],
        }

    return {"is_valid": False, "score": 0.0}


def analyze_semi_monthly_day_and_last_pattern(observed_paydays: List[datetime]) -> Dict[str, Any]:
    """Analyze semi-monthly pattern with one specific day and last day of month

    Mimics the logic of predict_monthly_regular_payday:
    - Generate candidate specific days from observed days
    - Pair with last day of month
    - Apply business day adjustment logic
    - Return the pattern with highest consistency score
    """
    if len(observed_paydays) < 2:
        return {"is_valid": False, "score": 0.0}

    # Generate candidate specific days (exclude days close to end of month)
    days_seen = set(date.day for date in observed_paydays)

    # If 3 or fewer observations, add potential intended paydays based on nearby non-business days
    if len(observed_paydays) <= 3:
        additional_candidates = set()

        for observed_date in observed_paydays:
            # Skip dates near end of month (they might be the "last day" slot)
            if observed_date.day >= 28:
                continue

            # Check if days around the observed date are non-business days
            for offset in [-2, -1, 1, 2]:
                try:
                    potential_intended_day = observed_date.day + offset
                    # Keep within valid day range for specific day (1-23)
                    if potential_intended_day < 1 or potential_intended_day > 23:
                        continue

                    # Try to construct the date in the same month
                    potential_date = datetime(observed_date.year, observed_date.month, potential_intended_day).date()

                    # If this potential date is NOT a business day, add it as a candidate
                    if not is_business_day(potential_date):
                        additional_candidates.add(potential_intended_day)
                except ValueError:
                    # Day doesn't exist in this month
                    continue

        # Add additional candidates to days_seen
        days_seen = days_seen.union(additional_candidates)

    # Consider days that are at least 7 days before typical month ends
    candidate_days = [day for day in days_seen if day <= 23]

    if not candidate_days:
        return {"is_valid": False, "score": 0.0}

    best_score = 0.0
    best_result = None

    for specific_day in candidate_days:
        adjusted_matches = 0
        adjustment_count_A = 0
        adjustment_count_B = 0

        for observed_date in observed_paydays:
            year, month = observed_date.year, observed_date.month
            last_day_of_month = get_last_day_of_month(year, month)

            # Check if date matches specific day (with adjustments)
            try:
                intended_specific = datetime(year, month, specific_day).date()

                if observed_date == intended_specific:
                    adjusted_matches += 1
                    continue

                if not is_business_day(intended_specific):
                    prev_bd = get_previous_business_day(intended_specific)
                    next_bd = get_next_business_day(intended_specific)

                    if observed_date == prev_bd:
                        adjusted_matches += 1
                        adjustment_count_B += 1
                        continue
                    elif observed_date == next_bd:
                        adjusted_matches += 1
                        adjustment_count_A += 1
                        continue
            except ValueError:
                pass

            # Check if date matches last day (with adjustments)
            intended_last = datetime(year, month, last_day_of_month).date()

            if observed_date == intended_last:
                adjusted_matches += 1
                continue

            if not is_business_day(intended_last):
                prev_bd = get_previous_business_day(intended_last)
                next_bd = get_next_business_day(intended_last)

                if observed_date == prev_bd:
                    adjusted_matches += 1
                    adjustment_count_B += 1
                elif observed_date == next_bd:
                    adjusted_matches += 1
                    adjustment_count_A += 1

        consistency = adjusted_matches / len(observed_paydays)

        if consistency > best_score:
            best_score = consistency
            best_result = {
                "specific_day": specific_day,
                "adjusted_matches": adjusted_matches,
                "consistency": consistency,
                "adjustment_count_A": adjustment_count_A,
                "adjustment_count_B": adjustment_count_B,
            }

    if best_result and best_score >= 0.6:
        adjustment_direction = "None"
        if best_result["adjustment_count_A"] > best_result["adjustment_count_B"]:
            adjustment_direction = "A"
        elif best_result["adjustment_count_B"] > best_result["adjustment_count_A"]:
            adjustment_direction = "B"
        elif (
            best_result["adjustment_count_A"] == best_result["adjustment_count_B"]
            and best_result["adjustment_count_A"] > 0
        ):
            adjustment_direction = "A"

        return {
            "is_valid": True,
            "pattern_type": "semi_monthly_day_and_last",
            "consistency": best_result["consistency"],
            "score": best_result["consistency"],
            "description": f"Semi-monthly payday on day {best_result['specific_day']} and last day of month",
            "specific_day": best_result["specific_day"],
            "adjusted_matches": best_result["adjusted_matches"],
            "total_paydays": len(observed_paydays),
            "adjustment_direction": adjustment_direction,
            "adjustment_count_A": best_result["adjustment_count_A"],
            "adjustment_count_B": best_result["adjustment_count_B"],
        }

    return {"is_valid": False, "score": 0.0}


def predict_semi_monthly_regular_payday(observed_paydays: List[datetime]) -> Dict[str, Any]:
    """Predict semi-monthly regular payday pattern

    Tests both semi-monthly pattern types and returns the one with highest consistency
    """
    if len(observed_paydays) < 2:
        return {
            "predicted_pattern": None,
            "confidence": 0.0,
            "pattern_details": None,
        }

    pattern_analyzers = [
        analyze_semi_monthly_two_days_pattern,
        analyze_semi_monthly_day_and_last_pattern,
    ]

    best_pattern = None
    best_score = 0.0

    for analyzer in pattern_analyzers:
        result = analyzer(observed_paydays)
        if result["is_valid"] and result["score"] > best_score:
            best_score = result["score"]
            best_pattern = result

    if best_pattern:
        return {
            "predicted_pattern": best_pattern["pattern_type"],
            "confidence": best_pattern["score"],
            "pattern_details": best_pattern,
            "adjustment_accuracy": best_pattern["score"],
        }

    return {
        "predicted_pattern": None,
        "confidence": 0.0,
        "pattern_details": None,
        "adjustment_accuracy": 0.0,
    }


def analyze_biweekly_weekday_pattern(observed_paydays: List[datetime]) -> Dict[str, Any]:
    """Analyze biweekly pattern with specific weekday, adjusted for holidays

    Checks if paydays fall on the same weekday consistently, with business day adjustments.
    This helps distinguish biweekly from semi-monthly patterns when intervals are 10-18 days.

    Args:
        observed_paydays: List of observed payday dates

    Returns:
        Dictionary with analysis results including consistency score
    """
    if len(observed_paydays) < 2:
        return {"is_valid": False, "score": 0.0}

    # Get all weekdays from observed paydays
    weekday_counts = Counter([date.weekday() for date in observed_paydays])

    if not weekday_counts:
        return {"is_valid": False, "score": 0.0}

    # Find the most common weekday(s)
    max_count = weekday_counts.most_common(1)[0][1]
    tied_weekdays = [weekday for weekday, count in weekday_counts.items() if count == max_count]

    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    best_score = 0.0
    best_result = None

    for candidate_weekday in tied_weekdays:
        raw_matches = weekday_counts[candidate_weekday]
        adjusted_matches = raw_matches
        adjustment_count_A = 0
        adjustment_count_B = 0

        # Check outliers - dates that don't fall on the candidate weekday
        for observed_date in observed_paydays:
            if observed_date.weekday() != candidate_weekday:
                # This might be an adjustment from the intended weekday
                # Calculate what the intended date would be
                days_diff = (candidate_weekday - observed_date.weekday()) % 7

                # Try moving backward to find intended date
                if days_diff > 0:
                    # Intended date is in the past
                    intended_date = observed_date - timedelta(days=(7 - days_diff))
                else:
                    # We're already past the intended weekday, look at previous week
                    intended_date = observed_date - timedelta(days=7)

                # Check if intended date is a non-business day
                if not is_business_day(intended_date):
                    next_bd = get_next_business_day(intended_date)
                    prev_bd = get_previous_business_day(intended_date)

                    if observed_date == next_bd:
                        adjusted_matches += 1
                        adjustment_count_A += 1
                    elif observed_date == prev_bd:
                        adjusted_matches += 1
                        adjustment_count_B += 1

                # Also try moving forward to find intended date
                if days_diff == 0:
                    days_diff = 7
                intended_date_forward = observed_date + timedelta(days=days_diff)

                if not is_business_day(intended_date_forward):
                    next_bd = get_next_business_day(intended_date_forward)
                    prev_bd = get_previous_business_day(intended_date_forward)

                    if observed_date == next_bd:
                        adjusted_matches += 1
                        adjustment_count_A += 1
                    elif observed_date == prev_bd:
                        adjusted_matches += 1
                        adjustment_count_B += 1

        consistency = adjusted_matches / len(observed_paydays)

        if consistency > best_score:
            best_score = consistency
            best_result = {
                "weekday": weekday_names[candidate_weekday],
                "weekday_num": candidate_weekday,
                "raw_matches": raw_matches,
                "adjusted_matches": adjusted_matches,
                "consistency": consistency,
                "adjustment_count_A": adjustment_count_A,
                "adjustment_count_B": adjustment_count_B,
            }

    if best_result and best_score >= 0.6:
        adjustment_direction = "None"
        if best_result["adjustment_count_A"] > best_result["adjustment_count_B"]:
            adjustment_direction = "A"
        elif best_result["adjustment_count_B"] > best_result["adjustment_count_A"]:
            adjustment_direction = "B"
        elif (
            best_result["adjustment_count_A"] == best_result["adjustment_count_B"]
            and best_result["adjustment_count_A"] > 0
        ):
            adjustment_direction = "A"

        return {
            "is_valid": True,
            "pattern_type": "biweekly_weekday",
            "consistency": best_result["consistency"],
            "score": best_result["consistency"],
            "description": f"Biweekly payday on {best_result['weekday']}",
            "weekday": best_result["weekday"],
            "raw_matches": best_result["raw_matches"],
            "adjusted_matches": best_result["adjusted_matches"],
            "total_paydays": len(observed_paydays),
            "adjustment_direction": adjustment_direction,
            "adjustment_count_A": best_result["adjustment_count_A"],
            "adjustment_count_B": best_result["adjustment_count_B"],
        }

    return {"is_valid": False, "score": 0.0}


def determine_biweekly_or_semimonthly(observed_paydays: List[datetime]) -> Dict[str, Any]:
    """Determine if pattern is biweekly or semi-monthly by comparing consistency scores

    When intervals are approximately 10-18 days, tests both:
    1. Biweekly pattern (specific weekday with holiday adjustments)
    2. Semi-monthly patterns (two specific days or day + last day)

    Returns the pattern with highest consistency score. If there's a tie and only 2-3 observations,
    favors biweekly.

    Args:
        observed_paydays: List of observed payday dates

    Returns:
        Dictionary with the best pattern type and details
    """
    if len(observed_paydays) < 2:
        return {
            "predicted_pattern": None,
            "confidence": 0.0,
            "pattern_details": None,
            "pattern_type": None,
        }

    # Test biweekly pattern
    biweekly_result = analyze_biweekly_weekday_pattern(observed_paydays)
    biweekly_score = biweekly_result.get("score", 0.0)

    # Test semi-monthly patterns
    semi_result = predict_semi_monthly_regular_payday(observed_paydays)
    semi_score = semi_result.get("confidence", 0.0)

    # Compare scores
    if biweekly_score > semi_score:
        # Biweekly wins
        return {
            "predicted_pattern": "biweekly",
            "confidence": biweekly_score,
            "pattern_details": biweekly_result,
            "pattern_type": "B",
            "regular_payday": biweekly_result.get("weekday", "None") if biweekly_result.get("is_valid") else "None",
        }
    elif semi_score > biweekly_score:
        # Semi-monthly wins
        return {
            "predicted_pattern": "semi_monthly",
            "confidence": semi_score,
            "pattern_details": semi_result.get("pattern_details"),
            "pattern_type": "S",
            "regular_payday": None,  # Will be formatted by caller
        }
    else:
        # Tie - favor biweekly if 2-3 observations
        if len(observed_paydays) <= 3 and biweekly_result.get("is_valid"):
            return {
                "predicted_pattern": "biweekly",
                "confidence": biweekly_score,
                "pattern_details": biweekly_result,
                "pattern_type": "B",
                "regular_payday": biweekly_result.get("weekday", "None"),
            }
        elif semi_result.get("predicted_pattern") is not None:
            return {
                "predicted_pattern": "semi_monthly",
                "confidence": semi_score,
                "pattern_details": semi_result.get("pattern_details"),
                "pattern_type": "S",
                "regular_payday": None,
            }
        else:
            # No valid pattern found
            return {
                "predicted_pattern": None,
                "confidence": 0.0,
                "pattern_details": None,
                "pattern_type": None,
            }


def predict_monthly_regular_payday_enhanced(observed_paydays: List[datetime]) -> Dict[str, Any]:
    """Enhanced prediction with fallback patterns for end-of-month and near-specific-days

    Args:
        observed_paydays: List of observed payday dates

    Returns:
        Dictionary with prediction results, including fallback patterns
    """
    # First try the regular prediction
    primary_result = predict_monthly_regular_payday(observed_paydays)

    # If primary prediction found a strong pattern, return it
    if primary_result["predicted_pattern"] is not None:
        return primary_result

    # If no strong pattern found, try fallback patterns
    fallback_patterns = []

    # Check for end-of-month tendency
    end_of_month_result = analyze_end_of_month_tendency(observed_paydays)
    if end_of_month_result["is_valid"]:
        fallback_patterns.append(end_of_month_result)

    # Check for near-specific-days tendency
    near_days_result = analyze_near_specific_days_tendency(observed_paydays)
    if near_days_result["is_valid"]:
        fallback_patterns.append(near_days_result)

    # If we found fallback patterns, return the best one
    if fallback_patterns:
        best_fallback = max(fallback_patterns, key=lambda p: p["score"])
        # Add adjustment_direction for fallback patterns (set to None)
        best_fallback["adjustment_direction"] = "None"
        return {
            "predicted_pattern": best_fallback["pattern_type"],
            "confidence": best_fallback["score"],
            "pattern_details": best_fallback,
            "adjustment_accuracy": best_fallback["score"],
            "is_fallback_pattern": True,
            "primary_result": primary_result,
        }

    # If no patterns found at all, return the original result
    return {
        **primary_result,
        "is_fallback_pattern": False,
        "fallback_patterns_attempted": ["end_of_month_tendency", "near_specific_day_tendency"],
    }
