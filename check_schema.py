import duckdb

conn = duckdb.connect('warehouse.duckdb')

print("=== Schema Check ===")
print(f"Current schema: {conn.execute('SELECT current_schema()').fetchone()[0]}")

print("\n=== All Schemas ===")
schemas = conn.execute("SELECT schema_name FROM information_schema.schemata").fetchall()
for schema in schemas:
    print(f"  - {schema[0]}")

print("\n=== Tables by Schema ===")
for schema in schemas:
    schema_name = schema[0]
    tables = conn.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema_name}'").fetchall()
    if tables:
        print(f"\n{schema_name}:")
        for table in tables:
            print(f"  - {table[0]}")

print("\n=== Sentiment Tables Location ===")
sentiment_tables = ['news_sentiment', 'sentiment_aggregates', 'market_events', 'sentiment_signals']
for table in sentiment_tables:
    result = conn.execute(f"SELECT table_schema FROM information_schema.tables WHERE table_name = '{table}'").fetchall()
    if result:
        print(f"{table}: {result[0][0]}")
    else:
        print(f"{table}: NOT FOUND")

conn.close()

