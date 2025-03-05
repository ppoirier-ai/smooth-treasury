#!/usr/bin/env python
"""
Grid bot runner with precise quantity handling for Bybit
"""
import sys
import os
import time
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.bot.improved_grid_bot import ImprovedGridBot
from common.exchange.bybit_client import BybitClient
from common.utils.logger import setup_logger

logger = setup_logger(__name__)

def get_symbol_info(client, symbol):
    """Get detailed symbol information to determine quantity precision."""
    try:
        # Extract base and quote currencies
        base, quote = symbol.split('/')
        
        # Get instrument info from Bybit
        category = client._detect_symbol_category(symbol)
        normalized_symbol = client._normalize_symbol(symbol)
        
        params = {
            "category": category,
            "symbol": normalized_symbol
        }
        
        response = client._get_public("/v5/market/instruments-info", params)
        
        if response and "result" in response and "list" in response["result"]:
            symbol_info = response["result"]["list"][0]
            
            # Get precision info
            lot_size_filter = next((f for f in symbol_info.get("lotSizeFilter", {}).items()), {})
            price_filter = next((f for f in symbol_info.get("priceFilter", {}).items()), {})
            
            # Extract relevant fields
            min_qty = float(lot_size_filter.get("minOrderQty", "0.001"))
            qty_step = float(lot_size_filter.get("qtyStep", "0.001"))
            min_price = float(price_filter.get("minPrice", "0.01"))
            price_step = float(price_filter.get("tickSize", "0.01"))
            
            return {
                "symbol": symbol,
                "min_qty": min_qty,
                "qty_step": qty_step,
                "min_price": min_price,
                "price_step": price_step,
                "info": symbol_info
            }
        
        # Fallback to default values
        return {
            "symbol": symbol,
            "min_qty": 0.001,  # Default min BTC quantity
            "qty_step": 0.001, # Default BTC step
            "min_price": 0.5,  # Default min price step
            "price_step": 0.5  # Default price step
        }
    
    except Exception as e:
        logger.error(f"Error getting symbol info: {str(e)}")
        return {
            "symbol": symbol,
            "min_qty": 0.001,  # Default min BTC quantity
            "qty_step": 0.001, # Default BTC step
            "min_price": 0.5,  # Default min price step
            "price_step": 0.5  # Default price step
        }

# Adjust amount to valid quantity according to exchange rules
def adjust_quantity(amount, symbol_info):
    """Adjust quantity to match exchange requirements."""
    min_qty = symbol_info["min_qty"]
    qty_step = symbol_info["qty_step"]
    
    # Ensure minimum quantity
    amount = max(amount, min_qty)
    
    # Round to valid step size
    steps = round(amount / qty_step)
    amount = steps * qty_step
    
    # Format to appropriate precision
    precision = len(str(qty_step).split('.')[-1])
    formatted_amount = format(amount, f'.{precision}f')
    
    return formatted_amount

# Adjust price to valid value according to exchange rules
def adjust_price(price, symbol_info):
    """Adjust price to match exchange requirements."""
    price_step = symbol_info["price_step"]
    
    # Round to valid price step
    steps = round(price / price_step)
    price = steps * price_step
    
    # Format to appropriate precision
    precision = len(str(price_step).split('.')[-1])
    formatted_price = format(price, f'.{precision}f')
    
    return formatted_price

# Main functionality
try:
    # Initialize Bybit client
    client = BybitClient(
        api_key="bcRYdfdO4Z7INAFPcE",
        api_secret="BmACyMG0LoWygr3p03fCv4E4fxrjtrsRsiir",
        testnet=True
    )
    
    # Get current price for setting up the grid
    symbol = "BTC/USDT"
    current_price = client.get_ticker(symbol)["last"]
    print(f"Current {symbol} price: {current_price}")
    
    # Get symbol precision info
    symbol_info = get_symbol_info(client, symbol)
    print(f"Symbol info: Min Qty={symbol_info['min_qty']}, Qty Step={symbol_info['qty_step']}")
    
    # Clean up any existing orders
    print("Cleaning up existing orders...")
    client.cancel_all_orders(symbol)
    time.sleep(2)
    
    # Set grid parameters
    grid_count = 5  # Fewer levels for testing
    range_percentage = 2.0  # 2% range around current price (tighter for testing)
    allocation = 100  # Smaller amount for testing
    
    # Calculate the effective price range
    lower_price = current_price * (1 - range_percentage/100)
    upper_price = current_price * (1 + range_percentage/100)
    
    print(f"Grid range: {lower_price:.2f} to {upper_price:.2f} ({range_percentage}% range)")
    print(f"Grid levels: {grid_count}")
    print(f"Allocation: {allocation} USDT")
    
    # Calculate grid levels
    price_step = (upper_price - lower_price) / grid_count
    price_levels = []
    
    for i in range(grid_count + 1):
        price = lower_price + (i * price_step)
        adjusted_price = float(adjust_price(price, symbol_info))
        price_levels.append(adjusted_price)
    
    print(f"Adjusted price levels: {price_levels}")
    
    # Calculate order amount
    # This is where we need to be careful with Bybit's minimum order requirements
    amount_per_level = allocation / current_price / grid_count
    adjusted_amount = adjust_quantity(amount_per_level, symbol_info)
    
    print(f"Order amount per level: {adjusted_amount} BTC (original: {amount_per_level:.8f})")
    
    # Manual grid placement
    for price in price_levels:
        # Skip if too close to current price
        if abs(price - current_price) / current_price < 0.001:
            print(f"Skipping level {price} (too close to current price)")
            continue
        
        # Determine order side
        side = "buy" if price < current_price else "sell"
        
        print(f"Placing {side} order: {adjusted_amount} BTC @ ${price}")
        
        try:
            # Place the order
            order = client.create_order(
                symbol=symbol,
                side=side,
                amount=float(adjusted_amount),
                price=price
            )
            
            if order and "id" in order:
                print(f"Order placed successfully: {order['id']}")
                time.sleep(1)  # Brief pause to avoid rate limits
            else:
                print(f"Failed to place {side} order at {price}")
        except Exception as e:
            print(f"Error placing order: {str(e)}")
    
    # Check open orders
    time.sleep(2)
    open_orders = client.get_open_orders(symbol)
    print(f"\nPlaced {len(open_orders)} orders")
    
    for order in open_orders:
        print(f"  {order['side']} {order['amount']} BTC @ ${order['price']}")
    
    # Let orders sit for a while
    print("\nOrders placed. Press Ctrl+C to cancel and exit...")
    try:
        for i in range(60):  # Run for ~10 minutes max
            time.sleep(10)
            if i % 6 == 0:  # Every minute
                current_price = client.get_ticker(symbol)["last"]
                print(f"{datetime.now().strftime('%H:%M:%S')} - Current price: {current_price}")
                
                # Check open orders
                open_orders = client.get_open_orders(symbol)
                print(f"  Open orders: {len(open_orders)}")
    except KeyboardInterrupt:
        print("\nStopping by user request")
    
except Exception as e:
    print(f"Error in main execution: {str(e)}")

finally:
    # Clean up all orders
    print("\nCancelling all orders...")
    client.cancel_all_orders(symbol)
    print("All orders cancelled. Exiting.") 