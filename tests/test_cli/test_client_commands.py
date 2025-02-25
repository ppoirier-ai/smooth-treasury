import pytest
from click.testing import CliRunner
from cli.commands.client_commands import add_client_key
from common.database.models import Client
from common.database.connection import get_session
from common.utils.config import get_config
from cryptography.fernet import Fernet

@pytest.fixture
def runner():
    return CliRunner()

def test_add_client_key(runner, test_session):
    client_id = 3  # Use a unique ID
    
    # Get encryption key from config
    config = get_config()
    key = config.get('encryption_key')
    assert key is not None, "Encryption key not found in config"
    
    result = runner.invoke(add_client_key, [
        '--client-id', str(client_id),
        '--api-key', 'test_api_key',
        '--api-secret', 'test_api_secret'
    ])
    assert result.exit_code == 0
    
    # Verify client was added
    client = test_session.query(Client).filter_by(client_id=client_id).first()
    assert client is not None
    assert client.api_key != 'test_api_key'  # Should be encrypted
    assert client.api_secret != 'test_api_secret'  # Should be encrypted 