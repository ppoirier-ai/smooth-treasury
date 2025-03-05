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

# Calculate grid boundaries (10% range)
lower_price = current_price * 0.95
upper_price = current_price * 1.05
grid_levels = 10
allocation = 5000  # Amount to allocate in USDT

print(f"Grid range: {lower_price:.2f} to {upper_price:.2f}")
print(f"Grid levels: {grid_levels}")
print(f"Allocation: {allocation} USDT")

# Try printing the GridBot signature to understand what parameters it accepts
try:
    import inspect
    print("\nGridBot constructor signature:")
    print(inspect.signature(GridBot.__init__))
except Exception as e:
    print(f"Could not print GridBot signature: {e}")

# Create and run the grid bot
# Trying with the most basic/common parameter names
bot = GridBot(
    exchange=client,
    symbol=symbol,
    capital=allocation,
    test_mode=True
)

print("Bot initialized. Starting...")

# Start the bot
bot.run()