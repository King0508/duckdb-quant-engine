"""
Example: Using the REST API

This script demonstrates various ways to interact with the API.
"""

import requests
import json
from typing import Dict, List


class WarehouseAPIClient:
    """Client for interacting with the Warehouse API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the API client."""
        self.base_url = base_url
        self.session = requests.Session()

    def health_check(self) -> Dict:
        """Check API health status."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def get_symbols(self, sector: str = None, limit: int = 100) -> List[Dict]:
        """Get list of symbols."""
        params = {"limit": limit}
        if sector:
            params["sector"] = sector

        response = self.session.get(f"{self.base_url}/symbols", params=params)
        response.raise_for_status()
        return response.json()

    def get_symbol(self, ticker: str) -> Dict:
        """Get specific symbol details."""
        response = self.session.get(f"{self.base_url}/symbols/{ticker}")
        response.raise_for_status()
        return response.json()

    def get_bars(self, ticker: str, start_date: str = None, end_date: str = None, limit: int = 100) -> List[Dict]:
        """Get OHLCV bars for a symbol."""
        params = {"limit": limit}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        response = self.session.get(f"{self.base_url}/bars/{ticker}", params=params)
        response.raise_for_status()
        return response.json()

    def get_rsi_analysis(self, ticker: str, limit: int = 30) -> List[Dict]:
        """Get RSI technical analysis."""
        response = self.session.get(f"{self.base_url}/analytics/rsi/{ticker}", params={"limit": limit})
        response.raise_for_status()
        return response.json()

    def get_vwap_analysis(self, ticker: str, limit: int = 30) -> List[Dict]:
        """Get VWAP analysis."""
        response = self.session.get(f"{self.base_url}/analytics/vwap/{ticker}", params={"limit": limit})
        response.raise_for_status()
        return response.json()

    def get_performance(self, days: int = 30, limit: int = 10) -> List[Dict]:
        """Get top performing stocks."""
        response = self.session.get(f"{self.base_url}/analytics/performance", params={"days": days, "limit": limit})
        response.raise_for_status()
        return response.json()

    def get_trading_signals(self) -> List[Dict]:
        """Get current trading signals."""
        response = self.session.get(f"{self.base_url}/analytics/signals")
        response.raise_for_status()
        return response.json()


def demo_basic_operations():
    """Demonstrate basic API operations."""
    print("\n" + "=" * 80)
    print("API Example: Basic Operations")
    print("=" * 80 + "\n")

    client = WarehouseAPIClient()

    # 1. Health check
    print("1. Health Check")
    print("-" * 80)
    health = client.health_check()
    print(f"Status: {health['status']}")
    print(f"Symbols in database: {health['symbols_count']}")

    # 2. Get symbols
    print("\n2. Available Symbols")
    print("-" * 80)
    symbols = client.get_symbols(limit=5)
    for symbol in symbols:
        print(f"  {symbol['ticker']:8} - {symbol['name'][:40]:40} | {symbol['sector']}")

    # 3. Get specific symbol details
    print("\n3. Symbol Details: AAPL")
    print("-" * 80)
    aapl = client.get_symbol("AAPL")
    print(f"Name: {aapl['name']}")
    print(f"Sector: {aapl['sector']}")
    print(f"Industry: {aapl['industry']}")
    print(f"Market Cap: ${aapl['market_cap']:,}")

    # 4. Get recent bars
    print("\n4. Recent Price Bars (AAPL)")
    print("-" * 80)
    bars = client.get_bars("AAPL", limit=5)
    for bar in bars:
        print(
            f"  {bar['ts']}: O={bar['open']:7.2f} H={bar['high']:7.2f} "
            f"L={bar['low']:7.2f} C={bar['close']:7.2f} V={bar['volume']:,}"
        )


def demo_analytics():
    """Demonstrate analytics operations."""
    print("\n" + "=" * 80)
    print("API Example: Analytics")
    print("=" * 80 + "\n")

    client = WarehouseAPIClient()

    # 1. Top performers
    print("1. Top Performers (Last 30 Days)")
    print("-" * 80)
    performers = client.get_performance(days=30, limit=5)
    for i, perf in enumerate(performers, 1):
        print(
            f"  {i}. {perf['symbol']:8} {perf['total_return_pct']:+7.2f}% "
            f"(${perf['start_price']:.2f} → ${perf['end_price']:.2f})"
        )

    # 2. RSI Analysis
    print("\n2. RSI Analysis: AAPL (Latest)")
    print("-" * 80)
    rsi_data = client.get_rsi_analysis("AAPL", limit=1)
    if rsi_data:
        data = rsi_data[0]
        print(f"  Price: ${data['price']:.2f}")
        print(f"  RSI(14): {data['rsi_14']:.2f}")
        print(f"  Signal: {data['rsi_signal']}")
        print(f"  1-Day Return: {data['return_1d_pct']:+.2f}%")

    # 3. VWAP Analysis
    print("\n3. VWAP Analysis: AAPL (Latest)")
    print("-" * 80)
    vwap_data = client.get_vwap_analysis("AAPL", limit=1)
    if vwap_data:
        data = vwap_data[0]
        print(f"  Price: ${data['price']:.2f}")
        print(f"  VWAP: ${data['vwap']:.2f}")
        print(f"  Price vs VWAP: {data['price_vs_vwap_pct']:+.2f}%")
        print(f"  Volume Ratio: {data['volume_ratio']:.2f}x")
        print(f"  Volume Category: {data['volume_category']}")

    # 4. Trading Signals
    print("\n4. Active Trading Signals")
    print("-" * 80)
    signals = client.get_trading_signals()
    if signals:
        for signal in signals[:5]:
            print(
                f"  {signal['symbol']:8} - {signal['rsi_signal']:12} "
                f"(RSI: {signal['rsi_14']:.2f}, Price: ${signal['price']:.2f})"
            )
    else:
        print("  No active signals")


def demo_sector_analysis():
    """Demonstrate sector-based analysis."""
    print("\n" + "=" * 80)
    print("API Example: Sector Analysis")
    print("=" * 80 + "\n")

    client = WarehouseAPIClient()

    # Get all symbols and group by sector
    symbols = client.get_symbols(limit=100)

    sectors = {}
    for symbol in symbols:
        sector = symbol.get("sector", "Unknown")
        if sector not in sectors:
            sectors[sector] = []
        sectors[sector].append(symbol["ticker"])

    print("Stocks by Sector:")
    print("-" * 80)
    for sector, tickers in sectors.items():
        print(f"  {sector:20} ({len(tickers)} stocks): {', '.join(tickers[:5])}")


def main():
    """Run all examples."""
    try:
        demo_basic_operations()
        demo_analytics()
        demo_sector_analysis()

        print("\n" + "=" * 80)
        print("✅ All API examples completed successfully!")
        print("=" * 80 + "\n")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print("Please start the API server with: python -m api.main")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()

