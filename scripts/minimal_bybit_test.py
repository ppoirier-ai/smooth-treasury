#!/usr/bin/env python
import requests
import hmac
import hashlib
import time
import json
import sys

def test_bybit_minimal(api_key, api_secret):
    print("=== Minimal Bybit API Test ===")
    
    # First try public endpoint - no authentication needed
    print("\n1. Testing public endpoint...")
    try:
        public_url = "https://api-testnet.bybit.com/v5/market/time"
        resp = requests.get(public_url)
        print(f"Public endpoint status: {resp.status_code}")
        print(f"Public response: {resp.text}")
        
        if resp.status_code != 200:
            print("⚠️ Public endpoint failed - possible network or server issue")
            return
    except Exception as e:
        print(f"Public endpoint error: {e}")
        return
    
    # Now test a private endpoint
    print("\n2. Testing private endpoint...")
    try:
        # Get server time for timestamp
        server_data = json.loads(resp.text)
        if not server_data.get("result", {}).get("timeSecond"):
            print("⚠️ Could not get server time")
            return
            
        # Use server time
        timestamp = server_data["result"]["timeSecond"] + "000"  # Add milliseconds
        print(f"Using server timestamp: {timestamp}")
        
        # Try testing with Binance's format as a comparison
        # (in case there's an issue with Bybit's specific authentication)
        binance_url = "https://testnet.binancefuture.com/fapi/v2/balance"
        binance_params = {
            "timestamp": timestamp,
        }
        binance_query = "&".join([f"{k}={v}" for k, v in binance_params.items()])
        binance_signature = hmac.new(
            api_secret.encode('utf-8'),
            binance_query.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        binance_params["signature"] = binance_signature
        binance_headers = {
            "X-MBX-APIKEY": api_key
        }
        
        print("\n2a. First trying Binance format as comparison...")
        print(f"Binance URL: {binance_url}")
        print(f"Binance Headers: {binance_headers}")
        print(f"Binance Params: {binance_params}")
        
        binance_resp = requests.get(binance_url, headers=binance_headers, params=binance_params)
        print(f"Binance response status: {binance_resp.status_code}")
        print(f"Binance response: {binance_resp.text}")
        
        # Now try Bybit's approach
        print("\n2b. Now trying Bybit format...")
        bybit_url = "https://api-testnet.bybit.com/v5/user/query-api"
        recv_window = "60000"  # Very large window for testing
        
        # Create parameter string for signature
        param_str = f"api_key={api_key}&recv_window={recv_window}&timestamp={timestamp}"
        
        # Generate signature
        signature = hmac.new(
            bytes(api_secret, "utf-8"),
            bytes(param_str, "utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        # Headers
        headers = {
            "X-BAPI-API-KEY": api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window
        }
        
        print(f"Bybit URL: {bybit_url}")
        print(f"Bybit Headers: {json.dumps(headers, indent=2)}")
        
        bybit_resp = requests.get(bybit_url, headers=headers)
        print(f"Bybit response status: {bybit_resp.status_code}")
        print(f"Bybit response: {bybit_resp.text}")
        
    except Exception as e:
        print(f"Private endpoint error: {e}")
        return

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python minimal_bybit_test.py <api_key> <api_secret>")
        sys.exit(1)
        
    api_key = sys.argv[1]
    api_secret = sys.argv[2]
    
    test_bybit_minimal(api_key, api_secret) 