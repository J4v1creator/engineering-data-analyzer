import pandas as pd

from config.settings import DEFAULT_ANOMALY_THRESHOLD
from src.utils import translate_indicator


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

    has_multiple_geos = len(df_demand["geo_name"].unique()) > 1

    for name_type in ordered_names:
        df_indicator = df_demand[df_demand["name"] == name_type]

        for geo_name, group_df in df_indicator.groupby("geo_name", sort=False):
            values = group_df["value"]
            max_idx = values.idxmax()
            max_time = group_df.loc[max_idx, "datetime"]

            series_label = (f"{name_type} ({geo_name})" if has_multiple_geos else name_type)

            display_label = translate_indicator(name_type, geo_name, has_multiple_geos)

            stats[series_label] = {
                "mean": float(values.mean()),
                "median": float(values.median()),
                "max": float(values.max()),
                "min": float(values.min()),
                "std_dev": float(values.std()) if len(values) > 1 else 0.0,
                "peak_time": max_time.strftime("%Y-%m-%d %H:%M"),
                "geo_name": geo_name,
            }
            print(f"📊 Demand stats calculated for: {display_label}")

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
    has_multiple_geos = len(df_price["geo_name"].unique()) > 1

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

        series_label = (f"{name_type} ({geo_name})" if has_multiple_geos else name_type)
        display_label = translate_indicator(name_type, geo_name, has_multiple_geos)

        stats[series_label] = {
            "max": max_val,
            "max_time": max_time.strftime("%Y-%m-%d %H:%M"),
            "min": min_val,
            "min_time": min_time.strftime("%Y-%m-%d %H:%M"),
            "spread": max_val - min_val,
            "zero_low_price_hours": zero_low_hours,
            "geo_name": geo_name,
        }
        print(f"💶 Price stats calculated for: {display_label}")

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
        model_a_en = translate_indicator(model_a)
        model_b_en = translate_indicator(model_b)
        print(f"⚠️ Advanced comparison skipped: One or both targets ('{model_a_en}', '{model_b_en}') are not in the current filtered data.")
        return {}

    model_a_en = translate_indicator(model_a)
    model_b_en = translate_indicator(model_b)
    print(f"\n🧠 Running advanced comparative analysis between '{model_a_en}' and '{model_b_en}'...")

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
        "correlation": correlation,
    }

    print("✅ Advanced comparative analysis completed successfully.")
    return comparison_stats


def detect_demand_anomalies(df: pd.DataFrame, threshold: float = DEFAULT_ANOMALY_THRESHOLD) -> dict[str, list[dict]]:
    """Detects abnormal spikes or drops in energy/price series using the Z-Score method.

    Args:
        df (pd.DataFrame): The filtered energy DataFrame.
        threshold (float): The Z-score cutoff used to detect anomalies.

    Returns:
        dict[str, list[dict]]: A dictionary categorized by indicator containing lists of detected anomalies.
    """
    print("\n🔍 Scanning for statistical anomalies in dataset series...")
    anomalies_report = {}
    has_multiple_geos = len(df["geo_name"].unique()) > 1

    # Analyze anomalies individually for each (name, geo_name) series
    for (series_name, geo_name), group_df in df.groupby(["name", "geo_name"]):
        if len(group_df) < 3:
            continue

        mean_val = group_df["value"].mean()
        std_dev = group_df["value"].std()

        # Handle edge case where std_dev is 0 to avoid division by zero
        if std_dev == 0 or pd.isna(std_dev):
            continue

        # Z-Score calculation: Z = (x - mean) / std_dev
        z_scores = (group_df["value"] - mean_val) / std_dev

        # Filter rows where the absolute Z-score breaks the threshold
        anomaly_rows = group_df[z_scores.abs() > threshold]

        series_label = (f"{series_name} ({geo_name})" if has_multiple_geos else series_name)

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


def calculate_market_economic_volume(df: pd.DataFrame) -> dict:
    """Calculates the total economic volume (€) moved in the wholesale market
    by aligning demand (5-min) and SPOT price (15-min) into 1-hour intervals.

    Args:
        df (pd.DataFrame): Validated market dataframe containing id, name, geo_id, geo_name, value, datetime.

    Returns:
        dict: Summary of market volume metrics (total euros, peak spend hour,
        weighted average price).
    """
    # Filter for correct series and compatible regions
    demand_mask = (df["name"] == "Demanda real") & (df["geo_name"].str.contains("Península", case=False, na=False))
    spot_mask = (df["name"] == "Precio mercado SPOT Diario") & (df["geo_name"].str.contains("España", case=False, na=False))

    demand_df = df[demand_mask].copy()
    spot_df = df[spot_mask].copy()

    if demand_df.empty or spot_df.empty:
        return {}

    # Temporary resampling to 1 hour (1h)
    demand_df["datetime"] = pd.to_datetime(demand_df["datetime"])
    spot_df["datetime"] = pd.to_datetime(spot_df["datetime"])

    # Group by hour using resample
    demand_hourly = (
        demand_df.set_index("datetime")["value"]
        .resample("1h")
        .mean()
        .reset_index()
        .rename(columns={"value": "demand_mwh"})
    )

    spot_hourly = (
        spot_df.set_index("datetime")["value"]
        .resample("1h")
        .mean()
        .reset_index()
        .rename(columns={"value": "spot_price_eur_mwh"})
    )

    # Merge both hourly aligned tables
    merged = pd.merge(demand_hourly, spot_hourly, on="datetime", how="inner")

    if merged.empty:
        return {}

    # Calculation of Economic Volume (€ per hour)
    merged["hourly_volume_eur"] = (merged["demand_mwh"] * merged["spot_price_eur_mwh"])

    # Consolidated metrics
    total_volume_eur = merged["hourly_volume_eur"].sum()
    total_energy_mwh = merged["demand_mwh"].sum()

    # Hour of maximum economic spending
    max_spend_row = merged.loc[merged["hourly_volume_eur"].idxmax()]

    # Demand-weighted average price (VWAP)
    volume_weighted_avg_price = (total_volume_eur / total_energy_mwh if total_energy_mwh > 0 else 0.0)

    return {
        "total_volume_eur": total_volume_eur,
        "total_energy_mwh": total_energy_mwh,
        "weighted_avg_price": volume_weighted_avg_price,
        "peak_spend_hour": max_spend_row["datetime"],
        "peak_spend_eur": max_spend_row["hourly_volume_eur"],
        "peak_spend_demand_mw": max_spend_row["demand_mwh"],
        "peak_spend_price_eur": max_spend_row["spot_price_eur_mwh"],
    }