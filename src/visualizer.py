import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

def plot_energy_demand(df: pd.DataFrame, output_dir: str = "data/processed") -> str:
    """
    Generates a multi-line plot of electricity demand over time, 
    separating different demand types by the 'name' column.
    
    Args:
        df (pd.DataFrame): The validated dataset containing 'datetime', 'value', and 'name'.
        output_dir (str): Directory where the plot image will be saved.
        
    Returns:
        str: The file path where the plot was saved.
    """
    print("\n📉 Generating multi-line electricity demand visualization...")

    # 1. Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 Created output directory at: '{output_dir}'")

    # 2. Setup the plot figure size and style
    plt.figure(figsize=(14, 7))
    plt.style.use('seaborn-v0_8-whitegrid')  # Clean and modern grid style

    # 3. Single Source of Truth for Translation and Color Mapping
    demand_config = {
        "Demanda real": {"label": "Real Demand", "color": "#1f77b4"},
        "Demanda prevista": {"label": "Forecasted Demand", "color": "#ff7f0e"},
        "Demanda programada": {"label": "Scheduled Demand", "color": "#2ca02c"},
        "Demanda Programada Total Peninsular": {"label": "Total Peninsular Scheduled Demand", "color": "#d62728"}
    }

    # 4. Group by 'name' and plot each line separately
    for name_spanish, group_df in df.groupby("name"):
        # Sort by datetime just in case the data is shuffled
        group_sorted = group_df.sort_values("datetime")

        # Get configuration or use fallbacks for unexpected new categories
        config = demand_config.get(name_spanish, {"label": name_spanish, "color": "#7f7f7f"})

        plt.plot(
            group_sorted["datetime"], 
            group_sorted["value"], 
            color=config["color"], 
            linewidth=2, 
            label=config["label"]
        )

    # 5. Format titles and labels
    plt.title("Spanish Peninsula Electricity Demand Comparison", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Time (HH:MM / Date)", fontsize=11, labelpad=10)
    plt.ylabel("Electricity Demand (MW)", fontsize=11, labelpad=10)

    # 6. Advanced date formatting for the X-axis to keep it readable
    ax = plt.gca()
    # Format ticks to show Hours:Minutes
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M\n%Y-%m-%d'))
    # Adjust spacing automatically so labels don't overlap
    plt.gcf().autofmt_xdate()

    # 7. Add legend and optimize layout
    # Place legend inside the plot or adjust to fit nicely
    plt.legend(loc="upper right", frameon=True, shadow=True, facecolor="white")
    plt.tight_layout()

    # 7. Save the plot to the output directory
    output_path = os.path.join(output_dir, "energy_demand_plot.png")
    plt.savefig(output_path, dpi=300)  # High resolution (300 DPI)
    plt.close()  # Close the figure to free up memory

    print(f"✅ Multi-line visualization successfully saved to: '{output_path}'")
    return output_path