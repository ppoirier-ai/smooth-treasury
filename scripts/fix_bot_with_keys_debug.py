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
import json

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

def get_min_qty(symbol_info):
    """Get minimum quantity for a symbol"""
    lot_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
    if lot_filter:
        return float(lot_filter['minQty'])
    return 0.001  # Default minimum quantity

def get_step_size(symbol_info):
    """Get step size for quantity"""
    lot_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
    if lot_filter:
        return float(lot_filter['stepSize'])
    return 0.001  # Default step size

def format_quantity(quantity, symbol_info, round_up=False):
    """Format quantity according to Binance requirements"""
    # Get lot size filter values
    min_qty = get_min_qty(symbol_info)
    step_size = get_step_size(symbol_info)
    
    # Ensure quantity is >= min_qty
    quantity = max(min_qty, quantity)
    
    # Get precision for formatting
    precision = 0
    if '.' in str(step_size):
        precision = len(str(step_size).split('.')[1].rstrip('0'))
    
    # Calculate number of steps
    steps = quantity / step_size
    
    # Round to step size (up or down based on parameter)
    if round_up:
        rounded_steps = math.ceil(steps)
    else:
        rounded_steps = math.floor(steps)
    
    rounded_qty = rounded_steps * step_size
    
    # Format to correct precision
    if precision > 0:
        return f"{rounded_qty:.{precision}f}"
    else:
        return str(int(rounded_qty))

def format_price(price, symbol_info):
    """Format price according to Binance requirements"""
    # Get price filter
    price_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER'), None)
    if not price_filter:
        return str(price)
    
    tick_size_str = price_filter['tickSize']
    tick_size = float(tick_size_str)
    
    # Round to tick size
    rounded_price = math.floor(price / tick_size) * tick_size
    
    # Format to correct precision
    precision = 0
    if '.' in tick_size_str:
        precision = len(tick_size_str.split('.')[1].rstrip('0'))
    
    if precision > 0:
        return f"{rounded_price:.{precision}f}"
    else:
        return str(int(rounded_price))

def calculate_min_quantity_for_notional(price, min_notional, symbol_info):
    """Calculate the minimum quantity needed to meet the minimum notional requirement"""
    # Get min quantity and step size
    min_qty = get_min_qty(symbol_info)
    step_size = get_step_size(symbol_info)
    
    # Calculate the raw quantity needed
    raw_qty_needed = min_notional / price
    
    # Round up to the nearest step size
    steps_needed = math.ceil(raw_qty_needed / step_size)
    qty_needed = steps_needed * step_size
    
    # Ensure it's at least the minimum quantity
    qty_needed = max(qty_needed, min_qty)
    
    return qty_needed

