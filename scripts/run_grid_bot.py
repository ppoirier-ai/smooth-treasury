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

print("Bot initialized.")

# Try to see what methods the bot has
try:
    print("\nAvailable methods:")
    methods = [method for method in dir(bot) if callable(getattr(bot, method)) and not method.startswith("__")]
    print(methods)
except Exception as e:
    print(f"Could not list methods: {str(e)}")

# Since there's no run() method, let's try to use the bot's methods
print("\nStarting manual grid bot loop...")
print(f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

try:
    # Setup the grid (if there's a setup method)
    if hasattr(bot, 'setup_grid'):
        print("Setting up grid...")
        bot.setup_grid()
    
    # Try to place initial orders
    if hasattr(bot, 'place_grid_orders'):
        print("Placing initial grid orders...")
        bot.place_grid_orders()
    
    # Monitor and adjust (simple example)
    run_time = 60  # Run for 60 seconds as a test
    print(f"Monitoring for {run_time} seconds...")
    
    start_time = time.time()
    while time.time() - start_time < run_time:
        # Get current price
        current_price = client.get_ticker(symbol)["last"]
        print(f"{datetime.now().strftime('%H:%M:%S')} - Current price: {current_price}")
        
        # Try to update grid or handle orders
        if hasattr(bot, 'update_grid'):
            bot.update_grid()
        elif hasattr(bot, 'check_and_update'):
            bot.check_and_update()
        elif hasattr(bot, 'manage_orders'):
            bot.manage_orders()
        
        # Sleep to avoid hammering the API
        time.sleep(5)
    
    print(f"Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
except KeyboardInterrupt:
    print("\nBot stopped by user.")
except Exception as e:
    print(f"Error running bot: {str(e)}")
finally:
    # Clean up resources or cancel orders if needed
    if hasattr(bot, 'cancel_all_orders'):
        print("Cancelling all orders...")
        bot.cancel_all_orders()
    elif hasattr(bot, 'cleanup'):
        print("Cleaning up...")
        bot.cleanup()
    
    print("Bot stopped.")