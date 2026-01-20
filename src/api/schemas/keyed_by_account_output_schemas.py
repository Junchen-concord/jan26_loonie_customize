from marshmallow import Schema, fields

from api.schemas.model_analyze_schemas import (
    AlertsAndInsights,
    CashFlowModelAnalyze as CashFlow,
    IncomeSourceModelAnalyze as IncomeSource,
    LendingGuideModelAnalyze as LendingGuide,
    LoanSourceModelAnalyze as LoanSource,
    MajorIncomeSource,
    ModelScoreReason,
    OverdraftIncidents,
    RedZoneBehavior,
    SummaryInfo,
    TransactionOutputSchema,
)


class ScoreSchema(Schema):
    score = fields.Integer(required=True)
    modelReasons = fields.List(fields.Nested(ModelScoreReason))


class ScoresSchema(Schema):
    redZone = fields.Nested(ScoreSchema)
    repeat = fields.Nested(ScoreSchema)
    loanPaidOff = fields.Nested(ScoreSchema)
    isBad = fields.Nested(ScoreSchema)


class AccountInfoSchema(Schema):
    summary = fields.Nested(SummaryInfo)
    incomeSources = fields.List(fields.Nested(IncomeSource))
    loanSources = fields.List(fields.Nested(LoanSource))
    overdraftIncidents = fields.List(fields.Nested(OverdraftIncidents))
    majorIncomeSource = fields.Nested(MajorIncomeSource)
    cashFlow = fields.Nested(CashFlow)
    scores = fields.Nested(ScoresSchema)
    lendingGuide = fields.Nested(LendingGuide)
    creditTrans = fields.List(fields.Nested(TransactionOutputSchema))
    debitTrans = fields.List(fields.Nested(TransactionOutputSchema))


class CustomerInfoSchema(Schema):
    redZoneBehavior = fields.Nested(RedZoneBehavior)
    alertsAndInsights = fields.Nested(AlertsAndInsights)
    recommendedBankAccount = fields.String(required=True)
    scores = fields.Nested(ScoresSchema)
    lendingGuide = fields.Nested(LendingGuide)


class KeyedModelAnalyzeResponse(Schema):
    accountInfo = fields.Dict(keys=fields.Str(), values=fields.Nested(AccountInfoSchema), required=True)
    customerInfo = fields.Nested(CustomerInfoSchema, required=True)
