import pytest
from click.testing import CliRunner
from cli.commands.bot_commands import configure_bot, start_bot, stop_bot
from common.database.models import Client, Bot

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
    return client.client_id

def test_configure_bot(runner, test_client, test_session):
    result = runner.invoke(configure_bot, [
        '--client-id', str(test_client),
        '--pair', 'BTC/SOL',
        '--lower', '20000',
        '--upper', '25000',
        '--grids', '10'
    ])
    assert result.exit_code == 0
    assert "Bot configured" in result.output

    bot = test_session.query(Bot).filter_by(client_id=test_client).first()
    assert bot is not None
    assert bot.pair == 'BTC/SOL'
    assert bot.status == 'configured'
    assert bot.capital_btc == 0.0  # Check initial capital

def test_start_bot(runner, test_client, test_session):
    # First configure a bot
    configure_result = runner.invoke(configure_bot, [
        '--client-id', str(test_client),
        '--pair', 'BTC/SOL',
        '--lower', '20000',
        '--upper', '25000',
        '--grids', '10'
    ])
    assert configure_result.exit_code == 0
    
    result = runner.invoke(start_bot, [
        '--client-id', str(test_client),
        '--pair', 'BTC/SOL',
        '--capital', '0.1'
    ])
    assert result.exit_code == 0
    assert "Bot started" in result.output

    bot = test_session.query(Bot).filter_by(client_id=test_client).first()
    assert bot.status == 'active'
    assert bot.capital_btc == 0.1 