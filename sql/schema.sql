PRAGMA enable_progress_bar=false;

-- Dimension: one row per instrument
CREATE TABLE IF NOT EXISTS symbols (
  symbol_id  INTEGER PRIMARY KEY,
  ticker     VARCHAR NOT NULL UNIQUE,
  asset_type VARCHAR NOT NULL
);

-- Fact: one row per symbol per minute (OHLCV)
CREATE TABLE IF NOT EXISTS bars (
  symbol_id INTEGER   NOT NULL,
  ts        TIMESTAMP NOT NULL,
  open      DOUBLE    NOT NULL,
  high      DOUBLE    NOT NULL,
  low       DOUBLE    NOT NULL,
  close     DOUBLE    NOT NULL,
  volume    BIGINT    NOT NULL,
  PRIMARY KEY (symbol_id, ts),
  FOREIGN KEY (symbol_id) REFERENCES symbols(symbol_id)
);

-- Fact: many rows per minute from trade prints
CREATE TABLE IF NOT EXISTS trades (
  symbol_id INTEGER   NOT NULL,
  ts        TIMESTAMP NOT NULL,
  price     DOUBLE    NOT NULL,
  size      BIGINT    NOT NULL,
  side      VARCHAR   NOT NULL CHECK (side IN ('B','S')),
  PRIMARY KEY (symbol_id, ts, price, size),
  FOREIGN KEY (symbol_id) REFERENCES symbols(symbol_id)
);

-- Helpful indexes for the common “per-symbol, time-ordered” pattern
CREATE INDEX IF NOT EXISTS idx_bars_symbol_ts   ON bars(symbol_id, ts);
CREATE INDEX IF NOT EXISTS idx_trades_symbol_ts ON trades(symbol_id, ts);
