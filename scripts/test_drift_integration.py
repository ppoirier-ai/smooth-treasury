#!/usr/bin/env python
"""
Test script for Drift Protocol integration.
"""
import sys
import os
import time
import json
import argparse
import asyncio

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.exchange.drift_client import DriftClient
from common.utils.logger import setup_logger

logger = setup_logger(__name__)

async def main():
    parser = argparse.ArgumentParser(description='Test Drift Protocol Integration')
    parser.add_argument('--private-key', type=str, required=True, help='Base58 encoded private key for Solana wallet')
    parser.add_argument('--testnet', action='store_true', help='Use Solana devnet')
    parser.add_argument('--rpc-url', type=str, default=None, help='Custom RPC URL (optional)')
    
    args = parser.parse_args()
    
    # Initialize Drift client
    client = DriftClient(
        private_key=args.private_key,
        rpc_url=args.rpc_url or ("https://api.devnet.solana.com" if args.testnet else "https://api.mainnet-beta.solana.com"),
        testnet=args.testnet
    )
    
    # Test basic functions
    print("\n=== Testing Drift Client ===\n")
    
    # 1. Check markets
    print("Available markets:")
    for symbol, market in client.markets.items():
        print(f"  {symbol}: {json.dumps(market, indent=2)}")
    
    # 2. Check balance
    print("\nAccount balance:")
    balance = client.get_balance()
    for currency, amount in balance.items():
        print(f"  {currency}: {amount}")
    
    # 3. Get ticker
    symbol = "cbBTC-PERP"
    print(f"\nCurrent price for {symbol}:")
    ticker = client.get_ticker(symbol)
    print(f"  Last: {ticker['last']}")
    print(f"  Bid: {ticker['bid']}")
    print(f"  Ask: {ticker['ask']}")
    
    # 4. Place a small limit order
    print("\nPlacing test limit order...")
    order_id = client.create_limit_order(
        symbol=symbol,
        side="buy",
        amount=0.001,  # Very small amount for testing
        price=ticker['last'] * 0.95  # 5% below current price
    )
    
    if order_id:
        print(f"  Success! Order ID: {order_id}")
        
        # 5. Check open orders
        print("\nChecking open orders...")
        open_orders = client.get_open_orders(symbol)
        print(f"  Open orders: {len(open_orders)}")
        for order in open_orders:
            print(f"  {order['id']}: {order['side']} {order['amount']} @ {order['price']}")
        
        # 6. Cancel the test order
        print("\nCancelling test order...")
        cancel_success = client.cancel_order(order_id)
        print(f"  Cancel {'successful' if cancel_success else 'failed'}")
    else:
        print("  Failed to place test order")
    
    # 7. Test position tracking
    print("\nCurrent positions:")
    positions = client.get_positions()
    if positions:
        for position in positions:
            print(f"  {position['symbol']}: {position['size']} @ {position['entry_price']} (PnL: {position['unrealized_pnl']})")
    else:
        print("  No open positions")
    
    print("\nDrift client test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 