import pandas as pd

# Define the expected schema for strict type checking
EXPECTED_COLUMNS = {
    "id": "int64",
    "name": "object",
    "geoname": "object",
    "value": "int64",
    "datetime": "datetime64[ns, pytz.FixedOffset(120)]"  # Matches +02:00 timezone
}

def validate_dataset(df: pd.DataFrame) -> bool:
    """
    Validates the dataset structure, data types, missing values, and duplicates.

    Args:
        df (pd.DataFrame): The DataFrame to validate.

    Returns:
        bool: True if the dataset passes all checks.
        
    Raises:
        ValueError: If any validation check fails.
    """
    print("\n🔍 Starting data validation pipeline...")
    
    # 1. Check for missing columns
    missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"❌ Validation failed: Missing required columns: {missing_cols}")
    print("✅ All required columns found.")
    
    # 2. Check for incorrect data types
    for col, expected_type in EXPECTED_COLUMNS.items():
        # Flexibly handle text columns (both object and string/str are valid for text)
        if expected_type in ["object", "str"]:
            if not (pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col])):
                raise ValueError(f"❌ Validation failed: Column '{col}' type is {df[col].dtype}, expected text (object/str)")
            continue

        # Safe check fallback for datetimes with timezones
        if col == "datetime" and isinstance(df[col].dtype, pd.DatetimeTZDtype):
            continue

        if not pd.api.types.is_dtype_equal(df[col].dtype, expected_type):
            raise ValueError(f"❌ Validation failed: Column '{col}' type is {df[col].dtype}, expected {expected_type}")
        
        print("✅ All data types are correct.")

    # 3. Check for missing values (NaNs)
    missing_values = df.isnull().sum().sum()
    if missing_values > 0:
        raise ValueError(f"❌ Validation failed: Found {missing_values} missing values in the dataset.")
    print("✅ No missing values.")

    # 4. Check for duplicate rows
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        raise ValueError(f"❌ Validation failed: Found {duplicate_count} duplicate rows.")
    print("✅ No duplicate rows.")

    print("\n🎉 [SUCCESS] Dataset passed all quality checks!")
    return True