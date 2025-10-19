# Examples

This directory contains example scripts demonstrating how to use the Quantitative Finance SQL Warehouse.

## Available Examples

### 1. `example_analysis.py`

Comprehensive stock analysis workflow including:

- Stock information lookup
- Performance metrics
- Technical indicators (RSI)
- Volume analysis
- Trading activity summary
- Comparative analysis

**Usage:**

```bash
python examples/example_analysis.py
```

### 2. `api_example.py`

REST API usage examples including:

- Health checks
- Symbol lookups
- Price data retrieval
- Analytics endpoints
- Sector analysis

**Prerequisites:**
Start the API server first:

```bash
python -m api.main
```

Then run:

```bash
python examples/api_example.py
```

## Common Use Cases

### Query Latest Prices

```python
import duckdb
import config

con = duckdb.connect(str(config.get_db_path()), read_only=True)
prices = con.execute("""
    SELECT symbol, price, return_1d_pct
    FROM features_returns_rsi
    WHERE ts = (SELECT MAX(ts) FROM features_returns_rsi)
""").fetchdf()
print(prices)
con.close()
```

### Find Trading Signals

```python
import duckdb
import config

con = duckdb.connect(str(config.get_db_path()), read_only=True)
signals = con.execute("""
    SELECT symbol, rsi_14, rsi_signal, price
    FROM features_returns_rsi
    WHERE ts = (SELECT MAX(ts) FROM features_returns_rsi)
    AND rsi_signal != 'NEUTRAL'
""").fetchdf()
print(signals)
con.close()
```

### Calculate Portfolio Returns

```python
import duckdb
import config

con = duckdb.connect(str(config.get_db_path()), read_only=True)

# Define portfolio
portfolio = {
    'AAPL': 10,  # 10 shares
    'MSFT': 5,
    'GOOGL': 3
}

# Get current prices
for ticker, shares in portfolio.items():
    price = con.execute("""
        SELECT price
        FROM features_returns_rsi
        WHERE symbol = ?
        ORDER BY ts DESC
        LIMIT 1
    """, [ticker]).fetchone()[0]

    value = price * shares
    print(f"{ticker}: {shares} shares @ ${price:.2f} = ${value:.2f}")

con.close()
```

## Tips

1. **Always use read-only connections** for queries:

   ```python
   con = duckdb.connect(str(config.get_db_path()), read_only=True)
   ```

2. **Use context managers** for automatic cleanup:

   ```python
   with AnalyticsEngine() as engine:
       data = engine.get_latest_prices()
   ```

3. **Parameterize queries** to prevent SQL injection:

   ```python
   con.execute("SELECT * FROM symbols WHERE ticker = ?", [ticker])
   ```

4. **Limit large result sets**:
   ```python
   con.execute("SELECT * FROM bars LIMIT 1000")
   ```

## Next Steps

- Review the [Usage Examples](../docs/USAGE_EXAMPLES.md) documentation
- Check the [Architecture](../docs/ARCHITECTURE.md) guide
- Explore the [API documentation](http://localhost:8000/docs) (when server is running)

