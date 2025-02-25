from common.database.models import Base
from common.database.connection import get_database_engine
from common.utils.logger import setup_logger

logger = setup_logger(__name__)

def init_database():
    """Initialize the database by creating all tables."""
    engine = get_database_engine()
    
    try:
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise

if __name__ == "__main__":
    init_database() 