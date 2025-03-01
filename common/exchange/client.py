from typing import Optional, Dict, Any
from common.utils.logger import setup_logger
import time
import random

logger = setup_logger(__name__)

try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    logger.warning("ccxt package not found. Exchange functionality will be limited.")
    CCXT_AVAILABLE = False

class ExchangeClient:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """Initialize exchange client.
        
        Args:
            api_key: API key
            api_secret: API secret
            testnet: If True, use testnet instead of mainnet
        """
        self.testnet = testnet
        
        if not CCXT_AVAILABLE:
            raise ImportError("ccxt package is required for exchange functionality")
        
        options = {
            'apiKey': api_key,
            'secret': api_secret,
        }
        
        if testnet:
            options.update({
                'urls': {
                    'api': 'https://testnet.binance.vision/api',
                }
            })
        
        self.exchange = ccxt.binance(options)
        
        # For testnet mock data
        self.mock_orders = {}
        self.next_order_id = 1000
    
    def get_ticker(self, symbol: str) -> Optional[float]:
        """Get current price for symbol."""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            logger.error(f"Failed to get ticker: {str(e)}")
            return None
    
    def create_order(self, symbol: str, side: str, amount: float, price: float) -> Optional[Dict[str, Any]]:
        """Create limit order."""
        try:
            if self.testnet:
                # In testnet, simulate order creation since sapi endpoints might not work
                order_id = f"test-{self.next_order_id}"
                self.next_order_id += 1
                
                order = {
                    'id': order_id,
                    'symbol': symbol,
                    'type': 'limit',
                    'side': side,
                    'amount': amount,
                    'price': price,
                    'status': 'open',
                    'timestamp': int(time.time() * 1000)
                }
                
                # Store the mock order
                self.mock_orders[order_id] = order
                logger.info(f"Created mock order in testnet: {order_id}")
                return order
            else:
                # Real order creation
                return self.exchange.create_order(
                    symbol=symbol,
                    type='limit',
                    side=side,
                    amount=amount,
                    price=price
                )
        except Exception as e:
            logger.error(f"Failed to create order: {str(e)}")
            return None

    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all open orders for a symbol."""
        try:
            if self.testnet:
                # In testnet, simulate cancellation
                cancelled = 0
                for order_id in list(self.mock_orders.keys()):
                    if self.mock_orders[order_id]['symbol'] == symbol:
                        self.mock_orders.pop(order_id)
                        cancelled += 1
                
                logger.info(f"Cancelled {cancelled} mock orders for {symbol}")
                return True
            else:
                # Real cancellation
                self.exchange.cancel_all_orders(symbol)
                return True
        except Exception as e:
            logger.error(f"Failed to cancel orders: {str(e)}")
            return False 