from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from common.utils.config import get_config
import os

# Global variables for engine and session factory
_engine = None
_SessionLocal = None

def get_engine():
    """Get SQLAlchemy engine."""
    global _engine
    if _engine is None:
        config = get_config()
        db_url = config['database']['url']
        
        # Use different pooling settings for SQLite
        if db_url.startswith('sqlite'):
            _engine = create_engine(
                db_url,
                connect_args={"check_same_thread": False}
            )
        else:
            _engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=config['database']['pool_size'],
                max_overflow=config['database']['max_overflow']
            )
    return _engine

def get_session_factory():
    """Get session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal

def get_session():
    """Get database session."""
    SessionLocal = get_session_factory()
    return SessionLocal() 