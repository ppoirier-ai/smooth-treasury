"""
Drift Protocol client for trading on Solana blockchain.
Handles integration with Drift Protocol for spot and perpetual trading.
"""

from typing import Dict, Any, Optional, List
import time
import base58
import json
import logging
import random
import uuid

from solana.rpc.api import Client as SolanaClient
from solana.transaction import Transaction
from solana.publickey import PublicKey
from solana.keypair import Keypair

from common.utils.logger import setup_logger
from common.exchange.base_client import BaseExchangeClient

logger = setup_logger(__name__)

class DriftClient(BaseExchangeClient):
    """Drift protocol client implementation."""
    
    def __init__(self, 
                 private_key: str, 
                 rpc_url: str = "https://api.mainnet-beta.solana.com",
                 testnet: bool = False):
        """Initialize Drift client with Solana wallet credentials.
        
        Args:
            private_key: Base58 encoded private key for Solana wallet
            rpc_url: Solana RPC URL
            testnet: Whether to use testnet (devnet) or mainnet
        """
        self.testnet = testnet
        self.rpc_url = "https://api.devnet.solana.com" if testnet else rpc_url
        
        # Initialize Solana client
        self.solana_client = SolanaClient(self.rpc_url)
        
        # Load keypair from private key
        try:
            decoded_key = base58.b58decode(private_key)
            self.keypair = Keypair.from_secret_key(decoded_key)
            self.wallet_public_key = self.keypair.public_key
            
            # Mask private key for logging
            masked_key = private_key[:4] + "..." + private_key[-4:] if len(private_key) > 8 else "****"
            logger.info(f"Initialized Drift client with wallet: {str(self.wallet_public_key)[:6]}...{str(self.wallet_public_key)[-6:]}")
            logger.info(f"Using {'devnet' if testnet else 'mainnet'} for Drift Protocol")
        except Exception as e:
            logger.error(f"Failed to initialize keypair: {e}")
            raise ValueError("Invalid private key format")
        
        # Initialize Drift program addresses
        self.drift_program_id = PublicKey("dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH") # Drift program ID
        
        # Cache for market data
        self.markets = {}
        self.user_account = None
        
        # Connect and initialize
        self._initialize()
    
    def _initialize(self):
        """Initialize connection to Drift protocol and load markets."""
        try:
            # Get available markets
            self._load_markets()
            
            # Load user account if it exists
            self._load_user_account()
            
            logger.info("Successfully initialized Drift client")
        except Exception as e:
            logger.error(f"Failed to initialize Drift client: {e}")
            raise
    
    def _load_markets(self):
        """Load available markets from Drift protocol."""
        try:
            logger.info("Loading Drift markets...")
            # This would involve Drift-specific API calls to fetch markets
            # For now, we'll just stub this with cbBTC market
            
            self.markets = {
                "cbBTC-PERP": {
                    "market_index": 0,
                    "base_symbol": "cbBTC",
                    "quote_symbol": "USDC",
                    "min_order_size": 0.0001,
                    "tick_size": 0.1,
                    "min_price": 0.1,
                    "price_step": 0.1,
                    "price_precision": 1
                }
            }
            
            logger.info(f"Loaded {len(self.markets)} markets from Drift")
        except Exception as e:
            logger.error(f"Error loading markets: {e}")
            raise
    
    def _load_user_account(self):
        """Load user account data from Drift protocol."""
        # This would involve Drift-specific API calls
        pass
    
    # Implement BaseExchangeClient methods
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current ticker for symbol."""
        try:
            # For testing, use price around current BTC price
            # In a real implementation, this would fetch data from Drift's oracle
            if symbol not in self.markets:
                logger.warning(f"Symbol {symbol} not found in markets. Using default price.")
                return {"last": 75000, "bid": 74995, "ask": 75005, "24h_change": 0.5}
            
            # Use stubbed data for now
            base_price = 75000
            variation = random.uniform(-100, 100)
            price = base_price + variation
            
            return {
                "symbol": symbol,
                "last": price,
                "bid": price - 5,
                "ask": price + 5,
                "24h_change": random.uniform(-1.5, 1.5),
                "24h_volume": random.uniform(100, 1000),
                "timestamp": int(time.time() * 1000)
            }
        except Exception as e:
            logger.error(f"Error getting ticker for {symbol}: {e}")
            # Return a default value for testing
            return {"last": 75000, "bid": 74995, "ask": 75005, "24h_change": 0.5}
    
    def get_balance(self, currency: str = None) -> Dict[str, float]:
        """Get user balance for a currency."""
        try:
            # In a real implementation, we would fetch the balance from Drift
            # For now, just return mock balances
            
            # Initialize balances if they don't exist
            if not hasattr(self, 'balances'):
                self.balances = {
                    "USDC": 10000.0,  # Default balance of 10,000 USDC
                    "SOL": 10.0,      # Default balance of 10 SOL
                    "cbBTC": 0.1      # Default balance of 0.1 cbBTC
                }
            
            if currency:
                currency = currency.upper()
                return {currency: self.balances.get(currency, 0.0)}
            else:
                return self.balances
            
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return {} if currency else {"USDC": 0.0, "SOL": 0.0}
    
    def create_limit_order(self, symbol: str, side: str, amount: float, price: float, params=None) -> Optional[str]:
        """Create a limit order on Drift."""
        try:
            logger.info(f"Creating limit order: {symbol} {side} {amount} @ {price}")
            
            # Validate the symbol
            if symbol not in self.markets:
                logger.error(f"Symbol {symbol} not found in available markets")
                return None
            
            # Normalize the side
            side = side.lower()
            if side not in ["buy", "sell"]:
                logger.error(f"Invalid side: {side}. Must be 'buy' or 'sell'")
                return None
            
            # Mock order ID generation (in real implementation, this would come from Drift)
            order_id = str(uuid.uuid4())
            
            # Log the order details
            logger.info(f"Order details: {symbol} {side} {amount} @ {price}")
            
            # In a real implementation, we would submit a transaction to Drift here
            # For now, just simulate a successful order placement
            logger.info(f"Simulating Drift protocol transaction for limit order")
            
            # Store the order in our internal tracking
            if not hasattr(self, 'orders'):
                self.orders = {}
            
            self.orders[order_id] = {
                "id": order_id,
                "symbol": symbol,
                "side": side,
                "amount": float(amount),
                "price": float(price),
                "filled": 0.0,
                "status": "open",
                "type": "limit",
                "timestamp": int(time.time() * 1000),
                "client_id": params.get("client_id", "") if params else ""
            }
            
            logger.info(f"Limit order created successfully: {order_id}")
            return order_id
            
        except Exception as e:
            logger.error(f"Error creating limit order: {e}")
            return None
    
    def create_market_order(self, symbol: str, side: str, amount: float, params=None) -> Optional[str]:
        """Create a market order on Drift."""
        try:
            logger.info(f"Creating market order: {symbol} {side} {amount}")
            
            # Validate the symbol
            if symbol not in self.markets:
                logger.error(f"Symbol {symbol} not found in available markets")
                return None
            
            # Normalize the side
            side = side.lower()
            if side not in ["buy", "sell"]:
                logger.error(f"Invalid side: {side}. Must be 'buy' or 'sell'")
                return None
            
            # Get current price for the symbol
            ticker = self.get_ticker(symbol)
            price = ticker["last"]
            
            # Mock order ID generation
            order_id = str(uuid.uuid4())
            
            # Log the order details
            logger.info(f"Market order details: {symbol} {side} {amount} @ ~{price} (market price)")
            
            # In a real implementation, we would submit a transaction to Drift here
            # For now, just simulate a successful order placement and immediate fill
            logger.info(f"Simulating Drift protocol transaction for market order")
            
            # Store the order in our internal tracking
            if not hasattr(self, 'orders'):
                self.orders = {}
            
            self.orders[order_id] = {
                "id": order_id,
                "symbol": symbol,
                "side": side,
                "amount": float(amount),
                "price": float(price),
                "filled": float(amount),  # Market orders are considered immediately filled
                "status": "filled",
                "type": "market",
                "timestamp": int(time.time() * 1000),
                "client_id": params.get("client_id", "") if params else ""
            }
            
            # Update balance based on the filled order
            self._update_balance_after_fill(symbol, side, amount, price)
            
            logger.info(f"Market order created and filled successfully: {order_id}")
            return order_id
            
        except Exception as e:
            logger.error(f"Error creating market order: {e}")
            return None
    
    def cancel_order(self, order_id: str, symbol: str = None) -> bool:
        """Cancel an order by ID."""
        try:
            logger.info(f"Cancelling order: {order_id}")
            
            # Check if we have this order
            if not hasattr(self, 'orders') or order_id not in self.orders:
                logger.warning(f"Order {order_id} not found")
                return False
            
            # Get the order
            order = self.orders[order_id]
            
            # If symbol is provided, check that it matches
            if symbol and order["symbol"] != symbol:
                logger.warning(f"Order {order_id} is for symbol {order['symbol']}, not {symbol}")
                return False
            
            # In a real implementation, we would submit a cancel transaction to Drift here
            # For now, just simulate a successful cancellation
            logger.info(f"Simulating Drift protocol transaction for order cancellation")
            
            # Update the order status
            order["status"] = "cancelled"
            self.orders[order_id] = order
            
            logger.info(f"Order cancelled successfully: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False
    
    def cancel_all_orders(self, symbol: str = None) -> bool:
        """Cancel all open orders, optionally for a specific symbol."""
        try:
            logger.info(f"Cancelling all orders{' for ' + symbol if symbol else ''}")
            
            if not hasattr(self, 'orders'):
                logger.info("No orders to cancel")
                return True
            
            cancelled_count = 0
            for order_id, order in list(self.orders.items()):
                # Skip orders that aren't open
                if order["status"] != "open":
                    continue
                    
                # Skip orders for other symbols if a symbol was specified
                if symbol and order["symbol"] != symbol:
                    continue
                    
                # Cancel the order
                if self.cancel_order(order_id):
                    cancelled_count += 1
            
            logger.info(f"Cancelled {cancelled_count} orders")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling all orders: {e}")
            return False
    
    def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get all open orders, optionally for a specific symbol."""
        try:
            if not hasattr(self, 'orders'):
                return []
            
            open_orders = []
            for order_id, order in self.orders.items():
                # Skip orders that aren't open
                if order["status"] != "open":
                    continue
                    
                # Skip orders for other symbols if a symbol was specified
                if symbol and order["symbol"] != symbol:
                    continue
                    
                open_orders.append(order)
            
            return open_orders
            
        except Exception as e:
            logger.error(f"Error getting open orders: {e}")
            return []
    
    def get_order(self, order_id: str, symbol: str = None) -> Optional[Dict[str, Any]]:
        """Get order details by ID."""
        try:
            if not hasattr(self, 'orders') or order_id not in self.orders:
                return None
            
            order = self.orders[order_id]
            
            # If symbol is provided, check that it matches
            if symbol and order["symbol"] != symbol:
                return None
            
            return order
            
        except Exception as e:
            logger.error(f"Error getting order: {e}")
            return None
    
    def get_order_status(self, order_id: str, symbol: str = None) -> Optional[str]:
        """Get order status by ID."""
        try:
            order = self.get_order(order_id, symbol)
            if order:
                return order["status"]
            return None
            
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return None
    
    def _update_balance_after_fill(self, symbol: str, side: str, amount: float, price: float):
        """Update balances after an order fill."""
        try:
            # Initialize balances if they don't exist
            if not hasattr(self, 'balances'):
                self.balances = {
                    "USDC": 10000.0,
                    "SOL": 10.0,
                    "cbBTC": 0.1
                }
            
            # Parse the symbol to get base and quote assets
            if "-" in symbol:
                base_asset = symbol.split("-")[0]
                quote_asset = "USDC"  # For perpetuals, quote is always USDC
            else:
                logger.warning(f"Unexpected symbol format: {symbol}")
                return
            
            # Calculate the trade value
            trade_value = amount * price
            
            # Update balances based on side
            if side == "buy":
                self.balances[base_asset] = self.balances.get(base_asset, 0.0) + amount
                self.balances[quote_asset] = self.balances.get(quote_asset, 0.0) - trade_value
            else:  # sell
                self.balances[base_asset] = self.balances.get(base_asset, 0.0) - amount
                self.balances[quote_asset] = self.balances.get(quote_asset, 0.0) + trade_value
            
            logger.info(f"Updated balances after {side} order: {self.balances}")
            
        except Exception as e:
            logger.error(f"Error updating balance after fill: {e}") 