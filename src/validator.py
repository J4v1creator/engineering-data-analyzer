"""Structural verification and timezone-aware datatype firewall for ESIOS datasets."""

import pandas as pd

from config.settings import EXPECTED_COLUMNS


def validate_dataset(df: pd.DataFrame) -> bool:
    """Validates dataset structure, data types, missing values, and business key uniqueness.
    Ensures data integrity for multi-region indicators by checking uniqueness
    across the composite key (indicator_id, datetime, geo_id).

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

    # Standardize column name 'id' to 'indicator_id' if present
    if "id" in df.columns and "indicator_id" not in df.columns:
        df = df.rename(columns={"id": "indicator_id"})

    # Step 2: Validate missing columns
    required_cols = list(EXPECTED_COLUMNS.keys())
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        raise ValueError(f"❌ Validation failed: Missing required columns: {missing_cols}")

    print("✅ All required columns found.")

    # Step 3: Validate data types
    for col, expected_type in EXPECTED_COLUMNS.items():
        if expected_type in ["object", "str"]:
            if not (
                pd.api.types.is_object_dtype(df[col])
                or pd.api.types.is_string_dtype(df[col])
            ):
                raise ValueError(f"❌ Validation failed: Column '{col}' type is {df[col].dtype}, expected text.")

        elif expected_type in ["int64", "int32", "int"]:
            if not pd.api.types.is_integer_dtype(df[col]):
                raise ValueError(f"❌ Validation failed: Column '{col}' type is {df[col].dtype}, expected integer.")

        elif expected_type in ["float64", "float32", "float"]:
            if not pd.api.types.is_float_dtype(df[col]):
                raise ValueError(f"❌ Validation failed: Column '{col}' type is {df[col].dtype}, expected float.")

        elif col == "datetime":
            if not (
                isinstance(df[col].dtype, pd.DatetimeTZDtype)
                or pd.api.types.is_datetime64_any_dtype(df[col])
            ):
                raise ValueError(f"❌ Validation failed: Column '{col}' type is {df[col].dtype}, expected datetime.")

    print("✅ All data types are correct.")

    # Step 4: Check for missing values (NaNs)
    missing_values = df.isnull().sum().sum()
    if missing_values > 0:
        raise ValueError(f"❌ Validation failed: Found {missing_values} missing (NaN) values in dataset.")

    print("✅ No missing values.")

    # Step 5: Check for duplicate entries based on composite business key
    composite_key = ["indicator_id", "datetime", "geo_id"]
    available_keys = [k for k in composite_key if k in df.columns]

    if len(available_keys) == len(composite_key):
        duplicate_count = df.duplicated(subset=available_keys).sum()
        if duplicate_count > 0:
            raise ValueError(f"❌ Validation failed: Found {duplicate_count} duplicate records for key combination {available_keys}.")
        print(f"✅ No duplicate records for composite key {available_keys}.")

    print("🎉 [SUCCESS] Dataset passed all quality checks!")
    return True