import pandas as pd
from src.constants import DEFAULT_ANOMALY_THRESHOLD

def calculate_energy_statistics(df: pd.DataFrame) -> dict[str, dict[str, float | int | str]]:
    """Calculates key statistical metrics (max, min, mean, median, std_dev) broken
    down by each unique electricity demand type present in the dataset.

    Args:
        df (pd.DataFrame): The validated energy DataFrame.

    Returns:
        dict[str, dict[str, float | int | str]]: A nested dictionary containing stats for each demand type.
    """
    print("\n🔍 Calculating advanced statistics per demand type...")

    stats_per_type = {}

    # Group by demand type to compute isolated metrics
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

def compare_demand_models(df: pd.DataFrame, targets: tuple[str, str] | None = None) -> dict[str, str | float | int]:
    """Performs advanced comparative analysis dynamically between the first two 
    selected electricity demand types available in the filtered dataset.

    Args:
        df (pd.DataFrame): The filtered energy DataFrame.
        targets (tuple[str, str] | None): Pair of demand series names (model_a, model_b).

    Returns:
        dict[str, str | float | int]: Comparative metrics dictionary or empty dict if targets are missing/invalid.
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

    # Align both demand models and keep only timestamps where both have available data
    pivoted_df = df.pivot(index="datetime", columns="name", values="value")

    rows_before = len(pivoted_df)

    # Remove timestamps with missing values in either demand model
    pivoted_df = pivoted_df.dropna()

    rows_after = len(pivoted_df)

    # Inform the user if part of the dataset was excluded due to missing values
    if rows_before != rows_after:
        print(f"ℹ️ {rows_before - rows_after} timestamps were excluded due to missing values in one of the series.")

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

def detect_demand_anomalies(df: pd.DataFrame, threshold: float = DEFAULT_ANOMALY_THRESHOLD) -> dict[str, list[dict]]:
    """Detects abnormal spikes or drops in electricity demand using the Z-Score method.
    An anomaly is defined as any value that deviates from the mean by more than
    'threshold' times the standard deviation.

    Args:
        df (pd.DataFrame): The filtered energy DataFrame.
        threshold (float): The Z-score cutoff used to detect anomalies.

    Returns:
        dict[str, list[dict]]: A dictionary categorized by demand type containing lists of detected anomalies.
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

        # Z-Score calculation: Z = (x - mean) / std_dev
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