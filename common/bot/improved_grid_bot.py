from typing import Dict, List, Optional
from common.exchange.base_client import BaseExchangeClient
from common.utils.logger import setup_logger
from datetime import datetime
import time
import math

logger = setup_logger(__name__)

class ImprovedGridBot:
    def __init__(
        self,
        exchange: BaseExchangeClient,
        symbol: str,
        capital: float,
        grid_count: int = 5,
        range_percentage: float = 2.0
    ):
        """Initialize the grid trading bot with working implementations.
        
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
        self.active_positions = {}  # Dict to track active positions
        
        # Get current price to calculate grid
        ticker = self.exchange.get_ticker(self.symbol)
        self.current_price = ticker["last"]
        
        # Calculate grid boundaries
        self.upper_price = self.current_price * (1 + self.range_percentage / 100)
        self.lower_price = self.current_price * (1 - self.range_percentage / 100)
        
        logger.info(f"Grid setup for {self.symbol}: Current price: {self.current_price}")
        logger.info(f"Range: {self.lower_price:.2f} to {self.upper_price:.2f}")
    
    def initialize_grid(self):
        """Actually initialize the grid by calculating levels and placing orders."""
        logger.info("Initializing grid with real implementation...")
        
        # Calculate grid levels
        price_step = (self.upper_price - self.lower_price) / self.grid_count
        price_levels = []
        
        for i in range(self.grid_count + 1):
            price = self.lower_price + (i * price_step)
            price = round(price, 2)  # Round to 2 decimal places
            price_levels.append(price)
        
        logger.info(f"Created {len(price_levels)} price levels from {price_levels[0]} to {price_levels[-1]}")
        
        # Calculate order amount per level (distribute capital evenly)
        amount_per_level = self.capital / self.current_price / self.grid_count
        amount_per_level = round(amount_per_level, 6)  # Round to 6 decimal places for BTC
        
        logger.info(f"Order size per level: {amount_per_level} {self.symbol.split('/')[0]}")
        
        # Place orders at each level
        for price in price_levels:
            # Skip if price is too close to current price (avoid immediate fills)
            if abs(price - self.current_price) / self.current_price < 0.001:
                continue
                
            # Determine order side
            side = "buy" if price < self.current_price else "sell"
            
            try:
                logger.info(f"Placing {side} order at {price}")
                order = self.exchange.create_order(
                    symbol=self.symbol,
                    side=side,
                    amount=amount_per_level,
                    price=price
                )
                
                if order and "id" in order:
                    logger.info(f"Order placed successfully: {order['id']}")
                    self.active_positions[order["id"]] = order
                else:
                    logger.error(f"Failed to place {side} order at {price}")
            except Exception as e:
                logger.error(f"Error placing grid order: {str(e)}")
    
    def cancel_all_orders(self):
        """Actually cancel all orders."""
        logger.info("Cancelling all orders with real implementation...")
        
        # Use exchange's cancel_all_orders method if available
        if hasattr(self.exchange, 'cancel_all_orders'):
            result = self.exchange.cancel_all_orders(self.symbol)
            if result:
                logger.info("Successfully cancelled all orders")
                self.active_positions = {}  # Clear active positions
            return result
            
        # Fallback: cancel orders one by one
        elif hasattr(self.exchange, 'cancel_order'):
            cancelled_count = 0
            cancel_errors = 0
            
            # Get current open orders
            open_orders = self.exchange.get_open_orders(self.symbol)
            logger.info(f"Found {len(open_orders)} open orders to cancel")
            
            for order in open_orders:
                try:
                    result = self.exchange.cancel_order(self.symbol, order["id"])
                    if result:
                        logger.info(f"Cancelled order {order['id']}")
                        cancelled_count += 1
                        # Remove from active positions
                        if order["id"] in self.active_positions:
                            del self.active_positions[order["id"]]
                    else:
                        logger.error(f"Failed to cancel order {order['id']}")
                        cancel_errors += 1
                except Exception as e:
                    logger.error(f"Error cancelling order {order['id']}: {str(e)}")
                    cancel_errors += 1
            
            logger.info(f"Cancelled {cancelled_count} orders with {cancel_errors} errors")
            return cancelled_count > 0 and cancel_errors == 0
        
        else:
            logger.error("Cannot cancel orders - exchange client lacks cancellation methods")
            return False
    
    def monitor_and_update(self):
        """Monitor orders and update grid as needed."""
        logger.info("Checking order status and market conditions...")
        
        # Get current price
        try:
            ticker = self.exchange.get_ticker(self.symbol)
            if ticker and "last" in ticker:
                current_price = ticker["last"]
                logger.info(f"Current price: {current_price}")
            else:
                logger.warning("Could not get current price")
                return
        except Exception as e:
            logger.error(f"Error getting current price: {str(e)}")
            return
            
        # Check open orders
        try:
            open_orders = self.exchange.get_open_orders(self.symbol)
            logger.info(f"Found {len(open_orders)} open orders")
            
            # Track which orders are still open
            open_order_ids = set(order["id"] for order in open_orders)
            
            # Look for filled orders
            for order_id in list(self.active_positions.keys()):
                if order_id not in open_order_ids:
                    # This order is no longer open, handle as filled
                    logger.info(f"Order {order_id} appears to be filled")
                    filled_order = self.active_positions[order_id]
                    
                    # Update filled_orders list
                    self.filled_orders.append({
                        **filled_order,
                        "fill_time": datetime.now(),
                        "fill_price": filled_order["price"],
                        "fill_amount": filled_order["amount"]
                    })
                    
                    # Remove from active positions
                    del self.active_positions[order_id]
                    
                    # Place opposite order
                    self._place_opposite_order(filled_order)
        except Exception as e:
            logger.error(f"Error checking open orders: {str(e)}")
    
    def _place_opposite_order(self, filled_order):
        """Place a new order on the opposite side after a fill."""
        try:
            # Determine opposite side
            side = "buy" if filled_order["side"] == "sell" else "sell"
            price = filled_order["price"]
            amount = filled_order["amount"]
            
            logger.info(f"Placing opposite {side} order at {price}")
            
            # Place the order
            order = self.exchange.create_order(
                symbol=self.symbol,
                side=side,
                amount=amount,
                price=price
            )
            
            if order and "id" in order:
                logger.info(f"Opposite order placed: {order['id']}")
                self.active_positions[order["id"]] = order
            else:
                logger.error("Failed to place opposite order")
        except Exception as e:
            logger.error(f"Error placing opposite order: {str(e)}")
    
    def print_summary(self):
        """Print a summary of the grid bot status."""
        logger.info("\n=== Grid Bot Summary ===")
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"Grid Range: {self.lower_price:.2f} to {self.upper_price:.2f}")
        logger.info(f"Grid Levels: {self.grid_count}")
        logger.info(f"Active Orders: {len(self.active_positions)}")
        logger.info(f"Filled Orders: {len(self.filled_orders)}")
        
        profit = self.calculate_profit()
        logger.info(f"Total Profit: {profit}")
        
        # Print active positions if any
        if self.active_positions:
            logger.info("\nActive Positions:")
            for order_id, order in self.active_positions.items():
                logger.info(f"  {order['side']} {order['amount']} @ {order['price']} (ID: {order_id})")
        
        # Print filled orders if any
        if self.filled_orders:
            logger.info("\nFilled Orders:")
            for i, order in enumerate(self.filled_orders):
                logger.info(f"  {i+1}. {order['side']} {order['amount']} @ {order['price']}")
    
    def calculate_profit(self):
        """Calculate total profit from filled orders."""
        total_profit = 0.0
        for order in self.filled_orders:
            # For simplicity, assume buy low, sell high profit calculation
            if order["side"] == "sell":
                # If we sold, profit is sell price - original buy price
                total_profit += order["amount"] * (order["price"] - order["fill_price"])
            else:
                # If we bought, profit is expected from future sell
                pass
        return total_profit
    
    def start(self):
        """Start the grid bot."""
        logger.info(f"Starting improved grid bot for {self.symbol}")
        self.running = True
        
        # Set leverage if the exchange supports it
        if hasattr(self.exchange, 'set_leverage'):
            try:
                result = self.exchange.set_leverage(self.symbol, 2)
                if result:
                    logger.info(f"Successfully set leverage to 2x for {self.symbol}")
                else:
                    logger.warning(f"Failed to set leverage for {self.symbol}")
            except Exception as e:
                logger.error(f"Error setting leverage: {str(e)}")
        
        # Initialize the grid
        self.initialize_grid()
        
        # Start monitoring in a loop
        try:
            while self.running:
                self.monitor_and_update()
                time.sleep(10)  # Check every 10 seconds
        except KeyboardInterrupt:
            logger.info("Grid bot stopped by user")
            self.stop()
        except Exception as e:
            logger.error(f"Error in grid bot main loop: {str(e)}")
            self.stop()
    
    def stop(self):
        """Stop the grid bot."""
        logger.info("Stopping improved grid bot...")
        self.running = False
        
        # Cancel all orders
        self.cancel_all_orders()
        
        # Print final summary
        self.print_summary() 