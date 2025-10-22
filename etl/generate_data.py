"""
Generate realistic sample market data for the data warehouse.

This script creates:
- Symbol master data with company information
- OHLCV price bars (daily frequency)
- Individual trade records

Data is generated using realistic patterns and distributions.
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import config


class MarketDataGenerator:
    """Generate realistic market data for testing and demonstration."""

    # Realistic company data for sample symbols
    COMPANIES = [
        {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "market_cap": 2800000000000,
            "base_price": 180.0,
            "volatility": 0.02,
        },
        {
            "ticker": "MSFT",
            "name": "Microsoft Corporation",
            "sector": "Technology",
            "industry": "Software",
            "market_cap": 2500000000000,
            "base_price": 350.0,
            "volatility": 0.018,
        },
        {
            "ticker": "GOOGL",
            "name": "Alphabet Inc.",
            "sector": "Technology",
            "industry": "Internet Services",
            "market_cap": 1700000000000,
            "base_price": 140.0,
            "volatility": 0.022,
        },
        {
            "ticker": "TSLA",
            "name": "Tesla Inc.",
            "sector": "Consumer Cyclical",
            "industry": "Auto Manufacturers",
            "market_cap": 800000000000,
            "base_price": 250.0,
            "volatility": 0.035,
        },
        {
            "ticker": "AMZN",
            "name": "Amazon.com Inc.",
            "sector": "Consumer Cyclical",
            "industry": "Internet Retail",
            "market_cap": 1600000000000,
            "base_price": 145.0,
            "volatility": 0.025,
        },
        {
            "ticker": "META",
            "name": "Meta Platforms Inc.",
            "sector": "Technology",
            "industry": "Social Media",
            "market_cap": 900000000000,
            "base_price": 350.0,
            "volatility": 0.028,
        },
        {
            "ticker": "NVDA",
            "name": "NVIDIA Corporation",
            "sector": "Technology",
            "industry": "Semiconductors",
            "market_cap": 1200000000000,
            "base_price": 480.0,
            "volatility": 0.032,
        },
        {
            "ticker": "AMD",
            "name": "Advanced Micro Devices",
            "sector": "Technology",
            "industry": "Semiconductors",
            "market_cap": 200000000000,
            "base_price": 140.0,
            "volatility": 0.030,
        },
    ]

    def __init__(self, start_date: str, end_date: str):
        """Initialize the generator with date range."""
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.trading_days = self._generate_trading_days()

    def _generate_trading_days(self) -> List[datetime]:
        """Generate list of trading days (weekdays only)."""
        days = []
        current = self.start_date
        while current <= self.end_date:
            # Skip weekends
            if current.weekday() < 5:
                days.append(current)
            current += timedelta(days=1)
        return days

    def generate_symbols(self) -> List[Dict]:
        """Generate symbol master data."""
        symbols = []
        for idx, company in enumerate(self.COMPANIES, start=1):
            symbols.append(
                {
                    "symbol_id": idx,
                    "ticker": company["ticker"],
                    "name": company["name"],
                    "sector": company["sector"],
                    "industry": company["industry"],
                    "market_cap": company["market_cap"],
                    "exchange": "NASDAQ",
                    "currency": "USD",
                    "created_at": self.start_date.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
        return symbols

    def generate_bars(self, symbols: List[Dict]) -> List[Dict]:
        """Generate OHLCV price bars for all symbols."""
        bars = []

        for symbol in symbols:
            symbol_id = symbol["symbol_id"]
            ticker = symbol["ticker"]

            # Get company-specific parameters
            company = next(c for c in self.COMPANIES if c["ticker"] == ticker)
            current_price = company["base_price"]
            volatility = company["volatility"]

            for day in self.trading_days:
                # Generate intraday bars (simplified: just end-of-day bar)
                # Add some drift (trend) and random walk
                drift = random.gauss(0.0005, 0.001)  # Slight upward bias
                price_change = current_price * (drift + random.gauss(0, volatility))
                current_price = max(
                    1.0, current_price + price_change
                )  # Ensure positive

                # Generate OHLC based on close
                day_volatility = current_price * random.uniform(0.01, 0.03)
                high = current_price + random.uniform(0, day_volatility)
                low = current_price - random.uniform(0, day_volatility)
                open_price = low + random.uniform(0, high - low)

                # Ensure OHLC relationships are valid
                high = max(high, open_price, current_price)
                low = min(low, open_price, current_price)

                # Generate volume (log-normal distribution)
                base_volume = random.lognormvariate(15, 1.5)  # Mean around 3-5 million
                volume = int(base_volume * random.uniform(0.5, 1.5))

                # Market close timestamp (4:00 PM ET)
                ts = day.replace(hour=16, minute=0, second=0)

                bars.append(
                    {
                        "symbol_id": symbol_id,
                        "ts": ts.strftime("%Y-%m-%d %H:%M:%S"),
                        "open": round(open_price, 2),
                        "high": round(high, 2),
                        "low": round(low, 2),
                        "close": round(current_price, 2),
                        "volume": volume,
                    }
                )

        return bars

    def generate_trades(
        self, symbols: List[Dict], num_trades_per_symbol_per_day: int = 50
    ) -> List[Dict]:
        """Generate individual trade records."""
        trades = []

        for symbol in symbols:
            symbol_id = symbol["symbol_id"]
            ticker = symbol["ticker"]

            # Get company-specific parameters
            company = next(c for c in self.COMPANIES if c["ticker"] == ticker)
            current_price = company["base_price"]

            for day in self.trading_days:
                # Generate trades throughout the trading day (9:30 AM - 4:00 PM)
                market_open = day.replace(hour=9, minute=30, second=0)
                market_close = day.replace(hour=16, minute=0, second=0)

                for _ in range(num_trades_per_symbol_per_day):
                    # Random time during market hours
                    seconds_range = int((market_close - market_open).total_seconds())
                    random_seconds = random.randint(0, seconds_range)
                    trade_time = market_open + timedelta(seconds=random_seconds)

                    # Price around current level with small variance
                    price_variance = current_price * 0.001
                    trade_price = current_price + random.gauss(0, price_variance)
                    trade_price = max(0.01, round(trade_price, 2))

                    # Trade size (power law distribution - most trades small, few large)
                    trade_size = int(random.paretovariate(1.5) * 100)
                    trade_size = max(1, min(trade_size, 100000))  # Cap at 100k shares

                    # Side (slight buy bias in bull market)
                    side = random.choices(["BUY", "SELL"], weights=[0.52, 0.48])[0]

                    trades.append(
                        {
                            "symbol_id": symbol_id,
                            "ts": trade_time.strftime("%Y-%m-%d %H:%M:%S"),
                            "price": trade_price,
                            "size": trade_size,
                            "side": side,
                        }
                    )

                # Update price for next day
                drift = random.gauss(0.0005, 0.001)
                volatility = company["volatility"]
                price_change = current_price * (drift + random.gauss(0, volatility))
                current_price = max(1.0, current_price + price_change)

        return trades

    def save_to_csv(self, data: List[Dict], filename: str):
        """Save data to CSV file."""
        filepath = config.DATA_DIR / filename

        if not data:
            print(f"⚠️  No data to save for {filename}")
            return

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        print(f"[OK] Generated {len(data):,} records -> {filepath}")


def main():
    """Main execution function."""
    print("=" * 80)
    print("Market Data Generator")
    print("=" * 80)
    print()

    # Initialize generator
    generator = MarketDataGenerator(
        start_date=config.DEFAULT_START_DATE, end_date=config.DEFAULT_END_DATE
    )

    print(f"Date range: {config.DEFAULT_START_DATE} to {config.DEFAULT_END_DATE}")
    print(f"Trading days: {len(generator.trading_days)}")
    print(f"Symbols: {len(generator.COMPANIES)}")
    print()

    # Generate data
    print("Generating data...")
    print()

    symbols = generator.generate_symbols()
    generator.save_to_csv(symbols, "symbols.csv")

    bars = generator.generate_bars(symbols)
    generator.save_to_csv(bars, "bars.csv")

    # Generate fewer trades to keep file size manageable
    trades = generator.generate_trades(symbols, num_trades_per_symbol_per_day=20)
    generator.save_to_csv(trades, "trades.csv")

    print()
    print("=" * 80)
    print("[SUCCESS] Data generation complete!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Run 'python etl/load_data.py' to load data into the warehouse")
    print("  2. Run 'python analytics/run_analysis.py' to execute analytical queries")
    print("  3. Run 'python -m api.main' to start the REST API server")


if __name__ == "__main__":
    main()
