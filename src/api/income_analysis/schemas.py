from marshmallow import Schema, fields

from api.schemas.keyed_by_account_output_schemas import ScoreSchema
from api.schemas.model_analyze_schemas import AlertsAndInsights, LendingGuideModelAnalyze as LendingGuide


class IncomeAnalysisRequest(Schema):
    # We don't take verbosity for these
    input = fields.Str()


class LendingGuideResponse(Schema):
    lendingGuide = fields.Nested(LendingGuide)


class RedZoneResponse(Schema):
    redZone = fields.Nested(ScoreSchema)


class AlertsAndInsightsResponse(Schema):
    alertsAndInsights = fields.List(fields.Nested(AlertsAndInsights))
