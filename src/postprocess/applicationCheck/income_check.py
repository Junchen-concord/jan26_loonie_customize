from postprocess.lending_guide.debit_date import filter_income


def income_feature_check(application_info, income_sources):
    # app_employer_name = application_info["employer_name"] #TODO list for future checks
    app_payroll_frequency = application_info["payroll_frequency"]
    app_monthly_income = application_info["monthly_income"]
    app_regular_payday = application_info["regular_payday"]
    app_requested_amount = application_info["requested_amount"]

    filtered_income_sources = filter_income(income_sources)

    (
        app_frequency_match,
        app_frequency_match_BS,
        IBV_suggests_inconsistent,
        IBV_suggests_biweekly,
        IBV_suggests_weekly,
        IBV_suggests_semi_monthly,
        IBV_suggests_monthly,
        IBV_suggests_BS,
        app_payday_match,
    ) = check_income_frequency(filtered_income_sources, app_payroll_frequency, app_regular_payday)

    IBV_monthly_income = filtered_income_sources.monthlyIncome.sum()
    reported_income_minus_active_income = app_monthly_income - IBV_monthly_income
    if IBV_monthly_income > 0:
        requested_amount_ratio = min(app_requested_amount / IBV_monthly_income, 5)
    else:
        requested_amount_ratio = 5

    return {
        "appFrequencyMatch": app_frequency_match,
        "appFrequencyMatchBS": app_frequency_match_BS,
        "IBVSuggestsInconsistent": IBV_suggests_inconsistent,
        "IBVSuggestsBiweekly": IBV_suggests_biweekly,
        "IBVSuggestsWeekly": IBV_suggests_weekly,
        "IBVSuggestsSemiMonthly": IBV_suggests_semi_monthly,
        "IBVSuggestsMonthly": IBV_suggests_monthly,
        "IBVSuggestsBS": IBV_suggests_BS,
        "appPaydayMatch": app_payday_match,
        "IBVMonthlyIncome": IBV_monthly_income,
        "reportedIncomeMinusActiveIncome": reported_income_minus_active_income,
        "requestedAmountRatio": requested_amount_ratio,
    }


def check_income_frequency(income_sources, app_frequency, app_payday):
    # output schema:
    # 1. Whether app frequency matches IBV found frequency,
    # 2. Whether app frequency matches IBV found frequency (if B and S are considered the same),
    # 3. Whether IBV suggests inconsistent income,
    # 4. Whether IBV suggests biweekly income,
    # 5. Whether IBV suggests weekly income,
    # 6. Whether IBV suggests semi-monthly income,
    # 7. Whether IBV suggests monthly income,
    # 8. Whether IBV suggests B/S income,
    # 9. Whether app payday matches IBV found payday
    if income_sources.shape[0] == 0:
        return 0, 0, 1, 0, 0, 0, 0, 0, 0
    unique_frequencies = list(income_sources.frequency.unique())
    unique_paydays = list(income_sources.regularPayDay.unique())
    unique_paydays = [x.lower() for x in unique_paydays if x is not None]

    app_payday = parse_app_payday(app_frequency, app_payday)

    if app_payday in unique_paydays:
        app_payday_match = 1
    else:
        app_payday_match = 0
    if app_frequency in unique_frequencies:
        app_frequency_match = 1
    else:
        app_frequency_match = 0

    if app_frequency_match == 1:
        app_frequency_match_BS = 1
    elif app_frequency in ["B", "S"] and ("B" in unique_frequencies or "S" in unique_frequencies):
        app_frequency_match_BS = 1
    else:
        app_frequency_match_BS = 0

    IBV_suggests_biweekly = "B" in unique_frequencies
    IBV_suggests_weekly = "W" in unique_frequencies
    IBV_suggests_semi_monthly = "S" in unique_frequencies
    IBV_suggests_monthly = "M" in unique_frequencies
    IBV_suggests_BS = "B" in unique_frequencies or "S" in unique_frequencies

    return (
        app_frequency_match,
        app_frequency_match_BS,
        0,
        IBV_suggests_biweekly,
        IBV_suggests_weekly,
        IBV_suggests_semi_monthly,
        IBV_suggests_monthly,
        IBV_suggests_BS,
        app_payday_match,
    )


def parse_app_payday(app_frequency, app_payday):
    try:
        how_paid = app_payday.get("howPaid", None)
        payday1 = app_payday.get("payDay1", None)
        payday2 = app_payday.get("payDay2", None)
        payweek1 = app_payday.get("payWeek1", None)
        payweek2 = app_payday.get("payWeek2", None)

        if app_frequency == "B" or app_frequency == "W":
            if how_paid != "Specific Weekday":
                return "Error Processing Payday"
            else:
                return payday1.lower()

        if app_frequency == "M":
            if how_paid == "Specific Week and Day":
                payweek1 = parse_payweek(payweek1)
                return f"{payday1} in Week {payweek1}".lower()
            elif how_paid == "Specific Day":
                return f"{payday1}".lower()
            else:
                return "Error Processing Payday"

        if app_frequency == "S":
            if how_paid == "Specific Day":
                if payday2 is not None:
                    return f"{payday1},{payday2}".lower()
                else:
                    return "Error Processing Payday"
            elif how_paid == "Specific Week and Day":
                payweek1 = parse_payweek(payweek1)
                payweek2 = parse_payweek(payweek2)
                if payday2 is not None:
                    return (
                        f"{payday1} in Week {payweek1},{payday2} in Week {payweek2}".lower()
                    )  # this is not used for now
                else:
                    return "Error Processing Payday"
            else:
                return "Error Processing Payday"
        else:
            return "Error Processing Payday"
    except Exception:
        return "Error Processing Payday"


def parse_payweek(payweek):
    mapping = {"first": "1", "second": "2", "third": "3", "fourth": "4", "last": "last"}

    return mapping.get(payweek.lower(), None)
