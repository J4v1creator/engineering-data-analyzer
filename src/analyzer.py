"""Core mathematics, price spread evaluation, market volume calculation, and Z-Score anomaly modeling."""

import pandas as pd

from config.settings import DEFAULT_ANOMALY_THRESHOLD
from src.utils import translate_indicator


def calculate_demand_statistics(df_demands: pd.DataFrame, selected_demands: list[int] | None = None) -> dict[str, dict[str, float | str]]:
    """Calculates power demand statistics (MW).

    Args:
        df_demands (pd.DataFrame): Filtered DataFrame containing demand indicators.
        selected_demands (list[int] | None): List of specific demand indicator IDs to analyze.

    Returns:
        dict[str, dict[str, float | str]]: Statistical summary per demand series.
    """
    if df_demands.empty:
        return {}

    print("\n🔍 Calculating power demand statistics...")
    
    # Identify ID column dynamically and filter by selected demand IDs
    id_col = "indicator_id" if "indicator_id" in df_demands.columns else "id"
    if selected_demands:
        df_demands = df_demands[df_demands[id_col].isin(selected_demands)]

    if df_demands.empty:
        return {}

    has_multiple_geos = df_demands["geo_id"].nunique() > 1
    stats = {}

    for (ind_id, geo_id), group in df_demands.groupby([id_col, "geo_id"], sort=False):
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
    """Calculates market price statistics (€/MWh), including spreads and low-price hours.

    Args:
        df_prices (pd.DataFrame): Filtered DataFrame containing price indicators.
        selected_prices (list[int] | None): List of specific price indicator IDs to analyze.

    Returns:
        dict: Specialized market statistics per price series.
    """
    stats = {}
    if df_prices.empty:
        return stats

    print("\n🔍 Calculating energy price statistics...")
    id_col = "indicator_id" if "indicator_id" in df_prices.columns else "id"

    if selected_prices:
        df_prices = df_prices[df_prices[id_col].isin(selected_prices)]

    has_multiple_geos = df_prices["geo_id"].nunique() > 1
    for (price_id, geo_id), df_sub in df_prices.groupby([id_col, "geo_id"], sort=False):
        if df_sub.empty:
            continue

        series_name = translate_indicator(indicator_id=price_id, geo_id=geo_id, show_geo=has_multiple_geos)

        max_val = df_sub["value"].max()
        max_row = df_sub.loc[df_sub["value"].idxmax()]
        min_val = df_sub["value"].min()
        min_row = df_sub.loc[df_sub["value"].idxmin()]

        max_time = max_row["datetime"]
        min_time = min_row["datetime"]
        max_str = max_time.strftime("%Y-%m-%d %H:%M") if hasattr(max_time, "strftime") else str(max_time)
        min_str = min_time.strftime("%Y-%m-%d %H:%M") if hasattr(min_time, "strftime") else str(min_time)

        stats[series_name] = {
            "max": float(max_val),
            "max_time": max_str,
            "min": float(min_val),
            "min_time": min_str,
            "spread": float(max_val - min_val),
            "zero_low_price_hours": int((df_sub["value"] <= 5.0).sum()),
            "mean": float(df_sub["value"].mean()),
        }

        print(f"📊 Price stats calculated for: {series_name}")

    return stats


def compare_demand_models(df: pd.DataFrame, targets: tuple[str, str] | None = None) -> dict[str, str | float | int]:
    """Performs comparative analysis dynamically between two selected demand series.

    Args:
        df (pd.DataFrame): Filtered energy DataFrame.
        targets (tuple[str, str] | None): Pair of demand series names (model_a, model_b).

    Returns:
        dict[str, str | float | int]: Comparative metrics dictionary or empty dict if invalid.
    """
    if not targets or len(targets) != 2:
        return {}

    model_a, model_b = targets

    # Validate presence of both models in dataset
    if model_a not in df["name"].values or model_b not in df["name"].values:
        print(f"⚠️ Advanced comparison skipped: One or both targets ('{model_a}', '{model_b}') are not present.")
        return {}

    id_col = "indicator_id" if "indicator_id" in df.columns else "id"
    id_a = df[df["name"] == model_a][id_col].iloc[0]
    id_b = df[df["name"] == model_b][id_col].iloc[0]

    model_a_en = translate_indicator(indicator_id=id_a)
    model_b_en = translate_indicator(indicator_id=id_b)

    print(f"\n🧠 Running advanced comparative analysis between '{model_a_en}' and '{model_b_en}'...")

    df_work = df.copy()
    if "series_id" not in df_work.columns:
        df_work["series_id"] = df_work["name"]

    pivoted_df = df_work.pivot_table(index="datetime", columns="series_id", values="value", aggfunc="first")

    rows_before = len(pivoted_df)
    pivoted_df = pivoted_df.dropna(subset=[model_a, model_b])
    rows_after = len(pivoted_df)

    if rows_before != rows_after:
        print(f"ℹ️ {rows_before - rows_after} timestamps excluded due to missing values in target series.")

    series_a = pivoted_df[model_a]
    series_b = pivoted_df[model_b]

    # Error and correlation metrics
    pivoted_df["difference"] = series_a - series_b
    pivoted_df["abs_difference"] = pivoted_df["difference"].abs()

    max_diff_idx = pivoted_df["abs_difference"].idxmax()
    max_diff_time = max_diff_idx.strftime("%Y-%m-%d %H:%M") if hasattr(max_diff_idx, "strftime") else str(max_diff_idx)
    max_diff_value = float(pivoted_df.loc[max_diff_idx, "difference"])

    mape = float((pivoted_df["abs_difference"] / series_a.replace(0, pd.NA)).mean() * 100)
    correlation = float(series_a.corr(series_b))

    return {
        "model_a": model_a_en,
        "model_b": model_b_en,
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
    print("\n🔍 Scanning for statistical anomalies in dataset series...")
    anomalies_report = {}
    has_multiple_geos = df["geo_id"].nunique() > 1
    id_col = "indicator_id" if "indicator_id" in df.columns else "id"

    for (ind_id, geo_id), group_df in df.groupby([id_col, "geo_id"]):
        if len(group_df) < 3:
            continue

        mean_val = group_df["value"].mean()
        std_dev = group_df["value"].std()

        if std_dev == 0 or pd.isna(std_dev):
            continue

        z_scores = (group_df["value"] - mean_val) / std_dev
        anomaly_rows = group_df[z_scores.abs() > threshold]

        series_label = translate_indicator(indicator_id=ind_id, geo_id=geo_id, show_geo=has_multiple_geos)

        geo_name = group_df["geo_name"].iloc[0] if "geo_name" in group_df.columns else "Unknown"

        if not anomaly_rows.empty:
            anomalies_report[series_label] = []
            for _, row in anomaly_rows.iterrows():
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
    """Calculates total economic volume (€) in wholesale market by aligning demand (5-min) and SPOT price (15-min) into 1-hour intervals.

    Args:
        df (pd.DataFrame): Validated market dataframe containing ESIOS fields.

    Returns:
        dict: Summary of market volume metrics (total euros, peak spend hour, VWAP).
    """
    id_col = "indicator_id" if "indicator_id" in df.columns else "id"

    # Filter for Real Demand (1293, Peninsula 8741) and Spot Price (600, Spain 3)
    demand_mask = (df[id_col] == 1293) & (df["geo_id"] == 8741)
    spot_mask = (df[id_col] == 600) & (df["geo_id"] == 3)

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