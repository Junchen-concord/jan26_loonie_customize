from marshmallow import INCLUDE, Schema, ValidationError, fields, validates


class SummaryInfo(Schema):
    accountType = fields.Str()
    activeMonthlyIncome = fields.Decimal()
    allTimeMonthlyIncome = fields.Decimal()
    asOfDate = fields.Str()
    averageMonthlyBalance3Month = fields.Decimal()
    averageMonthlyBalance6Month = fields.Decimal()
    averageMonthlyBalanceAll = fields.Decimal()
    card = fields.List(fields.Str())
    cashflowAllTime = fields.Decimal()
    cashflowSixMonth = fields.Decimal()
    cashflowThreeMonth = fields.Decimal()
    currentBalance = fields.Decimal()
    currentBalanceDate = fields.Str()
    incomeHistoryAllTime = fields.Integer()
    incomeHistorySixMonth = fields.Integer()
    incomeHistoryThreeMonth = fields.Integer()
    incomeSourceAllTime = fields.Integer()
    incomeSourceSixMonth = fields.Integer()
    incomeSourceThreeMonth = fields.Integer()
    index = fields.Integer()
    inflowExcludingLoans = fields.Decimal()
    loanIdentifiedAllTime = fields.Integer()
    loanIdentifiedSixMonth = fields.Integer()
    loanIdentifiedThreeMonth = fields.Integer()
    loanPmtAllTime = fields.Decimal()
    loanPmtSixMonth = fields.Decimal()
    loanPmtThreeMonth = fields.Decimal()
    od3m = fields.Integer()
    od6m = fields.Integer()
    odAll = fields.Integer()
    recurringMonthlyIncome = fields.Decimal()
    runError = fields.Integer()
    runMsg = fields.Str()
    sixMonthMonthlyIncome = fields.Decimal()
    threeMonthMonthlyIncome = fields.Decimal()


class CashFlowModelAnalyze(Schema):
    """Renamed from CashFlow to avoid schema naming conflicts."""

    accountGuid = fields.Str()
    netCashFlow = fields.Decimal()
    spending = fields.Decimal()
    totalCredits = fields.Decimal()
    totalDebits = fields.Decimal()


class AlertsAndInsights(Schema):
    alerts = fields.List(fields.Str())
    insights = fields.List(fields.Str())
    assessmentReasons = fields.List(fields.Str())


class RedZoneBehavior(Schema):
    riskScore = fields.Integer()
    riskBehavior = fields.Str()


class AdditionalInfo(Schema):
    alertsAndInsightsCustomer = fields.Nested(AlertsAndInsights)
    redZoneBehaviorCustomer = fields.Nested(RedZoneBehavior)
    recommendedBankAccount = fields.Str()


class OverdraftIncidents(Schema):
    accountGuid = fields.Str()
    amount = fields.Str()
    date = fields.Str()
    description = fields.Str()


class IncomeSourceModelAnalyze(Schema):
    """Renamed from IncomeSource to avoid schema naming conflicts."""

    accountGuid = fields.Str()
    activeScore = fields.Integer()
    depositMethod = fields.Str()
    errorCode = fields.Integer()
    errorMessage = fields.Str()
    frequency = fields.Str()
    historicalPayDay = fields.List(fields.Str())
    incomeType = fields.Str()
    isDominant = fields.Integer()
    lastPayDay = fields.Str()
    missingPayDay = fields.List(fields.Str())
    monthlyIncome = fields.Decimal()
    nextPayDay = fields.Str()
    nextPayDayOnHoliday = fields.Str()
    numOfPay = fields.Integer()
    numOfPayMonthly = fields.Integer()
    paymentNearHoliday = fields.Str()
    perPayCheck = fields.Decimal()
    recurringScore = fields.Integer()
    regularPayDay = fields.Str()
    sameDayFreq = fields.Integer()
    sourceChannel = fields.Str()
    sourceID = fields.Str()
    sourceName = fields.Str()
    sourceType = fields.Str()
    stabilityScore = fields.Integer()
    stableMonthlyIncome = fields.Decimal()


