#!/usr/bin/env python
"""
Advanced Grid Trading Bot for Binance Futures
- Creates and monitors grid orders
- Tracks filled orders
- Rebalances grid when orders are filled
"""
import sys
import os
import argparse
import logging
from datetime import datetime
import time
import math
import requests
import json
import threading
import signal

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.exchange.futures_client import FuturesExchangeClient
from scripts.grid_trade_monitor import (
    get_binance_server_time, 
    get_binance_futures_symbol_info, 
    get_filter_value,
    format_price,
    format_quantity,
    get_account_positions
)
from common.exchange.factory import ExchangeFactory
from common.bot.grid_bot import GridBot
from common.utils.logger import setup_logger

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GridTrader:
    def __init__(self, api_key, api_secret, symbol, capital, 
                 grid_count=3, range_percentage=2.0, testnet=True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.symbol = symbol
        self.capital = capital
        self.grid_count = grid_count
        self.range_percentage = range_percentage
        self.testnet = testnet
        
        # Initialize exchange client
        self.exchange = FuturesExchangeClient(api_key, api_secret, testnet=testnet)
        
        # Grid state
        self.grid_orders = []
        self.filled_orders = []
        self.active_positions = []
        
        # Grid parameters
        self.current_price = None
        self.lower_price = None
        self.upper_price = None
        self.price_step = None
        self.usdt_per_grid = None
        
        # Symbol constraints
        self.symbol_info = None
        self.min_qty = None
        self.step_size = None
        self.tick_size = None
        self.min_notional = None
        
        # Running flag
        self.running = False
    
    def initialize(self):
        """Initialize the grid trader with market data"""
        # Get current price
        self.current_price = self.exchange.get_ticker(self.symbol)
        if not self.current_price:
            logger.error(f"Failed to get current price for {self.symbol}")
            return False
        
        logger.info(f"Current price: {self.current_price}")
        
        # Get symbol info
        self.symbol_info = get_binance_futures_symbol_info(self.symbol, testnet=self.testnet)
        if not self.symbol_info:
            logger.error(f"Failed to get symbol info for {self.symbol}")
            return False
        
        # Extract important values
        self.min_qty = float(get_filter_value(self.symbol_info, 'LOT_SIZE', 'minQty') or 0.001)
        self.step_size = float(get_filter_value(self.symbol_info, 'LOT_SIZE', 'stepSize') or 0.001)
        self.tick_size = float(get_filter_value(self.symbol_info, 'PRICE_FILTER', 'tickSize') or 0.1)
        
        # Handle MIN_NOTIONAL filter
        min_notional_value = get_filter_value(self.symbol_info, 'MIN_NOTIONAL', 'notional')
        if min_notional_value is None:
            min_notional_value = get_filter_value(self.symbol_info, 'MIN_NOTIONAL', 'minNotional')
        
        self.min_notional = float(min_notional_value or 100.0)
        
        logger.info(f"Symbol: {self.symbol_info['symbol']} (Status: {self.symbol_info['status']})")
        logger.info(f"Min Quantity: {self.min_qty}, Step Size: {self.step_size}")
        logger.info(f"Tick Size: {self.tick_size}")
        logger.info(f"Min Notional: {self.min_notional}")
        
        # Calculate grid parameters
        range_factor = self.range_percentage / 100
        self.lower_price = self.current_price * (1 - range_factor)
        self.upper_price = self.current_price * (1 + range_factor)
        
        # Format prices
        self.lower_price = float(format_price(self.lower_price, self.tick_size))
        self.upper_price = float(format_price(self.upper_price, self.tick_size))
        
        logger.info(f"Grid range: {self.lower_price} to {self.upper_price}")
        
        # Calculate how many grids we can create
        max_grids = math.floor(self.capital / self.min_notional)
        if max_grids < 1:
            logger.error(f"Not enough capital to create even 1 grid. Need at least {self.min_notional} USDT.")
            return False
        
        if max_grids < self.grid_count:
            logger.warning(f"Can only create {max_grids} grids with {self.capital} USDT")
            self.grid_count = max_grids
        
        # Calculate USDT per grid
        self.usdt_per_grid = self.capital / self.grid_count
        self.usdt_per_grid = max(self.usdt_per_grid, self.min_notional)
        
        logger.info(f"Using {self.grid_count} grids with {self.usdt_per_grid:.2f} USDT per grid")
        
        # Calculate grid levels
        grid_steps = self.grid_count + 1
        self.price_step = (self.upper_price - self.lower_price) / grid_steps
        
        return True
    
    def create_grid_orders(self):
        """Create grid orders"""
        logger.info("Creating grid orders...")
        
        created_orders = []
        for i in range(self.grid_count):
            # Calculate grid price
            grid_price = self.lower_price + self.price_step * (i + 1)
            grid_price_str = format_price(grid_price, self.tick_size)
            
            # Alternate buy/sell orders
            side = "buy" if i % 2 == 0 else "sell"
            
            # Calculate quantity
            coin_quantity = self.usdt_per_grid / float(grid_price_str)
            qty_needed = max(coin_quantity, self.min_notional / float(grid_price_str))
            order_size_str = format_quantity(qty_needed, self.step_size, self.min_qty)
            
            # Calculate actual notional value
            notional = float(order_size_str) * float(grid_price_str)
            
            logger.info(f"Creating {side} order at {grid_price_str} for {order_size_str} BTC (notional: {notional:.2f} USDT)")
            
            # Ensure we meet min notional
            if notional < self.min_notional:
                logger.warning(f"Order notional too small. Adding buffer...")
                qty_needed = self.min_notional / float(grid_price_str) * 1.01  # Add 1% buffer
                order_size_str = format_quantity(qty_needed, self.step_size, self.min_qty)
                notional = float(order_size_str) * float(grid_price_str)
                logger.info(f"New order: {order_size_str} BTC (notional: {notional:.2f} USDT)")
            
            # Create order
            try:
                order = self.exchange.create_order(
                    symbol=self.symbol,
                    side=side,
                    amount=float(order_size_str),
                    price=float(grid_price_str)
                )
                
                if order:
                    logger.info(f"Created order: {order}")
                    created_orders.append(order)
                    
                    # Add to grid orders
                    grid_details = {
                        'id': order['id'],
                        'side': side,
                        'price': float(grid_price_str),
                        'amount': float(order_size_str),
                        'notional': notional,
                        'grid_index': i
                    }
                    self.grid_orders.append(grid_details)
            except Exception as e:
                logger.error(f"Error creating order: {str(e)}")
        
        logger.info(f"Created {len(created_orders)} out of {self.grid_count} orders")
        return len(created_orders) > 0
    
    def monitor_orders(self):
        """Monitor orders and positions"""
        try:
            # Get open orders
            open_orders = self.exchange.get_open_orders(self.symbol)
            open_order_ids = set(order['id'] for order in open_orders) if open_orders else set()
            
            logger.info(f"Open orders: {len(open_orders) if open_orders else 0}")
            for order in open_orders or []:
                logger.info(f"  Order {order['id']}: {order['side']} {order['amount']} @ {order['price']}")
            
            # Check for filled orders
            filled_orders = []
            for grid_order in self.grid_orders:
                if grid_order['id'] not in open_order_ids:
                    logger.info(f"Order {grid_order['id']} filled or canceled!")
                    filled_orders.append(grid_order)
            
            # Remove filled orders from grid orders
            for filled_order in filled_orders:
                self.grid_orders = [order for order in self.grid_orders if order['id'] != filled_order['id']]
                self.filled_orders.append(filled_order)
            
            # Get positions
            positions = get_account_positions(self.api_key, self.api_secret, testnet=self.testnet)
            self.active_positions = []
            
            if positions:
                for pos in positions:
                    if float(pos.get('positionAmt', 0)) != 0:
                        self.active_positions.append(pos)
                
                if self.active_positions:
                    logger.info("Active positions:")
                    for pos in self.active_positions:
                        symbol = pos.get('symbol', '')
                        amount = float(pos.get('positionAmt', 0))
                        entry_price = float(pos.get('entryPrice', 0))
                        pnl = float(pos.get('unRealizedProfit', 0))
                        
                        logger.info(f"  {symbol}: {amount} @ {entry_price} (PnL: {pnl:.2f} USDT)")
                else:
                    logger.info("No active positions")
            
            # Rebalance grid if needed
            if filled_orders and len(self.grid_orders) < self.grid_count:
                logger.info("Rebalancing grid...")
                self.rebalance_grid()
        
        except Exception as e:
            logger.error(f"Error monitoring orders: {str(e)}")
    
    def rebalance_grid(self):
        """Rebalance the grid after orders are filled"""
        # Get current price
        current_price = self.exchange.get_ticker(self.symbol)
        if not current_price:
            logger.error("Failed to get current price for rebalancing")
            return
        
        logger.info(f"Current price for rebalancing: {current_price}")
        
        # Calculate how many orders we need to create
        orders_needed = self.grid_count - len(self.grid_orders)
        if orders_needed <= 0:
            return
        
        logger.info(f"Creating {orders_needed} new orders to rebalance grid")
        
        # Create new orders based on the current price and existing grid
        for i in range(orders_needed):
            # Determine if we need a buy or sell order based on price position
            existing_prices = [order['price'] for order in self.grid_orders]
            
            if not existing_prices:
                # If no orders left, create a new grid centered on current price
                range_factor = self.range_percentage / 200  # Half the range
                new_lower = current_price * (1 - range_factor)
                new_upper = current_price * (1 + range_factor)
                price_step = (new_upper - new_lower) / 2
                
                if i == 0:
                    grid_price = new_lower + price_step
                    side = "buy"
                else:
                    grid_price = new_upper - price_step
                    side = "sell"
            else:
                # Find optimal price level based on gaps in the grid
                avg_price = sum(existing_prices) / len(existing_prices)
                
                if current_price > avg_price:
                    # Create more sell orders above
                    side = "sell"
                    grid_price = max(existing_prices) + self.price_step
                else:
                    # Create more buy orders below
                    side = "buy"
                    grid_price = min(existing_prices) - self.price_step
            
            # Format price
            grid_price_str = format_price(grid_price, self.tick_size)
            
            # Calculate quantity
            coin_quantity = self.usdt_per_grid / float(grid_price_str)
            qty_needed = max(coin_quantity, self.min_notional / float(grid_price_str))
            order_size_str = format_quantity(qty_needed, self.step_size, self.min_qty)
            
            # Calculate actual notional value
            notional = float(order_size_str) * float(grid_price_str)
            
            logger.info(f"Creating rebalance {side} order at {grid_price_str} for {order_size_str} BTC (notional: {notional:.2f} USDT)")
            
            # Ensure we meet min notional
            if notional < self.min_notional:
                qty_needed = self.min_notional / float(grid_price_str) * 1.01  # Add 1% buffer
                order_size_str = format_quantity(qty_needed, self.step_size, self.min_qty)
                notional = float(order_size_str) * float(grid_price_str)
            
            # Create order
            try:
                order = self.exchange.create_order(
                    symbol=self.symbol,
                    side=side,
                    amount=float(order_size_str),
                    price=float(grid_price_str)
                )
                
                if order:
                    logger.info(f"Created rebalance order: {order}")
                    
                    # Add to grid orders
                    grid_details = {
                        'id': order['id'],
                        'side': side,
                        'price': float(grid_price_str),
                        'amount': float(order_size_str),
                        'notional': notional,
                        'grid_index': i
                    }
                    self.grid_orders.append(grid_details)
            except Exception as e:
                logger.error(f"Error creating rebalance order: {str(e)}")
    
    def start(self):
        """Start grid trading."""
        logger.info(f"Starting grid trading for {self.symbol}")
        
        # Set leverage to 2x
        if self.exchange.set_leverage(self.symbol, 2):
            logger.info(f"Set leverage to 2x for {self.symbol}")
        else:
            logger.warning(f"Failed to set leverage to 2x for {self.symbol}. Using account default.")
        
        # Initialize
        if not self.initialize():
            logger.error("Failed to initialize grid trader")
            return
        
        # Create initial grid orders
        if not self.create_grid_orders():
            logger.error("Failed to create grid orders")
            return
        
        self.running = True
        logger.info("Grid trader started! Press Ctrl+C to cancel orders and exit.")
        
        # Monitor loop
        try:
            while self.running:
                self.monitor_orders()
                time.sleep(10)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the grid trader"""
        logger.info("Stopping grid trader...")
        self.running = False
        
        # Cancel all orders
        try:
            logger.info("Cancelling all orders...")
            self.exchange.cancel_all_orders(self.symbol)
            logger.info("Orders cancelled.")
        except Exception as e:
            logger.error(f"Error cancelling orders: {str(e)}")
        
        logger.info("Grid trader stopped.")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print trading summary"""
        logger.info("=== Grid Trading Summary ===")
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"Capital: {self.capital} USDT")
        logger.info(f"Grid Range: {self.lower_price} to {self.upper_price}")
        logger.info(f"Grid Levels: {self.grid_count}")
        logger.info(f"Filled Orders: {len(self.filled_orders)}")
        
        if self.filled_orders:
            logger.info("Order History:")
            for order in self.filled_orders:
                logger.info(f"  {order['side'].upper()} {order['amount']} @ {order['price']}")
        
        # Calculate estimated P&L if possible
        if self.active_positions:
            total_pnl = sum(float(pos.get('unRealizedProfit', 0)) for pos in self.active_positions)
            logger.info(f"Unrealized P&L: {total_pnl:.2f} USDT")

