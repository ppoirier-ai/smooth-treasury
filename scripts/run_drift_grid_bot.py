#!/usr/bin/env python
"""
Run a directional grid trading bot on Drift Protocol (Solana)
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
from common.exchange.drift_client import DriftClient
from common.utils.logger import setup_logger
from common.utils.solana_utils import decode_private_key

logger = setup_logger(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Run a directional grid trading bot on Drift (Solana)')
parser.add_argument('--private-key', type=str, required=True, help='Base58 encoded private key for Solana wallet')
parser.add_argument('--rpc-url', type=str, default="https://api.mainnet-beta.solana.com", 
                  help='Solana RPC URL (default: mainnet)')
parser.add_argument('--symbol', type=str, default='cbBTC-PERP', help='Trading pair symbol')
parser.add_argument('--capital', type=float, default=100, help='Total capital to use in USDC')
parser.add_argument('--grid-count', type=int, default=5, help='Number of grid levels')
parser.add_argument('--lower', type=float, help='Lower price bound for grid')
parser.add_argument('--upper', type=float, help='Upper price bound for grid')
parser.add_argument('--range-pct', type=float, default=3.0, help='Price range percentage (used if lower/upper not specified)')
parser.add_argument('--duration', type=int, default=3600, help='Duration to run in seconds')
parser.add_argument('--testnet', action='store_true', help='Use Solana devnet')
parser.add_argument('--direction', type=str, choices=['long', 'short'], default='long',
                    help='Trading direction (long or short)')
parser.add_argument('--leverage', type=int, default=2, help='Leverage to use')
parser.add_argument('--initial-position-pct', type=float, default=100.0, 
                    help='Percentage of capital to use for initial position (0-100)')
parser.add_argument('--close-on-exit', action='store_true', help='Close all positions on exit')

args = parser.parse_args()

# Initialize Drift client
try:
    client = DriftClient(
        private_key=args.private_key,
        rpc_url=args.rpc_url,
        testnet=args.testnet
    )
    
    # Get current price for the specified symbol
    try:
        ticker = client.get_ticker(args.symbol)
        current_price = ticker["last"]
        print(f"Current price for {args.symbol}: {current_price}")
    except Exception as e:
        print(f"Error getting ticker: {e}")
        print("Using default price of 75000 for testing purposes")
        current_price = 75000  # Default for testing

    # Set leverage for the symbol
    if args.leverage > 1:
        leverage_success = client.set_leverage(args.symbol, args.leverage)
        print(f"Setting leverage to {args.leverage}x: {'Success' if leverage_success else 'Failed'}")
    
    # Check available balance
    balance = client.get_balance("USDC")
    if "USDC" in balance and balance["USDC"] < args.capital:
        print(f"WARNING: Available USDC balance ({balance['USDC']}) is less than requested capital ({args.capital})")
        confirm = input("Continue anyway? (y/n): ")
        if confirm.lower() != 'y':
            print("Exiting...")
            sys.exit(0)
except Exception as e:
    print(f"Failed to initialize Drift client: {e}")
    sys.exit(1)

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
    # Check SOL balance
    sol_balance = client.solana_client.get_balance(client.wallet_public_key)
    if 'result' in sol_balance and sol_balance['result']['value'] < 1000000:  # Less than 0.001 SOL
        print("WARNING: Your wallet has very little SOL. You may not be able to pay for transactions.")
        print(f"Current SOL balance: {sol_balance['result']['value'] / 1000000000:.9f} SOL")
        # Ask for confirmation
        confirm = input("Continue anyway? (y/n): ")
        if confirm.lower() != 'y':
            print("Exiting...")
            sys.exit(0)
    
    # Initialize the bot
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
    
    # Start the bot immediately after creating it
    print("Starting grid bot on Drift Protocol...")
    success = bot.start()
    print(f"Bot start result: {success}")
    
    if not success:
        print("Failed to start bot. Exiting...")
        sys.exit(1)
    
    # Set end time for the bot run
    end_time = time.time() + args.duration
    
    print(f"\nGrid bot running on Drift. Will stop in {args.duration} seconds...")
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
    import traceback
    traceback.print_exc()

finally:
    # Clean up and summarize
    print("\nStopping grid bot and cleaning up...")
    if 'bot' in locals():
        bot.stop()
        
        # Close positions if requested
        if args.close_on_exit:
            print("Closing all positions...")
            try:
                client.cancel_all_orders(args.symbol)
                # Add code to close positions here
                print("All positions closed.")
            except Exception as e:
                print(f"Error closing positions: {e}")
    else:
        try:
            client.cancel_all_orders(args.symbol)
        except:
            pass
    
    print("Bot stopped. Bye!")
