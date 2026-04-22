import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .models import Base

# Configuration: Use Environment Variables for Security
# Format: postgresql://user:password@host:port/database
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/soodsai')

# High-Performance Connection Pooling for Rapid Telemetry Retrieval
engine = create_engine(
    DATABASE_URL, 
    pool_size=10, 
    max_overflow=20, 
    pool_timeout=30,
    pool_recycle=1800
)

# Scoped Session for Thread-Safety in Flask
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

def init_db():
    """Initializes the PostgreSQL Schema if it doesn't exist"""
    try:
        Base.metadata.create_all(engine)
        print("Sood AI Database Layer Successfully Synchronized.")
    except Exception as e:
        print(f"CRITICAL: Database Synchronization Failure: {e}")

def get_session():
    """Returns a fresh database session"""
    return Session()

def close_session(exception=None):
    """Closes the scoped session after request completion"""
    Session.remove()
