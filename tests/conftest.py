import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
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
    
    # Verify config can be loaded
    config = get_config()
    assert config is not None
    return config

@pytest.fixture
def test_db():
    """Create test database engine."""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def test_session(test_db) -> Session:
    """Create a new database session for a test."""
    connection = test_db.connect()
    transaction = connection.begin()
    
    TestingSessionLocal = sessionmaker(bind=connection)
    session = TestingSessionLocal()

    # Override the get_session function to use our test session
    from common.database.connection import get_session
    def mock_get_session():
        return session
    
    # Store the original function
    original_get_session = get_session
    import common.database.connection
    common.database.connection.get_session = mock_get_session
    
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        # Restore the original function
        common.database.connection.get_session = original_get_session 