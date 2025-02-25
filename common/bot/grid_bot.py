from common.exchange.client import ExchangeClient
from common.utils.grid import calculate_grid_levels, calculate_grid_orders
from common.utils.logger import setup_logger

logger = setup_logger(__name__)

class GridBot:
    def __init__(self, bot_id: int, client: ExchangeClient, pair: str,
                 lower: float, upper: float, grids: int, capital: float):
        self.bot_id = bot_id
        self.client = client
        self.pair = pair
        self.levels = calculate_grid_levels(lower, upper, grids)
        self.orders = calculate_grid_orders(capital, self.levels)
        
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
            if not result:
                logger.error(f"Failed to create order: {order}")
    
    def stop(self):
        """Stop grid trading."""
        logger.info(f"Stopping grid bot {self.bot_id}")
        # Cancel all open orders
        if not self.client.cancel_all_orders(self.pair):
            logger.error(f"Failed to cancel orders for {self.pair}") 