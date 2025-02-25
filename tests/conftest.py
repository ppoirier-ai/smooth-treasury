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
    config = get_config()
    engine = create_engine(config['database']['url'])
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine) 