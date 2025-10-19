# Architecture Documentation

## System Overview

The Quantitative Finance SQL Warehouse is a data warehouse system designed for storing and analyzing financial market data. It uses DuckDB as the analytical database engine and provides multiple interfaces for data access.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Sources                             │
│  (CSV Files, Market APIs, Historical Data Providers)         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     ETL Pipeline                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Data Gen    │  │  Validation  │  │  Loader      │      │
│  │  (generate_  │→ │  (data_      │→ │  (load_      │      │
│  │   data.py)   │  │   validator) │  │   data.py)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   DuckDB Warehouse                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Raw Tables          Views              Indexes      │   │
│  │  • symbols           • returns_rsi      • ts         │   │
│  │  • bars              • vwap_volume      • symbol_id  │   │
│  │  • trades            • daily_metrics    • sector     │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────┬───────────────────────┬─────────────────────┘
                │                       │
                ▼                       ▼
┌───────────────────────┐   ┌──────────────────────────┐
│   Analytics Module    │   │      REST API            │
│   (run_analysis.py)   │   │      (FastAPI)           │
│                       │   │                          │
│  • Performance        │   │  Endpoints:              │
│  • Technical          │   │  • /symbols              │
│  • Volume Analysis    │   │  • /bars/{ticker}        │
│  • Correlations       │   │  • /analytics/rsi        │
└───────────────────────┘   └──────────────────────────┘
                │                       │
                ▼                       ▼
