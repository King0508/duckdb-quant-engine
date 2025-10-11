import sys
import pathlib
import duckdb


def main():
    if len(sys.argv) < 2:
        print("Usage: python etl/run_queries.py path/to/file.sql")
        raise SystemExit(1)

    ROOT = pathlib.Path(__file__).resolve().parents[1]
    DB_PATH = ROOT / "warehouse.duckdb"
    SQL_PATH = pathlib.Path(sys.argv[1])

    con = duckdb.connect(str(DB_PATH))
    sql_text = SQL_PATH.read_text(encoding="utf-8")

    # Split on semicolons to run each statement in order (simple but effective here)
    statements = [s.strip() for s in sql_text.split(";") if s.strip()]

    for i, stmt in enumerate(statements, 1):
        print(f"\n-- Statement {i} --")
        try:
            res = con.execute(stmt)
            # If it's a SELECT, print top rows
            try:
                df = res.df()
                print(df.head(25).to_string(index=False))
            except duckdb.CatalogException:
                # Non-SELECT statements return no result set
                pass
        except Exception as e:
            print("Error:", e)

    con.close()


if __name__ == "__main__":
    main()
