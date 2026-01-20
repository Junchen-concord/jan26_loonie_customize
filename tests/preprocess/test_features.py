from preprocess_data import PreProcessTestData

from config import config
from labeling.xgboost.analyzer_features import IAFeatures


def test_IA_time_intervals_binning():
    x1, x2, x3, x4, x5, x6, x7, x8, x9 = 1, 4, 7, 11, 15, 19, 30, 37, -8
    assert IAFeatures.time_intervals_binning(x1) == "1"
    assert IAFeatures.time_intervals_binning(x2) == "2-5"
    assert IAFeatures.time_intervals_binning(x3) == "6-8"
    assert IAFeatures.time_intervals_binning(x4) == "9-12"
    assert IAFeatures.time_intervals_binning(x5) == "13-17"
    assert IAFeatures.time_intervals_binning(x6) == "18-24"
    assert IAFeatures.time_intervals_binning(x7) == "24-35"
    assert IAFeatures.time_intervals_binning(x8) == "36+"
    assert IAFeatures.time_intervals_binning(x9) == "36+"


def test_time_amount_features():
    df = PreProcessTestData().transactions_df
    time_amount_df = IAFeatures.time_amount_features(
        df, config.IA_DATE, config.IA_AMOUNT
    )
    assert len(time_amount_df.columns) == 31
    expected_cols = [
        "counts",
        "credit_time_interval_1",
        "credit_time_interval_2",
        "credit_time_interval_1_freq",
        "credit_time_interval_2_freq",
        "credit_time_interval_1_percentage",
        "credit_time_interval_2_percentage",
        "debit_time_interval_1",
        "debit_time_interval_2",
        "debit_time_interval_1_freq",
        "debit_time_interval_2_freq",
        "debit_time_interval_1_percentage",
        "debit_time_interval_2_percentage",
        "payment_amount_mean",
        "payment_amount_min",
        "payment_amount_max",
        "payment_amount_std",
        "originated_amount_mean",
        "originated_amount_min",
        "originated_amount_max",
        "originated_amount_std",
        "recent_originated_amount",
        "recent_payment_amount",
        "amount_mode",
        "amount_mode_freq",
        "multiple_of_5",
        "credit_only",
        "debit_only",
        "credit_and_debit",
        "n_credits",
        "n_debits",
    ]
    for col in expected_cols:
        assert col in time_amount_df.columns
