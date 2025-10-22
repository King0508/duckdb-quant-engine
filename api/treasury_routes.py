"""
Treasury API routes - REST endpoints for Treasury yields and fixed-income ETFs.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import duckdb
from pydantic import BaseModel

import config

router = APIRouter(prefix="/treasury", tags=["Treasury & Fixed Income"])


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class TreasuryYield(BaseModel):
    """Treasury yield data"""
    timestamp: datetime
    maturity: str
    yield_rate: float
    change_1d: Optional[float] = None
    change_1w: Optional[float] = None
    change_1m: Optional[float] = None
    source: str


class FixedIncomeETF(BaseModel):
    """Fixed-income ETF data"""
    timestamp: datetime
    ticker: str
    name: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    return_1d: Optional[float] = None
    return_1w: Optional[float] = None
    return_1m: Optional[float] = None


class YieldCurve(BaseModel):
    """Yield curve point"""
    maturity: str
    yield_rate: float
    timestamp: datetime


class TreasurySummary(BaseModel):
    """Summary statistics for Treasury data"""
    total_yield_records: int
    total_etf_records: int
    maturities: List[str]
    etf_tickers: List[str]
    date_range: dict


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_connection():
    """Get database connection."""
    db_path = config.get_db_path()
    return duckdb.connect(str(db_path), read_only=True)


# =============================================================================
# TREASURY YIELD ENDPOINTS
# =============================================================================

@router.get("/yields/latest", response_model=List[TreasuryYield])
def get_latest_yields():
    """
    Get the latest Treasury yields for all maturities.
    
    Returns the most recent yield snapshot.
    """
    try:
        con = get_connection()
        result = con.execute("""
            SELECT * FROM v_latest_yields
            ORDER BY 
                CASE maturity
                    WHEN '2Y' THEN 1
                    WHEN '5Y' THEN 2
                    WHEN '10Y' THEN 3
                    WHEN '30Y' THEN 4
                END
        """).fetchdf()
        con.close()
        
        return result.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/yields/curve", response_model=List[YieldCurve])
def get_yield_curve():
    """
    Get the current Treasury yield curve.
    
    Returns yields across all maturities to plot the yield curve.
    """
    try:
        con = get_connection()
        result = con.execute("SELECT * FROM v_yield_curve").fetchdf()
        con.close()
        
        if result.empty:
            raise HTTPException(status_code=404, detail="No yield curve data available")
        
        return result.to_dict('records')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/yields/{maturity}", response_model=List[TreasuryYield])
def get_yields_by_maturity(
    maturity: str,
    days: int = Query(30, ge=1, le=365, description="Number of days of history")
):
    """
    Get historical Treasury yields for a specific maturity.
    
    Args:
        maturity: Treasury maturity ('2Y', '5Y', '10Y', '30Y')
        days: Number of days of historical data
    """
    valid_maturities = ['2Y', '5Y', '10Y', '30Y']
    if maturity not in valid_maturities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid maturity. Must be one of: {', '.join(valid_maturities)}"
        )
    
    try:
        con = get_connection()
        result = con.execute(f"""
            SELECT *
            FROM treasury_yields
            WHERE maturity = ?
                AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '{days}' DAY
            ORDER BY timestamp DESC
        """, [maturity]).fetchdf()
        con.close()
        
        if result.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {maturity}")
        
        return result.to_dict('records')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# =============================================================================
# FIXED-INCOME ETF ENDPOINTS
# =============================================================================

@router.get("/etfs/latest", response_model=List[FixedIncomeETF])
def get_latest_etfs():
    """
    Get the latest prices for all fixed-income ETFs.
    
    Returns the most recent ETF snapshot.
    """
    try:
        con = get_connection()
        result = con.execute("""
            SELECT 
                timestamp, ticker, name, 
                close as open, close as high, close as low, close,
                0 as volume,
                return_1d, return_1w, return_1m
            FROM v_latest_etfs
            ORDER BY ticker
        """).fetchdf()
        con.close()
        
        return result.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/etfs/{ticker}", response_model=List[FixedIncomeETF])
def get_etf_history(
    ticker: str,
    days: int = Query(30, ge=1, le=365, description="Number of days of history")
):
    """
    Get historical price data for a specific fixed-income ETF.
    
    Args:
        ticker: ETF ticker symbol (e.g., 'TLT', 'IEF', 'SHY')
        days: Number of days of historical data
    """
    ticker = ticker.upper()
    
    try:
        con = get_connection()
        result = con.execute(f"""
            SELECT *
            FROM fixed_income_etfs
            WHERE ticker = ?
                AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '{days}' DAY
            ORDER BY timestamp DESC
        """, [ticker]).fetchdf()
        con.close()
        
        if result.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
        
        return result.to_dict('records')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# =============================================================================
# ANALYTICS ENDPOINTS
# =============================================================================

@router.get("/analytics/spread")
def get_yield_spread(
    short_maturity: str = Query("2Y", description="Short-term maturity"),
    long_maturity: str = Query("10Y", description="Long-term maturity"),
    days: int = Query(30, ge=1, le=365, description="Number of days of history")
):
    """
    Calculate yield spread between two maturities (e.g., 10Y-2Y spread).
    
    Useful for analyzing yield curve steepness and predicting recessions.
    """
    valid_maturities = ['2Y', '5Y', '10Y', '30Y']
    if short_maturity not in valid_maturities or long_maturity not in valid_maturities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid maturity. Must be one of: {', '.join(valid_maturities)}"
        )
    
    try:
        con = get_connection()
        result = con.execute(f"""
            SELECT 
                s.timestamp,
                s.yield_rate as short_yield,
                l.yield_rate as long_yield,
                (l.yield_rate - s.yield_rate) as spread_bps,
                CASE 
                    WHEN (l.yield_rate - s.yield_rate) < 0 THEN 'INVERTED'
                    WHEN (l.yield_rate - s.yield_rate) < 50 THEN 'FLAT'
                    ELSE 'NORMAL'
                END as curve_shape
            FROM treasury_yields s
            JOIN treasury_yields l 
                ON DATE_TRUNC('day', s.timestamp) = DATE_TRUNC('day', l.timestamp)
            WHERE s.maturity = ?
                AND l.maturity = ?
                AND s.timestamp >= CURRENT_TIMESTAMP - INTERVAL '{days}' DAY
            ORDER BY s.timestamp DESC
        """, [short_maturity, long_maturity]).fetchdf()
        con.close()
        
        if result.empty:
            raise HTTPException(status_code=404, detail="No spread data available")
        
        return result.to_dict('records')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/analytics/correlation")
def get_yield_etf_correlation(
    maturity: str = Query("10Y", description="Treasury maturity"),
    ticker: str = Query("TLT", description="ETF ticker"),
    days: int = Query(90, ge=30, le=365, description="Analysis window in days")
):
    """
    Calculate correlation between Treasury yields and ETF prices.
    
    Shows how ETF prices move relative to yield changes.
    """
    try:
        con = get_connection()
        result = con.execute(f"""
            WITH correlation_data AS (
                SELECT 
                    ty.timestamp,
                    ty.yield_rate,
                    ty.change_1d as yield_change_bps,
                    etf.close as etf_price,
                    etf.return_1d as etf_return_pct
                FROM treasury_yields ty
                JOIN fixed_income_etfs etf 
                    ON DATE_TRUNC('day', ty.timestamp) = DATE_TRUNC('day', etf.timestamp)
                WHERE ty.maturity = ?
                    AND etf.ticker = ?
                    AND ty.timestamp >= CURRENT_TIMESTAMP - INTERVAL '{days}' DAY
                    AND ty.change_1d IS NOT NULL
                    AND etf.return_1d IS NOT NULL
            )
            SELECT 
                COUNT(*) as sample_size,
                ROUND(CORR(yield_change_bps, etf_return_pct)::NUMERIC, 4) as correlation,
                ROUND(AVG(yield_change_bps)::NUMERIC, 2) as avg_yield_change_bps,
                ROUND(AVG(etf_return_pct)::NUMERIC, 4) as avg_etf_return_pct
            FROM correlation_data
        """, [maturity, ticker.upper()]).fetchdf()
        con.close()
        
        if result.empty or result.iloc[0]['sample_size'] == 0:
            raise HTTPException(status_code=404, detail="Insufficient data for correlation")
        
        return result.to_dict('records')[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# =============================================================================
# SUMMARY ENDPOINT
# =============================================================================

@router.get("/summary", response_model=TreasurySummary)
def get_treasury_summary():
    """
    Get summary statistics for all Treasury data in the warehouse.
    """
    try:
        con = get_connection()
        
        # Get counts
        yields_count = con.execute("SELECT COUNT(*) FROM treasury_yields").fetchone()[0]
        etfs_count = con.execute("SELECT COUNT(*) FROM fixed_income_etfs").fetchone()[0]
        
        # Get maturities
        maturities = con.execute("""
            SELECT DISTINCT maturity FROM treasury_yields ORDER BY maturity
        """).fetchdf()['maturity'].tolist()
        
        # Get ETF tickers
        tickers = con.execute("""
            SELECT DISTINCT ticker FROM fixed_income_etfs ORDER BY ticker
        """).fetchdf()['ticker'].tolist()
        
        # Get date range
        date_range_yields = con.execute("""
            SELECT MIN(timestamp) as min_date, MAX(timestamp) as max_date 
            FROM treasury_yields
        """).fetchone()
        
        date_range_etfs = con.execute("""
            SELECT MIN(timestamp) as min_date, MAX(timestamp) as max_date 
            FROM fixed_income_etfs
        """).fetchone()
        
        con.close()
        
        return {
            'total_yield_records': yields_count,
            'total_etf_records': etfs_count,
            'maturities': maturities,
            'etf_tickers': tickers,
            'date_range': {
                'yields': {
                    'min': date_range_yields[0],
                    'max': date_range_yields[1]
                } if date_range_yields[0] else None,
                'etfs': {
                    'min': date_range_etfs[0],
                    'max': date_range_etfs[1]
                } if date_range_etfs[0] else None,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

