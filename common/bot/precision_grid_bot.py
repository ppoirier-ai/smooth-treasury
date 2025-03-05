"""Grid trading bot with precision handling for accurate order placement."""
from typing import Dict, List, Optional
from common.exchange.base_client import BaseExchangeClient
from common.utils.logger import setup_logger
from common.utils.symbol_info import get_symbol_info, adjust_quantity, adjust_price
from datetime import datetime
import time

logger = setup_logger(__name__)

class PrecisionGridBot:
    """Grid trading bot with proper handling of exchange precision requirements."""
    
    def __init__(
        self,
        exchange: BaseExchangeClient,
        symbol: str,
        capital: float,
        grid_count: int = 5,
        range_percentage: float = 2.0
    ):
        """Initialize the precision-aware grid trading bot.
        
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
        self.filled_orders = []
        self.active_positions = {}  # Dict to track active positions
        
        # Get current price to calculate grid
        ticker = self.exchange.get_ticker(self.symbol)
        self.current_price = ticker["last"]
        
        # Get symbol precision info
        self.symbol_info = get_symbol_info(self.exchange, self.symbol)
        logger.info(f"Symbol precision: Min Qty={self.symbol_info['min_qty']}, Qty Step={self.symbol_info['qty_step']}")
        
        # Calculate grid boundaries
        self.upper_price = self.current_price * (1 + self.range_percentage / 100)
        self.lower_price = self.current_price * (1 - self.range_percentage / 100)
        
        # Adjust boundaries to valid price levels
        self.lower_price = float(adjust_price(self.lower_price, self.symbol_info))
        self.upper_price = float(adjust_price(self.upper_price, self.symbol_info))
        
        logger.info(f"Grid setup for {self.symbol}: Current price: {self.current_price}")
        logger.info(f"Range: {self.lower_price:.2f} to {self.upper_price:.2f}")
        
        # Calculate order size with precision adjustment
        self._calculate_order_size()
    
    def _calculate_order_size(self):
        """Calculate the precise order size for each grid level."""
        # Calculate raw amount per level
        raw_amount = self.capital / self.current_price / self.grid_count
        
        # Adjust to valid quantity
        self.order_amount = adjust_quantity(raw_amount, self.symbol_info)
        logger.info(f"Order size per level: {self.order_amount} {self.symbol.split('/')[0]}")
        
        # Calculate total allocation actually used
        total_allocation = float(self.order_amount) * self.grid_count * self.current_price
        logger.info(f"Actual allocation: {total_allocation:.2f} USDT (vs requested {self.capital:.2f})")
    
    def initialize_grid(self):
        """Initialize the grid by calculating levels and placing orders."""
        logger.info("Initializing precision grid...")
        
        # Calculate grid levels
        price_step = (self.upper_price - self.lower_price) / self.grid_count
        price_levels = []
        
        for i in range(self.grid_count + 1):
            price = self.lower_price + (i * price_step)
            adjusted_price = float(adjust_price(price, self.symbol_info))
            price_levels.append(adjusted_price)
        
        logger.info(f"Created {len(price_levels)} price levels:")
        for price in price_levels:
            logger.info(f"  - {price}")
        
        # Place orders at each level
        orders_placed = 0
        for price in price_levels:
            # Skip if price is too close to current price (avoid immediate fills)
            if abs(price - self.current_price) / self.current_price < 0.001:
                logger.info(f"Skipping level {price} (too close to current price)")
                continue
                
            # Determine order side
            side = "buy" if price < self.current_price else "sell"
            
            try:
                logger.info(f"Placing {side} order: {self.order_amount} @ {price}")
                order = self.exchange.create_order(
                    symbol=self.symbol,
                    side=side,
                    amount=float(self.order_amount),
                    price=price
                )
                
                if order and "id" in order:
                    logger.info(f"Order placed: {order['id']}")
                    self.active_positions[order["id"]] = order
                    orders_placed += 1
                    time.sleep(0.5)  # Small delay to avoid rate limits
                else:
                    logger.error(f"Failed to place {side} order at {price}")
            except Exception as e:
                logger.error(f"Error placing grid order: {str(e)}")
        
        logger.info(f"Successfully placed {orders_placed} orders")
    
    def cancel_all_orders(self):
        """Cancel all open orders."""
        logger.info("Cancelling all orders...")
        
        # Use exchange's cancel_all_orders method if available
        if hasattr(self.exchange, 'cancel_all_orders'):
            result = self.exchange.cancel_all_orders(self.symbol)
            if result:
                logger.info("Successfully cancelled all orders")
                self.active_positions = {}  # Clear active positions
            return result
        
        # Fallback: manual cancellation if needed
        else:
            cancelled_count = 0
            
            open_orders = self.exchange.get_open_orders(self.symbol)
            logger.info(f"Found {len(open_orders)} orders to cancel")
            
            for order in open_orders:
                try:
                    result = self.exchange.cancel_order(self.symbol, order["id"])
                    if result:
                        logger.info(f"Cancelled order {order['id']}")
                        cancelled_count += 1
                        # Remove from active positions
                        if order["id"] in self.active_positions:
                            del self.active_positions[order["id"]]
                except Exception as e:
                    logger.error(f"Error cancelling order {order['id']}: {str(e)}")
            
            logger.info(f"Cancelled {cancelled_count} orders")
            return cancelled_count > 0
    
    def monitor_and_update(self):
        """Check for order fills and update the grid."""
        # Get current market price
        try:
            ticker = self.exchange.get_ticker(self.symbol)
            current_price = ticker["last"]
            logger.debug(f"Current price: {current_price}")
            
            # Check open orders to identify fills
            open_orders = self.exchange.get_open_orders(self.symbol)
            
            # Create a set of open order IDs for fast lookup
            open_order_ids = set(order["id"] for order in open_orders)
            
            # Look for filled orders
            for order_id in list(self.active_positions.keys()):
                if order_id not in open_order_ids:
                    # This order is no longer open, handle as filled
                    logger.info(f"Order {order_id} appears to be filled")
                    filled_order = self.active_positions[order_id]
                    
                    # Record fill info
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
            logger.error(f"Error monitoring orders: {str(e)}")
    
    def _place_opposite_order(self, filled_order):
        """Place a new order on the opposite side after a fill."""
        try:
            # Determine opposite side
            side = "buy" if filled_order["side"] == "sell" else "sell"
            
            # Use the same price (grid rebuy/resell)
            price = filled_order["price"]
            
            # Place the opposite order
            logger.info(f"Placing opposite {side} order at {price}")
            
            order = self.exchange.create_order(
                symbol=self.symbol,
                side=side,
                amount=float(self.order_amount),
                price=price
            )
            
            if order and "id" in order:
                logger.info(f"Opposite order placed: {order['id']}")
                self.active_positions[order["id"]] = order
            else:
                logger.error("Failed to place opposite order")
        except Exception as e:
            logger.error(f"Error placing opposite order: {str(e)}")
    
    def calculate_profit(self):
        """Calculate total profit from filled orders."""
        total_profit = 0.0
        pairs_matched = 0
        
        # Group orders by price level
        orders_by_price = {}
        for order in self.filled_orders:
            price = order["price"]
            if price not in orders_by_price:
                orders_by_price[price] = []
            orders_by_price[price].append(order)
        
        # For each price level, match buys and sells
        for price, orders in orders_by_price.items():
            buys = [o for o in orders if o["side"] == "buy"]
            sells = [o for o in orders if o["side"] == "sell"]
            
            # Match buy/sell pairs and calculate profit
            pairs = min(len(buys), len(sells))
            if pairs > 0:
                pairs_matched += pairs
                for i in range(pairs):
                    buy_price = buys[i]["price"]
                    sell_price = sells[i]["price"]
                    amount = float(self.order_amount)
                    
                    # Profit is the difference between sell and buy prices
                    profit = (sell_price - buy_price) * amount
                    total_profit += profit
        
        logger.info(f"Calculated profit from {pairs_matched} matched pairs: {total_profit:.8f}")
        return total_profit
    
    def print_summary(self):
        """Print a summary of the grid bot status."""
        logger.info("\n=== Grid Bot Summary ===")
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"Grid Range: {self.lower_price:.2f} to {self.upper_price:.2f}")
        logger.info(f"Grid Levels: {self.grid_count}")
        logger.info(f"Order Size: {self.order_amount} {self.symbol.split('/')[0]}")
        logger.info(f"Active Orders: {len(self.active_positions)}")
        logger.info(f"Filled Orders: {len(self.filled_orders)}")
        
        profit = self.calculate_profit()
        logger.info(f"Total Profit: {profit:.8f} USDT")
        
        # Print active positions if any
        if self.active_positions:
            logger.info("\nActive Positions:")
            for order_id, order in self.active_positions.items():
                logger.info(f"  {order['side']} {order['amount']} @ {order['price']} (ID: {order_id})")
    
    def start(self):
        """Start the grid bot."""
        logger.info(f"Starting precision grid bot for {self.symbol}")
        self.running = True
        
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
        logger.info("Stopping precision grid bot...")
        self.running = False
        
        # Cancel all orders
        self.cancel_all_orders()
        
        # Print final summary
        self.print_summary() 