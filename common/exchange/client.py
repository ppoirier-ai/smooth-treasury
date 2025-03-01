from typing import Optional, Dict, Any, List
from common.utils.logger import setup_logger
import time
import hmac
import hashlib
import requests
import urllib.parse
from urllib.parse import urlencode
import json

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
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        if not CCXT_AVAILABLE:
            raise ImportError("ccxt package is required for exchange functionality")
        
        options = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
                'adjustForTimeDifference': True,
            }
        }
        
        if testnet:
            # Update base URLs for testnet
            options.update({
                'urls': {
                    'api': {
                        'public': 'https://testnet.binance.vision/api/v3',
                        'private': 'https://testnet.binance.vision/api/v3',
                    },
                    'www': 'https://testnet.binance.vision',
                    'test': True
                },
                'options': {
                    'adjustForTimeDifference': True,
                    'recvWindow': 10000
                }
            })
        
        self.exchange = ccxt.binance(options)
        
        # Verify connection
        try:
            self.exchange.load_markets()
            logger.info(f"Connected to Binance {'testnet' if testnet else 'mainnet'}")
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {str(e)}")
            raise
    
    def get_ticker(self, symbol: str) -> Optional[float]:
        """Get current price for symbol."""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            logger.info(f"Current price for {symbol}: {ticker['last']}")
            return ticker['last']
        except Exception as e:
            logger.error(f"Failed to get ticker: {str(e)}")
            return None
    
    def create_order(self, symbol: str, side: str, amount: float, price: float) -> Optional[Dict[str, Any]]:
        """Create limit order."""
        try:
            order = self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side=side.lower(),  # Ensure side is lowercase as required by CCXT
                amount=amount,
                price=price
            )
            logger.info(f"Created {side} order for {symbol}: amount={amount}, price={price}")
            return order
        except Exception as e:
            logger.error(f"Failed to create order: {str(e)}")
            return None

    def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get all open orders for a symbol."""
        try:
            orders = self.exchange.fetch_open_orders(symbol=symbol)
            logger.info(f"Found {len(orders)} open orders for {symbol or 'all symbols'}")
            return orders
        except Exception as e:
            logger.error(f"Failed to get open orders: {str(e)}")
            return []

    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all open orders for a symbol."""
        try:
            # First get open orders
            open_orders = self.get_open_orders(symbol)
            
            # Cancel each order
            for order in open_orders:
                self.exchange.cancel_order(id=order['id'], symbol=symbol)
                logger.info(f"Cancelled order {order['id']} for {symbol}")
            
            logger.info(f"Cancelled {len(open_orders)} orders for {symbol}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel orders: {str(e)}")
            return False
    
    def get_account_balance(self, currency: str = None) -> Dict[str, float]:
        """Get account balance."""
        try:
            balances = self.exchange.fetch_balance()
            
            if currency:
                if currency in balances['free']:
                    logger.info(f"{currency} balance: {balances['free'][currency]}")
                    return {
                        'free': balances['free'][currency],
                        'used': balances['used'][currency],
                        'total': balances['total'][currency]
                    }
                else:
                    logger.warning(f"Currency {currency} not found in balance")
                    return {'free': 0.0, 'used': 0.0, 'total': 0.0}
            else:
                # Return all currencies with non-zero balance
                result = {}
                for curr, amount in balances['total'].items():
                    if amount > 0:
                        result[curr] = {
                            'free': balances['free'][curr],
                            'used': balances['used'][curr],
                            'total': amount
                        }
                logger.info(f"Account has {len(result)} currencies with non-zero balance")
                return result
        except Exception as e:
            logger.error(f"Failed to get account balance: {str(e)}")
            return {} 