"""Directional grid trading bot with long or short bias."""
from typing import Dict, List, Optional, Literal
from common.exchange.base_client import BaseExchangeClient
from common.utils.logger import setup_logger
from common.utils.symbol_info import get_symbol_info, adjust_quantity, adjust_price
from datetime import datetime
import time

logger = setup_logger(__name__)

class DirectionalGridBot:
    """Grid trading bot with directional bias (long or short)."""
    
    def __init__(
        self,
        exchange: BaseExchangeClient,
        symbol: str,
        capital: float,
        grid_count: int = 5,
        range_percentage: float = 2.0,
        direction: Literal["long", "short"] = "long",
        leverage: int = 2,
        initial_position_pct: float = 50.0
    ):
        """Initialize the directional grid trading bot.
        
        Args:
            exchange: The exchange client instance
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            capital: Total capital to use
            grid_count: Number of grid levels
            range_percentage: Price range percentage
            direction: Trading direction ("long" or "short")
            leverage: Leverage to use (1 = no leverage)
            initial_position_pct: Percentage of capital to use for initial position (0-100)
        """
        self.exchange = exchange
        self.symbol = symbol
        self.capital = capital
        self.grid_count = grid_count
        self.range_percentage = range_percentage
        self.direction = direction
        self.leverage = leverage
        self.initial_position_pct = initial_position_pct
        
        self.running = False
        self.filled_orders = []
        self.active_positions = {}  # Dict to track active positions
        
        # Get current price to calculate grid
        ticker = self.exchange.get_ticker(self.symbol)
        self.current_price = ticker["last"]
        
        # Get symbol precision info
        self.symbol_info = get_symbol_info(self.exchange, self.symbol)
        logger.info(f"Symbol precision: Min Qty={self.symbol_info['min_qty']}, Qty Step={self.symbol_info['qty_step']}")
        
        # Calculate grid boundaries based on direction
        if self.direction == "long":
            # For long bias, we focus more on the downside for buying opportunities
            self.upper_price = self.current_price * (1 + self.range_percentage / 100)
            self.lower_price = self.current_price * (1 - (self.range_percentage * 1.5) / 100)
        else:  # short
            # For short bias, we focus more on the upside for selling opportunities
            self.upper_price = self.current_price * (1 + (self.range_percentage * 1.5) / 100)
            self.lower_price = self.current_price * (1 - self.range_percentage / 100)
        
        # Adjust boundaries to valid price levels
        self.lower_price = float(adjust_price(self.lower_price, self.symbol_info))
        self.upper_price = float(adjust_price(self.upper_price, self.symbol_info))
        
        logger.info(f"Directional ({self.direction}) grid setup for {self.symbol}: Current price: {self.current_price}")
        logger.info(f"Range: {self.lower_price:.2f} to {self.upper_price:.2f}")
        
        # Calculate order size and initial position size
        self._calculate_position_sizes()
        
        # Set leverage if supported
        self._set_leverage()
    
    def _set_leverage(self):
        """Set leverage for the trading pair if supported."""
        if hasattr(self.exchange, 'set_leverage') and self.leverage > 1:
            try:
                result = self.exchange.set_leverage(self.symbol, self.leverage)
                if result:
                    logger.info(f"Successfully set leverage to {self.leverage}x for {self.symbol}")
                else:
                    logger.warning(f"Failed to set leverage for {self.symbol}. Using account default.")
            except Exception as e:
                logger.error(f"Error setting leverage: {str(e)}")
    
    def _calculate_position_sizes(self):
        """Calculate initial position size and grid order sizes."""
        # Calculate initial position size
        self.initial_position_capital = self.capital * (self.initial_position_pct / 100)
        self.initial_position_size = self.initial_position_capital / self.current_price
        
        # Adjust to valid quantity
        self.initial_position_size = float(adjust_quantity(self.initial_position_size, self.symbol_info))
        
        # Calculate grid order size (remaining capital divided by grid count)
        remaining_capital = self.capital - self.initial_position_capital
        grid_capital_per_level = remaining_capital / self.grid_count
        
        if self.direction == "long":
            # For long, we size orders to increase position as price falls
            raw_grid_order_size = grid_capital_per_level / self.lower_price
        else:
            # For short, we size orders to increase position as price rises
            raw_grid_order_size = grid_capital_per_level / self.upper_price
        
        # Adjust to valid quantity
        self.grid_order_size = adjust_quantity(raw_grid_order_size, self.symbol_info)
        
        logger.info(f"Initial position: {self.initial_position_size} {self.symbol.split('/')[0]} " +
                   f"(~{self.initial_position_capital:.2f} USDT)")
        logger.info(f"Grid order size: {self.grid_order_size} {self.symbol.split('/')[0]} per level")
    
    def _take_initial_position(self):
        """Take the initial position based on direction."""
        try:
            if self.initial_position_pct <= 0:
                logger.info("No initial position requested, skipping.")
                return True
            
            logger.info(f"Taking initial {self.direction} position of {self.initial_position_size} {self.symbol.split('/')[0]}...")
            
            # For long bias, we buy the initial position at market
            if self.direction == "long":
                side = "buy"
            else:  # short
                side = "sell"
            
            # Place market order for initial position
            # Note: This assumes exchange client has a create_market_order method
            # You might need to implement this in your exchange client
            if hasattr(self.exchange, 'create_market_order'):
                order = self.exchange.create_market_order(
                    symbol=self.symbol,
                    side=side,
                    amount=float(self.initial_position_size)
                )
                
                if order and "id" in order:
                    logger.info(f"Initial position established: {order['id']}")
                    self.filled_orders.append({
                        **order,
                        "fill_time": datetime.now(),
                        "fill_price": order.get("price", self.current_price),
                        "fill_amount": order.get("amount", self.initial_position_size),
                        "is_initial": True
                    })
                    return True
                else:
                    logger.error("Failed to establish initial position")
                    return False
            else:
                # Fallback to limit order if market order not supported
                # Place a limit order slightly worse than market price to ensure fill
                price_adjustment = 0.99 if self.direction == "long" else 1.01
                adjusted_price = self.current_price * price_adjustment
                adjusted_price = float(adjust_price(adjusted_price, self.symbol_info))
                
                logger.info(f"Market order not supported, using limit order at {adjusted_price}")
                
                order = self.exchange.create_order(
                    symbol=self.symbol,
                    side=side,
                    amount=float(self.initial_position_size),
                    price=adjusted_price
                )
                
                if order and "id" in order:
                    logger.info(f"Initial position order placed: {order['id']}")
                    # Wait briefly for the order to fill
                    time.sleep(5)
                    # Check if order was filled
                    # This would require implementing an order status check in your exchange client
                    return True
                else:
                    logger.error("Failed to place initial position order")
                    return False
        except Exception as e:
            logger.error(f"Error taking initial position: {str(e)}")
            return False
    
    def initialize_grid(self):
        """Initialize the grid by placing directional orders."""
        logger.info(f"Initializing {self.direction} directional grid...")
        
        # First, take initial position if needed
        if self.initial_position_pct > 0:
            if not self._take_initial_position():
                logger.error("Failed to establish initial position, aborting grid setup")
                return False
        
        # Calculate grid levels
        price_step = (self.upper_price - self.lower_price) / self.grid_count
        price_levels = []
        
        for i in range(self.grid_count + 1):
            price = self.lower_price + (i * price_step)
            adjusted_price = float(adjust_price(price, self.symbol_info))
            price_levels.append(adjusted_price)
        
        logger.info(f"Created {len(price_levels)} price levels")
        
        # Place orders based on direction
        orders_placed = 0
        
        for price in price_levels:
            # Skip if too close to current price
            if abs(price - self.current_price) / self.current_price < 0.001:
                logger.info(f"Skipping level {price} (too close to current price)")
                continue
            
            # For long bias:
            # - Buy orders below current price (to buy dips)
            # - Sell orders above current price (to take profit)
            # For short bias:
            # - Sell orders above current price (to sell rallies)
            # - Buy orders below current price (to take profit)
            
            if self.direction == "long":
                # Long bias
                if price < self.current_price:
                    # Buy orders below (increasing position on dips)
                    side = "buy"
                    order_size = self.grid_order_size  # Buy more as price drops
                else:
                    # Sell orders above (taking profit)
                    side = "sell"
                    # Calculate sell size based on a portion of position
                    sell_size = float(self.initial_position_size) / self.grid_count
                    order_size = adjust_quantity(sell_size, self.symbol_info)
            else:
                # Short bias
                if price > self.current_price:
                    # Sell orders above (increasing short position on rallies)
                    side = "sell"
                    order_size = self.grid_order_size  # Sell more as price rises
                else:
                    # Buy orders below (taking profit on shorts)
                    side = "buy"
                    # Calculate buy size based on a portion of position
                    buy_size = float(self.initial_position_size) / self.grid_count
                    order_size = adjust_quantity(buy_size, self.symbol_info)
            
            # Place the grid order
            try:
                logger.info(f"Placing {side} order: {order_size} @ {price}")
                order = self.exchange.create_order(
                    symbol=self.symbol,
                    side=side,
                    amount=float(order_size),
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
        
        logger.info(f"Successfully placed {orders_placed} directional grid orders")
        return orders_placed > 0
    
    def monitor_and_update(self):
        """Monitor open orders and update grid if needed."""
        try:
            # Get open orders
            open_orders = self.exchange.get_open_orders(self.symbol)
            open_order_ids = [order["id"] for order in open_orders]
            
            logger.info(f"Monitoring {len(open_orders)} open orders...")
            
            # Check for filled orders
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
                    
                    # Place a new order based on direction and strategy
                    self._handle_fill_directional(filled_order)
            
        except Exception as e:
            logger.error(f"Error monitoring orders: {str(e)}")
    
    def _handle_fill_directional(self, filled_order):
        """Handle a filled order based on directional strategy."""
        try:
            price = filled_order["price"]
            side = filled_order["side"]
            
            # For long bias:
            # - If buy order filled (dip), place a sell order higher
            # - If sell order filled (profit), place a buy order lower
            # For short bias:
            # - If sell order filled (rally), place a buy order lower
            # - If buy order filled (profit), place a sell order higher
            
            if self.direction == "long":
                if side == "buy":
                    # Buy order filled, place sell order above
                    new_side = "sell"
                    # Calculate profit target (e.g., 1% above buy price)
                    new_price = price * 1.01
                    new_price = float(adjust_price(new_price, self.symbol_info))
                    new_amount = filled_order["amount"]  # Sell same amount we bought
                else:
                    # Sell order filled, place buy order below
                    new_side = "buy"
                    # Calculate new buy price (e.g., 1% below sell price)
                    new_price = price * 0.99
                    new_price = float(adjust_price(new_price, self.symbol_info))
                    # Buy same amount we sold
                    new_amount = filled_order["amount"]
            else:  # short
                if side == "sell":
                    # Sell order filled, place buy order below
                    new_side = "buy"
                    # Calculate profit target (e.g., 1% below sell price)
                    new_price = price * 0.99
                    new_price = float(adjust_price(new_price, self.symbol_info))
                    new_amount = filled_order["amount"]  # Buy same amount we sold
                else:
                    # Buy order filled, place sell order above
                    new_side = "sell"
                    # Calculate new sell price (e.g., 1% above buy price)
                    new_price = price * 1.01
                    new_price = float(adjust_price(new_price, self.symbol_info))
                    # Sell same amount we bought
                    new_amount = filled_order["amount"]
            
            # Place the new order
            logger.info(f"Placing new {new_side} order: {new_amount} @ {new_price} after fill")
            
            order = self.exchange.create_order(
                symbol=self.symbol,
                side=new_side,
                amount=float(new_amount),
                price=new_price
            )
            
            if order and "id" in order:
                logger.info(f"New order placed: {order['id']}")
                self.active_positions[order["id"]] = order
            else:
                logger.error(f"Failed to place new {new_side} order")
                
        except Exception as e:
            logger.error(f"Error handling fill: {str(e)}")
    
    def calculate_profit(self):
        """Calculate total profit from filled orders."""
        # This is more complex for directional strategies
        # We need to account for the initial position and current market value
        
        total_profit = 0.0
        initial_capital = self.initial_position_capital
        
        # Sum up the profit/loss from individual trades
        for order in self.filled_orders:
            if order.get("is_initial", False):
                # Skip initial position establishment
                continue
                
            if self.direction == "long":
                if order["side"] == "buy":
                    # Buying more costs money
                    total_profit -= float(order["amount"]) * float(order["price"])
                else:  # sell
                    # Selling generates income
                    total_profit += float(order["amount"]) * float(order["price"])
            else:  # short
                if order["side"] == "sell":
                    # Selling generates income
                    total_profit += float(order["amount"]) * float(order["price"])
                else:  # buy
                    # Buying costs money
                    total_profit -= float(order["amount"]) * float(order["price"])
        
        # Get current market value of position
        # This would require a more complex position tracking mechanism
        # For simplicity, we're just reporting realized PnL from grid trades
        
        logger.info(f"Calculated grid trading profit: {total_profit:.8f} USDT")
        return total_profit
    
    def print_summary(self):
        """Print a summary of the grid bot status."""
        logger.info("\n=== Directional Grid Bot Summary ===")
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"Direction: {self.direction}")
        logger.info(f"Grid Range: {self.lower_price:.2f} to {self.upper_price:.2f}")
        logger.info(f"Grid Levels: {self.grid_count}")
        logger.info(f"Initial Position: {self.initial_position_size} {self.symbol.split('/')[0]}")
        logger.info(f"Grid Order Size: {self.grid_order_size} {self.symbol.split('/')[0]}")
        logger.info(f"Leverage: {self.leverage}x")
        logger.info(f"Active Orders: {len(self.active_positions)}")
        logger.info(f"Filled Orders: {len(self.filled_orders)}")
        
        profit = self.calculate_profit()
        logger.info(f"Trading Profit: {profit:.8f} USDT")
        
        # Print active positions if any
        if self.active_positions:
            logger.info("\nActive Orders:")
            for order_id, order in self.active_positions.items():
                logger.info(f"  {order['side']} {order['amount']} @ {order['price']} (ID: {order_id})")
    
    def cancel_all_orders(self):
        """Cancel all open orders."""
        logger.info("Cancelling all orders...")
        
        # Use exchange's cancel_all_orders method if available
        if hasattr(self.exchange, 'cancel_all_orders'):
            result = self.exchange.cancel_all_orders(self.symbol)
            if result:
                logger.info(f"Successfully cancelled all orders for {self.symbol}")
                self.active_positions = {}
            else:
                logger.error(f"Failed to cancel orders for {self.symbol}")
        else:
            # Manually cancel each order
            cancelled = 0
            for order_id in list(self.active_positions.keys()):
                try:
                    if hasattr(self.exchange, 'cancel_order'):
                        result = self.exchange.cancel_order(self.symbol, order_id)
                        if result:
                            logger.info(f"Cancelled order: {order_id}")
                            del self.active_positions[order_id]
                            cancelled += 1
                except Exception as e:
                    logger.error(f"Error cancelling order {order_id}: {str(e)}")
            
            logger.info(f"Cancelled {cancelled} orders")
    
    def start(self):
        """Start the directional grid bot."""
        logger.info(f"Starting {self.direction} grid bot for {self.symbol}")
        self.running = True
        
        # Initialize the grid
        if not self.initialize_grid():
            logger.error("Failed to initialize grid, stopping bot")
            self.running = False
            return
        
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
        logger.info(f"Stopping {self.direction} grid bot...")
        self.running = False
        
        # Cancel all orders
        self.cancel_all_orders()
        
        # Print final summary
        self.print_summary() 