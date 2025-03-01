#!/usr/bin/env python
"""
Create grid orders on Binance Futures and monitor them
"""
import sys
import os
import argparse
import logging
from datetime import datetime
import time
import math
import requests
import json
import random

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.exchange.futures_client import FuturesExchangeClient

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_binance_futures_exchange_info(testnet=True):
    """Get futures exchange information directly from Binance API"""
    if testnet:
        url = "https://testnet.binancefuture.com/fapi/v1/exchangeInfo"
    else:
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to get exchange info: {response.text}")
        return None

def get_binance_futures_symbol_info(symbol, testnet=True):
    """Get symbol information from Binance Futures"""
    exchange_info = get_binance_futures_exchange_info(testnet)
    if not exchange_info or 'symbols' not in exchange_info:
        return None
    
    # Convert to Binance format
    if '/' in symbol:
        symbol = symbol.replace('/', '')
    
    for symbol_info in exchange_info['symbols']:
        if symbol_info['symbol'] == symbol:
            return symbol_info
    
    return None

def format_quantity(quantity, step_size, min_qty):
    """Format quantity according to Binance requirements"""
    # Ensure quantity is >= min_qty
    quantity = max(min_qty, quantity)
    
    # Get precision for formatting
    precision = 0
    if '.' in str(step_size):
        precision = len(str(step_size).split('.')[1].rstrip('0'))
    
    # Round up to step size
    steps = quantity / step_size
    rounded_steps = math.ceil(steps)
    rounded_qty = rounded_steps * step_size
    
    # Format to correct precision
    if precision > 0:
        return f"{rounded_qty:.{precision}f}"
    else:
        return str(int(rounded_qty))

def format_price(price, tick_size):
    """Format price according to Binance requirements"""
    # Round to tick size
    rounded_price = math.floor(price / tick_size) * tick_size
    
    # Format to correct precision
    precision = 0
    if '.' in str(tick_size):
        precision = len(str(tick_size).split('.')[1].rstrip('0'))
    
    if precision > 0:
        return f"{rounded_price:.{precision}f}"
    else:
        return str(int(rounded_price))

