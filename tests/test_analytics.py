"""
Tests for analytics functionality.
"""
import pytest
from pathlib import Path
import sys
import tempfile
import duckdb

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def analytics_test_db():
    """Create a test database with sample data for analytics."""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".duckdb")
    db_path = Path(temp_db.name)
    temp_db.close()
    
    con = duckdb.connect(str(db_path))
    
    # Create minimal schema
    con.execute("""
        CREATE TABLE symbols (
            symbol_id INTEGER PRIMARY KEY,
            ticker VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            sector VARCHAR
        )
    """)
    
    con.execute("""
        CREATE TABLE bars (
            symbol_id INTEGER NOT NULL,
            ts TIMESTAMP NOT NULL,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            volume BIGINT
        )
    """)
    
    # Insert test data
    con.execute("INSERT INTO symbols VALUES (1, 'TEST', 'Test Company', 'Technology')")
    
    # Insert multiple bars for time series analysis
    for i in range(30):
        con.execute(f"""
            INSERT INTO bars VALUES
            (1, '2024-01-{i+1:02d} 16:00:00', 100.0, 105.0, 99.0, 102.0 + {i}, 1000000)
        """)
    
    # Create test views
    con.execute("""
        CREATE VIEW features_returns_rsi AS
        SELECT 
            s.ticker as symbol,
            s.name,
            b.ts,
            b.close as price,
            b.volume,
            (b.close - 100.0) / 100.0 * 100 as return_1d_pct,
            0.0 as return_5d_pct,
            0.0 as return_20d_pct,
            0.0 as log_return_1d,
            50.0 as rsi_14,
            50.0 as rsi_28,
            'NEUTRAL' as rsi_signal
        FROM bars b
        JOIN symbols s ON b.symbol_id = s.symbol_id
    """)
    
    con.close()
    
    yield db_path
    
    # Cleanup
    db_path.unlink()


class TestAnalyticsEngine:
    """Test analytics engine functionality."""
    
    def test_analytics_engine_initialization(self, analytics_test_db):
        """Test analytics engine initialization."""
        from analytics.run_analysis import AnalyticsEngine
        
        with AnalyticsEngine(analytics_test_db) as engine:
            assert engine.con is not None
    
    def test_get_latest_prices(self, analytics_test_db):
        """Test getting latest prices."""
        from analytics.run_analysis import AnalyticsEngine
        
        with AnalyticsEngine(analytics_test_db) as engine:
            df = engine.get_latest_prices(limit=10)
            assert len(df) > 0
            assert 'symbol' in df.columns
            assert 'latest_price' in df.columns
    
    def test_get_top_performers(self, analytics_test_db):
        """Test getting top performers."""
        from analytics.run_analysis import AnalyticsEngine
        
        with AnalyticsEngine(analytics_test_db) as engine:
            df = engine.get_top_performers(days=30, limit=10)
            assert 'symbol' in df.columns
            assert 'total_return_pct' in df.columns
    
    def test_database_not_found(self):
        """Test error handling when database doesn't exist."""
        from analytics.run_analysis import AnalyticsEngine
        
        with pytest.raises(FileNotFoundError):
            AnalyticsEngine(Path("/nonexistent/database.duckdb"))


class TestAnalyticalQueries:
    """Test specific analytical query patterns."""
    
    def test_aggregation_query(self, analytics_test_db):
        """Test aggregation queries."""
        con = duckdb.connect(str(analytics_test_db))
        
        result = con.execute("""
            SELECT 
                symbol_id,
                COUNT(*) as bar_count,
                AVG(close) as avg_close,
                MAX(high) as max_high,
                MIN(low) as min_low
            FROM bars
            GROUP BY symbol_id
        """).fetchdf()
        
        assert len(result) > 0
        assert result['bar_count'].iloc[0] == 30
        
        con.close()
    
    def test_window_function_query(self, analytics_test_db):
        """Test window function queries."""
        con = duckdb.connect(str(analytics_test_db))
        
        result = con.execute("""
            SELECT 
                ts,
                close,
                LAG(close, 1) OVER (ORDER BY ts) as prev_close,
                AVG(close) OVER (ORDER BY ts ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) as ma_5
            FROM bars
            WHERE symbol_id = 1
            ORDER BY ts
        """).fetchdf()
        
        assert len(result) > 0
        assert 'prev_close' in result.columns
        assert 'ma_5' in result.columns
        
        con.close()
    
    def test_join_query(self, analytics_test_db):
        """Test join queries."""
        con = duckdb.connect(str(analytics_test_db))
        
        result = con.execute("""
            SELECT 
                s.ticker,
                s.name,
                b.ts,
                b.close
            FROM bars b
            JOIN symbols s ON b.symbol_id = s.symbol_id
            ORDER BY b.ts DESC
            LIMIT 10
        """).fetchdf()
        
        assert len(result) > 0
        assert 'ticker' in result.columns
        assert 'name' in result.columns
        
        con.close()

