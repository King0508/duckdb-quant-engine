"""
Pytest configuration and fixtures.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys
import duckdb

sys.path.insert(0, str(Path(__file__).parent.parent))
import config


@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def test_db_path(test_data_dir):
    """Create a test database path."""
    return test_data_dir / "test_warehouse.duckdb"


@pytest.fixture(scope="function")
def db_connection(test_db_path):
    """Create a test database connection."""
    con = duckdb.connect(str(test_db_path))

    # Create test schema
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS symbols (
            symbol_id INTEGER PRIMARY KEY,
            ticker VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            sector VARCHAR,
            industry VARCHAR,
            market_cap BIGINT,
            exchange VARCHAR DEFAULT 'NASDAQ',
            currency VARCHAR DEFAULT 'USD',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS bars (
            symbol_id INTEGER NOT NULL,
            ts TIMESTAMP NOT NULL,
            open DOUBLE NOT NULL,
            high DOUBLE NOT NULL,
            low DOUBLE NOT NULL,
            close DOUBLE NOT NULL,
            volume BIGINT NOT NULL,
            PRIMARY KEY (symbol_id, ts)
        )
    """
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS trades (
            symbol_id INTEGER NOT NULL,
            ts TIMESTAMP NOT NULL,
            price DOUBLE NOT NULL,
            size BIGINT NOT NULL,
            side VARCHAR,
            PRIMARY KEY (symbol_id, ts, price, size)
        )
    """
    )

    yield con

    con.close()


@pytest.fixture
def sample_symbols_data():
    """Sample symbols data for testing."""
    return [
        {
            "symbol_id": 1,
            "ticker": "TEST",
            "name": "Test Company",
            "sector": "Technology",
            "industry": "Software",
            "market_cap": 1000000000,
            "exchange": "NASDAQ",
            "currency": "USD",
        },
        {
            "symbol_id": 2,
            "ticker": "DEMO",
            "name": "Demo Corp",
            "sector": "Finance",
            "industry": "Banking",
            "market_cap": 5000000000,
            "exchange": "NYSE",
            "currency": "USD",
        },
    ]


@pytest.fixture
def sample_bars_data():
    """Sample bars data for testing."""
    return [
        {
            "symbol_id": 1,
            "ts": "2024-01-01 16:00:00",
            "open": 100.0,
            "high": 105.0,
            "low": 99.0,
            "close": 103.0,
            "volume": 1000000,
        },
        {
            "symbol_id": 1,
            "ts": "2024-01-02 16:00:00",
            "open": 103.0,
            "high": 108.0,
            "low": 102.0,
            "close": 107.0,
            "volume": 1200000,
        },
    ]


@pytest.fixture
def sample_trades_data():
    """Sample trades data for testing."""
    return [
        {
            "symbol_id": 1,
            "ts": "2024-01-01 10:00:00",
            "price": 100.5,
            "size": 100,
            "side": "BUY",
        },
        {
            "symbol_id": 1,
            "ts": "2024-01-01 10:01:00",
            "price": 100.75,
            "size": 200,
            "side": "SELL",
        },
    ]
