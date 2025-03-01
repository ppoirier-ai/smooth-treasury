#!/usr/bin/env python
"""
Comprehensive exchange connection tester
"""
import os
import sys
import requests
import time
import hmac
import hashlib
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_spot_connection(api_key, api_secret, testnet=True):
    """Test Binance Spot API connection"""
    print("\n===== TESTING BINANCE SPOT API =====")
    
    if testnet:
        base_url = "https://testnet.binance.vision"
    else:
        base_url = "https://api.binance.com"
    
    # 1. Test public endpoint (no auth)
    print("\nTesting public endpoint (price)...")
    try:
        response = requests.get(f"{base_url}/api/v3/ticker/price?symbol=BTCUSDT")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! BTC price: {data['price']}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # 2. Test private endpoint (requires auth)
    print("\nTesting private endpoint (account)...")
    timestamp = int(time.time() * 1000)
    
    params = {
        'timestamp': timestamp,
        'recvWindow': 5000
    }
    
    query_string = '&'.join([f"{key}={params[key]}" for key in params])
    signature = hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    url = f"{base_url}/api/v3/account?{query_string}&signature={signature}"
    headers = {
        'X-MBX-APIKEY': api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            balances = {asset['asset']: float(asset['free']) for asset in data['balances'] if float(asset['free']) > 0}
            print(f"✅ Success! Account connected.")
            print(f"Balances: {json.dumps(balances, indent=2)}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            print("\nPossible issues:")
            if "API-key format invalid" in response.text:
                print("- API key format is invalid")
            elif "Signature" in response.text:
                print("- Signature is incorrect (API secret might be wrong)")
            elif "Invalid API-key" in response.text:
                print("- API key is invalid or doesn't have permission")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    return

def test_futures_connection(api_key, api_secret, testnet=True):
    """Test Binance Futures API connection"""
    print("\n===== TESTING BINANCE FUTURES API =====")
    
    if testnet:
        base_url = "https://testnet.binancefuture.com"
    else:
        base_url = "https://fapi.binance.com"
    
    # 1. Test public endpoint (no auth)
    print("\nTesting public endpoint (price)...")
    try:
        response = requests.get(f"{base_url}/fapi/v1/ticker/price?symbol=BTCUSDT")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! BTC price: {data['price']}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # 2. Test private endpoint (requires auth)
    print("\nTesting private endpoint (account)...")
    timestamp = int(time.time() * 1000)
    
    params = {
        'timestamp': timestamp,
        'recvWindow': 5000
    }
    
    query_string = '&'.join([f"{key}={params[key]}" for key in params])
    signature = hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    url = f"{base_url}/fapi/v2/balance?{query_string}&signature={signature}"
    headers = {
        'X-MBX-APIKEY': api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            balances = {asset['asset']: float(asset['availableBalance']) for asset in data if float(asset['availableBalance']) > 0}
            print(f"✅ Success! Account connected.")
            print(f"Balances: {json.dumps(balances, indent=2)}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            print("\nPossible issues:")
            if "API-key format invalid" in response.text:
                print("- API key format is invalid")
            elif "Signature" in response.text:
                print("- Signature is incorrect (API secret might be wrong)")
            elif "Invalid API-key" in response.text:
                print("- API key is invalid or doesn't have permission")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # 3. Test order placement
    print("\nTesting market order placement (not executing)...")
    print("Skipping actual order placement to prevent accidental trades")
    
    return

def test_database_keys():
    """Test keys stored in database"""
    print("\n===== TESTING DATABASE API KEYS =====")
    
    try:
        from common.database.connection import get_session
        from common.database.models import Client
        
        # Force SQLite connection
        os.environ["DATABASE_URL"] = "sqlite:///./grid_bot.db"
        
        # Connect to database
        session = get_session()
        
        # Get all clients
        clients = session.query(Client).all()
        
        print(f"Found {len(clients)} clients in database:")
        for client in clients:
            print(f"\nClient ID: {client.client_id}")
            print(f"Testnet: {client.is_testnet}")
            print(f"API Key: {client.api_key[:10]}...")
            print(f"API Secret: {client.api_secret[:10]}...")
        
        session.close()
    except Exception as e:
        print(f"❌ Error accessing database: {str(e)}")

def main():
    # Check if arguments provided
    if len(sys.argv) == 3:
        api_key = sys.argv[1]
        api_secret = sys.argv[2]
        
        print(f"Testing with provided API keys:")
        print(f"API Key: {api_key[:5]}...{api_key[-5:]}")
        print(f"API Secret: {api_secret[:5]}...{api_secret[-5:]}")
        
        # Test both types of connections
        test_spot_connection(api_key, api_secret, testnet=True)
        test_futures_connection(api_key, api_secret, testnet=True)
    else:
        print("No API keys provided, checking database...")
        test_database_keys()
        
        print("\nUsage: python exchange_connection_test.py <api_key> <api_secret>")
        print("To test with specific API keys, provide them as arguments.")

if __name__ == "__main__":
    main() 