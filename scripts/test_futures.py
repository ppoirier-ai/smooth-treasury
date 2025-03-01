#!/usr/bin/env python
"""
Test script for Binance Futures Testnet API.
"""
import sys
import requests
import time
import hmac
import hashlib
import json

def main():
    if len(sys.argv) != 3:
        print("Usage: python test_futures.py <api_key> <api_secret>")
        return
    
    api_key = sys.argv[1]
    api_secret = sys.argv[2]
    
    print(f"Testing Binance Futures Testnet connection with provided API keys...")
    
    # Base URLs for Binance Futures Testnet
    base_url = "https://testnet.binancefuture.com"
    
    # 1. Test server time endpoint (public - no auth needed)
    time_url = f"{base_url}/fapi/v1/time"
    print(f"\nFetching server time from: {time_url}")
    
    try:
        response = requests.get(time_url)
        if response.status_code == 200:
            data = response.json()
            server_time = data['serverTime']
            print(f"Server time: {server_time}")
            
            # Calculate time difference
            local_time = int(time.time() * 1000)
            diff = local_time - server_time
            print(f"Time difference: {diff}ms")
        else:
            print(f"Failed to get server time: {response.text}")
            server_time = int(time.time() * 1000)
    except Exception as e:
        print(f"Error connecting to futures API: {str(e)}")
        server_time = int(time.time() * 1000)
    
    # 2. Test ticker endpoint (public - no auth needed)
    ticker_url = f"{base_url}/fapi/v1/ticker/price?symbol=BTCUSDT"
    print(f"\nFetching ticker from: {ticker_url}")
    
    try:
        response = requests.get(ticker_url)
        if response.status_code == 200:
            data = response.json()
            print(f"BTC/USDT price: {data['price']}")
        else:
            print(f"Failed to get ticker: {response.text}")
    except Exception as e:
        print(f"Error fetching ticker: {str(e)}")
    
    # 3. Test account endpoint (private - requires auth)
    endpoint = "/fapi/v2/balance"
    timestamp = server_time
    
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
    print(f"Using API Key: {api_key[:5]}...{api_key[-5:]}")
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            
            # Print balances
            print("\nAccount balances:")
            for asset in data:
                # Only show non-zero balances
                if float(asset['balance']) > 0:
                    print(f"{asset['asset']}: Available={asset['availableBalance']}, Balance={asset['balance']}")
                    
            print("\nConnection test successful!")
        else:
            print(f"Failed to get account info: {response.status_code} - {response.text}")
            
            # Special handling for API key issues
            if response.status_code == 401 or "API-key" in response.text:
                print("\n👉 API KEY ISSUE: You need to create API keys specifically for Binance Futures Testnet")
                print("1. Go to https://testnet.binancefuture.com/")
                print("2. Click on the user icon and select API Management")
                print("3. Create a new API key with Futures permissions")
    except Exception as e:
        print(f"Error connecting to Binance Futures API: {str(e)}")

if __name__ == "__main__":
    main() 