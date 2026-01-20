from marshmallow import Schema, fields


class ValidationErrorResponse(Schema):
    code = fields.Int()
    description = fields.Str()
    errors = fields.Dict()
    name = fields.Str()


class ErrorResponse(Schema):
    status = fields.Int(description="HTTP status code")
    message = fields.Str(description="Description of the error")
