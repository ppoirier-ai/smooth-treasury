from typing import Dict, Any, Optional, List
import time
import hmac
import hashlib
import json
import requests
import uuid
from urllib.parse import urlencode

from common.exchange.base_client import BaseExchangeClient
from common.utils.logger import setup_logger

logger = setup_logger(__name__)

class BybitClient(BaseExchangeClient):
    """Bybit exchange client implementation."""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """Initialize the Bybit client.
        
        Args:
            api_key: API key
            api_secret: API secret
            testnet: Whether to use testnet
        """
        # Call the parent constructor with the API credentials
        super().__init__(api_key=api_key, api_secret=api_secret)
        
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Bybit API URLs
        self.base_url = "https://api-testnet.bybit.com" if testnet else "https://api.bybit.com"
        
        # Configure for unified account
        self.account_type = "UNIFIED"  # Unified account
        
        # Sync time with server
        self._sync_time()
        
        # Initialize connection by fetching available symbols for both linear and inverse futures
        self.available_pairs = {}
        self.categories = ["linear", "inverse"]
        
        for category in self.categories:
            try:
                response = self._get_public("/v5/market/instruments-info", {"category": category})
                
                if response and "result" in response and "list" in response["result"]:
                    self.available_pairs[category] = [item["symbol"] for item in response["result"]["list"]]
                    logger.info(f"Found {len(self.available_pairs[category])} available trading pairs in {category} category")
                else:
                    logger.error(f"Failed to fetch available symbols for {category}")
                    self.available_pairs[category] = []
            except Exception as e:
                logger.error(f"Failed to fetch {category} symbols: {str(e)}")
                self.available_pairs[category] = []
        
        logger.info(f"Connected to Bybit {'testnet' if testnet else 'mainnet'} with unified account")
    
    def _sync_time(self):
        """Synchronize local time with Bybit server time."""
        try:
            response = self._get_public("/v5/market/time")
            if response and "result" in response and "timeSecond" in response["result"]:
                server_time = int(response["result"]["timeSecond"]) * 1000
                local_time = int(time.time() * 1000)
                time_diff = local_time - server_time
                
                if abs(time_diff) > 1000:  # If difference is more than 1 second
                    logger.warning(f"Time difference between local and server: {time_diff}ms")
                    # Store the offset to adjust future timestamps
                    self.time_offset = time_diff
                    return True
                else:
                    logger.info("Time is already synchronized with server")
                    self.time_offset = 0
                    return True
            else:
                logger.error("Failed to get server time")
                return False
        except Exception as e:
            logger.error(f"Error syncing time: {str(e)}")
            return False
    
    def _get_timestamp(self) -> int:
        """Get current timestamp in milliseconds directly from server if possible."""
        try:
            response = self._get_public("/v5/market/time")
            if response and "result" in response and "timeSecond" in response["result"]:
                return int(response["result"]["timeSecond"]) * 1000
        except:
            pass
        
        # Fallback to local time with offset
        if hasattr(self, 'time_offset'):
            return int(time.time() * 1000) - self.time_offset
        
        return int(time.time() * 1000)
    
    def _generate_signature(self, params_str: str) -> str:
        """Generate signature for API request."""
        signature = hmac.new(
            bytes(self.api_secret, "utf-8"),
            bytes(params_str, "utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_public(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a public GET request to Bybit API."""
        url = f"{self.base_url}{endpoint}"
        if params:
            url += f"?{urlencode(params)}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error in public request to {endpoint}: {str(e)}")
            return {}
    
    def _get_private(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a private GET request to Bybit API."""
        timestamp = str(self._get_timestamp())
        recv_window = "5000"
        params = params or {}
        
        # For GET requests with query parameters, we need to include them in the signature
        # First, create the query string for the URL
        query_string = ""
        if params:
            # Sort parameters alphabetically and create the query string
            sorted_params = dict(sorted(params.items()))
            query_string = "&".join([f"{k}={v}" for k, v in sorted_params.items()])
        
        # Create signature using timestamp + api_key + recv_window + query (if any)
        param_str = timestamp + self.api_key + recv_window
        if query_string:
            param_str += query_string
        
        # Generate signature
        signature = hmac.new(
            bytes(self.api_secret, "utf-8"),
            bytes(param_str, "utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        # Set headers
        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window
        }
        
        # Construct the URL with query parameters if any
        url = f"{self.base_url}{endpoint}"
        if query_string:
            url += f"?{query_string}"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error in private GET request to {endpoint}: {str(e)}")
            return {}
    
    def _post_private(self, endpoint: str, data: Dict = None) -> Dict:
        """Make a private POST request to Bybit API."""
        timestamp = str(self._get_timestamp())
        recv_window = "5000"
        data = data or {}
        
        # For POST requests, create signature using timestamp + api_key + recv_window + json_body
        json_body = json.dumps(data)
        param_str = timestamp + self.api_key + recv_window + json_body
        
        # Generate signature
        signature = hmac.new(
            bytes(self.api_secret, "utf-8"),
            bytes(param_str, "utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        # Set headers
        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window,
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error in private POST request to {endpoint}: {str(e)}")
            return {}
    
    def _detect_symbol_category(self, symbol: str) -> str:
        """Detect whether a symbol belongs to linear or inverse category."""
        normalized = self._normalize_symbol(symbol)
        
        # Check in inverse first (since we're focusing on BTCUSD)
        if normalized in self.available_pairs.get("inverse", []):
            return "inverse"
        # Then check in linear
        elif normalized in self.available_pairs.get("linear", []):
            return "linear"
        # Default to inverse for BTCUSD
        elif normalized == "BTCUSD":
            return "inverse"
        # Default to linear for other
        else:
            return "linear"
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for Bybit API."""
        if '/' in symbol:
            base, quote = symbol.split('/')
            return f"{base}{quote}"
        return symbol
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current ticker for a symbol."""
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            category = self._detect_symbol_category(symbol)
            
            params = {
                "category": category,
                "symbol": normalized_symbol
            }
            
            response = self._get_public("/v5/market/tickers", params)
            
            if response and "result" in response and "list" in response["result"] and len(response["result"]["list"]) > 0:
                ticker_data = response["result"]["list"][0]
                
                return {
                    "symbol": symbol,
                    "bid": float(ticker_data.get("bid1Price", 0)),
                    "ask": float(ticker_data.get("ask1Price", 0)),
                    "last": float(ticker_data.get("lastPrice", 0)),
                    "info": ticker_data
                }
            else:
                logger.warning(f"No ticker data found for {symbol} in {category} category")
                return {}
        except Exception as e:
            logger.error(f"Error getting ticker: {str(e)}")
            return {}
    
    def get_orderbook(self, symbol: str) -> Dict[str, Any]:
        """Get orderbook for a symbol."""
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            category = self._detect_symbol_category(symbol)
            
            params = {
                "category": category,
                "symbol": normalized_symbol,
                "limit": 50  # Number of price levels to include
            }
            
            response = self._get_public("/v5/market/orderbook", params)
            
            if response and "result" in response and "b" in response["result"] and "a" in response["result"]:
                bids = [[float(price), float(qty)] for price, qty in response["result"]["b"]]
                asks = [[float(price), float(qty)] for price, qty in response["result"]["a"]]
                
                return {
                    "symbol": symbol,
                    "bids": bids,
                    "asks": asks,
                    "timestamp": response["result"].get("ts", 0),
                    "datetime": None
                }
            else:
                logger.warning(f"No orderbook data found for {symbol} in {category} category")
                return {"bids": [], "asks": []}
        except Exception as e:
            logger.error(f"Error getting orderbook: {str(e)}")
            return {"bids": [], "asks": []}
    
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for a symbol."""
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            category = self._detect_symbol_category(symbol)
            
            data = {
                "category": category,
                "symbol": normalized_symbol,
                "buyLeverage": str(leverage),
                "sellLeverage": str(leverage)
            }
            
            response = self._post_private("/v5/position/set-leverage", data)
            
            if response and "retCode" in response and response["retCode"] == 0:
                logger.info(f"Successfully set leverage for {symbol} to {leverage}x")
                return True
            else:
                error_msg = response.get("retMsg", "Unknown error") if response else "No response"
                logger.error(f"Failed to set leverage: {error_msg}")
                return False
        except Exception as e:
            logger.error(f"Error setting leverage: {str(e)}")
            return False
    
    def get_account_balance(self, currency: str = "USDT") -> Dict[str, Any]:
        """Get account balance."""
        try:
            params = {
                "accountType": self.account_type
            }
            
            if currency:
                params["coin"] = currency
            
            response = self._get_private("/v5/account/wallet-balance", params)
            
            if response and "result" in response and "list" in response["result"] and len(response["result"]["list"]) > 0:
                for account in response["result"]["list"]:
                    if "coin" in account and len(account["coin"]) > 0:
                        for coin_data in account["coin"]:
                            if not currency or coin_data["coin"] == currency:
                                return {
                                    "free": float(coin_data.get("availableToWithdraw", 0)),
                                    "used": float(coin_data.get("walletBalance", 0)) - float(coin_data.get("availableToWithdraw", 0)),
                                    "total": float(coin_data.get("walletBalance", 0))
                                }
                
                logger.warning(f"No balance data found for {currency}")
                return {"free": 0.0, "used": 0.0, "total": 0.0}
            else:
                logger.warning("No balance data found")
                return {"free": 0.0, "used": 0.0, "total": 0.0}
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            return {}
    
    def create_order(self, symbol: str, side: str, amount: float, price: float) -> Optional[Dict]:
        """Create a new order."""
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            category = self._detect_symbol_category(symbol)
            
            # Generate client order ID
            client_order_id = f"bot_{uuid.uuid4().hex[:16]}"
            
            data = {
                "category": category,
                "symbol": normalized_symbol,
                "side": side.upper(),
                "orderType": "Limit",
                "qty": str(amount),
                "price": str(price),
                "timeInForce": "PostOnly",
                "orderLinkId": client_order_id
            }
            
            response = self._post_private("/v5/order/create", data)
            
            if response and "retCode" in response and response["retCode"] == 0 and "result" in response:
                order_data = response["result"]
                return {
                    "id": order_data.get("orderId", ""),
                    "symbol": symbol,
                    "side": side,
                    "amount": amount,
                    "price": price,
                    "status": "new",
                    "info": order_data
                }
            else:
                error_msg = response.get("retMsg", "Unknown error") if response else "No response"
                logger.error(f"Failed to create order: {error_msg}")
                return None
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return None
    
    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all orders for a symbol."""
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            category = self._detect_symbol_category(symbol)
            
            data = {
                "category": category,
                "symbol": normalized_symbol
            }
            
            response = self._post_private("/v5/order/cancel-all", data)
            
            if response and "retCode" in response and response["retCode"] == 0:
                logger.info(f"Successfully cancelled all orders for {symbol}")
                return True
            else:
                error_msg = response.get("retMsg", "Unknown error") if response else "No response"
                logger.error(f"Failed to cancel orders: {error_msg}")
                return False
        except Exception as e:
            logger.error(f"Error cancelling orders: {str(e)}")
            return False
    
    def get_open_orders(self, symbol: str) -> list:
        """Get all open orders for a symbol."""
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            category = self._detect_symbol_category(symbol)
            
            params = {
                "category": category,
                "symbol": normalized_symbol
            }
            
            response = self._get_private("/v5/order/realtime", params)
            
            if response and "result" in response and "list" in response["result"]:
                orders = []
                for order_data in response["result"]["list"]:
                    orders.append({
                        "id": order_data.get("orderId", ""),
                        "symbol": symbol,
                        "side": order_data.get("side", "").lower(),
                        "amount": float(order_data.get("qty", 0)),
                        "price": float(order_data.get("price", 0)),
                        "status": order_data.get("orderStatus", "").lower(),
                        "info": order_data
                    })
                return orders
            else:
                logger.warning(f"No open orders found for {symbol}")
                return []
        except Exception as e:
            logger.error(f"Error getting open orders: {str(e)}")
            return []
    
    def get_positions(self, symbol: str = None) -> list:
        """Get current positions."""
        try:
            params = {}
            
            if symbol:
                normalized_symbol = self._normalize_symbol(symbol)
                category = self._detect_symbol_category(symbol)
                params["category"] = category
                params["symbol"] = normalized_symbol
            
            response = self._get_private("/v5/position/list", params)
            
            if response and "result" in response and "list" in response["result"]:
                positions = []
                for position_data in response["result"]["list"]:
                    if float(position_data.get("size", 0)) > 0:
                        positions.append({
                            "symbol": position_data.get("symbol", ""),
                            "side": "long" if position_data.get("side", "") == "Buy" else "short",
                            "amount": float(position_data.get("size", 0)),
                            "entry_price": float(position_data.get("avgPrice", 0)),
                            "unrealized_pnl": float(position_data.get("unrealisedPnl", 0)),
                            "leverage": float(position_data.get("leverage", 0)),
                            "info": position_data
                        })
                return positions
            else:
                logger.warning("No positions found")
                return []
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return [] 