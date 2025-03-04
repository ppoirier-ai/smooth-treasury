#!/usr/bin/env python
import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.exchange.bybit_client import BybitClient
from common.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Simple Bybit Test')
    parser.add_argument('--api_key', type=str, required=True, help='API Key')
    parser.add_argument('--api_secret', type=str, required=True, help='API Secret')
    
    args = parser.parse_args()
    
    logger.info("Initializing BybitClient...")
    logger.info(f"API Key: {args.api_key}")
    logger.info(f"API Secret: {args.api_secret[:5]}...")  # Only show first 5 chars for security
    
    client = BybitClient(api_key=args.api_key, api_secret=args.api_secret, testnet=True)
    
    logger.info("Client initialized successfully!")
    
    # Test connection
    logger.info("Testing categories...")
    logger.info(f"Categories: {client.categories}")
    logger.info(f"Available pairs (inverse): {client.available_pairs.get('inverse', [])[:5]}")

if __name__ == "__main__":
    main() 