import sys
from pathlib import Path

# Add project root directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.database import get_connection


def inspect_database() -> None:
    """Prints a quick analytical summary of the SQLite cache database state."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # 1. Total records count
            cursor.execute("SELECT COUNT(*) FROM esios_records;")
            total_records = cursor.fetchone()[0]

            print("\n" + "=" * 50)
            print("📊 ESIOS CACHE DATABASE INSPECTION REPORT")
            print("=" * 50)
            print(f"📦 Total Cached Records: {total_records:,}")

            if total_records == 0:
                print("⚠️ Database is completely empty.")
                print("=" * 50 + "\n")
                return

            # 2. Date range covered
            cursor.execute("SELECT MIN(datetime), MAX(datetime) FROM esios_records;")
            min_date, max_date = cursor.fetchone()
            print(f"🗓️ Timeframe Covered: {min_date} ➔ {max_date}")

            # 3. Indicator breakdown
            cursor.execute(
                """
                SELECT indicator_id, name, COUNT(*) 
                FROM esios_records 
                GROUP BY indicator_id, name 
                ORDER BY COUNT(*) DESC;
            """
            )
            indicators = cursor.fetchall()

            print("\n📌 Cached Indicators Breakdown:")
            print(f"{'ID':<10} | {'Count':<10} | {'Indicator Name'}")
            print("-" * 50)
            for ind_id, name, count in indicators:
                print(f"{ind_id:<10} | {count:<10,} | {name}")

            print("=" * 50 + "\n")

    except Exception as e:
        print(f"❌ Failed to inspect database: {e}")


if __name__ == "__main__":
    inspect_database()