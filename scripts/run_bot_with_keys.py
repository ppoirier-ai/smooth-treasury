#!/usr/bin/env python
"""
Run grid bot with direct API keys (bypassing database)
"""
import sys
import os
import argparse
import logging
from datetime import datetime
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.exchange.futures_client import FuturesExchangeClient
from common.exchange.mock_client import MockExchangeClient
from common.bot.grid_bot import GridBot

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Run grid bot with direct API keys')
    parser.add_argument('api_key', help='Binance API key')
    parser.add_argument('api_secret', help='Binance API secret')
    parser.add_argument('pair', help='Trading pair, e.g. BTC/USDT')
    parser.add_argument('capital', type=float, help='Capital to use for trading')
    parser.add_argument('--testnet', action='store_true', help='Use testnet instead of mainnet')
    parser.add_argument('--grids', type=int, default=3, help='Number of grid levels')
    parser.add_argument('--range-percentage', type=float, default=2.0, 
                       help='Price range percentage above and below current price')
    
    args = parser.parse_args()
    
    # Create futures client directly with provided keys
    exchange = FuturesExchangeClient(args.api_key, args.api_secret, testnet=args.testnet)
    
    # Get current price to calculate grid range
    current_price = exchange.get_ticker(args.pair)
    if not current_price:
        logger.error(f"Failed to get current price for {args.pair}")
        return
        
    logger.info(f"Current {args.pair} price: {current_price}")
    
    # Calculate grid parameters
    range_factor = args.range_percentage / 100
    lower_price = current_price * (1 - range_factor)
    upper_price = current_price * (1 + range_factor)
    
    logger.info(f"Grid range: {lower_price:.2f} to {upper_price:.2f} ({args.range_percentage}% range)")
    logger.info(f"Grid levels: {args.grids}")
    
    # Get bot ID (use timestamp as a simple unique identifier)
    bot_id = int(datetime.now().timestamp())
    
    # Create grid bot with all required parameters
    bot = GridBot(
        bot_id, 
        args.pair, 
        exchange, 
        lower_price, 
        upper_price, 
        args.grids, 
        capital=args.capital
    )
    
    try:
        # Start grid bot
        logger.info(f"Starting bot with ID {bot_id} for {args.pair} with {args.capital} capital")
        bot.start()
        
        # Keep running until keyboard interrupt
        logger.info("Bot running. Press Ctrl+C to stop.")
        while True:
            bot.check_orders()
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Stopping bot...")
        bot.stop()
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Error running bot: {str(e)}")
        logger.exception("Exception details:")
        try:
            bot.stop()
        except:
            pass

if __name__ == "__main__":
    main() 