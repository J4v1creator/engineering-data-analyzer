import os
from datetime import datetime
import pandas as pd
from src.constants import DEFAULT_PROCESSED_DIR, DEMAND_TRANSLATIONS

def generate_text_report(df: pd.DataFrame, stats: dict, comp_stats: dict = None, anomalies: dict = None, start_dt: datetime = None,  end_dt: datetime = None, output_dir: str = DEFAULT_PROCESSED_DIR) -> str:
    """Generates a structured, professional text report summarizing the full
    statistical insights for each specific type of electricity demand.

    Args:
        df (pd.DataFrame): The validated dataset.
        stats (dict): The dictionary of statistics calculated by the analyzer.
        comp_stats (dict, optional): The advanced comparison statistics. Defaults to None.
        anomalies (dict, optional): The dictionary of detected anomalies. Defaults to None.
        start_dt (datetime, optional): The start datetime of the analyzed range.
        end_dt (datetime, optional): The end datetime of the analyzed range.
        output_dir (str): Directory where the report will be saved.

    Returns:
        str: The file path of the generated report.

    Raises:
        RuntimeError: If the system fails to write the report file.
    """
    print("\n📄 Generating automated text report...")

    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get the current timestamp for the analysis metadata
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Format the analysis period label for reporting and visualization purposes
    if start_dt and end_dt:
        analysis_period = f"{start_dt.strftime('%Y-%m-%d %H:%M')} to {end_dt.strftime('%Y-%m-%d %H:%M')}"
    else:
        analysis_period = "Full Dataset Range (Unfiltered)"

    # Gather dimensions
    num_rows, num_cols = df.shape
    column_names = ', '.join(df.columns)

    # Report Header and Metadata
    report_content = f"""==================================================
ENERGY CONSUMPTION ANALYSIS REPORT (AUTOMATED)
==================================================
Date of Analysis:  {current_time}
Analysis Period (Data): {analysis_period}
Data Source:       Red Eléctrica de España (REE)

--------------------------------------------------
1. DATASET METADATA
--------------------------------------------------
- Total Rows:       {num_rows}
- Total Columns:    {num_cols}
- Column Names:     {column_names}
- Selected Range:   [{analysis_period}]

--------------------------------------------------
2. STATISTICAL SUMMARY (DEMAND IN MW)
--------------------------------------------------"""

    # Iterate over the statistics and add them directly to the content
    for demand_name in pd.unique(df["name"]):
        if demand_name in stats:
            metrics = stats[demand_name]

            # Translate labels dynamically from the constants module
            english_name = DEMAND_TRANSLATIONS.get(demand_name, demand_name)

            report_content += f"""
--- {english_name.upper()} ---
- Maximum Demand:  {metrics['max']} MW (At: {metrics['peak_time']})
- Minimum Demand:  {metrics['min']} MW
- Mean (Average):  {metrics['mean']:.2f} MW
- Median:          {metrics['median']:.2f} MW
- Std. Deviation:  {metrics['std_dev']:.2f} MW
"""

    # Advanced Model Comparison Section (Injected dynamically if data is available)
    if comp_stats:
        # Translate the names of the two models compared
        model_a_en = DEMAND_TRANSLATIONS.get(comp_stats["model_a"], comp_stats["model_a"])
        model_b_en = DEMAND_TRANSLATIONS.get(comp_stats["model_b"], comp_stats["model_b"])

        report_content += f"""
--------------------------------------------------
3. ADVANCED MODEL COMPARISON
--------------------------------------------------
Comparison Baseline (Model A): {model_a_en}
Compared Target     (Model B): {model_b_en}

- Mean Difference (A - B):      {comp_stats['mean_difference']:.2f} MW
- Maximum Absolute Deviation:   {abs(comp_stats['max_difference_value'])} MW
    ↳ Occurred At:                {comp_stats['max_difference_time']}
    ↳ Directional Error (A - B):   {comp_stats['max_difference_value']} MW
- Mean Absolute Pct. Error:     {comp_stats['mape']:.2f}%
- Pearson Correlation (r):      {comp_stats['correlation']:.4f}
"""

    # Statistical Anomaly Detection Section
    report_content += f"""
--------------------------------------------------
4. STATISTICAL ANOMALY DETECTION (Z-SCORE > 2.0)
--------------------------------------------------"""

    if anomalies:
        for demand_name, issues in anomalies.items():
            english_name = DEMAND_TRANSLATIONS.get(demand_name, demand_name)
            report_content += f"\n• {english_name.upper()}:"
            for issue in issues:
                report_content += f"\n  ↳ [{issue['type']}] At {issue['datetime']} -> {issue['value']} MW (Deviation: {issue['deviation']:.2f} MW)"
            report_content += "\n"
    else:
        report_content += "\n- No statistical anomalies detected. All data points are within expected variance limits.\n"

    # Report Footer
    report_content += """
==================================================
Report successfully generated by Data Pipeline.
==================================================
"""

    # Save the report to a file
    output_path = os.path.join(output_dir, "energy_analysis_report.txt")
    try:
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(report_content)
        print(f"✅ Report successfully saved to: '{output_path}'")
        return output_path
    except IOError as e:
        raise RuntimeError(f"Failed to write the report file: {e}")