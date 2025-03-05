#!/usr/bin/env python
import sys
import os
import time
import argparse
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.exchange.bybit_client import BybitClient
from common.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Test Bybit Order Placement')
    parser.add_argument('--api_key', type=str, required=True, help='API Key')
    parser.add_argument('--api_secret', type=str, required=True, help='API Secret')
    parser.add_argument('--symbol', type=str, default='BTC/USD', help='Symbol (default: BTC/USD for inverse)')
    parser.add_argument('--action', type=str, choices=['check', 'place', 'cancel'], default='check', 
                        help='Action to perform: check balances/positions, place order, or cancel all orders')
    parser.add_argument('--size', type=float, default=0.001, help='Order size (in BTC)')
    parser.add_argument('--price', type=float, default=0, help='Order price (0 = 5% below market)')
    parser.add_argument('--side', type=str, choices=['buy', 'sell'], default='buy', help='Order side')
    parser.add_argument('--mainnet', action='store_true', help='Use mainnet instead of testnet')
    
    args = parser.parse_args()
    
    # Default to testnet
    testnet = not args.mainnet
    network = "mainnet" if not testnet else "testnet"
    logger.info(f"Testing Bybit {network} API for {args.symbol}...")
    
    try:
        # Initialize client
        client = BybitClient(
            api_key=args.api_key,
            api_secret=args.api_secret,
            testnet=testnet
        )
        
        # Check balances and positions
        if args.action in ['check', 'place']:
            logger.info(f"\n💰 Checking account balance...")
            balance = client.get_account_balance("BTC")
            logger.info(f"BTC Balance: {balance}")
            
            # Check USDT balance too for completeness
            balance = client.get_account_balance("USDT")
            logger.info(f"USDT Balance: {balance}")
            
            logger.info(f"\n📈 Checking positions...")
            positions = client.get_positions(args.symbol)
            logger.info(f"Current positions: {positions}")
            
            logger.info(f"\n📋 Checking open orders...")
            open_orders = client.get_open_orders(args.symbol)
            logger.info(f"Open orders: {open_orders}")
        
        # Place a test order
        if args.action == 'place':
            # Get current market price
            ticker = client.get_ticker(args.symbol)
            if not ticker:
                logger.error("Failed to get current market price. Cannot place order.")
                return
            
            market_price = ticker['last']
            logger.info(f"Current market price: ${market_price}")
            
            # Use specified price or calculate based on market
            price = args.price
            if price <= 0:
                # Place order 5% below/above market price depending on side
                if args.side == 'buy':
                    price = market_price * 0.95  # 5% below for buys
                else:
                    price = market_price * 1.05  # 5% above for sells
            
            logger.info(f"\n🛒 Placing {args.side} order for {args.size} {args.symbol} at ${price}...")
            
            # Set leverage if needed
            client.set_leverage(args.symbol, 10)  # Use 10x leverage
            
            # Place the order
            order = client.create_order(args.symbol, args.side, args.size, price)
            if order:
                logger.info(f"✅ Order placed successfully: {json.dumps(order, indent=2)}")
            else:
                logger.error("❌ Failed to place order")
        
        # Cancel all orders
        elif args.action == 'cancel':
            logger.info(f"\n🧹 Cancelling all orders for {args.symbol}...")
            success = client.cancel_all_orders(args.symbol)
            if success:
                logger.info("✅ All orders cancelled successfully")
            else:
                logger.error("❌ Failed to cancel orders")
        
    except Exception as e:
        logger.error(f"❌ Error during testing: {str(e)}")


if __name__ == "__main__":
    main() 