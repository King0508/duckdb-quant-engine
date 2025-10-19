-- =============================================================================
-- Daily Metrics Summary View
-- =============================================================================
-- Aggregated daily statistics for each symbol
-- Useful for daily reporting and analysis
-- =============================================================================

CREATE OR REPLACE VIEW daily_metrics AS

WITH daily_bars AS (
    SELECT
        s.ticker AS symbol,
        s.name,
        s.sector,
        DATE_TRUNC('day', b.ts) AS date,
        MIN(b.ts) AS first_ts,
        MAX(b.ts) AS last_ts,
        COUNT(*) AS num_bars,
        
        -- OHLC for the day (using first/last bars)
        FIRST(b.open ORDER BY b.ts) AS day_open,
        MAX(b.high) AS day_high,
        MIN(b.low) AS day_low,
        LAST(b.close ORDER BY b.ts) AS day_close,
        
        -- Volume metrics
        SUM(b.volume) AS total_volume,
        AVG(b.volume) AS avg_volume,
        MAX(b.volume) AS max_volume,
        
        -- Price metrics
        AVG(b.close) AS avg_price,
        STDDEV(b.close) AS price_volatility
    FROM bars b
    JOIN symbols s ON b.symbol_id = s.symbol_id
    GROUP BY s.ticker, s.name, s.sector, DATE_TRUNC('day', b.ts)
),

daily_trades AS (
    SELECT
        s.ticker AS symbol,
        DATE_TRUNC('day', t.ts) AS date,
        COUNT(*) AS num_trades,
        SUM(t.size) AS trade_volume,
        AVG(t.price) AS avg_trade_price,
        
        -- Buy/Sell analysis
        SUM(CASE WHEN t.side = 'BUY' THEN t.size ELSE 0 END) AS buy_volume,
        SUM(CASE WHEN t.side = 'SELL' THEN t.size ELSE 0 END) AS sell_volume,
        COUNT(CASE WHEN t.side = 'BUY' THEN 1 END) AS buy_count,
        COUNT(CASE WHEN t.side = 'SELL' THEN 1 END) AS sell_count
    FROM trades t
    JOIN symbols s ON t.symbol_id = s.symbol_id
    GROUP BY s.ticker, DATE_TRUNC('day', t.ts)
)

SELECT
    b.symbol,
    b.name,
    b.sector,
    b.date,
    b.num_bars,
    
    -- OHLC
    ROUND(b.day_open, 2) AS open,
    ROUND(b.day_high, 2) AS high,
    ROUND(b.day_low, 2) AS low,
    ROUND(b.day_close, 2) AS close,
    
    -- Daily return
    ROUND(((b.day_close - b.day_open) / NULLIF(b.day_open, 0)) * 100, 2) AS daily_return_pct,
    
    -- Intraday range
    ROUND(((b.day_high - b.day_low) / NULLIF(b.day_low, 0)) * 100, 2) AS intraday_range_pct,
    
    -- Volume
    b.total_volume,
    ROUND(b.avg_volume, 0) AS avg_volume_per_bar,
    
    -- Volatility
    ROUND(b.price_volatility, 2) AS price_volatility,
    
    -- Trade statistics
    COALESCE(t.num_trades, 0) AS num_trades,
    COALESCE(t.trade_volume, 0) AS trade_volume,
    COALESCE(ROUND(t.avg_trade_price, 2), 0) AS avg_trade_price,
    
    -- Order flow
    COALESCE(t.buy_volume, 0) AS buy_volume,
    COALESCE(t.sell_volume, 0) AS sell_volume,
    CASE 
        WHEN COALESCE(t.buy_volume, 0) + COALESCE(t.sell_volume, 0) > 0 
        THEN ROUND((COALESCE(t.buy_volume, 0)::DOUBLE / (COALESCE(t.buy_volume, 0) + COALESCE(t.sell_volume, 0))) * 100, 2)
        ELSE 50.0
    END AS buy_ratio_pct

FROM daily_bars b
LEFT JOIN daily_trades t ON b.symbol = t.symbol AND b.date = t.date
ORDER BY b.date DESC, b.symbol;

