from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from common.utils.config import get_config

def get_database_engine():
    """Create and return a database engine instance."""
    config = get_config()
    db_url = config['database']['url']
    
    engine = create_engine(
        db_url,
        poolclass=QueuePool,
        pool_size=config['database']['pool_size'],
        max_overflow=config['database']['max_overflow']
    )
    return engine

def get_session():
    """Create and return a database session."""
    engine = get_database_engine()
    Session = sessionmaker(bind=engine)
    return Session() 