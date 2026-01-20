from datetime import datetime

import pandas as pd
from data import PostProcessTestData

from postprocess.sources.benefit_source import BenefitSource
from postprocess.sources.gig_source import GigSource
from postprocess.sources.income_source import IncomeSource
from postprocess.sources.transfer_source import TransferSource

expected_gig_source_dict = {
    "AMpRdoAVarH4VZbV55XDHyMxLkEknYfY76BK5": {
        "accountGuid": "AMpRdoAVarH4VZbV55XDHyMxLkEknYfY76BK5",
        "sourceID": "None",
        "sourceName": "None",
        "sourceType": "None",
        "sourceChannel": "None",
        "numOfPay": 0,
        "numOfPayMonthly": 0,
        "frequency": "None",
        "perPayCheck": 0,
        "monthlyIncome": 0,
        "regularPayDay": "None",
        "historicalPayDay": [],
        "missingPayDay": [],
        "sameDayFreq": 0,
        "lastPayDay": "None",
        "incomeType": "None",
        "depositMethod": "None",
        "errorCode": 103,
        "errorMessage": "Gig income not found",
    },
    "KwO4y1ZoL8HDVZJV7763fBZ9XbJbm8CnpQvrz": {
        "accountGuid": "KwO4y1ZoL8HDVZJV7763fBZ9XbJbm8CnpQvrz",
        "sourceID": "None",
        "sourceName": "None",
        "sourceType": "None",
        "sourceChannel": "None",
        "numOfPay": 0,
        "numOfPayMonthly": 0,
        "frequency": "None",
        "perPayCheck": 0,
        "monthlyIncome": 0,
        "regularPayDay": "None",
        "historicalPayDay": [],
        "missingPayDay": [],
        "sameDayFreq": 0,
        "lastPayDay": "None",
        "incomeType": "None",
        "depositMethod": "None",
        "errorCode": 103,
        "errorMessage": "Gig income not found",
    },
    "kPvjdQ8XK6hD3RE311j8fp7Mg9Z9R6F6qRDQd": {
        "accountGuid": "kPvjdQ8XK6hD3RE311j8fp7Mg9Z9R6F6qRDQd",
        "sourceID": "None",
        "sourceName": "None",
        "sourceType": "None",
        "sourceChannel": "None",
        "numOfPay": 0,
        "numOfPayMonthly": 0,
        "frequency": "None",
        "perPayCheck": 0,
        "monthlyIncome": 0,
        "regularPayDay": "None",
        "historicalPayDay": [],
        "missingPayDay": [],
        "sameDayFreq": 0,
        "lastPayDay": "None",
        "incomeType": "None",
        "depositMethod": "None",
        "errorCode": 103,
        "errorMessage": "Gig income not found",
    },
    "yx3EvQLkOjhPZD7ZKKpytynr9dMdOJfr4OomM": {
        "accountGuid": "yx3EvQLkOjhPZD7ZKKpytynr9dMdOJfr4OomM",
        "sourceID": "None",
        "sourceName": "None",
        "sourceType": "None",
        "sourceChannel": "None",
        "numOfPay": 0,
        "numOfPayMonthly": 0,
        "frequency": "None",
        "perPayCheck": 0,
        "monthlyIncome": 0,
        "regularPayDay": "None",
        "historicalPayDay": [],
        "missingPayDay": [],
        "sameDayFreq": 0,
        "lastPayDay": "None",
        "incomeType": "None",
        "depositMethod": "None",
        "errorCode": 103,
        "errorMessage": "Gig income not found",
    },
}
expected_income_source_trans_columns = [
    "accountGuid",
    "transGUID",
    "sourceName",
    "description",
    "date",
    "amount",
    "transCategory",
    "cluster_label",
    "type",
    "fromModel",
    "WHO",
    "HOW",
    "WHAT",
    "whoCat",
    "dayOfWeek",
    "sourceID",
    "subcategory",
]


def test_categorize_income_source():
    df = PostProcessTestData().arg_for_categorize_income
    as_of_date = pd.to_datetime(datetime(2023, 9, 15))
    _, income_source_trans, sourceID = IncomeSource.categorize_income_source(df, as_of_date, 0)
    _, income_source_trans, sourceID = TransferSource.categorize_income_source(
        df, income_source_trans, as_of_date, sourceID
    )
    _, income_source_trans, sourceID = BenefitSource.categorize_income_source(
        df, income_source_trans, as_of_date, sourceID
    )
    gig_source_dict, income_source_trans, sourceID = GigSource.categorize_income_source(
        df, income_source_trans, as_of_date, sourceID
    )
    # Removing the exact match between output dictionary because of the rapid changing of output format,
    # to check specific fields, use test_QA_problems.py
    # assert gig_source_dict == expected_gig_source_dict
    assert len(income_source_trans) == 184
    assert len(income_source_trans.columns) == 17
    assert income_source_trans.columns.to_list() == expected_income_source_trans_columns
    assert sourceID == 3
