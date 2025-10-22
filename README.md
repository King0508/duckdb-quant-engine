# Quantitative Finance Data Warehouse

[![CI/CD Pipeline](https://github.com/King0508/market-data-analytics-db/actions/workflows/ci.yml/badge.svg)](https://github.com/King0508/market-data-analytics-db/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-ready data warehouse for quantitative finance analysis. **Unified platform** combining equity markets, fixed-income Treasuries, and ML-powered sentiment analysis. Built with DuckDB for blazing-fast analytical queries.

## ✨ Features

### 📈 **Equity Markets**

- **⚡ Fast Analytics**: DuckDB columnar storage optimized for OLAP workloads
- **📊 Technical Indicators**: Pre-computed RSI, VWAP, returns, and volume analytics
- **💹 Real-time Data**: 6,000+ OHLCV bars and 125,000+ trade records
- **🔄 Complete ETL Pipeline**: Automated data generation, validation, and loading

### 🏦 **Fixed-Income / Treasuries**

- **📉 Treasury Yields**: US 2Y, 5Y, 10Y, 30Y yield curves
- **💰 ETF Tracking**: TLT, IEF, SHY, LQD, HYG bond ETFs
- **📊 Spread Analysis**: Yield curve inversion detection
- **🔗 Correlations**: Treasury-ETF relationship analysis

### 🤖 **Sentiment Analytics** (Integration Ready)

- **📰 News Analysis**: ML-powered sentiment scoring (FinBERT)
- **🎯 Trading Signals**: Sentiment-based buy/sell signals
- **🔔 Event Detection**: FOMC, CPI, NFP high-impact news
- **📈 Performance Tracking**: Signal backtesting and P&L

### 🛠️ **Infrastructure**

- **🌐 Unified REST API**: Single API serving all data types
- **✅ Production Ready**: Comprehensive tests, CI/CD, logging
- **📈 No API Keys Needed**: Synthetic data generation for offline development
- **🔌 Easy Integration**: Connects with sentiment analysis projects

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/King0508/market-data-analytics-db.git
cd market-data-analytics-db
python -m venv venv
venv\Scripts\activate  # Windows (on Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt

# Generate equity market data
python etl/generate_data.py
python etl/load_data.py

# Generate Treasury & fixed-income data
python etl/generate_treasury_data.py --days 365

# Run equity analytics
python analytics/run_analysis.py

# Start unified REST API
python -m api.main
# Visit http://localhost:8000/docs for interactive API documentation
```

### **Verify Installation**

```bash
# Test API (in another terminal)
curl http://localhost:8000/

# Should return:
{
  "name": "Quantitative Finance Data Warehouse API",
  "version": "2.0.0",
  "features": {
    "equity_market_data": true,
    "treasury_fixed_income": true,
    "sentiment_analysis": true
  }
}
```

## 📊 What's Inside

### 📦 **Database Schema**

#### Equity Tables

- **symbols** - Security master data (ticker, name, sector, market cap)
- **bars** - OHLCV price data with 6,000+ daily bars
- **trades** - 125,000+ individual trade records

#### Treasury Tables

- **treasury_yields** - US Treasury yields (2Y, 5Y, 10Y, 30Y) with 1,000+ records
- **fixed_income_etfs** - Bond ETF prices (TLT, IEF, SHY, LQD, HYG) with 1,300+ records

#### Sentiment Tables (Integration Ready)

- **news_sentiment** - ML-analyzed news with FinBERT sentiment scores
- **sentiment_aggregates** - Hourly sentiment rollups
- **sentiment_signals** - Trading signals with backtest results
- **market_events** - FOMC, CPI, NFP event tracking

### 📊 **Analytical Views**

- **features_returns_rsi** - Returns (1d, 5d, 20d) + RSI indicators (14, 28 period)
- **features_vwap_volume** - VWAP, volume analytics, and anomaly detection
- **daily_metrics** - Daily aggregated stats per symbol
- **v_latest_yields** - Current Treasury yield snapshot
- **v_yield_curve** - Real-time yield curve
- **v_treasury_etf_correlation** - Treasury-ETF relationship metrics

### 🌐 **API Endpoints**

#### Equity Endpoints

```
GET /symbols                    - List all securities
GET /bars/{ticker}              - OHLCV price data
GET /trades/{ticker}            - Trade records
GET /analytics/rsi/{ticker}     - RSI analysis
GET /analytics/vwap/{ticker}    - VWAP analysis
GET /analytics/signals          - Trading signals (overbought/oversold)
```

#### Treasury Endpoints

```
GET /treasury/yields/latest     - Current Treasury yields (all maturities)
GET /treasury/yields/{maturity} - Historical yields (2Y, 5Y, 10Y, 30Y)
GET /treasury/yields/curve      - Yield curve visualization
GET /treasury/etfs/latest       - Current bond ETF prices
GET /treasury/etfs/{ticker}     - Historical ETF data
GET /treasury/analytics/spread  - Yield spread analysis (e.g., 10Y-2Y)
GET /treasury/analytics/correlation - Treasury-ETF correlation
GET /treasury/summary           - Treasury data statistics
```

#### Sentiment Endpoints (Integration Ready)

```
GET /sentiment/news/recent      - Recent news with ML sentiment
GET /sentiment/news/high-impact - FOMC, CPI, Fed speaker news
GET /sentiment/aggregates/timeseries - Hourly sentiment trends
GET /sentiment/signals/recent   - Trading signals from sentiment
GET /sentiment/signals/performance - Signal backtest results
GET /sentiment/analytics/sentiment-distribution - Sentiment breakdown
GET /sentiment/summary          - Sentiment data statistics
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
