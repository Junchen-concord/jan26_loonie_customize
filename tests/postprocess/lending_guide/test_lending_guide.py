import pandas as pd
import pytest

from postprocess.lending_guide import get_lending_guide

redzone_behavior_data_no = {
    "accountGuid": ["KwO4y1ZoL8HDVZJV7763fBZ9XbJbm8CnpQvrz"],
    "riskBehavior": ["NO"],
    "riskScore": [96],
}

redzone_behavior_data_yes = {
    "accountGuid": ["KwO4y1ZoL8HDVZJV7763fBZ9XbJbm8CnpQvrz"],
    "riskBehavior": ["YES"],
    "riskScore": [46],
}

income_sources_data = {
    "activeScore": [3, 3, 3, 0, 0],
    "errorCode": [000, 000, 205, 205, 205],
    "incomeType": ["Payroll", "Transfer", "Transfer", "Transfer", "Deposit"],
    "frequency": ["S", "I", "I", "I", "I"],
    "monthlyIncome": [937.48, 606.95, 145, 145, 145],
    "regularPayDay": ["Friday", "None", "None", "None", "None"],
    "sourceName": [
        "CAPGEMINI DES:REG.SALARY ID:CGA50481295 INDN:W...",
        "Balance Transfer",
        "Venmo",
        "Other Transfer",
        "Mobile Deposit",
    ],
    "paymentNearHoliday": "1 business day(s) before holiday",
    "nextPayDay": "2023-07-04",
    "nextPayDayOnHoliday": True,
}

scores_data = {
    "repeat": {
        "customerLevel": {"modelScore": [{"repeatScore": 200}]},
        "accountLevel": {"modelScore": [{"accountGuid": "KwO4y1ZoL8HDVZJV7763fBZ9XbJbm8CnpQvrz", "repeatScore": 200}]},
    }
}


@pytest.fixture
def income_sources():
    return pd.DataFrame(income_sources_data)


@pytest.fixture
def redzone_behavior_no():
    return pd.DataFrame(redzone_behavior_data_no)


@pytest.fixture
def redzone_behavior_yes():
    return pd.DataFrame(redzone_behavior_data_yes)


@pytest.fixture
def scores():
    return scores_data


def test_get_lending_guide_no_redzone(redzone_behavior_no, income_sources, scores):
    lending_guide = get_lending_guide(redzone_behavior_no, income_sources, scores)
    assert lending_guide["minLoanAmount"] == 300.0
    assert lending_guide["maxLoanAmount"] == 380
    assert lending_guide["minDebitAmount"] == 90.0
    assert lending_guide["maxDebitAmount"] == 120
    assert lending_guide["customerIncomeType"] == "Payroll"
    assert lending_guide["debitFrequency"] == "S"
    assert lending_guide["debitDate"] == "Friday"
    assert lending_guide["paymentNearHoliday"] == "1 business day(s) before holiday"
    assert lending_guide["repeatOpportunity"] == "Medium"


def test_get_lending_guide_yes_redzone(redzone_behavior_yes, income_sources, scores):
    income_sources = income_sources[income_sources["incomeType"] != "Payroll"]
    lending_guide = get_lending_guide(redzone_behavior_yes, income_sources, scores)
    assert lending_guide["minLoanAmount"] == 300.0
    assert lending_guide["maxLoanAmount"] == 300
    assert lending_guide["minDebitAmount"] == 90.0
    assert lending_guide["maxDebitAmount"] == 90.0
    assert lending_guide["customerIncomeType"] == "irregular"
    assert lending_guide["debitFrequency"] == "W"
    assert lending_guide["debitDate"] == "ask customer"
    assert lending_guide["paymentNearHoliday"] == "1 business day(s) before holiday"
    assert lending_guide["repeatOpportunity"] == "Medium"
