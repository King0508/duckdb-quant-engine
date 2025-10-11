# Market Data Analytics Database

This is a small, local analytics database for market data using DuckDB, SQL, and Python. It loads CSVs into typed tables, installs a couple of feature views (returns/RSI, VWAP/volume), and shows how to align trade-time features to a minute bar grid without look-ahead. It’s meant to be easy to clone, run, and extend into simple backtests.

## What’s here

Schema: `symbols`, `bars` (OHLCV), `trades`.  
ETL/ELT: one script builds the DB, loads CSVs, and installs views.  
Features: returns + RSI from bars; VWAP + volume z-score from trades.  
Point-in-time: joins trade features to bars using “latest trade at or before bar time.”

## Project layout

market-data-analytics-db/  
├─ data/ (seed CSVs: symbols, bars, trades)  
├─ etl/  
│ ├─ load_data.py (build DB: apply schema, load CSVs, install views)  
│ └─ run_queries.py (run a .sql file and print results)  
├─ sql/  
│ ├─ schema.sql  
│ ├─ views/  
│ │ ├─ features_returns_rsi.sql  
│ │ └─ features_vwap_volume.sql  
│ └─ queries/  
│ └─ example_queries.sql  
└─ warehouse.duckdb (created locally, gitignored)

## Quickstart (Windows / PowerShell)

1. clone and enter  
   `git clone https://github.com/King0508/market-data-analytics-db.git`  
   `cd market-data-analytics-db`

2. create a virtualenv (optional)  
   `py -m venv .venv`  
   `.\.venv\Scripts\Activate.ps1`

3. install dependencies  
   `pip install -r requirements.txt`

4. build the database (schema + data + views)  
   `python .\etl\load_data.py`

5. run demo queries  
   `python .\etl\run_queries.py .\sql\queries\example_queries.sql`

You should see table counts, a few bar rows, returns/RSI, VWAP/volume, and a joined result with trade features aligned to bar timestamps.

## Notes

CTEs and window functions do the heavy lifting.  
For VWAP we use a time-based window.  
For RSI we use a row-based window.  
For alignment we rank trades up to each bar and pick the latest trade at or before the bar.

## Next

Add a forward-return label view, a tiny strategy script that writes positions and PnL, and a couple of SQL reports (daily PnL, hit rate, drawdown).
