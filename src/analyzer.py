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