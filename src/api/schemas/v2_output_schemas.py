from marshmallow import INCLUDE, Schema, fields


class LendingGuideSchema(Schema):
    minLoanAmount = fields.Float()
    maxLoanAmount = fields.Float()
    minDebitAmount = fields.Float()
    maxDebitAmount = fields.Float()
    customerIncomeType = fields.Str()
    debitFrequency = fields.Str()
    debitDate = fields.Str()
    paymentNearHoliday = fields.Str()
    nextPaymentOnHoliday = fields.Str()
    repeatOpportunity = fields.Str()


class IncomeSourceSchema(Schema):
    activeScore = fields.Int()
    depositMethod = fields.Str()
    errorCode = fields.Int()
    errorMessage = fields.Str()
    frequency = fields.Str()
    pastDeposits = fields.List(fields.Str())
    incomeType = fields.Str()
    lastPayDay = fields.Str()
    missingPayDay = fields.List(fields.Str())
    estimatedMonthlyIncome = fields.Float()
    numOfPay = fields.Int()
    numOfPayMonthly = fields.Int()
    perPayCheck = fields.Float()
    recurringScore = fields.Int()
    regularPayDay = fields.Str()
    sameDayFreq = fields.Int()  # cast to int in transform_v2_output
    sourceChannel = fields.Str()
    sourceID = fields.Str()
    incomeSource = fields.Str()
    sourceType = fields.Str()
    stabilityScore = fields.Int()
    stableMonthlyIncome = fields.Float()
    isDominant = fields.Int()
    nextPayDay = fields.Str()
    paymentNearHoliday = fields.Str()
    nextPayDayOnHoliday = fields.Str()


class LoanSourceSchema(Schema):
    sourceID = fields.Str()
    sourceName = fields.Str()
    numOfOrigination = fields.Int()
    numOfPay = fields.Int()
    frequency = fields.Str()
    amountObserved = fields.Float()
    monthlyPayment = fields.Float()
    interestRate = fields.Float()
    schedule = fields.Str()
    latestTransaction = fields.Str()
    loanType = fields.Str()
    debitType = fields.Str()
    errorCode = fields.Int()
    errorMessage = fields.Str()


class OverdraftIncidentSchema(Schema):
    date = fields.Str()
    amount = fields.Float()
    description = fields.Str()


class CashFlowSchema(Schema):
    totalCredits = fields.Float()
    totalDebits = fields.Float()
    netCashFlow = fields.Float()
    spending = fields.Float()


class RiskAnalysisSchema(Schema):
    riskBehavior = fields.Str()
    riskScore = fields.Int()


class AllTimeSchema(Schema):
    avgMonthlyBalance = fields.Float()
    overdraftIncidents = fields.Integer(strict=True)
    avgMonthlyIncome = fields.Float()
    numIncomeSources = fields.Integer(strict=True)
    numMonthsIncomeHistory = fields.Integer(strict=True)
    amountPaidInLoans = fields.Float()
    numLoans = fields.Integer(strict=True)
    cashflow = fields.Float()


class ThreeMonthSchema(AllTimeSchema):
    pass  # Same fields as AllTimeSchema


class SixMonthSchema(AllTimeSchema):
    pass  # Same fields as AllTimeSchema


class MonthlyIncomeSchema(Schema):
    recurringMonthlyIncome = fields.Float()
    activeMonthlyIncome = fields.Float()


class BankingSchema(Schema):
    card = fields.List(fields.Str())


class FeaturesDict(Schema):
    class Meta:
        unknown = INCLUDE


class AccountSchema(Schema):
    accountGuid = fields.Str()
    lendingGuide = fields.Nested(LendingGuideSchema)
    incomeSources = fields.List(fields.Nested(IncomeSourceSchema))
    loanSources = fields.List(fields.Nested(LoanSourceSchema))
    overdraftIncidents = fields.List(fields.Nested(OverdraftIncidentSchema))
    cashFlow = fields.Nested(CashFlowSchema)
    allTime = fields.Nested(AllTimeSchema)
    threeMonth = fields.Nested(ThreeMonthSchema)
    sixMonth = fields.Nested(SixMonthSchema)
    assessmentReasonsGood = fields.List(fields.Str())
    assessmentReasonsBad = fields.List(fields.Str())
    riskAnalysis = fields.Nested(RiskAnalysisSchema)
    currentBalance = fields.Float()
    availableBalance = fields.Float()
    banking = fields.Nested(BankingSchema)
    monthlyIncome = fields.Nested(MonthlyIncomeSchema)
    inflowExcludingLoans = fields.Float()
    accountType = fields.Str()
    features = fields.Nested(FeaturesDict)


class CustomerInfoSchema(Schema):
    riskAnalysisCustomer = fields.Nested(RiskAnalysisSchema)
    assessmentReasonsCustomerGood = fields.List(fields.Str())
    assessmentReasonsCustomerBad = fields.List(fields.Str())
    recommendedBankAccount = fields.Str()
    lendingGuideCustomer = fields.Nested(LendingGuideSchema)


class TransactionV2OutputSchema(Schema):
    # Ideally, the only fields we should return are fields that can change
    id = fields.Integer(required=False)
    stackingPrediction = fields.String(allow_none=True)
    description = fields.String(allow_none=True)
    sourceName = fields.String(allow_none=True)
    sourceID = fields.String(allow_none=True)
    incomeType = fields.Int(allow_none=True)
    ibvCategory = fields.String(allow_none=True)
    agentCategory = fields.String(allow_none=True)
    how = fields.String(allow_none=True)
    what = fields.String(allow_none=True)
    who = fields.String(allow_none=True)
    whoCat = fields.String(allow_none=True)
    clusterLabel = fields.String(allow_none=True)
    fromModel = fields.String(allow_none=True)


class ModelAnalyzeResponseV2(Schema):
    asOfDate = fields.Str()
    accounts = fields.List(fields.Nested(AccountSchema))
    modelVersion = fields.Str()
    executionTime = fields.Str()
    customerInfo = fields.Nested(CustomerInfoSchema)
    transactions = fields.List(fields.Nested(TransactionV2OutputSchema))


# V3 uses same response format as V2
ModelAnalyzeResponseV3 = ModelAnalyzeResponseV2
