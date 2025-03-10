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
            capital: Total capital to use (in quote currency)
            grid_count: Number of grid levels
            range_percentage: Price range percentage
            direction: Trading direction ('long' or 'short')
            leverage: Leverage to use (1 = no leverage)
            initial_position_pct: Percentage of capital to use for initial position (0-100)
        """
        self.exchange = exchange
        self.symbol = symbol
        self.total_capital = capital  # Total capital in quote currency (e.g., USDT)
        self.grid_count = grid_count
        self.range_percentage = range_percentage
        self.direction = direction
        self.leverage = leverage
        self.initial_position_pct = initial_position_pct
        
        # Get symbol information
        self.symbol_info = get_symbol_info(exchange, symbol)
        logger.info(f"Symbol info: {self.symbol_info}")
        
        # Initialize state
        self.active_positions = {}  # order_id -> order details
        self.filled_orders = []
        self.running = False
        
        # Calculate current price
        self.current_price = self._get_current_price()
        logger.info(f"Current price: {self.current_price}")
        
        # Set leverage
        self._set_leverage()
        
        # Calculate grid levels based on direction
        self._calculate_grid_levels()
        
        # Calculate order size (per grid)
        self._calculate_order_size()
        
        logger.info(f"Initialized {direction}biased grid bot for {symbol}")
        logger.info(f"Total capital: {self.total_capital} using {self.leverage}x leverage")
        logger.info(f"Grid range: {self.lower_price} to {self.upper_price} with {self.grid_count} levels")
        logger.info(f"Order size per grid: {self.order_size} ({self.total_capital / self.grid_count} divided by price)")
    
    def _calculate_grid_levels(self):
        """Calculate grid price levels based on direction."""
        half_range = self.range_percentage / 100.0 / 2
        
        if self.direction == "long":
            # For long bias, we want more buy levels below current price
            self.lower_price = self.current_price * (1 - half_range * 1.5)  # More room below
            self.upper_price = self.current_price * (1 + half_range * 0.5)  # Less room above
        else:  # short bias
            # For short bias, we want more sell levels above current price
            self.lower_price = self.current_price * (1 - half_range * 0.5)  # Less room below
            self.upper_price = self.current_price * (1 + half_range * 1.5)  # More room above
        
        # Calculate grid step
        self.grid_step = (self.upper_price - self.lower_price) / (self.grid_count - 1)
        
        # Generate grid levels
        self.grid_levels = []
        for i in range(self.grid_count):
            price = self.lower_price + i * self.grid_step
            adjusted_price = float(adjust_price(price, self.symbol_info))
            self.grid_levels.append(adjusted_price)
        
        logger.info(f"Grid levels: {self.grid_levels}")
    
    def _calculate_order_size(self):
        """Calculate the size of each grid order."""
        # Calculate the per-grid capital allocation
        capital_per_grid = self.total_capital / self.grid_count
        
        # Convert capital to base currency amount using average price
        avg_price = (self.lower_price + self.upper_price) / 2
        base_amount = capital_per_grid / avg_price
        
        # Apply leverage if using futures
        if self.leverage > 1:
            base_amount = base_amount * self.leverage
        
        # Adjust for precision requirements
        self.order_size = adjust_quantity(base_amount, self.symbol_info)
        
        logger.info(f"Capital per grid: {capital_per_grid} -> Order size: {self.order_size}")
        
        # Calculate initial position size
        if self.initial_position_pct > 0:
            self.initial_position_size = base_amount * (self.initial_position_pct / 100.0)
            self.initial_position_size = adjust_quantity(self.initial_position_size, self.symbol_info)
            logger.info(f"Initial position size: {self.initial_position_size} ({self.initial_position_pct}% of capital)")
        else:
            self.initial_position_size = 0
    
    def _get_current_price(self):
        """Get current market price."""
        ticker = self.exchange.get_ticker(self.symbol)
        if not ticker or "last" not in ticker:
            raise ValueError(f"Could not get current price for {self.symbol}")
        return ticker["last"]
    
    def _set_leverage(self):
        """Set leverage for the symbol if using futures."""
        if self.leverage > 1:
            result = self.exchange.set_leverage(self.symbol, self.leverage)
            logger.info(f"Set leverage to {self.leverage}x: {result}")
    
    def place_initial_position(self):
        """Place initial position if configured."""
        if self.initial_position_pct <= 0 or self.initial_position_size <= 0:
            logger.info("No initial position configured")
            return
        
        logger.info(f"Placing initial {self.direction} position of {self.initial_position_size}...")
        
        # For long bias, we buy; for short bias, we sell
        side = "buy" if self.direction == "long" else "sell"
        
        # Use market price for initial position
        try:
            order = self.exchange.create_market_order(
                symbol=self.symbol,
                side=side,
                amount=float(self.initial_position_size)
            )
            
            if order and "id" in order:
                logger.info(f"Initial position placed: {order['id']}")
                return True
            else:
                logger.error("Failed to place initial position")
                return False
        except Exception as e:
            logger.error(f"Error placing initial position: {str(e)}")
            return False
    
    def place_grid_orders(self):
        """Place grid orders according to the calculated levels."""
        logger.info("Placing grid orders...")
        
        orders_placed = 0
        
        for i, price in enumerate(self.grid_levels):
            # Determine order side based on direction and grid level
            if self.direction == "long":
                # For long bias: buy at lower levels, sell at higher levels
                side = "buy" if i < (self.grid_count // 2) else "sell"
            else:  # short bias
                # For short bias: sell at higher levels, buy at lower levels
                side = "sell" if i > (self.grid_count // 2) else "buy"
            
            try:
                logger.info(f"Placing {side} order at {price} for {self.order_size}")
                
                order = self.exchange.create_order(
                    symbol=self.symbol,
                    side=side,
                    amount=float(self.order_size),
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
        
        logger.info(f"Placed {orders_placed} grid orders")
        return orders_placed > 0
    
    def monitor_and_update(self):
        """Monitor orders and update grid as needed."""
        logger.info("Checking order status...")
        
        # Get current open orders
        open_orders = self.exchange.get_open_orders(self.symbol)
        open_order_ids = set(order["id"] for order in open_orders if "id" in order)
        
        # Check for filled orders
        filled_orders = []
        for order_id, order_info in list(self.active_positions.items()):
            if order_id not in open_order_ids:
                # Order not in open orders, assume it was filled
                logger.info(f"Order {order_id} was likely filled")
                filled_orders.append(order_info)
                del self.active_positions[order_id]
        
        # Handle filled orders
        for filled_order in filled_orders:
            self.filled_orders.append(filled_order)
            self._handle_fill_directional(filled_order)
    
    def _handle_fill_directional(self, filled_order):
        """Handle a filled order in directional grid strategy."""
        try:
            logger.info(f"Handling fill for {filled_order}")
            
            # Determine the new order side (opposite of filled order)
            filled_side = filled_order.get("side", "")
            new_side = "sell" if filled_side == "buy" else "buy"
            
            # Get fill price and amount
            fill_price = filled_order.get("price", 0)
            fill_amount = filled_order.get("amount", 0)
            
            # For directional strategy, we place the next order at a profit target
            if self.direction == "long":
                if new_side == "sell":
                    # If we're selling after a buy, place order higher
                    price_adjustment = 1.01  # 1% higher
                else:
                    # If we're buying after a sell, place order lower
                    price_adjustment = 0.99  # 1% lower
            else:  # short bias
                if new_side == "buy":
                    # If we're buying after a sell, place order lower
                    price_adjustment = 0.99  # 1% lower
                else:
                    # If we're selling after a buy, place order higher
                    price_adjustment = 1.01  # 1% higher
            
            # Calculate new price
            new_price = fill_price * price_adjustment
            new_price = float(adjust_price(new_price, self.symbol_info))
            
            # Use same amount as the filled order
            new_amount = fill_amount
            
            logger.info(f"Placing new {new_side} order at {new_price} for {new_amount}")
            
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
    
    def start(self):
        """Start the grid trading bot."""
        logger.info("Starting directional grid bot...")
        self.running = True
        
        # Place initial position if configured
        if self.initial_position_pct > 0:
            self.place_initial_position()
        
        # Place grid orders
        if not self.place_grid_orders():
            logger.error("Failed to place grid orders, stopping bot")
            self.running = False
            return
        
        logger.info("Grid bot started successfully")
        
        # Initial status summary
        self.print_summary()
    
    def stop(self):
        """Stop the grid trading bot."""
        logger.info("Stopping directional grid bot...")
        self.running = False
        
        # Cancel all open orders
        self.cancel_all_orders()
        
        # Final status
        self.print_summary()
    
    def cancel_all_orders(self):
        """Cancel all open orders."""
        logger.info("Cancelling all open orders...")
        result = self.exchange.cancel_all_orders(self.symbol)
        if result:
            logger.info("All orders cancelled successfully")
            self.active_positions = {}
        else:
            logger.error("Failed to cancel all orders")
    
    def calculate_profit(self):
        """Calculate current profit from filled orders."""
        if not self.filled_orders:
            return 0.0
        
        total_profit = 0.0
        
        # Group orders by side
        buys = [order for order in self.filled_orders if order.get("side") == "buy"]
        sells = [order for order in self.filled_orders if order.get("side") == "sell"]
        
        # Sort by price
        buys.sort(key=lambda x: x.get("price", 0))
        sells.sort(key=lambda x: x.get("price", 0))
        
        # Match buy and sell orders to calculate profit
        pairs_matched = min(len(buys), len(sells))
        
        if pairs_matched > 0:
            for i in range(pairs_matched):
                buy_price = buys[i]["price"]
                sell_price = sells[i]["price"]
                amount = float(self.order_size)
                
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
        logger.info(f"Total Capital: {self.total_capital} using {self.leverage}x leverage")
        logger.info(f"Order Size: {self.order_size} per grid")
        logger.info(f"Direction: {self.direction}")
        logger.info(f"Active Orders: {len(self.active_positions)}")
        logger.info(f"Filled Orders: {len(self.filled_orders)}")
        
        profit = self.calculate_profit()
        logger.info(f"Total Profit: {profit:.8f} USDT")
        
        # Print active positions if any
        if self.active_positions:
            logger.info("\nActive Positions:")
            for order_id, order in self.active_positions.items():
                logger.info(f"  {order['side']} {order['amount']} @ {order['price']} (ID: {order_id})") 