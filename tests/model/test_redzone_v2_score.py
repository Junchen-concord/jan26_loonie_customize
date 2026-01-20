import json
import os

from api.transformations.transform_v2_output import transform_v2_output
from config import config
from model.run_model import run_model

sample_data_path = os.path.realpath(os.path.join(config.ROOT_DIR, "..", "tests", "data", "2000.json"))


def test_risk_analysis_uses_redzone_v2_score():
    """Test that riskAnalysisCustomer.riskScore equals int(redZoneV2.modelScore[0].riskScore)."""
    with open(sample_data_path, "r") as fp:
        data = json.load(fp)
    output = run_model(json.dumps(data))
    output_json = json.loads(output)

    v2_output = transform_v2_output(output_json)

    # Get the V2 risk score from scores
    v2_risk_score = v2_output["customerInfo"]["scores"]["redZoneV2"]["modelScore"][0]["riskScore"]

    # Get the riskAnalysisCustomer.riskScore
    risk_analysis_score = v2_output["customerInfo"]["riskAnalysisCustomer"]["riskScore"]

    assert risk_analysis_score == int(v2_risk_score)