def get_account_positions(api_key, api_secret, testnet=True):
    """Get account positions directly from Binance API"""
    # Construct URL
    if testnet:
        base_url = "https://testnet.binancefuture.com"
    else:
        base_url = "https://fapi.binance.com"
    
    # Get server time
    timestamp = int(time.time() * 1000)
    
    # Generate query string
    query_string = f"timestamp={timestamp}"
    
    # Generate signature using HMAC SHA256
    import hmac
    import hashlib
    signature = hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Construct full URL
    url = f"{base_url}/fapi/v2/positionRisk?{query_string}&signature={signature}"
    
    # Set headers
    headers = {
        'X-MBX-APIKEY': api_key
    }
    
    # Make request
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to get positions: {response.text}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Create and monitor grid orders')
    parser.add_argument('api_key', help='Binance API key')
    parser.add_argument('api_secret', help='Binance API secret')
    parser.add_argument('pair', help='Trading pair, e.g. BTC/USDT')
    parser.add_argument('capital', type=float, help='Capital to use for trading (in USDT)')
    parser.add_argument('--grids', type=int, default=3, help='Number of grid levels')
    parser.add_argument('--range-percentage', type=float, default=2.0, 
                       help='Price range percentage above and below current price')
    
    args = parser.parse_args()
    
    # Create exchange client
    exchange_client = FuturesExchangeClient(args.api_key, args.api_secret, testnet=True)
    
    # Get current price
    current_price = exchange_client.get_ticker(args.pair)
    if not current_price:
        logger.error(f"Failed to get current price for {args.pair}")
        return
    
    logger.info(f"Current price: {current_price}")
    
    # Get symbol info
    symbol_info = get_binance_futures_symbol_info(args.pair, testnet=True)
    if not symbol_info:
        logger.error(f"Failed to get symbol info for {args.pair}")
        return
    
    # Extract important values
    min_qty = float(symbol_info['filters'][1]['minQty'])  # LOT_SIZE filter
    step_size = float(symbol_info['filters'][1]['stepSize'])  # LOT_SIZE filter
    tick_size = float(symbol_info['filters'][0]['tickSize'])  # PRICE_FILTER
    min_notional = float(symbol_info['filters'][6]['notional'])  # MIN_NOTIONAL filter
    
    logger.info(f"Symbol: {symbol_info['symbol']} (Status: {symbol_info['status']})")
    logger.info(f"Min Quantity: {min_qty}, Step Size: {step_size}")
    logger.info(f"Tick Size: {tick_size}")
    logger.info(f"Min Notional: {min_notional}")
    
    # Calculate grid parameters
    range_factor = args.range_percentage / 100
    lower_price = current_price * (1 - range_factor)
    upper_price = current_price * (1 + range_factor)
    
    # Format prices
    lower_price_str = format_price(lower_price, tick_size)
    upper_price_str = format_price(upper_price, tick_size)
    
    logger.info(f"Grid range: {lower_price_str} to {upper_price_str}")
    
    # Calculate how many grids we can create
    max_grids = math.floor(args.capital / min_notional)
    if max_grids < 1:
        logger.error(f"Not enough capital to create even 1 grid. Need at least {min_notional} USDT.")
        return
    
    if max_grids < args.grids:
        logger.warning(f"Can only create {max_grids} grids with {args.capital} USDT")
        actual_grids = max_grids
    else:
        actual_grids = args.grids
    
    # Calculate USDT per grid
    usdt_per_grid = args.capital / actual_grids
    usdt_per_grid = max(usdt_per_grid, min_notional)
    
    logger.info(f"Using {actual_grids} grids with {usdt_per_grid:.2f} USDT per grid")
    
    # Calculate grid levels
    grid_steps = actual_grids + 1
    price_step = (float(upper_price_str) - float(lower_price_str)) / grid_steps
    
    # Create orders
    logger.info("Creating grid orders...")
    
    orders = []
    for i in range(actual_grids):
        # Calculate grid price
        grid_price = float(lower_price_str) + price_step * (i + 1)
        grid_price_str = format_price(grid_price, tick_size)
        
        # Alternate buy/sell orders
        side = "buy" if i % 2 == 0 else "sell"
        
        # Calculate quantity
        btc_quantity = usdt_per_grid / float(grid_price_str)
        qty_needed = max(btc_quantity, min_notional / float(grid_price_str))
        order_size_str = format_quantity(qty_needed, step_size, min_qty)
        
        # Calculate actual notional value
        notional = float(order_size_str) * float(grid_price_str)
        
        logger.info(f"Creating {side} order at {grid_price_str} for {order_size_str} BTC (notional: {notional:.2f} USDT)")
        
        # Ensure we meet min notional
        if notional < min_notional:
            logger.warning(f"Order notional too small. Adding buffer...")
            qty_needed = min_notional / float(grid_price_str) * 1.01  # Add 1% buffer
            order_size_str = format_quantity(qty_needed, step_size, min_qty)
            notional = float(order_size_str) * float(grid_price_str)
            logger.info(f"New order: {order_size_str} BTC (notional: {notional:.2f} USDT)")
        
        # Create order
        try:
            order = exchange_client.create_order(
                symbol=args.pair,
                side=side,
                amount=float(order_size_str),
                price=float(grid_price_str)
            )
            
            if order:
                logger.info(f"Created order: {order}")
                orders.append(order)
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
    
    logger.info(f"Created {len(orders)} out of {actual_grids} orders")
    
    if orders:
        logger.info("Monitoring orders... Press Ctrl+C to cancel orders and exit.")
        
        try:
            while True:
                # Get open orders
                open_orders = exchange_client.get_open_orders(args.pair)
                logger.info(f"Open orders: {len(open_orders) if open_orders else 0}")
                
                for order in open_orders or []:
                    logger.info(f"  Order {order['id']}: {order['side']} {order['amount']} @ {order['price']}")
                
                # Get account positions directly from API
                positions = get_account_positions(args.api_key, args.api_secret, testnet=True)
                active_positions = []
                
                if positions:
                    for pos in positions:
                        if float(pos.get('positionAmt', 0)) != 0:
                            active_positions.append(pos)
                    
                    if active_positions:
                        logger.info("Active positions:")
                        for pos in active_positions:
                            symbol = pos.get('symbol', '')
                            amount = float(pos.get('positionAmt', 0))
                            entry_price = float(pos.get('entryPrice', 0))
                            pnl = float(pos.get('unRealizedProfit', 0))
                            
                            logger.info(f"  {symbol}: {amount} @ {entry_price} (PnL: {pnl:.2f} USDT)")
                    else:
                        logger.info("No active positions")
                
                time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Cancelling all orders...")
            exchange_client.cancel_all_orders(args.pair)
            logger.info("Orders cancelled. Exiting.")
    else:
        logger.error("No orders created. Exiting.")

if __name__ == "__main__":
    main() 