class MajorIncomeSource(Schema):
    accountGuid = fields.Str()
    incomeType = fields.Str()


class LoanSourceModelAnalyze(Schema):
    """Renamed from LoanSource to avoid schema naming conflicts."""

    accountGuid = fields.Str()
    debitType = fields.Str()
    errorCode = fields.Integer()
    errorMessage = fields.Str()
    frequency = fields.Str()
    interestRate = fields.Decimal()
    lastPayDay = fields.Str()
    loanType = fields.Str()
    numOfOrigination = fields.Integer()
    numOfPay = fields.Integer()
    originationAmount = fields.Decimal()
    paymentAmount = fields.Integer()
    regularPayDay = fields.Str()
    sourceID = fields.Str()
    sourceName = fields.Str()


class TransactionOutputSchema(Schema):
    accountGuid = fields.Str()
    amount = fields.Decimal()
    clusterLabel = fields.Str()
    date = fields.Str()
    dayOfWeek = fields.Str()
    description = fields.Str()
    fromModel = fields.Str()
    how = fields.Str()
    ibvCategory = fields.Str()
    sourceID = fields.Str()
    sourceName = fields.Str()
    transCategory = fields.Integer()
    transGuid = fields.Str()
    type = fields.Str()
    what = fields.Str()
    who = fields.Str()
    whoCat = fields.Str()


class LendingGuideModelAnalyze(Schema):
    """Renamed from LendingGuide to avoid schema naming conflicts."""

    accountGuid = fields.Str(required=False)  # present only in account level
    customerIncomeType = fields.Str()
    debitDate = fields.Str()
    debitFrequency = fields.Str()
    maxDebitAmount = fields.Integer()
    maxLoanAmount = fields.Integer()
    minDebitAmount = fields.Decimal()
    minLoanAmount = fields.Decimal()
    nextPaymentOnHoliday = fields.Boolean()
    paymentNearHoliday = fields.Str()
    repeatOpportunity = fields.Str()


class ModelScoreReason(Schema):
    accountGuid = fields.Str(required=False)  # present only in account level
    explanation = fields.Str()
    feature = fields.Str()
    feature_contribution = fields.Decimal()
    feature_values = fields.Decimal()
    impact = fields.Str()
    importance_level = fields.Integer()


class ModelScore(Schema):
    accountGuid = fields.Str(required=False)  # present only in account level
    riskScore = fields.Integer(required=False)  # present only under redZone
    repeatScore = fields.Integer(required=False)  # present only under repeat
    totalLoanPaidOffScore = fields.Integer(required=False)  # present only under loanPaidOff
    isBadScore = fields.Integer(required=False)  # present only under isBad


class ScoreMetadata(Schema):
    modelScoreReasons = fields.List(fields.Nested(ModelScoreReason))
    modelScore = fields.List(fields.Nested(ModelScore))


class FeatureScoreDict(Schema):
    class Meta:
        unknown = INCLUDE


class Score(Schema):
    accountLevel = fields.Nested(ScoreMetadata)
    customerLevel = fields.Nested(ScoreMetadata)


class FeatureScore(Schema):
    accountLevel = fields.Nested(FeatureScoreDict)
    customerLevel = fields.Nested(FeatureScoreDict)


class Scores(Schema):
    isBad = fields.Nested(Score)
    loanPaidOff = fields.Nested(Score)
    redZone = fields.Nested(Score)
    repeat = fields.Nested(Score)
    features = fields.Nested(FeatureScore)


class Accounts(Schema):
    accountGuid = fields.Str()
    lendingGuide = fields.Nested(LendingGuideModelAnalyze)


class ModelAnalyzeExperimentalRequest(Schema):
    verbosity = fields.List(fields.Str())
    input = fields.Str()


