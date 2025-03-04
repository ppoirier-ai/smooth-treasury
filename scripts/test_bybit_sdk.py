#!/usr/bin/env python
import sys
import os
import argparse
import json
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Test Bybit API using official SDK')
    parser.add_argument('--api_key', type=str, required=True, help='API Key')
    parser.add_argument('--api_secret', type=str, required=True, help='API Secret')
    
    args = parser.parse_args()
    
    # Dynamically check if pybit is installed
    try:
        from pybit.unified_trading import HTTP
    except ImportError:
        logger.error("pybit package not found. Installing...")
        os.system("pip install pybit")
        from pybit.unified_trading import HTTP
    
    logger.info("Initializing Bybit client using official SDK...")
    
    try:
        # Initialize client
        session = HTTP(
            testnet=True,
            api_key=args.api_key,
            api_secret=args.api_secret
        )
        
        # Get server time
        server_time = session.get_server_time()
        logger.info(f"Server time: {server_time}")
        
        # Check wallet balance
        logger.info("\n💰 Checking wallet balance...")
        balance = session.get_wallet_balance(accountType="UNIFIED", coin="BTC")
        logger.info(f"BTC Balance: {json.dumps(balance, indent=2)}")
        
        # Check positions
        logger.info("\n📈 Checking positions...")
        positions = session.get_positions(category="inverse", symbol="BTCUSD")
        logger.info(f"BTCUSD Positions: {json.dumps(positions, indent=2)}")
        
        logger.info(f"\n✅ Tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    main() 