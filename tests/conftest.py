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
    
    # Verify config can be loaded
    config = get_config()
    assert config is not None
    return config

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture(scope="session")
def SessionLocal(test_engine):
    """Create a session factory."""
    return scoped_session(
        sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=test_engine
        )
    )

@pytest.fixture
def test_session(SessionLocal, monkeypatch) -> Session:
    """Create a new database session for a test."""
    session = SessionLocal()
    
    # Mock the get_session function
    def mock_get_session():
        return session
    
    # Patch the get_session function
    import common.database.connection
    monkeypatch.setattr(common.database.connection, "get_session", mock_get_session)
    
    yield session
    
    # Clean up
    session.rollback()
    SessionLocal.remove() 