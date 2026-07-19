import pandas as pd
from src.constants import EXPECTED_COLUMNS

def validate_dataset(df: pd.DataFrame) -> bool:
    """Validates the dataset structure, data types, missing values, and duplicates.

    Args:
        df (pd.DataFrame): The DataFrame to validate.

    Returns:
        bool: True if the dataset passes all checks.

    Raises:
        ValueError: If any validation check fails.
    """
    print("\n🔍 Starting data validation pipeline...")
    
    # Validate missing columns
    missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"❌ Validation failed: Missing required columns: {missing_cols}")
    print("✅ All required columns found.")
    
    # Validate data types
    for col, expected_type in EXPECTED_COLUMNS.items():
        # Handle text columns flexibly (both object and string/str are valid)
        if expected_type in ["object", "str"]:
            if not (pd.api.types.is_object_dtype(df[col])
                    or pd.api.types.is_string_dtype(df[col])):
                    raise ValueError(f"❌ Validation failed: Column '{col}' type is {df[col].dtype}, expected text (object/str)")
            continue

        # Fallback check for datetimes with timezones
        if col == "datetime" and isinstance(df[col].dtype, pd.DatetimeTZDtype):
            continue

        if not pd.api.types.is_dtype_equal(df[col].dtype, expected_type):
            raise ValueError(f"❌ Validation failed: Column '{col}' type is {df[col].dtype}, expected {expected_type}")
        
    print("✅ All data types are correct.")

    # Check for missing values (NaNs)
    missing_values = df.isnull().sum().sum()
    if missing_values > 0:
        raise ValueError(f"❌ Validation failed: Found {missing_values} missing values in the dataset.")
    print("✅ No missing values.")

    # Check for duplicate rows
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        raise ValueError(f"❌ Validation failed: Found {duplicate_count} duplicate rows.")
    print("✅ No duplicate rows.")

    print("\n🎉 [SUCCESS] Dataset passed all quality checks!")
    return True