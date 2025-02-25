from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from common.utils.config import get_config
import os

_engine = None
_SessionLocal = None

def get_database_engine():
    """Create and return a database engine instance."""
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

def get_session():
    """Create and return a database session."""
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_database_engine()
        _SessionLocal = sessionmaker(bind=engine)
    
    return _SessionLocal() 