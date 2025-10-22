-- =============================================================================
-- Fixed Income Sentiment Analytics Extension
-- Extends quant-sql-warehouse with news sentiment analysis capabilities
-- =============================================================================

-- Drop existing sentiment tables if they exist
DROP TABLE IF EXISTS sentiment_signals;
DROP TABLE IF EXISTS sentiment_aggregates;
DROP TABLE IF EXISTS market_events;
DROP TABLE IF EXISTS news_sentiment;

-- Drop and create sequence for news_id
DROP SEQUENCE IF EXISTS news_sentiment_id_seq;
CREATE SEQUENCE news_sentiment_id_seq START 1;

-- =============================================================================
-- NEWS_SENTIMENT TABLE
-- Stores news articles with ML-based sentiment analysis
-- =============================================================================
CREATE TABLE news_sentiment (
    news_id      INTEGER PRIMARY KEY DEFAULT nextval('news_sentiment_id_seq'),
    timestamp    TIMESTAMP NOT NULL,
    source       VARCHAR NOT NULL,
    title        VARCHAR NOT NULL,
    summary      TEXT,
    link         VARCHAR,
    
    -- Sentiment analysis (FinBERT)
    sentiment_score     DOUBLE NOT NULL,  -- -1 (bearish) to 1 (bullish)
    sentiment_label     VARCHAR NOT NULL CHECK (sentiment_label IN ('risk-on', 'risk-off', 'neutral')),
    confidence          DOUBLE,  -- Model confidence 0-1
    
    -- Entity extraction
    fed_officials       VARCHAR[],
    economic_indicators VARCHAR[],
    treasury_instruments VARCHAR[],
    credit_terms        VARCHAR[],
    yields              VARCHAR[],
    basis_points        VARCHAR[],
    
    -- High-impact flag
    is_high_impact      BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_news_timestamp ON news_sentiment(timestamp);
CREATE INDEX idx_news_sentiment_label ON news_sentiment(sentiment_label);
CREATE INDEX idx_news_source ON news_sentiment(source);
CREATE INDEX idx_news_high_impact ON news_sentiment(is_high_impact);

-- =============================================================================
-- MARKET_EVENTS TABLE
-- Stores major economic events (FOMC, CPI, NFP, etc.)
-- =============================================================================
DROP SEQUENCE IF EXISTS seq_market_events;
CREATE SEQUENCE seq_market_events START 1;

CREATE TABLE market_events (
    event_id    INTEGER PRIMARY KEY DEFAULT nextval('seq_market_events'),
    timestamp   TIMESTAMP NOT NULL,
    event_type  VARCHAR NOT NULL,  -- 'FOMC', 'CPI', 'NFP', 'AUCTION', 'FED_SPEECH'
    description TEXT NOT NULL,
    
    -- Market impact
    impact_level        VARCHAR CHECK (impact_level IN ('high', 'medium', 'low')),
    pre_event_sentiment DOUBLE,  -- Avg sentiment 24h before
    post_event_sentiment DOUBLE,  -- Avg sentiment 24h after
    
    -- Metadata
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_timestamp ON market_events(timestamp);
CREATE INDEX idx_events_type ON market_events(event_type);

-- =============================================================================
-- SENTIMENT_AGGREGATES TABLE
-- Hourly aggregated sentiment metrics for analysis
-- =============================================================================
DROP SEQUENCE IF EXISTS seq_sentiment_aggregates;
CREATE SEQUENCE seq_sentiment_aggregates START 1;

CREATE TABLE sentiment_aggregates (
    aggregate_id        INTEGER PRIMARY KEY DEFAULT nextval('seq_sentiment_aggregates'),
    hour_timestamp      TIMESTAMP NOT NULL UNIQUE,
    
    -- Aggregate metrics
    avg_sentiment       DOUBLE NOT NULL,
    sentiment_count     INTEGER NOT NULL,
    risk_on_count       INTEGER NOT NULL DEFAULT 0,
    risk_off_count      INTEGER NOT NULL DEFAULT 0,
    neutral_count       INTEGER NOT NULL DEFAULT 0,
    
    -- High-impact news flags
    has_fomc            BOOLEAN DEFAULT FALSE,
    has_cpi             BOOLEAN DEFAULT FALSE,
    has_nfp             BOOLEAN DEFAULT FALSE,
    has_fed_speaker     BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agg_hour ON sentiment_aggregates(hour_timestamp);

-- =============================================================================
-- SENTIMENT_SIGNALS TABLE
-- Trading signals based on sentiment + market data
-- =============================================================================
DROP SEQUENCE IF EXISTS seq_sentiment_signals;
CREATE SEQUENCE seq_sentiment_signals START 1;

CREATE TABLE sentiment_signals (
    signal_id           INTEGER PRIMARY KEY DEFAULT nextval('seq_sentiment_signals'),
    signal_timestamp    TIMESTAMP NOT NULL,
    
    -- Signal details
    signal_type         VARCHAR NOT NULL,  -- 'BUY_TLT', 'SELL_TLT', 'NEUTRAL'
    signal_strength     DOUBLE,  -- 0-1
    sentiment_input     DOUBLE,  -- Sentiment that triggered signal
    market_input        DOUBLE,  -- Market data that triggered signal (e.g., yield level)
    
    -- Position tracking (for backtesting)
    entry_price         DOUBLE,
    exit_price          DOUBLE,
    exit_timestamp      TIMESTAMP,
    
    -- Performance
    pnl                 DOUBLE,
    return_pct          DOUBLE,
    hold_hours          DOUBLE,
    
    -- Metadata
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_signals_timestamp ON sentiment_signals(signal_timestamp);
CREATE INDEX idx_signals_type ON sentiment_signals(signal_type);

-- =============================================================================
-- VIEWS FOR ANALYTICS
-- =============================================================================

-- Recent high-impact news (last 24 hours)
CREATE VIEW v_recent_high_impact AS
SELECT 
    news_id,
    timestamp,
    source,
    title,
    sentiment_score,
    sentiment_label,
    confidence,
    fed_officials,
    economic_indicators,
    treasury_instruments
FROM news_sentiment
WHERE 
    timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
    AND is_high_impact = TRUE
ORDER BY timestamp DESC;

-- Hourly sentiment trend (last 7 days)
CREATE VIEW v_sentiment_trend AS
SELECT 
    hour_timestamp,
    avg_sentiment,
    sentiment_count,
    risk_on_count,
    risk_off_count,
    neutral_count,
    has_fomc OR has_cpi OR has_nfp AS has_major_event
FROM sentiment_aggregates
WHERE hour_timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY hour_timestamp DESC;

-- Signal performance summary
CREATE VIEW v_signal_performance AS
SELECT 
    signal_type,
    COUNT(*) as total_signals,
    SUM(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) as winning_trades,
    AVG(return_pct) as avg_return_pct,
    SUM(pnl) as total_pnl,
    AVG(hold_hours) as avg_hold_hours
FROM sentiment_signals
WHERE exit_timestamp IS NOT NULL
GROUP BY signal_type
ORDER BY total_pnl DESC;

-- =============================================================================
-- COMMENTS
-- =============================================================================
COMMENT ON TABLE news_sentiment IS 'Fixed-income news articles with ML-based sentiment analysis';
COMMENT ON TABLE market_events IS 'Major economic events (FOMC, CPI, NFP) with market impact';
COMMENT ON TABLE sentiment_aggregates IS 'Hourly aggregated sentiment metrics';
COMMENT ON TABLE sentiment_signals IS 'Trading signals generated from sentiment + market data';

