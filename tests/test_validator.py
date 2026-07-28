import numpy as np
import pandas as pd
import pytest
from src.validator import validate_dataset

def test_validate_dataset_success():
    """Tests that a correctly structured DataFrame passes validation without raising errors."""
    valid_data = pd.DataFrame({
        "id": [1293],
        "name": ["Demanda real"],
        "geo_id": [8741],
        "geo_name": ["España"],
        "value": [25000],
        "datetime": pd.to_datetime(["2026-07-24 00:00:00+02:00"]),
    })

    # Should execute cleanly and return True
    assert validate_dataset(valid_data) is True

def test_validate_dataset_empty_dataframe():
    """Tests that an empty DataFrame raises a ValueError during validation."""
    empty_df = pd.DataFrame()

    with pytest.raises(ValueError, match="DataFrame is empty"):
        validate_dataset(empty_df)


def test_validate_dataset_missing_columns():
    """Tests that a DataFrame missing required schema columns raises a ValueError."""
    incomplete_data = pd.DataFrame({
        "id": [1293],
        "name": ["Demanda real"],
        # Missing 'geo_id', 'geo_name', 'value', 'datetime'
    })

    with pytest.raises(ValueError, match="Missing required column"):
        validate_dataset(incomplete_data)


def test_validate_dataset_null_values():
    """Tests that a DataFrame containing null/NaN values fails validation."""
    data_with_nulls = pd.DataFrame({
        "id": [1293],
        "name": ["Demanda real"],
        "geo_id": [8741],
        "geo_name": [None],
        "value": [25000],
        "datetime": pd.to_datetime(["2026-07-24 00:00:00+02:00"]),
    })

    with pytest.raises(ValueError, match="missing values"):
        validate_dataset(data_with_nulls)