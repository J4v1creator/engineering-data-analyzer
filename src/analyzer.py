"""Core mathematics, price spread evaluation, market volume calculation, and Z-Score anomaly modeling."""

import pandas as pd

from config.settings import DEFAULT_ANOMALY_THRESHOLD, DEMAND_INDICATOR_IDS, GLOBAL_GEO_ORDER, PRICE_INDICATOR_IDS
from src.utils import translate_indicator


def calculate_demand_statistics(df_demands: pd.DataFrame, selected_demands: list[int] | None = None) -> dict[str, dict[str, float | str]]:
    """Calculates power demand statistics (MW) sorted by configuration priority.

    Args:
        df_demands (pd.DataFrame): Filtered DataFrame containing demand indicators.
        selected_demands (list[int] | None): List of specific demand indicator IDs to analyze.

    Returns:
        dict[str, dict[str, float | str]]: Statistical summary per demand series.
    """
    if df_demands.empty:
        return {}

    print("\n🔍 Calculating power demand statistics...")

    # Determine which demand IDs to process (preserving configured priority order)
    target_ids = selected_demands if selected_demands else DEMAND_INDICATOR_IDS
    df_filtered = df_demands[df_demands["indicator_id"].isin(target_ids)].copy()

    if df_filtered.empty:
        return {}

    # Sort DataFrame rows based on DEMAND_INDICATOR_IDS ordering
    df_filtered["indicator_id"] = pd.Categorical(df_filtered["indicator_id"], categories=target_ids, ordered=True)
    df_filtered = df_filtered.sort_values("indicator_id")

    has_multiple_geos = df_filtered["geo_id"].nunique() > 1
    stats = {}

    # Grouping with sort=False preserves the categorical order applied above
    for (ind_id, geo_id), group in df_filtered.groupby(["indicator_id", "geo_id"], sort=False):
        values = group["value"]
        max_row = group.loc[values.idxmax()]

        peak_time = max_row["datetime"]
        peak_str = peak_time.strftime("%Y-%m-%d %H:%M") if hasattr(peak_time, "strftime") else str(peak_time)

        label = translate_indicator(indicator_id=ind_id, geo_id=geo_id, show_geo=has_multiple_geos)

        stats[label] = {
            "mean": float(values.mean()),
            "median": float(values.median()),
            "max": float(values.max()),
            "min": float(values.min()),
            "std_dev": float(values.std()) if len(values) > 1 else 0.0,
            "peak_time": peak_str,
            "geo_name": group["geo_name"].iloc[0] if "geo_name" in group.columns else "Unknown",
        }

        print(f"📊 Demand stats calculated for: {label}")

    return stats


def calculate_price_statistics(df_prices: pd.DataFrame, selected_prices: list[int] | None = None) -> dict:
    """Calculates market price statistics (€/MWh) sorted by configuration priority.

    Args:
        df_prices (pd.DataFrame): Filtered DataFrame containing price indicators.
        selected_prices (list[int] | None): List of specific price indicator IDs to analyze.

    Returns:
        dict: Specialized market statistics per price series.
    """
    if df_prices.empty:
        return {}

    print("\n🔍 Calculating energy price statistics...")

    # Determine which price IDs to process (preserving configured priority order)
    target_ids = selected_prices if selected_prices else PRICE_INDICATOR_IDS
    df_filtered = df_prices[df_prices["indicator_id"].isin(target_ids)].copy()

    if df_filtered.empty:
        return {}

    # Sort DataFrame rows based on PRICE_INDICATOR_IDS ordering
    df_filtered["indicator_id"] = pd.Categorical(df_filtered["indicator_id"], categories=target_ids, ordered=True)
    df_filtered["geo_id"] = pd.Categorical(df_filtered["geo_id"], categories=GLOBAL_GEO_ORDER, ordered=True)
    df_filtered = df_filtered.sort_values(["indicator_id", "geo_id"])

    has_multiple_geos = df_filtered["geo_id"].nunique() > 1
    stats = {}

    # Grouping with sort=False preserves the categorical order applied above
    for (price_id, geo_id), df_sub in df_filtered.groupby(["indicator_id", "geo_id"], sort=False, observed=True):
        if df_sub.empty:
            continue

        values = df_sub["value"]
        max_row = df_sub.loc[values.idxmax()]
        min_row = df_sub.loc[values.idxmin()]

        # Format timestamps safely
        max_time = max_row["datetime"]
        min_time = min_row["datetime"]
        max_str = max_time.strftime("%Y-%m-%d %H:%M") if hasattr(max_time, "strftime") else str(max_time)
        min_str = min_time.strftime("%Y-%m-%d %H:%M") if hasattr(min_time, "strftime") else str(min_time)

        # Generate translated label (includes geography region if applicable)
        series_name = translate_indicator(indicator_id=price_id, geo_id=geo_id, show_geo=has_multiple_geos)

        stats[series_name] = {
            "max": float(values.max()),
            "max_time": max_str,
            "min": float(values.min()),
            "min_time": min_str,
            "spread": float(values.max() - values.min()),
            "zero_low_price_hours": int((values <= 5.0).sum()),
            "mean": float(values.mean()),
        }

        print(f"📊 Price stats calculated for: {series_name}")

    return stats


