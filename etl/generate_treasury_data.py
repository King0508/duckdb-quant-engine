"""
Generate synthetic Treasury yield and fixed-income ETF data for testing.
Creates realistic market data without requiring external APIs.
"""

import random
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from pathlib import Path
import sys
import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Base yield rates (realistic starting points)
BASE_YIELDS = {
    "2Y": 4.50,
    "5Y": 4.25,
    "10Y": 4.10,
    "30Y": 4.30,
}

# Base ETF prices
BASE_ETF_PRICES = {
    "TLT": 95.50,  # 20+ Year Treasury Bond ETF
    "IEF": 100.20,  # 7-10 Year Treasury Bond ETF
    "SHY": 82.75,  # 1-3 Year Treasury Bond ETF
    "LQD": 108.50,  # Investment Grade Corporate Bond ETF
    "HYG": 75.80,  # High Yield Corporate Bond ETF
}

ETF_NAMES = {
    "TLT": "iShares 20+ Year Treasury Bond ETF",
    "IEF": "iShares 7-10 Year Treasury Bond ETF",
    "SHY": "iShares 1-3 Year Treasury Bond ETF",
    "LQD": "iShares iBoxx Investment Grade Corporate Bond ETF",
    "HYG": "iShares iBoxx High Yield Corporate Bond ETF",
}


def generate_treasury_yields(days: int = 365) -> List[Dict]:
    """
    Generate synthetic Treasury yield data.

    Args:
        days: Number of days of data to generate

    Returns:
        List of yield records
    """
    logger.info(f"Generating Treasury yield data for {days} days...")

    yields = []
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Initialize current yields
    current_yields = BASE_YIELDS.copy()

    for day in range(days):
        current_date = start_date + timedelta(days=day)

        # Skip weekends
        if current_date.weekday() >= 5:
            continue

        for maturity, base_yield in current_yields.items():
            # Random walk with mean reversion
            change = random.gauss(0, 0.05)  # Small daily changes
            mean_reversion = (BASE_YIELDS[maturity] - current_yields[maturity]) * 0.01

            new_yield = current_yields[maturity] + change + mean_reversion

            # Keep yields in realistic range (1% to 8%)
            new_yield = max(1.0, min(8.0, new_yield))
            current_yields[maturity] = new_yield

            yields.append(
                {
                    "timestamp": current_date,
                    "maturity": maturity,
                    "yield_rate": round(new_yield, 4),
                    "source": "GENERATED",
                }
            )

    logger.info(f"✓ Generated {len(yields)} Treasury yield records")
    return yields


