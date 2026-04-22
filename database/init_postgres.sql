-- SOOD AI - PostgreSQL Initialization Script (v5.0.0)
-- --------------------------------------------------

-- 1. Create Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    name VARCHAR(100) NOT NULL,
    market_preference VARCHAR(50) DEFAULT 'Both',
    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 2. Create Tickers Cache
CREATE TABLE IF NOT EXISTS tickers (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200),
    exchange VARCHAR(50),
    currency VARCHAR(10) DEFAULT 'USD',
    industry VARCHAR(100),
    sector VARCHAR(100),
    last_price FLOAT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create Activity Logs
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    ticker VARCHAR(20),
    strategy VARCHAR(50),
    ai_summary TEXT,
    signals JSONB, -- Binary JSON for high-speed indexing
    sentiment_score FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Create Watchlists
CREATE TABLE IF NOT EXISTS watchlists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(100) DEFAULT 'My Watchlist',
    symbols JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Create Insider Trades (Whale Watch)
CREATE TABLE IF NOT EXISTS insider_trades (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20),
    insider_name VARCHAR(200),
    position VARCHAR(100),
    transaction_type VARCHAR(50),
    shares INTEGER,
    value FLOAT,
    trade_date TIMESTAMP,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Create Terminal Configuration
CREATE TABLE IF NOT EXISTS terminal_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id),
    layout_state JSONB,
    theme VARCHAR(20) DEFAULT 'dark',
    stop_loss_defaults JSONB
);

-- Indexes for Mission-Critical Performance
CREATE INDEX idx_ticker_symbol ON tickers(symbol);
CREATE INDEX idx_activity_ticker ON activity_logs(ticker);
CREATE INDEX idx_insider_ticker ON insider_trades(ticker);
CREATE INDEX idx_activity_timestamp ON activity_logs(timestamp DESC);

INSERT INTO users (email, password_hash, name, market_preference) 
VALUES ('admin@soodsai.com', 'PBKDF2_HASH_PLACEHOLDER', 'Administrator', 'Both')
ON CONFLICT (email) DO NOTHING;