def compare_demand_models(df: pd.DataFrame, targets: tuple[int, int] | list[int] | None = None) -> dict[str, str | float | int]:
    """Performs comparative analysis dynamically between two selected demand series IDs.

    Args:
        df (pd.DataFrame): Filtered energy DataFrame.
        targets (tuple[int, int] | list[int] | None): Pair of demand indicator_ids (id_a, id_b).

    Returns:
        dict[str, str | float | int]: Comparative metrics dictionary or empty dict if invalid.
    """
    if not targets or len(targets) != 2:
        return {}

    id_a, id_b = targets[0], targets[1]

    # Validate presence of both indicator IDs in dataset
    if id_a not in df["indicator_id"].values or id_b not in df["indicator_id"].values:
        print(f"⚠️ Advanced comparison skipped: One or both target IDs ({id_a}, {id_b}) are not present.")
        return {}

    # Translate IDs to user-friendly names for printing/reporting
    model_a_en = translate_indicator(indicator_id=id_a)
    model_b_en = translate_indicator(indicator_id=id_b)

    print(f"\n🧠 Running advanced comparative analysis between '{model_a_en}' and '{model_b_en}'...")

    # Pivot table using indicator_id (guarantees numerical matching)
    pivoted_df = df.pivot_table(
        index="datetime", 
        columns="indicator_id", 
        values="value", 
        aggfunc="first"
    )

    rows_before = len(pivoted_df)
    pivoted_df = pivoted_df.dropna(subset=[id_a, id_b])
    rows_after = len(pivoted_df)

    # Check if there are valid rows to analyze
    if pivoted_df.empty:
        print("⚠️ Advanced comparison skipped: No overlapping valid data points found.")
        return {}

    if rows_before != rows_after:
        print(f"ℹ️ {rows_before - rows_after} timestamps excluded due to missing values in target series.")

    series_a = pivoted_df[id_a]
    series_b = pivoted_df[id_b]

    # Error and correlation metrics
    pivoted_df["difference"] = series_a - series_b
    pivoted_df["abs_difference"] = pivoted_df["difference"].abs()

    max_diff_idx = pivoted_df["abs_difference"].idxmax()
    max_diff_time = max_diff_idx.strftime("%Y-%m-%d %H:%M") if hasattr(max_diff_idx, "strftime") else str(max_diff_idx)
    max_diff_value = float(pivoted_df.loc[max_diff_idx, "difference"])

    mape = float((pivoted_df["abs_difference"] / series_a.replace(0, pd.NA)).mean() * 100)
    correlation = float(series_a.corr(series_b))

    return {
        "model_a": id_a,
        "model_b": id_b,
        "mean_difference": float(pivoted_df["difference"].mean()),
        "max_difference_value": max_diff_value,
        "max_difference_time": max_diff_time,
        "mape": mape,
        "correlation": correlation,
    }


