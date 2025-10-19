"""
Tests for the REST API.
"""
import pytest
from fastapi.testclient import TestClient
import tempfile
from pathlib import Path
import sys
import duckdb

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def test_db():
    """Create a test database with sample data."""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".duckdb")
    db_path = Path(temp_db.name)
    temp_db.close()
    
    con = duckdb.connect(str(db_path))
    
    # Create schema
    con.execute("""
        CREATE TABLE symbols (
            symbol_id INTEGER PRIMARY KEY,
            ticker VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            sector VARCHAR,
            industry VARCHAR,
            market_cap BIGINT,
            exchange VARCHAR,
            currency VARCHAR
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
            volume BIGINT,
            PRIMARY KEY (symbol_id, ts)
        )
    """)
    
    con.execute("""
        CREATE TABLE trades (
            symbol_id INTEGER NOT NULL,
            ts TIMESTAMP NOT NULL,
            price DOUBLE,
            size BIGINT,
            side VARCHAR
        )
    """)
    
    # Insert test data
    con.execute("""
        INSERT INTO symbols VALUES
        (1, 'TEST', 'Test Company', 'Technology', 'Software', 1000000000, 'NASDAQ', 'USD')
    """)
    
    con.execute("""
        INSERT INTO bars VALUES
        (1, '2024-01-01 16:00:00', 100.0, 105.0, 99.0, 103.0, 1000000),
        (1, '2024-01-02 16:00:00', 103.0, 108.0, 102.0, 107.0, 1200000)
    """)
    
    con.execute("""
        INSERT INTO trades VALUES
        (1, '2024-01-01 10:00:00', 100.5, 100, 'BUY'),
        (1, '2024-01-01 10:01:00', 100.75, 200, 'SELL')
    """)
    
    # Create views
    con.execute("""
        CREATE VIEW features_returns_rsi AS
        SELECT 
            s.ticker as symbol,
            s.name,
            b.ts,
            b.close as price,
            b.volume,
            0.0 as return_1d_pct,
            0.0 as return_5d_pct,
            0.0 as return_20d_pct,
            0.0 as log_return_1d,
            50.0 as rsi_14,
            50.0 as rsi_28,
            'NEUTRAL' as rsi_signal
        FROM bars b
        JOIN symbols s ON b.symbol_id = s.symbol_id
    """)
    
    con.execute("""
        CREATE VIEW features_vwap_volume AS
        SELECT 
            s.ticker as symbol,
            s.name,
            DATE_TRUNC('day', b.ts) as date,
            b.ts,
            b.close as price,
            b.volume,
            b.close as vwap,
            b.volume as avg_volume_20,
            1.0 as volume_ratio,
            'STABLE' as volume_trend,
            0.0 as price_vs_vwap_pct,
            'NORMAL' as volume_category,
            b.volume as day_cumulative_volume
        FROM bars b
        JOIN symbols s ON b.symbol_id = s.symbol_id
    """)
    
    con.close()
    
    yield db_path
    
    # Cleanup
    db_path.unlink()


@pytest.fixture
def client(test_db, monkeypatch):
    """Create a test client with mocked database path."""
    import config
    monkeypatch.setattr(config, "DB_PATH", test_db)
    
    from api.main import app
    return TestClient(app)


class TestAPIEndpoints:
    """Test API endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "symbols_count" in data
    
    def test_get_symbols(self, client):
        """Test get symbols endpoint."""
        response = client.get("/symbols")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "ticker" in data[0]
        assert "name" in data[0]
    
    def test_get_symbol_by_ticker(self, client):
        """Test get specific symbol endpoint."""
        response = client.get("/symbols/TEST")
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "TEST"
        assert data["name"] == "Test Company"
    
    def test_get_symbol_not_found(self, client):
        """Test get non-existent symbol."""
        response = client.get("/symbols/NONEXISTENT")
        assert response.status_code == 404
    
    def test_get_bars(self, client):
        """Test get bars endpoint."""
        response = client.get("/bars/TEST")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "open" in data[0]
        assert "high" in data[0]
        assert "low" in data[0]
        assert "close" in data[0]
        assert "volume" in data[0]
    
    def test_get_bars_with_limit(self, client):
        """Test get bars with limit parameter."""
        response = client.get("/bars/TEST?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
    
    def test_get_trades(self, client):
        """Test get trades endpoint."""
        response = client.get("/trades/TEST")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "price" in data[0]
        assert "size" in data[0]
        assert "side" in data[0]
    
    def test_get_rsi_analysis(self, client):
        """Test RSI analysis endpoint."""
        response = client.get("/analytics/rsi/TEST")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_vwap_analysis(self, client):
        """Test VWAP analysis endpoint."""
        response = client.get("/analytics/vwap/TEST")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_performance(self, client):
        """Test performance analysis endpoint."""
        response = client.get("/analytics/performance?days=30&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_trading_signals(self, client):
        """Test trading signals endpoint."""
        response = client.get("/analytics/signals")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAPIErrorHandling:
    """Test API error handling."""
    
    def test_invalid_endpoint(self, client):
        """Test accessing invalid endpoint."""
        response = client.get("/invalid/endpoint")
        assert response.status_code == 404
    
    def test_invalid_query_parameters(self, client):
        """Test invalid query parameters."""
        response = client.get("/bars/TEST?limit=99999999")
        # Should either return 422 (validation error) or successfully limit
        assert response.status_code in [200, 422]

