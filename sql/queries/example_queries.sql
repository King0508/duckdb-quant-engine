-- sql/queries/example_queries.sql
-- Demo queries: health checks, feature previews, and bar↔trade alignment.

-- 1) Quick health checks
SELECT * FROM symbols;
SELECT COUNT(*) AS n_bars   FROM bars;
SELECT COUNT(*) AS n_trades FROM trades;

-- 2) Peek first few bars per symbol (chronological)
SELECT symbol_id, ts, open, high, low, close, volume
FROM bars
ORDER BY symbol_id, ts
LIMIT 10;

-- 3) Returns + RSI from the view
SELECT symbol_id, ts, r_1m, rsi_14
FROM features__returns_rsi
WHERE symbol_id = 1
ORDER BY ts
LIMIT 10;

-- 4) VWAP + volume z-score from the trades view
SELECT symbol_id, ts, vwap_30m, z_vol_30m
FROM features__vwap_volume_z
WHERE symbol_id = 2
ORDER BY ts
LIMIT 10;

-- 5) Align trade-time features to the bar grid (nearest trade <= bar ts)
-- Portable pattern (no IGNORE NULLS): rank trades up to the bar and pick rn=1.
WITH joined AS (
  SELECT
    b.symbol_id,
    b.ts AS bar_ts,
    b.close,
    r.r_1m,
    r.rsi_14,
    t.ts AS trade_ts
  FROM bars b
  LEFT JOIN features__returns_rsi r
    ON r.symbol_id = b.symbol_id AND r.ts = b.ts
  LEFT JOIN trades t
    ON t.symbol_id = b.symbol_id AND t.ts <= b.ts
),
ranked AS (
  SELECT
    symbol_id,
    bar_ts,
    close,
    r_1m,
    rsi_14,
    trade_ts,
    ROW_NUMBER() OVER (
      PARTITION BY symbol_id, bar_ts
      ORDER BY (trade_ts IS NULL), trade_ts DESC
    ) AS rn
  FROM joined
)
SELECT
  r.symbol_id,
  r.bar_ts AS ts,
  r.close,
  r.r_1m,
  r.rsi_14,
  v.vwap_30m,
  v.z_vol_30m
FROM ranked r
LEFT JOIN features__vwap_volume_z v
  ON v.symbol_id = r.symbol_id AND v.ts = r.trade_ts
WHERE r.rn = 1
ORDER BY r.symbol_id, r.bar_ts
LIMIT 20;
