import os
import time
from src.constants import DEFAULT_RAW_DIR, CACHE_EXPIRATION_DAYS, RAW_FILE_PREFIX

def clean_expired_cache(target_dir: str = DEFAULT_RAW_DIR, expiration_days: int = CACHE_EXPIRATION_DAYS) -> None:
    """Scans the cache directory and deletes files older than the specified expiration days.

    Only files matching the API cache prefix are targeted to prevent accidental 
    deletion of other user data.

    Args:
        target_dir (str): The directory to scan for expired cache files.
        expiration_days (int): The age in days after which files are considered expired.
    """
    print("\n==================================================")
    print(f"🧹 [CLEANER] Scanning cache directory: '{target_dir}'")
    
    # Check if directory exists before iterating
    if not os.path.exists(target_dir):
        print(f"⚠️ [CLEANER] Target directory '{target_dir}' does not exist. Skipping.")
        print("==================================================")
        return

    now = time.time()
    # Convert expiration days into seconds
    expiration_seconds = expiration_days * 24 * 60 * 60
    deleted_count = 0

    # Iterate through all files in the target folder
    for filename in os.listdir(target_dir):
        # Strict security check: only touch our dynamic API CSV files
        if filename.startswith(RAW_FILE_PREFIX) and filename.endswith(".csv"):
            filepath = os.path.join(target_dir, filename)

            try:
                # Get last modification timestamp
                file_mod_time = os.path.getmtime(filepath)
                file_age_seconds = now - file_mod_time

                # Check if the file has expired
                if file_age_seconds > expiration_seconds:
                    file_age_days = file_age_seconds / (24 * 60 * 60)
                    print(f"🗑️ [CLEANER] Removing expired file: '{filename}' (Age: {file_age_days:.1f} days)")
                    os.remove(filepath)
                    deleted_count += 1

            except OSError as e:
                print(f"❌ [CLEANER] Error accessing file '{filename}': {e}")

    print(f"✅ [CLEANER] Cache clean up complete. Total files deleted: {deleted_count}")
    print("==================================================")