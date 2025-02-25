import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from common.database.models import Base
from common.utils.config import get_config
from cryptography.fernet import Fernet

@pytest.fixture(scope="function", autouse=True)
def setup_test_env():
    """Set up test environment."""
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
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Override the database connection in the application
    import common.database.connection
    common.database.connection._engine = engine  # Store engine reference
    common.database.connection._SessionLocal = SessionLocal  # Store session factory
    common.database.connection.get_session = lambda: session  # Override get_session
    
    yield session
    
    # Clean up
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def test_session(setup_test_env):
    """Get the test session."""
    return setup_test_env 