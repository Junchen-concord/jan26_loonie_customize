from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LendingGuide(BaseModel):
    minLoanAmount: Optional[float] = None
    maxLoanAmount: Optional[float] = None
    minDebitAmount: Optional[float] = None
    maxDebitAmount: Optional[float] = None
    customerIncomeType: Optional[str] = None
    debitFrequency: Optional[str] = None
    debitDate: Optional[str] = None
    paymentNearHoliday: Optional[str] = None
    nextPaymentOnHoliday: Optional[str] = None
    repeatOpportunity: Optional[str] = None

    class Config:
        extra = "allow"


class IncomeSource(BaseModel):
    activeScore: Optional[int] = None
    depositMethod: Optional[str] = None
    errorCode: Optional[int] = None
    errorMessage: Optional[str] = None
    frequency: Optional[str] = None
    pastDeposits: Optional[List[str]] = None
    incomeType: Optional[str] = None
    lastPayDay: Optional[str] = None
    missingPayDay: Optional[List[str]] = None
    estimatedMonthlyIncome: Optional[float] = None
    numOfPay: Optional[int] = None
    numOfPayMonthly: Optional[int] = None
    perPayCheck: Optional[float] = None
    recurringScore: Optional[int] = None
    regularPayDay: Optional[str] = None
    sameDayFreq: Optional[int] = None
    sourceChannel: Optional[str] = None
    sourceID: Optional[str] = None
    incomeSource: Optional[str] = None
    sourceType: Optional[str] = None
    stabilityScore: Optional[int] = None
    stableMonthlyIncome: Optional[float] = None
    isDominant: Optional[int] = None
    nextPayDay: Optional[str] = None
    paymentNearHoliday: Optional[str] = None
    nextPayDayOnHoliday: Optional[str] = None

    class Config:
        extra = "allow"


class LoanSource(BaseModel):
    sourceID: Optional[str] = None
    sourceName: Optional[str] = None
    numOfOrigination: Optional[int] = None
    numOfPay: Optional[int] = None
    frequency: Optional[str] = None
    amountObserved: Optional[float] = None
    monthlyPayment: Optional[float] = None
    interestRate: Optional[float] = None
    schedule: Optional[str] = None
    latestTransaction: Optional[str] = None
    loanType: Optional[str] = None
    debitType: Optional[str] = None
    errorCode: Optional[int] = None
    errorMessage: Optional[str] = None
    lenderName: Optional[str] = None

    class Config:
        extra = "allow"


class OverdraftIncident(BaseModel):
    date: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None

    class Config:
        extra = "allow"


class CashFlow(BaseModel):
    totalCredits: Optional[float] = None
    totalDebits: Optional[float] = None
    netCashFlow: Optional[float] = None
    spending: Optional[float] = None

    class Config:
        extra = "allow"


class RiskAnalysis(BaseModel):
    riskBehavior: Optional[str] = None
    riskScore: Optional[int] = None

    class Config:
        extra = "allow"


class AgentWithdrawnModel(BaseModel):
    score: Optional[int] = None

    class Config:
        extra = "allow"


class AppVerificationResult(BaseModel):
    appFrequencyMatch: Optional[int] = None
    appFrequencyMatchBS: Optional[int] = None
    IBVSuggestsInconsistent: Optional[int] = None
    IBVSuggestsBiweekly: Optional[bool] = None
    IBVSuggestsWeekly: Optional[bool] = None
    IBVSuggestsSemiMonthly: Optional[bool] = None
    IBVSuggestsMonthly: Optional[bool] = None
    IBVSuggestsBS: Optional[bool] = None
    appPaydayMatch: Optional[int] = None
    IBVMonthlyIncome: Optional[float] = None
    reportedIncomeMinusActiveIncome: Optional[float] = None
    requestedAmountRatio: Optional[float] = None
    fnameMatchRate: Optional[float] = None
    lnameMatchRate: Optional[float] = None
    IBVFromChase: Optional[bool] = None
    appFromChase: Optional[bool] = None
    accountNumberMatchAuth: Optional[bool] = None
    accountNumberLastFourMatchAuth: Optional[bool] = None
    accountNumberFirstFourMatchAuth: Optional[bool] = None
    routingNumberMatch: Optional[bool] = None
    cityMatchAuth: Optional[bool] = None
    stateMatchAuth: Optional[bool] = None
    zipMatchAuth: Optional[bool] = None
    phoneMatch: Optional[bool] = None
    emailMatch: Optional[bool] = None
    fnameInTransactions: Optional[bool] = None
    fnameInTransactionsTime: Optional[int] = None
    lnameInTransactions: Optional[bool] = None
    lnameInTransactionsTime: Optional[int] = None
    accountNumberInTransactions: Optional[bool] = None
    accountNumberInTransactionsTime: Optional[int] = None
    cityInTransactions: Optional[bool] = None
    cityInTransactionsTime: Optional[int] = None
    stateInTransactions: Optional[bool] = None
    stateInTransactionsTime: Optional[int] = None
    zipInTransactions: Optional[bool] = None
    zipInTransactionsTime: Optional[int] = None
    fnameMatch: Optional[bool] = None
    lnameMatch: Optional[bool] = None
    accountNumberMatch: Optional[bool] = None
    stateMatch: Optional[bool] = None
    zipMatch: Optional[bool] = None
    cityMatch: Optional[bool] = None

    class Config:
        extra = "allow"


