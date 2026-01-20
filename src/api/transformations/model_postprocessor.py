from typing import List

from api.config.config import (
    ACCOUNT_GUID,
    ACCOUNT_LEVEL,
    ACCOUNT_TYPE,
    ACTIVE_MONTHLY_INCOME,
    ACTIVE_SCORE,
    ALERTS,
    ALERTS_AND_INSIGHTS_CUSTOMER,
    AMOUNT,
    AS_OF_DATE,
    ASSESSMENT_REASONS,
    AVERAGE_MONTHLY_BALANCE_ALL_TIME,
    AVERAGE_MONTHLY_BALANCE_SIX_MONTH,
    AVERAGE_MONTHLY_BALANCE_THREE_MONTH,
    CARD,
    CASHFLOW_ALL_TIME,
    CASHFLOW_SIX_MONTH,
    CASHFLOW_THREE_MONTH,
    CLUSTER_LABEL,
    CURRENT_BALANCE,
    CURRENT_BALANCE_DATE,
    CUSTOMER_INCOME_TYPE,
    CUSTOMER_LEVEL,
    DATE,
    DAY_OF_WEEK,
    DEBIT_DATE,
    DEBIT_FREQUENCY,
    DEBIT_TYPE,
    DEPOSIT_METHOD,
    DESCRIPTION,
    ERROR_CODE,
    ERROR_MESSAGE,
    EXPLANATION,
    FEATURE,
    FEATURE_CONTRIBUTION,
    FEATURE_VALUES,
    FREQUENCY,
    FROM_MODEL,
    HISTORICAL_PAY_DAY,
    HOW,
    IBV_CATEGORY,
    IMPACT,
    IMPORTANCE_LEVEL,
    INCOME_HISTORY_ALL_TIME,
    INCOME_HISTORY_SIX_MONTH,
    INCOME_HISTORY_THREE_MONTH,
    INCOME_SOURCE_ALL_TIME,
    INCOME_SOURCE_SIX_MONTH,
    INCOME_SOURCE_THREE_MONTH,
    INCOME_TYPE,
    INDEX,
    INFLOW_EXCLUDING_LOANS,
    INSIGHTS,
    INTEREST_RATE,
    IS_BAD,
    IS_BAD_SCORE,
    IS_DOMINANT,
    LAST_PAY_DAY,
    LENDING_GUIDE,
    LOAN_IDENTIFIED_ALL_TIME,
    LOAN_IDENTIFIED_SIX_MONTH,
    LOAN_IDENTIFIED_THREE_MONTH,
    LOAN_PAID_OFF,
    LOAN_PAYMENT_ALL_TIME,
    LOAN_PAYMENT_SIX_MONTH,
    LOAN_PAYMENT_THREE_MONTH,
    LOAN_TYPE,
    MAX_DEBIT_AMOUNT,
    MAX_LOAN_AMOUNT,
    MIN_DEBIT_AMOUNT,
    MIN_LOAN_AMOUNT,
    MISSING_PAY_DAY,
    MODEL_REASONS,
    MODEL_SCORE,
    MONTHLY_INCOME,
    MONTHLY_INCOME_ALL_TIME,
    MONTHLY_INCOME_SIX_MONTH,
    MONTHLY_INCOME_THREE_MONTH,
    NET_CASH_FLOW,
    NEXT_PAY_DAY,
    NEXT_PAY_DAY_ON_HOLIDAY,
    NEXT_PAYMENT_ON_HOLIDAY,
    NUM_OF_ORIGINATION,
    NUM_OF_PAY,
    NUM_OF_PAY_MONTHLY,
    ORIGINATION_AMOUNT,
    OVERDRAFT_ALL_TIME,
    OVERDRAFT_SIX_MONTH,
    OVERDRAFT_THREE_MONTH,
    PAYMENT_AMOUNT,
    PAYMENT_NEAR_HOLIDAY,
    PER_PAY_CHECK,
    RECOMMENDED_BANK_ACCOUNT,
    RECURRING_MONTHLY_INCOME,
    RECURRING_SCORE,
    RED_ZONE,
    REDZONE_BEHAVIOR_CUSTOMER,
    REGULAR_PAY_DAY,
    REPEAT,
    REPEAT_OPPORTUNITY,
    REPEAT_SCORE,
    RISK_BEHAVIOR,
    RISK_SCORE,
    RUN_ERROR,
    RUN_MESSAGE,
    SAME_DAY_FREQUENCY,
    SOURCE_CHANNEL,
    SOURCE_ID,
    SOURCE_NAME,
    SOURCE_TYPE,
    SPENDING,
    STABILITY_SCORE,
    STABLE_MONTHLY_INCOME,
    TOTAL_CREDITS,
    TOTAL_DEBITS,
    TOTAL_LOAN_PAID_OFF_SCORE,
    TRANS_CATEGORY,
    TRANS_GUID,
    TYPE,
    WHAT,
    WHO,
    WHO_CAT,
)
from api.types.enums import IAResponseFields


