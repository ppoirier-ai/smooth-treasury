from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from common.utils.config import get_config
import logging
from common.database.models import Base

logger = logging.getLogger(__name__)

# Global variables for engine and session factory
_engine = None
_SessionLocal = None

def init_db():
    """Initialize database and create tables."""
    config = get_config()
    db_url = config.get('database', {}).get('url')
    
    if not db_url:
        raise ValueError("Database URL not configured")
    
    engine = create_engine(db_url)
    logger.info(f"Creating database tables at {db_url}")
    Base.metadata.create_all(bind=engine)
    
    return engine, sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_engine():
    """Get SQLAlchemy engine."""
    global _engine, _SessionLocal
    if _engine is None:
        _engine, _SessionLocal = init_db()
    return _engine

def get_session_factory():
    """Get session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal

def get_session():
    """Get database session."""
    global _engine, _SessionLocal
    if _SessionLocal is None:
        _engine, _SessionLocal = init_db()
    return _SessionLocal() 