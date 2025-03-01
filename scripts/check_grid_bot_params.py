#!/usr/bin/env python
"""
Check GridBot parameters
"""
import sys
import os
import inspect

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.bot.grid_bot import GridBot

# Inspect GridBot constructor
signature = inspect.signature(GridBot.__init__)
print("GridBot constructor parameters:")
for name, param in signature.parameters.items():
    print(f"  {name}: {param.default}")

# Print the source code of the constructor
print("\nGridBot constructor source code:")
print(inspect.getsource(GridBot.__init__)) 