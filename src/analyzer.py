import pandas as pd

def calculate_energy_statistics(df: pd.DataFrame) -> dict:
    """
    Calculates key statistical metrics (max, min, mean) broken down
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

def compare_demand_models(df: pd.DataFrame) -> dict:
    """
    Performs advanced comparative analysis dynamically between the first two 
    selected electricity demand types available in the filtered dataset.

    Args:
        df (pd.DataFrame): The filtered energy DataFrame.

    Returns:
        dict: A dictionary containing comparative metrics, or empty if fewer than two types are available.
    """
    # 1. Get the unique demand names present in the current filtered data
    available_types = list(df["name"].unique())

    # 2. Guard clause: If there are fewer than 2 demands selected, we cannot compare
    if len(available_types) < 2:
        print("\nℹ️ Advanced comparison skipped: At least 2 demand types must be selected.")
        return {}

    # 3. Take the first two demand types dynamically
    model_a = available_types[0]
    model_b = available_types[1]

    print(f"\n🧠 Running advanced comparative analysis between '{model_a}' and '{model_b}'...")

    # 4. Pivot and align data by datetime
    pivoted_df = df.pivot(index="datetime", columns="name", values="value").dropna()

    series_a = pivoted_df[model_a]
    series_b = pivoted_df[model_b]

    # 5. Calculate differences (Model A - Model B)
    pivoted_df["difference"] = series_a - series_b
    pivoted_df["abs_difference"] = pivoted_df["difference"].abs()

    # 6. Find the exact timestamp of the maximum absolute deviation
    max_diff_idx = pivoted_df["abs_difference"].idxmax()
    max_diff_time = max_diff_idx.strftime("%Y-%m-%d %H:%M")
    max_diff_value = int(pivoted_df.loc[max_diff_idx, "difference"])

    # 7. Calculate Mean Absolute Percentage Error (MAPE) assuming Model A is the baseline/real
    mape = float((pivoted_df["abs_difference"] / series_a).mean() * 100)

    # 8. Calculate Pearson Correlation Coefficient
    correlation = float(series_a.corr(series_b))

    # 9. Package metrics along with the names of the compared models
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