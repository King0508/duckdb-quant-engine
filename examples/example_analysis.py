"""
Example: Complete analysis workflow

This script demonstrates a typical analytical workflow:
1. Load data from the warehouse
2. Perform technical analysis
3. Generate signals
4. Create visualizations
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import duckdb
import pandas as pd
import config


def analyze_stock(ticker: str):
    """Perform comprehensive analysis on a stock."""
    print(f"\n{'=' * 80}")
    print(f"Analysis Report: {ticker}")
    print("=" * 80)

    con = duckdb.connect(str(config.get_db_path()), read_only=True)

    # 1. Basic Information
    print("\n1. Stock Information")
    print("-" * 80)
    info = con.execute(
        """
        SELECT ticker, name, sector, industry, market_cap
        FROM symbols
        WHERE ticker = ?
    """,
        [ticker],
    ).fetchdf()

    if len(info) == 0:
        print(f"Stock {ticker} not found in database.")
        con.close()
        return

    print(info.to_string(index=False))

    # 2. Recent Performance
    print("\n2. Recent Performance (Last 30 Days)")
    print("-" * 80)
    performance = con.execute(
        """
        WITH recent AS (
            SELECT 
                price,
                return_1d_pct,
                ts,
                ROW_NUMBER() OVER (ORDER BY ts DESC) as rn
            FROM features_returns_rsi
            WHERE symbol = ?
        ),
        stats AS (
            SELECT 
                FIRST(price ORDER BY ts DESC) as current_price,
                FIRST(price ORDER BY ts) as price_30d_ago,
                AVG(return_1d_pct) as avg_daily_return,
                STDDEV(return_1d_pct) as volatility,
                MIN(price) as low_30d,
                MAX(price) as high_30d
            FROM recent
            WHERE rn <= 30
        )
        SELECT 
            ROUND(current_price, 2) as current_price,
            ROUND(price_30d_ago, 2) as price_30d_ago,
            ROUND(((current_price - price_30d_ago) / price_30d_ago * 100), 2) as return_30d_pct,
            ROUND(avg_daily_return, 2) as avg_daily_return,
            ROUND(volatility, 2) as volatility,
            ROUND(low_30d, 2) as low_30d,
            ROUND(high_30d, 2) as high_30d
        FROM stats
    """,
        [ticker],
    ).fetchdf()

    print(performance.to_string(index=False))

    # 3. Technical Indicators
    print("\n3. Technical Indicators (Latest)")
    print("-" * 80)
    indicators = con.execute(
        """
        SELECT 
            ROUND(price, 2) as price,
            rsi_14,
            rsi_28,
            rsi_signal,
            ROUND(return_1d_pct, 2) as return_1d_pct,
            ROUND(return_5d_pct, 2) as return_5d_pct
        FROM features_returns_rsi
        WHERE symbol = ?
        ORDER BY ts DESC
        LIMIT 1
    """,
        [ticker],
    ).fetchdf()

    print(indicators.to_string(index=False))

    # 4. Volume Analysis
    print("\n4. Volume Analysis (Latest)")
    print("-" * 80)
    volume = con.execute(
        """
        SELECT 
            volume,
            ROUND(avg_volume_20, 0) as avg_volume_20,
            ROUND(volume_ratio, 2) as volume_ratio,
            volume_category,
            volume_trend,
            ROUND(vwap, 2) as vwap,
            ROUND(price_vs_vwap_pct, 2) as price_vs_vwap_pct
        FROM features_vwap_volume
        WHERE symbol = ?
        ORDER BY ts DESC
        LIMIT 1
    """,
        [ticker],
    ).fetchdf()

    print(volume.to_string(index=False))

    # 5. Trading Activity
    print("\n5. Trading Activity (Last 7 Days)")
    print("-" * 80)
    trading = con.execute(
        """
        SELECT 
            date,
            ROUND(open, 2) as open,
            ROUND(high, 2) as high,
            ROUND(low, 2) as low,
            ROUND(close, 2) as close,
            total_volume,
            num_trades,
            ROUND(daily_return_pct, 2) as daily_return_pct
        FROM daily_metrics
        WHERE symbol = ?
        ORDER BY date DESC
        LIMIT 7
    """,
        [ticker],
    ).fetchdf()

    print(trading.to_string(index=False))

    # 6. Generate Trading Recommendations
    print("\n6. Analysis Summary")
    print("-" * 80)

    latest_rsi = indicators["rsi_14"].iloc[0]
    vol_category = volume["volume_category"].iloc[0]
    recent_return = performance["return_30d_pct"].iloc[0]

    recommendations = []

    if latest_rsi > 70:
        recommendations.append("⚠️  Stock appears OVERBOUGHT (RSI > 70)")
    elif latest_rsi < 30:
        recommendations.append("✅ Stock appears OVERSOLD (RSI < 30) - potential buy opportunity")
    else:
        recommendations.append("📊 RSI in neutral range")

    if vol_category in ["VERY_HIGH", "HIGH"]:
        recommendations.append("📈 Unusual high volume detected - increased interest")
    elif vol_category in ["VERY_LOW", "LOW"]:
        recommendations.append("📉 Low volume - limited market interest")

    if recent_return > 10:
        recommendations.append(f"🚀 Strong 30-day performance (+{recent_return:.1f}%)")
    elif recent_return < -10:
        recommendations.append(f"⚠️  Weak 30-day performance ({recent_return:.1f}%)")

    for rec in recommendations:
        print(f"  {rec}")

    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80 + "\n")

    con.close()


def compare_stocks(tickers: list):
    """Compare multiple stocks."""
    print(f"\n{'=' * 80}")
    print(f"Comparative Analysis: {', '.join(tickers)}")
    print("=" * 80 + "\n")

    con = duckdb.connect(str(config.get_db_path()), read_only=True)

    # Get comparison data
    placeholders = ", ".join(["?" for _ in tickers])
    comparison = con.execute(
        f"""
        WITH latest AS (
            SELECT 
                symbol,
                price,
                rsi_14,
                return_1d_pct,
                return_5d_pct,
                ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY ts DESC) as rn
            FROM features_returns_rsi
            WHERE symbol IN ({placeholders})
        ),
        volume_data AS (
            SELECT 
                symbol,
                volume_ratio,
                volume_category,
                ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY ts DESC) as rn
            FROM features_vwap_volume
            WHERE symbol IN ({placeholders})
        )
        SELECT 
            l.symbol,
            ROUND(l.price, 2) as price,
            l.rsi_14,
            ROUND(l.return_1d_pct, 2) as return_1d,
            ROUND(l.return_5d_pct, 2) as return_5d,
            ROUND(v.volume_ratio, 2) as vol_ratio,
            v.volume_category
        FROM latest l
        JOIN volume_data v ON l.symbol = v.symbol AND v.rn = 1
        WHERE l.rn = 1
        ORDER BY l.return_5d_pct DESC
    """,
        tickers + tickers,
    ).fetchdf()

    print(comparison.to_string(index=False))

    # Identify best performer
    best_performer = comparison.iloc[0]["symbol"]
    best_return = comparison.iloc[0]["return_5d"]

    print(f"\n🏆 Best 5-day performer: {best_performer} ({best_return:+.2f}%)")

    con.close()


def main():
    """Main execution function."""
    # Analyze individual stocks
    stocks_to_analyze = ["AAPL", "MSFT", "GOOGL"]

    for ticker in stocks_to_analyze:
        analyze_stock(ticker)

    # Compare stocks
    compare_stocks(stocks_to_analyze)


if __name__ == "__main__":
    main()

