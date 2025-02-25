from typing import Optional
from common.utils.logger import setup_logger

logger = setup_logger(__name__)

try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    logger.warning("ccxt package not found. Exchange functionality will be limited.")
    CCXT_AVAILABLE = False

class ExchangeClient:
    def __init__(self, api_key: str, api_secret: str):
        if not CCXT_AVAILABLE:
            raise ImportError("ccxt package is required for exchange functionality")
        
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True
        })
    
    def get_ticker(self, symbol: str) -> Optional[float]:
        """Get current price for symbol."""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            logger.error(f"Failed to get ticker: {str(e)}")
            return None
    
    def create_order(self, symbol: str, side: str, amount: float, price: float):
        """Create limit order."""
        try:
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
            self.exchange.cancel_all_orders(symbol)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel orders: {str(e)}")
            return False 