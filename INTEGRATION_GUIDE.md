# Fixed-Income Sentiment Integration Guide

## ✅ Integration Complete!

Your `quant-sql-warehouse` and `fixed-income-news-summarizer` projects are now fully integrated.

---

## 📊 Current Data Status

| Table                  | Records | Status     | Purpose                                     |
| ---------------------- | ------- | ---------- | ------------------------------------------- |
| `treasury_yields`      | 1,044   | ✅ Ready   | US Treasury yield curves (2Y, 5Y, 10Y, 30Y) |
| `fixed_income_etfs`    | 1,305   | ✅ Ready   | Bond ETF data (TLT, IEF, SHY, LQD, HYG)     |
| `news_sentiment`       | 2       | ✅ Ready   | ML-analyzed news articles                   |
| `market_events`        | 1,033   | ✅ Ready   | Significant yield movements (≥8 bps)        |
| `sentiment_aggregates` | 2       | ✅ Ready   | Hourly sentiment metrics                    |
| `sentiment_signals`    | 0       | ⚠️ Limited | Trading signals (needs high-impact news)    |

---

## 🚀 How to Run the Integrated System

### **Terminal 1: Warehouse API** (Always Running)

```powershell
cd C:\Users\kings\Downloads\quant-sql-warehouse
python -m api.main
```

- Runs on: `http://localhost:8000`
- Provides: Treasury data, market events, sentiment analytics

### **Terminal 2: Collect News** (Run Periodically)

```powershell
cd C:\Users\kings\Downloads\fixed-income-news-summarizer
.\.venv\Scripts\activate
python -m squawk.main --hours 72 --top 100
```

- Scrapes news from sources (WSJ, Bloomberg, Reuters, etc.)
- Analyzes sentiment with FinBERT ML model
- Stores in warehouse `news_sentiment` table

### **Terminal 3: Rebuild Analytics** (After Collecting News)

```powershell
cd C:\Users\kings\Downloads\quant-sql-warehouse
python etl/build_analytics.py
```

- Regenerates `market_events`, `sentiment_aggregates`, `sentiment_signals`
- Run this after each news collection cycle

### **Terminal 4: Dashboard** (View Results)

```powershell
cd C:\Users\kings\Downloads\fixed-income-news-summarizer
.\.venv\Scripts\activate
streamlit run dashboard/app.py
```

- Runs on: `http://localhost:8501`
- Shows: Live feed, analytics, event studies, backtests

---

## 🎯 How Each Dashboard Tab Works

### **1. Live Feed** ✅

- **Data Source**: `news_sentiment` table
- **Status**: Works with 2 articles (shows older news when you expand time range)
- **To Populate**: Run `squawk.main` to collect more news

### **2. Analytics** ⚠️

- **Data Source**: `sentiment_aggregates` table
- **Status**: Works but limited (only 2 hourly aggregates)
- **To Populate**: Collect more news over multiple hours/days

### **3. Event Studies** ✅

- **Data Source**: `market_events` table
- **Status**: Fully functional with 1,033 events
- **Shows**: Major Treasury yield movements and their timing

### **4. Backtest Results** ⚠️

- **Data Source**: `sentiment_signals` table
- **Status**: Empty (requires high-impact news with strong sentiment)
- **To Populate**: Collect high-impact news (FOMC, CPI, NFP) with sentiment score ≥ 0.3

---

## 📈 Signal Generation Logic

Trading signals are generated when:

1. `is_high_impact = TRUE` (FOMC, CPI, NFP events)
2. `ABS(sentiment_score) >= 0.3` (strong bullish or bearish sentiment)
3. Signal types:
   - `BUY_TREASURIES`: Sentiment ≥ 0.3 (risk-off → yields fall → bond prices rise)
   - `SELL_TREASURIES`: Sentiment ≤ -0.3 (risk-on → yields rise → bond prices fall)
   - `HOLD`: Neutral sentiment

---

## 🔄 Typical Workflow

### **Daily Routine:**

1. **Morning**: Collect overnight news

   ```powershell
   python -m squawk.main --hours 24 --top 50
   ```

2. **Rebuild**: Update analytics

   ```powershell
   python etl/build_analytics.py
   ```

3. **Review**: Check dashboard
   ```powershell
   streamlit run dashboard/app.py
   ```

### **Weekly Routine:**

1. **Weekend**: Generate fresh Treasury data

   ```powershell
   python etl/generate_treasury_data.py --days 365
   ```

2. **Rebuild**: Full analytics refresh
   ```powershell
   python etl/build_analytics.py
   ```

---

## 🧪 Testing the Integration

### **1. Test API Endpoints:**

```powershell
# Treasury data
curl http://localhost:8000/treasury/yields/latest
curl http://localhost:8000/treasury/summary

# Sentiment data (use 168 hours = 7 days to see the 2 articles)
curl "http://localhost:8000/sentiment/news/recent?hours=168&limit=10"
curl http://localhost:8000/sentiment/summary
```

### **2. Test Database:**

