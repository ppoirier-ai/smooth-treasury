#!/usr/bin/env python
"""
Run a directional grid trading bot (long or short) on Bybit
"""
import sys
import os
import time
from datetime import datetime
import argparse
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.bot.directional_grid_bot import DirectionalGridBot
from common.exchange.bybit_client import BybitClient
from common.utils.logger import setup_logger

logger = setup_logger(__name__)

# Add at the beginning of run script
logging.basicConfig(level=logging.INFO)

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Run a directional grid trading bot')
parser.add_argument('--symbol', type=str, default='BTC/USDT', help='Trading pair symbol')
parser.add_argument('--capital', type=float, default=100, help='Total capital to use in quote currency (e.g., USDT)')
parser.add_argument('--grid-count', type=int, default=5, help='Number of grid levels')
parser.add_argument('--lower', type=float, help='Lower price bound for grid')
parser.add_argument('--upper', type=float, help='Upper price bound for grid')
parser.add_argument('--range-pct', type=float, default=3.0, help='Price range percentage (used if lower/upper not specified)')
parser.add_argument('--duration', type=int, default=3600, help='Duration to run in seconds')
parser.add_argument('--testnet', action='store_true', help='Use testnet')
parser.add_argument('--direction', type=str, choices=['long', 'short'], default='long',
                    help='Trading direction (long or short)')
parser.add_argument('--leverage', type=int, default=2, help='Leverage to use')
parser.add_argument('--initial-position-pct', type=float, default=100.0, 
                    help='Percentage of capital to use for initial position (0-100)')
parser.add_argument('--close-on-exit', action='store_true', help='Close all positions on exit')

args = parser.parse_args()

# Initialize Bybit client
client = BybitClient(
    api_key="bcRYdfdO4Z7INAFPcE",
    api_secret="BmACyMG0LoWygr3p03fCv4E4fxrjtrsRsiir",
    testnet=args.testnet
)

# Get current price for the specified symbol
ticker = client.get_ticker(args.symbol)
current_price = ticker["last"]
print(f"Current price for {args.symbol}: {current_price}")

# Determine grid range
if args.lower and args.upper:
    lower_price = args.lower
    upper_price = args.upper
    # Calculate the percentage range for logging
    range_pct = ((upper_price - lower_price) / current_price) * 100
    print(f"Using specified price range: {lower_price} to {upper_price} ({range_pct:.2f}%)")
else:
    # Calculate range based on percentage
    half_range = current_price * (args.range_pct / 100) / 2
    lower_price = current_price - half_range
    upper_price = current_price + half_range
    print(f"Using calculated price range: {lower_price:.2f} to {upper_price:.2f} ({args.range_pct}%)")

# Calculate order size per grid
grid_capital = args.capital / args.grid_count
order_size = grid_capital * args.leverage
print(f"Capital per grid: {grid_capital} | Order size per grid with {args.leverage}x leverage: {order_size}")

try:
    # Create and start the directional grid bot
    bot = DirectionalGridBot(
        exchange=client,
        symbol=args.symbol,
        capital=args.capital,
        grid_count=args.grid_count,
        direction=args.direction,
        leverage=args.leverage,
        initial_position_pct=args.initial_position_pct,
        lower_price=lower_price,
        upper_price=upper_price
    )
    
    # Set end time for the bot run
    end_time = time.time() + args.duration
    
    print(f"\nGrid bot running. Will stop in {args.duration} seconds...")
    print("Press Ctrl+C to stop earlier")
    
    try:
        while time.time() < end_time:
            current_time = datetime.now().strftime('%H:%M:%S')
            remaining = int(end_time - time.time())
            
            print(f"[{current_time}] Checking for order updates... ({remaining}s remaining)")
            bot.monitor_and_update()
            
            # Sleep for a bit
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    
    # After creating the bot instance
    print("Starting grid bot...")
    success = bot.start()
    print(f"Bot start result: {success}")
    
except Exception as e:
    print(f"Error in main execution: {str(e)}")

finally:
    # Clean up and summarize
    print("\nStopping grid bot and cleaning up...")
    if 'bot' in locals():
        bot.stop()
        
        # Close positions if requested
        if args.close_on_exit:
            print("Closing all positions...")
            client.cancel_all_orders(args.symbol)
            # Add code to close positions here
    else:
        client.cancel_all_orders(args.symbol)
    
    print("Bot stopped. Bye!") 