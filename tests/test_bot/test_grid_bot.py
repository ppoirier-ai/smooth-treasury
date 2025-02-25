import pytest
from unittest.mock import Mock
from common.bot.grid_bot import GridBot
from common.exchange.client import ExchangeClient

@pytest.fixture
def mock_client():
    client = Mock(spec=ExchangeClient)
    client.create_order.return_value = {'id': '123', 'status': 'open'}
    client.cancel_all_orders.return_value = True
    return client

def test_grid_bot_initialization():
    """Test grid bot initialization."""
    client = Mock(spec=ExchangeClient)
    bot = GridBot(
        bot_id=1,
        client=client,
        pair='BTC/USDT',
        lower=20000,
        upper=25000,
        grids=5,
        capital=1.0
    )
    
    assert bot.bot_id == 1
    assert bot.pair == 'BTC/USDT'
    assert len(bot.levels) == 5
    assert len(bot.orders) == 8  # (5-1) * 2 orders

def test_grid_bot_start(mock_client):
    """Test grid bot start."""
    bot = GridBot(
        bot_id=1,
        client=mock_client,
        pair='BTC/USDT',
        lower=20000,
        upper=25000,
        grids=5,
        capital=1.0
    )
    
    bot.start()
    assert mock_client.create_order.call_count == 8  # (5-1) * 2 orders

def test_grid_bot_stop(mock_client):
    """Test grid bot stop."""
    bot = GridBot(
        bot_id=1,
        client=mock_client,
        pair='BTC/USDT',
        lower=20000,
        upper=25000,
        grids=5,
        capital=1.0
    )
    
    bot.stop()
    mock_client.cancel_all_orders.assert_called_once_with('BTC/USDT') 