class ApplicationCheck(BaseModel):
    agentWithdrawnModel: Optional[AgentWithdrawnModel] = None
    appVerificationResult: Optional[AppVerificationResult] = None

    class Config:
        extra = "allow"


class AllTime(BaseModel):
    avgMonthlyBalance: Optional[float] = None
    overdraftIncidents: Optional[int] = None
    avgMonthlyIncome: Optional[float] = None
    numIncomeSources: Optional[int] = None
    numMonthsIncomeHistory: Optional[int] = None
    amountPaidInLoans: Optional[float] = None
    numLoans: Optional[int] = None
    cashflow: Optional[float] = None

    class Config:
        extra = "allow"


class ThreeMonth(BaseModel):
    avgMonthlyBalance: Optional[float] = None
    overdraftIncidents: Optional[int] = None
    avgMonthlyIncome: Optional[float] = None
    numIncomeSources: Optional[int] = None
    numMonthsIncomeHistory: Optional[int] = None
    amountPaidInLoans: Optional[float] = None
    numLoans: Optional[int] = None
    cashflow: Optional[float] = None

    class Config:
        extra = "allow"


class SixMonth(BaseModel):
    avgMonthlyBalance: Optional[float] = None
    overdraftIncidents: Optional[int] = None
    avgMonthlyIncome: Optional[float] = None
    numIncomeSources: Optional[int] = None
    numMonthsIncomeHistory: Optional[int] = None
    amountPaidInLoans: Optional[float] = None
    numLoans: Optional[int] = None
    cashflow: Optional[float] = None

    class Config:
        extra = "allow"


class MonthlyIncome(BaseModel):
    recurringMonthlyIncome: Optional[float] = None
    activeMonthlyIncome: Optional[float] = None

    class Config:
        extra = "allow"


class Banking(BaseModel):
    card: Optional[List[str]] = None

    class Config:
        extra = "allow"


class Account(BaseModel):
    accountGuid: Optional[str] = None
    lendingGuide: Optional[LendingGuide] = None
    incomeSources: Optional[List[IncomeSource]] = None
    loanSources: Optional[List[LoanSource]] = None
    overdraftIncidents: Optional[List[OverdraftIncident]] = None
    cashFlow: Optional[CashFlow] = None
    allTime: Optional[AllTime] = None
    threeMonth: Optional[ThreeMonth] = None
    sixMonth: Optional[SixMonth] = None
    assessmentReasonsGood: Optional[List[str]] = None
    assessmentReasonsBad: Optional[List[str]] = None
    riskAnalysis: Optional[RiskAnalysis] = None
    currentBalance: Optional[float] = None
    availableBalance: Optional[float] = None
    banking: Optional[Banking] = None
    monthlyIncome: Optional[MonthlyIncome] = None
    inflowExcludingLoans: Optional[float] = None
    features: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"


class CustomerInfo(BaseModel):
    riskAnalysisCustomer: Optional[RiskAnalysis] = None
    assessmentReasonsCustomerGood: Optional[List[str]] = None
    assessmentReasonsCustomerBad: Optional[List[str]] = None
    recommendedBankAccount: Optional[str] = None
    lendingGuideCustomer: Optional[LendingGuide] = None
    applicationCheck: Optional[ApplicationCheck] = None

    class Config:
        extra = "allow"


class TransactionV2Output(BaseModel):
    id: Optional[int] = None
    stackingPrediction: Optional[str] = None
    description: Optional[str] = None
    sourceName: Optional[str] = None
    sourceID: Optional[str] = None
    incomeType: Optional[int] = None
    ibvCategory: Optional[str] = None
    agentCategory: Optional[str] = None
    how: Optional[str] = None
    what: Optional[str] = None
    who: Optional[str] = None
    whoCat: Optional[str] = None
    clusterLabel: Optional[str] = None
    fromModel: Optional[str] = None

    class Config:
        extra = "allow"


class ModelAnalyzeResponseV3(BaseModel):
    asOfDate: Optional[str] = Field(None, description="Analysis Date")
    accounts: Optional[List[Account]] = Field(None, description="Account-level analysis results")
    modelVersion: Optional[str] = Field(None, description="Version of the model used for analysis")
    customerInfo: Optional[CustomerInfo] = Field(None, description="Customer-level analysis information")
    transactions: Optional[List[TransactionV2Output]] = Field(None, description="Transaction analysis results")

    class Config:
        schema_extra = {
            "example": {
                "accounts": [
                    {
                        "accountGuid": "12345",
                        "accountType": "CHECKING",
                        "currentBalance": 1500.00,
                        "monthlyIncome": {"activeMonthlyIncome": 3500.00, "recurringMonthlyIncome": 3200.00},
                        "lendingGuide": {"maxLoanAmount": 1000.00, "debitFrequency": "Biweekly"},
                    }
                ],
                "modelVersion": "16.13.0",
                "customerInfo": {"recommendedBankAccount": "12345"},
            }
        }


class HealthCheckResponse(BaseModel):
    status: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Health check message")
    model_version: str = Field(..., description="Current model version")
