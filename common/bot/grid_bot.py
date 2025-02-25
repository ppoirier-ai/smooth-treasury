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
        for order in self.orders:
            self.client.create_order(
                symbol=self.pair,
                side=order['side'],
                amount=order['amount'],
                price=order['price']
            )
    
    def stop(self):
        """Stop grid trading."""
        # Cancel all open orders
        self.client.cancel_all_orders(self.pair) 