-- =============================================================================
-- Features: Returns and RSI (Relative Strength Index)
-- =============================================================================
-- This view calculates price returns and the RSI technical indicator
-- RSI is a momentum oscillator that measures speed and magnitude of price changes
-- =============================================================================

CREATE OR REPLACE VIEW features_returns_rsi AS

WITH price_changes AS (
    SELECT 
        s.ticker AS symbol,
        s.name,
        b.ts,
        b.close,
        b.volume,
        -- Calculate returns
        LAG(b.close, 1) OVER w AS prev_close,
        (b.close - LAG(b.close, 1) OVER w) / LAG(b.close, 1) OVER w AS return_1d,
        (b.close - LAG(b.close, 5) OVER w) / LAG(b.close, 5) OVER w AS return_5d,
        (b.close - LAG(b.close, 20) OVER w) / LAG(b.close, 20) OVER w AS return_20d,
        
        -- Log returns (better for statistical analysis)
        LN(b.close / NULLIF(LAG(b.close, 1) OVER w, 0)) AS log_return_1d,
        
        -- Price changes for RSI calculation
        b.close - LAG(b.close, 1) OVER w AS price_change
    FROM bars b
    JOIN symbols s ON b.symbol_id = s.symbol_id
    WINDOW w AS (PARTITION BY b.symbol_id ORDER BY b.ts)
),

gains_losses AS (
    SELECT 
        *,
        CASE WHEN price_change > 0 THEN price_change ELSE 0 END AS gain,
        CASE WHEN price_change < 0 THEN ABS(price_change) ELSE 0 END AS loss
    FROM price_changes
),

rsi_calc AS (
    SELECT
        *,
        -- Average gains and losses over 14 periods (standard RSI period)
        AVG(gain) OVER (PARTITION BY symbol ORDER BY ts ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_gain_14,
        AVG(loss) OVER (PARTITION BY symbol ORDER BY ts ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_loss_14,
        
        -- Also calculate 28-period RSI for longer-term view
        AVG(gain) OVER (PARTITION BY symbol ORDER BY ts ROWS BETWEEN 27 PRECEDING AND CURRENT ROW) AS avg_gain_28,
        AVG(loss) OVER (PARTITION BY symbol ORDER BY ts ROWS BETWEEN 27 PRECEDING AND CURRENT ROW) AS avg_loss_28
    FROM gains_losses
)

SELECT
    symbol,
    name,
    ts,
    close AS price,
    volume,
    ROUND(return_1d * 100, 4) AS return_1d_pct,
    ROUND(return_5d * 100, 4) AS return_5d_pct,
    ROUND(return_20d * 100, 4) AS return_20d_pct,
    ROUND(log_return_1d, 6) AS log_return_1d,
    
    -- RSI calculation: 100 - (100 / (1 + RS))
    -- where RS = Average Gain / Average Loss
    ROUND(100 - (100 / (1 + NULLIF(avg_gain_14, 0) / NULLIF(avg_loss_14, 0))), 2) AS rsi_14,
    ROUND(100 - (100 / (1 + NULLIF(avg_gain_28, 0) / NULLIF(avg_loss_28, 0))), 2) AS rsi_28,
    
    -- RSI interpretation helpers
    CASE 
        WHEN 100 - (100 / (1 + NULLIF(avg_gain_14, 0) / NULLIF(avg_loss_14, 0))) > 70 THEN 'OVERBOUGHT'
        WHEN 100 - (100 / (1 + NULLIF(avg_gain_14, 0) / NULLIF(avg_loss_14, 0))) < 30 THEN 'OVERSOLD'
        ELSE 'NEUTRAL'
    END AS rsi_signal
    
FROM rsi_calc
WHERE prev_close IS NOT NULL  -- Filter out first row with no previous data
ORDER BY symbol, ts DESC;

