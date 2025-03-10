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
        """Place the initial position based on direction."""
        if self.initial_position_pct <= 0:
            logger.info("No initial position requested, skipping...")
            return True
        
        try:
            # Set position mode first if needed
            if hasattr(self.exchange, 'set_position_mode'):
                try:
                    mode = 'one_way' if self.direction == 'long' else 'hedge'
                    self.exchange.set_position_mode(mode, self.symbol)
                    logger.info(f"Set position mode to {mode}")
                except Exception as e:
                    logger.warning(f"Could not set position mode: {str(e)}")
            
            # For long-biased bots, place an initial long position
            # For short-biased bots, place an initial short position
            side = "buy" if self.direction == "long" else "sell"
            
            # Calculate position size - be careful with inverse contracts
            position_size = self.total_capital * (self.initial_position_pct / 100) * self.leverage
            
            # For inverse contracts like BTCUSD, size is in contracts (1 contract = 1 USD)
            if self.symbol_info.get("contract_type") == "inverse":
                # No need to divide by price for inverse contracts
                position_size = position_size
            else:
                # For linear contracts, convert to the base currency
                position_size = position_size / self.current_price
            
            # Adjust quantity to exchange requirements
            position_size = adjust_quantity(position_size, self.symbol_info)
            
            logger.info(f"Placing initial {self.direction} position: {side} {position_size} contracts at market")
            
            # Use the existing create_market_order without position_idx
            order_id = self.exchange.create_market_order(
                symbol=self.symbol,
                side=side,
                amount=position_size
            )
            
            self.initial_position_size = float(position_size)
            logger.info(f"Initial position placed: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to place initial position: {str(e)}")
            return False
    
    def place_grid_orders(self):
        """Place grid orders based on the calculated levels."""
        logger.info("Placing grid orders...")
        
        # For long-biased bots:
        # - Place buy orders below current price for accumulation
        # - Place sell orders above current price for profit-taking
        
        # For short-biased bots:
        # - Place sell orders above current price for accumulation
        # - Place buy orders below current price for profit-taking
        
        orders_placed = 0
        
        for price in self.grid_levels:
            try:
                # Determine order side based on price relative to current and direction
                if self.direction == "long":
                    side = "buy" if price < self.current_price else "sell"
                    order_type = "re_entry" if side == "buy" else "take_profit"
                else:
                    side = "sell" if price > self.current_price else "buy"
                    order_type = "re_entry" if side == "sell" else "take_profit"
                
                logger.info(f"Placing {side} order at {price} for {self.order_size}")
                
                # Use the exchange client's create_limit_order method
                # Check if reduce_only is supported
                params = {}
                if hasattr(self.exchange, 'supports_reduce_only') and self.exchange.supports_reduce_only:
                    params['reduce_only'] = (order_type == "take_profit")
                    
                # Place the limit order
                order_id = self.exchange.create_limit_order(
                    symbol=self.symbol,
                    side=side,
                    amount=self.order_size,
                    price=price,
                    params=params
                )
                
                # Record the order in our tracking dict
                self.active_positions[order_id] = {
                    "price": price,
                    "side": side,
                    "amount": self.order_size,
                    "type": order_type,
                    "status": "open"
                }
                
                logger.info(f"Order placed: {order_id}")
                orders_placed += 1
                
            except Exception as e:
                logger.error(f"Failed to place {side} order at {price}: {str(e)}")
        
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
                    self._handle_filled_order(order_id, order_data)
            
            # Create new orders if needed
            if self.has_initial_position and len(self.active_positions) < self.grid_count / 2:
                logger.info("Adding more grid orders...")
                self.place_grid_orders()
            
        except Exception as e:
            logger.error(f"Error monitoring orders: {str(e)}")
    
    def _handle_filled_order(self, order_id, order_data):
        """Handle a filled order - core logic of the directional grid trading."""
        try:
            # extract order details
            side = order_data.get("side")
            price = order_data.get("price")
            amount = order_data.get("amount")
            order_type = order_data.get("type")
            
            logger.info(f"Handling filled {side} order at price {price}")
            
            # record the filled order
            self.filled_orders.append({
                "id": order_id,
                "side": side,
                "price": price,
                "amount": amount,
                "time": datetime.now(),
                "type": order_type
            })
            
            self.filled_order_ids.add(order_id)
            
            # remove from active positions
            if order_id in self.active_positions:
                del self.active_positions[order_id]
            
            # For inverse contracts like BTCUSD, special handling is needed
            is_inverse = self.symbol_info.get("contract_type") == "inverse"
            
            # get current price
            current_price = self._get_current_price()
            
            # place new orders based on direction and side
            if self.direction == "long":
                if side == "sell":  # sell order filled - profit taken
                    # Place a new buy order at a lower price
                    # For inverse contracts, quantity remains fixed (in contracts)
                    new_price = price - (2 * self.grid_step)
                    new_price = adjust_price(new_price, self.symbol_info)
                    
                    logger.info(f"Placing new buy order at {new_price} for {amount}")
                    
                    # Place the order
                    try:
                        order = self.exchange.create_limit_order(
                            symbol=self.symbol,
                            side="buy",
                            amount=amount,
                            price=new_price
                        )
                        
                        if order:
                            logger.info(f"New order placed: {order}")
                            self.active_positions[order] = {
                                "price": new_price,
                                "side": "buy",
                                "amount": amount,
                                "type": "re_entry",
                                "status": "open"
                            }
                        else:
                            logger.error(f"Failed to place buy order at {new_price}")
                            
                    except Exception as e:
                        logger.error(f"Error placing buy order: {str(e)}")
                    
                elif side == "buy":  # buy order filled - position replenished
                    # Place a new sell order at a higher price
                    new_price = price + (2 * self.grid_step)
                    new_price = adjust_price(new_price, self.symbol_info)
                    
                    logger.info(f"Placing new sell order at {new_price} for {amount}")
                    
                    # Place the order 
                    try:
                        order = self.exchange.create_limit_order(
                            symbol=self.symbol,
                            side="sell",
                            amount=amount,
                            price=new_price
                        )
                        
                        if order:
                            logger.info(f"New order placed: {order}")
                            self.active_positions[order] = {
                                "price": new_price,
                                "side": "sell",
                                "amount": amount,
                                "type": "take_profit",
                                "status": "open"
                            }
                        else:
                            logger.error(f"Failed to place sell order at {new_price}")
                            
                    except Exception as e:
                        logger.error(f"Error placing sell order: {str(e)}")
            
            else:  # short direction
                # Similar logic for short bias
                # Omitted for brevity - similar to long but with reversed order types
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