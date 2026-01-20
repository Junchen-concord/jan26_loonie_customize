import logging
from logging.config import dictConfig

from dotenv import load_dotenv

#############################
# Config for API
#############################

# Logger

load_dotenv()

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] [%(levelname)s | %(module)s] %(message)s",
                "datefmt": "%B %d, %Y %H:%M:%S %Z",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "INFO",
            },
            "warn_console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "WARNING",
            },
            "error_console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "ERROR",
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "warn_console", "error_console"],
        },
    }
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# top-level fields
SUMMARY_INFO = "summaryInfo"
INCOME_SOURCES = "incomeSources"
LOAN_SOURCES = "loanSources"
OVERDRAFT_INCIDENTS = "overdraftIncidents"
CASHFLOW = "cashFlow"
REDZONE_BEHAVIOR = "redZoneBehavior"
ALERTS_AND_INSIGHTS = "alertsAndInsights"
MAJOR_INCOME_SOURCE = "majorIncomeSource"
CREDIT_TRANS = "creditTrans"
DEBIT_TRANS = "debitTrans"
ADDITIONAL_INFO = "additionalInfo"
LENDING_GUIDE = "lendingGuide"
ACCOUNTS = "accounts"
SCORES = "scores"
MODEL_VERSION = "modelVersion"


ACCOUNT_GUID = "accountGuid"

# summaryInfo
CARD = "card"
INCOME_SOURCE_ALL_TIME = "incomeSourceAllTime"
INCOME_SOURCE_THREE_MONTH = "incomeSourceThreeMonth"
INCOME_SOURCE_SIX_MONTH = "incomeSourceSixMonth"
MONTHLY_INCOME_ALL_TIME = "allTimeMonthlyIncome"
MONTHLY_INCOME_THREE_MONTH = "threeMonthMonthlyIncome"
MONTHLY_INCOME_SIX_MONTH = "sixMonthMonthlyIncome"
OVERDRAFT_ALL_TIME = "odAll"
OVERDRAFT_THREE_MONTH = "od3m"
OVERDRAFT_SIX_MONTH = "od6m"
INDEX = "index"
AVERAGE_MONTHLY_BALANCE_ALL_TIME = "averageMonthlyBalanceAll"
AVERAGE_MONTHLY_BALANCE_THREE_MONTH = "averageMonthlyBalance3Month"
AVERAGE_MONTHLY_BALANCE_SIX_MONTH = "averageMonthlyBalance6Month"
ACCOUNT_TYPE = "accountType"
CURRENT_BALANCE = "currentBalance"
CURRENT_BALANCE_DATE = "currentBalanceDate"
AS_OF_DATE = "asOfDate"
INCOME_HISTORY_ALL_TIME = "incomeHistoryAllTime"
INCOME_HISTORY_THREE_MONTH = "incomeHistoryThreeMonth"
INCOME_HISTORY_SIX_MONTH = "incomeHistorySixMonth"
LOAN_PAYMENT_ALL_TIME = "loanPmtAllTime"
LOAN_PAYMENT_THREE_MONTH = "loanPmtThreeMonth"
LOAN_PAYMENT_SIX_MONTH = "loanPmtSixMonth"
LOAN_IDENTIFIED_ALL_TIME = "loanIdentifiedAllTime"
LOAN_IDENTIFIED_THREE_MONTH = "loanIdentifiedThreeMonth"
LOAN_IDENTIFIED_SIX_MONTH = "loanIdentifiedSixMonth"
CASHFLOW_ALL_TIME = "cashflowAllTime"
CASHFLOW_THREE_MONTH = "cashflowThreeMonth"
CASHFLOW_SIX_MONTH = "cashflowSixMonth"
INFLOW_EXCLUDING_LOANS = "inflowExcludingLoans"
RECURRING_MONTHLY_INCOME = "recurringMonthlyIncome"
ACTIVE_MONTHLY_INCOME = "activeMonthlyIncome"
RUN_ERROR = "runError"
RUN_MESSAGE = "runMsg"

