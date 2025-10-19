# Quick Start Guide

Get up and running with the Quantitative Finance SQL Warehouse in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- 500MB free disk space

## Installation

### 1. Clone or Download

```bash
# If using git
git clone https://github.com/yourusername/quant-sql-warehouse.git
cd quant-sql-warehouse

# Or download and extract the ZIP file
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Quick Setup

Use the Makefile for the fastest setup:

```bash
make setup
```

This will:

1. Install all dependencies
2. Generate sample market data
3. Create and populate the database

## Manual Setup

Prefer to run each step manually?

### Step 1: Generate Data

```bash
python etl/generate_data.py
```

**Output**: Creates CSV files in the `data/` directory with realistic market data.

### Step 2: Load Data

```bash
python etl/load_data.py
```

**Output**: Creates `warehouse.duckdb` and loads all data with validation.

### Step 3: Run Analytics

```bash
python analytics/run_analysis.py
```

**Output**: Displays various analytical reports and insights.

### Step 4: Start API (Optional)

```bash
python -m api.main
```

**Output**: API server running at `http://localhost:8000`

Visit `http://localhost:8000/docs` for interactive API documentation!

## Verify Installation

Run the test suite to ensure everything works:

```bash
pytest tests/ -v
```

All tests should pass ✅

## Your First Query

### Using Python

```python
import duckdb
import config

# Connect to the database
con = duckdb.connect(str(config.get_db_path()), read_only=True)

# Get latest prices
prices = con.execute("""
    SELECT symbol, price, rsi_14, return_1d_pct
    FROM features_returns_rsi
    WHERE ts = (SELECT MAX(ts) FROM features_returns_rsi)
    ORDER BY symbol
""").fetchdf()

print(prices)
con.close()
```

### Using the API

```bash
# Get all symbols
curl http://localhost:8000/symbols

# Get AAPL price data
curl http://localhost:8000/bars/AAPL?limit=10

# Get RSI analysis
curl http://localhost:8000/analytics/rsi/AAPL

# Get trading signals
curl http://localhost:8000/analytics/signals
```

## Common Commands

All available via `make` command:

```bash
make help              # Show all commands
make test              # Run tests
make lint              # Check code quality
make format            # Format code
make run-etl           # Regenerate data
make run-analytics     # Run analysis
make run-api           # Start API server
make clean             # Clean generated files
```

## Project Structure

```
quant-sql-warehouse/
├── data/              # Generated CSV data files
├── etl/               # ETL scripts (generate, validate, load)
├── sql/               # SQL schemas and views
├── analytics/         # Analysis scripts and queries
├── api/               # REST API (FastAPI)
├── tests/             # Test suite
├── examples/          # Example scripts
├── docs/              # Detailed documentation
└── warehouse.duckdb   # Database file (created after setup)
```

## What's in the Database?

After setup, you'll have:

- **8 symbols**: AAPL, MSFT, GOOGL, TSLA, AMZN, META, NVDA, AMD
- **~750 trading days** of data (2022-2024)
- **~6,000 OHLCV bars** (daily prices)
- **~120,000 trade records** (individual trades)
- **3 analytical views** with technical indicators

## Example Outputs

### Analytics Report

```
Latest Prices
====================================================================
 symbol              name  latest_timestamp  latest_price  daily_return_pct  rsi_14
   AAPL         Apple Inc.   2024-12-31 16:00         185.50            +0.75   58.23
   MSFT  Microsoft Corporation 2024-12-31 16:00      365.20            +1.20   62.45
```

### API Response

```json
{
  "symbol": "AAPL",
  "price": 185.5,
  "rsi_14": 58.23,
  "rsi_signal": "NEUTRAL",
  "return_1d_pct": 0.75
}
```

## Next Steps

1. **Explore Analytics**: Run `python analytics/run_analysis.py`
2. **Try the API**: Visit `http://localhost:8000/docs`
3. **Run Examples**: Check `examples/` directory
4. **Read Documentation**: See `docs/` for detailed guides
5. **Customize**: Modify `config.py` for your needs

## Getting Help

- 📖 **Full Documentation**: See `README.md` and `docs/` folder
- 💡 **Examples**: Check `examples/` directory
- 🐛 **Issues**: Report bugs on GitHub Issues
- 💬 **Questions**: Open a Discussion on GitHub

## Troubleshooting

### Import Errors

```bash
# Make sure you're in the project directory
cd quant-sql-warehouse

# And virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### Database Not Found

```bash
# Regenerate the database
make run-etl
```

### API Won't Start

```bash
# Check if port 8000 is available
# Use a different port if needed
uvicorn api.main:app --host 0.0.0.0 --port 8080
```

### Tests Failing

```bash
# Clean and reinstall
make clean
pip install -r requirements.txt
make setup
```

## Success! 🎉

You now have a fully functional quantitative finance data warehouse!

Start exploring market data, running analytics, and building your trading strategies.

---

**Pro Tip**: Use `make all` to run the complete ETL and analytics pipeline in one command!

