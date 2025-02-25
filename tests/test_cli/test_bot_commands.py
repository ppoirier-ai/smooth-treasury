import pytest
from click.testing import CliRunner
from cli.commands.bot_commands import configure_bot, start_bot, stop_bot
from common.database.models import Client, Bot
from common.database.connection import get_session

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def test_client(test_session):
    """Create a test client."""
    client = Client(
        client_id=1,
        api_key="test_key",
        api_secret="test_secret"
    )
    test_session.add(client)
    test_session.commit()
    
    # Get a fresh instance that's attached to the session
    client = test_session.query(Client).filter_by(client_id=1).first()
    return client

def test_configure_bot(runner, test_client, test_session):
    # Ensure client is attached to session
    test_session.add(test_client)
    
    result = runner.invoke(configure_bot, [
        '--client-id', str(test_client.client_id),
        '--pair', 'BTC/SOL',
        '--lower', '20000',
        '--upper', '25000',
        '--grids', '10'
    ])
    assert result.exit_code == 0
    assert "Bot configured" in result.output

    # Refresh the session to get the latest state
    test_session.expire_all()
    bot = test_session.query(Bot).filter_by(client_id=test_client.client_id).first()
    assert bot is not None
    assert bot.pair == 'BTC/SOL'
    assert bot.status == 'configured'
    assert bot.capital_btc == 0.0  # Check initial capital

def test_start_bot(runner, test_client, test_session):
    # Ensure client is attached to session
    test_session.add(test_client)
    
    # First configure a bot
    configure_result = runner.invoke(configure_bot, [
        '--client-id', str(test_client.client_id),
        '--pair', 'BTC/SOL',
        '--lower', '20000',
        '--upper', '25000',
        '--grids', '10'
    ])
    assert configure_result.exit_code == 0
    
    result = runner.invoke(start_bot, [
        '--client-id', str(test_client.client_id),
        '--pair', 'BTC/SOL',
        '--capital', '0.1'
    ])
    assert result.exit_code == 0
    assert "Bot started" in result.output

    # Refresh the session to get the latest state
    test_session.expire_all()
    bot = test_session.query(Bot).filter_by(client_id=test_client.client_id).first()
    assert bot.status == 'active'
    assert bot.capital_btc == 0.1 