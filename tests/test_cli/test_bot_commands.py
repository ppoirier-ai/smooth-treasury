import pytest
from click.testing import CliRunner
from cli.commands.bot_commands import configure_bot, start_bot, stop_bot
from common.database.models import Client, Bot
from common.database.connection import get_session

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def test_client():
    session = get_session()
    client = Client(
        client_id=1,
        api_key="test_key",
        api_secret="test_secret"
    )
    session.add(client)
    session.commit()
    yield client
    session.delete(client)
    session.commit()
    session.close()

def test_configure_bot(runner, test_client):
    result = runner.invoke(configure_bot, [
        '--client-id', '1',
        '--pair', 'BTC/SOL',
        '--lower', '20000',
        '--upper', '25000',
        '--grids', '10'
    ])
    assert result.exit_code == 0
    assert "Bot configured" in result.output

    session = get_session()
    bot = session.query(Bot).filter_by(client_id=1).first()
    assert bot is not None
    assert bot.pair == 'BTC/SOL'
    assert bot.status == 'configured'
    session.close()

def test_start_bot(runner, test_client):
    # First configure a bot
    runner.invoke(configure_bot, [
        '--client-id', '1',
        '--pair', 'BTC/SOL',
        '--lower', '20000',
        '--upper', '25000',
        '--grids', '10'
    ])
    
    result = runner.invoke(start_bot, [
        '--client-id', '1',
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