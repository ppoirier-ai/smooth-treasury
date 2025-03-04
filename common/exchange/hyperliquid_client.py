from typing import Dict, Any, Optional, List
from common.exchange.base_client import BaseExchangeClient
from common.utils.logger import setup_logger
from hyperliquid.info import Info
import json

logger = setup_logger(__name__)

class HyperliquidClient(BaseExchangeClient):
    """Hyperliquid exchange client implementation."""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """Initialize the Hyperliquid client.
        
        Args:
            api_key: Wallet address
            api_secret: Private key or signature
            testnet: Whether to use testnet
        """
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Initialize SDK client
        self.base_url = "https://dev.hyperliquid.xyz" if testnet else "https://api.hyperliquid.xyz"
        self.info = Info(self.base_url)
        
        # Initialize connection
        try:
            # Test connection
            meta = self.info.meta()
            self.available_pairs = [asset['name'] for asset in meta['universe']]
            
            # Get proper API name
            environment = "testnet" if testnet else "mainnet"
            logger.info(f"Connected to Hyperliquid {environment}")
        except Exception as e:
            logger.error(f"Failed to connect to Hyperliquid: {str(e)}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current ticker for a symbol."""
        try:
            # Normalize symbol format (strip /USD or /USDT if present)
            coin = symbol.split('/')[0].upper().strip()
            
            # Verify coin exists
            if coin not in self.available_pairs:
                logger.warning(f"Symbol {coin} not found in available pairs")
                return {}
            
            # Get current price
            prices = self.info.all_mids()
            if coin in prices:
                price = float(prices[coin])
                
                return {
                    "symbol": symbol,
                    "bid": price * 0.9999,  # Approximate bid
                    "ask": price * 1.0001,  # Approximate ask
                    "last": price,
                    "info": {"mid": price}
                }
            else:
                logger.warning(f"No price found for {coin}")
                return {}
        except Exception as e:
            logger.error(f"Error getting ticker: {str(e)}")
            return {}
    
    def get_orderbook(self, symbol: str) -> Dict[str, Any]:
        """Get orderbook for a symbol."""
        try:
            # Normalize symbol format
            coin = symbol.split('/')[0].upper().strip()
            
            # Verify coin exists
            if coin not in self.available_pairs:
                logger.warning(f"Symbol {coin} not found in available pairs")
                return {"bids": [], "asks": []}
            
            # Get orderbook using the alternative method that works
            orderbook_data = {
                "type": "l2Book",
                "coin": coin,
                "depth": 10  # Get top 10 levels
            }
            
            orderbook = self.info.post("/info", orderbook_data)
            
            # Format the orderbook to match the expected structure
            formatted_bids = []
            formatted_asks = []
            
            # Process bids (first array in levels)
            if "levels" in orderbook and len(orderbook["levels"]) > 0:
                for bid in orderbook["levels"][0]:
                    formatted_bids.append([float(bid["px"]), float(bid["sz"])])
            
            # Process asks (second array in levels)
            if "levels" in orderbook and len(orderbook["levels"]) > 1:
                for ask in orderbook["levels"][1]:
                    formatted_asks.append([float(ask["px"]), float(ask["sz"])])
            
            return {
                "symbol": symbol,
                "bids": formatted_bids,
                "asks": formatted_asks,
                "timestamp": orderbook.get("time", 0),
                "datetime": None  # Will be calculated if needed
            }
        except Exception as e:
            logger.error(f"Error getting orderbook: {str(e)}")
            return {"bids": [], "asks": []}
    
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for a symbol."""
        try:
            # This is a placeholder - we'll need to implement the actual API call
            # when we implement private methods
            logger.info(f"Setting leverage for {symbol} to {leverage}x")
            return True
        except Exception as e:
            logger.error(f"Error setting leverage: {str(e)}")
            return False
    
    def get_account_balance(self, currency: str = None) -> Dict[str, Any]:
        """Get account balance."""
        try:
            # This is a placeholder - we'll need to implement the actual API call
            # when we implement private methods
            return {"free": 0.0, "used": 0.0, "total": 0.0}
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            return {}
    
    def create_order(self, symbol: str, side: str, amount: float, price: float) -> Optional[Dict]:
        """Create a new order."""
        try:
            # This is a placeholder - we'll need to implement the actual API call
            # when we implement private methods
            order_id = "placeholder_order_id"
            return {
                "id": order_id,
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "price": price,
                "status": "new"
            }
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return None
    
    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all orders for a symbol."""
        try:
            # This is a placeholder - we'll need to implement the actual API call
            # when we implement private methods
            logger.info(f"Cancelled all orders for {symbol}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling orders: {str(e)}")
            return False
    
    def get_open_orders(self, symbol: str) -> list:
        """Get all open orders for a symbol."""
        try:
            # This is a placeholder - we'll need to implement the actual API call
            # when we implement private methods
            return []
        except Exception as e:
            logger.error(f"Error getting open orders: {str(e)}")
            return []
    
    def get_positions(self, symbol: str = None) -> list:
        """Get current positions."""
        try:
            # This is a placeholder - we'll need to implement the actual API call
            # when we implement private methods
            return []
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return []
    
    # ... implement other required methods 