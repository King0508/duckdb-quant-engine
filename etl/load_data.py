# etl/load_data.py
# Purpose: one command to (1) create/open the DuckDB database file,
# (2) apply the SQL schema, (3) load CSV data into typed tables,
# and (4) install feature views so you can query immediately.

import pathlib
import duckdb


# Locate the repo root and DB file regardless of where the script is run from.
ROOT = pathlib.Path(__file__).resolve().parents[1]  # .../market-data-analytics-db
DB_PATH = ROOT / "warehouse.duckdb"  # database file at project root


def main():
    # 1) Connect to DuckDB (creates the file if it doesn't exist)
    con = duckdb.connect(str(DB_PATH))

    # 2) Apply schema (tables, keys, indexes)
    schema_sql_path = ROOT / "sql" / "schema.sql"
    schema_sql = schema_sql_path.read_text(encoding="utf-8")
    con.execute(schema_sql)

    # 3) Stage CSVs as TEMP views (so we can INSERT ... SELECT)
    symbols_csv = ROOT / "data" / "symbols.csv"
    bars_csv = ROOT / "data" / "bars.csv"
    trades_csv = ROOT / "data" / "trades.csv"

    con.execute(
        "CREATE OR REPLACE TEMP VIEW _symbols_src AS "
        "SELECT * FROM read_csv_auto(?, HEADER=True);",
        [str(symbols_csv)],
    )
    con.execute(
        "CREATE OR REPLACE TEMP VIEW _bars_src AS "
        "SELECT * FROM read_csv_auto(?, HEADER=True);",
        [str(bars_csv)],
    )
    con.execute(
        "CREATE OR REPLACE TEMP VIEW _trades_src AS "
        "SELECT * FROM read_csv_auto(?, HEADER=True);",
        [str(trades_csv)],
    )

    # 4) Replace-load into typed tables (cast text → correct types)
    con.execute("DELETE FROM symbols;")
    con.execute("INSERT INTO symbols SELECT * FROM _symbols_src;")

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

    # 5) Install feature views (saved SQL queries you can SELECT from)
    for view_file in ["features_returns_rsi.sql", "features_vwap_volume.sql"]:
        view_sql_path = ROOT / "sql" / "views" / view_file
        view_sql = view_sql_path.read_text(encoding="utf-8")
        con.execute(view_sql)

    # 6) Friendly summary
    summary = con.execute(
        """
        SELECT
          (SELECT COUNT(*) FROM bars)    AS n_bars,
          (SELECT COUNT(*) FROM trades)  AS n_trades,
          (SELECT COUNT(*) FROM symbols) AS n_symbols
    """
    ).fetchdf()

    print(f"✅ Loaded database at: {DB_PATH}")
    print(summary.to_string(index=False))

    con.close()


if __name__ == "__main__":
    main()
