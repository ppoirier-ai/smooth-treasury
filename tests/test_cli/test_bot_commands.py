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
    client = Client(
        client_id=1,
        api_key="test_key",
        api_secret="test_secret"
    )
    test_session.add(client)
    test_session.commit()
    test_session.refresh(client)
    return client

def test_configure_bot(runner, test_client, test_session):
    result = runner.invoke(configure_bot, [
        '--client-id', str(test_client.client_id),
        '--pair', 'BTC/SOL',
        '--lower', '20000',
        '--upper', '25000',
        '--grids', '10'
    ])
    assert result.exit_code == 0
    assert "Bot configured" in result.output

    bot = test_session.query(Bot).filter_by(client_id=test_client.client_id).first()
    assert bot is not None
    assert bot.pair == 'BTC/SOL'
    assert bot.status == 'configured'

def test_start_bot(runner, test_client, test_session):
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

    session = get_session()
    bot = session.query(Bot).filter_by(client_id=1).first()
    assert bot.status == 'active'
    assert bot.capital_btc == 0.1
    session.close() 