def main():
    parser = argparse.ArgumentParser(description='Run grid bot with direct API keys')
    parser.add_argument('api_key', help='Binance API key')
    parser.add_argument('api_secret', help='Binance API secret')
    parser.add_argument('pair', help='Trading pair, e.g. BTC/USDT')
    parser.add_argument('capital', type=float, help='Capital to use for trading (in USDT)')
    parser.add_argument('--grids', type=int, default=3, help='Number of grid levels')
    parser.add_argument('--range-percentage', type=float, default=2.0, 
                       help='Price range percentage above and below current price')
    
    args = parser.parse_args()
    
    # Get exact symbol information from Binance
    symbol_info = get_binance_futures_symbol_info(args.pair, testnet=True)
    if not symbol_info:
        logger.error(f"Symbol {args.pair} not found on Binance Futures Testnet")
        return
    
    # Print symbol info and filters
    logger.info(f"Symbol: {symbol_info['symbol']} (Status: {symbol_info['status']})")
    logger.info("Symbol filters:")
    for f in symbol_info['filters']:
        logger.info(f"  {f['filterType']}: {json.dumps(f)}")
    
    # Create exchange client
    exchange_client = FuturesExchangeClient(args.api_key, args.api_secret, testnet=True)
    
    # Get current price
    current_price = exchange_client.get_ticker(args.pair)
    if not current_price:
        logger.error(f"Failed to get current price for {args.pair}")
        return
    
    logger.info(f"Current price: {current_price}")
    
    # Calculate grid parameters
    range_factor = args.range_percentage / 100
    lower_price = current_price * (1 - range_factor)
    upper_price = current_price * (1 + range_factor)
    
    # Format prices
    lower_price_str = format_price(lower_price, symbol_info)
    upper_price_str = format_price(upper_price, symbol_info)
    
    logger.info(f"Grid range: {lower_price_str} to {upper_price_str}")
    
    # Get minimum notional value
    min_notional = 100.0  # Default from error message
    min_notional_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'MIN_NOTIONAL'), None)
    if min_notional_filter:
        min_notional = float(min_notional_filter['notional'])
    
    logger.info(f"Minimum notional value: {min_notional} USDT")
    
    # Calculate the minimum BTC amount needed at current price to meet min notional
    min_btc_required = calculate_min_quantity_for_notional(current_price, min_notional, symbol_info)
    min_btc_formatted = format_quantity(min_btc_required, symbol_info)
    min_notional_actual = float(min_btc_formatted) * current_price
    
    logger.info(f"Minimum quantity required: {min_btc_formatted} BTC (notional: {min_notional_actual:.2f} USDT)")
    
    # Check if our total capital is sufficient for at least one order
    if args.capital < min_notional:
        logger.error(f"Total capital {args.capital} USDT is below the minimum notional {min_notional} USDT")
        return
    
    # Calculate how many grids we can create
    max_grids = math.floor(args.capital / min_notional)
    if max_grids < 1:
        logger.error(f"Not enough capital to create even 1 grid. Need at least {min_notional} USDT.")
        return
    
    if max_grids < args.grids:
        logger.warning(f"Can only create {max_grids} grids with {args.capital} USDT (min notional: {min_notional} USDT)")
        actual_grids = max_grids
    else:
        actual_grids = args.grids
    
    # Calculate USDT per grid
    usdt_per_grid = args.capital / actual_grids
    usdt_per_grid = max(usdt_per_grid, min_notional)  # Ensure we meet minimum
    
    logger.info(f"Using {actual_grids} grids with {usdt_per_grid:.2f} USDT per grid")
    
    # Calculate grid levels
    grid_steps = actual_grids + 1
    price_step = (float(upper_price_str) - float(lower_price_str)) / grid_steps
    
    # Create orders
    logger.info("Creating orders directly with proper formatting:")
    
    successful_orders = 0
    for i in range(actual_grids):
        # Calculate grid price
        grid_price = float(lower_price_str) + price_step * (i + 1)
        grid_price_str = format_price(grid_price, symbol_info)
        grid_price_float = float(grid_price_str)
        
        # Alternate buy/sell orders
        side = "buy" if i % 2 == 0 else "sell"
        
        # Calculate the minimum BTC needed at this price point to meet min notional
        min_btc_at_price = calculate_min_quantity_for_notional(grid_price_float, min_notional, symbol_info)
        
        # Calculate quantity in BTC based on the USDT amount we want to use per grid
        btc_quantity = usdt_per_grid / grid_price_float
        
        # Use the larger of the two to ensure we meet minimum notional
        final_btc_quantity = max(btc_quantity, min_btc_at_price)
        
        # Format the quantity (round up to ensure we meet min notional)
        order_size_str = format_quantity(final_btc_quantity, symbol_info, round_up=True)
        
        # Calculate the actual notional value
        notional_value = float(order_size_str) * grid_price_float
        
        logger.info(f"Creating {side} order at {grid_price_str} for {order_size_str} BTC (notional: {notional_value:.2f} USDT)")
        
        # Double-check we meet the minimum notional
        if notional_value < min_notional:
            logger.warning(f"Order notional ({notional_value:.2f} USDT) still below minimum ({min_notional} USDT). This shouldn't happen.")
            logger.warning(f"Price: {grid_price_float}, Min BTC needed: {min_btc_at_price}, Calculated: {final_btc_quantity}, Formatted: {order_size_str}")
            # Try one more time by forcing a larger quantity
            forced_btc = min_notional / grid_price_float * 1.01  # Add 1% buffer
            order_size_str = format_quantity(forced_btc, symbol_info, round_up=True)
            notional_value = float(order_size_str) * grid_price_float
            
            if notional_value < min_notional:
                logger.error(f"Still can't meet minimum notional. Skipping order.")
                continue
        
        try:
            # Debug the exact parameters being sent
            logger.info(f"API parameters: symbol={args.pair}, side={side}, amount={order_size_str}, price={grid_price_str}")
            
            # Create order
            result = exchange_client.create_order(
                symbol=args.pair,
                side=side,
                amount=float(order_size_str),
                price=grid_price_float
            )
            
            if result:
                logger.info(f"Created order: {result}")
                successful_orders += 1
            else:
                logger.error(f"Failed to create order")
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
    
    logger.info(f"Created {successful_orders} out of {actual_grids} orders!")
    
    if successful_orders > 0:
        logger.info("Orders created! Press Ctrl+C to cancel all orders and exit.")
        
        try:
            while True:
                # Get open orders
                orders = exchange_client.get_open_orders(args.pair)
                logger.info(f"Open orders: {len(orders) if orders else 0}")
                for order in orders or []:
                    logger.info(f"  Order: {order}")
                
                # Get positions
                positions = exchange_client.get_positions(args.pair)
                if positions:
                    logger.info(f"Current positions: {positions}")
                else:
                    logger.info("No open positions")
                    
                time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Cancelling all orders...")
            exchange_client.cancel_all_orders(args.pair)
            logger.info("Orders cancelled. Exiting.")
    else:
        logger.error("No orders were created successfully.")

if __name__ == "__main__":
    main() 