def detect_demand_anomalies(df: pd.DataFrame, threshold: float = DEFAULT_ANOMALY_THRESHOLD) -> dict[str, list[dict]]:
    """Detects abnormal spikes or drops in energy/price series using Z-Score methodology.

    Args:
        df (pd.DataFrame): Filtered energy DataFrame.
        threshold (float): Z-score cut-off threshold.

    Returns:
        dict[str, list[dict]]: Dictionary mapping series labels to lists of anomaly events.
    """
    # 1. Early exit if DataFrame is empty or missing required columns
    if df.empty or "indicator_id" not in df.columns or "geo_id" not in df.columns:
        print("⚠️ [ANOMALIES] Empty dataset or missing required columns. Skipping analysis.")
        return {}

    print("\n🔍 Scanning for statistical anomalies in dataset series...")
    anomalies_report = {}
    has_multiple_geos = df["geo_id"].nunique() > 1

    # 2. Group by indicator and region to calculate localized Z-Scores
    for (ind_id, geo_id), group_df in df.groupby(["indicator_id", "geo_id"]):
        if len(group_df) < 3:
            continue

        mean_val = group_df["value"].mean()
        std_dev = group_df["value"].std()

        # Avoid division by zero when standard deviation is zero or NaN
        if std_dev == 0 or pd.isna(std_dev):
            continue

        # Z-Score calculation: (X - μ) / σ
        z_scores = (group_df["value"] - mean_val) / std_dev
        anomaly_rows = group_df[z_scores.abs() > threshold]

        if not anomaly_rows.empty:
            series_label = translate_indicator(indicator_id=ind_id, geo_id=geo_id, show_geo=has_multiple_geos)
            geo_name = group_df["geo_name"].iloc[0] if "geo_name" in group_df.columns else "Unknown"

            anomalies_report[series_label] = []

            for _, row in anomaly_rows.iterrows():
                # Format datetime safely to string (e.g. "2026-03-15 14:00")
                dt_val = row["datetime"]
                dt_str = dt_val.strftime("%Y-%m-%d %H:%M") if hasattr(dt_val, "strftime") else str(dt_val)

                anomaly_type = "SPIKE 📈" if row["value"] > mean_val else "DROP 📉"

                anomalies_report[series_label].append({
                    "datetime": dt_str,
                    "value": float(row["value"]),
                    "type": anomaly_type,
                    "deviation": float(row["value"] - mean_val),
                    "geo_name": str(geo_name),
                })

    return anomalies_report


def calculate_market_economic_volume(df: pd.DataFrame) -> dict:
    """Calculates total economic volume (€) in wholesale market by aligning demand (5-min) and SPOT price (15-min) into 1-hour intervals.

    Args:
        df (pd.DataFrame): Validated market dataframe containing ESIOS fields.

    Returns:
        dict: Summary of market volume metrics (total euros, peak spend hour, VWAP).
    """
    # Filter for Real Demand (1293, Peninsula 8741) and Spot Price (600, Spain 3)
    demand_mask = (df["indicator_id"] == 1293) & (df["geo_id"] == 8741)
    spot_mask = (df["indicator_id"] == 600) & (df["geo_id"] == 3)

    demand_df = df[demand_mask].copy()
    spot_df = df[spot_mask].copy()

    if demand_df.empty or spot_df.empty:
        return {}

    demand_df["datetime"] = pd.to_datetime(demand_df["datetime"])
    spot_df["datetime"] = pd.to_datetime(spot_df["datetime"])

    # Hourly resampling (1h)
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

    merged = pd.merge(demand_hourly, spot_hourly, on="datetime", how="inner")

    if merged.empty:
        return {}

    merged["hourly_volume_eur"] = (merged["demand_mwh"] * merged["spot_price_eur_mwh"])

    total_volume_eur = float(merged["hourly_volume_eur"].sum())
    total_energy_mwh = float(merged["demand_mwh"].sum())

    max_spend_row = merged.loc[merged["hourly_volume_eur"].idxmax()]
    volume_weighted_avg_price = (total_volume_eur / total_energy_mwh if total_energy_mwh > 0 else 0.0)

    return {
        "total_volume_eur": total_volume_eur,
        "total_energy_mwh": total_energy_mwh,
        "weighted_avg_price": volume_weighted_avg_price,
        "peak_spend_hour": max_spend_row["datetime"],
        "peak_spend_eur": float(max_spend_row["hourly_volume_eur"]),
        "peak_spend_demand_mw": float(max_spend_row["demand_mwh"]),
        "peak_spend_price_eur": float(max_spend_row["spot_price_eur_mwh"]),
    }