class ModelPostProcessor:
    def __init__(self, model_output) -> None:
        self.model_output = model_output

    def mask_output(self):
        summary_info = self.__get_summary_info()
        income_sources = self.__get_income_sources()
        loan_sources = self.__get_loan_sources()
        overdraft_incidents = self.__get_overdraft_incidents()
        cashflow = self.__get_cashflow()
        major_income_source = self.__get_major_income_source()
        credit_transactions = self.__get_credit_transactions()
        debit_transactions = self.__get_debit_transactions()
        additional_info = self.__get_additional_info()
        lending_guide = self.__get_lending_guide()
        scores = self.__get_scores()
        accounts = self.__get_accounts()

        model_version = self.__get_model_version()

        return {
            IAResponseFields.summaryInfo.value: summary_info,
            IAResponseFields.incomeSources.value: income_sources,
            IAResponseFields.loanSources.value: loan_sources,
            IAResponseFields.overdraftIncidents.value: overdraft_incidents,
            IAResponseFields.cashFlow.value: cashflow,
            IAResponseFields.majorIncomeSource.value: major_income_source,
            IAResponseFields.creditTrans.value: credit_transactions,
            IAResponseFields.debitTrans.value: debit_transactions,
            IAResponseFields.additionalInfo.value: additional_info,
            IAResponseFields.lendingGuide.value: lending_guide,
            IAResponseFields.scores.value: scores,
            IAResponseFields.accounts.value: accounts,
            IAResponseFields.modelVersion.value: model_version,
        }

    def cherry_pick_output(self, cherries: List[IAResponseFields]):
        out = {}
        cherry_method_mapping = {
            IAResponseFields.summaryInfo: self.__get_summary_info,
            IAResponseFields.incomeSources: self.__get_income_sources,
            IAResponseFields.loanSources: self.__get_loan_sources,
            IAResponseFields.overdraftIncidents: self.__get_overdraft_incidents,
            IAResponseFields.cashFlow: self.__get_cashflow,
            IAResponseFields.majorIncomeSource: self.__get_major_income_source,
            IAResponseFields.creditTrans: self.__get_credit_transactions,
            IAResponseFields.debitTrans: self.__get_debit_transactions,
            IAResponseFields.additionalInfo: self.__get_additional_info,
            IAResponseFields.lendingGuide: self.__get_lending_guide,
            IAResponseFields.scores: self.__get_scores,
            IAResponseFields.accounts: self.__get_accounts,
            IAResponseFields.modelVersion: self.__get_model_version,
        }

        for cherry in cherries:
            get_cherry = cherry_method_mapping.get(cherry)
            if get_cherry:
                out[cherry.value] = get_cherry()

        return out

    def __get_summary_info(self):
        if IAResponseFields.summaryInfo.value not in self.model_output or not isinstance(
            self.model_output[IAResponseFields.summaryInfo.value], list
        ):
            return []
        return [
            {
                ACCOUNT_GUID: source.get(ACCOUNT_GUID),
                ACCOUNT_TYPE: source.get(ACCOUNT_TYPE),
                ACTIVE_MONTHLY_INCOME: source.get(ACTIVE_MONTHLY_INCOME),
                ALERTS: source.get(ALERTS),
                MONTHLY_INCOME_ALL_TIME: source.get(MONTHLY_INCOME_ALL_TIME),
                AS_OF_DATE: source.get(AS_OF_DATE),
                ASSESSMENT_REASONS: source.get(ASSESSMENT_REASONS),
                AVERAGE_MONTHLY_BALANCE_ALL_TIME: source.get(AVERAGE_MONTHLY_BALANCE_ALL_TIME),
                AVERAGE_MONTHLY_BALANCE_THREE_MONTH: source.get(AVERAGE_MONTHLY_BALANCE_THREE_MONTH),
                AVERAGE_MONTHLY_BALANCE_SIX_MONTH: source.get(AVERAGE_MONTHLY_BALANCE_SIX_MONTH),
                CARD: source.get(CARD),
                CASHFLOW_ALL_TIME: source.get(CASHFLOW_ALL_TIME),
                CASHFLOW_THREE_MONTH: source.get(CASHFLOW_THREE_MONTH),
                CASHFLOW_SIX_MONTH: source.get(CASHFLOW_SIX_MONTH),
                CURRENT_BALANCE: source.get(CURRENT_BALANCE),
                CURRENT_BALANCE_DATE: source.get(CURRENT_BALANCE_DATE),
                INCOME_HISTORY_ALL_TIME: source.get(INCOME_HISTORY_ALL_TIME),
                INCOME_HISTORY_THREE_MONTH: source.get(INCOME_HISTORY_THREE_MONTH),
                INCOME_HISTORY_SIX_MONTH: source.get(INCOME_HISTORY_SIX_MONTH),
                INCOME_SOURCE_ALL_TIME: source.get(INCOME_SOURCE_ALL_TIME),
                INCOME_SOURCE_THREE_MONTH: source.get(INCOME_SOURCE_THREE_MONTH),
                INCOME_SOURCE_SIX_MONTH: source.get(INCOME_SOURCE_SIX_MONTH),
                INDEX: source.get(INDEX),
                INFLOW_EXCLUDING_LOANS: source.get(INFLOW_EXCLUDING_LOANS),
                INSIGHTS: source.get(INSIGHTS),
                LOAN_IDENTIFIED_ALL_TIME: source.get(LOAN_IDENTIFIED_ALL_TIME),
                LOAN_IDENTIFIED_THREE_MONTH: source.get(LOAN_IDENTIFIED_THREE_MONTH),
                LOAN_IDENTIFIED_SIX_MONTH: source.get(LOAN_IDENTIFIED_SIX_MONTH),
                LOAN_PAYMENT_ALL_TIME: source.get(LOAN_PAYMENT_ALL_TIME),
                LOAN_PAYMENT_THREE_MONTH: source.get(LOAN_PAYMENT_THREE_MONTH),
                LOAN_PAYMENT_SIX_MONTH: source.get(LOAN_PAYMENT_SIX_MONTH),
                OVERDRAFT_ALL_TIME: source.get(OVERDRAFT_ALL_TIME),
                OVERDRAFT_THREE_MONTH: source.get(OVERDRAFT_THREE_MONTH),
                OVERDRAFT_SIX_MONTH: source.get(OVERDRAFT_SIX_MONTH),
                RECURRING_MONTHLY_INCOME: source.get(RECURRING_MONTHLY_INCOME),
                RISK_BEHAVIOR: source.get(RISK_BEHAVIOR),
                RISK_SCORE: source.get(RISK_SCORE),
                RUN_ERROR: source.get(RUN_ERROR),
                RUN_MESSAGE: source.get(RUN_MESSAGE),
                MONTHLY_INCOME_SIX_MONTH: source.get(MONTHLY_INCOME_SIX_MONTH),
                MONTHLY_INCOME_THREE_MONTH: source.get(MONTHLY_INCOME_THREE_MONTH),
            }
            for source in self.model_output[IAResponseFields.summaryInfo.value]
        ]

    def __get_income_sources(self):
        if IAResponseFields.incomeSources.value not in self.model_output or not isinstance(
            self.model_output[IAResponseFields.incomeSources.value], list
        ):
            return []
        return [
            {
                ACCOUNT_GUID: source.get(ACCOUNT_GUID),
                SOURCE_ID: source.get(SOURCE_ID),
                SOURCE_NAME: source.get(SOURCE_NAME),
                SOURCE_TYPE: source.get(SOURCE_TYPE),
                SOURCE_CHANNEL: source.get(SOURCE_CHANNEL),
                NUM_OF_PAY: source.get(NUM_OF_PAY),
                NUM_OF_PAY_MONTHLY: source.get(NUM_OF_PAY_MONTHLY),
                FREQUENCY: source.get(FREQUENCY),
                PER_PAY_CHECK: source.get(PER_PAY_CHECK),
                MONTHLY_INCOME: source.get(MONTHLY_INCOME),
                STABLE_MONTHLY_INCOME: source.get(STABLE_MONTHLY_INCOME),
                REGULAR_PAY_DAY: source.get(REGULAR_PAY_DAY),
                HISTORICAL_PAY_DAY: source.get(HISTORICAL_PAY_DAY),
                MISSING_PAY_DAY: source.get(MISSING_PAY_DAY),
                SAME_DAY_FREQUENCY: source.get(SAME_DAY_FREQUENCY),
                LAST_PAY_DAY: source.get(LAST_PAY_DAY),
                INCOME_TYPE: source.get(INCOME_TYPE),
                DEPOSIT_METHOD: source.get(DEPOSIT_METHOD),
                ACTIVE_SCORE: source.get(ACTIVE_SCORE),
                RECURRING_SCORE: source.get(RECURRING_SCORE),
                STABILITY_SCORE: source.get(STABILITY_SCORE),
                ERROR_CODE: source.get(ERROR_CODE),
                ERROR_MESSAGE: source.get(ERROR_MESSAGE),
                IS_DOMINANT: source.get(IS_DOMINANT),
                NEXT_PAY_DAY: source.get(NEXT_PAY_DAY),
                PAYMENT_NEAR_HOLIDAY: source.get(PAYMENT_NEAR_HOLIDAY),
                NEXT_PAY_DAY_ON_HOLIDAY: source.get(NEXT_PAY_DAY_ON_HOLIDAY),
            }
            for source in self.model_output[IAResponseFields.incomeSources.value]
        ]

    def __get_loan_sources(self):
        if IAResponseFields.loanSources.value not in self.model_output or not isinstance(
            self.model_output[IAResponseFields.loanSources.value], list
        ):
            return []
        return [
            {
                ACCOUNT_GUID: source.get(ACCOUNT_GUID),
                SOURCE_ID: source.get(SOURCE_ID),
                SOURCE_NAME: source.get(SOURCE_NAME),
                NUM_OF_ORIGINATION: source.get(NUM_OF_ORIGINATION),
                NUM_OF_PAY: source.get(NUM_OF_PAY),
                FREQUENCY: source.get(FREQUENCY),
                ORIGINATION_AMOUNT: source.get(ORIGINATION_AMOUNT),
                PAYMENT_AMOUNT: source.get(PAYMENT_AMOUNT),
                INTEREST_RATE: source.get(INTEREST_RATE),
                REGULAR_PAY_DAY: source.get(REGULAR_PAY_DAY),
                LAST_PAY_DAY: source.get(LAST_PAY_DAY),
                LOAN_TYPE: source.get(LOAN_TYPE),
                DEBIT_TYPE: source.get(DEBIT_TYPE),
                ERROR_CODE: source.get(ERROR_CODE),
                ERROR_MESSAGE: source.get(ERROR_MESSAGE),
            }
            for source in self.model_output[IAResponseFields.loanSources.value]
        ]

    def __get_overdraft_incidents(self):
        if IAResponseFields.overdraftIncidents.value not in self.model_output or not isinstance(
            self.model_output[IAResponseFields.overdraftIncidents.value], list
        ):
            return []
        return [
            {
                ACCOUNT_GUID: incident.get(ACCOUNT_GUID),
                DATE: incident.get(DATE),
                AMOUNT: incident.get(AMOUNT),
                DESCRIPTION: incident.get(DESCRIPTION),
            }
            for incident in self.model_output[IAResponseFields.overdraftIncidents.value]
        ]

    def __get_cashflow(self):
        if IAResponseFields.cashFlow.value not in self.model_output or not isinstance(
            self.model_output[IAResponseFields.cashFlow.value], list
        ):
            return []
        return [
            {
                ACCOUNT_GUID: source.get(ACCOUNT_GUID),
                TOTAL_CREDITS: source.get(TOTAL_CREDITS),
                TOTAL_DEBITS: source.get(TOTAL_DEBITS),
                NET_CASH_FLOW: source.get(NET_CASH_FLOW),
                SPENDING: source.get(SPENDING),
            }
            for source in self.model_output[IAResponseFields.cashFlow.value]
        ]

    def __get_major_income_source(self):
        if IAResponseFields.majorIncomeSource.value not in self.model_output or not isinstance(
            self.model_output[IAResponseFields.majorIncomeSource.value], list
        ):
            return []
        return [
            {ACCOUNT_GUID: source.get(ACCOUNT_GUID), INCOME_TYPE: source.get(INCOME_TYPE)}
            for source in self.model_output[IAResponseFields.majorIncomeSource.value]
        ]

    def __get_credit_transactions(self):
        if IAResponseFields.creditTrans.value not in self.model_output or not isinstance(
            self.model_output[IAResponseFields.creditTrans.value], list
        ):
            return []
        return [
            {
                ACCOUNT_GUID: source.get(ACCOUNT_GUID),
                TRANS_GUID: source.get(TRANS_GUID),
                SOURCE_NAME: source.get(SOURCE_NAME),
                DESCRIPTION: source.get(DESCRIPTION),
                DATE: source.get(DATE),
                AMOUNT: source.get(AMOUNT),
                TRANS_CATEGORY: source.get(TRANS_CATEGORY),
                CLUSTER_LABEL: source.get(CLUSTER_LABEL),
                TYPE: source.get(TYPE),
                FROM_MODEL: source.get(FROM_MODEL),
                WHO: source.get(WHO),
                HOW: source.get(HOW),
                WHAT: source.get(WHAT),
                DAY_OF_WEEK: source.get(DAY_OF_WEEK),
                SOURCE_ID: source.get(SOURCE_ID),
                IBV_CATEGORY: source.get(IBV_CATEGORY),
                WHO_CAT: source.get(WHO_CAT),
            }
            for source in self.model_output[IAResponseFields.creditTrans.value]
        ]

    def __get_debit_transactions(self):
        if IAResponseFields.debitTrans.value not in self.model_output or not isinstance(
            self.model_output[IAResponseFields.debitTrans.value], list
        ):
            return []
        return [
            {
                ACCOUNT_GUID: source.get(ACCOUNT_GUID),
                TRANS_GUID: source.get(TRANS_GUID),
                SOURCE_NAME: source.get(SOURCE_NAME),
                DESCRIPTION: source.get(DESCRIPTION),
                DATE: source.get(DATE),
                AMOUNT: source.get(AMOUNT),
                TRANS_CATEGORY: source.get(TRANS_CATEGORY),
                CLUSTER_LABEL: source.get(CLUSTER_LABEL),
                TYPE: source.get(TYPE),
                FROM_MODEL: source.get(FROM_MODEL),
                WHO: source.get(WHO),
                HOW: source.get(HOW),
                WHAT: source.get(WHAT),
                DAY_OF_WEEK: source.get(DAY_OF_WEEK),
                SOURCE_ID: source.get(SOURCE_ID),
                IBV_CATEGORY: source.get(IBV_CATEGORY),
                WHO_CAT: source.get(WHO_CAT),
            }
            for source in self.model_output[IAResponseFields.debitTrans.value]
        ]

    def __get_additional_info(self):
        if IAResponseFields.additionalInfo.value not in self.model_output or not isinstance(
            self.model_output[IAResponseFields.additionalInfo.value], dict
        ):
            return {}
        return {
            REDZONE_BEHAVIOR_CUSTOMER: [
                {
                    RISK_BEHAVIOR: source.get(RISK_BEHAVIOR),
                    RISK_SCORE: source.get(RISK_SCORE),
                }
                for source in self.model_output[IAResponseFields.additionalInfo.value].get(REDZONE_BEHAVIOR_CUSTOMER)
            ][0],
            ALERTS_AND_INSIGHTS_CUSTOMER: [
                {
                    ALERTS: source.get(ALERTS),
                    INSIGHTS: source.get(INSIGHTS),
                    ASSESSMENT_REASONS: source.get(ASSESSMENT_REASONS),
                }
                for source in self.model_output[IAResponseFields.additionalInfo.value].get(ALERTS_AND_INSIGHTS_CUSTOMER)
            ][0],
            RECOMMENDED_BANK_ACCOUNT: self.model_output[IAResponseFields.additionalInfo.value].get(
                RECOMMENDED_BANK_ACCOUNT
            ),
        }

    def __get_lending_guide(self):
        if IAResponseFields.lendingGuide.value not in self.model_output or not isinstance(
            self.model_output[IAResponseFields.lendingGuide.value], dict
        ):
            return {}
        return {
            MIN_LOAN_AMOUNT: self.model_output[IAResponseFields.lendingGuide.value].get(MIN_LOAN_AMOUNT),
            MAX_LOAN_AMOUNT: self.model_output[IAResponseFields.lendingGuide.value].get(MAX_LOAN_AMOUNT),
            MIN_DEBIT_AMOUNT: self.model_output[IAResponseFields.lendingGuide.value].get(MIN_DEBIT_AMOUNT),
            MAX_DEBIT_AMOUNT: self.model_output[IAResponseFields.lendingGuide.value].get(MAX_DEBIT_AMOUNT),
            CUSTOMER_INCOME_TYPE: self.model_output[IAResponseFields.lendingGuide.value].get(CUSTOMER_INCOME_TYPE),
            DEBIT_FREQUENCY: self.model_output[IAResponseFields.lendingGuide.value].get(DEBIT_FREQUENCY),
            DEBIT_DATE: self.model_output[IAResponseFields.lendingGuide.value].get(DEBIT_DATE),
            PAYMENT_NEAR_HOLIDAY: self.model_output[IAResponseFields.lendingGuide.value].get(PAYMENT_NEAR_HOLIDAY),
            NEXT_PAYMENT_ON_HOLIDAY: self.model_output[IAResponseFields.lendingGuide.value].get(
                NEXT_PAYMENT_ON_HOLIDAY
            ),
            REPEAT_OPPORTUNITY: self.model_output[IAResponseFields.lendingGuide.value].get(REPEAT_OPPORTUNITY),
        }

    def __get_scores(self):
        if IAResponseFields.scores.value not in self.model_output or not isinstance(
            self.model_output[IAResponseFields.scores.value], dict
        ):
            return {}
        return {
            IS_BAD: {
                CUSTOMER_LEVEL: {
                    MODEL_REASONS: [
                        {
                            EXPLANATION: source.get(EXPLANATION),
                            FEATURE: source.get(FEATURE),
                            FEATURE_CONTRIBUTION: source.get(FEATURE_CONTRIBUTION),
                            FEATURE_VALUES: source.get(FEATURE_VALUES),
                            IMPACT: source.get(IMPACT),
                            IMPORTANCE_LEVEL: source.get(IMPORTANCE_LEVEL),
                        }
                        for source in self.model_output[IAResponseFields.scores.value]
                        .get(IS_BAD)
                        .get(CUSTOMER_LEVEL)
                        .get(MODEL_REASONS)
                    ],
                    MODEL_SCORE: [
                        {IS_BAD_SCORE: source.get(IS_BAD_SCORE)}
                        for source in self.model_output[IAResponseFields.scores.value]
                        .get(IS_BAD)
                        .get(CUSTOMER_LEVEL)
                        .get(MODEL_SCORE)
                    ],
                },
                ACCOUNT_LEVEL: {
                    MODEL_REASONS: [
                        {
                            ACCOUNT_GUID: source.get(ACCOUNT_GUID),
                            EXPLANATION: source.get(EXPLANATION),
                            FEATURE: source.get(FEATURE),
                            FEATURE_CONTRIBUTION: source.get(FEATURE_CONTRIBUTION),
                            FEATURE_VALUES: source.get(FEATURE_VALUES),
                            IMPACT: source.get(IMPACT),
                            IMPORTANCE_LEVEL: source.get(IMPORTANCE_LEVEL),
                        }
                        for source in self.model_output[IAResponseFields.scores.value]
                        .get(IS_BAD)
                        .get(ACCOUNT_LEVEL)
                        .get(MODEL_REASONS)
                    ],
                    MODEL_SCORE: [
                        {ACCOUNT_GUID: source.get(ACCOUNT_GUID), IS_BAD_SCORE: source.get(IS_BAD_SCORE)}
                        for source in self.model_output[IAResponseFields.scores.value]
                        .get(IS_BAD)
                        .get(ACCOUNT_LEVEL)
                        .get(MODEL_SCORE)
                    ],
                },
            },
            LOAN_PAID_OFF: {
                CUSTOMER_LEVEL: {
                    MODEL_REASONS: [
                        {
                            EXPLANATION: source.get(EXPLANATION),
                            FEATURE: source.get(FEATURE),
                            FEATURE_CONTRIBUTION: source.get(FEATURE_CONTRIBUTION),
                            FEATURE_VALUES: source.get(FEATURE_VALUES),
                            IMPACT: source.get(IMPACT),
                            IMPORTANCE_LEVEL: source.get(IMPORTANCE_LEVEL),
                        }
                        for source in self.model_output[IAResponseFields.scores.value]
                        .get(LOAN_PAID_OFF)
                        .get(CUSTOMER_LEVEL)
                        .get(MODEL_REASONS)
                    ],
                    MODEL_SCORE: [
                        {TOTAL_LOAN_PAID_OFF_SCORE: source.get(TOTAL_LOAN_PAID_OFF_SCORE)}
                        for source in self.model_output[IAResponseFields.scores.value]
                        .get(LOAN_PAID_OFF)
                        .get(CUSTOMER_LEVEL)
                        .get(MODEL_SCORE)
                    ],
                },
                ACCOUNT_LEVEL: {
                    MODEL_REASONS: [
                        {
                            ACCOUNT_GUID: source.get(ACCOUNT_GUID),
                            EXPLANATION: source.get(EXPLANATION),
                            FEATURE: source.get(FEATURE),
                            FEATURE_CONTRIBUTION: source.get(FEATURE_CONTRIBUTION),
                            FEATURE_VALUES: source.get(FEATURE_VALUES),
                            IMPACT: source.get(IMPACT),
                            IMPORTANCE_LEVEL: source.get(IMPORTANCE_LEVEL),
                        }
                        for source in self.model_output[IAResponseFields.scores.value]
                        .get(LOAN_PAID_OFF)
                        .get(ACCOUNT_LEVEL)
                        .get(MODEL_REASONS)
                    ],
                    MODEL_SCORE: [
                        {
                            ACCOUNT_GUID: source.get(ACCOUNT_GUID),
                            TOTAL_LOAN_PAID_OFF_SCORE: source.get(TOTAL_LOAN_PAID_OFF_SCORE),
                        }
                        for source in self.model_output[IAResponseFields.scores.value]
                        .get(LOAN_PAID_OFF)
                        .get(ACCOUNT_LEVEL)
                        .get(MODEL_SCORE)
                    ],
                },
            },
            RED_ZONE: {
                CUSTOMER_LEVEL: {
                    MODEL_REASONS: [
                        {
                            EXPLANATION: source.get(EXPLANATION),
                            FEATURE: source.get(FEATURE),
                            FEATURE_CONTRIBUTION: source.get(FEATURE_CONTRIBUTION),
                            FEATURE_VALUES: source.get(FEATURE_VALUES),
                            IMPACT: source.get(IMPACT),
                            IMPORTANCE_LEVEL: source.get(IMPORTANCE_LEVEL),
                        }
                        for source in self.model_output[IAResponseFields.scores.value]
                        .get(RED_ZONE)
                        .get(CUSTOMER_LEVEL)
                        .get(MODEL_REASONS)
                    ],
                    MODEL_SCORE: [
                        {RISK_SCORE: source.get(RISK_SCORE)}
                        for source in self.model_output[IAResponseFields.scores.value]
                        .get(RED_ZONE)
                        .get(CUSTOMER_LEVEL)
                        .get(MODEL_SCORE)
                    ],
                },
                ACCOUNT_LEVEL: {
                    MODEL_REASONS: [
                        {
                            ACCOUNT_GUID: source.get(ACCOUNT_GUID),
                            EXPLANATION: source.get(EXPLANATION),
                            FEATURE: source.get(FEATURE),
                            FEATURE_CONTRIBUTION: source.get(FEATURE_CONTRIBUTION),
                            FEATURE_VALUES: source.get(FEATURE_VALUES),
                            IMPACT: source.get(IMPACT),
                            IMPORTANCE_LEVEL: source.get(IMPORTANCE_LEVEL),
                        }
                        for source in self.model_output[IAResponseFields.scores.value]
                        .get(RED_ZONE)
                        .get(ACCOUNT_LEVEL)
                        .get(MODEL_REASONS)
                    ],
                    MODEL_SCORE: [
                        {ACCOUNT_GUID: source.get(ACCOUNT_GUID), RISK_SCORE: source.get(RISK_SCORE)}
                        for source in self.model_output[IAResponseFields.scores.value]
                        .get(RED_ZONE)
                        .get(ACCOUNT_LEVEL)
                        .get(MODEL_SCORE)
                    ],
                },
            },
            REPEAT: {
                CUSTOMER_LEVEL: {
                    MODEL_REASONS: [
                        {
                            EXPLANATION: source.get(EXPLANATION),
                            FEATURE: source.get(FEATURE),
                            FEATURE_CONTRIBUTION: source.get(FEATURE_CONTRIBUTION),
                            FEATURE_VALUES: source.get(FEATURE_VALUES),
                            IMPACT: source.get(IMPACT),
                            IMPORTANCE_LEVEL: source.get(IMPORTANCE_LEVEL),
                        }
                        for source in self.model_output[IAResponseFields.scores.value]
                        .get(REPEAT)
                        .get(CUSTOMER_LEVEL)
                        .get(MODEL_REASONS)
                    ],
                    MODEL_SCORE: [
                        {REPEAT_SCORE: source.get(REPEAT_SCORE)}
                        for source in self.model_output[IAResponseFields.scores.value]
                        .get(REPEAT)
                        .get(CUSTOMER_LEVEL)
                        .get(MODEL_SCORE)
                    ],
                },
                ACCOUNT_LEVEL: {
                    MODEL_REASONS: [
                        {
                            ACCOUNT_GUID: source.get(ACCOUNT_GUID),
                            EXPLANATION: source.get(EXPLANATION),
                            FEATURE: source.get(FEATURE),
                            FEATURE_CONTRIBUTION: source.get(FEATURE_CONTRIBUTION),
                            FEATURE_VALUES: source.get(FEATURE_VALUES),
                            IMPACT: source.get(IMPACT),
                            IMPORTANCE_LEVEL: source.get(IMPORTANCE_LEVEL),
                        }
                        for source in self.model_output[IAResponseFields.scores.value]
                        .get(REPEAT)
                        .get(ACCOUNT_LEVEL)
                        .get(MODEL_REASONS)
                    ],
                    MODEL_SCORE: [
                        {ACCOUNT_GUID: source.get(ACCOUNT_GUID), REPEAT_SCORE: source.get(REPEAT_SCORE)}
                        for source in self.model_output[IAResponseFields.scores.value]
                        .get(REPEAT)
                        .get(ACCOUNT_LEVEL)
                        .get(MODEL_SCORE)
                    ],
                },
            },
        }

    def __get_accounts(self):
        if IAResponseFields.accounts.value not in self.model_output or not isinstance(
            self.model_output[IAResponseFields.accounts.value], list
        ):
            return []
        return [
            {
                ACCOUNT_GUID: source.get(ACCOUNT_GUID),
                LENDING_GUIDE: {
                    MIN_LOAN_AMOUNT: source.get(LENDING_GUIDE).get(MIN_LOAN_AMOUNT),
                    MAX_LOAN_AMOUNT: source.get(LENDING_GUIDE).get(MAX_LOAN_AMOUNT),
                    MIN_DEBIT_AMOUNT: source.get(LENDING_GUIDE).get(MIN_DEBIT_AMOUNT),
                    MAX_DEBIT_AMOUNT: source.get(LENDING_GUIDE).get(MAX_DEBIT_AMOUNT),
                    CUSTOMER_INCOME_TYPE: source.get(LENDING_GUIDE).get(CUSTOMER_INCOME_TYPE),
                    DEBIT_FREQUENCY: source.get(LENDING_GUIDE).get(DEBIT_FREQUENCY),
                    DEBIT_DATE: source.get(LENDING_GUIDE).get(DEBIT_DATE),
                    PAYMENT_NEAR_HOLIDAY: source.get(LENDING_GUIDE).get(PAYMENT_NEAR_HOLIDAY),
                    NEXT_PAYMENT_ON_HOLIDAY: source.get(LENDING_GUIDE).get(NEXT_PAYMENT_ON_HOLIDAY),
                    REPEAT_OPPORTUNITY: source.get(LENDING_GUIDE).get(REPEAT_OPPORTUNITY),
                },
            }
            for source in self.model_output[IAResponseFields.accounts.value]
        ]

    def __get_model_version(self):
        if IAResponseFields.modelVersion.value not in self.model_output:
            return "UNKNOWN"
        return self.model_output[IAResponseFields.modelVersion.value]
