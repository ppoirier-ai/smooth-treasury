import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from common.database.models import Base
from common.utils.config import get_config
from cryptography.fernet import Fernet
import yaml

@pytest.fixture(scope='session', autouse=True)
def setup_test_config(tmp_path_factory):
    """Create test config with valid encryption key."""
    # Generate a valid Fernet key
    key = Fernet.generate_key().decode()
    
    config = {
        'database': {
            'url': 'sqlite:///:memory:'
        },
        'encryption_key': key,
        'log_level': 'INFO'
    }
    
    # Create config directory if it doesn't exist
    config_dir = tmp_path_factory.mktemp('config')
    config_path = config_dir / 'test_config.yaml'
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    # Set environment variable to point to test config
    os.environ['CONFIG_PATH'] = str(config_path)
    
    yield config_path
    
    # Cleanup
    if 'CONFIG_PATH' in os.environ:
        del os.environ['CONFIG_PATH']

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