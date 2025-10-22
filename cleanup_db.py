"""Clean up and reset database tables."""
import duckdb
from pathlib import Path

db_path = Path("warehouse.duckdb")
conn = duckdb.connect(str(db_path))

print("=== Cleaning Database ===")

# Drop views first (they depend on tables)
views = ['v_latest_yields', 'v_latest_etfs', 'v_yield_curve', 'v_treasury_etf_correlation']
for view in views:
    try:
        conn.execute(f"DROP VIEW IF EXISTS {view}")
        print(f"[OK] Dropped view: {view}")
    except Exception as e:
        print(f"[SKIP] {view}: {e}")

# Drop tables
tables = ['treasury_yields', 'fixed_income_etfs']
for table in tables:
    try:
        conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        print(f"[OK] Dropped table: {table}")
    except Exception as e:
        print(f"[SKIP] {table}: {e}")

# Drop sequences
sequences = ['seq_treasury_yields', 'seq_fixed_income_etfs']
for seq in sequences:
    try:
        conn.execute(f"DROP SEQUENCE IF EXISTS {seq}")
        print(f"[OK] Dropped sequence: {seq}")
    except Exception as e:
        print(f"[SKIP] {seq}: {e}")

conn.close()
print("\n[SUCCESS] Database cleaned!")

