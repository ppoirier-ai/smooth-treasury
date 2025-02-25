import pytest
from unittest.mock import Mock, patch
from common.bot.price_monitor import PriceMonitor
import time

@pytest.fixture
def mock_exchange():
    with patch('common.bot.price_monitor.ExchangeClient') as mock:
        mock.return_value = Mock()
        yield mock.return_value

def test_price_monitor_add_symbol():
    """Test adding symbols to monitor."""
    monitor = PriceMonitor()
    callback = lambda symbol, price: None
    
    monitor.add_symbol('BTC/USDT', callback)
    assert 'BTC/USDT' in monitor.symbols
    assert callback in monitor.callbacks['BTC/USDT']

def test_price_monitor_remove_symbol():
    """Test removing symbols from monitor."""
    monitor = PriceMonitor()
    monitor.add_symbol('BTC/USDT')
    monitor.remove_symbol('BTC/USDT')
    assert 'BTC/USDT' not in monitor.symbols
    assert 'BTC/USDT' not in monitor.callbacks

def test_price_monitor_updates(mock_exchange):
    """Test price updates."""
    monitor = PriceMonitor(update_interval=0.1)
    
    # Setup mock prices
    prices = [20000.0, 20100.0, 20200.0]
    mock_exchange.get_ticker.side_effect = prices
    
    # Setup callback
    received_prices = []
    def callback(symbol: str, price: float):
        received_prices.append(price)
    
    # Run monitor
    monitor.add_symbol('BTC/USDT', callback)
    monitor.start()
    time.sleep(0.35)  # Wait for 3 updates
    monitor.stop()
    
    assert len(received_prices) == 3
    assert received_prices == prices 