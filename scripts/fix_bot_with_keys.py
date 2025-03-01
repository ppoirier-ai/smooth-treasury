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
import requests

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

def get_symbol_precision_info(symbol, testnet=True):
    """Get precision info for symbol from Binance API"""
    if testnet:
        url = "https://testnet.binancefuture.com/fapi/v1/exchangeInfo"
    else:
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    
    # Convert to Binance format
    if '/' in symbol:
        binance_symbol = symbol.replace('/', '')
    else:
        binance_symbol = symbol
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for sym_info in data['symbols']:
                if sym_info['symbol'] == binance_symbol:
                    # Get price precision
                    price_filter = next((f for f in sym_info['filters'] if f['filterType'] == 'PRICE_FILTER'), None)
                    price_tick = float(price_filter['tickSize']) if price_filter else 0.1
                    price_precision = len(price_tick.as_integer_ratio()[1].bit_length()) if price_tick < 1 else 0
                    
                    # Get quantity precision
                    lot_filter = next((f for f in sym_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
                    qty_step = float(lot_filter['stepSize']) if lot_filter else 0.001
                    qty_precision = len(qty_step.as_integer_ratio()[1].bit_length()) if qty_step < 1 else 0
                    
                    # Get min notional
                    min_notional = next((f for f in sym_info['filters'] if f['filterType'] == 'MIN_NOTIONAL'), None)
                    min_val = float(min_notional['notional']) if min_notional else 5.0
                    
                    return {
                        'price_precision': price_precision,
                        'price_tick': price_tick,
                        'qty_precision': qty_precision,
                        'qty_step': qty_step,
                        'min_notional': min_val
                    }
            logger.warning(f"Symbol {binance_symbol} not found")
            return None
        else:
            logger.error(f"Failed to get exchange info: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting symbol precision: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Run grid bot with direct API keys')
    parser.add_argument('api_key', help='Binance API key')
    parser.add_argument('api_secret', help='Binance API secret')
    parser.add_argument('pair', help='Trading pair, e.g. BTC/USDT')
    parser.add_argument('capital', type=float, help='Capital to use for trading')
    parser.add_argument('--grids', type=int, default=3, help='Number of grid levels')
    parser.add_argument('--range-percentage', type=float, default=2.0, 
                       help='Price range percentage above and below current price')
    parser.add_argument('--use-defaults', action='store_true', 
                       help='Use default precision instead of querying API')
    
    args = parser.parse_args()
    
    # Get precision information from Binance
    if args.use_defaults:
        precision_info = {
            'price_precision': 0,  # Use integers for BTC price
            'price_tick': 1.0,     # 1 USD increments
            'qty_precision': 3,    # 0.001 BTC increments 
            'qty_step': 0.001,     # 0.001 BTC increments
            'min_notional': 5.0    # Minimum order value 5 USDT
        }
    else:
        precision_info = get_symbol_precision_info(args.pair, testnet=True)
        if not precision_info:
            logger.error("Could not get precision info. Using defaults.")
            precision_info = {
                'price_precision': 0,
                'price_tick': 1.0,
                'qty_precision': 3,
                'qty_step': 0.001, 
                'min_notional': 5.0
            }
    
    logger.info(f"Using precision settings: {precision_info}")
    
    # Create futures client directly with provided keys
    exchange_client = FuturesExchangeClient(args.api_key, args.api_secret, testnet=True)
    
    # Get current price to calculate grid range
    current_price = exchange_client.get_ticker(args.pair)
    if not current_price:
        logger.error(f"Failed to get current price for {args.pair}")
        return
        
    logger.info(f"Current {args.pair} price: {current_price}")
    
    # Calculate grid parameters and round to correct precision using price tick
    range_factor = args.range_percentage / 100
    
    # Round to nearest tick
    tick = precision_info['price_tick']
    lower_price = math.floor(current_price * (1 - range_factor) / tick) * tick
    upper_price = math.ceil(current_price * (1 + range_factor) / tick) * tick
    
    logger.info(f"Grid range: {lower_price:.2f} to {upper_price:.2f} ({args.range_percentage}% range)")
    logger.info(f"Grid levels: {args.grids}")
    
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
        
        # Implement a simple order monitoring loop
        while True:
            logger.info(f"Bot running... Current profit: {bot.calculate_profit()}")
            
            # Print active orders
            logger.info(f"Active orders: {len(bot.active_orders)}")
            for order_id, order_info in bot.active_orders.items():
                logger.info(f"  Order {order_id}: {order_info.get('side')} {order_info.get('amount')} @ {order_info.get('price')}")
            
            # Check if any orders have been filled
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