import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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

@pytest.fixture(scope="session")
def test_db():
    """Create test database engine."""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    
    # Override the get_session function to use our test database
    from common.database.connection import _SessionLocal
    global _SessionLocal
    _SessionLocal = TestingSessionLocal
    
    return engine

@pytest.fixture
def test_session(test_db):
    """Create a new database session for a test."""
    Session = sessionmaker(bind=test_db)
    session = Session()
    try:
        yield session
    finally:
        session.close() 