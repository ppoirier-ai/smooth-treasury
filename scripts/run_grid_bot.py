#!/usr/bin/env python
import sys
import os

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

print("Bot initialized. Starting...")

# Start the bot
bot.run()