#!/usr/bin/env python
import sys
import os
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.bot.grid_bot import GridBot
from common.exchange.bybit_client import BybitClient
from common.utils.logger import setup_logger

logger = setup_logger(__name__)

# Initialize Bybit client
client = BybitClient(
    api_key="bcRYdfdO4Z7INAFPcE",
    api_secret="BmACyMG0LoWygr3p03fCv4E4fxrjtrsRsiir",
    testnet=True
)

# Get current price for setting up the grid
symbol = "BTC/USDT"
current_price = client.get_ticker(symbol)["last"]
print(f"Current {symbol} price: {current_price}")

# Set grid parameters
grid_count = 10  # Number of grid levels
range_percentage = 10.0  # 10% range around current price
allocation = 5000  # Amount to allocate in USDT

# Calculate the effective price range for information
lower_price = current_price * (1 - range_percentage/100)
upper_price = current_price * (1 + range_percentage/100)

print(f"Grid range: {lower_price:.2f} to {upper_price:.2f} ({range_percentage}% range)")
print(f"Grid levels: {grid_count}")
print(f"Allocation: {allocation} USDT")

# Try printing the GridBot signature to understand what parameters it accepts
try:
    import inspect
    print("\nGridBot constructor signature:")
    print(inspect.signature(GridBot.__init__))
except Exception as e:
    print(f"Could not print GridBot signature: {e}")

# Create the grid bot using the correct parameters
bot = GridBot(
    exchange=client,
    symbol=symbol,
    capital=allocation,
    grid_count=grid_count,
    range_percentage=range_percentage
)

print("Bot created. Available methods:")
methods = [method for method in dir(bot) if callable(getattr(bot, method)) and not method.startswith("__")]
print(methods)

# First, initialize the grid
print("\nInitializing grid...")
if hasattr(bot, 'initialize_grid'):
    bot.initialize_grid()

# Print a summary before starting
if hasattr(bot, 'print_summary'):
    print("\nGrid Summary:")
    bot.print_summary()

# Start the bot with a time limit
run_duration = 300  # Run for 5 minutes
print(f"\nStarting grid bot for {run_duration} seconds...")
print(f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

try:
    # Start the bot
    if hasattr(bot, 'start'):
        bot.start()  # This should start the actual grid bot logic
        
        # Keep the script running for the specified duration
        start_time = time.time()
        while time.time() - start_time < run_duration:
            # Print current price and time periodically
            current_price = client.get_ticker(symbol)["last"]
            print(f"{datetime.now().strftime('%H:%M:%S')} - Current price: {current_price}")
            
            # Sleep to avoid flooding the console
            time.sleep(10)
            
            # Optionally check profit
            if hasattr(bot, 'calculate_profit'):
                profit = bot.calculate_profit()
                print(f"Current profit: {profit}")
    else:
        print("ERROR: Bot does not have a 'start' method!")
        
except KeyboardInterrupt:
    print("\nBot stopped by user.")
except Exception as e:
    print(f"Error running bot: {str(e)}")
finally:
    # Stop the bot properly
    if hasattr(bot, 'stop'):
        print("\nStopping bot...")
        bot.stop()
    
    # Cancel any remaining orders
    if hasattr(bot, 'cancel_all_orders'):
        print("Cancelling all orders...")
        bot.cancel_all_orders()
    
    print(f"\nBot session ended at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Final profit calculation
    if hasattr(bot, 'calculate_profit'):
        final_profit = bot.calculate_profit()
        print(f"Final profit: {final_profit}")
    
    # Final summary
    if hasattr(bot, 'print_summary'):
        print("\nFinal Grid Summary:")
        bot.print_summary()