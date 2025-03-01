from typing import Optional, Dict, Any, List
from common.utils.logger import setup_logger
import time
import hmac
import hashlib
import requests
import json
import random

logger = setup_logger(__name__)

class FuturesExchangeClient:
    """Client for Binance Futures API."""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """Initialize Binance Futures client."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Debug log - Show partial API key for debugging
        logger.info(f"Using API key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")
        
        # Base URLs
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = "https://fapi.binance.com"
            
        # Test connection
        try:
            server_time = self._get_timestamp()
            logger.info(f"Connected to Binance Futures {'testnet' if testnet else 'mainnet'}")
        except Exception as e:
            logger.error(f"Failed to connect to Binance Futures: {str(e)}")
            raise
    
    def _get_timestamp(self) -> int:
        """Get server timestamp to avoid time sync issues."""
        url = f"{self.base_url}/fapi/v1/time"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()['serverTime']
        return int(time.time() * 1000)
    
    def _sign_request(self, params: Dict) -> tuple:
        """Sign request with API secret."""
        # Convert all values to strings
        params = {k: str(v) for k, v in params.items()}
        
        # Create query string
        query_string = '&'.join([f"{key}={params[key]}" for key in params])
        
        # Create signature
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return query_string, signature
    
    def get_ticker(self, symbol: str) -> Optional[float]:
        """Get current price for symbol."""
        # Convert symbol format from BTC/USDT to BTCUSDT
        formatted_symbol = symbol.replace('/', '')
        
        url = f"{self.base_url}/fapi/v1/ticker/price"
        params = {'symbol': formatted_symbol}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                price = float(data['price'])
                logger.info(f"Current price for {symbol}: {price}")
                return price
            else:
                logger.error(f"Failed to get ticker: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting ticker: {str(e)}")
            return None
    
    def create_order(self, symbol: str, side: str, amount: float, price: float) -> Optional[Dict[str, Any]]:
        """Create limit order."""
        # Convert symbol format
        formatted_symbol = symbol.replace('/', '')
        
        # Get server time for timestamp
        timestamp = self._get_timestamp()
        
        # Add client order ID to help track orders
        order_id = f"grid-{int(time.time())}-{random.randint(1000, 9999)}"
        
        # Prepare parameters
        params = {
            'symbol': formatted_symbol,
            'side': side.upper(),
            'type': 'LIMIT',
            'timeInForce': 'GTC',
            'quantity': str(amount),  # Convert to string
            'price': str(price),      # Convert to string
            'timestamp': str(timestamp),
            'recvWindow': '5000',
            'newClientOrderId': order_id
        }
        
        # Sign request
        query_string, signature = self._sign_request(params)
        url = f"{self.base_url}/fapi/v1/order?{query_string}&signature={signature}"
        
        # Prepare headers
        headers = {
            'X-MBX-APIKEY': self.api_key
        }
        
        # Debug output
        logger.debug(f"Placing order: URL={url}, Headers={headers}")
        
        try:
            response = requests.post(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Created {side} order: {data['orderId']}")
                return {
                    'id': str(data['orderId']),
                    'symbol': symbol,
                    'side': side.lower(),
                    'amount': float(data['origQty']),
                    'price': float(data['price']),
                    'status': data['status'].lower()
                }
            else:
                logger.error(f"Failed to create order: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return None

    def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get all open orders for a symbol."""
        # Get server time for timestamp
        timestamp = self._get_timestamp()
        
        # Prepare parameters
        params = {
            'timestamp': timestamp,
            'recvWindow': 5000
        }
        
        if symbol:
            # Convert symbol format
            formatted_symbol = symbol.replace('/', '')
            params['symbol'] = formatted_symbol
        
        # Sign request
        query_string, signature = self._sign_request(params)
        url = f"{self.base_url}/fapi/v1/openOrders?{query_string}&signature={signature}"
        
        # Prepare headers
        headers = {
            'X-MBX-APIKEY': self.api_key
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                orders = []
                for order in data:
                    # Convert BTCUSDT back to BTC/USDT format
                    symbol_with_slash = f"{order['symbol'][:-4]}/{order['symbol'][-4:]}"
                    orders.append({
                        'id': str(order['orderId']),
                        'symbol': symbol_with_slash,
                        'side': order['side'].lower(),
                        'amount': float(order['origQty']),
                        'price': float(order['price']),
                        'status': order['status'].lower()
                    })
                logger.info(f"Found {len(orders)} open orders")
                return orders
            else:
                logger.error(f"Failed to get open orders: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error getting open orders: {str(e)}")
            return []

    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all open orders for a symbol."""
        # Convert symbol format
        formatted_symbol = symbol.replace('/', '')
        
        # Get server time for timestamp
        timestamp = self._get_timestamp()
        
        # Prepare parameters
        params = {
            'symbol': formatted_symbol,
            'timestamp': timestamp,
            'recvWindow': 5000
        }
        
        # Sign request
        query_string, signature = self._sign_request(params)
        url = f"{self.base_url}/fapi/v1/allOpenOrders?{query_string}&signature={signature}"
        
        # Prepare headers
        headers = {
            'X-MBX-APIKEY': self.api_key
        }
        
        try:
            response = requests.delete(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Cancelled all orders for {symbol}")
                return True
            else:
                logger.error(f"Failed to cancel orders: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error cancelling orders: {str(e)}")
            return False
    
    def get_account_balance(self, currency: str = None) -> Dict[str, Any]:
        """Get account balance."""
        # Get server time for timestamp
        timestamp = self._get_timestamp()
        
        # Prepare parameters
        params = {
            'timestamp': timestamp,
            'recvWindow': 5000
        }
        
        # Sign request
        query_string, signature = self._sign_request(params)
        url = f"{self.base_url}/fapi/v2/balance?{query_string}&signature={signature}"
        
        # Prepare headers
        headers = {
            'X-MBX-APIKEY': self.api_key
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                result = {}
                
                for asset in data:
                    asset_name = asset['asset']
                    if float(asset['balance']) > 0 or currency == asset_name:
                        result[asset_name] = {
                            'free': float(asset['availableBalance']),
                            'used': float(asset['balance']) - float(asset['availableBalance']),
                            'total': float(asset['balance'])
                        }
                
                if currency:
                    if currency in result:
                        logger.info(f"{currency} balance: {result[currency]['free']}")
                        return result[currency]
                    else:
                        logger.warning(f"Currency {currency} not found in balance")
                        return {'free': 0.0, 'used': 0.0, 'total': 0.0}
                else:
                    logger.info(f"Account has {len(result)} currencies with non-zero balance")
                    return result
            else:
                logger.error(f"Failed to get account balance: {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Error getting account balance: {str(e)}")
            return {} 