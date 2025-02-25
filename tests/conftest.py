import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from common.database.models import Base
from common.utils.config import get_config
from cryptography.fernet import Fernet

@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    return create_engine('sqlite:///:memory:', echo=False)

@pytest.fixture(scope="session")
def tables(engine):
    """Create all tables."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="session")
def session_factory(engine):
    """Create session factory."""
    return scoped_session(sessionmaker(bind=engine))

@pytest.fixture
def test_session(session_factory, tables):
    """Create a new database session for a test."""
    session = session_factory()
    yield session
    session.close()
    session_factory.remove()

@pytest.fixture(autouse=True)
def setup_test_env(test_session):
    """Set up test environment."""
    # Generate a valid Fernet key for testing
    test_key = Fernet.generate_key().decode()
    
    # Set environment variables
    os.environ['CONFIG_PATH'] = os.path.join(os.path.dirname(__file__), '..', 'config', 'test_config.yaml')
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['ENCRYPTION_KEY'] = test_key
    
    # Override the database connection in the application
    import common.database.connection
    common.database.connection.get_session = lambda: test_session
    
    yield
    
    # Clean up tables after each test
    for table in reversed(Base.metadata.sorted_tables):
        test_session.execute(table.delete())
    test_session.commit() 