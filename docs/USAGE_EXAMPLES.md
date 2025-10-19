# Usage Examples

This document provides practical examples of using the Quantitative Finance SQL Warehouse.

## Table of Contents

- [Setup](#setup)
- [ETL Operations](#etl-operations)
- [Analytics Queries](#analytics-queries)
- [API Usage](#api-usage)
- [Advanced Queries](#advanced-queries)
- [Integration Examples](#integration-examples)

## Setup

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/quant-sql-warehouse.git
cd quant-sql-warehouse

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate sample data
python etl/generate_data.py

# Load data into warehouse
python etl/load_data.py
```

## ETL Operations

### Generate Custom Date Range

```python
from etl.generate_data import MarketDataGenerator
import config

# Generate data for specific date range
generator = MarketDataGenerator("2023-01-01", "2023-12-31")

# Generate and save data
symbols = generator.generate_symbols()
bars = generator.generate_bars(symbols)
trades = generator.generate_trades(symbols, num_trades_per_symbol_per_day=100)

# Save to CSV
generator.save_to_csv(symbols, "symbols.csv")
generator.save_to_csv(bars, "bars.csv")
generator.save_to_csv(trades, "trades.csv")
```

### Validate Data Before Loading

```python
from etl.data_validator import validate_csv_files

# Validate all CSV files
is_valid = validate_csv_files()

if is_valid:
    print("Data validation passed! Ready to load.")
else:
    print("Data validation failed. Please fix errors.")
```

### Custom Data Loading

```python
import duckdb
import config

# Connect to database
con = duckdb.connect(str(config.get_db_path()))

# Load custom CSV file
con.execute("""
    CREATE TEMP VIEW custom_data AS
    SELECT * FROM read_csv_auto('path/to/custom.csv', HEADER=True)
""")

# Insert into table
con.execute("""
    INSERT INTO bars
    SELECT
        symbol_id,
        CAST(timestamp AS TIMESTAMP),
        CAST(open AS DOUBLE),
        CAST(high AS DOUBLE),
        CAST(low AS DOUBLE),
        CAST(close AS DOUBLE),
        CAST(volume AS BIGINT)
    FROM custom_data
""")

con.close()
```

## Analytics Queries

### Basic Price Analysis

```python
from analytics.run_analysis import AnalyticsEngine

with AnalyticsEngine() as engine:
    # Get latest prices
    prices = engine.get_latest_prices(limit=10)
    print(prices)

    # Get top performers
    top_performers = engine.get_top_performers(days=30, limit=5)
    print("\nTop 5 performers (last 30 days):")
    print(top_performers)
```

### Technical Analysis

```python
import duckdb
import config

con = duckdb.connect(str(config.get_db_path()), read_only=True)

# RSI analysis for specific stock
rsi_data = con.execute("""
    SELECT
        ts,
        price,
        rsi_14,
        rsi_signal
    FROM features_returns_rsi
    WHERE symbol = 'AAPL'
    ORDER BY ts DESC
    LIMIT 30
""").fetchdf()

print(rsi_data)

# Find overbought stocks
overbought = con.execute("""
    WITH latest_rsi AS (
        SELECT
            symbol,
            rsi_14,
            price,
            ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY ts DESC) as rn
        FROM features_returns_rsi
    )
    SELECT symbol, rsi_14, price
    FROM latest_rsi
    WHERE rn = 1 AND rsi_14 > 70
    ORDER BY rsi_14 DESC
""").fetchdf()

print("\nOverbought stocks (RSI > 70):")
print(overbought)

con.close()
```

### Volume Analysis

```python
import duckdb
import config

con = duckdb.connect(str(config.get_db_path()), read_only=True)

# Unusual volume activity
unusual_volume = con.execute("""
    WITH latest_volume AS (
        SELECT
            symbol,
            volume,
            avg_volume_20,
            volume_ratio,
            volume_category,
            ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY ts DESC) as rn
        FROM features_vwap_volume
    )
    SELECT
        symbol,
        volume,
        avg_volume_20,
        volume_ratio,
        volume_category
    FROM latest_volume
    WHERE rn = 1 AND volume_ratio > 2
    ORDER BY volume_ratio DESC
""").fetchdf()

print("Stocks with unusual volume (>2x average):")
print(unusual_volume)

con.close()
```

### Correlation Analysis

```python
import duckdb
import config
import pandas as pd

con = duckdb.connect(str(config.get_db_path()), read_only=True)

# Get daily returns for correlation analysis
returns = con.execute("""
    SELECT
        symbol,
        DATE_TRUNC('day', ts) as date,
        AVG(return_1d_pct) as avg_return
    FROM features_returns_rsi
    WHERE return_1d_pct IS NOT NULL
    GROUP BY symbol, DATE_TRUNC('day', ts)
    ORDER BY date, symbol
""").fetchdf()

# Pivot for correlation matrix
returns_pivot = returns.pivot(index='date', columns='symbol', values='avg_return')

# Calculate correlation
correlation_matrix = returns_pivot.corr()
print("Correlation Matrix:")
print(correlation_matrix)

con.close()
```

## API Usage

### Python Requests

```python
import requests

base_url = "http://localhost:8000"

# Get all symbols
response = requests.get(f"{base_url}/symbols")
symbols = response.json()
print(f"Found {len(symbols)} symbols")

# Get bars for AAPL
response = requests.get(
    f"{base_url}/bars/AAPL",
    params={
        "start_date": "2024-01-01",
        "limit": 100
    }
)
bars = response.json()
print(f"\nAAPL bars: {len(bars)} records")

# Get RSI analysis
response = requests.get(f"{base_url}/analytics/rsi/AAPL")
rsi_data = response.json()
print(f"\nLatest RSI: {rsi_data[0]['rsi_14']}")

# Get trading signals
response = requests.get(f"{base_url}/analytics/signals")
signals = response.json()
print(f"\nActive trading signals: {len(signals)}")
for signal in signals[:5]:
    print(f"{signal['symbol']}: {signal['rsi_signal']} (RSI: {signal['rsi_14']})")
```

### JavaScript/Node.js

```javascript
const axios = require("axios");

const baseUrl = "http://localhost:8000";

async function getMarketData() {
  try {
    // Get symbols
    const symbolsResponse = await axios.get(`${baseUrl}/symbols`);
    console.log(`Found ${symbolsResponse.data.length} symbols`);

    // Get bars for AAPL
    const barsResponse = await axios.get(`${baseUrl}/bars/AAPL`, {
      params: { limit: 10 },
    });
    console.log("AAPL bars:", barsResponse.data);

    // Get performance data
    const perfResponse = await axios.get(`${baseUrl}/analytics/performance`, {
      params: { days: 30, limit: 5 },
    });
    console.log("Top performers:", perfResponse.data);
  } catch (error) {
    console.error("Error:", error.message);
  }
}

getMarketData();
```

### cURL Examples

```bash
# Get all symbols
curl http://localhost:8000/symbols

# Get bars for AAPL
curl "http://localhost:8000/bars/AAPL?limit=10"

# Get RSI analysis
curl http://localhost:8000/analytics/rsi/AAPL

# Get trading signals
curl http://localhost:8000/analytics/signals

# Get performance data
curl "http://localhost:8000/analytics/performance?days=30&limit=10"
```

## Advanced Queries

### Moving Averages

```sql
SELECT
    symbol,
    ts,
    close,
    AVG(close) OVER (
        PARTITION BY symbol
        ORDER BY ts
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) as ma_5,
    AVG(close) OVER (
        PARTITION BY symbol
        ORDER BY ts
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) as ma_20,
    AVG(close) OVER (
        PARTITION BY symbol
        ORDER BY ts
        ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
    ) as ma_50
FROM bars
WHERE symbol_id = 1
ORDER BY ts DESC
LIMIT 100
```

### Bollinger Bands

```sql
WITH price_stats AS (
    SELECT
        symbol_id,
        ts,
        close,
        AVG(close) OVER w as sma_20,
        STDDEV(close) OVER w as std_20
    FROM bars
    WINDOW w AS (
        PARTITION BY symbol_id
        ORDER BY ts
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    )
)
SELECT
    s.ticker,
    ps.ts,
    ps.close,
    ROUND(ps.sma_20, 2) as middle_band,
    ROUND(ps.sma_20 + 2 * ps.std_20, 2) as upper_band,
    ROUND(ps.sma_20 - 2 * ps.std_20, 2) as lower_band,
    CASE
        WHEN ps.close > ps.sma_20 + 2 * ps.std_20 THEN 'ABOVE_UPPER'
        WHEN ps.close < ps.sma_20 - 2 * ps.std_20 THEN 'BELOW_LOWER'
        ELSE 'WITHIN_BANDS'
    END as position
FROM price_stats ps
JOIN symbols s ON ps.symbol_id = s.symbol_id
WHERE s.ticker = 'AAPL'
ORDER BY ps.ts DESC
LIMIT 30
```

### Volume Profile

```sql
WITH price_levels AS (
    SELECT
        symbol_id,
        FLOOR(close / 5) * 5 as price_level,
        SUM(volume) as total_volume,
        COUNT(*) as bar_count
    FROM bars
    WHERE ts >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY symbol_id, FLOOR(close / 5) * 5
)
SELECT
    s.ticker,
    pl.price_level,
    pl.total_volume,
    pl.bar_count,
    ROUND(pl.total_volume * 100.0 / SUM(pl.total_volume) OVER (PARTITION BY pl.symbol_id), 2) as volume_pct
FROM price_levels pl
JOIN symbols s ON pl.symbol_id = s.symbol_id
WHERE s.ticker = 'AAPL'
ORDER BY pl.price_level DESC
```

## Integration Examples

### Pandas Integration

```python
import duckdb
import pandas as pd
import config

# Connect to database
con = duckdb.connect(str(config.get_db_path()), read_only=True)

# Load data into DataFrame
df = con.execute("""
    SELECT * FROM features_returns_rsi
    WHERE symbol = 'AAPL'
    ORDER BY ts
""").fetchdf()

# Pandas analysis
df['ts'] = pd.to_datetime(df['ts'])
df.set_index('ts', inplace=True)

# Calculate additional metrics
df['volatility_30d'] = df['log_return_1d'].rolling(window=30).std()
df['sharpe_ratio'] = df['return_1d_pct'].rolling(window=30).mean() / df['return_1d_pct'].rolling(window=30).std()

print(df.tail())

con.close()
```

### Matplotlib Visualization

```python
import matplotlib.pyplot as plt
import duckdb
import config

con = duckdb.connect(str(config.get_db_path()), read_only=True)

# Get data
df = con.execute("""
    SELECT ts, price, rsi_14
    FROM features_returns_rsi
    WHERE symbol = 'AAPL'
    ORDER BY ts
""").fetchdf()

# Create plots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# Price plot
ax1.plot(df['ts'], df['price'], label='Price')
ax1.set_ylabel('Price ($)')
ax1.set_title('AAPL Price and RSI')
ax1.legend()
ax1.grid(True)

# RSI plot
ax2.plot(df['ts'], df['rsi_14'], label='RSI(14)', color='orange')
ax2.axhline(y=70, color='r', linestyle='--', label='Overbought')
ax2.axhline(y=30, color='g', linestyle='--', label='Oversold')
ax2.set_ylabel('RSI')
ax2.set_xlabel('Date')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.savefig('aapl_analysis.png')
plt.show()

con.close()
```

### Export to CSV

```python
import duckdb
import config

con = duckdb.connect(str(config.get_db_path()), read_only=True)

# Export query results to CSV
con.execute("""
    COPY (
        SELECT * FROM features_returns_rsi
        WHERE symbol IN ('AAPL', 'MSFT', 'GOOGL')
        ORDER BY symbol, ts DESC
    ) TO 'export/analysis_results.csv' (HEADER, DELIMITER ',')
""")

print("Data exported to export/analysis_results.csv")

con.close()
```

## Best Practices

1. **Use context managers** for database connections
2. **Use parameterized queries** to prevent SQL injection
3. **Limit result sets** for large queries
4. **Create indexes** on frequently queried columns
5. **Use views** for complex repeated queries
6. **Cache API results** for frequently accessed data
7. **Monitor query performance** with EXPLAIN
8. **Batch operations** for better performance
9. **Use read-only connections** for analytics
10. **Regular backups** of the database file

## Troubleshooting

### Common Issues

**Database locked error:**

```python
# Use read-only connection for queries
con = duckdb.connect(str(config.get_db_path()), read_only=True)
```

**Memory issues with large queries:**

```python
# Process in chunks
chunk_size = 10000
offset = 0
while True:
    chunk = con.execute(f"""
        SELECT * FROM bars
        LIMIT {chunk_size} OFFSET {offset}
    """).fetchdf()

    if len(chunk) == 0:
        break

    # Process chunk
    process_data(chunk)
    offset += chunk_size
```

**API connection refused:**

```bash
# Check if API is running
python -m api.main

# Or use uvicorn directly
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

