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
def test_data():
    session = get_session()
    
    # Create test client
    client = Client(client_id=1, api_key="test", api_secret="test")
    session.add(client)
    
    # Create test bot
    bot = Bot(
        client_id=1,
        pair='BTC/SOL',
        status='active',
        lower_price=20000,
        upper_price=25000,
        grids=10,
        capital_btc=0.1
    )
    session.add(bot)
    
    # Create test trades
    trade1 = Trade(
        bot_id=1,
        timestamp=datetime.now() - timedelta(hours=12),
        amount_btc=0.01,
        profit_btc=0.001
    )
    trade2 = Trade(
        bot_id=1,
        timestamp=datetime.now() - timedelta(days=2),
        amount_btc=0.01,
        profit_btc=0.002
    )
    session.add_all([trade1, trade2])
    
    session.commit()
    yield
    
    # Cleanup
    session.query(Trade).delete()
    session.query(Bot).delete()
    session.query(Client).delete()
    session.commit()
    session.close()

def test_status(runner, test_data):
    result = runner.invoke(status, ['--client-id', '1'])
    assert result.exit_code == 0
    assert "BTC/SOL" in result.output
    assert "active" in result.output

def test_metrics(runner, test_data):
    result = runner.invoke(metrics, ['--client-id', '1'])
    assert result.exit_code == 0
    assert "btc_profit_24h" in result.output
    assert "roi_24h" in result.output 