from postprocess.scores.redzone_explain import red_zone_feature_explain

def test_extreme_feature_value():
    """
    Test the extreme feature value case
    """
    features = ['activeMonthlyIncome', 'good_days_to_debit_by_peak_500','loanPmtAllTime']
    impacts = ['negative', 'negative', 'negative']
    feature_values = [0, 0, 0]
    # Run the red zone feature explanation function
    explanation = red_zone_feature_explain(features, impacts, feature_values)

    assert explanation == ['None','None','None']