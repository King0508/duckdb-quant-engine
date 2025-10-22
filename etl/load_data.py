"""
ETL script to load market data into the DuckDB warehouse.

This script:
1. Creates/connects to the DuckDB database
2. Applies the schema (tables, indexes, constraints)
3. Validates and loads CSV data
4. Creates analytical views
5. Provides summary statistics
"""

import pathlib
import duckdb
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import config
from etl.data_validator import validate_csv_files


def setup_logging():
    """Setup simple logging to file and console."""
    log_file = config.LOG_FILE
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def log(message: str, level: str = "INFO"):
        """Log message to file and console."""
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")

    return log


def main():
    """Main ETL execution function."""
    log = setup_logging()

    print("=" * 80)
    print("ETL Pipeline: Load Market Data into Warehouse")
    print("=" * 80)
    print()

    # Step 0: Validate CSV files
    log("Starting data validation...")
    if not validate_csv_files():
        log("Data validation failed. Aborting ETL.", "ERROR")
        sys.exit(1)

    try:
        # 1) Connect to DuckDB (creates the file if it doesn't exist)
        log(f"Connecting to database: {config.get_db_path()}")
        con = duckdb.connect(str(config.get_db_path()))

        # 2) Apply schema (tables, keys, indexes)
        log("Applying database schema...")
        schema_sql_path = config.get_sql_file("schema.sql")
        schema_sql = schema_sql_path.read_text(encoding="utf-8")
        con.execute(schema_sql)
        log("Schema applied successfully")

        # 3) Stage CSVs as TEMP views (so we can INSERT ... SELECT)
        log("Staging CSV files as temporary views...")
        symbols_csv = config.get_data_file("symbols.csv")
        bars_csv = config.get_data_file("bars.csv")
        trades_csv = config.get_data_file("trades.csv")

        con.execute(
            f"CREATE OR REPLACE TEMP VIEW _symbols_src AS "
            f"SELECT * FROM read_csv_auto('{symbols_csv}', HEADER=True);"
        )
        con.execute(
            f"CREATE OR REPLACE TEMP VIEW _bars_src AS "
            f"SELECT * FROM read_csv_auto('{bars_csv}', HEADER=True);"
        )
        con.execute(
            f"CREATE OR REPLACE TEMP VIEW _trades_src AS "
            f"SELECT * FROM read_csv_auto('{trades_csv}', HEADER=True);"
        )
        log("CSV staging complete")

        # 4) Replace-load into typed tables (cast text → correct types)
        log("Loading symbols...")
        con.execute("DELETE FROM symbols;")
        con.execute("INSERT INTO symbols SELECT * FROM _symbols_src;")
        symbol_count = con.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
        log(f"Loaded {symbol_count:,} symbols")

        log("Loading bars...")
        con.execute("DELETE FROM bars;")
        con.execute(
            """
            INSERT INTO bars
            SELECT
              CAST(symbol_id AS INTEGER),
              CAST(ts        AS TIMESTAMP),
              CAST(open      AS DOUBLE),
              CAST(high      AS DOUBLE),
              CAST(low       AS DOUBLE),
              CAST(close     AS DOUBLE),
              CAST(volume    AS BIGINT)
            FROM _bars_src
            ORDER BY symbol_id, ts;
        """
        )
        bars_count = con.execute("SELECT COUNT(*) FROM bars").fetchone()[0]
        log(f"Loaded {bars_count:,} bars")

        log("Loading trades...")
        con.execute("DELETE FROM trades;")
        con.execute(
            """
            INSERT INTO trades
            SELECT
              CAST(symbol_id AS INTEGER),
              CAST(ts        AS TIMESTAMP),
              CAST(price     AS DOUBLE),
              CAST(size      AS BIGINT),
              CAST(side      AS VARCHAR)
            FROM _trades_src
            ORDER BY symbol_id, ts;
        """
        )
        trades_count = con.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
        log(f"Loaded {trades_count:,} trades")

        # 5) Install feature views (saved SQL queries you can SELECT from)
        log("Creating analytical views...")
        views_dir = config.SQL_DIR / "views"
        for view_file in [
            "features_returns_rsi.sql",
            "features_vwap_volume.sql",
            "daily_metrics.sql",
        ]:
            view_sql_path = views_dir / view_file
            if view_sql_path.exists():
                view_sql = view_sql_path.read_text(encoding="utf-8")
                con.execute(view_sql)
                log(f"  Created view from {view_file}")
            else:
                log(f"  Warning: View file not found: {view_file}", "WARNING")

        # 6) Friendly summary
        log("Generating summary statistics...")
        summary = con.execute(
            """
            SELECT
              (SELECT COUNT(*) FROM bars)    AS n_bars,
              (SELECT COUNT(*) FROM trades)  AS n_trades,
              (SELECT COUNT(*) FROM symbols) AS n_symbols,
              (SELECT MIN(ts) FROM bars)     AS min_date,
              (SELECT MAX(ts) FROM bars)     AS max_date
        """
        ).fetchdf()

        print()
        print("=" * 80)
        print("[SUCCESS] ETL COMPLETE - Database loaded successfully!")
        print("=" * 80)
        print(f"\nDatabase: {config.get_db_path()}")
        print("\nSummary:")
        print(summary.to_string(index=False))
        print()
        log("ETL pipeline completed successfully")

        con.close()

    except Exception as e:
        log(f"ETL pipeline failed: {str(e)}", "ERROR")
        print(f"\n[ERROR] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
