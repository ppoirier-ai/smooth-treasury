import pytest
from unittest.mock import Mock, patch
from common.exchange.client import ExchangeClient

@pytest.fixture
def mock_ccxt():
    with patch('common.exchange.client.ccxt') as mock:
        yield mock

@pytest.fixture
def exchange_client(mock_ccxt):
    return ExchangeClient('test_key', 'test_secret')

def test_get_ticker(exchange_client, mock_ccxt):
    """Test ticker price retrieval."""
    # Setup mock
    mock_ccxt.binance.return_value.fetch_ticker.return_value = {'last': 20000.0}
    
    # Test successful case
    price = exchange_client.get_ticker('BTC/USDT')
    assert price == 20000.0
    
    # Test error case
    mock_ccxt.binance.return_value.fetch_ticker.side_effect = Exception('API error')
    price = exchange_client.get_ticker('BTC/USDT')
    assert price is None

def test_create_order(exchange_client, mock_ccxt):
    """Test order creation."""
    # Setup mock
    mock_order = {'id': '123', 'status': 'open'}
    mock_ccxt.binance.return_value.create_order.return_value = mock_order
    
    # Test successful case
    order = exchange_client.create_order(
        symbol='BTC/USDT',
        side='buy',
        amount=0.1,
        price=20000.0
    )
    assert order == mock_order
    
    # Test error case
    mock_ccxt.binance.return_value.create_order.side_effect = Exception('API error')
    order = exchange_client.create_order(
        symbol='BTC/USDT',
        side='buy',
        amount=0.1,
        price=20000.0
    )
    assert order is None 