import pytest
from click.testing import CliRunner
from cli.commands.client_commands import add_client_key
from common.database.models import Client
from common.database.connection import get_session

@pytest.fixture
def runner():
    return CliRunner()

def test_add_client_key(runner, test_session):
    result = runner.invoke(add_client_key, [
        '--client-id', '3',  # Use a unique ID
        '--key', 'test_api_key',
        '--secret', 'test_api_secret'
    ])
    assert result.exit_code == 0
    assert "Client API keys stored" in result.output

    client = test_session.query(Client).filter_by(client_id=3).first()
    assert client is not None
    assert client.api_key != 'test_api_key'  # Should be encrypted
    assert client.api_secret != 'test_api_secret'  # Should be encrypted 