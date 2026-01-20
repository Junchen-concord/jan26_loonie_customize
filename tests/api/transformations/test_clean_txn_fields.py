import numpy as np

from api.transformations.transform_v2_output import clean_txn_fields


def test_clean_txn_fields():
    transactions = [
        {
            "accountGuid": "KwO4y1ZoL8HDVZJV7763fBZ9XbJbm8CnpQvrz",
            "transGuid": "12345",
            "sourceName": "Example Source",
            "description": "Test transaction",
            "date": "2023-07-03 00:00:00",
            "amount": 190.12,
            "transCategory": 2,
            "type": "DEBIT",
            "ibvCategory": "Other",
            "sourceID": "Other",
        },
        {  # Should be removed (accountGuid is None)
            "accountGuid": None,
            "transGuid": "67890",
            "sourceName": "Another Source",
            "description": "Valid Description",
            "date": "2023-07-04 00:00:00",
            "amount": 50.00,
            "transCategory": 3,
            "type": "CREDIT",
            "ibvCategory": "Income",
            "sourceID": "Other",
        },
        {  # Should be removed (accountGuid is NaN)
            "accountGuid": np.nan,
            "transGuid": "55555",
            "sourceName": "Yet Another Source",
            "description": "Another Valid Transaction",
            "date": "2023-07-06 00:00:00",
            "amount": 75.00,
            "transCategory": 4,
            "type": "DEBIT",
            "ibvCategory": "Savings",
            "sourceID": "Other",
        },
        {
            "accountGuid": "789",
            "transGuid": "54321",
            "sourceName": "Valid Source",
            "description": None,
            "date": "2023-07-05 00:00:00",
            "amount": 75.50,
            "transCategory": 1,
            "type": "DEBIT",
            "ibvCategory": "Expense",
            "sourceID": "Other",
        },
    ]

    expected_output = [
        {
            "accountGuid": "KwO4y1ZoL8HDVZJV7763fBZ9XbJbm8CnpQvrz",
            "transGuid": "12345",
            "sourceName": "Example Source",
            "description": "Test transaction",
            "date": "2023-07-03 00:00:00",
            "amount": 190.12,
            "incomeType": 2,
            "type": "DEBIT",
            "ibvCategory": "Other",
            "sourceID": "Other",
        },
        {
            "accountGuid": "789",
            "transGuid": "54321",
            "sourceName": "Valid Source",
            "description": None,
            "date": "2023-07-05 00:00:00",
            "amount": 75.50,
            "incomeType": 1,
            "type": "DEBIT",
            "ibvCategory": "Expense",
            "sourceID": "Other",
        },
    ]

    result = clean_txn_fields(transactions)

    assert result == expected_output, f"Expected {expected_output}, but got {result}"