┌──────────────────────────────────────────────────────────┐
│                    End Users                              │
│  • Traders    • Researchers    • Applications            │
└──────────────────────────────────────────────────────────┘
```

## Components

### 1. ETL Pipeline

#### Data Generator (`etl/generate_data.py`)

- Generates realistic market data for testing
- Creates symbols, OHLCV bars, and trade data
- Uses statistical models for realistic patterns
- Configurable date ranges and symbols

**Key Features:**

- Log-normal distribution for volumes
- Geometric Brownian motion for prices
- Realistic intraday patterns
- Power-law distribution for trade sizes

#### Data Validator (`etl/data_validator.py`)

- Pre-load data quality checks
- Validates data integrity and constraints
- Detects outliers and anomalies
- Provides warnings and errors

**Validation Rules:**

- Price validations (positive, OHLC relationships)
- Volume validations (non-negative)
- Referential integrity checks
- Outlier detection (z-score based)

#### Data Loader (`etl/load_data.py`)

- Loads CSV data into DuckDB
- Applies schema and creates tables
- Installs analytical views
- Provides logging and error handling

**Process:**

1. Validate CSV files
2. Connect to database
3. Apply schema
4. Stage data in temp views
5. Load into typed tables
6. Create analytical views
7. Generate summary statistics

### 2. Database Layer

#### Schema Design

**symbols** - Security Master

- Primary key: `symbol_id`
- Attributes: ticker, name, sector, industry, market_cap
- Indexes: ticker, sector

**bars** - OHLCV Data

- Composite primary key: (symbol_id, ts)
- Attributes: open, high, low, close, volume
- Indexes: ts, (symbol_id, ts)
- Time-series data optimized for queries

**trades** - Transaction Data

- Composite primary key: (symbol_id, ts, price, size)
- Attributes: price, size, side (BUY/SELL)
- Indexes: ts, (symbol_id, ts), side
- High-volume tick data

#### Analytical Views

**features_returns_rsi**

- Calculates returns (1d, 5d, 20d)
- RSI indicator (14 and 28 periods)
- Trading signals (overbought/oversold)
- Window functions for time-series analysis

**features_vwap_volume**

- VWAP calculation
- Volume analytics
- Volume trends and ratios
- Volume categorization

**daily_metrics**

- Daily aggregated statistics
- OHLC summary
- Volume totals
- Buy/sell flow analysis

### 3. Analytics Module

Provides pre-built analytical queries:

- Latest prices and returns
- Top/bottom performers
- RSI signals
- Volume analysis
- VWAP comparisons
- Correlation matrices

**Design Pattern:**

- Context manager for connection handling
- Pandas DataFrame outputs
- Parameterized queries
- Read-only connections

### 4. REST API

FastAPI-based REST API for programmatic access:

**Endpoints:**

- `/symbols` - List securities
- `/bars/{ticker}` - Get OHLCV data
- `/trades/{ticker}` - Get trade data
- `/analytics/rsi/{ticker}` - RSI analysis
- `/analytics/vwap/{ticker}` - VWAP analysis
- `/analytics/performance` - Performance rankings
- `/analytics/signals` - Trading signals

**Features:**

- Query parameter validation
- Error handling
- JSON serialization
- Interactive documentation (Swagger UI)
- Health check endpoint

## Data Flow

### Write Path (ETL)

```
CSV Files → Validation → Staging Views → Typed Tables → Views
```

### Read Path (Analytics)

```
Views → Analytics Engine → Pandas DataFrame → Display
```

### Read Path (API)

```
HTTP Request → API Endpoint → Database Query → JSON Response
```

## Performance Considerations

### Database Optimization

- **Columnar storage**: DuckDB's columnar format optimizes analytical queries
- **Indexes**: Strategic indexes on time, symbol_id, and sector
- **Views**: Pre-computed complex calculations
- **Partitioning**: Time-based partitioning potential for large datasets

### Query Optimization

- **Window functions**: Efficient for time-series calculations
- **CTEs**: Improved readability and optimization
- **Batch operations**: Bulk inserts for better performance
- **Read-only connections**: For analytics and API

### Scalability

- **Horizontal**: Multiple read replicas possible
- **Vertical**: DuckDB scales with available memory
- **Caching**: API-level caching for hot data
- **Compression**: Built-in compression in DuckDB

## Security

### Data Access

- Read-only connections for analytics and API
- No user authentication (add as needed)
- SQL injection prevention via parameterized queries

### Data Validation

- Input validation at ETL stage
- Constraint checks at database level
- Type enforcement via schema

## Deployment

### Local Development

```bash
python etl/generate_data.py
python etl/load_data.py
python analytics/run_analysis.py
python -m api.main
```

### Production Considerations

1. **Database**: Move to persistent storage
2. **API**: Deploy with Gunicorn/Uvicorn workers
3. **Monitoring**: Add logging, metrics, alerting
4. **Backup**: Regular database backups
5. **Security**: Add authentication, rate limiting
6. **Caching**: Redis for API responses
7. **Load balancing**: Multiple API instances

## Technology Choices

### Why DuckDB?

- **Embedded**: No server management
- **Fast**: Optimized for analytics
- **SQL**: Standard SQL interface
- **Portable**: Single file database
- **Open source**: Free and well-maintained

### Why FastAPI?

- **Modern**: Async support
- **Fast**: High performance
- **Type hints**: Built-in validation
- **Documentation**: Auto-generated OpenAPI docs
- **Pythonic**: Clean, readable code

### Why Pandas?

- **Standard**: De facto for data analysis
- **Integration**: Works with DuckDB
- **Rich**: Comprehensive data manipulation
- **Visualization**: Easy plotting integration

## Extension Points

### Adding New Data Types

1. Extend schema in `sql/schema.sql`
2. Update data generator
3. Add validation rules
4. Create relevant views
5. Add API endpoints

### Adding New Analytics

1. Create SQL views in `sql/views/`
2. Add query functions in analytics module
3. Create API endpoints
4. Add tests

### Integration with External Systems

- Market data APIs (Alpha Vantage, IEX Cloud)
- Trading platforms (Interactive Brokers, TD Ameritrade)
- Data lakes (S3, Azure Blob Storage)
- BI tools (Tableau, Power BI, Metabase)

## References

- [DuckDB Documentation](https://duckdb.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Quantitative Finance Resources](https://www.quantstart.com/)

