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
from common.utils.symbol_info import get_symbol_info

logger = setup_logger(__name__)

class BybitClient(BaseExchangeClient):
    """Bybit exchange client implementation."""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """Initialize Bybit client with API credentials."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.base_url = "https://api-testnet.bybit.com" if testnet else "https://api.bybit.com"
        
        # For time synchronization
        self.time_offset = 0
        self.sync_time()  # Sync time on initialization
        
        # Configure for unified account
        self.account_type = "UNIFIED"  # Unified account
        
        # Debug log - Show partial API key for debugging
        masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "****"
        logger.info(f"Initializing Bybit client with API key: {masked_key}")
        
        # Initialize available trading pairs
        self.available_pairs = {}
        self._get_available_trading_pairs()
        
        # Try to check connection - but continue even if it fails
        try:
            self._check_connection()
        except Exception as e:
            logger.error(f"Connection check failed: {str(e)}")
        
        logger.info(f"Connected to Bybit {'testnet' if testnet else 'mainnet'} with unified account")
    
    def sync_time(self):
        """Synchronize local time with Bybit server time."""
        try:
            server_time = self._get_server_time()
            local_time = int(time.time() * 1000)
            self.time_offset = server_time - local_time
            logger.info(f"Time offset between local and server: {self.time_offset}ms")
        except Exception as e:
            logger.error(f"Failed to sync time: {str(e)}")
    
    def _get_server_time(self):
        """Get Bybit server time."""
        try:
            response = requests.get(f"{self.base_url}/v5/market/time")
            if response.status_code == 200:
                result = response.json()
                if "result" in result and "timeSecond" in result["result"]:
                    return int(result["result"]["timeSecond"]) * 1000
            raise Exception("Failed to get server time")
        except Exception as e:
            logger.error(f"Error getting server time: {str(e)}")
            return int(time.time() * 1000)  # Fallback to local time
    
    def _get_timestamp(self):
        """Get current timestamp adjusted for server time offset."""
        return int(time.time() * 1000) + self.time_offset
    
    def _check_time_sync(self):
        """Check if local time is synchronized with server time."""
        try:
            response = self._get_public("/v5/market/time")
            if response and "result" in response and "timeSecond" in response["result"]:
                server_time = int(response["result"]["timeSecond"]) * 1000
                local_time = int(time.time() * 1000)
                diff = abs(local_time - server_time)
                
                if diff > 10000:  # If difference is more than 10 seconds
                    logger.warning(f"Time difference between local and server: {diff}ms")
                    # We'll continue anyway, as the timestamp will be generated at request time
                return diff
        except Exception as e:
            logger.error(f"Error checking time sync: {str(e)}")
            return None
    
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
        try:
            # Use the corrected timestamp
            timestamp = str(self._get_timestamp())
            recv_window = "20000"
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
                self.api_secret.encode("utf-8"),
                param_str.encode("utf-8"),
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
            
            # Debug logs
            logger.info(f"API Request: GET {url}")
            logger.info(f"Request Headers: {headers}")
            
            response = requests.get(url, headers=headers)
            
            # Debug log response
            logger.info(f"API Response Status: {response.status_code}")
            logger.info(f"API Response Content: {response.text}")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Error in private GET request to {endpoint}: {str(e)}")
            return {}
    
    def _post_private(self, endpoint, data=None):
        """Make a POST request to a private API endpoint."""
        try:
            url = f"{self.base_url}{endpoint}"
            
            # Generate signature with adjusted timestamp
            timestamp = self._get_timestamp()
            recv_window = 20000
            
            param_str = ""
            if data:
                param_str = json.dumps(data)
            
            signature_payload = f"{timestamp}{self.api_key}{recv_window}{param_str}"
            signature = hmac.new(
                self.api_secret.encode("utf-8"),
                signature_payload.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            
            # Headers with corrected timestamp
            headers = {
                "X-BAPI-API-KEY": self.api_key,
                "X-BAPI-TIMESTAMP": str(timestamp),
                "X-BAPI-RECV-WINDOW": str(recv_window),
                "X-BAPI-SIGN": signature,
                "Content-Type": "application/json"
            }
            
            # Debug log request details
            logger.info(f"API Request: POST {url}")
            logger.info(f"Request Headers: {headers}")
            logger.info(f"Request Data: {data}")
            
            # Make request
            response = requests.post(url, headers=headers, json=data)
            
            # Debug log response
            logger.info(f"API Response Status: {response.status_code}")
            logger.info(f"API Response Content: {response.text}")
            
            # Parse response
            if response.status_code == 200:
                result = response.json()
                if result and "retCode" in result and result["retCode"] == 0:
                    return result
                else:
                    error_msg = result.get("retMsg", "Unknown error") if result else "No response"
                    logger.error(f"API error: {error_msg}")
                    return result  # Return the result even with error for debugging
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"Error in _post_private: {str(e)}")
            return None
    
    def _get_available_trading_pairs(self):
        """Fetch available trading pairs from Bybit."""
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
    
    def _detect_symbol_category(self, symbol):
        """Detect the symbol category (linear, inverse, spot, etc.)."""
        # Remove any suffix like ':inverse'
        base_symbol = symbol.split(':')[0]
        
        # Normalize the symbol to exchange format
        normalized = self._normalize_symbol(base_symbol)
        
        # First check if it's explicitly provided
        if ':inverse' in symbol:
            return "inverse"
        
        # Try to determine from available symbols
        if normalized in self.available_pairs.get("inverse", []):
            return "inverse"
        elif normalized in self.available_pairs.get("linear", []):
            return "linear"
        
        # Special cases
        if normalized == "BTCUSD" or normalized.endswith("USD"):
            return "inverse"
        if normalized.endswith("USDT"):
            return "linear"
        
        # Default to linear if we can't determine
        logger.warning(f"Could not determine category for {symbol}, using linear")
        return "linear"
    
    def _normalize_symbol(self, symbol):
        """Normalize symbol name for Bybit API."""
        # Handle special suffixes
        if ':' in symbol:
            symbol = symbol.split(':')[0]
        
        # Handle standard format with /
        if '/' in symbol:
            parts = symbol.split('/')
            return f"{parts[0]}{parts[1]}"
        
        # Already normalized (e.g., BTCUSD)
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
    
    def get_account_balance(self, currency: str = None) -> Dict:
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
                                # Safely convert values with handling for empty strings
                                available = coin_data.get("availableToWithdraw", "0")
                                available = float(available) if available else 0.0
                                
                                wallet_balance = coin_data.get("walletBalance", "0")
                                wallet_balance = float(wallet_balance) if wallet_balance else 0.0
                                
                                return {
                                    "free": available,
                                    "used": wallet_balance - available,
                                    "total": wallet_balance
                                }
                
                logger.warning(f"No balance data found for {currency}")
                return {"free": 0.0, "used": 0.0, "total": 0.0}
            else:
                logger.warning("No balance data found")
                return {"free": 0.0, "used": 0.0, "total": 0.0}
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            return {"free": 0.0, "used": 0.0, "total": 0.0}  # Return empty balance rather than empty dict
    
    def create_order(self, symbol: str, side: str, amount: float, price: float) -> Optional[Dict]:
        """Create a new limit order."""
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            category = self._detect_symbol_category(symbol)
            
            # Convert side to proper format for Bybit (first letter uppercase)
            bybit_side = side.capitalize()  # Convert 'buy' -> 'Buy', 'sell' -> 'Sell'
            
            # Create order data
            data = {
                "category": category,
                "symbol": normalized_symbol,
                "side": bybit_side,  # Use properly formatted side
                "orderType": "Limit",
                "price": str(price),
                "qty": str(amount)
            }
            
            response = self._post_private("/v5/order/create", data)
            
            if response and "result" in response and "orderId" in response["result"]:
                return {
                    "id": response["result"]["orderId"],
                    "symbol": symbol,
                    "side": side.lower(),  # Keep consistent lowercase for our code
                    "price": price,
                    "amount": amount,
                    "status": "open",
                    "info": response["result"]
                }
            else:
                error_msg = response.get("retMsg", "Unknown error") if response else "No response"
                logger.error(f"Failed to create order: {error_msg}")
                return None
        except Exception as e:
            logger.error(f"Failed to create order: {str(e)}")
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
                        "amount": self._safe_float(order_data.get("qty", 0)),
                        "price": self._safe_float(order_data.get("price", 0)),
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
                    size = self._safe_float(position_data.get("size", 0))
                    if size > 0:
                        positions.append({
                            "symbol": position_data.get("symbol", ""),
                            "side": "long" if position_data.get("side", "") == "Buy" else "short",
                            "amount": size,
                            "entry_price": self._safe_float(position_data.get("avgPrice", 0)),
                            "unrealized_pnl": self._safe_float(position_data.get("unrealisedPnl", 0)),
                            "leverage": self._safe_float(position_data.get("leverage", 0)),
                            "info": position_data
                        })
                return positions
            else:
                logger.warning("No positions found")
                return []
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return []
    
    def _safe_float(self, value, default=0.0):
        """Safely convert a value to float."""
        if value is None or value == '':
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"Could not convert value to float: {value}, using default {default}")
            return default
    
    def cancel_order(self, symbol: str, order_id: str) -> Optional[Dict]:
        """Cancel a specific order by ID."""
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            category = self._detect_symbol_category(symbol)
            
            data = {
                "category": category,
                "symbol": normalized_symbol,
                "orderId": order_id
            }
            
            response = self._post_private("/v5/order/cancel", data)
            
            if response and "retCode" in response and response["retCode"] == 0:
                logger.info(f"Successfully cancelled order: {order_id}")
                return {
                    "id": order_id,
                    "symbol": symbol,
                    "status": "cancelled",
                    "info": response["result"]
                }
            else:
                error_msg = response.get("retMsg", "Unknown error") if response else "No response"
                logger.error(f"Failed to cancel order: {error_msg}")
                return None
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return None
    
    def create_market_order(self, symbol: str, side: str, amount: float) -> Optional[Dict]:
        """Create a new market order."""
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            category = self._detect_symbol_category(symbol)
            
            # Convert side to proper format for Bybit
            bybit_side = side.capitalize()  # Convert 'buy' -> 'Buy', 'sell' -> 'Sell'
            
            # Create order data
            data = {
                "category": category,
                "symbol": normalized_symbol,
                "side": bybit_side,
                "orderType": "Market",
                "qty": str(amount)
            }
            
            response = self._post_private("/v5/order/create", data)
            
            if response and "result" in response and "orderId" in response["result"]:
                logger.info(f"Market order placed: {response['result']['orderId']}")
                return {
                    "id": response["result"]["orderId"],
                    "symbol": symbol,
                    "side": side.lower(),
                    "amount": amount,
                    "status": "filled",  # Market orders are usually filled immediately
                    "info": response["result"]
                }
            else:
                error_msg = response.get("retMsg", "Unknown error") if response else "No response"
                logger.error(f"Failed to create market order: {error_msg}")
                return None
        except Exception as e:
            logger.error(f"Failed to create market order: {str(e)}")
            return None
    
    def set_position_mode(self, mode, symbol=None):
        """Set position mode for the account or specific symbol.
        
        Args:
            mode (str): 'one_way' or 'hedge'
            symbol (str, optional): Symbol to set mode for
        """
        try:
            mode_param = 0 if mode == 'one_way' else 3  # Bybit uses 0 for one-way, 3 for hedge
            
            params = {
                "category": self.get_market_type(symbol) if symbol else "linear",
                "mode": mode_param
            }
            
            if symbol:
                params["symbol"] = symbol
            
            response = self._post_private("/v5/position/switch-mode", params)
            
            if response and response.get("retCode") == 0:
                logger.info(f"Successfully set position mode to {mode}")
                return True
            else:
                error_msg = response.get("retMsg", "Unknown error") if response else "No response"
                logger.warning(f"Failed to set position mode: {error_msg}")
                return False
        
        except Exception as e:
            logger.error(f"Error setting position mode: {str(e)}")
            return False
    
    def get_market_type(self, symbol):
        """Determine market type for a symbol (linear, inverse, etc)."""
        if symbol and "USD" in symbol and not symbol.endswith("USDT"):
            return "inverse"
        else:
            return "linear"
    
    def create_limit_order(self, symbol: str, side: str, amount: float, price: float, params=None) -> Optional[str]:
        """Create a new limit order.
        
        Args:
            symbol: Trading pair symbol
            side: Order side ('buy' or 'sell')
            amount: Order amount
            price: Order price
            params: Additional parameters
            
        Returns:
            Order ID if successful, None otherwise
        """
        try:
            logger.info(f"Attempting to create limit order: {symbol} {side} {amount} @ {price}")
            
            # Debug logs for request details
            symbol_info = get_symbol_info(self, symbol)
            logger.info(f"Symbol info for order: {symbol_info}")
            
            # Format symbol for Bybit (remove '/' if present)
            formatted_symbol = symbol.replace('/', '')
            
            # Convert and validate amount and price according to exchange rules
            from common.utils.symbol_info import adjust_quantity, adjust_price
            adjusted_amount = adjust_quantity(amount, symbol_info)
            adjusted_price = adjust_price(price, symbol_info)
            
            logger.info(f"Adjusted order: {formatted_symbol} {side} {adjusted_amount} @ {adjusted_price}")
            
            # Direct API call for debugging
            order_id = self._create_order(
                symbol=formatted_symbol,
                side=side,
                order_type="Limit",
                qty=adjusted_amount,
                price=adjusted_price,
                time_in_force="GoodTillCancel"
            )
            
            if order_id:
                logger.info(f"Order created successfully: {order_id}")
            else:
                logger.error("Order creation failed - no order ID returned")
            
            return order_id
        
        except Exception as e:
            logger.error(f"Error creating limit order: {str(e)}")
            return None
    
    def _create_order(self, symbol, side, order_type, qty, price=None, time_in_force="GoodTillCancel"):
        """Create a new order with simplified interface."""
        try:
            logger.info(f"Creating order: {symbol} {side} {order_type} {qty} @ {price}")
            
            # Validate inputs
            if not symbol or not side or not order_type or not qty:
                logger.error("Missing required parameters for order creation")
                return None
            
            # Normalize the symbol
            symbol = symbol.replace('/', '')
            
            # Normalize side
            bybit_side = side.capitalize()  # Buy or Sell
            
            # Detect category (linear, inverse, etc.)
            if symbol.endswith('USD'):
                category = 'inverse'
            elif symbol.endswith('USDT'):
                category = 'linear'
            else:
                category = 'spot'
            
            logger.info(f"Order category: {category}")
            
            # Create order data
            data = {
                "category": category,
                "symbol": symbol,
                "side": bybit_side,
                "orderType": order_type,
                "qty": str(qty)
            }
            
            # Add price for limit orders
            if price is not None:
                data["price"] = str(price)
            
            # Add time in force
            data["timeInForce"] = time_in_force
            
            # Make the API request
            logger.info(f"Sending order request to Bybit: {data}")
            response = self._post_private("/v5/order/create", data)
            
            if response:
                logger.info(f"Full API response: {response}")
                
            if response and "result" in response and "orderId" in response["result"]:
                order_id = response["result"]["orderId"]
                logger.info(f"Order created successfully: {order_id}")
                return order_id
            else:
                error_msg = "Unknown error"
                if response:
                    if "retMsg" in response:
                        error_msg = response["retMsg"]
                    elif "ret_msg" in response:
                        error_msg = response["ret_msg"]
                
                logger.error(f"Failed to create order: {error_msg}")
                return None
            
        except Exception as e:
            logger.error(f"Error in _create_order: {str(e)}")
            logger.exception("Full traceback:")
            return None
    
    def _check_connection(self):
        """Check connection to Bybit and verify account type."""
        try:
            # Test API connectivity with a simple account info request
            response = self._get_private("/v5/account/info")
            
            if response and "result" in response:
                # Check if the account is unified margin
                account_type = response["result"].get("unifiedMarginStatus")
                
                if account_type:
                    logger.info(f"Account type: {account_type}")
                    if account_type in [1, "1", "UNIFIED"]:
                        logger.info("Unified margin account confirmed")
                    else:
                        logger.warning("Account is not using unified margin - some features may not work")
                else:
                    logger.warning("Could not determine account type")
                
                return True
            else:
                logger.error("Failed to connect to Bybit API")
                return False
        except Exception as e:
            logger.error(f"Error checking connection: {str(e)}")
            # Continue anyway - don't fail initialization
            return False 