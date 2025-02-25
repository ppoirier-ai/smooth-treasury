import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from common.database.models import Base
from common.utils.config import get_config
from cryptography.fernet import Fernet

@pytest.fixture(scope="session", autouse=True)
def test_config():
    """Set test configuration for all tests."""
    # Generate a valid Fernet key for testing
    test_key = Fernet.generate_key().decode()
    
    # Set environment variables
    os.environ['CONFIG_PATH'] = os.path.join(os.path.dirname(__file__), '..', 'config', 'test_config.yaml')
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['ENCRYPTION_KEY'] = test_key
    
    # Create test database engine
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    
    # Create session factory
    session_factory = scoped_session(
        sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
    )
    
    # Override the database connection in the application
    import common.database.connection
    common.database.connection._engine = engine
    common.database.connection._SessionLocal = session_factory
    
    yield get_config()
    
    # Clean up
    Base.metadata.drop_all(engine)
    session_factory.remove()

@pytest.fixture
def test_session() -> Session:
    """Create a new database session for a test."""
    from common.database.connection import get_session
    session = get_session()
    
    try:
        yield session
    finally:
        # Rollback any changes and expire all objects
        session.rollback()
        session.expire_all()
        session.close()

@pytest.fixture(autouse=True)
def cleanup_tables(test_session):
    """Clean up tables after each test."""
    yield
    # Clean up all tables
    for table in reversed(Base.metadata.sorted_tables):
        test_session.execute(table.delete())
    test_session.commit()
    # Expire all objects to ensure fresh state
    test_session.expire_all() 