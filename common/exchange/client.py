from typing import Optional
import ccxt

class ExchangeClient:
    def __init__(self, api_key: str, api_secret: str):
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