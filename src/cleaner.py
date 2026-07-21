import os
import time
from src.constants import CACHE_EXPIRATION_DAYS, DEFAULT_OUTPUT_DIR, DEFAULT_RAW_DIR, RAW_FILE_PREFIX

def _clean_directory(target_dir: str, expiration_days: int, file_prefix: str = None) -> int:
    """Helper function to scan a directory and delete files older than expiration_days.

    Args:
        target_dir (str): Directory to clean.
        expiration_days (int): File age threshold in days.
        file_prefix (str, optional): If provided, only files starting with this prefix are deleted.

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

        # Skip directories if any exist inside
        if not os.path.isfile(filepath):
            continue

        # Optional prefix filter check for security
        if file_prefix and not filename.startswith(file_prefix):
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


def clean_expired_cache(raw_dir: str = DEFAULT_RAW_DIR, output_dir: str = DEFAULT_OUTPUT_DIR, expiration_days: int = CACHE_EXPIRATION_DAYS) -> None:
    """Scans both raw data cache and output directories to purge expired files.

    Args:
        raw_dir (str): Directory containing cached raw API CSV files.
        output_dir (str): Directory containing generated charts and text reports.
        expiration_days (int): Maximum allowed file age in days before purging.
    """
    print("\n==================================================")
    print("🧹 [CLEANER] Starting automated system storage maintenance...")

    # Clean Raw Data API Cache
    print(f"📂 Scanning raw cache directory: '{raw_dir}'")
    raw_deleted = _clean_directory(raw_dir, expiration_days, file_prefix=RAW_FILE_PREFIX)

    # Clean Output Generated Reports and Visualizations
    print(f"📂 Scanning output reports/plots directory: '{output_dir}'")
    output_deleted = _clean_directory(output_dir, expiration_days)

    total_deleted = raw_deleted + output_deleted
    print(f"✅ [CLEANER] Maintenance complete. Total expired files purged: {total_deleted}")
    print("==================================================")