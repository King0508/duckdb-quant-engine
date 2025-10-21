"""
Sentiment API endpoints for quant-sql-warehouse.
Extends the main API with fixed-income news sentiment analysis capabilities.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import duckdb
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


def get_db_connection():
    """Get a database connection."""
    db_path = config.get_db_path()
    if not db_path.exists():
        raise HTTPException(
            status_code=503,
            detail="Database not found. Please run ETL to initialize the database.",
        )
    return duckdb.connect(str(db_path), read_only=True)


@router.get("/recent")
async def get_recent_sentiment(
    hours: int = Query(default=24, le=168, description="Hours to look back"),
    limit: int = Query(default=50, le=500, description="Max results"),
    high_impact_only: bool = Query(default=False, description="Filter for high-impact news only"),
):
    """
    Get recent news sentiment data.
    
    Returns news articles with ML-based sentiment analysis, entity extraction,
    and high-impact classification.
    """
    try:
        con = get_db_connection()
        
        query = """
        SELECT 
            news_id,
            timestamp,
            source,
            title,
            summary,
            sentiment_score,
            sentiment_label,
            confidence,
            fed_officials,
            economic_indicators,
            treasury_instruments,
            is_high_impact
        FROM news_sentiment
        WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL ? HOUR
        """
        
        params = [hours]
        
        if high_impact_only:
            query += " AND is_high_impact = TRUE"
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        result = con.execute(query, params).fetchdf()
        con.close()
        
        if len(result) == 0:
            return {"message": "No sentiment data found", "data": []}
        
        result["timestamp"] = result["timestamp"].astype(str)
        return {"data": result.to_dict("records"), "count": len(result)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeseries")
async def get_sentiment_timeseries(
    hours: int = Query(default=168, le=720, description="Hours to look back (max 30 days)"),
):
    """
    Get hourly aggregated sentiment time series.
    
    Returns aggregated sentiment metrics by hour for trend analysis.
    """
    try:
        con = get_db_connection()
        
        query = """
        SELECT 
            hour_timestamp as timestamp,
            avg_sentiment,
            sentiment_count,
            risk_on_count,
            risk_off_count,
            neutral_count,
            has_fomc,
            has_cpi,
            has_nfp,
            has_fed_speaker
        FROM sentiment_aggregates
        WHERE hour_timestamp >= CURRENT_TIMESTAMP - INTERVAL ? HOUR
        ORDER BY hour_timestamp ASC
        """
        
        result = con.execute(query, [hours]).fetchdf()
        con.close()
        
        if len(result) == 0:
            return {"message": "No aggregated data found", "data": []}
        
        result["timestamp"] = result["timestamp"].astype(str)
        return {"data": result.to_dict("records"), "count": len(result)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_sentiment_stats():
    """
    Get overall sentiment statistics.
    
    Returns summary statistics about the sentiment database.
    """
    try:
        con = get_db_connection()
        
        # Overall stats
        stats_query = """
        SELECT 
            COUNT(*) as total_news,
            COUNT(CASE WHEN is_high_impact THEN 1 END) as high_impact_count,
            AVG(sentiment_score) as avg_sentiment,
            MIN(timestamp) as earliest_news,
            MAX(timestamp) as latest_news
        FROM news_sentiment
        """
        
        overall = con.execute(stats_query).fetchone()
        
        # Sentiment distribution
        dist_query = """
        SELECT 
            sentiment_label,
            COUNT(*) as count,
            AVG(confidence) as avg_confidence
        FROM news_sentiment
        WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days'
        GROUP BY sentiment_label
        """
        
        distribution = con.execute(dist_query).fetchdf()
        
        # Top sources
        source_query = """
        SELECT 
            source,
            COUNT(*) as article_count,
            AVG(sentiment_score) as avg_sentiment
        FROM news_sentiment
        WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '30 days'
        GROUP BY source
        ORDER BY article_count DESC
        LIMIT 10
        """
        
        sources = con.execute(source_query).fetchdf()
        
        con.close()
        
        return {
            "overall": {
                "total_news": int(overall[0]) if overall[0] else 0,
                "high_impact_count": int(overall[1]) if overall[1] else 0,
                "avg_sentiment": float(overall[2]) if overall[2] else 0.0,
                "earliest_news": str(overall[3]) if overall[3] else None,
                "latest_news": str(overall[4]) if overall[4] else None,
            },
            "sentiment_distribution": distribution.to_dict("records"),
            "top_sources": sources.to_dict("records"),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
async def get_market_events(
    days: int = Query(default=30, le=365, description="Days to look back"),
    event_type: Optional[str] = Query(default=None, description="Filter by event type (FOMC, CPI, NFP, etc.)"),
):
    """
    Get major market events with sentiment impact.
    
    Returns economic events with pre/post sentiment analysis.
    """
    try:
        con = get_db_connection()
        
        query = """
        SELECT 
            event_id,
            timestamp,
            event_type,
            description,
            impact_level,
            pre_event_sentiment,
            post_event_sentiment,
            post_event_sentiment - pre_event_sentiment as sentiment_change
        FROM market_events
        WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL ? DAY
        """
        
        params = [days]
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.upper())
        
        query += " ORDER BY timestamp DESC"
        
        result = con.execute(query, params).fetchdf()
        con.close()
        
        if len(result) == 0:
            return {"message": "No events found", "data": []}
        
        result["timestamp"] = result["timestamp"].astype(str)
        return {"data": result.to_dict("records"), "count": len(result)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals")
async def get_trading_signals(
    days: int = Query(default=30, le=90, description="Days to look back"),
    signal_type: Optional[str] = Query(default=None, description="Filter by signal type"),
):
    """
    Get sentiment-based trading signals with performance.
    
    Returns trading signals generated from sentiment analysis with backtested results.
    """
    try:
        con = get_db_connection()
        
        query = """
        SELECT 
            signal_id,
            signal_timestamp,
            signal_type,
            signal_strength,
            sentiment_input,
            market_input,
            entry_price,
            exit_price,
            return_pct,
            pnl,
            hold_hours
        FROM sentiment_signals
        WHERE signal_timestamp >= CURRENT_TIMESTAMP - INTERVAL ? DAY
        """
        
        params = [days]
        
        if signal_type:
            query += " AND signal_type = ?"
            params.append(signal_type.upper())
        
        query += " ORDER BY signal_timestamp DESC"
        
        result = con.execute(query, params).fetchdf()
        con.close()
        
        if len(result) == 0:
            return {"message": "No signals found", "data": []}
        
        result["signal_timestamp"] = result["signal_timestamp"].astype(str)
        return {"data": result.to_dict("records"), "count": len(result)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/performance")
async def get_signal_performance():
    """
    Get aggregated performance metrics for trading signals.
    
    Returns summary statistics of signal performance by type.
    """
    try:
        con = get_db_connection()
        
        query = """
        SELECT 
            signal_type,
            COUNT(*) as total_signals,
            SUM(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) as winning_trades,
            ROUND(100.0 * SUM(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate_pct,
            ROUND(AVG(return_pct), 3) as avg_return_pct,
            ROUND(SUM(pnl), 2) as total_pnl,
            ROUND(AVG(hold_hours), 1) as avg_hold_hours,
            ROUND(MAX(return_pct), 3) as max_return_pct,
            ROUND(MIN(return_pct), 3) as min_return_pct
        FROM sentiment_signals
        WHERE exit_timestamp IS NOT NULL
        GROUP BY signal_type
        ORDER BY total_pnl DESC
        """
        
        result = con.execute(query).fetchdf()
        con.close()
        
        if len(result) == 0:
            return {"message": "No completed signals found", "data": []}
        
        return {"data": result.to_dict("records")}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_news(
    keyword: str = Query(..., min_length=2, description="Search keyword"),
    days: int = Query(default=30, le=365, description="Days to look back"),
    limit: int = Query(default=50, le=200, description="Max results"),
):
    """
    Search news articles by keyword.
    
    Searches through titles and summaries for specified keyword.
    """
    try:
        con = get_db_connection()
        
        query = """
        SELECT 
            news_id,
            timestamp,
            source,
            title,
            summary,
            sentiment_score,
            sentiment_label,
            confidence
        FROM news_sentiment
        WHERE (title ILIKE ? OR summary ILIKE ?)
            AND timestamp >= CURRENT_TIMESTAMP - INTERVAL ? DAY
        ORDER BY timestamp DESC
        LIMIT ?
        """
        
        search_pattern = f"%{keyword}%"
        result = con.execute(query, [search_pattern, search_pattern, days, limit]).fetchdf()
        con.close()
        
        if len(result) == 0:
            return {"message": f"No articles found matching '{keyword}'", "data": []}
        
        result["timestamp"] = result["timestamp"].astype(str)
        return {"data": result.to_dict("records"), "count": len(result)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

