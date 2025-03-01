#!/usr/bin/env python
"""
Script to update API keys directly and test the connection.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.database.connection import get_session
from common.database.models import Client
from common.exchange.futures_client import FuturesExchangeClient

def main():
    # Set API keys from the test that worked
    api_key = "47d673ccaffaeee0be06465eaec1e9384bb11fdac429953a8001a24fbc97c9bf"
    api_secret = "b5f7cf3fbbb08fd8d79637a74cd43aa321a5ae5c3ed66c052c0d79fedc844180"
    
    print("Testing direct connection with these keys...")
    try:
        # Create futures client directly
        client = FuturesExchangeClient(api_key, api_secret, testnet=True)
        
        # Get BTC/USDT price
        price = client.get_ticker("BTC/USDT")
        print(f"Current BTC/USDT price: {price}")
        
        # Get account balance
        balance = client.get_account_balance("USDT")
        print(f"USDT balance: {balance}")
        
        print("Connection test successful!")
    except Exception as e:
        print(f"Error testing connection: {str(e)}")
    
    # Try to update API keys in database
    try:
        # Force SQLite connection
        os.environ["DATABASE_URL"] = "sqlite:///./grid_bot.db"
        
        # Connect to database
        session = get_session()
        
        # Get first client
        client = session.query(Client).filter(Client.client_id == 1).first()
        if client:
            print(f"Found client: {client.client_id}")
            print(f"Current testnet setting: {client.is_testnet}")
            
            # Update the keys directly (raw, unencrypted)
            client.api_key = api_key
            client.api_secret = api_secret
            client.is_testnet = True
            
            # Save changes
            session.commit()
            print("Updated client keys successfully!")
        else:
            print("Client not found in database!")
        
        session.close()
    except Exception as e:
        print(f"Error updating database: {str(e)}")

if __name__ == "__main__":
    main() 