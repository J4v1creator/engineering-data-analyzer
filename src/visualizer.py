import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

def plot_energy_demand(df: pd.DataFrame, output_dir: str = "data/processed") -> str:
    """
    Generates a line plot of electricity demand over time and saves it as a PNG file.
    
    Args:
        df (pd.DataFrame): The validated dataset containing 'datetime' and 'value'.
        output_dir (str): Directory where the plot image will be saved. Default is 'output'.
        
    Returns:
        str: The file path where the plot was saved.
    """
    print("\n📉 Generating electricity demand visualization...")

    # 1. Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 Created output directory at: '{output_dir}'")

    # 2. Setup the plot figure size and style
    plt.figure(figsize=(12, 6))
    plt.style.use('seaborn-v0_8-whitegrid')  # Clean and modern grid style

    # 3. Plot the data
    # X axis: datetime, Y axis: demand value
    plt.plot(df["datetime"], df["value"], color="#1f77b4", linewidth=2, label="Real-time Demand")

    # 4. Format titles and labels
    plt.title("Spanish Peninsula Electricity Demand (Real-time)", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Time (HH:MM / Date)", fontsize=11, labelpad=10)
    plt.ylabel("Electricity Demand (MW)", fontsize=11, labelpad=10)

    # 5. Advanced date formatting for the X-axis to keep it readable
    ax = plt.gca()
    # Format ticks to show Hours:Minutes
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M\n%Y-%m-%d'))
    # Adjust spacing automatically so labels don't overlap
    plt.gcf().autofmt_xdate()

    plt.legend(loc="upper right")
    plt.tight_layout()  # Adjusts margins perfectly

    # 6. Save the plot to the output directory
    output_path = os.path.join(output_dir, "energy_demand_plot.png")
    plt.savefig(output_path, dpi=300)  # High resolution (300 DPI)
    plt.close()  # Close the figure to free up memory

    print(f"✅ Visualization successfully saved to: '{output_path}'")
    return output_path