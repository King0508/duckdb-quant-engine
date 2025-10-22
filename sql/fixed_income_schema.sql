-- =============================================================================
-- Fixed Income Market Data Extension
-- Extends quant-sql-warehouse with Treasury yields and fixed-income ETFs
-- =============================================================================

-- Drop existing tables if they exist
DROP TABLE IF EXISTS treasury_yields;
DROP TABLE IF EXISTS fixed_income_etfs;

-- =============================================================================
-- TREASURY_YIELDS TABLE
-- Stores US Treasury yield data across different maturities
-- =============================================================================
CREATE SEQUENCE IF NOT EXISTS seq_treasury_yields START 1;

CREATE TABLE treasury_yields (
    yield_id        INTEGER PRIMARY KEY DEFAULT nextval('seq_treasury_yields'),
    timestamp       TIMESTAMP NOT NULL,
    maturity        VARCHAR NOT NULL,  -- '2Y', '5Y', '10Y', '30Y'
    yield_rate      DOUBLE NOT NULL,   -- Yield in percentage (e.g., 4.25 = 4.25%)
    
    -- Calculated changes
    change_1d       DOUBLE,  -- Daily change in basis points
    change_1w       DOUBLE,  -- Weekly change in basis points
    change_1m       DOUBLE,  -- Monthly change in basis points
    
    -- Data source
    source          VARCHAR DEFAULT 'FRED',
    
    -- Metadata
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_treasury_timestamp ON treasury_yields(timestamp);
CREATE INDEX idx_treasury_maturity ON treasury_yields(maturity);
CREATE INDEX idx_treasury_maturity_time ON treasury_yields(maturity, timestamp);

-- =============================================================================
-- FIXED_INCOME_ETFS TABLE
-- Stores fixed-income ETF price and volume data
-- =============================================================================
CREATE SEQUENCE IF NOT EXISTS seq_fixed_income_etfs START 1;

CREATE TABLE fixed_income_etfs (
    etf_id          INTEGER PRIMARY KEY DEFAULT nextval('seq_fixed_income_etfs'),
    timestamp       TIMESTAMP NOT NULL,
    ticker          VARCHAR NOT NULL,   -- 'TLT', 'IEF', 'SHY', 'LQD', 'HYG'
    name            VARCHAR NOT NULL,   -- Full ETF name
    
    -- Price data
    open            DOUBLE NOT NULL,
    high            DOUBLE NOT NULL,
    low             DOUBLE NOT NULL,
    close           DOUBLE NOT NULL,
    volume          BIGINT NOT NULL,
    
    -- Calculated metrics
    return_1d       DOUBLE,  -- Daily return in percentage
    return_1w       DOUBLE,  -- Weekly return in percentage
    return_1m       DOUBLE,  -- Monthly return in percentage
    avg_volume_20d  BIGINT,  -- 20-day average volume
    
    -- Data source
    source          VARCHAR DEFAULT 'YahooFinance',
    
    -- Metadata
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_etf_timestamp ON fixed_income_etfs(timestamp);
CREATE INDEX idx_etf_ticker ON fixed_income_etfs(ticker);
CREATE INDEX idx_etf_ticker_time ON fixed_income_etfs(ticker, timestamp);

-- =============================================================================
-- VIEWS FOR ANALYTICS
-- =============================================================================

-- Latest Treasury yields (most recent snapshot)
CREATE OR REPLACE VIEW v_latest_yields AS
SELECT DISTINCT ON (maturity)
    maturity,
    timestamp,
    yield_rate,
    change_1d,
    change_1w,
    change_1m,
    source
FROM treasury_yields
ORDER BY maturity, timestamp DESC;

-- Latest ETF prices (most recent snapshot)
CREATE OR REPLACE VIEW v_latest_etfs AS
SELECT DISTINCT ON (ticker)
    ticker,
    name,
    timestamp,
    close as price,
    volume,
    return_1d,
    return_1w,
    return_1m
FROM fixed_income_etfs
ORDER BY ticker, timestamp DESC;

-- Yield curve (current)
CREATE OR REPLACE VIEW v_yield_curve AS
SELECT 
    maturity,
    yield_rate,
    timestamp
FROM v_latest_yields
ORDER BY 
    CASE maturity
        WHEN '2Y' THEN 1
        WHEN '5Y' THEN 2
        WHEN '10Y' THEN 3
        WHEN '30Y' THEN 4
    END;

-- Treasury-ETF correlation data
CREATE OR REPLACE VIEW v_treasury_etf_correlation AS
SELECT 
    ty.timestamp,
    ty.maturity,
    ty.yield_rate,
    ty.change_1d as yield_change_bps,
    etf.ticker,
    etf.close as etf_price,
    etf.return_1d as etf_return_pct
FROM treasury_yields ty
JOIN fixed_income_etfs etf 
    ON DATE_TRUNC('day', ty.timestamp) = DATE_TRUNC('day', etf.timestamp)
WHERE ty.timestamp >= CURRENT_TIMESTAMP - INTERVAL '90 days'
ORDER BY ty.timestamp DESC;

-- =============================================================================
-- COMMENTS
-- =============================================================================
COMMENT ON TABLE treasury_yields IS 'US Treasury yield data across multiple maturities (2Y, 5Y, 10Y, 30Y)';
COMMENT ON TABLE fixed_income_etfs IS 'Fixed-income ETF price and volume data (TLT, IEF, SHY, LQD, HYG)';
COMMENT ON VIEW v_latest_yields IS 'Most recent Treasury yield snapshot';
COMMENT ON VIEW v_latest_etfs IS 'Most recent fixed-income ETF prices';
COMMENT ON VIEW v_yield_curve IS 'Current yield curve across maturities';

