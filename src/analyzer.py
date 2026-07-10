import pandas as pd

def calculate_energy_statistics(df: pd.DataFrame) -> dict:
    """Calculates key statistical metrics (max, min, mean) broken down
    by each unique electricity demand type in the 'name' column.

    Args:
        df (pd.DataFrame): The validated energy DataFrame.

    Returns:
        dict: A nested dictionary containing stats for each demand type.
    """
    print("\n🔍 Calculating advanced statistics per demand type...")

    stats_per_type = {}

    # Group by 'name' to isolate each demand type (Real, Prevista, Programada...)
    for name_type, group_df in df.groupby("name", sort=False):
        values = group_df["value"]

        # Find the exact time when the maximum peak occurred for this specific group
        max_time = group_df.loc[values.idxmax(), "datetime"]

        # Store full analytical metrics using exact native types
        stats_per_type[name_type] = {
            "mean": float(values.mean()),
            "median": float(values.median()),
            "max": int(values.max()),
            "min": int(values.min()),
            "std_dev": float(values.std()),
            "peak_time": max_time.strftime("%Y-%m-%d %H:%M")
        }

        print(f"📊 Processed comprehensive stats for: {name_type}")

    return stats_per_type

def compare_demand_models(df: pd.DataFrame, targets: tuple = None) -> dict:
    """Performs advanced comparative analysis dynamically between the first two 
    selected electricity demand types available in the filtered dataset.

    Args:
        df (pd.DataFrame): The filtered energy DataFrame.
        targets (tuple, optional): A tuple containing (model_a, model_b) names to compare.

    Returns:
        dict: A dictionary containing comparative metrics, or empty if targets are missing or invalid.
    """
    # Safe guard: Skip if no explicit targets are passed or the format is invalid
    if not targets or len(targets) != 2:
        return {}

    # Extract target model names
    model_a, model_b = targets

    # Validate that both models exist in the DataFrame to prevent KeyErrors
    if model_a not in df["name"].values or model_b not in df["name"].values:
        print(f"⚠️ Advanced comparison skipped: One or both targets ('{model_a}', '{model_b}') are not in the current filtered data.")
        return {}

    print(f"\n🧠 Running advanced comparative analysis between '{model_a}' and '{model_b}'...")

    # Pivot and align data by datetime
    pivoted_df = df.pivot(index="datetime", columns="name", values="value").dropna()

    series_a = pivoted_df[model_a]
    series_b = pivoted_df[model_b]

    # Calculate differences (Model A - Model B)
    pivoted_df["difference"] = series_a - series_b
    pivoted_df["abs_difference"] = pivoted_df["difference"].abs()

    # Find the exact timestamp of the maximum absolute deviation
    max_diff_idx = pivoted_df["abs_difference"].idxmax()
    max_diff_time = max_diff_idx.strftime("%Y-%m-%d %H:%M")
    max_diff_value = int(pivoted_df.loc[max_diff_idx, "difference"])

    # Calculate Mean Absolute Percentage Error (MAPE) assuming Model A is the baseline
    mape = float((pivoted_df["abs_difference"] / series_a).mean() * 100)

    # Calculate Pearson Correlation Coefficient
    correlation = float(series_a.corr(series_b))

    # Package metrics along with the names of the compared models
    comparison_stats = {
        "model_a": model_a,
        "model_b": model_b,
        "mean_difference": float(pivoted_df["difference"].mean()),
        "max_difference_value": max_diff_value,
        "max_difference_time": max_diff_time,
        "mape": mape,
        "correlation": correlation
    }

    print("✅ Advanced comparative analysis completed successfully.")
    return comparison_stats

def detect_demand_anomalies(df: pd.DataFrame, threshold: float = 2.0) -> dict:
    """Detects abnormal spikes or drops in electricity demand using the Z-Score method.
    An anomaly is defined as any value that deviates from the mean by more than
    'threshold' times the standard deviation.

    Args:
        df (pd.DataFrame): The filtered energy DataFrame.
        threshold (float): The Z-score cutoff (default is 2.0).

    Returns:
        dict: A dictionary categorized by demand type containing lists of detected anomalies.
    """
    print("\n🔍 Scanning for statistical anomalies in energy demand...")
    anomalies_report = {}

    # Analyze anomalies individually for each demand type present in the data
    for demand_name in df["name"].unique():
        demand_data = df[df["name"] == demand_name]

        if len(demand_data) < 3:
            continue # Not enough data points to compute variance reliably

        mean_val = demand_data["value"].mean()
        std_dev = demand_data["value"].std()

        # Handle edge case where std_dev is 0 to avoid division by zero
        if std_dev == 0:
            continue

        # Calculate Z-score for every row in this demand type
        # Z = (x - mean) / std_dev
        z_scores = (demand_data["value"] - mean_val) / std_dev

        # Filter rows where the absolute Z-score breaks the threshold
        anomaly_rows = demand_data[z_scores.abs() > threshold]

        if not anomaly_rows.empty:
            anomalies_report[demand_name] = []
            for _, row in anomaly_rows.iterrows():
                # Determine if it's a Spike (positive deviation) or a Drop (negative deviation)
                anomaly_type = "SPIKE 📈" if row["value"] > mean_val else "DROP 📉"

                anomalies_report[demand_name].append({
                    "datetime": row["datetime"],
                    "value": row["value"],
                    "type": anomaly_type,
                    "deviation": (row["value"] - mean_val)
                })

    return anomalies_report

def filter_dataframe_by_hour(df: pd.DataFrame, start_hour: int, end_hour: int) -> pd.DataFrame:
    """Filters the DataFrame to keep only the rows within the specified hour range.

    Args:
        df (pd.DataFrame): The validated dataset containing a 'datetime'
        column.
        start_hour (int): Lower bound of the hour range (inclusive, 0-23).
        end_hour (int): Upper bound of the hour range (exclusive, 0-23).

    Returns:
        pd.DataFrame: A new safely isolated DataFrame containing only the
        filtered hours.
    """
    print(f"\n⏳ Filtering timeline data from {start_hour:02d}:00 to {end_hour:02d}:00...")

    # Ensure datetime column is actually in datetime format
    df_copy = df.copy()
    df_copy["datetime"] = pd.to_datetime(df_copy["datetime"])

    # Filter using pandas dt.hour accessor
    # end_hour is exclusive to handle standard ranges nicely (e.g. 0 to 8 means 00:00 to 07:59)
    hour_mask = (df_copy["datetime"].dt.hour >= start_hour) & (df_copy["datetime"].dt.hour < end_hour)

    filtered_df = df_copy[hour_mask]

    # Data availability sanity check before returning
    if filtered_df.empty:
        print("⚠️ Warning: The selected time filter returned an empty dataset!")

    return filtered_df