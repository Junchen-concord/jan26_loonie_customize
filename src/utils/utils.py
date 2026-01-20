import datetime
import os
import re
from enum import Enum

import pandas as pd
from dateutil.relativedelta import relativedelta


class TimeFrame(Enum):
    ONE_MONTH = "ONE_MONTH"
    TWO_MONTH = "TWO_MONTH"
    THREE_MONTH = "THREE_MONTH"
    FOUR_MONTH = "FOUR_MONTH"
    FIVE_MONTH = "FIVE_MONTH"
    SIX_MONTH = "SIX_MONTH"
    ALL = "ALL"


def ensure_dir(path) -> None:
    """
    create path by first checking its existence,
    :param paths: path
    :return:
    """
    if not os.path.exists(path):
        os.makedirs(path)


# Define a regular expression pattern to match invalid characters
clean_pattern = re.compile(r"[^\x20-\x7E]+")


def clean_json_string_general(json_string: str) -> str:  #
    # Use the pattern to replace invalid characters with an empty string
    cleaned_json_string = clean_pattern.sub("", json_string)

    return cleaned_json_string


clean_dict_pattern = re.compile(r"[^\x20-\x7E]+")


def clean_dict_strings(data):
    """Clean non-printable ASCII characters from all string values in dict/list structures.

    Uses the same regex pattern as clean_json_string_general to ensure consistency.
    """

    if isinstance(data, dict):
        return {k: clean_dict_strings(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_dict_strings(item) for item in data]
    elif isinstance(data, str):
        return clean_dict_pattern.sub("", data)
    else:
        return data


def clean_json_string_specific(json_string: str) -> str:
    invalid_characters = ["�", ""]
    # Replace each character in the list with an empty string
    cleaned_json_string = json_string
    for char in invalid_characters:
        cleaned_json_string = cleaned_json_string.replace(char, "")
    return cleaned_json_string


def standardize_date_format(date_series: pd.Series) -> pd.Series:
    """
    Standardize milliseconds for datetime strings in a pandas Series.
    Adds '.999' milliseconds to datetime strings that do not have them.
    Adds 'T23:59:59.999Z' to datetime strings that do not have a time at all.
    Args:
        date_series (pd.Series): A Series of datetime strings.
    Returns:
        pd.Series: A Series with standardized datetime strings.
    """
    # Convert all entries to string for processing
    date_str_series = date_series.astype(str)

    def append_ms(date_str):
        # Check if the date string contains milliseconds (assumes ISO format)
        if "T" not in date_str:
            if "Z" in date_str:
                date_str = date_str.split("Z")[0]
            return date_str + "T23:59:59.999Z"
        if "." not in date_str.split("T")[1]:
            # Insert milliseconds before the 'Z'
            parts = date_str.split("Z")
            return parts[0] + ".999Z"
        else:
            return date_str

    standardized_dates = date_str_series.apply(append_ms)
    return pd.to_datetime(standardized_dates)


def df_to_json(df: pd.DataFrame) -> list[dict]:
    dict = df.to_dict(orient="index")
    return [i for i in dict.values()]


def truncate_transactions(df: pd.DataFrame, timeframe: TimeFrame, as_of_date: datetime.date) -> pd.DataFrame:
    """
    Truncates transaction dataframe to the timeframe provided.
    Args:
        df (pd.DataFrame): a DataFrame of all transactions
        timeframe (TimeFrame): timeframe to truncate to
        as_of_date (datetime.date): date of the application, any transactions after this date are discarded
    Returns:
        pd.DataFrame: truncated transactions DataFrame
    """
    # Remove transactions that occur after as_of_date (transactions on as_of_date are allowed)
    as_of_timestamp = pd.Timestamp(as_of_date)
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"] <= as_of_timestamp]

    timeframe_offsets = {
        TimeFrame.ONE_MONTH: 1,
        TimeFrame.TWO_MONTH: 2,
        TimeFrame.THREE_MONTH: 3,
        TimeFrame.FOUR_MONTH: 4,
        TimeFrame.FIVE_MONTH: 5,
        TimeFrame.SIX_MONTH: 6,
    }

    if timeframe == TimeFrame.ALL:
        return df
    else:
        most_recent_transaction_date = df["date"].max()
        cutoff_date = (most_recent_transaction_date - relativedelta(months=timeframe_offsets[timeframe])).replace(day=1)
        return df[df["date"] >= cutoff_date]


def remove_account_guid(d):
    """
    Remove all fields inside that has accountGuid as key
    """
    if isinstance(d, dict):
        if "accountGuid" in d:
            del d["accountGuid"]
        for key in d:
            remove_account_guid(d[key])
    elif isinstance(d, list):
        for item in d:
            remove_account_guid(item)


def merge_duplicate_clusters(
    df: pd.DataFrame, comparison_column: str, cluster_label_col: str = "cluster_label", threshold: float = 0.5
) -> pd.DataFrame:
    """
    Merge clusters when their comparison_column values are duplicates (e.g., "ABC" vs "ABC ABC").

    This function compares clusters pairwise and merges them if:
    1. One cluster's dominant value (>=threshold) is a doubled version of another cluster's dominant value
    2. Example: if cluster1 has "ABC" and cluster2 has "ABC ABC", they'll be merged

    Args:
        df (pd.DataFrame): DataFrame with transactions and cluster labels
        comparison_column (str): Column name to compare for duplicate patterns
        cluster_label_col (str): Column name containing cluster labels (default: "cluster_label")
        threshold (float): Minimum proportion a value must represent in its cluster (default: 0.5)

    Returns:
        pd.DataFrame: DataFrame with merged cluster labels
    """
    if comparison_column not in df.columns or cluster_label_col not in df.columns:
        return df

    df = df.copy()
    unique_clusters = df[cluster_label_col].unique()

    # Build a mapping of comparison values to their clusters
    for i, cluster1 in enumerate(unique_clusters):
        cluster1_data = df[df[cluster_label_col] == cluster1]
        cluster1_values = cluster1_data[comparison_column].value_counts()
        cluster1_size = len(cluster1_data)

        for cluster2 in unique_clusters[i + 1 :]:
            cluster2_data = df[df[cluster_label_col] == cluster2]
            cluster2_values = cluster2_data[comparison_column].value_counts()
            cluster2_size = len(cluster2_data)

            # Compare values between the two clusters
            for val1 in cluster1_values.index:
                val1_count = cluster1_values[val1]
                # Check if val1 represents >= threshold of cluster1
                if val1_count / cluster1_size < threshold:
                    continue

                for val2 in cluster2_values.index:
                    val2_count = cluster2_values[val2]
                    # Check if val2 represents >= threshold of cluster2
                    if val2_count / cluster2_size < threshold:
                        continue

                    # Check if val1 = val2 + " " + val2 or val2 = val1 + " " + val1
                    if val1 == val2 + " " + val2 or val2 == val1 + " " + val1:
                        # Merge clusters: use the cluster with more common value
                        if val1_count >= val2_count:
                            target_cluster = cluster1
                        else:
                            target_cluster = cluster2

                        # Update all rows in both clusters to use target cluster
                        df.loc[df[cluster_label_col].isin([cluster1, cluster2]), cluster_label_col] = target_cluster
                        break

    return df
