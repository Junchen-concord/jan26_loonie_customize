import numpy as np
import pandas as pd

from postprocess.cashflow.atp.good_to_debit_by_peak import good_to_debit_by_peak
from postprocess.cashflow.atp.make_time_series import make_time_series
from utils.decorators import timer


@timer
def get_all_peak_features(df: pd.DataFrame) -> pd.DataFrame:
    time_series = make_time_series(df)
    features_500_peak = get_peak_features(
        time_series,
        peak=True,
        minimum_prominence=500,
        due_amount=200,
        cashflow_info=True,
    )
    features_250_peak = get_peak_features(
        time_series,
        peak=True,
        minimum_prominence=250,
        due_amount=100,
        cashflow_info=False,
    )
    features_100_peak = get_peak_features(
        time_series,
        peak=True,
        minimum_prominence=100,
        due_amount=40,
        cashflow_info=False,
    )
    features_500_valley = get_peak_features(
        time_series,
        peak=False,
        minimum_prominence=500,
        due_amount=200,
        cashflow_info=False,
    )
    features_250_valley = get_peak_features(
        time_series,
        peak=False,
        minimum_prominence=250,
        due_amount=100,
        cashflow_info=False,
    )
    features_100_valley = get_peak_features(
        time_series,
        peak=False,
        minimum_prominence=100,
        due_amount=40,
        cashflow_info=False,
    )
    # Filter out any empty dataframes to avoid the concatenation warning
    feature_dfs = [
        features_500_peak,
        features_250_peak,
        features_100_peak,
        features_500_valley,
        features_250_valley,
        features_100_valley,
    ]
    
    non_empty_dfs = [df for df in feature_dfs if not df.empty]
    
    if non_empty_dfs:
        all_atp_features = pd.concat(non_empty_dfs, axis=1)
    else:
        # Create an empty DataFrame with appropriate columns if all inputs are empty
        all_atp_features = pd.DataFrame()
    return all_atp_features


@timer
def get_peak_features(
    time_series: pd.DataFrame,
    peak=True,
    minimum_prominence=500,
    due_amount=200,
    cashflow_info=True,
) -> pd.DataFrame:
    minimum_days = 3
    minimum_peak_intervals = 7
    peak_or_valley = "peak_" if peak else "valley_"
    # net_cashflow = cashflow.resample("1D").first()
    # time_series = make_time_series(df)
    if peak:
        time_series_df_by_peak, peaks, peak_properties = good_to_debit_by_peak(
            time_series,
            due_amount,
            minimum_days,
            minimum_prominence,
            minimum_peak_intervals,
        )
    else:
        # Logic change from debit at peak to avoid the valley
        time_series_df_by_peak, peaks, peak_properties = good_to_debit_by_peak(
            -time_series,
            due_amount,
            minimum_days,
            minimum_prominence,
            minimum_peak_intervals,
        )
        # Create a copy to ensure we're not working with a view
        time_series_copy = time_series_df_by_peak.copy()
        
        # Use loc to avoid SettingWithCopyWarning
        time_series_copy.loc[:, "good_to_debit"] = ~time_series_df_by_peak.good_to_debit
        
        # Reassign to original variable
        time_series_df_by_peak = time_series_copy

    n_good_days_to_debit = time_series_df_by_peak.good_to_debit.sum()
    peak_prominence = peak_properties["prominences"]
    n_peaks = len(peaks)
    if len(peaks) > 0:
        max_peak_prominence = np.max(peak_prominence)
        min_peak_prominence = np.min(peak_prominence)
        avg_peak_prominence = np.mean(peak_prominence)
    else:
        max_peak_prominence = 0
        min_peak_prominence = 0
        avg_peak_prominence = 0

    good_to_debit_groups = (
        time_series_df_by_peak[time_series_df_by_peak.enough_balance]
        .groupby("temp_interval_group")
        .time_len.first()
    )
    if len(good_to_debit_groups) > 0:
        max_peak_gtd = np.max(good_to_debit_groups)
        min_peak_gtd = np.min(good_to_debit_groups)
        avg_peak_gtd = np.mean(good_to_debit_groups)
        peak_most_recent_gtd_length = good_to_debit_groups.iloc[-1]
    else:
        max_peak_gtd = 0
        min_peak_gtd = 0
        avg_peak_gtd = 0
        peak_most_recent_gtd_length = 0
    if not cashflow_info:
        return pd.DataFrame(
            {
                "n_" + peak_or_valley + str(minimum_prominence): [n_peaks],
                "good_days_to_debit_by_"
                + peak_or_valley
                + str(minimum_prominence): [n_good_days_to_debit],
                peak_or_valley
                + "trans_history_ratio_"
                + str(minimum_prominence): [n_peaks / len(time_series)],
                peak_or_valley
                + "good_days_to_debit_trans_history_ratio"
                + str(minimum_prominence): [
                    n_good_days_to_debit / len(time_series)
                ],
                "max_"
                + peak_or_valley
                + "prominence_"
                + str(minimum_prominence): [max_peak_prominence],
                "min_"
                + peak_or_valley
                + "prominence_"
                + str(minimum_prominence): [min_peak_prominence],
                "avg_"
                + peak_or_valley
                + "prominence_"
                + str(minimum_prominence): [avg_peak_prominence],
                "max_" + peak_or_valley + "gtd_" + str(minimum_prominence): [
                    max_peak_gtd
                ],
                "min_" + peak_or_valley + "gtd_" + str(minimum_prominence): [
                    min_peak_gtd
                ],
                "avg_" + peak_or_valley + "gtd_" + str(minimum_prominence): [
                    avg_peak_gtd
                ],
                peak_or_valley
                + "most_recent_gtd_length_"
                + str(minimum_prominence): [peak_most_recent_gtd_length],
            }
        )
    else:
        return pd.DataFrame(
            {
                "transation_period_lengths": [len(time_series)],
                "max_balance_differences": [
                    time_series_df_by_peak.net.max()
                    - time_series_df_by_peak.net.min()
                ],
                "net_cashflow_from_start_to_end": [
                    time_series_df_by_peak.net.iloc[1]
                    - time_series_df_by_peak.net.iloc[-2]
                ],
                "n_" + peak_or_valley + str(minimum_prominence): [n_peaks],
                "good_days_to_debit_by_"
                + peak_or_valley
                + str(minimum_prominence): [n_good_days_to_debit],
                peak_or_valley
                + "trans_history_ratio_"
                + str(minimum_prominence): [n_peaks / len(time_series)],
                peak_or_valley
                + "good_days_to_debit_trans_history_ratio"
                + str(minimum_prominence): [
                    n_good_days_to_debit / len(time_series)
                ],
                "max_"
                + peak_or_valley
                + "prominence_"
                + str(minimum_prominence): [max_peak_prominence],
                "min_"
                + peak_or_valley
                + "prominence_"
                + str(minimum_prominence): [min_peak_prominence],
                "avg_"
                + peak_or_valley
                + "prominence_"
                + str(minimum_prominence): [avg_peak_prominence],
                "max_" + peak_or_valley + "gtd_" + str(minimum_prominence): [
                    max_peak_gtd
                ],
                "min_" + peak_or_valley + "gtd_" + str(minimum_prominence): [
                    min_peak_gtd
                ],
                "avg_" + peak_or_valley + "gtd_" + str(minimum_prominence): [
                    avg_peak_gtd
                ],
                peak_or_valley
                + "most_recent_gtd_length_"
                + str(minimum_prominence): [peak_most_recent_gtd_length],
            }
        )
