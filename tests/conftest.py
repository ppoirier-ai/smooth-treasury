import os
import pytest
from sqlalchemy import create_engine
from common.database.models import Base
from common.utils.config import get_config

@pytest.fixture(autouse=True)
def test_config():
    """Set test configuration for all tests."""
    os.environ['CONFIG_PATH'] = 'config/test_config.yaml'
    os.environ['ENVIRONMENT'] = 'test'

@pytest.fixture(autouse=True)
def setup_test_database():
    """Create test database tables before tests and drop them after."""
    # Use in-memory SQLite for testing
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    
    # Update the database URL in the config to use our test engine
    config = get_config()
    config['database']['url'] = str(engine.url)
    
    yield engine
    
    Base.metadata.drop_all(engine) 