"""
Run analytical queries on the data warehouse.

This script demonstrates various analytical queries for quantitative research:
- Technical indicators (RSI, VWAP)
- Performance metrics
- Volume analysis
- Statistical analysis
"""

import duckdb
import pandas as pd
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
import config


class AnalyticsEngine:
    """Run analytics queries on the warehouse."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize connection to database."""
        self.db_path = db_path or config.get_db_path()
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.db_path}\n"
                "Please run 'python etl/load_data.py' first to create the database."
            )
        self.con = duckdb.connect(str(self.db_path), read_only=True)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.con.close()

    def get_latest_prices(self, limit: int = 10) -> pd.DataFrame:
        """Get latest prices for all symbols."""
        query = """
        SELECT 
            symbol,
            name,
            MAX(ts) as latest_timestamp,
            LAST(price ORDER BY ts) as latest_price,
            ROUND(LAST(return_1d_pct ORDER BY ts), 2) as daily_return_pct,
            LAST(rsi_14 ORDER BY ts) as rsi_14
        FROM features_returns_rsi
        GROUP BY symbol, name
        ORDER BY symbol
        LIMIT ?
        """
        return self.con.execute(query, [limit]).fetchdf()

    def get_top_performers(self, days: int = 30, limit: int = 10) -> pd.DataFrame:
        """Get top performing stocks over a time period."""
        query = f"""
        WITH recent_data AS (
            SELECT 
                symbol,
                name,
                ts,
                price,
                return_1d_pct,
                ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY ts DESC) as rn
            FROM features_returns_rsi
            WHERE ts >= CURRENT_DATE - INTERVAL {days} DAY
        ),
        performance AS (
            SELECT 
                symbol,
                name,
                FIRST(price ORDER BY ts) as start_price,
                LAST(price ORDER BY ts DESC) as end_price,
                SUM(return_1d_pct) as total_return_pct,
                COUNT(*) as trading_days
            FROM recent_data
            GROUP BY symbol, name
        )
        SELECT 
            symbol,
            name,
            ROUND(start_price, 2) as start_price,
            ROUND(end_price, 2) as end_price,
            ROUND(total_return_pct, 2) as total_return_pct,
            trading_days
        FROM performance
        ORDER BY total_return_pct DESC
        LIMIT {limit}
        """
        return self.con.execute(query).fetchdf()

    def get_rsi_signals(self) -> pd.DataFrame:
        """Get current RSI signals (overbought/oversold)."""
        query = """
        WITH latest_rsi AS (
            SELECT 
                symbol,
                name,
                ts,
                price,
                rsi_14,
                rsi_signal,
                ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY ts DESC) as rn
            FROM features_returns_rsi
        )
        SELECT 
            symbol,
            name,
            ROUND(price, 2) as price,
            rsi_14,
            rsi_signal
        FROM latest_rsi
        WHERE rn = 1 AND rsi_signal != 'NEUTRAL'
        ORDER BY 
            CASE rsi_signal 
                WHEN 'OVERBOUGHT' THEN 1 
                WHEN 'OVERSOLD' THEN 2 
            END,
            symbol
        """
        return self.con.execute(query).fetchdf()

    def get_volume_analysis(self, limit: int = 10) -> pd.DataFrame:
        """Get volume analysis with unusual activity."""
        query = """
        WITH latest_volume AS (
            SELECT 
                symbol,
                name,
                ts,
                volume,
                avg_volume_20,
                volume_ratio,
                volume_category,
                volume_trend,
                ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY ts DESC) as rn
            FROM features_vwap_volume
        )
        SELECT 
            symbol,
            name,
            ROUND(volume, 0) as volume,
            ROUND(avg_volume_20, 0) as avg_volume_20,
            volume_ratio,
            volume_category,
            volume_trend
        FROM latest_volume
        WHERE rn = 1
        ORDER BY volume_ratio DESC
        LIMIT ?
        """
        return self.con.execute(query, [limit]).fetchdf()

    def get_vwap_analysis(self) -> pd.DataFrame:
        """Get VWAP analysis (price vs VWAP)."""
        query = """
        WITH latest_vwap AS (
            SELECT 
                symbol,
                name,
                ts,
                price,
                vwap,
                price_vs_vwap_pct,
                ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY ts DESC) as rn
            FROM features_vwap_volume
        )
        SELECT 
            symbol,
            name,
            ROUND(price, 2) as price,
            ROUND(vwap, 2) as vwap,
            price_vs_vwap_pct,
            CASE 
                WHEN price_vs_vwap_pct > 1 THEN 'ABOVE_VWAP'
                WHEN price_vs_vwap_pct < -1 THEN 'BELOW_VWAP'
                ELSE 'AT_VWAP'
            END as position
        FROM latest_vwap
        WHERE rn = 1
        ORDER BY ABS(price_vs_vwap_pct) DESC
        """
        return self.con.execute(query).fetchdf()

    def get_daily_summary(self, days: int = 5) -> pd.DataFrame:
        """Get daily summary statistics."""
        query = f"""
        SELECT 
            date,
            symbol,
            sector,
            open,
            high,
            low,
            close,
            daily_return_pct,
            total_volume,
            num_trades
        FROM daily_metrics
        WHERE date >= CURRENT_DATE - INTERVAL {days} DAY
        ORDER BY date DESC, daily_return_pct DESC
        """
        return self.con.execute(query).fetchdf()

    def get_correlation_matrix(self) -> pd.DataFrame:
        """Calculate correlation matrix of returns between stocks."""
        query = """
        WITH daily_returns AS (
            SELECT 
                DATE_TRUNC('day', ts) as date,
                symbol,
                AVG(log_return_1d) as avg_return
            FROM features_returns_rsi
            WHERE log_return_1d IS NOT NULL
            GROUP BY DATE_TRUNC('day', ts), symbol
        )
        SELECT 
            a.symbol as symbol_a,
            b.symbol as symbol_b,
            ROUND(CORR(a.avg_return, b.avg_return), 3) as correlation
        FROM daily_returns a
        JOIN daily_returns b ON a.date = b.date AND a.symbol < b.symbol
        GROUP BY a.symbol, b.symbol
        HAVING COUNT(*) > 20  -- At least 20 days of data
        ORDER BY ABS(correlation) DESC
        """
        return self.con.execute(query).fetchdf()


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def main():
    """Run various analytical queries and display results."""
    print("\n" + "=" * 80)
    print("Quantitative Finance Analytics")
    print("=" * 80)

    try:
        with AnalyticsEngine() as engine:
            # 1. Latest Prices
            print_section("Latest Prices")
            df = engine.get_latest_prices(limit=20)
            print(df.to_string(index=False))

            # 2. Top Performers (Last 30 Days)
            print_section("Top Performers (Last 30 Days)")
            df = engine.get_top_performers(days=30, limit=10)
            print(df.to_string(index=False))

            # 3. RSI Signals
            print_section("RSI Signals (Overbought/Oversold)")
            df = engine.get_rsi_signals()
            if len(df) > 0:
                print(df.to_string(index=False))
            else:
                print("No overbought/oversold signals currently")

            # 4. Volume Analysis
            print_section("Volume Analysis (Highest Volume Ratios)")
            df = engine.get_volume_analysis(limit=10)
            print(df.to_string(index=False))

            # 5. VWAP Analysis
            print_section("VWAP Analysis")
            df = engine.get_vwap_analysis()
            print(df.to_string(index=False))

            # 6. Daily Summary (Last 5 Days)
            print_section("Daily Summary (Last 5 Days)")
            df = engine.get_daily_summary(days=5)
            print(df.head(20).to_string(index=False))

            # 7. Correlation Matrix
            print_section("Stock Return Correlations (Top 10)")
            df = engine.get_correlation_matrix()
            print(df.head(10).to_string(index=False))

            print("\n" + "=" * 80)
            print("✅ Analysis Complete")
            print("=" * 80 + "\n")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running analysis: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
