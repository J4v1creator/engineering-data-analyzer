"""Structural verification and timezone-aware datatype firewall for ESIOS datasets."""

import pandas as pd

from config.settings import EXPECTED_COLUMNS


def validate_dataset(df: pd.DataFrame) -> bool:
    """Validates dataset structure, data types, missing values, and business key uniqueness.
    Ensures data integrity for multi-region indicators by checking uniqueness across the composite key (indicator_id/id, datetime, geo_id).

    Args:
        df (pd.DataFrame): The DataFrame to validate.

    Returns:
        bool: True if the dataset passes all validation checks.

    Raises:
        ValueError: If any validation check fails or if the dataset is empty.
    """
    print("\n🔍 Starting data validation pipeline...")

    # Step 1: Validate empty dataset
    if df.empty:
        raise ValueError("❌ Validation failed: Provided DataFrame is empty.")

    # Step 2: Validate missing columns (allowing 'indicator_id' or 'id')
    required_cols = list(EXPECTED_COLUMNS.keys())
    missing_cols = []

    for col in required_cols:
        if col == "indicator_id" and "indicator_id" not in df.columns and "id" in df.columns:
            continue
        if col not in df.columns:
            missing_cols.append(col)

    if missing_cols:
        raise ValueError(f"❌ Validation failed: Missing required columns: {missing_cols}")

    print("✅ All required columns found.")

    # Step 3: Validate data types
    for col, expected_type in EXPECTED_COLUMNS.items():
        target_col = "id" if (col == "indicator_id" and "id" in df.columns and "indicator_id" not in df.columns) else col
        # Flexible handling for text / string types
        if expected_type in ["object", "str"]:
            if not (pd.api.types.is_object_dtype(df[target_col]) or pd.api.types.is_string_dtype(df[target_col])):
                raise ValueError(f"❌ Validation failed: Column '{target_col}' type is {df[target_col].dtype}, expected text")
            continue

        # Flexible check for integer types
        if expected_type == "int64":
            if not pd.api.types.is_integer_dtype(df[target_col]):
                raise ValueError(f"❌ Validation failed: Column '{target_col}' type is {df[target_col].dtype}, expected integer")
            continue

        # Flexible check for float numeric types
        if expected_type == "float64":
            if not pd.api.types.is_float_dtype(df[target_col]):
                raise ValueError(f"❌ Validation failed: Column '{target_col}' type is {df[target_col].dtype}, expected float")
            continue

        # Flexible check for timezone-aware or naive datetime columns
        if target_col == "datetime":
            if not (isinstance(df[target_col].dtype, pd.DatetimeTZDtype) or pd.api.types.is_datetime64_any_dtype(df[target_col])):
                raise ValueError(f"❌ Validation failed: Column '{target_col}' type is {df[target_col].dtype}, expected datetime")
            continue

    print("✅ All data types are correct.")

    # Step 4: Check for missing values (NaNs)
    missing_values = df.isnull().sum().sum()
    if missing_values > 0:
        raise ValueError(f"❌ Validation failed: Found {missing_values} missing values in dataset.")
    print("✅ No missing values.")

    # # Step 5: Check for duplicate entries based on composite key
    composite_key = ["indicator_id", "datetime", "geo_id"]
    duplicate_count = df.duplicated(subset=composite_key).sum()
    if duplicate_count > 0:
        raise ValueError(f"❌ Validation failed: Found {duplicate_count} duplicate records for key combination {composite_key}.")

    print("✅ No duplicate records for composite key (indicator_id, datetime, geo_id).")

    print("🎉 [SUCCESS] Dataset passed all quality checks!")
    return True