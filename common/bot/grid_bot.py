from typing import Dict, List, Optional
from common.exchange.client import ExchangeClient
from common.utils.grid import calculate_grid_levels, calculate_grid_orders
from common.utils.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)

class GridBot:
    def __init__(self, bot_id: int, client: ExchangeClient, pair: str,
                 lower: float, upper: float, grids: int, capital: float):
        self.bot_id = bot_id
        self.client = client
        self.pair = pair
        self.capital = capital
        self.levels = calculate_grid_levels(lower, upper, grids)
        self.orders = calculate_grid_orders(capital, self.levels)
        self.active_orders: Dict[str, dict] = {}  # order_id -> order_info
        self.filled_orders: List[dict] = []
        
    def start(self):
        """Start grid trading."""
        logger.info(f"Starting grid bot {self.bot_id} for {self.pair}")
        for order in self.orders:
            result = self.client.create_order(
                symbol=self.pair,
                side=order['side'],
                amount=order['amount'],
                price=order['price']
            )
            if result:
                self.active_orders[result['id']] = {
                    **order,
                    'order_id': result['id'],
                    'status': result['status'],
                    'timestamp': datetime.now()
                }
            else:
                logger.error(f"Failed to create order: {order}")
    
    def stop(self):
        """Stop grid trading."""
        logger.info(f"Stopping grid bot {self.bot_id}")
        if not self.client.cancel_all_orders(self.pair):
            logger.error(f"Failed to cancel orders for {self.pair}")
        self.active_orders.clear()
    
    def handle_order_fill(self, order_id: str, fill_price: float, fill_amount: float):
        """Handle order fill event."""
        if order_id not in self.active_orders:
            logger.warning(f"Unknown order filled: {order_id}")
            return
            
        filled_order = self.active_orders.pop(order_id)
        filled_order.update({
            'fill_price': fill_price,
            'fill_amount': fill_amount,
            'fill_time': datetime.now()
        })
        self.filled_orders.append(filled_order)
        
        # Create new order on opposite side
        new_order = {
            'side': 'buy' if filled_order['side'] == 'sell' else 'sell',
            'price': filled_order['price'],
            'amount': filled_order['amount']
        }
        
        result = self.client.create_order(
            symbol=self.pair,
            side=new_order['side'],
            amount=new_order['amount'],
            price=new_order['price']
        )
        if result:
            self.active_orders[result['id']] = {
                **new_order,
                'order_id': result['id'],
                'status': result['status'],
                'timestamp': datetime.now()
            }
    
    def calculate_profit(self) -> float:
        """Calculate total profit from filled orders."""
        total_profit = 0.0
        for order in self.filled_orders:
            if order['side'] == 'sell':
                total_profit += (order['fill_price'] - order['price']) * order['fill_amount']
            else:
                total_profit += (order['price'] - order['fill_price']) * order['fill_amount']
        return total_profit * order['fill_price'] 