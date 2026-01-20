from marshmallow import Schema, fields


# Deprecate
class ModelLabelRequest(Schema):
    input = fields.Str()


class ModelLabelResponse(Schema):
    labeledTransactions = fields.List(fields.Field())
