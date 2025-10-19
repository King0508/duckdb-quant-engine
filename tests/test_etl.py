"""
Tests for ETL functionality.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from etl.data_validator import DataValidator


class TestDataValidator:
    """Test data validation logic."""
    
    def test_validate_symbols_success(self):
        """Test successful symbol validation."""
        validator = DataValidator()
        df = pd.DataFrame([
            {"symbol_id": 1, "ticker": "AAPL", "name": "Apple Inc."},
            {"symbol_id": 2, "ticker": "MSFT", "name": "Microsoft"}
        ])
        
        assert validator.validate_symbols(df) is True
        assert len(validator.errors) == 0
    
    def test_validate_symbols_duplicate_ticker(self):
        """Test symbol validation with duplicate tickers."""
        validator = DataValidator()
        df = pd.DataFrame([
            {"symbol_id": 1, "ticker": "AAPL", "name": "Apple Inc."},
            {"symbol_id": 2, "ticker": "AAPL", "name": "Apple Inc."}
        ])
        
        assert validator.validate_symbols(df) is False
        assert len(validator.errors) > 0
    
    def test_validate_symbols_missing_column(self):
        """Test symbol validation with missing required column."""
        validator = DataValidator()
        df = pd.DataFrame([
            {"symbol_id": 1, "name": "Apple Inc."}  # Missing ticker
        ])
        
        assert validator.validate_symbols(df) is False
        assert any("ticker" in error for error in validator.errors)
    
    def test_validate_bars_success(self):
        """Test successful bars validation."""
        validator = DataValidator()
        df = pd.DataFrame([
            {
                "symbol_id": 1,
                "ts": "2024-01-01",
                "open": 100.0,
                "high": 105.0,
                "low": 98.0,
                "close": 103.0,
                "volume": 1000000
            }
        ])
        
        assert validator.validate_bars(df) is True
        assert len(validator.errors) == 0
    
    def test_validate_bars_invalid_prices(self):
        """Test bars validation with invalid prices."""
        validator = DataValidator()
        df = pd.DataFrame([
            {
                "symbol_id": 1,
                "ts": "2024-01-01",
                "open": -10.0,  # Invalid negative price
                "high": 105.0,
                "low": 98.0,
                "close": 103.0,
                "volume": 1000000
            }
        ])
        
        assert validator.validate_bars(df) is False
        assert len(validator.errors) > 0
    
    def test_validate_bars_high_low_relationship(self):
        """Test bars validation with invalid high/low relationship."""
        validator = DataValidator()
        df = pd.DataFrame([
            {
                "symbol_id": 1,
                "ts": "2024-01-01",
                "open": 100.0,
                "high": 95.0,  # High less than open - invalid
                "low": 98.0,
                "close": 103.0,
                "volume": 1000000
            }
        ])
        
        # This should generate warnings
        validator.validate_bars(df)
        assert len(validator.warnings) > 0
    
    def test_validate_trades_success(self):
        """Test successful trades validation."""
        validator = DataValidator()
        df = pd.DataFrame([
            {
                "symbol_id": 1,
                "ts": "2024-01-01 10:00:00",
                "price": 100.5,
                "size": 100,
                "side": "BUY"
            }
        ])
        
        assert validator.validate_trades(df) is True
        assert len(validator.errors) == 0
    
    def test_validate_trades_invalid_side(self):
        """Test trades validation with invalid side."""
        validator = DataValidator()
        df = pd.DataFrame([
            {
                "symbol_id": 1,
                "ts": "2024-01-01 10:00:00",
                "price": 100.5,
                "size": 100,
                "side": "INVALID"  # Invalid side
            }
        ])
        
        assert validator.validate_trades(df) is False
        assert len(validator.errors) > 0


class TestDataGeneration:
    """Test data generation logic."""
    
    def test_market_data_generator_imports(self):
        """Test that market data generator can be imported."""
        from etl.generate_data import MarketDataGenerator
        assert MarketDataGenerator is not None
    
    def test_generator_initialization(self):
        """Test generator initialization."""
        from etl.generate_data import MarketDataGenerator
        
        generator = MarketDataGenerator("2024-01-01", "2024-01-31")
        assert generator.start_date.year == 2024
        assert generator.start_date.month == 1
        assert generator.end_date.month == 1
    
    def test_generate_symbols(self):
        """Test symbol generation."""
        from etl.generate_data import MarketDataGenerator
        
        generator = MarketDataGenerator("2024-01-01", "2024-01-31")
        symbols = generator.generate_symbols()
        
        assert len(symbols) > 0
        assert all("ticker" in s for s in symbols)
        assert all("name" in s for s in symbols)
        assert all("symbol_id" in s for s in symbols)
    
    def test_generate_bars(self):
        """Test bars generation."""
        from etl.generate_data import MarketDataGenerator
        
        generator = MarketDataGenerator("2024-01-01", "2024-01-05")
        symbols = generator.generate_symbols()
        bars = generator.generate_bars(symbols)
        
        assert len(bars) > 0
        assert all("open" in b for b in bars)
        assert all("high" in b for b in bars)
        assert all("low" in b for b in bars)
        assert all("close" in b for b in bars)
        assert all("volume" in b for b in bars)
        
        # Check that high >= low
        for bar in bars:
            assert bar["high"] >= bar["low"]


class TestDatabaseLoading:
    """Test database loading functionality."""
    
    def test_database_connection(self, db_connection):
        """Test database connection."""
        assert db_connection is not None
        
        # Test simple query
        result = db_connection.execute("SELECT 1 as test").fetchone()
        assert result[0] == 1
    
    def test_insert_symbols(self, db_connection, sample_symbols_data):
        """Test inserting symbols."""
        for symbol in sample_symbols_data:
            db_connection.execute("""
                INSERT INTO symbols 
                (symbol_id, ticker, name, sector, industry, market_cap, exchange, currency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                symbol["symbol_id"],
                symbol["ticker"],
                symbol["name"],
                symbol["sector"],
                symbol["industry"],
                symbol["market_cap"],
                symbol["exchange"],
                symbol["currency"]
            ])
        
        # Verify insertion
        count = db_connection.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
        assert count == len(sample_symbols_data)
    
    def test_insert_bars(self, db_connection, sample_symbols_data, sample_bars_data):
        """Test inserting bars."""
        # First insert symbols
        for symbol in sample_symbols_data:
            db_connection.execute("""
                INSERT INTO symbols 
                (symbol_id, ticker, name, sector, industry, market_cap, exchange, currency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                symbol["symbol_id"],
                symbol["ticker"],
                symbol["name"],
                symbol["sector"],
                symbol["industry"],
                symbol["market_cap"],
                symbol["exchange"],
                symbol["currency"]
            ])
        
        # Then insert bars
        for bar in sample_bars_data:
            db_connection.execute("""
                INSERT INTO bars (symbol_id, ts, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                bar["symbol_id"],
                bar["ts"],
                bar["open"],
                bar["high"],
                bar["low"],
                bar["close"],
                bar["volume"]
            ])
        
        # Verify insertion
        count = db_connection.execute("SELECT COUNT(*) FROM bars").fetchone()[0]
        assert count == len(sample_bars_data)
    
    def test_query_bars_by_symbol(self, db_connection, sample_symbols_data, sample_bars_data):
        """Test querying bars by symbol."""
        # Insert test data
        for symbol in sample_symbols_data:
            db_connection.execute("""
                INSERT INTO symbols 
                (symbol_id, ticker, name, sector, industry, market_cap, exchange, currency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                symbol["symbol_id"],
                symbol["ticker"],
                symbol["name"],
                symbol["sector"],
                symbol["industry"],
                symbol["market_cap"],
                symbol["exchange"],
                symbol["currency"]
            ])
        
        for bar in sample_bars_data:
            db_connection.execute("""
                INSERT INTO bars (symbol_id, ts, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                bar["symbol_id"],
                bar["ts"],
                bar["open"],
                bar["high"],
                bar["low"],
                bar["close"],
                bar["volume"]
            ])
        
        # Query bars for symbol_id = 1
        result = db_connection.execute("""
            SELECT * FROM bars WHERE symbol_id = 1 ORDER BY ts
        """).fetchdf()
        
        assert len(result) == 2
        assert result.iloc[0]["close"] == 103.0
        assert result.iloc[1]["close"] == 107.0

