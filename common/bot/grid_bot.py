from typing import Dict, List, Optional
from common.exchange.base_client import BaseExchangeClient
from common.utils.grid import calculate_grid_levels, calculate_grid_orders
from common.utils.logger import setup_logger
from datetime import datetime
import time

logger = setup_logger(__name__)

class GridBot:
    def __init__(
        self,
        exchange: BaseExchangeClient,  # Add type hint for exchange
        symbol: str,
        capital: float,
        grid_count: int = 5,
        range_percentage: float = 2.0
    ):
        """Initialize the grid trading bot.
        
        Args:
            exchange: The exchange client instance
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            capital: Amount of capital to use
            grid_count: Number of grid levels
            range_percentage: Price range percentage
        """
        self.exchange = exchange
        self.symbol = symbol
        self.capital = capital
        self.grid_count = grid_count
        self.range_percentage = range_percentage
        
        self.running = False
        self.grid_orders = []
        self.filled_orders = []
        self.active_positions = []
    
    def start(self):
        """Start the grid trading bot."""
        logger.info(f"Starting grid trading for {self.symbol}")
        
        # Set leverage
        if self.exchange.set_leverage(self.symbol, 2):
            logger.info(f"Set leverage to 2x for {self.symbol}")
        else:
            logger.warning(f"Failed to set leverage to 2x for {self.symbol}. Using account default.")
        
        # Initialize grid
        self.initialize_grid()
        self.running = True
        
        # Start monitoring
        try:
            while self.running:
                self.monitor_and_update()
                time.sleep(10)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the grid trading bot."""
        logger.info("Stopping grid trading bot...")
        self.running = False
        self.cancel_all_orders()
        self.print_summary()
    
    def initialize_grid(self):
        # Implementation of initialize_grid method
        pass
    
    def monitor_and_update(self):
        # Implementation of monitor_and_update method
        pass
    
    def cancel_all_orders(self):
        # Implementation of cancel_all_orders method
        pass
    
    def print_summary(self):
        # Implementation of print_summary method
        pass
    
    def handle_order_fill(self, order_id: str, fill_price: float, fill_amount: float):
        """Handle order fill event."""
        if order_id not in self.active_positions:
            logger.warning(f"Unknown order filled: {order_id}")
            return
            
        filled_order = self.active_positions.pop(order_id)
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
        
        result = self.exchange.create_order(
            symbol=self.symbol,
            side=new_order['side'],
            amount=new_order['amount'],
            price=new_order['price']
        )
        if result:
            self.active_positions[result['id']] = {
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
        return total_profit 