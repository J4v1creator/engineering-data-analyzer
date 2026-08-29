"""SQLite database connection managers, schema initialization, and query operations."""

from datetime import datetime
from pathlib import Path
import sqlite3

import pandas as pd

from config.settings import DEFAULT_DB_PATH


def get_connection(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Creates and returns a connection to the SQLite database.
    Ensures the parent directory exists before connecting.

    Args:
        db_path (str | Path): Path to the SQLite database file.

    Returns:
        sqlite3.Connection: Active SQLite database connection object.
    """
    path_obj = Path(db_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path_obj)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    """Initializes the database schema by creating required tables and indexes.

    Args:
        db_path (str | Path): Path to the SQLite database file.
    """
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()

            # Create main unified ESIOS records table (supports both demand and prices)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS esios_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    indicator_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    geo_id INTEGER NOT NULL,
                    geo_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    datetime TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(indicator_id, datetime, geo_id)
                )
            """)

            # Composite index for optimized query performance across time ranges
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_records_indicator_geo_datetime 
                ON esios_records (indicator_id, geo_id, datetime);
            """)

            # Index on last_accessed_at for ultra-fast expiration purges
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_records_last_accessed 
                ON esios_records (last_accessed_at);
            """)

            conn.commit()
        print("✅ [DATABASE] Database schema initialized successfully.")

    except sqlite3.Error as e:
        print(f"\n❌ [DATABASE ERROR] Failed to initialize SQLite storage:\n{e}")


def save_dataframe(df: pd.DataFrame, db_path: str | Path = DEFAULT_DB_PATH) -> int:
    """Saves a pandas DataFrame into the SQLite database.
    If the record already exists, refreshes value and last_accessed_at timestamp.

    Args:
        df (pd.DataFrame): DataFrame containing ESIOS records.
        db_path (str | Path): Path to the SQLite database file.

    Returns:
        int: Total number of new or updated rows processed in the database.
    """
    if df.empty:
        return 0

    df_to_save = df.copy()

    # Flexible mapping fallback if column is named 'id' instead of 'indicator_id'
    if "indicator_id" not in df_to_save.columns and "id" in df_to_save.columns:
        df_to_save["indicator_id"] = df_to_save["id"]

        # Convert datetime column to standardized UTC ISO string format for SQLite comparisons
    if pd.api.types.is_datetime64_any_dtype(df_to_save["datetime"]):
        df_to_save["datetime"] = (
            df_to_save["datetime"].dt.tz_convert("UTC").dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        )

    records = df_to_save[["indicator_id", "name", "geo_id", "geo_name", "value", "datetime"]].values.tolist()

    insert_query = """
        INSERT INTO esios_records (indicator_id, name, geo_id, geo_name, value, datetime)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(indicator_id, geo_id, datetime) 
        DO UPDATE SET 
            value = excluded.value,
            last_accessed_at = CURRENT_TIMESTAMP
    """

    with get_connection(db_path) as conn:
        initial_changes = conn.total_changes
        cursor = conn.cursor()
        cursor.executemany(insert_query, records)
        conn.commit()
        inserted_count = conn.total_changes - initial_changes

    print(f"💾 [DATABASE] Processed {inserted_count} records in SQLite database.")
    return inserted_count


def load_data_by_ids(
    indicator_ids: list[int],
    start_iso: str | datetime,
    end_iso: str | datetime,
    geo_ids: list[int] | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> pd.DataFrame:
    """Loads ESIOS records matching selected IDs and time range, and updates last_accessed_at.

    Args:
        indicator_ids (list[int]): List of indicator IDs to filter.
        start_iso (str | datetime): Start datetime in ISO string or datetime object.
        end_iso (str | datetime): End datetime in ISO string or datetime object.
        geo_ids (list[int] | None): Optional list of geo_id values to filter by region.
        db_path (str | Path): Path to the SQLite database file.

    Returns:
        pd.DataFrame: Retrieved data formatted identically to API payload dataframes.
    """
    if not indicator_ids:
        return pd.DataFrame()

    # Normalize start and end datetimes to standard UTC ISO format for SQL query
    start_dt_obj = pd.to_datetime(start_iso, utc=True)
    end_dt_obj = pd.to_datetime(end_iso, utc=True)

    start_str = start_dt_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_dt_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

    id_placeholders = ", ".join(["?"] * len(indicator_ids))

    # Build dynamic WHERE clause
    where_conditions = [
        f"indicator_id IN ({id_placeholders})",
        "datetime >= ?",
        "datetime <= ?"
    ]
    params: list = list(indicator_ids) + [start_str, end_str]

    if geo_ids:
        geo_placeholders = ", ".join(["?"] * len(geo_ids))
        where_conditions.append(f"geo_id IN ({geo_placeholders})")
        params.extend(geo_ids)

    where_clause = " AND ".join(where_conditions)

    select_query = f"""
        SELECT indicator_id, name, geo_id, geo_name, value, datetime
        FROM esios_records
        WHERE {where_clause}
        ORDER BY datetime ASC, geo_id ASC
    """

    update_query = f"""
        UPDATE esios_records
        SET last_accessed_at = CURRENT_TIMESTAMP
        WHERE {where_clause}
    """

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(update_query, params)
        df = pd.read_sql_query(select_query, conn, params=params)

    if not df.empty:
        # Convert datetime column back to Europe/Madrid localized objects
        df["datetime"] = pd.to_datetime(df["datetime"], utc=True).dt.tz_convert("Europe/Madrid")

    return df