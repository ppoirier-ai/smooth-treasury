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
import math

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.exchange.futures_client import FuturesExchangeClient
from common.bot.grid_bot import GridBot

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def round_to_precision(value, precision):
    """Round value to specific precision (decimal places)"""
    factor = 10 ** precision
    return math.floor(value * factor) / factor

def main():
    parser = argparse.ArgumentParser(description='Run grid bot with direct API keys')
    parser.add_argument('api_key', help='Binance API key')
    parser.add_argument('api_secret', help='Binance API secret')
    parser.add_argument('pair', help='Trading pair, e.g. BTC/USDT')
    parser.add_argument('capital', type=float, help='Capital to use for trading')
    parser.add_argument('--grids', type=int, default=3, help='Number of grid levels')
    parser.add_argument('--range-percentage', type=float, default=2.0, 
                       help='Price range percentage above and below current price')
    parser.add_argument('--price-precision', type=int, default=1, 
                       help='Price precision (decimal places)')
    parser.add_argument('--qty-precision', type=int, default=3, 
                       help='Quantity precision (decimal places)')
    
    args = parser.parse_args()
    
    # Create futures client directly with provided keys
    exchange_client = FuturesExchangeClient(args.api_key, args.api_secret, testnet=True)
    
    # Get current price to calculate grid range
    current_price = exchange_client.get_ticker(args.pair)
    if not current_price:
        logger.error(f"Failed to get current price for {args.pair}")
        return
        
    logger.info(f"Current {args.pair} price: {current_price}")
    
    # Calculate grid parameters and round to correct precision
    range_factor = args.range_percentage / 100
    lower_price = round_to_precision(current_price * (1 - range_factor), args.price_precision)
    upper_price = round_to_precision(current_price * (1 + range_factor), args.price_precision)
    
    logger.info(f"Grid range: {lower_price:.2f} to {upper_price:.2f} ({args.range_percentage}% range)")
    logger.info(f"Grid levels: {args.grids}")
    logger.info(f"Using price precision: {args.price_precision}, quantity precision: {args.qty_precision}")
    
    # Get bot ID (use timestamp as a simple unique identifier)
    bot_id = int(datetime.now().timestamp())
    
    # Print the parameter list to debug
    logger.info(f"Creating GridBot with parameters:")
    logger.info(f"  bot_id: {bot_id}")
    logger.info(f"  client: [exchange client object]")
    logger.info(f"  pair: {args.pair}")
    logger.info(f"  lower: {lower_price}")
    logger.info(f"  upper: {upper_price}")
    logger.info(f"  grids: {args.grids}")
    logger.info(f"  capital: {args.capital}")
    
    # Use CORRECT ORDER: bot_id, client, pair, lower, upper, grids, capital
    bot = GridBot(
        bot_id,
        exchange_client,
        args.pair,
        lower_price, 
        upper_price, 
        args.grids,
        args.capital
    )
    
    try:
        # Start grid bot
        logger.info(f"Starting bot with ID {bot_id} for {args.pair} with {args.capital} capital")
        bot.start()
        
        # Keep running until keyboard interrupt - but don't call check_orders since it doesn't exist
        logger.info("Bot running. Press Ctrl+C to stop.")
        
        # Instead of calling a non-existent method, poll the order status manually
        while True:
            # Just sleep and wait for manual interrupt
            logger.info(f"Bot running... Current profit: {bot.calculate_profit()}")
            
            # Check if any orders have been filled
            # We'll do this manually since check_orders doesn't exist
            for order_id, order_info in list(bot.active_orders.items()):
                order_status = exchange_client.get_order(args.pair, order_id)
                if order_status and order_status.get('status') == 'filled':
                    logger.info(f"Order {order_id} has been filled!")
                    bot.handle_order_fill(
                        order_id, 
                        float(order_status['price']), 
                        float(order_status['amount'])
                    )
            
            time.sleep(10)
            
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