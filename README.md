# Quantitative Finance Data Warehouse

[![CI/CD Pipeline](https://github.com/King0508/market-data-analytics-db/actions/workflows/ci.yml/badge.svg)](https://github.com/King0508/market-data-analytics-db/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-ready data warehouse for quantitative finance analysis. Features ETL pipelines, technical indicators (RSI, VWAP), REST API, and automated testing. Built with DuckDB for fast analytical queries on market data.

## ✨ Features

- **⚡ Fast Analytics**: DuckDB columnar storage optimized for OLAP workloads
- **🔄 Complete ETL Pipeline**: Automated data generation, validation, and loading
- **📊 Technical Indicators**: Pre-computed RSI, VWAP, returns, and volume analytics
- **🌐 REST API**: FastAPI endpoints with interactive docs at `/docs`
- **✅ Production Ready**: Comprehensive tests, CI/CD, logging, and error handling
- **📈 Sample Data**: Realistic market data generator (no API keys needed!)

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/King0508/market-data-analytics-db.git
cd market-data-analytics-db
python -m venv venv
venv\Scripts\activate  # Windows (on Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt

# Generate sample data and load warehouse
python etl/generate_data.py
python etl/load_data.py

# Run analytics
python analytics/run_analysis.py

# Start REST API (optional)
python -m api.main  # Visit http://localhost:8000/docs
```

## 📊 What's Inside

### Database Schema

- **symbols** - Security master data (ticker, name, sector, market cap)
- **bars** - OHLCV price data with 6,000+ daily bars
- **trades** - 125,000+ individual trade records

### Analytical Views

- **features_returns_rsi** - Returns (1d, 5d, 20d) + RSI indicators (14, 28 period)
- **features_vwap_volume** - VWAP, volume analytics, and anomaly detection
- **daily_metrics** - Daily aggregated stats per symbol

### API Endpoints

```
GET /symbols              - List all securities
GET /bars/{ticker}        - OHLCV price data
GET /trades/{ticker}      - Trade records
GET /analytics/rsi/{ticker}    - RSI analysis
GET /analytics/vwap/{ticker}   - VWAP analysis
GET /analytics/signals    - Trading signals (overbought/oversold)
```

## 📈 Example Output

```python
# Latest prices with RSI signals
from analytics.run_analysis import AnalyticsEngine

with AnalyticsEngine() as engine:
    signals = engine.get_rsi_signals()
    print(signals)

# Output:
#   symbol  price  rsi_14  rsi_signal
#   MSFT   176.52   80.64  OVERBOUGHT  ⚠️
#   META   269.93   16.93  OVERSOLD    ✅
```

## 🛠️ Tech Stack

- **Database**: DuckDB (embedded analytical database)
- **ETL**: Python with pandas, data validation
- **API**: FastAPI + Uvicorn
- **Testing**: pytest with 35+ test cases
- **CI/CD**: GitHub Actions

## 📚 Documentation

- [Quick Start Guide](QUICKSTART.md) - Get running in 5 minutes
- [Usage Examples](docs/USAGE_EXAMPLES.md) - Code samples and API usage
- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [Contributing](CONTRIBUTING.md) - Development guidelines

## 🎯 Use Cases

- **Backtesting**: Historical market data for strategy testing
- **Research**: Quantitative analysis and indicator development
- **Education**: Learn SQL, databases, and financial analytics
- **Prototyping**: Quick setup for financial applications
- **Portfolio Projects**: Demonstrate full-stack data engineering skills

## 🧪 Testing

```bash
pytest tests/ -v                    # Run all tests
pytest --cov=. --cov-report=html   # With coverage report
make test                           # Using Makefile
```

## 📦 Project Structure

```
market-data-analytics-db/
├── etl/              # ETL pipeline (generate, validate, load)
├── sql/              # Database schema and views
├── api/              # FastAPI REST endpoints
├── analytics/        # Pre-built analytical queries
├── tests/            # Test suite (pytest)
├── examples/         # Usage examples
├── docs/             # Detailed documentation
└── data/             # Generated CSV data
```

## 🤝 Contributing

Contributions welcome! Please check [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📝 License

MIT License - See [LICENSE](LICENSE) for details

## 🎓 About

This project demonstrates production-ready data engineering practices including ETL design, database optimization, API development, testing, and CI/CD automation. Perfect for quantitative finance portfolios and learning modern data stack technologies.

---

**Built with ❤️ for the quantitative finance community**
