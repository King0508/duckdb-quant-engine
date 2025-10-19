"""
Configuration management for the quantitative finance data warehouse.
"""

import os
import pathlib
from typing import Optional

# Project root directory
ROOT = pathlib.Path(__file__).resolve().parent

# Database configuration
DB_PATH = ROOT / "warehouse.duckdb"
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))

# Data directories
DATA_DIR = ROOT / "data"
SQL_DIR = ROOT / "sql"
LOGS_DIR = ROOT / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
SQL_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# API configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_WORKERS = int(os.getenv("API_WORKERS", "4"))

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "warehouse.log"

# Data generation configuration
DEFAULT_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA", "AMD"]
DEFAULT_START_DATE = "2022-01-01"
DEFAULT_END_DATE = "2024-12-31"

# ETL configuration
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10000"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))

# Data quality thresholds
MIN_VOLUME = 100
MAX_PRICE_CHANGE_PCT = 50.0  # Flag if price changes more than 50% in one period
OUTLIER_STD_THRESHOLD = 5.0  # Standard deviations for outlier detection

# Feature engineering parameters
RSI_PERIODS = [14, 28]
VWAP_WINDOW = 20
MOVING_AVG_WINDOWS = [5, 10, 20, 50, 200]

# API rate limiting (requests per minute)
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))


def get_db_path() -> pathlib.Path:
    """Get the database path, allowing override via environment variable."""
    env_path = os.getenv("DB_PATH")
    if env_path:
        return pathlib.Path(env_path)
    return DB_PATH


def get_data_file(filename: str) -> pathlib.Path:
    """Get path to a data file."""
    return DATA_DIR / filename


def get_sql_file(filename: str) -> pathlib.Path:
    """Get path to a SQL file."""
    return SQL_DIR / filename
