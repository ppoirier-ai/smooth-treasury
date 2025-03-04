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
    parser = argparse.ArgumentParser(description='Test Bybit Account Access')
    parser.add_argument('--api_key', type=str, required=True, help='API Key')
    parser.add_argument('--api_secret', type=str, required=True, help='API Secret')
    
    args = parser.parse_args()
    
    logger.info("Initializing Bybit client with time synchronization...")
    
    try:
        # Initialize client
        client = BybitClient(
            api_key=args.api_key,
            api_secret=args.api_secret,
            testnet=True
        )
        
        # Check account balance
        logger.info("\n💰 Checking account balance...")
        btc_balance = client.get_account_balance("BTC")
        logger.info(f"BTC Balance: {json.dumps(btc_balance, indent=2)}")
        
        usdt_balance = client.get_account_balance("USDT")
        logger.info(f"USDT Balance: {json.dumps(usdt_balance, indent=2)}")
        
        # Check positions for BTC/USD
        logger.info("\n📈 Checking BTCUSD positions...")
        positions = client.get_positions("BTC/USD")
        logger.info(f"BTCUSD Positions: {json.dumps(positions, indent=2)}")
        
        logger.info(f"\n✅ Tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    main() 