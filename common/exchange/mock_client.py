from typing import Optional, Dict, Any, List
from common.utils.logger import setup_logger
import time
import random
import uuid

logger = setup_logger(__name__)

class MockExchangeClient:
    """Mock exchange client for testing without API connectivity."""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = True):
        """Initialize mock exchange client."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Mock data
        self.current_price = 85000.0
        self.balances = {
            'BTC': {'free': 0.1, 'used': 0.0, 'total': 0.1},
            'USDT': {'free': 5000.0, 'used': 0.0, 'total': 5000.0}
        }
        self.open_orders = {}
        
        logger.info("Mock exchange client initialized")
    
    def get_ticker(self, symbol: str) -> Optional[float]:
        """Get current price for symbol."""
        # Simulate small price movement
        change = random.uniform(-0.001, 0.001)
        self.current_price *= (1 + change)
        logger.info(f"Mock current price for {symbol}: {self.current_price}")
        return self.current_price
    
    def create_order(self, symbol: str, side: str, amount: float, price: float) -> Optional[Dict[str, Any]]:
        """Create limit order."""
        order_id = f"mock-{uuid.uuid4().hex[:8]}"
        
        # Simulate balance update
        symbol_parts = symbol.split('/')
        base_currency = symbol_parts[0]  # BTC in BTC/USDT
        quote_currency = symbol_parts[1]  # USDT in BTC/USDT
        
        order = {
            'id': order_id,
            'symbol': symbol,
            'side': side.lower(),
            'amount': amount,
            'price': price,
            'status': 'open',
            'timestamp': int(time.time() * 1000)
        }
        
        # Update balances based on order
        if side.lower() == 'buy':
            cost = amount * price
            # Lock quote currency (USDT for BTC/USDT)
            if quote_currency in self.balances:
                if self.balances[quote_currency]['free'] >= cost:
                    self.balances[quote_currency]['free'] -= cost
                    self.balances[quote_currency]['used'] += cost
                else:
                    logger.error(f"Insufficient {quote_currency} balance")
                    return None
        else:  # sell
            # Lock base currency (BTC for BTC/USDT)
            if base_currency in self.balances:
                if self.balances[base_currency]['free'] >= amount:
                    self.balances[base_currency]['free'] -= amount
                    self.balances[base_currency]['used'] += amount
                else:
                    logger.error(f"Insufficient {base_currency} balance")
                    return None
        
        # Store order
        self.open_orders[order_id] = order
        
        logger.info(f"Created mock {side} order: {order_id}")
        return order

    def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get all open orders for a symbol."""
        orders = []
        
        for order_id, order in self.open_orders.items():
            if symbol is None or order['symbol'] == symbol:
                orders.append(order)
        
        logger.info(f"Found {len(orders)} mock open orders")
        return orders

    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all open orders for a symbol."""
        cancelled = 0
        order_ids_to_remove = []
        
        for order_id, order in self.open_orders.items():
            if order['symbol'] == symbol:
                order_ids_to_remove.append(order_id)
                cancelled += 1
                
                # Return locked funds
                symbol_parts = symbol.split('/')
                base_currency = symbol_parts[0]
                quote_currency = symbol_parts[1]
                
                if order['side'] == 'buy':
                    cost = order['amount'] * order['price']
                    if quote_currency in self.balances:
                        self.balances[quote_currency]['free'] += cost
                        self.balances[quote_currency]['used'] -= cost
                else:  # sell
                    if base_currency in self.balances:
                        self.balances[base_currency]['free'] += order['amount']
                        self.balances[base_currency]['used'] -= order['amount']
        
        # Remove cancelled orders
        for order_id in order_ids_to_remove:
            del self.open_orders[order_id]
        
        logger.info(f"Cancelled {cancelled} mock orders")
        return True
    
    def get_account_balance(self, currency: str = None) -> Dict[str, Any]:
        """Get account balance."""
        if currency:
            if currency in self.balances:
                logger.info(f"Mock {currency} balance: {self.balances[currency]['free']}")
                return self.balances[currency]
            else:
                logger.warning(f"Currency {currency} not found in mock balance")
                return {'free': 0.0, 'used': 0.0, 'total': 0.0}
        else:
            logger.info(f"Mock account has {len(self.balances)} currencies")
            return self.balances 