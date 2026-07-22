from datetime import datetime
import os
import sqlite3
from typing import List
import pandas as pd
from src.constants import DEFAULT_DB_PATH

def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Creates and returns a connection to the SQLite database.
    Ensures the parent directory exists before connecting.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        sqlite3.Connection: A connection object to the SQLite database.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    # Enable dict-like column access
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initializes the database schema by creating required tables and indexes.
    Args:
        db_path (str): Path to the SQLite database file.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Create main demand records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS demand_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                indicator_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                geoname TEXT NOT NULL,
                value INTEGER NOT NULL,
                datetime TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(indicator_id, datetime)
            )
        """)

        # Create index on datetime for ultra-fast time range queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_demand_datetime 
            ON demand_records (datetime);
        """)

        conn.commit()
    print("✅ [DATABASE] Database schema initialized successfully.")

def save_demand_dataframe(df: pd.DataFrame, db_path: str = DEFAULT_DB_PATH) -> int:
    """Saves a pandas DataFrame into the SQLite database.
    Uses INSERT OR IGNORE to automatically bypass duplicate timestamps.

    Args:
        df (pd.DataFrame): DataFrame containing demand records with columns.
        db_path (str): Path to the SQLite database file.

    Returns:
        int: Total number of new rows inserted.
    """
    if df.empty:
        return 0

    init_db(db_path)  # Ensures table exists before writing

    # Prepare DataFrame records for bulk insertion
    df_to_save = df.copy()
    
    # Ensure datetime column is converted to string ISO format for SQLite storage
    if pd.api.types.is_datetime64_any_dtype(df_to_save["datetime"]):
        df_to_save["datetime"] = df_to_save["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%S%z")

    records = df_to_save[["id", "name", "geoname", "value", "datetime"]].values.tolist()

    insert_query = """
        INSERT OR IGNORE INTO demand_records (indicator_id, name, geoname, value, datetime)
        VALUES (?, ?, ?, ?, ?)
    """

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany(insert_query, records)
        conn.commit()
        inserted_count = cursor.rowcount

    print(f"💾 [DATABASE] Inserted {inserted_count} new records into SQLite database.")
    return inserted_count

def load_demand_data(demands: List[str], start_iso: str, end_iso: str, db_path: str = DEFAULT_DB_PATH) -> pd.DataFrame:
    """Loads demand records from SQLite matching selected demand names and time range.

    Args:
        demands (List[str]): List of demand names to filter.
        start_iso (str): Start datetime in ISO format.
        end_iso (str): End datetime in ISO format.
        db_path (str): Path to the SQLite database file.

    Returns:
        pd.DataFrame: Retrieved data formatted identically to API payload dataframes.
    """
    if not demands:
        return pd.DataFrame()

    init_db(db_path)

    # Ensure start and end datetimes are in ISO format strings
    if isinstance(start_iso, datetime):
        start_iso = start_iso.isoformat()
    if isinstance(end_iso, datetime):
        end_iso = end_iso.isoformat()

    # Prepare dynamic placeholders for the IN clause (?, ?, ?)
    placeholders = ", ".join(["?"] * len(demands))
    query = f"""
        SELECT indicator_id AS id, name, geoname, value, datetime
        FROM demand_records
        WHERE name IN ({placeholders})
            AND datetime >= ?
            AND datetime <= ?
        ORDER BY datetime ASC
    """

    params = list(demands) + [start_iso, end_iso]

    with get_connection(db_path) as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if not df.empty:
        # Restore timezone-aware datetime objects matching mainland Madrid time
        df["datetime"] = pd.to_datetime(df["datetime"], utc=True).dt.tz_convert("Europe/Madrid")

    return df