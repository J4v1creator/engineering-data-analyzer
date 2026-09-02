"""Core mathematics, price spread evaluation, market volume calculation, and Z-Score anomaly modeling."""

import pandas as pd

from config.settings import (
    DEFAULT_ANOMALY_THRESHOLD,
    GLOBAL_GEO_ORDER,
)
from src.utils import format_datetime, translate_full_indicator, translate_indicator


def calculate_demand_statistics(df_demands: pd.DataFrame, selected_demands: list[int] | None = None) -> dict[str, dict[str, float | str]]:
    """Calculates power demand statistics (MW) sorted by configuration priority.

    Args:
        df_demands (pd.DataFrame): Filtered DataFrame containing demand indicators.
        selected_demands (list[int] | None): List of specific demand indicator IDs to analyze.

    Returns:
        dict[str, dict[str, float | str]]: Statistical summary per demand series.
    """
    if df_demands.empty or not selected_demands:
        return {}

    print("\n🔍 Calculating power demand statistics...")

    # Use the selected IDs directly
    df_filtered = df_demands[df_demands["indicator_id"].isin(selected_demands)].copy()

    if df_filtered.empty:
        return {}

    # Ensure categorical ordering based on selected IDs
    df_filtered["indicator_id"] = pd.Categorical(df_filtered["indicator_id"], categories=selected_demands, ordered=True)
    df_filtered = df_filtered.sort_values("indicator_id")

    has_multiple_geos = df_filtered["geo_id"].nunique() > 1
    stats = {}

    # Grouping with sort=False preserves the categorical order applied above
    for (ind_id, geo_id), group in df_filtered.groupby(["indicator_id", "geo_id"], sort=False):
        values = group["value"]
        max_row = group.loc[values.idxmax()]
        label = translate_full_indicator(ind_id, geo_id, has_multiple_geos=has_multiple_geos)

        stats[label] = {
            "mean": float(values.mean()),
            "median": float(values.median()),
            "max": float(values.max()),
            "min": float(values.min()),
            "std_dev": float(values.std()) if len(values) > 1 else 0.0,
            "peak_time": format_datetime(max_row["datetime"]),
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
    if df_prices.empty or not selected_prices:
        return {}

    print("\n🔍 Calculating energy price statistics...")

    # Use the selected IDs directly
    df_filtered = df_prices[df_prices["indicator_id"].isin(selected_prices)].copy()

    if df_filtered.empty:
        return {}

    # Ensure categorical ordering based on selected IDs
    df_filtered["indicator_id"] = pd.Categorical(df_filtered["indicator_id"], categories=selected_prices, ordered=True)
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
        series_name = translate_full_indicator(price_id, geo_id, has_multiple_geos=has_multiple_geos)

        stats[series_name] = {
            "max": float(values.max()),
            "max_time": format_datetime(max_row["datetime"]),
            "min": float(values.min()),
            "min_time": format_datetime(min_row["datetime"]),
            "spread": float(values.max() - values.min()),
            "zero_low_price_hours": int((values <= 5.0).sum()),
        }

        print(f"📊 Price stats calculated for: {series_name}")

    return stats


def compare_demand_models(df_demands: pd.DataFrame, comparison_targets: tuple[int, int] | list[int] | None = None) -> dict[str, str | float | int]:
    """Performs comparative analysis dynamically between two selected demand series IDs.

    Args:
        df_demands (pd.DataFrame): Filtered demand DataFrame.
        targets (tuple[int, int] | list[int] | None): Pair of demand indicator_ids (id_a, id_b).

    Returns:
        dict[str, str | float | int]: Comparative metrics dictionary or empty dict if invalid.
    """
    if df_demands.empty or not comparison_targets:
        return None

    if not comparison_targets or len(comparison_targets) != 2:
        return {}

    id_baseline, id_target = comparison_targets[0], comparison_targets[1]

    # Validate presence of both indicator IDs in dataset
    if id_baseline not in df_demands["indicator_id"].values or id_target not in df_demands["indicator_id"].values:
        print(f"⚠️ Advanced comparison skipped: One or both target IDs ({id_baseline}, {id_target}) are not present.")
        return {}

    # Translate IDs to user-friendly names for printing/reporting
    baseline_name = translate_indicator(indicator_id=id_baseline)
    target_name = translate_indicator(indicator_id=id_target)

    print(f"\n🧠 Running advanced comparative analysis between '{baseline_name}' and '{target_name}'...")

    # Pivot table using indicator_id (guarantees numerical matching)
    pivoted_df = df_demands.pivot_table(
        index="datetime",
        columns="indicator_id",
        values="value",
        aggfunc="first"
    )

    rows_before = len(pivoted_df)
    pivoted_df = pivoted_df.dropna(subset=[id_baseline, id_target])
    rows_after = len(pivoted_df)

    # Check if there are valid rows to analyze
    if pivoted_df.empty:
        print("⚠️ Advanced comparison skipped: No overlapping valid data points found.")
        return {}

    if rows_before != rows_after:
        print(f"ℹ️ {rows_before - rows_after} timestamps excluded due to missing values in target series.")

    series_a = pivoted_df[id_baseline]
    series_b = pivoted_df[id_target]

    # Error and correlation metrics
    pivoted_df["difference"] = series_a - series_b
    pivoted_df["abs_difference"] = pivoted_df["difference"].abs()

    max_diff_idx = pivoted_df["abs_difference"].idxmax()
    max_diff_value = float(pivoted_df.loc[max_diff_idx, "difference"])

    mape = float((pivoted_df["abs_difference"] / series_a.replace(0, pd.NA)).mean() * 100)
    correlation = float(series_a.corr(series_b))

    return {
        "baseline_id": id_baseline,
        "target_id": id_target,
        "mean_difference": float(pivoted_df["difference"].mean()),
        "max_difference_value": max_diff_value,
        "max_difference_time": format_datetime(max_diff_idx),
        "mape": mape,
        "correlation": correlation,
    }


def detect_demand_anomalies(df_demands: pd.DataFrame, threshold: float = DEFAULT_ANOMALY_THRESHOLD) -> list[dict]:
    """Detects abnormal spikes or drops in demand series using Z-Score methodology.

    Returns:
        list[dict]: List of anomaly event records ready for display.
    """
    if df_demands.empty or "indicator_id" not in df_demands.columns:
        return []

    print("\n🔍 Scanning for statistical anomalies in energy demand series...")
    anomalies_list = []
    has_multiple_geos = df_demands["geo_id"].nunique() > 1 if "geo_id" in df_demands.columns else False

    # Agrupamos por indicador y geografía
    group_cols = ["indicator_id", "geo_id"] if "geo_id" in df_demands.columns else ["indicator_id"]

    for keys, group in df_demands.groupby(group_cols, observed=True):
        if len(group) < 3:
            continue

        ind_id = keys[0] if isinstance(keys, tuple) else keys
        geo_id = keys[1] if isinstance(keys, tuple) and len(keys) > 1 else 3

        mean_val = group["value"].mean()
        std_dev = group["value"].std()

        if std_dev == 0 or pd.isna(std_dev):
            continue

        # Cálculo vectorizado del Z-Score
        z_scores = (group["value"] - mean_val) / std_dev
        anomalies = group[z_scores.abs() > threshold].copy()

        if not anomalies.empty:
            series_label = translate_full_indicator(ind_id, geo_id, has_multiple_geos=has_multiple_geos)

            # Asignación vectorizada de columnas
            anomalies["Series"] = series_label
            anomalies["Timestamp"] = anomalies["datetime"].apply(format_datetime)
            anomalies["Value (MW)"] = anomalies["value"].round(2)
            anomalies["Type"] = anomalies["value"].apply(lambda v: "SPIKE 📈" if v > mean_val else "DROP 📉")
            anomalies["Deviation (MW)"] = (anomalies["value"] - mean_val).round(2)

            # Seleccionamos las columnas finales y las añadimos a la lista
            records = anomalies[["Timestamp", "Series", "Type", "Value (MW)", "Deviation (MW)"]].to_dict("records")
            anomalies_list.extend(records)

    return anomalies_list


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

    merged["hourly_volume_eur"] = merged["demand_mwh"] * merged["spot_price_eur_mwh"]

    total_volume_eur = float(merged["hourly_volume_eur"].sum())
    total_energy_mwh = float(merged["demand_mwh"].sum())

    max_spend_row = merged.loc[merged["hourly_volume_eur"].idxmax()]
    volume_weighted_avg_price = total_volume_eur / total_energy_mwh if total_energy_mwh > 0 else 0.0

    return {
        "total_volume_eur": total_volume_eur,
        "total_energy_mwh": total_energy_mwh,
        "weighted_avg_price": volume_weighted_avg_price,
        "peak_spend_hour": max_spend_row["datetime"],
        "peak_spend_eur": float(max_spend_row["hourly_volume_eur"]),
        "peak_spend_demand_mw": float(max_spend_row["demand_mwh"]),
        "peak_spend_price_eur": float(max_spend_row["spot_price_eur_mwh"]),
    }