import pandas as pd
import numpy as np
from scipy.stats import zscore


def detect_outliers_zscore(df, column_name, threshold=3):
    """
    This function detects outliers in a specified column of a pandas DataFrame using z-scores.
    Outliers are defined as values with z-scores greater than the threshold or less than -threshold.
    Detected outliers are set to NaN, and the number of dropped values (outliers) is printed.
    The 'stn_id_dendra' column is retained in the output.

    Parameters:
    df (pd.DataFrame): The input DataFrame
    column_name (str): The name of the column to check for outliers
    threshold (float): The z-score threshold for identifying outliers (default is 3)

    Returns:
    pd.DataFrame: A DataFrame with outliers in the specified column replaced by NaN
    """
    # Carry over the 'stn_id_dendra' column to the output DataFrame
    stn_id_dendra = (
        df["stn_id_dendra"].iloc[0] if "stn_id_dendra" in df.columns else None
    )

    # Calculate z-scores for the column, excluding NaN values
    z_scores = zscore(df[column_name].dropna())

    # Create a boolean mask for outliers
    outliers_mask = np.abs(z_scores) > threshold
    num_outliers = outliers_mask.sum()

    # Align the mask with the original DataFrame by reindexing and replace outliers with NaN
    df.loc[df[column_name].dropna().index[outliers_mask], column_name] = np.nan
    print(f"Number of outliers dropped: {num_outliers}")

    # Add the 'stn_id_dendra' column back with the same value for all rows
    df["stn_id_dendra"] = stn_id_dendra

    return df


import pandas as pd
import numpy as np


def drop_outliers_rolling(df, column, window=3, threshold=1.5):
    """
    Removes outliers from a time series DataFrame by comparing each data point with its
    preceding and following values in a rolling window and prints the number of outliers dropped.

    Parameters:
        df (pd.DataFrame): The time series DataFrame.
        column (str): The column to check for outliers.
        window (int): The window size for rolling comparison (default is 3).
        threshold (float): The z-score threshold to consider a point as an outlier (default is 1.5).

    Returns:
        pd.DataFrame: The DataFrame with outliers removed.
    """
    # Carry over the 'stn_id_dendra' column to the output DataFrame
    stn_id_dendra = (
        df["stn_id_dendra"].iloc[0] if "stn_id_dendra" in df.columns else None
    )

    # Calculate the rolling mean and standard deviation for the window
    rolling_mean = df[column].rolling(window=window, center=True).mean()
    rolling_std = df[column].rolling(window=window, center=True).std()

    # Calculate the z-scores (how many standard deviations a point is from the rolling mean)
    z_scores = (df[column] - rolling_mean) / rolling_std

    # Create a mask where data points within the threshold are kept
    mask = z_scores.abs() <= threshold

    # Count and print the number of outliers dropped
    outliers_dropped = len(df) - mask.sum()
    print(f"Number of outliers dropped: {outliers_dropped}")

    # Drop rows where the z-scores are above the threshold (outliers)
    clean_df = df[mask].copy()
    # add station id back
    clean_df["stn_id_dendra"] = stn_id_dendra

    return clean_df


def leading_trailing_nan(df, column_name):
    """Remove leading and trailing NaN from df.

    Parameters:
    df (pd.DataFrame): The input DataFrame
    column_name (str): The name of the column to check for NaNs

    Returns:
    pd.DataFrame: A DataFrame with lead and trailing NaNs removed
    """
    first_idx = df[column_name].first_valid_index()
    last_idx = df[column_name].last_valid_index()

    return df.loc[first_idx:last_idx]
