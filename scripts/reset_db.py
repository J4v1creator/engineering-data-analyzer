import sys
from pathlib import Path

# Add project root directory to sys.path to resolve internal modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.database import get_connection


def reset_database() -> None:
    """Wipes all records from the esios_records table in SQLite cache."""
    print("⚠️ WARNING: You are about to wipe all records from 'esios_records' in esios_cache.db.")
    confirm = input("Are you sure you want to proceed? (y/N): ")
    
    if confirm.lower() != "y":
        print("❌ Operation cancelled.")
        return

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Clear main table records
            cursor.execute("DELETE FROM esios_records;")
            
            # Reset autoincrement sequence if sqlite_sequence exists
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='esios_records';")
            
            conn.commit()
            print("✅ Successfully cleared all data from 'esios_records'.")

    except Exception as e:
        print(f"❌ Failed to reset database: {e}")


if __name__ == "__main__":
    reset_database()