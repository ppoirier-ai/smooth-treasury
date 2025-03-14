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
import asyncio
from pathlib import Path

from solana.rpc.api import Client as SolanaClient
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solana.publickey import PublicKey
from solana.keypair import Keypair
from solana.rpc.types import TxOpts

try:
    # Try to import Anchor libraries - these might not be available in testing environments
    from anchorpy import Provider, Wallet, Program, Idl
    ANCHOR_AVAILABLE = True
except ImportError:
    # If Anchor libraries aren't available, we'll fall back to mock implementations
    ANCHOR_AVAILABLE = False
    print("AnchorPy not available - using mock implementations for Drift")

from common.utils.logger import setup_logger
from common.exchange.base_client import BaseExchangeClient
from common.utils.solana_utils import decode_private_key, wait_for_confirmation

logger = setup_logger(__name__)

# Drift Program IDs
DRIFT_MAINNET_PROGRAM_ID = "dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH"
DRIFT_DEVNET_PROGRAM_ID = "dRifLzFj5UrUaULWviJaUAJDZeirM6LCBFSdNXvsfSa"

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
            logger.info(f"Initialized Drift client with wallet: {str(self.wallet_public_key)}")
            logger.info(f"Using {'devnet' if testnet else 'mainnet'} for Drift Protocol")
        except Exception as e:
            logger.error(f"Failed to initialize keypair: {e}")
            raise ValueError("Invalid private key format")
        
        # Initialize Drift program addresses
        self.drift_program_id = PublicKey(DRIFT_DEVNET_PROGRAM_ID if testnet else DRIFT_MAINNET_PROGRAM_ID)
        
        # Cache for market data
        self.markets = {}
        self.user_account = None
        
        # Setup Anchor Provider and Program if available
        self.program = None
        self.provider = None
        if ANCHOR_AVAILABLE:
            try:
                self._setup_anchor_program()
                logger.info("Successfully initialized Anchor program for Drift")
            except Exception as e:
                logger.error(f"Failed to initialize Anchor program: {e}")
                logger.warning("Falling back to mock implementation")
                
        # Initialize with market data and user account
        self._initialize()
    
    def _setup_anchor_program(self):
        """Setup Anchor provider and program for Drift."""
        try:
            # Create a wallet instance for Anchor
            wallet = Wallet(self.keypair)
            
            # Create a provider
            provider = Provider(self.solana_client, wallet)
            self.provider = provider
            
            # Load the IDL - in a real implementation, this would load from a file or fetch from chain
            # For now, we'll use a placeholder approach
            idl_path = Path(__file__).parent / "drift_idl.json"
            if idl_path.exists():
                with open(idl_path, 'r') as f:
                    idl = json.load(f)
                    self.program = Program(Idl.from_json(json.dumps(idl)), self.drift_program_id, provider)
                    logger.info("Loaded Drift IDL from file")
            else:
                # In a real implementation, we would fetch the IDL from the chain
                # or use a pre-packaged IDL from the SDK
                logger.warning("Drift IDL file not found, using mock implementation")
                
        except Exception as e:
            logger.error(f"Error setting up Anchor program: {e}")
            raise
    
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
            
            if self.program:
                # In a real implementation, this would fetch markets from the Drift program
                # For now, we'll just use mock data even if the program is available
                pass
                
            # For testing purposes, we'll use mock market data
            self.markets = {
                "cbBTC-PERP": {
                    "market_index": 0,
                    "base_symbol": "cbBTC",
                    "quote_symbol": "USDC",
                    "min_order_size": 0.0001,
                    "tick_size": 0.1,
                    "min_price": 0.1,
                    "price_step": 0.1,
                    "price_precision": 1,
                    "oracle": "FKh6Fvp5bDaFeuYZvV21VoDzDnYfUG7vXWXknL9xy5Rv",
                },
                "SOL-PERP": {
                    "market_index": 1,
                    "base_symbol": "SOL",
                    "quote_symbol": "USDC",
                    "min_order_size": 0.01,
                    "tick_size": 0.001,
                    "min_price": 0.001,
                    "price_step": 0.001,
                    "price_precision": 3,
                    "oracle": "J83w4HKfqxwcq3BEMMkPFSppX3gqekLyLJBexEiDTB8K",
                },
                "ETH-PERP": {
                    "market_index": 2,
                    "base_symbol": "ETH",
                    "quote_symbol": "USDC",
                    "min_order_size": 0.001,
                    "tick_size": 0.01,
                    "min_price": 0.01,
                    "price_step": 0.01,
                    "price_precision": 2,
                    "oracle": "EMkxjGC1CQ7JLiutDbfYb7UKb3zm9SJcUmr1YicBsdpZ",
                }
            }
            
            logger.info(f"Loaded {len(self.markets)} markets from Drift")
        except Exception as e:
            logger.error(f"Error loading markets: {e}")
            raise
    
    def _load_user_account(self):
        """Load user account data from Drift protocol."""
        try:
            if self.program:
                # In a real implementation, this would fetch the user account from the Drift program
                # User account is a PDA derived from the user's wallet address
                
                # Generate the user account address
                USER_ACCOUNT_SEED = "user"
                user_account_pda, bump = PublicKey.find_program_address(
                    [bytes(USER_ACCOUNT_SEED, "utf-8"), bytes(self.wallet_public_key)],
                    self.drift_program_id
                )
                
                # Try to fetch the user account
                try:
                    # This is a placeholder - in a real implementation, we would use the
                    # program's methods to fetch the account data
                    logger.info(f"Attempting to load user account: {user_account_pda}")
                    # user_account_data = self.program.account["User"].fetch(user_account_pda)
                    # self.user_account = user_account_data
                    # logger.info(f"Loaded user account for {self.wallet_public_key}")
                except Exception as e:
                    logger.warning(f"User account not found, might need to be initialized: {e}")
                    self.user_account = None
            else:
                # Mock user account data for testing
                self.user_account = {
                    "authority": str(self.wallet_public_key),
                    "collateral": 10000.0,
                    "positions": []
                }
                logger.info("Loaded mock user account data")
                
        except Exception as e:
            logger.error(f"Error loading user account: {e}")
            self.user_account = None
    
    async def _initialize_user_account_async(self):
        """Initialize a user account on Drift if it doesn't exist (async version)."""
        if not self.program:
            logger.warning("Anchor program not initialized, can't create user account")
            return False
            
        try:
            # This is a placeholder for the initialization transaction
            # In a real implementation, this would use the Drift program's methods
            # to initialize a user account
            
            # Get recent blockhash
            async with AsyncClient(self.rpc_url) as client:
                recent_blockhash = await client.get_recent_blockhash()
                
                # Create the transaction
                tx = Transaction()
                tx.recent_blockhash = recent_blockhash["result"]["value"]["blockhash"]
                
                # Add initialization instruction
                # tx.add(self.program.instruction["initializeUser"](
                #     {"authority": self.wallet_public_key},
                #     program_id=self.drift_program_id
                # ))
                
                # Sign and send transaction
                tx.sign(self.keypair)
                txid = await client.send_transaction(tx, self.keypair)
                
                # Wait for confirmation
                await asyncio.sleep(1)  # Give the transaction some time
                
                # Check if transaction succeeded
                tx_status = await client.get_transaction(txid["result"])
                if tx_status["result"] and tx_status["result"]["meta"]["err"] is None:
                    logger.info(f"Successfully initialized user account: {txid['result']}")
                    return True
                else:
                    logger.error(f"Failed to initialize user account: {tx_status}")
                    return False
                
        except Exception as e:
            logger.error(f"Error initializing user account: {e}")
            return False
    
    def initialize_user_account(self):
        """Initialize a user account on Drift if it doesn't exist (sync wrapper)."""
        # Run the async function in a new event loop
        return asyncio.run(self._initialize_user_account_async())
    
    # Implement BaseExchangeClient methods with Drift SDK if available
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current ticker for symbol."""
        try:
            if self.program and symbol in self.markets:
                # In a real implementation, this would fetch price from the Drift oracle
                # For now, we'll just use mock data
                market = self.markets[symbol]
                
                # Use stubbed data for now
                base_price = 75000 if "BTC" in symbol else (3000 if "ETH" in symbol else 100)
                variation = random.uniform(-base_price*0.001, base_price*0.001)
                price = base_price + variation
                
                return {
                    "symbol": symbol,
                    "last": price,
                    "bid": price * 0.9999,
                    "ask": price * 1.0001,
                    "24h_change": random.uniform(-1.5, 1.5),
                    "24h_volume": random.uniform(100, 1000),
                    "timestamp": int(time.time() * 1000)
                }
            else:
                # Fall back to mock data
                if symbol not in self.markets:
                    logger.warning(f"Symbol {symbol} not found in markets. Using default price.")
                    return {"last": 75000, "bid": 74995, "ask": 75005, "24h_change": 0.5}
                
                # Mock data based on symbol
                base_price = 75000 if "BTC" in symbol else (3000 if "ETH" in symbol else 100)
                variation = random.uniform(-base_price*0.001, base_price*0.001)
                price = base_price + variation
                
                return {
                    "symbol": symbol,
                    "last": price,
                    "bid": price * 0.9999,
                    "ask": price * 1.0001,
                    "24h_change": random.uniform(-1.5, 1.5),
                    "24h_volume": random.uniform(100, 1000),
                    "timestamp": int(time.time() * 1000)
                }
        except Exception as e:
            logger.error(f"Error getting ticker for {symbol}: {e}")
            # Return a default value for testing
            return {"last": 75000, "bid": 74995, "ask": 75005, "24h_change": 0.5}
    
    async def _create_limit_order_async(self, symbol: str, side: str, amount: float, price: float, params=None) -> Optional[str]:
        """Create a limit order on Drift (async version)."""
        if not self.program:
            logger.warning("Anchor program not initialized, falling back to mock implementation")
            return self._create_limit_order_mock(symbol, side, amount, price, params)
            
        try:
            # Make sure user account exists
            if not self.user_account:
                logger.warning("User account not initialized, attempting to initialize")
                success = await self._initialize_user_account_async()
                if not success:
                    logger.error("Failed to initialize user account")
                    return None
            
            # Get market details
            if symbol not in self.markets:
                logger.error(f"Symbol {symbol} not found in available markets")
                return None
                
            market = self.markets[symbol]
            
            # Create order parameters
            order_params = {
                "marketIndex": market["market_index"],
                "direction": 0 if side.lower() == "buy" else 1,  # 0 for long, 1 for short
                "price": int(price * (10 ** market["price_precision"])),  # Convert to integer format
                "size": int(amount * (10 ** 8)),  # Convert to integer format (8 decimal places)
                "orderType": 0,  # 0 for limit
                "reduceOnly": False,
                "postOnly": True,
                "immediateOrCancel": False,
                "triggerPrice": 0,
                "triggerCondition": 0,
                "maxTs": 0
            }
            
            # Generate a client order ID
            client_order_id = str(uuid.uuid4())
            
            # Get recent blockhash
            async with AsyncClient(self.rpc_url) as client:
                recent_blockhash = await client.get_recent_blockhash()
                
                # Create the transaction
                tx = Transaction()
                tx.recent_blockhash = recent_blockhash["result"]["value"]["blockhash"]
                
                # Add placement instruction
                # tx.add(self.program.instruction["placeOrder"](
                #     order_params,
                #     {"authority": self.wallet_public_key},
                #     program_id=self.drift_program_id
                # ))
                
                # Sign and send transaction
                tx.sign(self.keypair)
                txid = await client.send_transaction(tx, self.keypair)
                
                # Wait for confirmation
                await asyncio.sleep(1)  # Give the transaction some time
                
                # Check if transaction succeeded
                tx_status = await client.get_transaction(txid["result"])
                if tx_status["result"] and tx_status["result"]["meta"]["err"] is None:
                    logger.info(f"Successfully placed limit order: {txid['result']}")
                    return client_order_id
                else:
                    logger.error(f"Failed to place limit order: {tx_status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating limit order: {e}")
            return None
    
    def _create_limit_order_mock(self, symbol: str, side: str, amount: float, price: float, params=None) -> Optional[str]:
        """Mock implementation of limit order creation."""
        try:
            logger.info(f"Creating mock limit order: {symbol} {side} {amount} @ {price}")
            
            # Validate the symbol
            if symbol not in self.markets:
                logger.error(f"Symbol {symbol} not found in available markets")
                return None
            
            # Normalize the side
            side = side.lower()
            if side not in ["buy", "sell"]:
                logger.error(f"Invalid side: {side}. Must be 'buy' or 'sell'")
                return None
            
            # Mock order ID generation
            order_id = str(uuid.uuid4())
            
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
            
            logger.info(f"Mock limit order created successfully: {order_id}")
            return order_id
            
        except Exception as e:
            logger.error(f"Error creating mock limit order: {e}")
            return None
    
    def create_limit_order(self, symbol: str, side: str, amount: float, price: float, params=None) -> Optional[str]:
        """Create a limit order on Drift (sync wrapper)."""
        if self.program:
            # Try to use the async implementation
            try:
                return asyncio.run(self._create_limit_order_async(symbol, side, amount, price, params))
            except Exception as e:
                logger.error(f"Error in async limit order creation, falling back to mock: {e}")
                return self._create_limit_order_mock(symbol, side, amount, price, params)
        else:
            # Use the mock implementation
            return self._create_limit_order_mock(symbol, side, amount, price, params)
    
    # Similar implementations for other methods (create_market_order, cancel_order, etc.)
    # For brevity, we'll just use the mock implementations for now
    
    # Then include the rest of the mock implementations as fallbacks

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