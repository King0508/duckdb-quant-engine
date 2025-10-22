"""Initialize sentiment schema in warehouse database."""

import duckdb
import re

conn = duckdb.connect("warehouse.duckdb")

print("Initializing sentiment tables...")

# Read schema
with open("sql/sentiment_schema.sql", "r", encoding="utf-8") as f:
    schema_sql = f.read()

# Split by semicolon
statements = schema_sql.split(";")

executed = 0
for statement in statements:
    statement = statement.strip()

    # Skip empty
    if not statement:
        continue

    # Skip if it's only comments
    lines = [line.strip() for line in statement.split("\n") if line.strip()]
    non_comment_lines = [line for line in lines if not line.startswith("--")]

    if not non_comment_lines:
        continue

    # Skip COMMENT ON statements
    if statement.upper().startswith("COMMENT ON"):
        continue

    try:
        conn.execute(statement)
        executed += 1

        if "CREATE TABLE" in statement.upper():
            # Extract table name
            match = re.search(r"CREATE TABLE\s+(\w+)", statement, re.IGNORECASE)
            if match:
                table_name = match.group(1)
                print(f"[+] Created table: {table_name}")
        elif "CREATE INDEX" in statement.upper():
            match = re.search(r"CREATE INDEX\s+(\w+)", statement, re.IGNORECASE)
            if match:
                print(f"[+] Created index: {match.group(1)}")
        elif "CREATE VIEW" in statement.upper():
            match = re.search(r"CREATE VIEW\s+(\w+)", statement, re.IGNORECASE)
            if match:
                print(f"[+] Created view: {match.group(1)}")

    except Exception as e:
        error_msg = str(e).lower()
        if "already exists" in error_msg:
            print(f"  (Already exists, skipping)")
        elif "does not exist" in error_msg:
            # Table doesn't exist yet - this is expected for indices/views
            pass
        else:
            print(f"[!] Error: {e}")

print(f"\nExecuted {executed} statements")

# Verify tables
print("\nVerifying schema...")
tables = conn.execute("SHOW TABLES").fetchall()
sentiment_tables = ["news_sentiment", "sentiment_aggregates", "market_events", "sentiment_signals"]

found_tables = []
for table in sentiment_tables:
    if any(table in str(t) for t in tables):
        print(f"[OK] {table}")
        found_tables.append(table)
    else:
        print(f"[MISSING] {table}")

print(f"\nTotal tables in database: {len(tables)}")
print(f"Sentiment tables created: {len(found_tables)}/4")

if len(found_tables) == 4:
    print("\n SUCCESS! Sentiment schema initialized successfully!")
else:
    print("\n WARNING: Not all tables were created. Check errors above.")

# Commit and close
conn.commit()
conn.close()
print("Changes committed to database.")
