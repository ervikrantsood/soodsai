from sqlalchemy import create_all, Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    """Core Operator Authentication and Profile"""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    name = Column(String(100), nullable=False)
    market_preference = Column(String(50), default='Both') # 'India', 'US', 'Both'
    last_login = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Ticker(Base):
    """Global Asset Telemetry Cache"""
    __tablename__ = 'tickers'
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, nullable=False)
    name = Column(String(200))
    exchange = Column(String(50))
    currency = Column(String(10), default='USD')
    industry = Column(String(100))
    sector = Column(String(100))
    last_price = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ActivityLog(Base):
    """Tactical Audit Trail of Terminal Usage"""
    __tablename__ = 'activity_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    ticker = Column(String(20))
    strategy = Column(String(50)) # 'Entry', 'Exit', 'Duel'
    ai_summary = Column(Text)
    signals = Column(JSON) # Store Soods-Signals as JSON list
    sentiment_score = Column(Float) # Fear & Greed value at time of analysis
    timestamp = Column(DateTime, default=datetime.utcnow)

class Watchlist(Base):
    """User-Defined Asset Monitoring Groups"""
    __tablename__ = 'watchlists'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(100), default='My Watchlist')
    symbols = Column(JSON) # List of symbols
    created_at = Column(DateTime, default=datetime.utcnow)

class InsiderTrade(Base):
    """Whale Watch Persistence Layer"""
    __tablename__ = 'insider_trades'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), index=True)
    insider_name = Column(String(200))
    position = Column(String(100))
    transaction_type = Column(String(50)) # Buy/Sell
    shares = Column(Integer)
    value = Column(Float)
    trade_date = Column(DateTime)
    captured_at = Column(DateTime, default=datetime.utcnow)

class TerminalConfig(Base):
    """Mission Control Layout Persistence"""
    __tablename__ = 'terminal_configs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    layout_state = Column(JSON) # Coordinates, dimensions, ordering
    theme = Column(String(20), default='dark')
    stop_loss_defaults = Column(JSON) # Default simulator settings
