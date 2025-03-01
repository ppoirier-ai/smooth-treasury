#!/usr/bin/env python
"""
Script to test the exchange connection.
"""
import sys
import os
import logging
import pathlib
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up configuration path
root_dir = pathlib.Path(__file__).parent.parent.absolute()
os.environ['CONFIG_PATH'] = str(root_dir / 'config' / 'dev_config.yaml')

from common.database.connection import get_session
from common.database.models import Client
from common.exchange.client import ExchangeClient
from common.utils.crypto import decrypt_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_json(data: Dict[str, Any]) -> None:
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2))

def main():
    """Test the exchange connection."""
    if len(sys.argv) < 2:
        print("Usage: python test_exchange.py <client_id>")
        sys.exit(1)
    
    client_id = int(sys.argv[1])
    
    session = get_session()
    
    try:
        # Get client from database
        client = session.query(Client).filter_by(client_id=client_id).first()
        if not client:
            logger.error(f"Client {client_id} not found")
            sys.exit(1)
        
        # Decrypt API keys
        api_key = decrypt_key(client.api_key)
        api_secret = decrypt_key(client.api_secret)
        
        # Create exchange client
        exchange = ExchangeClient(api_key, api_secret, testnet=client.is_testnet)
        
        # Test basic functionality
        print("\n--- Exchange Connection Test ---\n")
        
        # Get BTC/USDT ticker
        print("Testing price ticker:")
        btc_price = exchange.get_ticker("BTC/USDT")
        print(f"Current BTC/USDT price: {btc_price}\n")
        
        # Get account balance
        print("Testing account balance:")
        balances = exchange.get_account_balance()
        print_json(balances)
        print()
        
        # Get open orders
        print("Testing open orders:")
        open_orders = exchange.get_open_orders("BTC/USDT")
        print(f"Found {len(open_orders)} open orders")
        if open_orders:
            print_json(open_orders[0])  # Print first order as sample
        print()
        
        # Place small test order if balance allows
        btc_balance = balances.get('BTC', {}).get('free', 0)
        usdt_balance = balances.get('USDT', {}).get('free', 0)
        
        if btc_balance >= 0.001:
            # Place sell order significantly above market price so it won't fill
            sell_price = btc_price * 1.1  # 10% above market
            print(f"Placing test SELL order: 0.001 BTC at ${sell_price}")
            sell_order = exchange.create_order("BTC/USDT", "sell", 0.001, sell_price)
            if sell_order:
                print_json(sell_order)
            print()
        
        if usdt_balance >= 100:
            # Place buy order significantly below market price so it won't fill
            buy_price = btc_price * 0.9  # 10% below market
            buy_amount = 100 / buy_price
            print(f"Placing test BUY order: {buy_amount:.8f} BTC at ${buy_price}")
            buy_order = exchange.create_order("BTC/USDT", "buy", buy_amount, buy_price)
            if buy_order:
                print_json(buy_order)
            print()
        
        # Get open orders again to see our new orders
        print("Checking open orders after placing test orders:")
        open_orders = exchange.get_open_orders("BTC/USDT")
        print(f"Found {len(open_orders)} open orders")
        for order in open_orders:
            print(f"Order {order['id']}: {order['side']} {order['amount']} BTC at ${order['price']}")
        print()
        
        # Ask if we should cancel all orders
        answer = input("Do you want to cancel all open orders? (y/n): ")
        if answer.lower() == 'y':
            print("Cancelling all open orders...")
            result = exchange.cancel_all_orders("BTC/USDT")
            print(f"Cancel result: {result}")
            
            # Verify cancellation
            open_orders = exchange.get_open_orders("BTC/USDT")
            print(f"Open orders after cancellation: {len(open_orders)}")
        
        print("\nExchange test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    main() 