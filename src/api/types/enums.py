from enum import Enum

from api.config.config import (
    ACCOUNTS,
    ADDITIONAL_INFO,
    CASHFLOW,
    CREDIT_TRANS,
    DEBIT_TRANS,
    INCOME_SOURCES,
    LENDING_GUIDE,
    LOAN_SOURCES,
    MAJOR_INCOME_SOURCE,
    MODEL_VERSION,
    OVERDRAFT_INCIDENTS,
    SCORES,
    SUMMARY_INFO,
)


class IAResponseFields(Enum):
    summaryInfo = SUMMARY_INFO
    incomeSources = INCOME_SOURCES
    loanSources = LOAN_SOURCES
    overdraftIncidents = OVERDRAFT_INCIDENTS
    cashFlow = CASHFLOW
    majorIncomeSource = MAJOR_INCOME_SOURCE
    creditTrans = CREDIT_TRANS
    debitTrans = DEBIT_TRANS
    additionalInfo = ADDITIONAL_INFO
    lendingGuide = LENDING_GUIDE
    scores = SCORES
    accounts = ACCOUNTS
    modelVersion = MODEL_VERSION