def generate_etf_data(days: int = 365) -> List[Dict]:
    """
    Generate synthetic fixed-income ETF data.

    Args:
        days: Number of days of data to generate

    Returns:
        List of ETF price records
    """
    logger.info(f"Generating ETF data for {days} days...")

    etf_data = []
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Initialize current prices
    current_prices = BASE_ETF_PRICES.copy()

    for day in range(days):
        current_date = start_date + timedelta(days=day)

        # Skip weekends
        if current_date.weekday() >= 5:
            continue

        for ticker, base_price in current_prices.items():
            # Generate OHLCV data
            # Daily volatility (bond ETFs are less volatile than equities)
            volatility = 0.008 if ticker in ["TLT", "IEF", "SHY"] else 0.012

            # Random return with slight drift
            daily_return = random.gauss(0.0001, volatility)

            # Calculate prices
            prev_close = current_prices[ticker]
            new_close = prev_close * (1 + daily_return)

            # Generate OHLC from close
            intraday_range = abs(random.gauss(0, volatility * 0.5))
            high = new_close * (1 + intraday_range)
            low = new_close * (1 - intraday_range)
            open_price = prev_close * (1 + random.gauss(0, volatility * 0.3))

            # Ensure OHLC relationships
            high = max(high, open_price, new_close)
            low = min(low, open_price, new_close)

            # Generate volume (bond ETFs have consistent volume)
            base_volume = {
                "TLT": 25_000_000,
                "IEF": 12_000_000,
                "SHY": 8_000_000,
                "LQD": 18_000_000,
                "HYG": 20_000_000,
            }

            volume = int(base_volume[ticker] * random.uniform(0.7, 1.3))

            etf_data.append(
                {
                    "timestamp": current_date,
                    "ticker": ticker,
                    "name": ETF_NAMES[ticker],
                    "open": round(open_price, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(new_close, 2),
                    "volume": volume,
                    "source": "GENERATED",
                }
            )

            # Update current price
            current_prices[ticker] = new_close

    logger.info(f"✓ Generated {len(etf_data)} ETF records")
    return etf_data


def calculate_derived_metrics(conn: duckdb.DuckDBPyConnection) -> None:
    """Calculate derived metrics like returns and changes."""

    logger.info("Calculating derived metrics...")

    # Calculate Treasury yield changes (in basis points)
    conn.execute(
        """
        WITH lagged_yields AS (
            SELECT 
                yield_id,
                yield_rate,
                LAG(yield_rate, 1) OVER (PARTITION BY maturity ORDER BY timestamp) as prev_1d,
                LAG(yield_rate, 5) OVER (PARTITION BY maturity ORDER BY timestamp) as prev_1w,
                LAG(yield_rate, 20) OVER (PARTITION BY maturity ORDER BY timestamp) as prev_1m
            FROM treasury_yields
        )
        UPDATE treasury_yields ty
        SET 
            change_1d = ROUND((ty.yield_rate - ly.prev_1d) * 100, 2),
            change_1w = ROUND((ty.yield_rate - ly.prev_1w) * 100, 2),
            change_1m = ROUND((ty.yield_rate - ly.prev_1m) * 100, 2)
        FROM lagged_yields ly
        WHERE ty.yield_id = ly.yield_id
    """
    )

    # Calculate ETF returns
    conn.execute(
        """
        WITH lagged_prices AS (
            SELECT 
                etf_id,
                close,
                LAG(close, 1) OVER (PARTITION BY ticker ORDER BY timestamp) as prev_1d,
                LAG(close, 5) OVER (PARTITION BY ticker ORDER BY timestamp) as prev_1w,
                LAG(close, 20) OVER (PARTITION BY ticker ORDER BY timestamp) as prev_1m,
                AVG(volume) OVER (
                    PARTITION BY ticker 
                    ORDER BY timestamp 
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                ) as avg_vol_20d
            FROM fixed_income_etfs
        )
        UPDATE fixed_income_etfs fe
        SET 
            return_1d = ROUND(((fe.close - lp.prev_1d) / lp.prev_1d) * 100, 4),
            return_1w = ROUND(((fe.close - lp.prev_1w) / lp.prev_1w) * 100, 4),
            return_1m = ROUND(((fe.close - lp.prev_1m) / lp.prev_1m) * 100, 4),
            avg_volume_20d = CAST(lp.avg_vol_20d AS BIGINT)
        FROM lagged_prices lp
        WHERE fe.etf_id = lp.etf_id
    """
    )

    logger.info("✓ Calculated derived metrics")


def load_to_warehouse(yields: List[Dict], etf_data: List[Dict]) -> None:
    """
    Load generated data into the warehouse.

    Args:
        yields: List of Treasury yield records
        etf_data: List of ETF price records
    """
    db_path = config.get_db_path()
    logger.info(f"Loading data to warehouse: {db_path}")

    conn = duckdb.connect(str(db_path))

    try:
        # Apply schema
        schema_path = config.get_sql_file("fixed_income_schema.sql")
        if schema_path.exists():
            logger.info("Applying fixed income schema...")
            conn.execute(schema_path.read_text())

        # Load Treasury yields
        if yields:
            logger.info(f"Loading {len(yields)} Treasury yield records...")

            yields_df = pd.DataFrame(yields)
            conn.execute(
                """
                INSERT INTO treasury_yields (timestamp, maturity, yield_rate, source)
                SELECT * FROM yields_df
            """
            )

            logger.info(f"✓ Loaded {len(yields)} Treasury yield records")

        # Load ETF data
        if etf_data:
            logger.info(f"Loading {len(etf_data)} ETF records...")

            etf_df = pd.DataFrame(etf_data)
            conn.execute(
                """
                INSERT INTO fixed_income_etfs (timestamp, ticker, name, open, high, low, close, volume, source)
                SELECT * FROM etf_df
            """
            )

            logger.info(f"✓ Loaded {len(etf_data)} ETF records")

        # Calculate derived metrics
        calculate_derived_metrics(conn)

        # Show summary
        summary = conn.execute(
            """
            SELECT 
                'Treasury Yields' as data_type,
                COUNT(*) as records,
                MIN(timestamp) as min_date,
                MAX(timestamp) as max_date
            FROM treasury_yields
            UNION ALL
            SELECT 
                'Fixed Income ETFs' as data_type,
                COUNT(*) as records,
                MIN(timestamp) as min_date,
                MAX(timestamp) as max_date
            FROM fixed_income_etfs
        """
        ).fetchdf()

        logger.info("\n📊 Treasury Data Summary:")
        logger.info(f"\n{summary.to_string(index=False)}")

    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise
    finally:
        conn.close()


def main():
    """Main entry point for generating Treasury data."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic Treasury and ETF data")
    parser.add_argument("--days", type=int, default=365, help="Number of days of data to generate")
    parser.add_argument("--yields-only", action="store_true", help="Generate only Treasury yields")
    parser.add_argument("--etfs-only", action="store_true", help="Generate only ETF data")

    args = parser.parse_args()

    logger.info("=== Treasury Data Generator ===")
    logger.info(f"Generating {args.days} days of data...")

    # Generate data
    yields = []
    etf_data = []

    if not args.etfs_only:
        yields = generate_treasury_yields(days=args.days)

    if not args.yields_only:
        etf_data = generate_etf_data(days=args.days)

    # Load to warehouse
    load_to_warehouse(yields, etf_data)

    logger.info("✓ Treasury data generation complete!")


if __name__ == "__main__":
    main()
