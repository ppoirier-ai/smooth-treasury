#!/usr/bin/env python
"""
Direct Binance Testnet API test using requests.
"""
import sys
import requests
import time
import hmac
import hashlib
import json

def main():
    if len(sys.argv) != 3:
        print("Usage: python direct_test.py <api_key> <api_secret>")
        return
    
    api_key = sys.argv[1]
    api_secret = sys.argv[2]
    
    print(f"Testing connection with provided API keys...")
    
    # Base URLs for Binance Testnet
    base_url = "https://testnet.binance.vision"
    
    # 1. Test ticker endpoint (public - no auth needed)
    ticker_url = f"{base_url}/api/v3/ticker/price?symbol=BTCUSDT"
    print(f"\nFetching ticker from: {ticker_url}")
    
    response = requests.get(ticker_url)
    if response.status_code == 200:
        data = response.json()
        print(f"BTC/USDT price: {data['price']}")
    else:
        print(f"Failed to get ticker: {response.text}")
    
    # Get server time to avoid timestamp issues
    server_time_url = f"{base_url}/api/v3/time"
    print(f"\nGetting server time from: {server_time_url}")
    
    response = requests.get(server_time_url)
    if response.status_code == 200:
        data = response.json()
        server_timestamp = data['serverTime']
        print(f"Server time: {server_timestamp}")
        
        # Calculate time difference
        local_timestamp = int(time.time() * 1000)
        time_diff = local_timestamp - server_timestamp
        print(f"Time difference: {time_diff}ms")
    else:
        print(f"Failed to get server time: {response.text}")
        server_timestamp = int(time.time() * 1000) - 1000  # Subtract 1 second as fallback
    
    # 2. Test account endpoint (private - requires auth)
    endpoint = "/api/v3/account"
    
    # Use server timestamp instead of local time
    timestamp = server_timestamp
    
    # Prepare the query string
    query_string = f"timestamp={timestamp}"
    
    # Create signature
    signature = hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Final URL with query string and signature
    url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
    
    # Headers with API key
    headers = {
        'X-MBX-APIKEY': api_key
    }
    
    print(f"\nFetching account info from: {base_url}{endpoint}")
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        
        # Print balances
        print("\nAccount balances:")
        for balance in data['balances']:
            # Only show non-zero balances
            free = float(balance['free'])
            locked = float(balance['locked'])
            if free > 0 or locked > 0:
                print(f"{balance['asset']}: Free={free}, Locked={locked}")
                
        print("\nAccount permissions:", data.get('permissions', 'Unknown'))
        print("Connection test successful!")
    else:
        print(f"Failed to get account info: {response.status_code} - {response.text}")

    # 3. Test open orders endpoint
    endpoint = "/api/v3/openOrders"
    
    # Use server timestamp
    timestamp = server_timestamp + 1000  # Add 1 second to ensure it's fresh
    
    # Prepare the query string
    query_string = f"timestamp={timestamp}"
    
    # Create signature
    signature = hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Final URL with query string and signature
    url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
    
    print(f"\nFetching open orders from: {base_url}{endpoint}")
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} open orders")
        for order in data:
            print(f"Order: {order['side']} {order['origQty']} {order['symbol']} @ {order['price']}")
    else:
        print(f"Failed to get open orders: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main() 