class ModelAnalyzeExperimentalResponse(Schema):
    summaryInfo = fields.Nested(SummaryInfo)
    incomeSources = fields.List(fields.Nested(IncomeSourceModelAnalyze))
    loanSources = fields.List(fields.Nested(LoanSourceModelAnalyze))
    overdraftIncidents = fields.List(fields.Nested(OverdraftIncidents))
    cashFlow = fields.List(fields.Nested(CashFlowModelAnalyze))
    redZoneBehavior = fields.List(fields.Nested(RedZoneBehavior))
    alertsAndInsights = fields.List(fields.Nested(AlertsAndInsights))
    majorIncomeSource = fields.List(fields.Nested(MajorIncomeSource))
    creditTrans = fields.List(fields.Nested(TransactionOutputSchema))
    debitTrans = fields.List(fields.Nested(TransactionOutputSchema))
    additionalInfo = fields.Nested(AdditionalInfo)
    lendingGuide = fields.Nested(LendingGuideModelAnalyze)
    scores = fields.Nested(Scores)
    accounts = fields.Nested(Accounts)
    modelVersion = fields.Str()


class ModelAnalyzeRequest(Schema):
    verbosity = fields.List(fields.Str())
    input = fields.Str()


class ModelAnalyzeResponseV1(Schema):
    summaryInfo = fields.Nested(SummaryInfo)
    incomeSources = fields.List(fields.Nested(IncomeSourceModelAnalyze))
    loanSources = fields.List(fields.Nested(LoanSourceModelAnalyze))
    overdraftIncidents = fields.List(fields.Nested(OverdraftIncidents))
    cashFlow = fields.List(fields.Nested(CashFlowModelAnalyze))
    redZoneBehavior = fields.List(fields.Nested(RedZoneBehavior))
    alertsAndInsights = fields.List(fields.Nested(AlertsAndInsights))
    majorIncomeSource = fields.List(fields.Nested(MajorIncomeSource))
    creditTrans = fields.List(fields.Nested(TransactionOutputSchema))
    debitTrans = fields.List(fields.Nested(TransactionOutputSchema))
    additionalInfo = fields.Nested(AdditionalInfo)
    lendingGuide = fields.Nested(LendingGuideModelAnalyze)
    scores = fields.Nested(Scores)
    accounts = fields.Nested(Accounts)
    modelVersion = fields.Str()


class AccountInputSchema(Schema):
    accountGuid = fields.Str()
    accountType = fields.Str(missing="CHECKING")
    currentBalance = fields.Raw()
    availableBalance = fields.Raw(missing=0.0)
    currentBalanceDate = fields.Str()

    @validates("currentBalance")
    def validate_current_balance(self, value):
        if not isinstance(value, (str, int, float)):
            raise ValidationError("currentBalance must be a string, int, or float.")


class TransactionInputSchema(Schema):
    originalDescription = fields.Str()
    description = fields.Str()
    guid = fields.Str()
    accountGuid = fields.Str()
    category = fields.Raw()
    amount = fields.Raw()
    date = fields.Str()
    type = fields.Str()
    label = fields.Str()

    class Meta:
        unknown = INCLUDE

    @validates("amount")
    def validate_amount(self, value):
        if not isinstance(value, (int, float)):
            raise ValidationError("transaction amount must be either int or float.")

    @validates("type")
    def validate_type(self, value):
        if value not in ["CREDIT", "DEBIT"]:
            raise ValidationError("transactions must be either CREDIT or DEBIT.")


class InputJson(Schema):
    input = fields.Str()


class ModelAnalyzeRequestV3(Schema):
    asOfDate = fields.Str(required=True)
    accounts = fields.List(fields.Nested(AccountInputSchema), required=True)
    transactions = fields.List(fields.Nested(TransactionInputSchema), required=True)
    applicationInformation = fields.Dict(missing={})
    IBVAuth = fields.Dict(missing={})

    class Meta:
        unknown = INCLUDE
