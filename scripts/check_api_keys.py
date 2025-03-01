#!/usr/bin/env python
"""
Script to check API keys stored in the database.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.database.connection import get_session
from common.database.models import Client

# First, let's examine crypto module functions
from common.utils import crypto
print("Available functions in crypto module:", dir(crypto))

def main():
    # Connect to database
    session = get_session()
    
    # Get all clients
    clients = session.query(Client).all()
    
    print(f"\nFound {len(clients)} clients in database:")
    for client in clients:
        try:
            # Show encrypted data (raw from database)
            print(f"Client ID: {client.client_id}")
            print(f"Testnet: {client.is_testnet}")
            print(f"Encrypted API Key: {client.api_key[:10]}...")
            print(f"Encrypted API Secret: {client.api_secret[:10]}...")
            print("---")
        except Exception as e:
            print(f"Error accessing client {client.client_id}: {str(e)}")
    
    session.close()

if __name__ == "__main__":
    main() 