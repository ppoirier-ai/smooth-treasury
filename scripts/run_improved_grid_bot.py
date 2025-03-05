#!/usr/bin/env python
"""
Improved grid bot runner that actually places orders
"""
import sys
import os
import time
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.bot.improved_grid_bot import ImprovedGridBot
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
range_percentage = 5.0  # 5% range around current price (tighter for more trades)
allocation = 1000  # Amount to allocate in USDT (starting smaller for testing)

# Calculate the effective price range for information
lower_price = current_price * (1 - range_percentage/100)
upper_price = current_price * (1 + range_percentage/100)

print(f"Grid range: {lower_price:.2f} to {upper_price:.2f} ({range_percentage}% range)")
print(f"Grid levels: {grid_count}")
print(f"Allocation: {allocation} USDT")

# Clean up any existing orders
print("Cleaning up existing orders...")
client.cancel_all_orders(symbol)
time.sleep(2)

# Create the improved grid bot using the correct parameters
bot = ImprovedGridBot(
    exchange=client,
    symbol=symbol,
    capital=allocation,
    grid_count=grid_count,
    range_percentage=range_percentage
)

print("Bot initialized. Starting...")

# Set timeout for bot run
run_duration = 300  # 5 minutes
print(f"Bot will run for {run_duration} seconds...")

try:
    bot.start()  # This will run in a blocking mode
except KeyboardInterrupt:
    print("\nBot stopped by user")
finally:
    # Ensure all orders are cancelled
    print("Cancelling all orders...")
    client.cancel_all_orders(symbol)
    print("Orders cancelled. Bot stopped.") 