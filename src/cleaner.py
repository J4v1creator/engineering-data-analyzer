import os
import sqlite3
import time
from src.constants import CACHE_EXPIRATION_DAYS, DEFAULT_DB_PATH, DEFAULT_OUTPUT_DIR
from src.database import get_connection

def _clean_directory(target_dir: str, expiration_days: int) -> int:
    """Scans a directory and deletes files older than the expiration threshold.

    Args:
        target_dir (str): Directory path to clean.
        expiration_days (int): File age threshold in days.

    Returns:
        int: Number of deleted files.
    """
    if not os.path.exists(target_dir):
        print(f"⚠️ [CLEANER] Target directory '{target_dir}' does not exist. Skipping.")
        return 0

    now = time.time()
    # Convert expiration days into seconds
    expiration_seconds = expiration_days * 24 * 60 * 60
    deleted_count = 0

    for filename in os.listdir(target_dir):
        filepath = os.path.join(target_dir, filename)

        # Skip subdirectories if present
        if not os.path.isfile(filepath):
            continue

        try:
            file_mod_time = os.path.getmtime(filepath)
            file_age_seconds = now - file_mod_time

            if file_age_seconds > expiration_seconds:
                file_age_days = file_age_seconds / (24 * 60 * 60)
                print(f"🗑️ [CLEANER] Removing expired file: '{filename}' (Age: {file_age_days:.1f} days)")
                os.remove(filepath)
                deleted_count += 1

        except OSError as e:
            print(f"❌ [CLEANER] Error processing file '{filename}': {e}")

    return deleted_count

def _clean_expired_database_records(db_path: str, expiration_days: int) -> int:
    """Deletes records from SQLite database older than the expiration threshold.

    Args:
        db_path (str): Path to the SQLite database file.
        expiration_days (int): Age threshold in days.

    Returns:
        int: Number of deleted database rows.
    """
    if not os.path.exists(db_path):
        return 0

    deleted_rows = 0
    try:
        with get_connection(db_path) as conn:
            initial_changes = conn.total_changes
            cursor = conn.cursor()

            # Ensure datetime comparison parses ISO strings properly
            query = """
                DELETE FROM demand_records
                WHERE datetime < DATETIME('now', ? || ' days');
            """
            cursor.execute(query, (f"-{expiration_days}",))
            conn.commit()
            deleted_rows = conn.total_changes - initial_changes

        if deleted_rows > 0:
            print(f"🗑️ [CLEANER] Purged {deleted_rows} expired records from SQLite database.")

    except sqlite3.Error as e:
        print(f"❌ [CLEANER] Error cleaning database records: {e}")

    return deleted_rows

def clean_expired_cache(db_path: str = DEFAULT_DB_PATH, output_dir: str = DEFAULT_OUTPUT_DIR, expiration_days: int = CACHE_EXPIRATION_DAYS) -> None:
    """Scans system output directory and purges expired database records.

    Args:
        db_path (str): Path to SQLite database file.
        output_dir (str): Directory containing generated charts and text reports.
        expiration_days (int): Maximum allowed age in days before purging.
    """
    print("\n==================================================")
    print("🧹 [CLEANER] Starting automated system storage maintenance...")

    # Clean expired database records
    print(f"📂 Scanning database: '{db_path}'")
    db_rows_deleted = _clean_expired_database_records(db_path, expiration_days)

    # Clean generated output reports and visualizations
    print(f"📂 Scanning output reports/plots directory: '{output_dir}'")
    files_deleted = _clean_directory(output_dir, expiration_days)

    print(f"✅ [CLEANER] Maintenance complete. (Purged: {db_rows_deleted} DB rows, {files_deleted} output files)")
    print("==================================================")