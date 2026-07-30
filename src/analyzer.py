import pandas as pd
from config.settings import DEFAULT_ANOMALY_THRESHOLD

def calculate_demand_statistics(df_demand: pd.DataFrame, selected_demands: list[str] | None = None) -> dict[str, dict[str, float | str]]:
    """Calculates traditional power demand statistics (MW).

    Args:
        df_demand (pd.DataFrame): Filtered DataFrame containing demand indicators.
        selected_demands (list[str] | None): List of specific demand series to analyze.

    Returns:
        dict[str, dict[str, float | str]]: Statistical summary per demand series.
    """
    if df_demand.empty:
        return {}

    print("\n🔍 Calculating power demand statistics...")
    stats = {}

    ordered_names = ([name for name in selected_demands if name in df_demand["name"].values]
        if selected_demands
        else df_demand["name"].unique()
    )

    for name_type in ordered_names:
        df_indicator = df_demand[df_demand["name"] == name_type]

        for geo_name, group_df in df_indicator.groupby("geo_name", sort=False):
            values = group_df["value"]
            max_idx = values.idxmax()
            max_time = group_df.loc[max_idx, "datetime"]

            series_label = (
                f"{name_type} ({geo_name})"
                if len(df_demand["geo_name"].unique()) > 1
                else name_type
            )

            stats[series_label] = {
                "mean": float(values.mean()),
                "median": float(values.median()),
                "max": float(values.max()),
                "min": float(values.min()),
                "std_dev": float(values.std()) if len(values) > 1 else 0.0,
                "peak_time": max_time.strftime("%Y-%m-%d %H:%M"),
                "geo_name": geo_name,
            }
            print(f"📊 Demand stats calculated for: {series_label}")

    return stats

def calculate_price_statistics(df_price: pd.DataFrame,) -> dict[str, dict[str, float | int | str]]:
    """Calculates market price statistics (€/MWh), including spreads and zero-price hours.

    Args:
        df_price (pd.DataFrame): Filtered DataFrame containing price indicators.

    Returns:
        dict[str, dict[str, float | int | str]]: Specialized market statistics per price series.
    """
    if df_price.empty:
        return {}

    print("\n🔍 Calculating energy price statistics...")
    stats = {}

    for (name_type, geo_name), group_df in df_price.groupby(["name", "geo_name"], sort=False):
        values = group_df["value"]

        max_idx = values.idxmax()
        min_idx = values.idxmin()

        max_time = group_df.loc[max_idx, "datetime"]
        min_time = group_df.loc[min_idx, "datetime"]

        max_val = float(values.max())
        min_val = float(values.min())

        # Zero or near-zero price hours (<= 5.0 €/MWh)
        hourly_series = group_df.set_index("datetime")["value"].resample("1h").mean()
        zero_low_hours = int((hourly_series <= 5.0).sum())

        series_label = (
            f"{name_type} ({geo_name})"
            if len(df_price["geo_name"].unique()) > 1
            else name_type
        )

        stats[series_label] = {
            "max": max_val,
            "max_time": max_time.strftime("%Y-%m-%d %H:%M"),
            "min": min_val,
            "min_time": min_time.strftime("%Y-%m-%d %H:%M"),
            "spread": max_val - min_val,
            "zero_low_price_hours": zero_low_hours,
            "geo_name": geo_name,
        }
        print(f"💶 Price stats calculated for: {series_label}")

    return stats

def compare_demand_models(df: pd.DataFrame, targets: tuple[str, str] | None = None) -> dict[str, str | float | int]:
    """Performs advanced comparative analysis dynamically between two selected demand or price series.

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

    # For comparison, ensure we isolate single geography or pivot by unique composite key
    df_work = df.copy()
    if "series_id" not in df_work.columns:
        df_work["series_id"] = df_work["name"]

    # Align both demand models and keep only timestamps where both have available data
    pivoted_df = df_work.pivot_table(index="datetime", columns="series_id", values="value", aggfunc="first")

    rows_before = len(pivoted_df)

    # Remove timestamps with missing values in either model
    pivoted_df = pivoted_df.dropna(subset=[model_a, model_b])

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
    max_diff_value = float(pivoted_df.loc[max_diff_idx, "difference"])

    # Calculate Mean Absolute Percentage Error (MAPE) assuming Model A is the baseline
    mape = float((pivoted_df["abs_difference"] / series_a.replace(0, pd.NA)).mean() * 100)

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
    """Detects abnormal spikes or drops in energy/price series using the Z-Score method.
    An anomaly is defined as any value that deviates from the mean by more than
    'threshold' times the standard deviation.

    Args:
        df (pd.DataFrame): The filtered energy DataFrame.
        threshold (float): The Z-score cutoff used to detect anomalies.

    Returns:
        dict[str, list[dict]]: A dictionary categorized by indicator and region containing lists of detected anomalies.
    """
    print("\n🔍 Scanning for statistical anomalies in dataset series...")
    anomalies_report = {}

    # Analyze anomalies individually for each (name, geo_name) series
    for (series_name, geo_name), group_df in df.groupby(["name", "geo_name"]):
        if len(group_df) < 3:
            continue # Not enough data points to compute variance reliably

        mean_val = group_df["value"].mean()
        std_dev = group_df["value"].std()

        # Handle edge case where std_dev is 0 to avoid division by zero
        if std_dev == 0 or pd.isna(std_dev):
            continue

        # Z-Score calculation: Z = (x - mean) / std_dev
        z_scores = (group_df["value"] - mean_val) / std_dev

        # Filter rows where the absolute Z-score breaks the threshold
        anomaly_rows = group_df[z_scores.abs() > threshold]

        series_label = f"{series_name} ({geo_name})" if len(df["geo_name"].unique()) > 1 else series_name

        if not anomaly_rows.empty:
            anomalies_report[series_label] = []
            for _, row in anomaly_rows.iterrows():
                # Determine if it's a Spike (positive deviation) or a Drop (negative deviation)
                anomaly_type = "SPIKE 📈" if row["value"] > mean_val else "DROP 📉"

                anomalies_report[series_label].append({
                    "datetime": row["datetime"],
                    "value": float(row["value"]),
                    "type": anomaly_type,
                    "deviation": float(row["value"] - mean_val),
                    "geo_name": geo_name,
                })

    return anomalies_report