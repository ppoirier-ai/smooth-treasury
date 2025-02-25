import pytest
from common.utils.config import get_config

def test_config_loading(test_config):
    """Test that configuration can be loaded properly."""
    config = get_config()
    assert config is not None
    assert 'database' in config
    assert 'url' in config['database']
    assert config['database']['url'] == "sqlite:///:memory:" 