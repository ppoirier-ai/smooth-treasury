import pytest
from unittest.mock import Mock
from common.bot.grid_bot import GridBot
from common.exchange.client import ExchangeClient
from datetime import datetime

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

def test_handle_order_fill(mock_client):
    """Test order fill handling."""
    bot = GridBot(
        bot_id=1,
        client=mock_client,
        pair='BTC/USDT',
        lower=20000,
        upper=25000,
        grids=5,
        capital=1.0
    )
    
    # Add a test order
    test_order = {
        'side': 'buy',
        'price': 20000,
        'amount': 0.1,
        'order_id': '123',
        'status': 'open',
        'timestamp': datetime.now()
    }
    bot.active_orders['123'] = test_order
    
    # Setup mock for new order
    mock_client.create_order.return_value = {
        'id': '456',
        'status': 'open'
    }
    
    # Test order fill
    bot.handle_order_fill('123', 19900, 0.1)
    
    # Check that original order was moved to filled_orders
    assert '123' not in bot.active_orders
    assert len(bot.filled_orders) == 1
    assert bot.filled_orders[0]['order_id'] == '123'
    
    # Check that new order was created
    assert '456' in bot.active_orders
    assert bot.active_orders['456']['side'] == 'sell'
    mock_client.create_order.assert_called_once()

def test_calculate_profit(mock_client):
    """Test profit calculation."""
    bot = GridBot(
        bot_id=1,
        client=mock_client,
        pair='BTC/USDT',
        lower=20000,
        upper=25000,
        grids=5,
        capital=1.0
    )
    
    # Add some test filled orders
    bot.filled_orders = [
        {
            'side': 'buy',
            'price': 20000,
            'amount': 0.1,
            'fill_price': 19900,
            'fill_amount': 0.1
        },
        {
            'side': 'sell',
            'price': 21000,
            'amount': 0.1,
            'fill_price': 21100,
            'fill_amount': 0.1
        }
    ]
    
    profit = bot.calculate_profit()
    # Buy profit: (20000 - 19900) * 0.1 = 10
    # Sell profit: (21100 - 21000) * 0.1 = 10
    # Total profit = 20
    assert profit == 20.0 