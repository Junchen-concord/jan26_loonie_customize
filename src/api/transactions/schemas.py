from marshmallow import Schema, fields

from api.schemas.model_analyze_schemas import AccountInputSchema


class LabeledTransactionSchema(Schema):
    accountGuid = fields.Str()
    transGuid = fields.Str()
    sourceName = fields.Str()
    description = fields.Str()
    date = fields.DateTime()
    amount = fields.Float()
    clusterLabel = fields.Str()
    type = fields.Str()
    fromModel = fields.Str()
    who = fields.Str(allow_none=True)
    how = fields.Str(allow_none=True)
    what = fields.Str(allow_none=True)
    whoCat = fields.Str(allow_none=True)
    dayOfWeek = fields.Str()
    sourceID = fields.Str()
    ibvCategory = fields.Str(allow_none=True)
    StackingPrediction = fields.Str(allow_none=True)
    incomeType = fields.Int()


class TransactionsAnalyzeRequest(Schema):
    labeledTransactions = fields.List(fields.Nested(LabeledTransactionSchema))
    accounts = fields.List(fields.Nested(AccountInputSchema))
    asOfDate = fields.Str()
