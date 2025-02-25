import pytest
from click.testing import CliRunner
from cli.commands.metrics_commands import status, metrics
from common.database.models import Client, Bot, Trade
from common.database.connection import get_session
from datetime import datetime, timedelta

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def test_data(test_session):
    # Create test client with unique ID
    client = Client(client_id=2, api_key="test", api_secret="test")
    test_session.add(client)
    test_session.flush()  # Get the ID without committing
    
    # Create test bot
    bot = Bot(
        client_id=client.client_id,
        pair='BTC/SOL',
        status='active',
        lower_price=20000,
        upper_price=25000,
        grids=10,
        capital_btc=0.1
    )
    test_session.add(bot)
    test_session.flush()
    
    # Create test trades
    trade1 = Trade(
        bot_id=bot.bot_id,
        timestamp=datetime.now() - timedelta(hours=12),
        amount_btc=0.01,
        profit_btc=0.001
    )
    trade2 = Trade(
        bot_id=bot.bot_id,
        timestamp=datetime.now() - timedelta(days=2),
        amount_btc=0.01,
        profit_btc=0.002
    )
    test_session.add_all([trade1, trade2])
    test_session.commit()
    return client.client_id

def test_status(runner, test_data):
    result = runner.invoke(status, ['--client-id', str(test_data)])
    assert result.exit_code == 0
    assert "BTC/SOL" in result.output
    assert "active" in result.output

def test_metrics(runner, test_data):
    result = runner.invoke(metrics, ['--client-id', str(test_data)])
    assert result.exit_code == 0
    assert "btc_profit_24h" in result.output
    assert "roi_24h" in result.output 