-- sql/views/features_returns_rsi.sql
-- Rolling 1-minute returns and 14-period RSI computed from minute bars.

CREATE OR REPLACE VIEW features__returns_rsi AS
WITH b AS (
  SELECT
    symbol_id,
    ts,
    close,
    -- r_1m: percent change from previous close (per symbol, in time order)
    close / NULLIF(LAG(close, 1) OVER (PARTITION BY symbol_id ORDER BY ts), 0) - 1 AS r_1m
  FROM bars
),
rsi_prep AS (
  SELECT
    symbol_id, ts, r_1m,
    GREATEST(r_1m, 0)  AS gain,  -- keep positive part
    GREATEST(-r_1m, 0) AS loss   -- keep magnitude of negative part
  FROM b
),
rsi_agg AS (
  SELECT
    symbol_id, ts, r_1m,
    -- 14-row rolling averages (13 preceding + current)
    AVG(gain) OVER (
      PARTITION BY symbol_id ORDER BY ts
      ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
    ) AS avg_gain,
    AVG(loss) OVER (
      PARTITION BY symbol_id ORDER BY ts
      ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
    ) AS avg_loss
  FROM rsi_prep
)
SELECT
  symbol_id, ts, r_1m,
  CASE
    WHEN avg_loss IS NULL OR avg_loss = 0 THEN 100.0
    ELSE 100.0 - (100.0 / (1.0 + (avg_gain / NULLIF(avg_loss,0))))
  END AS rsi_14
FROM rsi_agg;
