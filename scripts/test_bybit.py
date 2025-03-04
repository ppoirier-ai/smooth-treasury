#!/usr/bin/env python
import sys
import os
import time
import argparse

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.exchange.bybit_client import BybitClient
from common.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Test Bybit API connection')
    parser.add_argument('api_key', type=str, help='API Key')
    parser.add_argument('api_secret', type=str, help='API Secret')
    parser.add_argument('--symbol', type=str, default='BTC/USDT', help='Symbol (default: BTC/USDT)')
    parser.add_argument('--mainnet', action='store_true', help='Use mainnet instead of testnet')
    
    args = parser.parse_args()
    
    # Default to testnet (opposite of other clients for safety)
    testnet = not args.mainnet
    network = "mainnet" if not testnet else "testnet"
    logger.info(f"Testing Bybit {network} API...")
    
    try:
        # Initialize client
        client = BybitClient(args.api_key, args.api_secret, testnet)
        
        # Test ticker
        logger.info(f"\n📊 Testing ticker for {args.symbol}...")
        ticker = client.get_ticker(args.symbol)
        logger.info(f"Ticker: {ticker}")
        
        time.sleep(1)
        
        # Test orderbook
        logger.info(f"\n📚 Testing orderbook for {args.symbol}...")
        orderbook = client.get_orderbook(args.symbol)
        logger.info(f"First few bids: {orderbook['bids'][:3]}")
        logger.info(f"First few asks: {orderbook['asks'][:3]}")
        
        time.sleep(1)
        
        # Test account balance
        logger.info("\n💰 Testing account balance...")
        balance = client.get_account_balance()
        logger.info(f"Balance: {balance}")
        
        time.sleep(1)
        
        # Test get positions
        logger.info("\n📈 Testing positions...")
        positions = client.get_positions(args.symbol)
        logger.info(f"Positions: {positions}")
        
        time.sleep(1)
        
        # Test get open orders
        logger.info(f"\n📋 Testing open orders for {args.symbol}...")
        open_orders = client.get_open_orders(args.symbol)
        logger.info(f"Open orders: {open_orders}")
        
        logger.info("\n✅ All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during testing: {str(e)}")


if __name__ == "__main__":
    main() 