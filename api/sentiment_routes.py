"""
Sentiment API routes - REST endpoints for news sentiment and trading signals.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import duckdb
from pydantic import BaseModel

import config

router = APIRouter(prefix="/sentiment", tags=["Sentiment Analytics"])


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class NewsSentiment(BaseModel):
    """News sentiment data"""
    news_id: int
    timestamp: datetime
    source: str
    title: str
    summary: Optional[str] = None
    link: Optional[str] = None
    sentiment_score: float
    sentiment_label: str
    confidence: Optional[float] = None
    is_high_impact: bool
    fed_officials: Optional[List[str]] = None
    economic_indicators: Optional[List[str]] = None


class SentimentAggregate(BaseModel):
    """Hourly sentiment aggregate"""
    hour_timestamp: datetime
    avg_sentiment: float
    sentiment_count: int
    risk_on_count: int
    risk_off_count: int
    neutral_count: int
    has_fomc: bool
    has_cpi: bool
    has_nfp: bool
    has_fed_speaker: bool


class TradingSignal(BaseModel):
    """Trading signal data"""
    signal_id: int
    signal_timestamp: datetime
    signal_type: str
    signal_strength: Optional[float] = None
    sentiment_input: Optional[float] = None
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    return_pct: Optional[float] = None


class SentimentSummary(BaseModel):
    """Summary statistics for sentiment data"""
    total_news: int
    high_impact_news: int
    date_range: dict
    avg_sentiment_24h: Optional[float] = None
    sentiment_distribution: dict


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_connection():
    """Get database connection."""
    db_path = config.get_db_path()
    return duckdb.connect(str(db_path), read_only=True)


# =============================================================================
# NEWS SENTIMENT ENDPOINTS
# =============================================================================

@router.get("/news/recent", response_model=List[NewsSentiment])
def get_recent_news(
    hours: int = Query(24, ge=1, le=168, description="Hours of history"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results"),
    high_impact_only: bool = Query(False, description="Show only high-impact news")
):
    """
    Get recent news with ML sentiment analysis.
    
    Args:
        hours: Number of hours of history to retrieve
        limit: Maximum number of news items to return
        high_impact_only: Filter for high-impact news only
    """
    try:
        con = get_connection()
        
        high_impact_filter = "AND is_high_impact = TRUE" if high_impact_only else ""
        
        result = con.execute(f"""
            SELECT 
                news_id, timestamp, source, title, summary, link,
                sentiment_score, sentiment_label, confidence, is_high_impact,
                fed_officials, economic_indicators
            FROM news_sentiment
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '{hours}' HOUR
                {high_impact_filter}
            ORDER BY timestamp DESC
            LIMIT {limit}
        """).fetchdf()
        con.close()
        
        if result.empty:
            return []
        
        return result.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/news/search")
def search_news(
    keyword: str = Query(..., description="Search keyword"),
    days: int = Query(30, ge=1, le=90, description="Days to search"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results")
):
    """
    Search news by keyword in title and summary.
    
    Args:
        keyword: Search term (case-insensitive)
        days: Number of days to search
        limit: Maximum number of results
    """
    try:
        con = get_connection()
        result = con.execute(f"""
            SELECT 
                news_id, timestamp, source, title, summary,
                sentiment_score, sentiment_label, confidence, is_high_impact
            FROM news_sentiment
            WHERE (
                    LOWER(title) LIKE LOWER(?)
                    OR LOWER(summary) LIKE LOWER(?)
                )
                AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '{days}' DAY
            ORDER BY timestamp DESC
            LIMIT {limit}
        """, [f'%{keyword}%', f'%{keyword}%']).fetchdf()
        con.close()
        
        return result.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/news/high-impact", response_model=List[NewsSentiment])
def get_high_impact_news(
    hours: int = Query(24, ge=1, le=168, description="Hours of history")
):
    """
    Get recent high-impact news (FOMC, CPI, Fed speakers, etc.).
    
    High-impact news items are those that typically move markets.
    """
    try:
        con = get_connection()
        result = con.execute(f"""
            SELECT * FROM v_recent_high_impact
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '{hours}' HOUR
        """).fetchdf()
        con.close()
        
        return result.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# =============================================================================
# SENTIMENT AGGREGATES ENDPOINTS
# =============================================================================

@router.get("/aggregates/timeseries", response_model=List[SentimentAggregate])
def get_sentiment_timeseries(
    hours: int = Query(168, ge=24, le=720, description="Hours of history (1-30 days)")
):
    """
    Get hourly sentiment aggregates over time.
    
    Useful for plotting sentiment trends and identifying market-moving periods.
    """
    try:
        con = get_connection()
        result = con.execute(f"""
            SELECT * FROM v_sentiment_trend
            WHERE hour_timestamp >= CURRENT_TIMESTAMP - INTERVAL '{hours}' HOUR
            ORDER BY hour_timestamp DESC
        """).fetchdf()
        con.close()
        
        return result.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/aggregates/current")
def get_current_sentiment():
    """
    Get the current sentiment reading (last hour aggregate).
    
    Returns a single sentiment snapshot for the most recent hour.
    """
    try:
        con = get_connection()
        result = con.execute("""
            SELECT * FROM sentiment_aggregates
            ORDER BY hour_timestamp DESC
            LIMIT 1
        """).fetchdf()
        con.close()
        
        if result.empty:
            raise HTTPException(status_code=404, detail="No sentiment data available")
        
        return result.to_dict('records')[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# =============================================================================
# TRADING SIGNALS ENDPOINTS
# =============================================================================

@router.get("/signals/recent", response_model=List[TradingSignal])
def get_recent_signals(
    days: int = Query(30, ge=1, le=90, description="Days of history"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type")
):
    """
    Get recent trading signals generated from sentiment analysis.
    
    Args:
        days: Number of days of signal history
        signal_type: Optional filter by signal type (e.g., 'BUY_TLT', 'SELL_TLT')
    """
    try:
        con = get_connection()
        
        type_filter = f"AND signal_type = '{signal_type}'" if signal_type else ""
        
        result = con.execute(f"""
            SELECT *
            FROM sentiment_signals
            WHERE signal_timestamp >= CURRENT_TIMESTAMP - INTERVAL '{days}' DAY
                {type_filter}
            ORDER BY signal_timestamp DESC
        """).fetchdf()
        con.close()
        
        return result.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/signals/performance")
def get_signal_performance():
    """
    Get performance statistics for trading signals.
    
    Returns win rate, average return, total P&L, etc. grouped by signal type.
    """
    try:
        con = get_connection()
        result = con.execute("SELECT * FROM v_signal_performance").fetchdf()
        con.close()
        
        if result.empty:
            return {"message": "No closed signals available for performance analysis"}
        
        return result.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# =============================================================================
# ANALYTICS ENDPOINTS
# =============================================================================

@router.get("/analytics/sentiment-distribution")
def get_sentiment_distribution(
    days: int = Query(30, ge=1, le=90, description="Analysis period in days")
):
    """
    Get sentiment label distribution (risk-on, risk-off, neutral).
    
    Shows the overall market sentiment bias over the analysis period.
    """
    try:
        con = get_connection()
        result = con.execute(f"""
            SELECT 
                sentiment_label,
                COUNT(*) as count,
                ROUND(AVG(sentiment_score)::NUMERIC, 4) as avg_score,
                ROUND(AVG(confidence)::NUMERIC, 4) as avg_confidence
            FROM news_sentiment
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '{days}' DAY
            GROUP BY sentiment_label
            ORDER BY count DESC
        """).fetchdf()
        con.close()
        
        return result.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/analytics/top-entities")
def get_top_entities(
    entity_type: str = Query("fed_officials", description="Entity type to analyze"),
    days: int = Query(30, ge=1, le=90, description="Analysis period")
):
    """
    Get most frequently mentioned entities in news.
    
    Args:
        entity_type: Type of entity ('fed_officials', 'economic_indicators', 'treasury_instruments')
        days: Number of days to analyze
    """
    valid_types = ['fed_officials', 'economic_indicators', 'treasury_instruments']
    if entity_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entity_type. Must be one of: {', '.join(valid_types)}"
        )
    
    try:
        con = get_connection()
        result = con.execute(f"""
            WITH entities AS (
                SELECT 
                    UNNEST({entity_type}) as entity,
                    sentiment_score
                FROM news_sentiment
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '{days}' DAY
                    AND array_length({entity_type}) > 0
            )
            SELECT 
                entity,
                COUNT(*) as mention_count,
                ROUND(AVG(sentiment_score)::NUMERIC, 4) as avg_sentiment
            FROM entities
            GROUP BY entity
            ORDER BY mention_count DESC
            LIMIT 20
        """).fetchdf()
        con.close()
        
        return result.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# =============================================================================
# SUMMARY ENDPOINT
# =============================================================================

@router.get("/summary", response_model=SentimentSummary)
def get_sentiment_summary():
    """
    Get summary statistics for all sentiment data in the warehouse.
    """
    try:
        con = get_connection()
        
        # Get counts
        total_news = con.execute("SELECT COUNT(*) FROM news_sentiment").fetchone()[0]
        high_impact = con.execute("""
            SELECT COUNT(*) FROM news_sentiment WHERE is_high_impact = TRUE
        """).fetchone()[0]
        
        # Get date range
        date_range = con.execute("""
            SELECT MIN(timestamp) as min_date, MAX(timestamp) as max_date 
            FROM news_sentiment
        """).fetchone()
        
        # Get 24h average sentiment
        avg_24h = con.execute("""
            SELECT AVG(sentiment_score) 
            FROM news_sentiment
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
        """).fetchone()[0]
        
        # Get sentiment distribution
        distribution = con.execute("""
            SELECT 
                sentiment_label,
                COUNT(*) as count
            FROM news_sentiment
            GROUP BY sentiment_label
        """).fetchdf()
        
        con.close()
        
        return {
            'total_news': total_news,
            'high_impact_news': high_impact,
            'date_range': {
                'min': date_range[0],
                'max': date_range[1]
            } if date_range[0] else None,
            'avg_sentiment_24h': float(avg_24h) if avg_24h else None,
            'sentiment_distribution': {
                row['sentiment_label']: int(row['count']) 
                for _, row in distribution.iterrows()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

