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
        initial_position_pct: float = 100.0
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
        self.filled_order_ids = set()  # Track IDs of filled orders
        self.running = False
        self.has_initial_position = False
        
        # Calculate current price
        self.current_price = self._get_current_price()
        logger.info(f"Current price: {self.current_price}")
        
        # Set leverage
        self._set_leverage()
        
        # Calculate grid levels based on direction
        self._calculate_grid_levels()
        
        # Calculate order size (per grid)
        self.order_size = self._calculate_order_size()
        
        # Calculate initial position size (if any)
        self.initial_position_size = float(self.order_size) * (self.initial_position_pct / 100.0)
        logger.info(f"Initial position size: {self.initial_position_size} ({self.initial_position_pct}% of capital)")
        
        logger.info(f"Initialized {direction}biased grid bot for {symbol}")
        logger.info(f"Total capital: {self.total_capital} using {self.leverage}x leverage")
        logger.info(f"Grid range: {self.lower_price} to {self.upper_price} with {self.grid_count} levels")
        logger.info(f"Order size per grid: {self.order_size} ({self.total_capital/self.grid_count} divided by price)")
    
    def _calculate_grid_levels(self):
        """Calculate grid price levels based on direction."""
        # For proper directional trading, we focus on the range above current price for long
        # and below current price for short
        
        if self.direction == "long":
            # For long bias, we place sell orders above current price
            # and buy orders at lower levels when sells are filled
            self.lower_price = self.current_price * (1 - self.range_percentage / 100.0)
            self.upper_price = self.current_price * (1 + self.range_percentage / 100.0)
        else:  # short bias
            # For short bias, we place buy orders below current price
            # and sell orders at higher levels when buys are filled
            self.lower_price = self.current_price * (1 - self.range_percentage / 100.0)
            self.upper_price = self.current_price * (1 + self.range_percentage / 100.0)
        
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
        """Calculate the order size based on capital allocation."""
        # Calculate capital per grid level
        capital_per_grid = self.total_capital / self.grid_count
        
        # For inverse contracts like BTCUSD, order size is in contracts
        # 1 contract = 1 USD / price (for BTCUSD)
        avg_price = (self.lower_price + self.upper_price) / 2
        
        # For BTCUSD inverse perpetual, we need to convert USD to contract quantity
        # The contract value is 1 USD, so the number of contracts is simply the capital amount
        if 'USD' in self.symbol and self.symbol.startswith('BTC'):
            # For inverse contracts, order size is directly in USD
            order_size = capital_per_grid
            logger.info(f"Inverse contract detected. Using {order_size} contracts per grid.")
        else:
            # For linear contracts, we need to convert to the base currency
            order_size = capital_per_grid / avg_price
        
        # Apply leverage
        order_size = order_size * self.leverage
        
        # Adjust order size for exchange precision requirements
        order_size = adjust_quantity(order_size, self.symbol_info)
        
        logger.info(f"Capital per grid: {capital_per_grid} -> Order size: {order_size}")
        return float(order_size)  # Ensure it's a float, not a string
    
    def _get_current_price(self):
        """Get current market price."""
        ticker = self.exchange.get_ticker(self.symbol)
        if not ticker or "last" not in ticker:
            raise ValueError(f"Could not get current price for {self.symbol}")
        return float(ticker["last"])
    
    def _set_leverage(self):
        """Set leverage for the symbol if using futures."""
        if self.leverage > 1:
            result = self.exchange.set_leverage(self.symbol, self.leverage)
            logger.info(f"Set leverage to {self.leverage}x: {result}")
    
    def place_initial_position(self):
        """Place initial position if configured."""
        if self.initial_position_pct <= 0 or self.initial_position_size <= 0:
            logger.info("No initial position configured")
            return False
        
        # For directional trading, we take a full position at the start
        # in the direction of our bias
        side = "buy" if self.direction == "long" else "sell"
        
        logger.info(f"Placing initial {self.direction} position of {self.initial_position_size}...")
        
        # Use market price for initial position
        order = self.exchange.create_market_order(
            symbol=self.symbol,
            side=side,
            amount=float(self.initial_position_size)
        )
        
        if order and "id" in order:
            logger.info(f"Initial position placed: {order['id']}")
            self.has_initial_position = True
            return True
        else:
            logger.error("Failed to place initial position")
            return False
    
    def place_grid_orders(self):
        """Place grid orders according to the directional strategy."""
        logger.info("Placing grid orders...")
        
        # For directional trading:
        # - Long bias: Place SELL orders above entry (to take profit)
        # - Short bias: Place BUY orders below entry (to take profit)
        
        orders_placed = 0
        
        if self.direction == "long":
            # For long bias, place sell orders at higher prices
            for i in range(self.grid_count):
                price_level = self.grid_levels[i]
                
                # Only place sell orders above current price
                if price_level > self.current_price:
                    logger.info(f"Placing sell order at {price_level} for {self.order_size}")
                    
                    order = self.exchange.create_order(
                        symbol=self.symbol,
                        side="sell",
                        amount=float(self.order_size),
                        price=price_level
                    )
                    
                    if order and "id" in order:
                        logger.info(f"Order placed: {order['id']}")
                        self.active_positions[order["id"]] = {
                            "id": order["id"],
                            "side": "sell",
                            "price": price_level,
                            "amount": float(self.order_size),
                            "status": "open",
                            "type": "take_profit"
                        }
                        orders_placed += 1
                    else:
                        logger.error(f"Failed to place sell order at {price_level}")
        else:
            # For short bias, place buy orders at lower prices
            for i in range(self.grid_count):
                price_level = self.grid_levels[i]
                
                # Only place buy orders below current price
                if price_level < self.current_price:
                    logger.info(f"Placing buy order at {price_level} for {self.order_size}")
                    
                    order = self.exchange.create_order(
                        symbol=self.symbol,
                        side="buy",
                        amount=float(self.order_size),
                        price=price_level
                    )
                    
                    if order and "id" in order:
                        logger.info(f"Order placed: {order['id']}")
                        self.active_positions[order["id"]] = {
                            "id": order["id"],
                            "side": "buy",
                            "price": price_level,
                            "amount": float(self.order_size),
                            "status": "open",
                            "type": "take_profit"
                        }
                        orders_placed += 1
                    else:
                        logger.error(f"Failed to place buy order at {price_level}")
        
        logger.info(f"Placed {orders_placed} grid orders")
        return orders_placed > 0
    
    def monitor_and_update(self):
        """Monitor and update the grid positions."""
        try:
            # Get current price
            current_price = self._get_current_price()
            
            # Get all open orders
            open_orders = self.exchange.get_open_orders(self.symbol)
            open_order_ids = {str(order.get('id', '')) for order in open_orders if order.get('id')}
            
            # Check for filled orders
            for order_id, order_data in list(self.active_positions.items()):
                if str(order_id) not in open_order_ids and order_id not in self.filled_order_ids:
                    logger.info(f"Order {order_id} appears to be filled")
                    # Save to filled orders and remove from active
                    self.filled_orders.append(order_data)
                    self.filled_order_ids.add(order_id)
                    del self.active_positions[order_id]
                    
                    # Handle the filled order based on direction
                    self._handle_filled_order(order_data, current_price)
            
            # Create new orders if needed
            if self.has_initial_position and len(self.active_positions) < self.grid_count / 2:
                logger.info("Adding more grid orders...")
                self.place_grid_orders()
            
        except Exception as e:
            logger.error(f"Error monitoring orders: {str(e)}")
    
    def _handle_filled_order(self, order_data, current_price):
        """Handle a filled order based on directional strategy."""
        try:
            side = order_data.get("side")
            price = order_data.get("price")
            amount = order_data.get("amount")
            
            logger.info(f"Handling filled {side} order at price {price}")
            
            if self.direction == "long":
                if side == "sell":
                    # Sell order filled (profit taken), place a buy order at a lower price
                    # Find an appropriate price level below current price
                    for level in self.grid_levels:
                        if level < current_price and level < price:
                            new_price = level
                            logger.info(f"Placing new buy order at {new_price} for {amount}")
                            
                            order = self.exchange.create_order(
                                symbol=self.symbol,
                                side="buy",
                                amount=float(amount),
                                price=new_price
                            )
                            
                            if order and "id" in order:
                                logger.info(f"New order placed: {order['id']}")
                                self.active_positions[order["id"]] = {
                                    "id": order["id"],
                                    "side": "buy",
                                    "price": new_price,
                                    "amount": float(amount),
                                    "status": "open",
                                    "type": "reentry"
                                }
                                break
                            else:
                                logger.error(f"Failed to place buy order at {new_price}")
                
                elif side == "buy":
                    # Buy order filled (reentry), place a sell order at a higher price
                    for level in self.grid_levels:
                        if level > current_price and level > price:
                            new_price = level
                            logger.info(f"Placing new sell order at {new_price} for {amount}")
                            
                            order = self.exchange.create_order(
                                symbol=self.symbol,
                                side="sell",
                                amount=float(amount),
                                price=new_price
                            )
                            
                            if order and "id" in order:
                                logger.info(f"New order placed: {order['id']}")
                                self.active_positions[order["id"]] = {
                                    "id": order["id"],
                                    "side": "sell",
                                    "price": new_price,
                                    "amount": float(amount),
                                    "status": "open",
                                    "type": "take_profit"
                                }
                                break
                            else:
                                logger.error(f"Failed to place sell order at {new_price}")
            
            else:  # short direction
                # Implement similar logic for short direction
                pass
                
        except Exception as e:
            logger.error(f"Error handling filled order: {str(e)}")
    
    def start(self):
        """Start the grid trading bot."""
        logger.info("Starting directional grid bot...")
        self.running = True
        
        # Place initial position if configured
        if self.initial_position_pct > 0:
            if not self.place_initial_position():
                logger.error("Failed to place initial position, stopping bot")
                self.running = False
                return False
        
        # Place grid orders
        if not self.place_grid_orders():
            logger.error("Failed to place grid orders, stopping bot")
            self.running = False
            return False
        
        logger.info("Grid bot started successfully")
        
        # Initial status summary
        self.print_summary()
        return True
    
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
        
        # For directional trading, profit calculation is different
        # We track buy-sell pairs based on the direction
        if self.direction == "long":
            # For long bias, profit is from selling higher than buying
            for order in self.filled_orders:
                if order.get("side") == "sell" and order.get("type") == "take_profit":
                    # This is a profit-taking sell
                    sell_price = order.get("price", 0)
                    amount = order.get("amount", 0)
                    
                    # Assume initial position was at current_price (simplified)
                    # In a real implementation, we'd track the actual buy price for each position
                    buy_price = self.current_price  
                    profit = (sell_price - buy_price) * amount
                    total_profit += profit
        else:
            # For short bias, profit is from buying lower than selling
            for order in self.filled_orders:
                if order.get("side") == "buy" and order.get("type") == "take_profit":
                    # This is a profit-taking buy
                    buy_price = order.get("price", 0)
                    amount = order.get("amount", 0)
                    
                    # Assume initial position was at current_price (simplified)
                    sell_price = self.current_price
                    profit = (sell_price - buy_price) * amount
                    total_profit += profit
        
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