def main():
    parser = argparse.ArgumentParser(description='Advanced Grid Trading Bot')
    parser.add_argument('exchange', type=str, choices=['binance', 'hyperliquid'],
                      help='Exchange to trade on (binance or hyperliquid)')
    parser.add_argument('api_key', type=str, help='API Key')
    parser.add_argument('api_secret', type=str, help='API Secret')
    parser.add_argument('pair', type=str, help='Trading pair')
    parser.add_argument('capital', type=float, help='Trading capital')
    parser.add_argument('--grids', type=int, default=5, help='Number of grids')
    parser.add_argument('--range-percentage', type=float, default=2.0,
                      help='Grid range as percentage')
    parser.add_argument('--testnet', action='store_true', help='Use testnet')
    
    args = parser.parse_args()
    
    # Create exchange client
    try:
        exchange = ExchangeFactory.create_exchange(
            args.exchange,
            args.api_key,
            args.api_secret,
            args.testnet
        )
        
        # Create and run grid bot
        bot = GridBot(
            exchange=exchange,
            symbol=args.pair,
            capital=args.capital,
            grid_count=args.grids,
            range_percentage=args.range_percentage
        )
        
        bot.start()
        
    except KeyboardInterrupt:
        logger.info("Shutting down bot...")
        if 'bot' in locals():
            bot.stop()
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 