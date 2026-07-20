import os
from zoneinfo import ZoneInfo
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from src.constants import DEFAULT_PROCESSED_DIR, DEMAND_COLOR_PALETTE, DEMAND_TRANSLATIONS

def plot_energy_demand(df: pd.DataFrame, output_dir: str = DEFAULT_PROCESSED_DIR) -> str:
    """Generates a multi-line plot of electricity demand over time.
    Separates different demand types by the 'name' column.

    Args:
        df (pd.DataFrame): The validated dataset containing 'datetime', 'value', and 'name'.
        output_dir (str): Directory where the plot image will be saved.

    Returns:
        str: The file path where the plot was saved.
    """
    print("\n📉 Generating multi-line electricity demand visualization...")

    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 Created output directory at: '{output_dir}'")

    # Dynamic Filename Generation based on Dataset Temporal Range
    min_dt = df["datetime"].min()
    max_dt = df["datetime"].max()

    # Format timestamps: include hours if range is within the same day
    if min_dt.date() == max_dt.date():
        start_str = min_dt.strftime("%Y%m%d_%H%M")
        end_str = max_dt.strftime("%Y%m%d_%H%M")
    else:
        start_str = min_dt.strftime("%Y%m%d")
        end_str = max_dt.strftime("%Y%m%d")

    filename = f"plot_energy_demand_{start_str}_to_{end_str}.png"
    output_path = os.path.join(output_dir, filename)

    # Setup the plot figure size and style
    plt.figure(figsize=(14, 7))
    plt.style.use('seaborn-v0_8-whitegrid')  # Clean and modern grid style

    # Group by 'name' and plot each line separately
    for name_spanish, group_df in df.groupby("name"):
        # Sort by datetime just in case the data is shuffled
        group_sorted = group_df.sort_values("datetime")

        # Get color configuration from constants or apply the fallback color
        config = DEMAND_COLOR_PALETTE.get(name_spanish, DEMAND_COLOR_PALETTE["default"])

        # Dynamic label fetched from the centralized DEMAND_TRANSLATIONS dictionary
        english_label = DEMAND_TRANSLATIONS.get(name_spanish, name_spanish)

        plt.plot(
            group_sorted["datetime"], 
            group_sorted["value"], 
            color=config["color"], 
            linewidth=2, 
            label=english_label
        )

    # Format titles and labels
    plt.title("Spanish Peninsula Electricity Demand Comparison", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Time (HH:MM / Date)", fontsize=11, labelpad=10)
    plt.ylabel("Electricity Demand (MW)", fontsize=11, labelpad=10)

    # Advanced date formatting for the X-axis to keep it readable
    ax = plt.gca()
    spain_tz = ZoneInfo("Europe/Madrid")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M\n%Y-%m-%d', tz=spain_tz))

    # Adjust spacing automatically so labels don't overlap
    plt.gcf().autofmt_xdate()

    # Add legend and optimize layout
    plt.legend(loc="upper right", frameon=True, shadow=True, facecolor="white")
    plt.tight_layout()

    # Save the plot to the output directory
    plt.savefig(output_path, dpi=300)  # High resolution (300 DPI)
    plt.close()  # Close the figure to free up memory

    print(f"✅ Multi-line visualization successfully saved to: '{output_path}'")
    return output_path