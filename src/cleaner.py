"""Cache maintenance engine and expired DB entry cleaner."""

from pathlib import Path
import time
import sqlite3

from config.settings import CACHE_EXPIRATION_DAYS, DEFAULT_DB_PATH, DEFAULT_OUTPUT_DIR
from src.database import get_connection


def _clean_directory(target_dir: str | Path, expiration_days: int) -> int:
    """Scans a directory and deletes files older than the expiration threshold.

    Args:
        target_dir (str | Path): Directory path to clean.
        expiration_days (int): File age threshold in days.

    Returns:
        int: Number of deleted files.
    """
    target_path = Path(target_dir)

    if not target_path.exists():
        print(f"⚠️ [CLEANER] Target directory '{target_path}' does not exist. Skipping.")
        return 0

    now = time.time()
    expiration_seconds = expiration_days * 24 * 60 * 60
    deleted_count = 0

    for file_item in target_path.iterdir():
        if not file_item.is_file():
            continue

        try:
            file_mod_time = file_item.stat().st_mtime
            file_age_seconds = now - file_mod_time

            if file_age_seconds > expiration_seconds:
                file_age_days = file_age_seconds / (24 * 60 * 60)
                print(f"🗑️ [CLEANER] Removing expired file: '{file_item.name}' (Age: {file_age_days:.1f} days)")
                file_item.unlink()
                deleted_count += 1

        except OSError as e:
            print(f"❌ [CLEANER] Error processing file '{file_item.name}': {e}")

    return deleted_count


def _clean_expired_database_records(db_path: str | Path, expiration_days: int) -> int:
    """Deletes records from SQLite database older than the expiration threshold.

    Args:
        db_path (str | Path): Path to the SQLite database file.
        expiration_days (int): Age threshold in days.

    Returns:
        int: Number of deleted database rows.
    """
    db_file = Path(db_path)

    if not db_file.exists():
        return 0

    deleted_rows = 0
    try:
        with get_connection(db_file) as conn:
            cursor = conn.cursor()

            query = """
                DELETE FROM esios_records
                WHERE julianday(last_accessed_at) < julianday('now', ? || ' days');
            """
            initial_changes = conn.total_changes
            cursor.execute(query, (f"-{expiration_days}",))
            conn.commit()
            deleted_rows = conn.total_changes - initial_changes

        if deleted_rows > 0:
            print(f"🗑️ [CLEANER] Purged {deleted_rows} expired records from SQLite database.")

    except sqlite3.Error as e:
        print(f"❌ [CLEANER] Error cleaning database records: {e}")

    return deleted_rows


def clean_expired_cache(
    db_path: str | Path = DEFAULT_DB_PATH,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    expiration_days: int = CACHE_EXPIRATION_DAYS,
) -> None:
    """Scans system output directory and purges expired database records.

    Args:
        db_path (str | Path): Path to SQLite database file.
        output_dir (str | Path): Directory containing generated charts and text reports.
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