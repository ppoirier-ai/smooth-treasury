#!/usr/bin/env python
"""
Inspect GridBot implementation directly
"""
import sys
import os
import inspect
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.bot.grid_bot import GridBot

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Print GridBot constructor source code
print("GridBot constructor source code:")
print(inspect.getsource(GridBot.__init__))

# Print the exact grid bot implementation
print("\nGridBot class definition:")
with open(inspect.getfile(GridBot), 'r') as f:
    print(f.read())

print("\nNow trying to use the class...")

# Create a simple mock client that just logs calls
class MockClient:
    def __init__(self):
        self.calls = []
        
    def create_order(self, *args, **kwargs):
        self.calls.append(('create_order', args, kwargs))
        logger.info(f"Mock create_order called with {args}, {kwargs}")
        return {'id': 'mock-123', 'symbol': 'BTC/USDT', 'side': 'buy', 'price': 30000, 'amount': 0.001}
    
    def get_order(self, *args, **kwargs):
        self.calls.append(('get_order', args, kwargs))
        logger.info(f"Mock get_order called with {args}, {kwargs}")
        return {'id': 'mock-123', 'symbol': 'BTC/USDT', 'side': 'buy', 'price': 30000, 'amount': 0.001, 'status': 'open'}
    
    def cancel_order(self, *args, **kwargs):
        self.calls.append(('cancel_order', args, kwargs))
        logger.info(f"Mock cancel_order called with {args}, {kwargs}")
        return True
    
    def get_ticker(self, *args, **kwargs):
        self.calls.append(('get_ticker', args, kwargs))
        logger.info(f"Mock get_ticker called with {args}, {kwargs}")
        return 30000

# Try to create a GridBot with various parameter combinations
try:
    # Try with positional parameters
    client = MockClient()
    bot = GridBot(1, "BTC/USDT", client, 29000, 31000, 3, 0.001)
    print("\nSuccess creating GridBot with positional parameters!")
except Exception as e:
    print(f"\nError creating GridBot with positional parameters: {str(e)}")

try:
    # Try with a subset of named parameters
    client = MockClient()
    bot = GridBot(1, "BTC/USDT", client, 29000, 31000, 3, capital=0.001)
    print("\nSuccess creating GridBot with mixed parameters!")
except Exception as e:
    print(f"\nError creating GridBot with mixed parameters: {str(e)}")

try:
    # Try with all named parameters
    client = MockClient()
    bot = GridBot(
        bot_id=1, 
        pair="BTC/USDT", 
        client=client, 
        lower=29000, 
        upper=31000, 
        grids=3, 
        capital=0.001
    )
    print("\nSuccess creating GridBot with named parameters!")
except Exception as e:
    print(f"\nError creating GridBot with named parameters: {str(e)}") 