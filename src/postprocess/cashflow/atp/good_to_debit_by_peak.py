import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.signal import find_peaks

from utils.decorators import timer


@timer
def good_to_debit_by_peak(
    time_series: pd.DataFrame,
    amount_due: int,
    minimum_days: int,
    prominence: int,
    peak_distance: int,
) -> tuple[pd.DataFrame, NDArray[np.float64], dict[str, NDArray[np.float64]]]:
    peaks, peak_properties = find_peaks(time_series.net, prominence=prominence, distance=peak_distance)
    peak_prominences = peak_properties["prominences"]

    # Create a copy of time_series to avoid SettingWithCopyWarning
    time_series_df = time_series.copy()
    
    # Initialize enough_balance column properly using loc
    time_series_df.loc[:, "enough_balance"] = False

    net_values = time_series_df.net.values

    # Vectorized check for balance sufficiency
    for i, peak in enumerate(peaks):
        peak_prominence = peak_prominences[i]
        if i == len(peaks) - 1:
            next_peak = len(time_series_df)
        else:
            next_peak = peaks[i + 1]

        # Vectorized operation to calculate the conditions across the range from peak to next_peak
        net_differences = net_values[peak] - net_values[peak:next_peak]

        # Calculate the condition in a vectorized manner
        conditions_met = (peak_prominence - net_differences) > amount_due
        time_series_df.loc[time_series_df.index[peak:next_peak], "enough_balance"] = conditions_met

    # Use loc for column assignment
    time_series_df.loc[:, "temp_interval_group"] = (~time_series_df.enough_balance).cumsum()
    
    # Reassign to original variable name
    time_series = time_series_df
    interval_length = (
        time_series[time_series.enough_balance]
        .groupby("temp_interval_group")
        .agg(time_len=("enough_balance", "sum"))
        .reset_index()
    )
    time_series = (
        time_series.reset_index()
        .merge(interval_length, how="left", on="temp_interval_group")
        .fillna(0)
        .infer_objects(copy=False)
        .set_index("date")
    )
    time_series["good_to_debit"] = time_series.enough_balance & (time_series.time_len >= minimum_days)
    return time_series, peaks, peak_properties
