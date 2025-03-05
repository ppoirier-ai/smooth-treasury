#!/usr/bin/env python
import sys
import os
import time
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.bot.grid_bot import GridBot
from common.exchange.bybit_client import BybitClient
from common.utils.logger import setup_logger

logger = setup_logger(__name__)

def test_direct_order(client, symbol, is_buy=True, amount=0.001):
    """Place a small direct order to test trading permissions."""
    try:
        logger.info(f"Testing direct {'buy' if is_buy else 'sell'} order...")
        
        # Get current market price
        ticker = client.get_ticker(symbol)
        market_price = ticker["last"]
        logger.info(f"Current market price: {market_price}")
        
        # Place a limit order slightly away from market price
        side = "buy" if is_buy else "sell"
        price = market_price * 0.95 if is_buy else market_price * 1.05
        price = round(price, 2)  # Round to avoid precision issues
        
        logger.info(f"Placing {side} limit order: {amount} {symbol} @ {price}")
        order = client.create_order(
            symbol=symbol,
            side=side,
            amount=amount,
            price=price
        )
        
        logger.info(f"Order placed: {json.dumps(order, indent=2)}")
        
        # Wait a moment then cancel the order
        time.sleep(2)
        if order and "id" in order:
            logger.info(f"Cancelling test order: {order['id']}")
            result = client.cancel_order(symbol, order["id"])
            logger.info(f"Cancel result: {result}")
            return True
        else:
            logger.error("Failed to place test order - no order ID returned")
            return False
    except Exception as e:
        logger.error(f"Error in test order: {str(e)}")
        return False

def check_open_orders(client, symbol):
    """Check if there are any open orders for the symbol."""
    try:
        open_orders = client.get_open_orders(symbol)
        logger.info(f"Open orders for {symbol}: {len(open_orders)}")
        
        if open_orders:
            logger.info("Current open orders:")
            for order in open_orders:
                logger.info(f"  - {order['side']} {order['amount']} @ {order['price']} (ID: {order['id']})")
        else:
            logger.info("No open orders found.")
        
        return open_orders
    except Exception as e:
        logger.error(f"Error checking open orders: {str(e)}")
        return []

def verify_api_permissions(client):
    """Verify that the API key has the necessary permissions."""
    logger.info("Verifying API key permissions...")
    
    try:
        # Test getting account info
        account_info = client._get_private("/v5/user/query-api")
        
        if "result" in account_info and "permissions" in account_info["result"]:
            perms = account_info["result"]["permissions"]
            logger.info(f"API key permissions: {json.dumps(perms, indent=2)}")
            
            if "ContractTrade" in str(perms) or "Spot" in str(perms):
                logger.info("✅ API key has trading permissions")
                return True
            else:
                logger.error("❌ API key doesn't have trading permissions!")
                return False
        else:
            logger.error("❌ Could not verify API key permissions!")
            return False
    except Exception as e:
        logger.error(f"Error verifying API permissions: {str(e)}")
        return False

# Main script starts here
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

# Verify API permissions
if not verify_api_permissions(client):
    print("ERROR: API key doesn't have required permissions. Exiting.")
    sys.exit(1)

# Check for existing open orders
print("\nChecking for existing open orders before starting...")
existing_orders = check_open_orders(client, symbol)
if existing_orders:
    print(f"WARNING: Found {len(existing_orders)} existing open orders. These may interfere with the grid bot.")
    response = input("Do you want to cancel all existing orders? (y/n): ")
    if response.lower() == 'y':
        for order in existing_orders:
            client.cancel_order(symbol, order['id'])
        print("All existing orders cancelled.")

# Test direct order functionality
print("\nTesting direct order placement...")
if not test_direct_order(client, symbol):
    print("ERROR: Direct order test failed. Check logs for details.")
    response = input("Continue anyway? (y/n): ")
    if response.lower() != 'y':
        sys.exit(1)

# Set grid parameters
grid_count = 10  # Number of grid levels
range_percentage = 10.0  # 10% range around current price
allocation = 5000  # Amount to allocate in USDT

# Calculate the effective price range for information
lower_price = current_price * (1 - range_percentage/100)
upper_price = current_price * (1 + range_percentage/100)

print(f"Grid range: {lower_price:.2f} to {upper_price:.2f} ({range_percentage}% range)")
print(f"Grid levels: {grid_count}")
print(f"Allocation: {allocation} USDT")

# Create the grid bot using the correct parameters
bot = GridBot(
    exchange=client,
    symbol=symbol,
    capital=allocation,
    grid_count=grid_count,
    range_percentage=range_percentage
)

print("Bot created. Available methods:")
methods = [method for method in dir(bot) if callable(getattr(bot, method)) and not method.startswith("__")]
print(methods)

# First, initialize the grid
print("\nInitializing grid...")
if hasattr(bot, 'initialize_grid'):
    bot.initialize_grid()

# Print a summary before starting
if hasattr(bot, 'print_summary'):
    print("\nGrid Summary:")
    bot.print_summary()

# Start the bot with a time limit
run_duration = 300  # Run for 5 minutes
print(f"\nStarting grid bot for {run_duration} seconds...")
print(f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

try:
    # Start the bot
    if hasattr(bot, 'start'):
        bot.start()  # This should start the actual grid bot logic
        
        # Check for orders after 30 seconds
        time.sleep(30)
        print("\nVerifying orders after 30 seconds:")
        orders = check_open_orders(client, symbol)
        if not orders:
            print("WARNING: No orders placed after 30 seconds! The bot may not be working correctly.")
            response = input("Continue running? (y/n): ")
            if response.lower() != 'y':
                raise KeyboardInterrupt("User cancelled after order verification")
        
        # Keep the script running for the specified duration
        start_time = time.time() + 30  # Account for the 30 seconds we already waited
        while time.time() - start_time < run_duration:
            # Print current price and time periodically
            current_price = client.get_ticker(symbol)["last"]
            print(f"{datetime.now().strftime('%H:%M:%S')} - Current price: {current_price}")
            
            # Check orders every minute
            if int((time.time() - start_time) / 60) % 2 == 0:  # Every 2 minutes
                check_open_orders(client, symbol)
            
            # Sleep to avoid flooding the console
            time.sleep(10)
            
            # Optionally check profit
            if hasattr(bot, 'calculate_profit'):
                profit = bot.calculate_profit()
                print(f"Current profit: {profit}")
    else:
        print("ERROR: Bot does not have a 'start' method!")
        
except KeyboardInterrupt:
    print("\nBot stopped by user.")
except Exception as e:
    print(f"Error running bot: {str(e)}")
finally:
    # Stop the bot properly
    if hasattr(bot, 'stop'):
        print("\nStopping bot...")
        bot.stop()
    
    # Cancel any remaining orders
    if hasattr(bot, 'cancel_all_orders'):
        print("Cancelling all orders...")
        bot.cancel_all_orders()
    
    print(f"\nBot session ended at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Final profit calculation
    if hasattr(bot, 'calculate_profit'):
        final_profit = bot.calculate_profit()
        print(f"Final profit: {final_profit}")
    
    # Final summary
    if hasattr(bot, 'print_summary'):
        print("\nFinal Grid Summary:")
        bot.print_summary()
    
    # Final order check
    print("\nFinal order check:")
    check_open_orders(client, symbol)