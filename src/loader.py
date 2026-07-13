import pandas as pd
import os

def load_csv_data(file_path: str) -> pd.DataFrame:
    """Loads an energy dataset from a CSV file into a Pandas DataFrame.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        pd.DataFrame: The loaded dataset.
        
    Raises:
        FileNotFoundError: If the file does not exist at the specified path.
        ValueError: If the file is empty or has parsing issues.
        RuntimeError: If an unexpected error occurs while reading the file.
    """
    print(f"📂 Attempting to load data from: {file_path}")

    # Pre-validation: Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file does not exist at the specified path: '{file_path}'")
    
    try:
        # Read CSV tailored to REE data structure (semi-colon separated)
        df = pd.read_csv(file_path, sep=";", parse_dates=["datetime"])

        # Post-validation: Check if the DataFrame is empty
        if df.empty:
            raise ValueError(f"The file '{file_path}' is empty.")

        print(f"✅ Successfully loaded {len(df)} rows.")
        return df
    
    except pd.errors.ParserError as e:
        raise ValueError(f"Formatting error while parsing CSV. Check delimiters: {e}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred while reading the file: {e}")