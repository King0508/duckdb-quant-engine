# Fixed Income Sentiment Analytics Integration

This document describes the sentiment analysis extension to the quant-sql-warehouse.

## Overview

The `fixed-income-news-summarizer` project has been integrated with this data warehouse to provide:
- ML-based sentiment analysis of fixed-income news
- Trading signal generation from sentiment
- Event impact studies
- Sentiment-market correlation analysis

## New Database Tables

### news_sentiment
Stores news articles with FinBERT sentiment analysis:
- Sentiment scores (-1 to 1)
- Confidence levels
- Extracted entities (Fed officials, indicators, instruments)
- High-impact flags

### sentiment_aggregates  
Hourly aggregated sentiment metrics:
- Average sentiment per hour
- Risk-on/off/neutral counts
- Major event flags (FOMC, CPI, NFP)

### market_events
Major economic events with pre/post sentiment:
- Event classification
- Sentiment before/after event
- Market impact levels

### sentiment_signals
Trading signals with backtest results:
- Signal type (BUY_TLT, SELL_TLT)
- Entry/exit prices
- P&L and performance metrics

## New API Endpoints

All endpoints are available at `/sentiment/*`:

### GET /sentiment/recent
Get recent news with sentiment analysis
```bash
curl "http://localhost:8000/sentiment/recent?hours=24&high_impact_only=true"
```

### GET /sentiment/timeseries
Get hourly sentiment aggregates
```bash
curl "http://localhost:8000/sentiment/timeseries?hours=168"
```

### GET /sentiment/stats
Get overall sentiment statistics
```bash
curl "http://localhost:8000/sentiment/stats"
```

### GET /sentiment/events
Get major market events with sentiment impact
```bash
curl "http://localhost:8000/sentiment/events?days=30&event_type=FOMC"
```

### GET /sentiment/signals
Get trading signals with performance
```bash
curl "http://localhost:8000/sentiment/signals?days=30&signal_type=BUY_TLT"
```

### GET /sentiment/signals/performance
Get aggregated signal performance metrics
```bash
curl "http://localhost:8000/sentiment/signals/performance"
```

### GET /sentiment/search
Search news by keyword
```bash
curl "http://localhost:8000/sentiment/search?keyword=powell&days=30"
```

## Setup Instructions

### 1. Initialize Sentiment Schema

```bash
# From quant-sql-warehouse directory
python -c "import duckdb; conn = duckdb.connect('warehouse.duckdb'); conn.execute(open('sql/sentiment_schema.sql').read())"
```

### 2. Collect News Data

```bash
# From fixed-income-news-summarizer directory
cd ../fixed-income-news-summarizer
python -m squawk.main --hours 24 --top 50
```

This will:
- Fetch news from configured RSS feeds
- Analyze sentiment with FinBERT
- Extract financial entities
- Store in warehouse

### 3. Start API with Sentiment Endpoints

```bash
# From quant-sql-warehouse directory
python -m api.main

# API will be available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

The API now includes both market data AND sentiment endpoints.

### 4. Launch Dashboard

```bash
# From fixed-income-news-summarizer directory
streamlit run dashboard/app.py

# Dashboard at http://localhost:8501
```

## Integration Architecture

```
fixed-income-news-summarizer/
├── squawk/
│   ├── ml_sentiment.py          → FinBERT analysis
│   ├── entity_extraction.py     → NER
│   └── warehouse_integration.py → Connects to warehouse
└── analytics/
    ├── correlations.py          → Sentiment-market correlation
    ├── event_studies.py         → Event impact analysis
    └── signals.py               → Signal generation

                    ↓

quant-sql-warehouse/
├── warehouse.duckdb             → Unified database
├── sql/sentiment_schema.sql     → Sentiment tables
└── api/
    ├── main.py                  → Extended API
    └── sentiment_api.py         → New sentiment routes
```

## Data Flow

1. **Collection**: RSS feeds → News items
2. **Processing**: FinBERT → Sentiment scores + Entity extraction
3. **Storage**: warehouse_integration.py → warehouse.duckdb
4. **Aggregation**: Hourly metrics computed
5. **Analysis**: Correlations, events, signals
6. **Serving**: FastAPI endpoints + Streamlit dashboard

## Database Queries Example

```sql
-- Recent high-impact news
SELECT timestamp, title, sentiment_score, sentiment_label, confidence
FROM news_sentiment
WHERE is_high_impact = TRUE
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- Hourly sentiment trend
SELECT hour_timestamp, avg_sentiment, sentiment_count
FROM sentiment_aggregates
WHERE hour_timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY hour_timestamp;

