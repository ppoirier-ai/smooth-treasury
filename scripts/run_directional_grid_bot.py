#!/usr/bin/env python
"""
Run a directional grid trading bot (long or short) on Bybit
"""
import sys
import os
import time
from datetime import datetime
import argparse

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.bot.directional_grid_bot import DirectionalGridBot
from common.exchange.bybit_client import BybitClient
from common.utils.logger import setup_logger

logger = setup_logger(__name__)

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Run a directional grid trading bot')
parser.add_argument('--symbol', type=str, default='BTC/USDT', help='Trading pair symbol')
parser.add_argument('--capital', type=float, default=100, help='Total capital to use')
parser.add_argument('--grid-count', type=int, default=5, help='Number of grid levels')
parser.add_argument('--range-pct', type=float, default=3.0, help='Price range percentage')
parser.add_argument('--duration', type=int, default=300, help='Bot run duration in seconds')
parser.add_argument('--testnet', action='store_true', help='Use testnet instead of mainnet')
parser.add_argument('--direction', choices=['long', 'short'], default='long', help='Trading direction')
parser.add_argument('--leverage', type=int, default=2, help='Leverage to use (1 = no leverage)')
parser.add_argument('--initial-position', type=float, default=50.0, 
                   help='Percentage of capital for initial position (0-100)')
parser.add_argument('--close-on-exit', action='store_true', 
                    help='Close all positions when the bot exits')
args = parser.parse_args()

# Main functionality
try:
    # Initialize Bybit client
    client = BybitClient(
        api_key="bcRYdfdO4Z7INAFPcE",
        api_secret="BmACyMG0LoWygr3p03fCv4E4fxrjtrsRsiir",
        testnet=args.testnet
    )
    
    print(f"Starting {args.direction} grid bot for {args.symbol}")
    print(f"Settings: Capital=${args.capital}, Grid Levels={args.grid_count}, Range={args.range_pct}%")
    print(f"Leverage: {args.leverage}x, Initial Position: {args.initial_position}%")
    
    # Clean up any existing orders first
    print("Cleaning up existing orders...")
    client.cancel_all_orders(args.symbol)
    time.sleep(2)
    
    # Create and start the grid bot
    bot = DirectionalGridBot(
        exchange=client,
        symbol=args.symbol,
        capital=args.capital,
        grid_count=args.grid_count,
        range_percentage=args.range_pct,
        direction=args.direction,
        leverage=args.leverage,
        initial_position_pct=args.initial_position
    )
    
    # Add this property for exit behavior
    bot.close_positions_on_exit = args.close_on_exit
    
    # Set timeout for the bot
    end_time = time.time() + args.duration
    
    # Start the process
    bot.initialize_grid()
    bot.print_summary()
    
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
    
except Exception as e:
    print(f"Error in main execution: {str(e)}")

finally:
    # Clean up and summarize
    print("\nStopping grid bot and cleaning up...")
    if 'bot' in locals():
        bot.stop()
    else:
        client.cancel_all_orders(args.symbol)
    
    print("Bot stopped. Bye!") 