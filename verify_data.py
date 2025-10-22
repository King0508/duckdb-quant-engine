import duckdb

conn = duckdb.connect("warehouse.duckdb")

result = conn.execute("SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM news_sentiment").fetchone()
print(f"News articles: {result[0]}")
print(f"Date range: {result[1]} to {result[2]}")

print("\nSample articles:")
articles = conn.execute("SELECT title, sentiment_label, sentiment_score FROM news_sentiment LIMIT 5").fetchall()
for title, label, score in articles:
    print(f"  - {title[:60]}... [{label}, {score:.2f}]")

conn.close()
