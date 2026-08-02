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
        sqlite3.Connection: A connection object to the SQLite database.
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
                    UNIQUE(indicator_id, datetime, geo_id)
                )
            """)

            # Composite index for optimized query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_records_name_geo_datetime 
                ON esios_records (name, geo_id, datetime);
            """)

            conn.commit()
        print("✅ [DATABASE] Database schema initialized successfully.")

    except sqlite3.Error as e:
        print(f"\n❌ Database Error: An issue occurred with SQLite storage.\n{e}")


def save_dataframe(df: pd.DataFrame, db_path: str | Path = DEFAULT_DB_PATH) -> int:
    """Saves a pandas DataFrame into the SQLite database.
    Uses INSERT OR IGNORE to automatically bypass duplicate entries for (indicator_id, datetime, geo_id).

    Args:
        df (pd.DataFrame): DataFrame containing ESIOS records with required columns.
        db_path (str | Path): Path to the SQLite database file.

    Returns:
        int: Total number of new rows inserted into the database.
    """
    if df.empty:
        return 0

    init_db(db_path)  # Ensures table exists before writing

    # Prepare DataFrame records for bulk insertion
    df_to_save = df.copy()

    # Ensure datetime column is converted to string ISO format for SQLite storage
    if pd.api.types.is_datetime64_any_dtype(df_to_save["datetime"]):
        df_to_save["datetime"] = df_to_save["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%S%z")

    records = df_to_save[["id", "name", "geo_id", "geo_name", "value", "datetime"]].values.tolist()

    insert_query = """
        INSERT OR IGNORE INTO esios_records (indicator_id, name, geo_id, geo_name, value, datetime)
        VALUES (?, ?, ?, ?, ?, ?)
    """

    with get_connection(db_path) as conn:
        initial_changes = conn.total_changes
        cursor = conn.cursor()
        cursor.executemany(insert_query, records)
        conn.commit()
        inserted_count = conn.total_changes - initial_changes

    print(f"💾 [DATABASE] Inserted {inserted_count} new records into SQLite database.")
    return inserted_count


def load_data_by_names(
    names: list[str],
    start_iso: str | datetime,
    end_iso: str | datetime,
    geo_ids: list[int] | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> pd.DataFrame:
    """Loads ESIOS records from SQLite matching selected names, optional geography IDs, and time range.

    Args:
        names (list[str]): List of indicator names to filter.
        start_iso (str | datetime): Start datetime in ISO format or datetime object.
        end_iso (str | datetime): End datetime in ISO format or datetime object.
        geo_ids (list[int] | None): Optional list of geo_id values to filter by region.
        db_path (str | Path): Path to the SQLite database file.

    Returns:
        pd.DataFrame: Retrieved data formatted identically to API payload dataframes.
    """
    if not names:
        return pd.DataFrame()

    init_db(db_path)

    # Ensure start and end datetimes are in ISO format strings
    if isinstance(start_iso, datetime):
        start_iso = start_iso.isoformat()
    if isinstance(end_iso, datetime):
        end_iso = end_iso.isoformat()

    # Build dynamic SQL query
    name_placeholders = ", ".join(["?"] * len(names))
    query = f"""
        SELECT indicator_id AS id, name, geo_id, geo_name, value, datetime
        FROM esios_records
        WHERE name IN ({name_placeholders})
            AND datetime >= ?
            AND datetime <= ?
    """
    params = list(names) + [start_iso, end_iso]

    # Optional filtering by geographic IDs
    if geo_ids:
        geo_placeholders = ", ".join(["?"] * len(geo_ids))
        query += f" AND geo_id IN ({geo_placeholders})"
        params.extend(geo_ids)

    query += " ORDER BY datetime ASC, geo_id ASC"

    with get_connection(db_path) as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if not df.empty:
        # Convert datetime column back to timezone-aware objects
        df["datetime"] = pd.to_datetime(df["datetime"], utc=True).dt.tz_convert("Europe/Madrid")

    return df