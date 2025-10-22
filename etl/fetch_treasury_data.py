"""
Treasury data fetcher - Fetches US Treasury yields and fixed-income ETFs.
Integrates with FRED API for yields and Yahoo Finance for ETFs.
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import sys
import duckdb

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logging.warning("yfinance not available - ETF data fetching disabled")

try:
    from fredapi import Fred
    FREDAPI_AVAILABLE = True
except ImportError:
    FREDAPI_AVAILABLE = False
    logging.warning("fredapi not available - Treasury yield fetching disabled")

import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Treasury instruments mapping
TREASURY_MATURITIES = {
    "2Y": "DGS2",   # 2-Year Treasury Constant Maturity Rate
    "5Y": "DGS5",   # 5-Year Treasury Constant Maturity Rate
    "10Y": "DGS10", # 10-Year Treasury Constant Maturity Rate
    "30Y": "DGS30", # 30-Year Treasury Constant Maturity Rate
}

# Fixed-income ETFs
FIXED_INCOME_ETFS = {
    "TLT": "iShares 20+ Year Treasury Bond ETF",
    "IEF": "iShares 7-10 Year Treasury Bond ETF",
    "SHY": "iShares 1-3 Year Treasury Bond ETF",
    "LQD": "iShares iBoxx Investment Grade Corporate Bond ETF",
    "HYG": "iShares iBoxx High Yield Corporate Bond ETF",
}


class TreasuryDataFetcher:
    """Fetches Treasury yields and fixed-income ETF data."""
    
    def __init__(self, fred_api_key: Optional[str] = None):
        """
        Initialize the fetcher.
        
        Args:
            fred_api_key: FRED API key (or uses FRED_API_KEY env var)
        """
        self.fred_api_key = fred_api_key or os.getenv("FRED_API_KEY")
        self.fred = None
        
        if FREDAPI_AVAILABLE and self.fred_api_key:
            try:
                self.fred = Fred(api_key=self.fred_api_key)
                logger.info("FRED API initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize FRED API: {e}")
        elif not self.fred_api_key:
            logger.warning("FRED_API_KEY not set - Treasury yield fetching disabled")
    
    def fetch_treasury_yields(self, days_back: int = 30) -> List[Dict]:
        """
        Fetch Treasury yields from FRED.
        
        Args:
            days_back: Number of days of historical data to fetch
            
        Returns:
            List of yield records
        """
        if not self.fred:
            logger.error("FRED API not available")
            return []
        
        yields = []
        start_date = datetime.now() - timedelta(days=days_back)
        
        for maturity, series_id in TREASURY_MATURITIES.items():
            try:
                logger.info(f"Fetching {maturity} Treasury yields...")
                
                # Fetch series data
                data = self.fred.get_series(series_id, observation_start=start_date)
                
                for date, yield_rate in data.items():
                    if not yield_rate or str(yield_rate) == 'nan':
                        continue
                    
                    yields.append({
                        'timestamp': datetime.combine(date, datetime.min.time()).replace(tzinfo=timezone.utc),
                        'maturity': maturity,
                        'yield_rate': float(yield_rate),
                        'source': 'FRED'
                    })
                
                logger.info(f"Fetched {len(data)} records for {maturity}")
                
            except Exception as e:
                logger.error(f"Failed to fetch {maturity} yields: {e}")
                continue
        
        return yields
    
    def fetch_etf_data(self, days_back: int = 30) -> List[Dict]:
        """
        Fetch fixed-income ETF data from Yahoo Finance.
        
        Args:
            days_back: Number of days of historical data to fetch
            
        Returns:
            List of ETF price records
        """
        if not YFINANCE_AVAILABLE:
            logger.error("yfinance not available")
            return []
        
        etf_data = []
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        for ticker, name in FIXED_INCOME_ETFS.items():
            try:
                logger.info(f"Fetching {ticker} data...")
                
                # Fetch ETF data
                etf = yf.Ticker(ticker)
                hist = etf.history(start=start_date)
                
                if hist.empty:
                    logger.warning(f"No data available for {ticker}")
                    continue
                
                for date, row in hist.iterrows():
                    etf_data.append({
                        'timestamp': date.to_pydatetime().replace(tzinfo=timezone.utc),
                        'ticker': ticker,
                        'name': name,
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': float(row['Close']),
                        'volume': int(row['Volume']),
                        'source': 'YahooFinance'
                    })
                
                logger.info(f"Fetched {len(hist)} records for {ticker}")
                
            except Exception as e:
                logger.error(f"Failed to fetch {ticker} data: {e}")
                continue
        
        return etf_data
    
    def load_to_warehouse(self, yields: List[Dict], etf_data: List[Dict]) -> None:
        """
        Load Treasury and ETF data into the warehouse.
        
        Args:
            yields: List of Treasury yield records
            etf_data: List of ETF price records
        """
        db_path = config.get_db_path()
        conn = duckdb.connect(str(db_path))
        
        try:
            # Ensure schema exists
            schema_path = config.get_sql_file('fixed_income_schema.sql')
            if schema_path.exists():
                logger.info("Applying fixed income schema...")
                conn.execute(schema_path.read_text())
            
            # Load Treasury yields
            if yields:
                logger.info(f"Loading {len(yields)} Treasury yield records...")
                
                for record in yields:
                    conn.execute("""
                        INSERT INTO treasury_yields (timestamp, maturity, yield_rate, source)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT DO NOTHING
                    """, [
                        record['timestamp'],
                        record['maturity'],
                        record['yield_rate'],
                        record['source']
                    ])
                
                logger.info(f"✓ Loaded {len(yields)} Treasury yield records")
            
            # Load ETF data
            if etf_data:
                logger.info(f"Loading {len(etf_data)} ETF records...")
                
                for record in etf_data:
                    conn.execute("""
                        INSERT INTO fixed_income_etfs 
                        (timestamp, ticker, name, open, high, low, close, volume, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT DO NOTHING
                    """, [
                        record['timestamp'],
                        record['ticker'],
                        record['name'],
                        record['open'],
                        record['high'],
                        record['low'],
                        record['close'],
                        record['volume'],
                        record['source']
                    ])
                
                logger.info(f"✓ Loaded {len(etf_data)} ETF records")
            
            # Calculate derived metrics
            self._calculate_metrics(conn)
            
            logger.info("✓ Treasury data load complete")
            
        except Exception as e:
            logger.error(f"Failed to load data to warehouse: {e}")
            raise
        finally:
            conn.close()
    
    def _calculate_metrics(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Calculate derived metrics (returns, changes, etc.)"""
        
        # Calculate Treasury yield changes
        logger.info("Calculating Treasury yield changes...")
        conn.execute("""
            UPDATE treasury_yields ty
            SET 
                change_1d = (
                    SELECT (ty.yield_rate - prev.yield_rate) * 100
                    FROM treasury_yields prev
                    WHERE prev.maturity = ty.maturity
                        AND prev.timestamp = (
                            SELECT MAX(timestamp)
                            FROM treasury_yields
                            WHERE maturity = ty.maturity
                                AND timestamp < ty.timestamp
                        )
                )
        """)
        
        # Calculate ETF returns
        logger.info("Calculating ETF returns...")
        conn.execute("""
            UPDATE fixed_income_etfs fe
            SET 
                return_1d = (
                    SELECT ((fe.close - prev.close) / prev.close) * 100
                    FROM fixed_income_etfs prev
                    WHERE prev.ticker = fe.ticker
                        AND prev.timestamp = (
                            SELECT MAX(timestamp)
                            FROM fixed_income_etfs
                            WHERE ticker = fe.ticker
                                AND timestamp < fe.timestamp
                        )
                )
        """)
        
        logger.info("✓ Calculated derived metrics")


def main():
    """Main entry point for fetching Treasury data."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch Treasury yields and ETF data')
    parser.add_argument('--days', type=int, default=30, help='Days of historical data to fetch')
    parser.add_argument('--fred-key', type=str, help='FRED API key (or use FRED_API_KEY env var)')
    parser.add_argument('--yields-only', action='store_true', help='Fetch only Treasury yields')
    parser.add_argument('--etfs-only', action='store_true', help='Fetch only ETF data')
    
    args = parser.parse_args()
    
    # Initialize fetcher
    fetcher = TreasuryDataFetcher(fred_api_key=args.fred_key)
    
    # Fetch data
    yields = []
    etf_data = []
    
    if not args.etfs_only:
        yields = fetcher.fetch_treasury_yields(days_back=args.days)
        logger.info(f"Fetched {len(yields)} Treasury yield records")
    
    if not args.yields_only:
        etf_data = fetcher.fetch_etf_data(days_back=args.days)
        logger.info(f"Fetched {len(etf_data)} ETF records")
    
    # Load to warehouse
    if yields or etf_data:
        fetcher.load_to_warehouse(yields, etf_data)
        logger.info("✓ Data successfully loaded to warehouse")
    else:
        logger.warning("No data fetched")


if __name__ == '__main__':
    main()

