import pandas as pd
from config.settings import EXPECTED_COLUMNS

def validate_dataset(df: pd.DataFrame) -> bool:
    """Validates dataset structure, data types, missing values, and business key uniqueness.

    Ensures data integrity for multi-region indicators by checking uniqueness across
    the composite key (id, datetime, geo_id).

    Args:
        df (pd.DataFrame): The DataFrame to validate.

    Returns:
        bool: True if the dataset passes all validation checks.

    Raises:
        ValueError: If any validation check fails or if the dataset is empty.
    """
    print("\n🔍 Starting data validation pipeline...")

    # Validate empty dataset
    if df.empty:
        raise ValueError("❌ Validation failed: Provided DataFrame is empty.")

    # Validate missing columns
    missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"❌ Validation failed: Missing required columns: {missing_cols}")
    print("✅ All required columns found.")

    # Validate data types
    for col, expected_type in EXPECTED_COLUMNS.items():
        # Flexible handling for string types (object or string/str)
        if expected_type in ["object", "str"]:
            if not (pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col])):
                raise ValueError(f"❌ Validation failed: Column '{col}' type is {df[col].dtype}, expected text (object/str)")
            continue

        # Flexible check for integer types (int64, int32, etc.)
        if expected_type == "int64":
            if not pd.api.types.is_integer_dtype(df[col]):
                raise ValueError(f"❌ Validation failed: Column '{col}' type is {df[col].dtype}, expected integer")
            continue

        # Flexible check for numeric floats
        if expected_type == "float64":
            if not pd.api.types.is_float_dtype(df[col]):
                raise ValueError(f"❌ Validation failed: Column '{col}' type is {df[col].dtype}, expected float")
            continue

        # Flexible check for timezone-aware datetime columns
        # Flexible check for timezone-aware or naive datetime columns
        if col == "datetime":
            if not (isinstance(df[col].dtype, pd.DatetimeTZDtype) or pd.api.types.is_datetime64_any_dtype(df[col])):
                raise ValueError(f"❌ Validation failed: Column '{col}' type is {df[col].dtype}, expected datetime")
            continue

        if not pd.api.types.is_dtype_equal(df[col].dtype, expected_type):
            raise ValueError(f"❌ Validation failed: Column '{col}' type is {df[col].dtype}, expected {expected_type}")

    print("✅ All data types are correct.")

    # Check for missing values (NaNs)
    missing_values = df.isnull().sum().sum()
    if missing_values > 0:
        raise ValueError(f"❌ Validation failed: Found {missing_values} missing values in the dataset.")
    print("✅ No missing values.")

    # Check for duplicate entries based on composite domain key (indicator id, datetime, geo_id)
    composite_key = ["id", "datetime", "geo_id"]
    duplicate_count = df.duplicated(subset=composite_key).sum()
    if duplicate_count > 0:
        raise ValueError(f"❌ Validation failed: Found {duplicate_count} duplicate records for key combination {composite_key}.")
    print("✅ No duplicate records for composite key (id, datetime, geo_id).")

    print("\n🎉 [SUCCESS] Dataset passed all quality checks!")
    return True