# income/loan sources
SOURCE_ID = "sourceID"
SOURCE_NAME = "sourceName"
SOURCE_TYPE = "sourceType"
SOURCE_CHANNEL = "sourceChannel"
NUM_OF_PAY = "numOfPay"
NUM_OF_PAY_MONTHLY = "numOfPayMonthly"
FREQUENCY = "frequency"
PER_PAY_CHECK = "perPayCheck"
MONTHLY_INCOME = "monthlyIncome"
STABLE_MONTHLY_INCOME = "stableMonthlyIncome"
REGULAR_PAY_DAY = "regularPayDay"
HISTORICAL_PAY_DAY = "historicalPayDay"
MISSING_PAY_DAY = "missingPayDay"
SAME_DAY_FREQUENCY = "sameDayFreq"
LAST_PAY_DAY = "lastPayDay"
INCOME_TYPE = "incomeType"
DEPOSIT_METHOD = "depositMethod"
ACTIVE_SCORE = "activeScore"
RECURRING_SCORE = "recurringScore"
STABILITY_SCORE = "stabilityScore"
ERROR_CODE = "errorCode"
ERROR_MESSAGE = "errorMessage"
IS_DOMINANT = "isDominant"
NEXT_PAY_DAY = "nextPayDay"
PAYMENT_NEAR_HOLIDAY = "paymentNearHoliday"
NEXT_PAY_DAY_ON_HOLIDAY = "nextPayDayOnHoliday"
NUM_OF_ORIGINATION = "numOfOrigination"
ORIGINATION_AMOUNT = "originationAmount"
PAYMENT_AMOUNT = "paymentAmount"
INTEREST_RATE = "interestRate"
LOAN_TYPE = "loanType"
DEBIT_TYPE = "debitType"

DATE = "date"
AMOUNT = "amount"
DESCRIPTION = "description"

RISK_BEHAVIOR = "riskBehavior"
RISK_SCORE = "riskScore"

TOTAL_CREDITS = "totalCredits"
TOTAL_DEBITS = "totalDebits"
NET_CASH_FLOW = "netCashFlow"
SPENDING = "spending"

ALERTS = "alerts"
INSIGHTS = "insights"
GREEN_ZONE_REASONS = "greenZoneReasons"
ASSESSMENT_REASONS = "assessmentReasons"

TRANS_GUID = "transGuid"
TRANS_CATEGORY = "transCategory"
CLUSTER_LABEL = "clusterLabel"
TYPE = "type"
FROM_MODEL = "fromModel"
WHO = "who"
HOW = "how"
WHAT = "what"
DAY_OF_WEEK = "dayOfWeek"
IBV_CATEGORY = "ibvCategory"
WHO_CAT = "whoCat"

REDZONE_BEHAVIOR_CUSTOMER = "redZoneBehaviorCustomer"
ALERTS_AND_INSIGHTS_CUSTOMER = "alertsAndInsightsCustomer"
RECOMMENDED_BANK_ACCOUNT = "recommendedBankAccount"

MIN_LOAN_AMOUNT = "minLoanAmount"
MAX_LOAN_AMOUNT = "maxLoanAmount"
MIN_DEBIT_AMOUNT = "minDebitAmount"
MAX_DEBIT_AMOUNT = "maxDebitAmount"
CUSTOMER_INCOME_TYPE = "customerIncomeType"
DEBIT_FREQUENCY = "debitFrequency"
DEBIT_DATE = "debitDate"
REPEAT_OPPORTUNITY = "repeatOpportunity"
NEXT_PAYMENT_ON_HOLIDAY = "nextPaymentOnHoliday"

IS_BAD = "isBad"
LOAN_PAID_OFF = "loanPaidOff"
RED_ZONE = "redZone"
REPEAT = "repeat"

ACCOUNT_LEVEL = "accountLevel"
CUSTOMER_LEVEL = "customerLevel"
MODEL_REASONS = "modelReasons"
MODEL_SCORE = "modelScore"

EXPLANATION = "explanation"
FEATURE = "feature"
FEATURE_CONTRIBUTION = "feature_contribution"
FEATURE_VALUES = "feature_values"
IMPACT = "impact"
IMPORTANCE_LEVEL = "importance_level"
IS_BAD_SCORE = "isBadScore"
REPEAT_SCORE = "repeatScore"
TOTAL_LOAN_PAID_OFF_SCORE = "totalLoanPaidOffScore"
