"""
Build Analytics Tables
Populates derived tables from raw data:
- market_events from treasury_yields
- sentiment_aggregates from news_sentiment
- sentiment_signals from sentiment + market data
"""

import duckdb
from pathlib import Path
from datetime import datetime, timezone
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def connect_warehouse():
    """Connect to warehouse database."""
    warehouse_path = Path(__file__).parent.parent / "warehouse.duckdb"
    return duckdb.connect(str(warehouse_path))


def populate_market_events(conn):
    """
    Populate market_events table with significant Treasury yield movements.
    """
    print("\n=== Populating market_events ===")

    # Clear existing events
    conn.execute("DELETE FROM market_events")

    # Insert significant yield movements as market events
    # Use daily changes to identify significant moves
    query = """
    INSERT INTO market_events (timestamp, event_type, description, impact_level)
    SELECT 
        timestamp,
        CASE 
            WHEN ABS(change_1d) >= 0.15 THEN 'MAJOR_MOVE'
            WHEN ABS(change_1d) >= 0.10 THEN 'SIGNIFICANT_MOVE'
            ELSE 'YIELD_MOVE'
        END as event_type,
        maturity || ' Treasury yield ' || 
        CASE WHEN change_1d > 0 THEN 'up ' ELSE 'down ' END ||
        CAST(ROUND(ABS(change_1d * 100), 1) AS VARCHAR) || ' bps' as description,
        CASE 
            WHEN ABS(change_1d) >= 0.15 THEN 'high'
            WHEN ABS(change_1d) >= 0.10 THEN 'medium'
            ELSE 'low'
        END as impact_level
    FROM treasury_yields
    WHERE change_1d IS NOT NULL
        AND ABS(change_1d) >= 0.08  -- Only track moves >= 8 bps (0.08%)
    ORDER BY timestamp
    """

    result = conn.execute(query)
    count = conn.execute("SELECT COUNT(*) FROM market_events").fetchone()[0]
    print(f"[OK] Created {count} market events from Treasury yield movements")

    return count


def populate_sentiment_aggregates(conn):
    """
    Populate sentiment_aggregates table from news_sentiment.
    Creates hourly aggregates of sentiment metrics.
    """
    print("\n=== Populating sentiment_aggregates ===")

    # Clear existing aggregates
    conn.execute("DELETE FROM sentiment_aggregates")

    # Create hourly aggregates
    query = """
    INSERT INTO sentiment_aggregates (
        hour_timestamp,
        sentiment_count,
        avg_sentiment,
        risk_on_count,
        risk_off_count,
        neutral_count
    )
    SELECT 
        DATE_TRUNC('hour', timestamp) as hour_timestamp,
        COUNT(*) as sentiment_count,
        AVG(sentiment_score) as avg_sentiment,
        SUM(CASE WHEN sentiment_label = 'risk-on' THEN 1 ELSE 0 END) as risk_on_count,
        SUM(CASE WHEN sentiment_label = 'risk-off' THEN 1 ELSE 0 END) as risk_off_count,
        SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count
    FROM news_sentiment
    GROUP BY DATE_TRUNC('hour', timestamp)
    ORDER BY hour_timestamp
    """

    result = conn.execute(query)
    count = conn.execute("SELECT COUNT(*) FROM sentiment_aggregates").fetchone()[0]
    print(f"[OK] Created {count} hourly sentiment aggregates")

    return count


def populate_sentiment_signals(conn):
    """
    Generate trading signals from sentiment extremes.
    Signals are generated when sentiment is strongly positive or negative.
    """
    print("\n=== Populating sentiment_signals ===")

    # Clear existing signals
    conn.execute("DELETE FROM sentiment_signals")

    # Generate signals based on sentiment extremes
    # For now, just create signals - entry/exit prices would need backtesting
    query = """
    INSERT INTO sentiment_signals (
        signal_timestamp,
        signal_type,
        signal_strength,
        sentiment_input,
        market_input
    )
    SELECT 
        timestamp as signal_timestamp,
        CASE 
            WHEN sentiment_score >= 0.3 THEN 'BUY_TREASURIES'
            WHEN sentiment_score <= -0.3 THEN 'SELL_TREASURIES'
            ELSE 'HOLD'
        END as signal_type,
        ABS(sentiment_score) as signal_strength,
        sentiment_score as sentiment_input,
        NULL as market_input
    FROM news_sentiment
    WHERE is_high_impact = TRUE
        AND ABS(sentiment_score) >= 0.3
    ORDER BY timestamp
    """

    result = conn.execute(query)
    count = conn.execute("SELECT COUNT(*) FROM sentiment_signals").fetchone()[0]
    print(f"[OK] Created {count} trading signals from high-impact news")

    return count


def verify_tables(conn):
    """Verify all tables have data."""
    print("\n=== Verification ===")

    tables = [
        "treasury_yields",
        "fixed_income_etfs",
        "news_sentiment",
        "market_events",
        "sentiment_aggregates",
        "sentiment_signals",
    ]

    for table in tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"[OK] {table}: {count:,} records")
        except Exception as e:
            print(f"[ERROR] {table}: {e}")


def main():
    """Main execution."""
    print("=" * 60)
    print("Building Analytics Tables for Fixed Income Sentiment Platform")
    print("=" * 60)

    conn = connect_warehouse()

    try:
        # Build derived tables
        market_events_count = populate_market_events(conn)
        aggregates_count = populate_sentiment_aggregates(conn)
        signals_count = populate_sentiment_signals(conn)

        # Commit changes
        conn.commit()

        # Verify
        verify_tables(conn)

        print("\n" + "=" * 60)
        print("[SUCCESS] Analytics tables built successfully!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  - Market Events: {market_events_count}")
        print(f"  - Sentiment Aggregates: {aggregates_count}")
        print(f"  - Trading Signals: {signals_count}")
        print("\n[READY] Dashboard tabs should now be fully functional!")

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