```python
import duckdb
conn = duckdb.connect('warehouse.duckdb')

# Check all tables
tables = ['treasury_yields', 'news_sentiment', 'market_events', 'sentiment_aggregates']
for t in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"{t}: {count} records")

conn.close()
```

---

## ⚠️ Why Dashboard May Show "Empty" Tabs

### **Live Feed: No articles?**

- Articles from Oct 16-17 are outside default 24-hour window
- **Fix**: In dashboard, expand time range to 7 days (168 hours)

### **Backtest Results: No signals?**

- Current 2 articles are neutral (score 0.0) and not high-impact
- **Fix**: Collect news during major events (FOMC meetings, CPI releases)

### **Analytics: No trends?**

- Only 2 hourly aggregates - not enough for meaningful trends
- **Fix**: Collect news over multiple days to build history

---

## 🎓 Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│                    QUANT-SQL-WAREHOUSE                      │
│                 (Central Data Repository)                   │
├────────────────────────────────────────────────────────────┤
│                                                              │
│  Raw Data (Read-Only for Dashboard):                        │
│  ├─ treasury_yields        (1,044 records)                  │
│  ├─ fixed_income_etfs      (1,305 records)                  │
│  └─ news_sentiment         (2 records) ← Written by Squawk  │
│                                                              │
│  Derived Analytics (Built by build_analytics.py):           │
│  ├─ market_events          (1,033 records)                  │
│  ├─ sentiment_aggregates   (2 records)                      │
│  └─ sentiment_signals      (0 records)                      │
│                                                              │
│  REST API (http://localhost:8000):                          │
│  ├─ /treasury/*            (Yield curves, ETF data)         │
│  ├─ /sentiment/*           (News, signals, analytics)       │
│  └─ /analytics/*           (Equity market analytics)        │
│                                                              │
└────────────────────────────────────────────────────────────┘
                              ▲
                              │ Reads Data
                              │
┌────────────────────────────────────────────────────────────┐
│             FIXED-INCOME-NEWS-SUMMARIZER                    │
│               (Data Collection & Display)                   │
├────────────────────────────────────────────────────────────┤
│                                                              │
│  Data Collection (squawk.main):                             │
│  └─ Scrapes news → ML analysis → Writes to warehouse        │
│                                                              │
│  Dashboard (Streamlit):                                     │
│  ├─ Live Feed      (reads news_sentiment)                   │
│  ├─ Analytics      (reads sentiment_aggregates)             │
│  ├─ Event Studies  (reads market_events)                    │
│  └─ Backtest       (reads sentiment_signals)                │
│                                                              │
└────────────────────────────────────────────────────────────┘
```

---

## 📝 Key Files

### **Warehouse Project:**

- `etl/generate_treasury_data.py` - Generate synthetic Treasury data
- `etl/build_analytics.py` - Build derived analytics tables
- `api/main.py` - Unified REST API
- `api/treasury_routes.py` - Treasury endpoints
- `api/sentiment_routes.py` - Sentiment endpoints
- `sql/fixed_income_schema.sql` - Treasury/ETF schema
- `sql/sentiment_schema.sql` - Sentiment schema

### **Summarizer Project:**

- `squawk/main.py` - News collection with ML analysis
- `dashboard/app.py` - Streamlit dashboard
- (Files in other project - not shown here)

---

## 🐛 Troubleshooting

### **Problem: "Database is locked"**

- **Cause**: API server has database open
- **Fix**: Stop API server before running ETL scripts
  ```powershell
  # Find process
  netstat -ano | findstr :8000
  # Kill it
  taskkill /F /PID <PID>
  ```

### **Problem: "No module named 'fastapi'"**

- **Cause**: Missing dependencies
- **Fix**:
  ```powershell
  pip install -r requirements.txt
  ```

### **Problem: "Dashboard shows no data"**

- **Cause**: Time range too narrow (articles from Oct 16-17)
- **Fix**: In dashboard, change time range to 7 days (168 hours)

### **Problem: "Sentiment signals = 0"**

- **Cause**: No high-impact news with strong sentiment
- **Fix**: Collect news during major economic events (FOMC, CPI, NFP)

---

## ✅ Success Checklist

- [x] Warehouse has Treasury data (1,044 yields + 1,305 ETFs)
- [x] Warehouse has sentiment schema (all tables created)
- [x] API serves both Treasury and sentiment endpoints
- [x] Analytics builder (`build_analytics.py`) populates derived tables
- [x] News collector can write to warehouse
- [x] Dashboard can read from warehouse
- [ ] Collect 50+ articles over multiple days (user action)
- [ ] Generate signals from high-impact news (user action)

---

## 🎉 You're Ready!

The integration is complete. Start collecting news and the dashboard will populate automatically!

**Next Steps:**

1. Run news collector daily: `python -m squawk.main --hours 24 --top 50`
2. Rebuild analytics: `python etl/build_analytics.py`
3. View dashboard: `streamlit run dashboard/app.py`

Good luck! 🚀
