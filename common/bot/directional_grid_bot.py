"""Directional grid trading bot with long or short bias."""
from typing import Dict, List, Optional, Literal
from common.exchange.base_client import BaseExchangeClient
from common.exchange.bybit_client import BybitClient
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
        initial_position_pct: float = 100.0,
        lower_price: float = 0.0,
        upper_price: float = 0.0
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
            lower_price: Lower price bound for grid
            upper_price: Upper price bound for grid
        """
        self.exchange = exchange
        self.symbol = symbol
        self.total_capital = capital  # Total capital in quote currency (e.g., USDT)
        self.grid_count = grid_count
        self.range_percentage = range_percentage
        self.direction = direction
        self.leverage = leverage
        self.initial_position_pct = initial_position_pct
        self.lower_price = lower_price
        self.upper_price = upper_price
        
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
        """Calculate grid price levels."""
        try:
            # Use explicitly provided lower/upper prices if available
            if self.lower_price > 0 and self.upper_price > 0:
                logger.info(f"Using provided price range: {self.lower_price} to {self.upper_price}")
                lower_price = self.lower_price
                upper_price = self.upper_price
            else:
                # Otherwise calculate based on range percentage
                logger.info(f"Calculating price range based on {self.range_percentage}% range")
                half_range = self.current_price * (self.range_percentage / 100) / 2
                lower_price = self.current_price - half_range
                upper_price = self.current_price + half_range
            
            # Calculate grid step size
            step = (upper_price - lower_price) / (self.grid_count - 1) if self.grid_count > 1 else 0
            
            # Create grid levels
            self.grid_levels = [lower_price + i * step for i in range(self.grid_count)]
            
            # Adjust prices according to exchange precision
            self.grid_levels = [float(adjust_price(price, self.symbol_info)) for price in self.grid_levels]
            logger.info(f"Grid levels: {self.grid_levels}")
            
            # Store the actual range used for reference
            self.lower_price = self.grid_levels[0]
            self.upper_price = self.grid_levels[-1]
            logger.info(f"Grid range: {self.lower_price} to {self.upper_price} with {self.grid_count} levels")
            
        except Exception as e:
            logger.error(f"Error calculating grid levels: {str(e)}")
            self.grid_levels = []
    
    def _calculate_order_size(self):
        """Calculate the order size based on capital allocation."""
        # Calculate capital per grid level
        capital_per_grid = self.total_capital / self.grid_count
        
        # Get current price for calculations
        current_price = self._get_current_price()
        
        # For BTCUSD inverse perpetual on Bybit:
        # 1. Capital is specified in USD
        # 2. Order size should be specified in contracts (where 1 contract = 1 USD)
        # 3. Need to convert USD value to appropriate contract size
        
        if 'USD' in self.symbol and self.symbol.endswith('USD') and isinstance(self.exchange, BybitClient):
            # For Bybit inverse contracts, we need to scale down the size appropriately
            # Contract value is 1 USD, but we need to consider the actual BTC amount
            
            # A reasonable size for BTCUSD (at ~80k USD/BTC) might be 100-200 contracts
            # Let's calculate a scaled size based on current price
            btc_amount = capital_per_grid / current_price  # Convert USD to BTC
            scaled_size = int(btc_amount * 10000)  # Scale to a reasonable contract size 
            
            # Ensure minimum size
            min_size = 100  # Reasonable minimum for BTCUSD
            order_size = max(scaled_size, min_size)
            
            logger.info(f"Bybit inverse contract detected. Adjusted size: {order_size} contracts")
            logger.info(f"BTC equivalent: ~{btc_amount:.6f} BTC")
        else:
            # For other contracts, use the original calculation
            if 'USD' in self.symbol and self.symbol.startswith('BTC'):
                # For inverse contracts, order size is directly in USD
                order_size = capital_per_grid
                logger.info(f"Inverse contract detected. Using {order_size} contracts per grid.")
            else:
                # For linear contracts, convert to the base currency
                avg_price = (self.lower_price + self.upper_price) / 2
                order_size = capital_per_grid / avg_price
        
        # Apply leverage
        order_size = order_size * self.leverage
        
        # Adjust order size for exchange precision requirements
        order_size = adjust_quantity(order_size, self.symbol_info)
        
        logger.info(f"Capital per grid: {capital_per_grid} -> Order size: {order_size}")
        return float(order_size)
    
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
        """Place an initial position based on the direction."""
        try:
            # Calculate initial position size
            position_size = float(self.order_size) * (self.initial_position_pct / 100.0)
            logger.info(f"Initial position size: {position_size}")
            
            # Get current market price
            price = self._get_current_price()
            
            # Determine side based on direction
            side = "buy" if self.direction == "long" else "sell"
            
            # Create a market order for the initial position
            logger.info(f"Placing initial {side} position of {position_size} at market price")
            
            # Use direct API call for market order
            result = self.exchange._create_order(
                symbol=self.symbol,
                side=side,
                order_type="Market",
                qty=position_size
            )
            
            if result:
                logger.info(f"Initial position placed successfully: {result}")
                self.has_initial_position = True
                
                # Add to tracking
                self.active_positions[result] = {
                    "price": price,
                    "side": side,
                    "amount": position_size,
                    "status": "filled",
                    "is_initial": True
                }
                
                return True
            else:
                logger.error("Failed to place initial position")
                return False
            
        except Exception as e:
            logger.error(f"Error placing initial position: {str(e)}")
            return False
    
    def place_grid_orders(self):
        """Place grid orders based on the calculated levels."""
        logger.info("Placing grid orders...")
        
        orders_placed = 0
        current_price = self._get_current_price()
        logger.info(f"Current price for grid placement: {current_price}")
        
        # For Bybit inverse contracts (BTCUSD), directly place orders across the grid
        try:
            # Place buy orders (below current price)
            for price in self.grid_levels:
                if price >= current_price:
                    continue  # Skip prices above current price for buy orders
                    
                side = "buy"
                amount = self.order_size
                logger.info(f"Placing {side} limit order at {price} for {amount}")
                
                try:
                    # Direct Bybit order placement for inverse contracts
                    order_id = self.exchange.create_limit_order(
                        symbol=self.symbol,
                        side=side,
                        amount=amount,
                        price=price
                    )
                    
                    if order_id:
                        logger.info(f"Buy order placed: {order_id}")
                        self.active_positions[order_id] = {
                            "price": float(price),
                            "side": side,
                            "amount": float(amount),
                            "status": "open"
                        }
                        orders_placed += 1
                    else:
                        logger.error(f"Failed to place {side} order at {price}")
                except Exception as e:
                    logger.error(f"Error placing {side} order at {price}: {str(e)}")
            
            # Place sell orders (above current price)
            for price in self.grid_levels:
                if price <= current_price:
                    continue  # Skip prices below current price for sell orders
                    
                side = "sell"
                amount = self.order_size
                logger.info(f"Placing {side} limit order at {price} for {amount}")
                
                try:
                    # Direct Bybit order placement for inverse contracts
                    order_id = self.exchange.create_limit_order(
                        symbol=self.symbol,
                        side=side,
                        amount=amount,
                        price=price
                    )
                    
                    if order_id:
                        logger.info(f"Sell order placed: {order_id}")
                        self.active_positions[order_id] = {
                            "price": float(price),
                            "side": side,
                            "amount": float(amount),
                            "status": "open"
                        }
                        orders_placed += 1
                    else:
                        logger.error(f"Failed to place {side} order at {price}")
                except Exception as e:
                    logger.error(f"Error placing {side} order at {price}: {str(e)}")
            
            logger.info(f"Placed {orders_placed} grid orders")
            return orders_placed > 0
            
        except Exception as e:
            logger.error(f"Error placing grid orders: {str(e)}")
            return False
    
    def monitor_and_update(self):
        """Monitor orders and update when necessary."""
        if not self.running:
            return
        
        try:
            # Get current price
            current_price = self._get_current_price()
            
            # Check for open orders
            open_orders = self.exchange.get_open_orders(self.symbol)
            if open_orders:
                logger.info(f"Open orders: {len(open_orders)}")
            else:
                logger.info("No open orders found!")
                
                # If no orders, try placing them again
                if not self.active_positions:
                    logger.warning("No active positions - attempting to place grid orders again")
                    self.start()
            
            # Get current positions
            positions = self.exchange.get_positions(self.symbol)
            if positions:
                logger.info(f"Current positions: {positions}")
                
            # Check for filled orders
            if open_orders:
                active_order_ids = {order['id'] for order in open_orders if 'id' in order}
                filled_order_ids = set(self.active_positions.keys()) - active_order_ids
                
                if filled_order_ids:
                    logger.info(f"Found {len(filled_order_ids)} filled orders")
                    
                    # Handle each filled order
                    for order_id in filled_order_ids:
                        if order_id in self.active_positions:
                            filled_order = self.active_positions[order_id]
                            self._handle_filled_order(order_id, filled_order)
        
        except Exception as e:
            logger.error(f"Error in monitor_and_update: {str(e)}")
    
    def _handle_filled_order(self, order_id, order_data):
        """Handle a filled order."""
        try:
            # Extract order details
            side = order_data.get("side")
            price = float(order_data.get("price"))
            amount = float(order_data.get("amount"))
            order_type = order_data.get("type")
            
            logger.info(f"Handling filled {side} order at price {price}")
            
            # Record the filled order
            self.filled_orders.append({
                "id": order_id,
                "side": side,
                "price": price,
                "amount": amount,
                "time": datetime.now(),
                "type": order_type
            })
            
            self.filled_order_ids.add(order_id)
            
            # Remove from active positions
            if order_id in self.active_positions:
                del self.active_positions[order_id]
            
            # Place new orders to maintain the grid
            if self.direction == "long":
                if side == "sell":  # Sell order filled (profit taken)
                    # Place a new sell order at the same price level
                    self._place_new_order("sell", price, amount, "take_profit")
                elif side == "buy":  # Buy order filled (re-entry)
                    # Place a new buy order at the same price level
                    self._place_new_order("buy", price, amount, "re_entry")
            else:  # short direction
                if side == "buy":  # Buy order filled (profit taken)
                    # Place a new buy order at the same price level
                    self._place_new_order("buy", price, amount, "take_profit")
                elif side == "sell":  # Sell order filled (re-entry)
                    # Place a new sell order at the same price level
                    self._place_new_order("sell", price, amount, "re_entry")
        
        except Exception as e:
            logger.error(f"Error handling filled order: {str(e)}")

    def _place_new_order(self, side, price, amount, order_type):
        """Place a new order after a fill."""
        try:
            logger.info(f"Placing new {side} order at {price} for {amount}")
            
            # Use the same price and amount as the filled order
            params = {}
            if order_type == "take_profit":
                params['reduce_only'] = True
            
            if hasattr(self.exchange, 'create_limit_order'):
                order_id = self.exchange.create_limit_order(
                    symbol=self.symbol,
                    side=side,
                    amount=amount,
                    price=price,
                    params=params
                )
            else:
                order_id = self.exchange.create_order(
                    symbol=self.symbol,
                    type="limit",
                    side=side,
                    amount=amount,
                    price=price
                )
            
            if order_id:
                logger.info(f"New order placed: {order_id}")
                self.active_positions[order_id] = {
                    "price": float(price),
                    "side": side,
                    "amount": float(amount),
                    "type": order_type,
                    "status": "open"
                }
            else:
                logger.error(f"Failed to place {side} order at {price}")
            
        except Exception as e:
            logger.error(f"Error placing {side} order: {str(e)}")
    
    def start(self):
        """Start the grid bot."""
        try:
            logger.info("Starting directional grid bot...")
            self.running = True
            
            # Ensure we have grid levels
            if not self.grid_levels:
                logger.error("No grid levels calculated. Cannot start bot.")
                return False
            
            # Cancel any existing orders for this symbol
            logger.info("Cancelling any existing orders...")
            self.exchange.cancel_all_orders(self.symbol)
            
            # SAFETY CHECK: Limit maximum order size for BTCUSD on Bybit
            if 'BTCUSD' in self.symbol and self.order_size > 1000:
                logger.warning(f"Order size {self.order_size} seems too large for {self.symbol}, limiting to 100")
                self.order_size = 100  # A more reasonable size for testing
            
            # Place initial position if configured
            if self.initial_position_pct > 0:
                logger.info(f"Placing initial position ({self.initial_position_pct}% of capital)...")
                if not self.place_initial_position():
                    logger.error("Failed to place initial position. Continuing without it.")
                else:
                    logger.info("Initial position placed successfully")
            
            # DEBUG: Show we're at the order placement stage 
            logger.info("=== PLACING GRID ORDERS ===")
            
            # Get current price for reference
            current_price = self._get_current_price()
            logger.info(f"Current price for order placement: {current_price}")
            
            # Place buy orders below current price
            buy_orders_placed = 0
            
            # Place sell orders above current price
            sell_orders_placed = 0
            
            # Place buy orders below current price
            for price in self.grid_levels:
                if price >= current_price:
                    continue  # Skip prices above current price for buy orders
                    
                logger.info(f"ATTEMPTING BUY ORDER at {price} for {self.order_size}")
                
                # Create buy order with direct API call
                result = self.exchange._create_order(
                    symbol=self.symbol,
                    side="buy",
                    order_type="Limit",
                    qty=self.order_size,
                    price=price
                )
                
                logger.info(f"BUY ORDER RESULT: {result}")
                
                if result:
                    logger.info(f"BUY ORDER SUCCESS at {price}")
                    buy_orders_placed += 1
            
            # Place sell orders above current price
            for price in self.grid_levels:
                if price <= current_price:
                    continue  # Skip prices below current price for sell orders
                    
                logger.info(f"ATTEMPTING SELL ORDER at {price} for {self.order_size}")
                
                # Create sell order with direct API call
                result = self.exchange._create_order(
                    symbol=self.symbol,
                    side="sell",
                    order_type="Limit",
                    qty=self.order_size,
                    price=price
                )
                
                logger.info(f"SELL ORDER RESULT: {result}")
                
                if result:
                    logger.info(f"SELL ORDER SUCCESS at {price}")
                    sell_orders_placed += 1
                
            logger.info(f"ORDER PLACEMENT SUMMARY: {buy_orders_placed} buy orders, {sell_orders_placed} sell orders")
            
            # Verify by getting open orders
            open_orders = self.exchange.get_open_orders(self.symbol)
            logger.info(f"VERIFICATION: Found {len(open_orders)} open orders")
            
            # Print initial summary
            self.print_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting grid bot: {str(e)}")
            logger.exception("Stack trace:")
            self.running = False
            return False
    
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
        """Calculate profit more accurately."""
        if not self.filled_orders:
            return 0.0
        
        # Sort orders by time
        sorted_orders = sorted(self.filled_orders, key=lambda x: x.get('time', datetime.min))
        
        total_profit = 0.0
        positions = []  # Track open positions
        
        if self.direction == "long":
            # Track initial position
            if self.has_initial_position:
                positions.append({
                    "price": float(self.initial_position_price),
                    "amount": float(self.initial_position_size)
                })
            
            # Process each order chronologically
            for order in sorted_orders:
                side = order.get("side")
                price = float(order.get("price", 0))
                amount = float(order.get("amount", 0))
                
                if side == "buy":
                    # Add to our positions
                    positions.append({"price": price, "amount": amount})
                elif side == "sell":
                    # Calculate profit against earliest open positions (FIFO)
                    remaining = amount
                    while remaining > 0 and positions:
                        pos = positions[0]
                        use_amount = min(remaining, pos["amount"])
                        
                        # Calculate profit for this portion
                        entry_price = pos["price"]
                        profit_per_unit = price - entry_price
                        profit = profit_per_unit * use_amount
                        total_profit += profit
                        
                        # Update or remove position
                        if use_amount >= pos["amount"]:
                            positions.pop(0)  # Position fully closed
                        else:
                            pos["amount"] -= use_amount  # Reduce position size
                        
                        remaining -= use_amount
        else:
            # Similar logic for short positions
            pass
        
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

    def _place_order(self, side, price, amount, order_type=None):
        """Place a limit order with proper error handling."""
        try:
            params = {}
            if order_type == "take_profit":
                params['reduce_only'] = True
            
            # Try the direct create_limit_order method first
            if hasattr(self.exchange, 'create_limit_order'):
                order_id = self.exchange.create_limit_order(
                    symbol=self.symbol,
                    side=side,
                    amount=amount,
                    price=price,
                    params=params
                )
            else:
                # Fall back to the general create_order method
                order_id = self.exchange.create_order(
                    symbol=self.symbol,
                    type="limit",
                    side=side,
                    amount=amount,
                    price=price,
                    params=params
                )
            
            return order_id
        except Exception as e:
            logger.error(f"Error placing {side} order at {price}: {str(e)}")
            return None 