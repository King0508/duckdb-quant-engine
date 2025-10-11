-- 1) Quick health checks
SELECT * FROM symbols;
SELECT COUNT(*) AS n_bars   FROM bars;
SELECT COUNT(*) AS n_trades FROM trades;

-- 2) Peek first few bars per symbol (chronological)
SELECT symbol_id, ts, open, high, low, close, volume
FROM bars
ORDER BY symbol_id, ts
LIMIT 10;

-- 3) Returns + RSI from the view (requires features_returns_rsi.sql installed)
SELECT symbol_id, ts, r_1m, rsi_14
FROM features__returns_rsi
WHERE symbol_id = 1
ORDER BY ts
LIMIT 10;

-- 4) VWAP + volume z-score from the view (requires features_vwap_volume.sql installed)
SELECT symbol_id, ts, vwap_30m, z_vol_30m
FROM features__vwap_volume_z
WHERE symbol_id = 2
ORDER BY ts
LIMIT 10;

-- 5) Align trade-time features to bar-time grid (nearest trade <= bar ts)
--    This lets you join VWAP/z-volume to the bar rows for signal generation/backtests.
WITH nearest_trade AS (
  SELECT
    b.symbol_id,
    b.ts AS bar_ts,
    -- last trade timestamp at or before the bar timestamp (per symbol)
    LAST_VALUE(t.ts) IGNORE NULLS OVER (
      PARTITION BY b.symbol_id
      ORDER BY b.ts
      RANGE BETWEEN INTERVAL '30 seconds' PRECEDING AND CURRENT ROW
    ) AS trade_ts
  FROM bars b
  LEFT JOIN trades t
    ON t.symbol_id = b.symbol_id
   AND t.ts <= b.ts
)
SELECT
  b.symbol_id,
  b.ts,
  b.close,
  r.r_1m,
  r.rsi_14,
  v.vwap_30m,
  v.z_vol_30m
FROM bars b
LEFT JOIN features__returns_rsi r
  ON r.symbol_id = b.symbol_id AND r.ts = b.ts
LEFT JOIN nearest_trade nt
  ON nt.symbol_id = b.symbol_id AND nt.bar_ts = b.ts
LEFT JOIN features__vwap_volume_z v
  ON v.symbol_id = nt.symbol_id AND v.ts = nt.trade_ts
ORDER BY b.symbol_id, b.ts
LIMIT 20;
