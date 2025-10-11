-- sql/views/features_vwap_volume.sql
-- 30-minute rolling VWAP from trades and a z-score of rolling volume.

CREATE OR REPLACE VIEW features__vwap_volume_z AS
WITH roll AS (
  SELECT
    symbol_id,
    ts,
    -- time-based rolling window over last 30 minutes (per symbol, in timestamp order)
    SUM(price*size) OVER w / NULLIF(SUM(size) OVER w, 0) AS vwap_30m,
    SUM(size) OVER w AS vol_30m
  FROM trades
  WINDOW w AS (
    PARTITION BY symbol_id ORDER BY ts
    RANGE BETWEEN INTERVAL '30 minutes' PRECEDING AND CURRENT ROW
  )
),
z AS (
  SELECT
    symbol_id, ts, vwap_30m, vol_30m,
    -- row-based rolling window (last ~N rows) to standardize volume
    AVG(vol_30m)        OVER w2 AS avg_vol,
    STDDEV_SAMP(vol_30m)OVER w2 AS sd_vol
  FROM roll
  WINDOW w2 AS (
    PARTITION BY symbol_id ORDER BY ts
    ROWS BETWEEN 180 PRECEDING AND CURRENT ROW
  )
)
SELECT
  symbol_id, ts, vwap_30m, vol_30m,
  CASE WHEN sd_vol IS NULL OR sd_vol = 0 THEN NULL
       ELSE (vol_30m - avg_vol) / sd_vol
  END AS z_vol_30m;
