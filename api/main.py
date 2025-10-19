"""
FastAPI REST API for the quantitative finance data warehouse.

Provides endpoints for accessing market data, analytics, and indicators.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import duckdb
from datetime import datetime, date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

# Initialize FastAPI app
app = FastAPI(
    title="Quantitative Finance Data Warehouse API",
    description="REST API for accessing market data and analytics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


def get_db_connection():
    """Get a database connection."""
    db_path = config.get_db_path()
    if not db_path.exists():
        raise HTTPException(
            status_code=503,
            detail="Database not found. Please run ETL to initialize the database.",
        )
    return duckdb.connect(str(db_path), read_only=True)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Quantitative Finance Data Warehouse API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "symbols": "/symbols",
            "bars": "/bars/{ticker}",
            "trades": "/trades/{ticker}",
            "analytics": "/analytics/*",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        con = get_db_connection()
        # Test query
        result = con.execute("SELECT COUNT(*) as count FROM symbols").fetchone()
        con.close()
        return {
            "status": "healthy",
            "database": "connected",
            "symbols_count": result[0],
        }
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": str(e)})


@app.get("/symbols")
async def get_symbols(sector: Optional[str] = None, limit: int = Query(default=100, le=1000)):
    """Get all symbols with optional filtering."""
    try:
        con = get_db_connection()

        if sector:
            query = """
            SELECT symbol_id, ticker, name, sector, industry, market_cap, exchange, currency
            FROM symbols
            WHERE sector = ?
            ORDER BY market_cap DESC
            LIMIT ?
            """
            result = con.execute(query, [sector, limit]).fetchdf()
        else:
            query = """
            SELECT symbol_id, ticker, name, sector, industry, market_cap, exchange, currency
            FROM symbols
            ORDER BY market_cap DESC
            LIMIT ?
            """
            result = con.execute(query, [limit]).fetchdf()

        con.close()
        return result.to_dict("records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/symbols/{ticker}")
async def get_symbol(ticker: str):
    """Get details for a specific symbol."""
    try:
        con = get_db_connection()
        query = """
        SELECT symbol_id, ticker, name, sector, industry, market_cap, exchange, currency
        FROM symbols
        WHERE ticker = ?
        """
        result = con.execute(query, [ticker.upper()]).fetchdf()
        con.close()

        if len(result) == 0:
            raise HTTPException(status_code=404, detail=f"Symbol {ticker} not found")

        return result.to_dict("records")[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bars/{ticker}")
async def get_bars(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(default=100, le=10000),
):
    """Get OHLCV bars for a symbol."""
    try:
        con = get_db_connection()

        # Build query based on parameters
        base_query = """
        SELECT b.ts, b.open, b.high, b.low, b.close, b.volume
        FROM bars b
        JOIN symbols s ON b.symbol_id = s.symbol_id
        WHERE s.ticker = ?
        """
        params = [ticker.upper()]

        if start_date:
            base_query += " AND b.ts >= ?"
            params.append(start_date)

        if end_date:
            base_query += " AND b.ts <= ?"
            params.append(end_date)

        base_query += " ORDER BY b.ts DESC LIMIT ?"
        params.append(limit)

        result = con.execute(base_query, params).fetchdf()
        con.close()

        if len(result) == 0:
            raise HTTPException(status_code=404, detail=f"No bars found for {ticker}")

        # Convert timestamps to strings for JSON serialization
        result["ts"] = result["ts"].astype(str)
        return result.to_dict("records")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trades/{ticker}")
async def get_trades(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    side: Optional[str] = None,
    limit: int = Query(default=100, le=10000),
):
    """Get trades for a symbol."""
    try:
        con = get_db_connection()

        base_query = """
        SELECT t.ts, t.price, t.size, t.side
        FROM trades t
        JOIN symbols s ON t.symbol_id = s.symbol_id
        WHERE s.ticker = ?
        """
        params = [ticker.upper()]

        if start_date:
            base_query += " AND t.ts >= ?"
            params.append(start_date)

        if end_date:
            base_query += " AND t.ts <= ?"
            params.append(end_date)

        if side:
            base_query += " AND t.side = ?"
            params.append(side.upper())

        base_query += " ORDER BY t.ts DESC LIMIT ?"
        params.append(limit)

        result = con.execute(base_query, params).fetchdf()
        con.close()

        if len(result) == 0:
            raise HTTPException(status_code=404, detail=f"No trades found for {ticker}")

        result["ts"] = result["ts"].astype(str)
        return result.to_dict("records")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/rsi/{ticker}")
async def get_rsi_analysis(ticker: str, limit: int = Query(default=30, le=1000)):
    """Get RSI technical analysis for a symbol."""
    try:
        con = get_db_connection()
        query = """
        SELECT ts, price, return_1d_pct, rsi_14, rsi_28, rsi_signal
        FROM features_returns_rsi
        WHERE symbol = ?
        ORDER BY ts DESC
        LIMIT ?
        """
        result = con.execute(query, [ticker.upper(), limit]).fetchdf()
        con.close()

        if len(result) == 0:
            raise HTTPException(status_code=404, detail=f"No RSI data found for {ticker}")

        result["ts"] = result["ts"].astype(str)
        return result.to_dict("records")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/vwap/{ticker}")
async def get_vwap_analysis(ticker: str, limit: int = Query(default=30, le=1000)):
    """Get VWAP analysis for a symbol."""
    try:
        con = get_db_connection()
        query = """
        SELECT ts, price, volume, vwap, avg_volume_20, volume_ratio, 
               volume_trend, price_vs_vwap_pct, volume_category
        FROM features_vwap_volume
        WHERE symbol = ?
        ORDER BY ts DESC
        LIMIT ?
        """
        result = con.execute(query, [ticker.upper(), limit]).fetchdf()
        con.close()

        if len(result) == 0:
            raise HTTPException(status_code=404, detail=f"No VWAP data found for {ticker}")

        result["ts"] = result["ts"].astype(str)
        return result.to_dict("records")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/daily/{ticker}")
async def get_daily_metrics(ticker: str, limit: int = Query(default=30, le=365)):
    """Get daily aggregated metrics for a symbol."""
    try:
        con = get_db_connection()
        query = """
        SELECT date, open, high, low, close, daily_return_pct, 
               intraday_range_pct, total_volume, num_trades, 
               buy_volume, sell_volume, buy_ratio_pct
        FROM daily_metrics
        WHERE symbol = ?
        ORDER BY date DESC
        LIMIT ?
        """
        result = con.execute(query, [ticker.upper(), limit]).fetchdf()
        con.close()

        if len(result) == 0:
            raise HTTPException(status_code=404, detail=f"No daily metrics found for {ticker}")

        result["date"] = result["date"].astype(str)
        return result.to_dict("records")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/performance")
async def get_performance(days: int = Query(default=30, le=365), limit: int = Query(default=10, le=100)):
    """Get top performing stocks over a time period."""
    try:
        con = get_db_connection()
        query = """
        WITH recent_data AS (
            SELECT 
                symbol,
                name,
                ts,
                price,
                return_1d_pct,
                ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY ts DESC) as rn
            FROM features_returns_rsi
            WHERE ts >= CURRENT_DATE - INTERVAL ? DAY
        ),
        performance AS (
            SELECT 
                symbol,
                name,
                FIRST(price ORDER BY ts) as start_price,
                LAST(price ORDER BY ts DESC) as end_price,
                SUM(return_1d_pct) as total_return_pct,
                COUNT(*) as trading_days
            FROM recent_data
            GROUP BY symbol, name
        )
        SELECT 
            symbol,
            name,
            ROUND(start_price, 2) as start_price,
            ROUND(end_price, 2) as end_price,
            ROUND(total_return_pct, 2) as total_return_pct,
            trading_days
        FROM performance
        ORDER BY total_return_pct DESC
        LIMIT ?
        """
        result = con.execute(query, [days, limit]).fetchdf()
        con.close()

        return result.to_dict("records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/signals")
async def get_trading_signals():
    """Get current trading signals (RSI overbought/oversold)."""
    try:
        con = get_db_connection()
        query = """
        WITH latest_rsi AS (
            SELECT 
                symbol,
                name,
                ts,
                price,
                rsi_14,
                rsi_signal,
                ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY ts DESC) as rn
            FROM features_returns_rsi
        )
        SELECT 
            symbol,
            name,
            ROUND(price, 2) as price,
            rsi_14,
            rsi_signal
        FROM latest_rsi
        WHERE rn = 1 AND rsi_signal != 'NEUTRAL'
        ORDER BY 
            CASE rsi_signal 
                WHEN 'OVERBOUGHT' THEN 1 
                WHEN 'OVERSOLD' THEN 2 
            END,
            symbol
        """
        result = con.execute(query).fetchdf()
        con.close()

        return result.to_dict("records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    print(f"Starting API server on {config.API_HOST}:{config.API_PORT}")
    uvicorn.run("api.main:app", host=config.API_HOST, port=config.API_PORT, reload=True)
