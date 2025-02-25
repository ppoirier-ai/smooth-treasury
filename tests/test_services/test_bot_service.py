import pytest
from unittest.mock import Mock, patch
from common.services.bot_service import BotService
from common.database.models import Bot, Client, Trade
from common.exchange.client import ExchangeClient
from common.bot.grid_bot import GridBot

@pytest.fixture
def mock_exchange():
    with patch('common.services.bot_service.ExchangeClient') as mock:
        mock.return_value = Mock(spec=ExchangeClient)
        yield mock

@pytest.fixture
def mock_grid_bot():
    with patch('common.services.bot_service.GridBot') as mock:
        mock.return_value = Mock(spec=GridBot)
        yield mock

@pytest.fixture
def bot_service():
    return BotService()

def test_start_bot(bot_service, mock_exchange, mock_grid_bot):
    """Test starting a bot."""
    # Create test data
    client = Client(client_id=1, api_key='test', api_secret='test')
    bot = Bot(
        bot_id=1,
        client_id=1,
        pair='BTC/USDT',
        status='configured',
        lower_price=20000,
        upper_price=25000,
        grids=5,
        capital_btc=1.0
    )
    
    # Test successful start
    assert bot_service.start_bot(bot, client)
    assert 1 in bot_service.active_bots
    mock_grid_bot.return_value.start.assert_called_once()
    
    # Test error handling
    mock_exchange.side_effect = Exception('API error')
    assert not bot_service.start_bot(bot, client)

def test_stop_bot(bot_service, mock_exchange, mock_grid_bot):
    """Test stopping a bot."""
    # Create and start a bot first
    client = Client(client_id=1, api_key='test', api_secret='test')
    bot = Bot(
        bot_id=1,
        client_id=1,
        pair='BTC/USDT',
        status='configured',
        lower_price=20000,
        upper_price=25000,
        grids=5,
        capital_btc=1.0
    )
    bot_service.start_bot(bot, client)
    
    # Test successful stop
    assert bot_service.stop_bot(1)
    assert 1 not in bot_service.active_bots
    mock_grid_bot.return_value.stop.assert_called_once()
    
    # Test stopping non-existent bot
    assert not bot_service.stop_bot(999)

def test_handle_order_fill(bot_service, mock_exchange, mock_grid_bot, test_session):
    """Test order fill handling."""
    # Create test data
    client = Client(client_id=1, api_key='test', api_secret='test')
    bot = Bot(
        bot_id=1,
        client_id=1,
        pair='BTC/USDT',
        status='configured',
        lower_price=20000,
        upper_price=25000,
        grids=5,
        capital_btc=1.0
    )
    
    # Start bot first
    bot_service.start_bot(bot, client)
    
    # Setup mock for profit calculation
    mock_grid_bot.return_value.calculate_profit.return_value = 0.001
    
    # Test successful order fill
    assert bot_service.handle_order_fill(1, 'test_order', 20100.0, 0.1, test_session)
    
    # Verify trade was recorded
    trade = test_session.query(Trade).filter_by(bot_id=1).first()
    assert trade is not None
    assert trade.amount_btc == 0.1
    assert trade.profit_btc == 0.001
    
    # Test handling fill for non-existent bot
    assert not bot_service.handle_order_fill(999, 'test_order', 20100.0, 0.1, test_session) 