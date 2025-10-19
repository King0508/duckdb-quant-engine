"""
Data validation and quality checks for the ETL pipeline.

Validates data quality before and after loading into the warehouse.
"""

import pandas as pd
from typing import Dict, List, Tuple
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import config


class DataValidator:
    """Validate data quality for market data."""

    def __init__(self):
        """Initialize the validator."""
        self.errors = []
        self.warnings = []

    def validate_symbols(self, df: pd.DataFrame) -> bool:
        """Validate symbols data."""
        print("  Validating symbols data...")

        # Required columns
        required_cols = ["symbol_id", "ticker", "name"]
        for col in required_cols:
            if col not in df.columns:
                self.errors.append(f"Missing required column: {col}")

        # Check for duplicates
        if df["ticker"].duplicated().any():
            duplicates = df[df["ticker"].duplicated()]["ticker"].tolist()
            self.errors.append(f"Duplicate tickers found: {duplicates}")

        # Check for nulls in critical fields
        for col in required_cols:
            if col in df.columns and df[col].isnull().any():
                null_count = df[col].isnull().sum()
                self.errors.append(f"NULL values in {col}: {null_count} rows")

        # Check symbol_id uniqueness
        if df["symbol_id"].duplicated().any():
            self.errors.append("Duplicate symbol_id values found")

        return len(self.errors) == 0

    def validate_bars(self, df: pd.DataFrame) -> bool:
        """Validate OHLCV bars data."""
        print("  Validating bars data...")

        # Required columns
        required_cols = ["symbol_id", "ts", "open", "high", "low", "close", "volume"]
        for col in required_cols:
            if col not in df.columns:
                self.errors.append(f"Missing required column: {col}")
                return False

        # Price validations
        if (df["open"] <= 0).any():
            self.errors.append("Invalid open prices (<=0) found")

        if (df["high"] < df["open"]).any():
            count = (df["high"] < df["open"]).sum()
            self.warnings.append(f"High < Open in {count} rows")

        if (df["high"] < df["close"]).any():
            count = (df["high"] < df["close"]).sum()
            self.warnings.append(f"High < Close in {count} rows")

        if (df["low"] > df["open"]).any():
            count = (df["low"] > df["open"]).sum()
            self.warnings.append(f"Low > Open in {count} rows")

        if (df["low"] > df["close"]).any():
            count = (df["low"] > df["close"]).sum()
            self.warnings.append(f"Low > Close in {count} rows")

        # Volume validation
        if (df["volume"] < 0).any():
            self.errors.append("Negative volume values found")

        if (df["volume"] < config.MIN_VOLUME).any():
            count = (df["volume"] < config.MIN_VOLUME).sum()
            self.warnings.append(
                f"Very low volume (<{config.MIN_VOLUME}) in {count} rows"
            )

        # Check for extreme price changes
        df_sorted = df.sort_values(["symbol_id", "ts"])
        df_sorted["price_change_pct"] = (
            df_sorted.groupby("symbol_id")["close"].pct_change() * 100
        )
        extreme_changes = (
            df_sorted["price_change_pct"].abs() > config.MAX_PRICE_CHANGE_PCT
        )
        if extreme_changes.any():
            count = extreme_changes.sum()
            self.warnings.append(
                f"Extreme price changes (>{config.MAX_PRICE_CHANGE_PCT}%) in {count} rows"
            )

        # Check for nulls
        for col in required_cols:
            if df[col].isnull().any():
                null_count = df[col].isnull().sum()
                self.errors.append(f"NULL values in {col}: {null_count} rows")

        return len(self.errors) == 0

    def validate_trades(self, df: pd.DataFrame) -> bool:
        """Validate trades data."""
        print("  Validating trades data...")

        # Required columns
        required_cols = ["symbol_id", "ts", "price", "size", "side"]
        for col in required_cols:
            if col not in df.columns:
                self.errors.append(f"Missing required column: {col}")
                return False

        # Price validation
        if (df["price"] <= 0).any():
            self.errors.append("Invalid trade prices (<=0) found")

        # Size validation
        if (df["size"] <= 0).any():
            self.errors.append("Invalid trade sizes (<=0) found")

        # Side validation
        valid_sides = ["BUY", "SELL", "UNKNOWN"]
        invalid_sides = ~df["side"].isin(valid_sides)
        if invalid_sides.any():
            count = invalid_sides.sum()
            self.errors.append(
                f"Invalid trade sides in {count} rows (must be {valid_sides})"
            )

        # Check for nulls
        for col in required_cols:
            if df[col].isnull().any():
                null_count = df[col].isnull().sum()
                self.errors.append(f"NULL values in {col}: {null_count} rows")

        return len(self.errors) == 0

    def get_summary(self) -> Dict[str, List[str]]:
        """Get validation summary."""
        return {"errors": self.errors, "warnings": self.warnings}

    def print_summary(self):
        """Print validation summary."""
        if self.errors:
            print("\n  ❌ ERRORS:")
            for error in self.errors:
                print(f"     - {error}")

        if self.warnings:
            print("\n  ⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"     - {warning}")

        if not self.errors and not self.warnings:
            print("  ✅ All validation checks passed!")


def validate_csv_files() -> bool:
    """Validate all CSV files before loading."""
    print("\n" + "=" * 80)
    print("Data Validation")
    print("=" * 80 + "\n")

    validator = DataValidator()
    all_valid = True

    # Validate symbols
    symbols_path = config.get_data_file("symbols.csv")
    if symbols_path.exists():
        df = pd.read_csv(symbols_path)
        print(f"Symbols: {len(df)} records")
        if not validator.validate_symbols(df):
            all_valid = False
    else:
        print(f"⚠️  Symbols file not found: {symbols_path}")
        all_valid = False

    # Validate bars
    bars_path = config.get_data_file("bars.csv")
    if bars_path.exists():
        df = pd.read_csv(bars_path)
        print(f"\nBars: {len(df)} records")
        if not validator.validate_bars(df):
            all_valid = False
    else:
        print(f"⚠️  Bars file not found: {bars_path}")
        all_valid = False

    # Validate trades
    trades_path = config.get_data_file("trades.csv")
    if trades_path.exists():
        df = pd.read_csv(trades_path)
        print(f"\nTrades: {len(df)} records")
        if not validator.validate_trades(df):
            all_valid = False
    else:
        print(f"⚠️  Trades file not found: {trades_path}")
        all_valid = False

    # Print summary
    validator.print_summary()

    print("\n" + "=" * 80)
    if all_valid:
        print("✅ Data validation PASSED")
    else:
        print("❌ Data validation FAILED")
    print("=" * 80 + "\n")

    return all_valid


if __name__ == "__main__":
    success = validate_csv_files()
    sys.exit(0 if success else 1)
