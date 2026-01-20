import os

import pandas as pd
from config import config
from postprocess.lending_guide.debit_date import payment_near_holiday
from postprocess.sources.helpers.source_debit_date import debit_date_analysis

sample_data_path = os.path.realpath(
    os.path.join(config.ROOT_DIR, "..", "tests", "data", "sample_income_sources_1day_before.csv")
)
modified_data_path = os.path.realpath(
    os.path.join(config.ROOT_DIR, "..", "tests", "data", "sample_income_sources_1day_before_modified.csv")
)


def test_find_debit_near_holidays():
    income_sources = pd.read_csv(sample_data_path)
    income_sources.loc[:, "historicalPayDay"] = income_sources.historicalPayDay.apply(lambda x: eval(x))
    income_sources = debit_date_analysis(income_sources, "2023-12-31")
    payment_near_holiday = income_sources[income_sources.sourceID == "I1_err_000"].iloc[0].paymentNearHoliday
    next_pay_date = income_sources[income_sources.sourceID == "I1_err_000"].iloc[0].nextPayDay
    next_payday_on_holiday = income_sources[income_sources.sourceID == "I1_err_000"].iloc[0].nextPayDayOnHoliday

    # assert payment_near_holiday == "1 business day(s) after holiday"
    assert payment_near_holiday == "A"
    assert pd.to_datetime(next_pay_date) == pd.to_datetime("2023-07-11")
    assert next_payday_on_holiday == "False"


def test_find_debit_near_holidays_modified():
    income_sources = pd.read_csv(modified_data_path)
    income_sources.loc[:, "historicalPayDay"] = income_sources.historicalPayDay.apply(lambda x: eval(x))
    income_sources = debit_date_analysis(income_sources, "2023-12-31")
    payment_near_holiday = income_sources[income_sources.sourceID == "I1_err_000"].iloc[0].paymentNearHoliday
    next_pay_date = income_sources[income_sources.sourceID == "I1_err_000"].iloc[0].nextPayDay
    next_payday_on_holiday = income_sources[income_sources.sourceID == "I1_err_000"].iloc[0].nextPayDayOnHoliday
    # assert payment_near_holiday == "1 business day(s) before holiday"
    assert payment_near_holiday == "B"
    # this is modified because the function will detect whether the payday is on holiday and move it if it is
    assert pd.to_datetime(next_pay_date) == pd.to_datetime("2023-07-03")
    assert next_payday_on_holiday == "True"


def test_lending_guide_holidays():
    income_sources = pd.read_csv(modified_data_path)
    income_sources.loc[:, "historicalPayDay"] = income_sources.historicalPayDay.apply(lambda x: eval(x))
    income_sources = debit_date_analysis(income_sources, "2023-12-31")
    payment_behavior_near_holiday, next_payment_on_holiday = payment_near_holiday(income_sources)
    # assert payment_behavior_near_holiday == "1 business day(s) before holiday"
    assert payment_behavior_near_holiday == "B"
    assert next_payment_on_holiday == "True"


# test_find_debit_near_holidays_modified()
