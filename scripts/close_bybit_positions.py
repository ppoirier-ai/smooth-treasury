#!/usr/bin/env python
"""
Utility script to close all open positions on Bybit
"""
import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.exchange.bybit_client import BybitClient
from common.utils.logger import setup_logger

logger = setup_logger(__name__)

# Parse arguments
parser = argparse.ArgumentParser(description='Close all open positions on Bybit')
parser.add_argument('--symbol', type=str, help='Symbol to close positions for (e.g. BTCUSD)')
parser.add_argument('--testnet', action='store_true', help='Use testnet instead of mainnet')
args = parser.parse_args()

try:
    # Initialize Bybit client
    client = BybitClient(
        api_key="bcRYdfdO4Z7INAFPcE",
        api_secret="BmACyMG0LoWygr3p03fCv4E4fxrjtrsRsiir",
        testnet=args.testnet
    )
    
    # Get open positions
    positions = client.get_positions(args.symbol)
    
    if not positions:
        print(f"No open positions for {args.symbol or 'any symbol'}")
        sys.exit(0)
    
    # Print positions to close
    print(f"Found {len(positions)} open positions:")
    for pos in positions:
        print(f"  {pos['side']} {pos['amount']} {pos['symbol']} @ {pos['entry_price']}")
    
    # Confirm with user
    confirmation = input("Close these positions? (y/n): ")
    if confirmation.lower() != 'y':
        print("Operation cancelled")
        sys.exit(0)
    
    # Close each position
    for position in positions:
        size = position.get("amount", 0)
        side = position.get("side", "")
        symbol = position.get("symbol", "")
        
        if size <= 0 or not symbol:
            continue
        
        print(f"Closing {side} position of {size} {symbol}...")
        
        # Create opposite order to close
        close_side = "sell" if side == "long" else "buy"
        
        # Place market order to close position
        result = client.create_market_order(
            symbol=symbol,
            side=close_side,
            amount=size
        )
        
        if result:
            print(f"Successfully closed position: {result.get('id', 'unknown')}")
        else:
            print(f"Failed to close position for {symbol}")
    
    print("Position closing complete!")
    
except Exception as e:
    print(f"Error: {str(e)}") 