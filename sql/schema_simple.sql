-- =============================================================================
-- Quantitative Finance Data Warehouse Schema (DuckDB Compatible)
-- =============================================================================

-- Drop existing tables if they exist
DROP TABLE IF EXISTS trades;
DROP TABLE IF EXISTS bars;
DROP TABLE IF EXISTS symbols;

-- =============================================================================
-- SYMBOLS TABLE
-- =============================================================================
CREATE TABLE symbols (
    symbol_id    INTEGER PRIMARY KEY,
    ticker       VARCHAR NOT NULL UNIQUE,
    name         VARCHAR NOT NULL,
    sector       VARCHAR,
    industry     VARCHAR,
    market_cap   BIGINT,
    exchange     VARCHAR DEFAULT 'NASDAQ',
    currency     VARCHAR DEFAULT 'USD',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_symbols_ticker ON symbols(ticker);
CREATE INDEX idx_symbols_sector ON symbols(sector);

-- =============================================================================
-- BARS TABLE
-- =============================================================================
CREATE TABLE bars (
    symbol_id    INTEGER NOT NULL,
    ts           TIMESTAMP NOT NULL,
    open         DOUBLE NOT NULL CHECK (open > 0),
    high         DOUBLE NOT NULL,
    low          DOUBLE NOT NULL,
    close        DOUBLE NOT NULL CHECK (close > 0),
    volume       BIGINT NOT NULL CHECK (volume >= 0),
    
    PRIMARY KEY (symbol_id, ts),
    FOREIGN KEY (symbol_id) REFERENCES symbols(symbol_id)
);

CREATE INDEX idx_bars_ts ON bars(ts);
CREATE INDEX idx_bars_symbol_ts ON bars(symbol_id, ts);

-- =============================================================================
-- TRADES TABLE
-- =============================================================================
CREATE TABLE trades (
    symbol_id    INTEGER NOT NULL,
    ts           TIMESTAMP NOT NULL,
    price        DOUBLE NOT NULL CHECK (price > 0),
    size         BIGINT NOT NULL CHECK (size > 0),
    side         VARCHAR CHECK (side IN ('BUY', 'SELL', 'UNKNOWN')),
    
    PRIMARY KEY (symbol_id, ts, price, size),
    FOREIGN KEY (symbol_id) REFERENCES symbols(symbol_id)
);

CREATE INDEX idx_trades_ts ON trades(ts);
CREATE INDEX idx_trades_symbol_ts ON trades(symbol_id, ts);
CREATE INDEX idx_trades_side ON trades(side);