-- Signal performance
SELECT signal_type, COUNT(*) as trades, AVG(return_pct) as avg_return
FROM sentiment_signals
WHERE exit_timestamp IS NOT NULL
GROUP BY signal_type;

-- Sentiment vs market (requires joining with bars/symbols)
SELECT 
  sa.hour_timestamp,
  sa.avg_sentiment,
  b.close as market_price
FROM sentiment_aggregates sa
JOIN symbols s ON s.ticker = 'TLT'
JOIN bars b ON b.symbol_id = s.symbol_id 
  AND b.ts BETWEEN sa.hour_timestamp - INTERVAL '1 hour' 
                AND sa.hour_timestamp + INTERVAL '1 hour'
ORDER BY sa.hour_timestamp;
```

## Analytics Integration

The sentiment data can be combined with existing technical indicators:

```python
# Sentiment + RSI analysis
SELECT 
  f.ts,
  f.symbol,
  f.price,
  f.rsi_14,
  sa.avg_sentiment
FROM features_returns_rsi f
LEFT JOIN sentiment_aggregates sa 
  ON date_trunc('hour', f.ts) = sa.hour_timestamp
WHERE f.symbol = 'TLT'
ORDER BY f.ts DESC;
```

## API Response Examples

### Recent News
```json
{
  "data": [
    {
      "news_id": 1,
      "timestamp": "2025-10-21T14:30:00",
      "source": "Reuters",
      "title": "Fed signals caution on rate cuts amid sticky inflation",
      "sentiment_score": -0.42,
      "sentiment_label": "risk-off",
      "confidence": 0.89,
      "fed_officials": ["Jerome Powell"],
      "economic_indicators": ["CPI", "FOMC"],
      "is_high_impact": true
    }
  ],
  "count": 1
}
```

### Signal Performance
```json
{
  "data": [
    {
      "signal_type": "BUY_TLT",
      "total_signals": 15,
      "winning_trades": 9,
      "win_rate_pct": 60.0,
      "avg_return_pct": 0.45,
      "total_pnl": 127.35
    }
  ]
}
```

## Maintenance

### Recompute Aggregates
```python
from squawk.warehouse_integration import get_warehouse
warehouse = get_warehouse()
warehouse.compute_sentiment_aggregates(hours_back=168)
```

### Check Data Quality
```sql
-- Missing timestamps
SELECT date_trunc('hour', timestamp) as hour, COUNT(*)
FROM news_sentiment
GROUP BY hour
HAVING COUNT(*) < 1;

-- Confidence distribution
SELECT 
  CASE 
    WHEN confidence >= 0.8 THEN 'high'
    WHEN confidence >= 0.6 THEN 'medium'
    ELSE 'low'
  END as confidence_level,
  COUNT(*) as count
FROM news_sentiment
GROUP BY confidence_level;
```

## Performance Considerations

- **Aggregates**: Recompute hourly for fresh data
- **Indexes**: Already optimized for timestamp queries
- **API Limits**: Default 500 items per request
- **Dashboard**: Uses caching for expensive queries

## Troubleshooting

### Sentiment endpoints return 404
- Ensure `sentiment_schema.sql` has been executed
- Check API startup logs for import errors

### No sentiment data in dashboard
- Run news collection: `python -m squawk.main`
- Check warehouse connection path
- Verify data with: `SELECT COUNT(*) FROM news_sentiment`

### FinBERT model not loading
- Install transformers: `pip install transformers torch`
- First run downloads model (~500MB)
- Requires internet connection

## Future Enhancements

Potential additions:
- Real-time streaming (WebSocket)
- Multi-instrument analysis
- Portfolio-level sentiment
- Alternative data sources (Twitter, earnings calls)
- Advanced ML models (sentiment forecasting)

## Contact

For issues or questions about the integration, see the main README in `fixed-income-news-summarizer`.

