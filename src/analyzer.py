import pandas as pd

def calculate_energy_statistics(df: pd.DataFrame) -> dict:
    """
    Calculates key statistical metrics for the electricity demand column ('value').
    
    Args:
        df (pd.DataFrame): The validated energy dataset.
        
    Returns:
        dict: A dictionary containing mean, median, max, min, and standard deviation.
    """
    print("\n📊 Analyzing energy consumption metrics...")
    
    # Extract the 'value' column (electricity demand in MW)
    values = df["value"]
    
    # Calculate statistics using native Pandas methods
    stats = {
        "mean": float(values.mean()),
        "median": float(values.median()),
        "max": int(values.max()),
        "min": int(values.min()),
        "std_dev": float(values.std())
    }
    
    # Print a clean, professional summary in the terminal
    print("\n--- Statistical Summary (Demand in MW) ---")
    print(f"🔹 Mean (Average):     {stats['mean']:.2f} MW")
    print(f"🔹 Median:             {stats['median']:.2f} MW")
    print(f"🔹 Maximum Demand:     {stats['max']} MW")
    print(f"🔹 Minimum Demand:     {stats['min']} MW")
    print(f"🔹 Standard Deviation: {stats['std_dev']:.2f} MW")
    print("------------------------------------------")
    
    return stats