-- =============================================================================
-- Features: VWAP and Volume Analytics
-- =============================================================================
-- This view calculates Volume Weighted Average Price and volume analytics
-- VWAP is the average price weighted by volume, useful for execution analysis
-- =============================================================================

CREATE OR REPLACE VIEW features_vwap_volume AS

WITH daily_metrics AS (
    SELECT
        s.ticker AS symbol,
        s.name,
        DATE_TRUNC('day', b.ts) AS date,
        b.ts,
        b.close,
        b.volume,
        b.high,
        b.low,
        
        -- Typical price for VWAP calculation
        (b.high + b.low + b.close) / 3.0 AS typical_price
    FROM bars b
    JOIN symbols s ON b.symbol_id = s.symbol_id
),

vwap_calc AS (
    SELECT
        symbol,
        name,
        date,
        ts,
        close,
        volume,
        high,
        low,
        typical_price,
        
        -- Cumulative volume and volume*price for VWAP
        SUM(volume) OVER w AS cumulative_volume,
        SUM(typical_price * volume) OVER w AS cumulative_tp_volume,
        
        -- Rolling volume metrics
        AVG(volume) OVER (PARTITION BY symbol ORDER BY ts ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS avg_volume_20,
        MAX(volume) OVER (PARTITION BY symbol ORDER BY ts ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS max_volume_20,
        
        -- Volume moving averages
        AVG(volume) OVER (PARTITION BY symbol ORDER BY ts ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS vol_ma_5,
        AVG(volume) OVER (PARTITION BY symbol ORDER BY ts ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) AS vol_ma_10
    FROM daily_metrics
    WINDOW w AS (PARTITION BY symbol, date ORDER BY ts)
),

volume_stats AS (
    SELECT
        *,
        -- VWAP calculation
        cumulative_tp_volume / NULLIF(cumulative_volume, 0) AS vwap,
        
        -- Volume ratio to average
        volume / NULLIF(avg_volume_20, 0) AS volume_ratio,
        
        -- Volume trend
        CASE 
            WHEN vol_ma_5 > vol_ma_10 THEN 'INCREASING'
            WHEN vol_ma_5 < vol_ma_10 THEN 'DECREASING'
            ELSE 'STABLE'
        END AS volume_trend
    FROM vwap_calc
)

SELECT
    symbol,
    name,
    date,
    ts,
    ROUND(close, 2) AS price,
    volume,
    ROUND(vwap, 2) AS vwap,
    ROUND(avg_volume_20, 0) AS avg_volume_20,
    ROUND(volume_ratio, 2) AS volume_ratio,
    volume_trend,
    
    -- Price relative to VWAP (useful for execution)
    ROUND(((close - vwap) / NULLIF(vwap, 0)) * 100, 2) AS price_vs_vwap_pct,
    
    -- Volume classification
    CASE
        WHEN volume > avg_volume_20 * 2 THEN 'VERY_HIGH'
        WHEN volume > avg_volume_20 * 1.5 THEN 'HIGH'
        WHEN volume < avg_volume_20 * 0.5 THEN 'LOW'
        WHEN volume < avg_volume_20 * 0.25 THEN 'VERY_LOW'
        ELSE 'NORMAL'
    END AS volume_category,
    
    -- Cumulative volume for the day
    ROUND(cumulative_volume, 0) AS day_cumulative_volume
    
FROM volume_stats
ORDER BY symbol, ts DESC;

