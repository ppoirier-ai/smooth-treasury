#!/usr/bin/env python
"""
Direct trading test - minimal version that places real orders on testnet.
"""
import sys
import requests
import time
import hmac
import hashlib
import json
import random

def main():
    if len(sys.argv) != 3:
        print("Usage: python direct_trade_test.py <api_key> <api_secret>")
        return
    
    api_key = sys.argv[1]
    api_secret = sys.argv[2]
    
    print(f"Testing trading with provided API keys...")
    
    # Base URLs for Binance Futures Testnet
    base_url = "https://testnet.binancefuture.com"
    
    # 1. Get server time to avoid timestamp issues
    time_url = f"{base_url}/fapi/v1/time"
    print(f"\nGetting server time from: {time_url}")
    
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
    
    # 2. Get current BTC price
    ticker_url = f"{base_url}/fapi/v1/ticker/price?symbol=BTCUSDT"
    print(f"\nFetching ticker from: {ticker_url}")
    
    try:
        response = requests.get(ticker_url)
        if response.status_code == 200:
            data = response.json()
            current_price = float(data['price'])
            print(f"BTC/USDT price: {current_price}")
        else:
            print(f"Failed to get ticker: {response.text}")
            return
    except Exception as e:
        print(f"Error fetching ticker: {str(e)}")
        return
    
    # 3. Calculate grid price levels
    print("\nCalculating grid price levels...")
    lower_price = current_price * 0.95  # 5% below current price
    upper_price = current_price * 1.05  # 5% above current price
    
    grid_count = 3
    grid_step = (upper_price - lower_price) / grid_count
    
    grid_prices = []
    for i in range(grid_count + 1):
        price = lower_price + i * grid_step
        grid_prices.append(round(price, 2))
    
    print(f"Grid prices: {grid_prices}")
    
    # 4. Place test buy limit order at lowest grid level
    buy_price = grid_prices[0]
    small_amount = 0.001  # Very small BTC amount
    
    order_id = f"test-{random.randint(1000, 9999)}"
    print(f"\nPlacing test BUY order: {small_amount} BTC at ${buy_price}")
    
    # Prepare the order parameters
    timestamp = server_time + 1000  # Add 1 second to ensure timestamp is valid
    
    params = {
        'symbol': 'BTCUSDT',
        'side': 'BUY',
        'type': 'LIMIT',
        'timeInForce': 'GTC',
        'quantity': small_amount,
        'price': buy_price,
        'timestamp': timestamp,
        'recvWindow': 5000,
        'newClientOrderId': order_id
    }
    
    # Sign the request
    query_string = '&'.join([f"{key}={params[key]}" for key in params])
    signature = hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Final URL with query string and signature
    url = f"{base_url}/fapi/v1/order?{query_string}&signature={signature}"
    
    # Headers with API key
    headers = {
        'X-MBX-APIKEY': api_key
    }
    
    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Order placed successfully!")
            print(json.dumps(data, indent=2))
            
            order_id = data['orderId']
            
            # Wait a moment to ensure the order is registered
            time.sleep(2)
            
            # 5. Get the order status
            print(f"\nChecking order status for order ID: {order_id}")
            
            timestamp = int(time.time() * 1000)
            params = {
                'symbol': 'BTCUSDT',
                'orderId': order_id,
                'timestamp': timestamp,
                'recvWindow': 5000
            }
            
            query_string = '&'.join([f"{key}={params[key]}" for key in params])
            signature = hmac.new(
                api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            url = f"{base_url}/fapi/v1/order?{query_string}&signature={signature}"
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                print("\n✅ Order status retrieved successfully!")
                print(json.dumps(data, indent=2))
                
                # 6. Cancel the order to clean up
                print(f"\nCancelling order ID: {order_id}")
                
                timestamp = int(time.time() * 1000)
                params = {
                    'symbol': 'BTCUSDT',
                    'orderId': order_id,
                    'timestamp': timestamp,
                    'recvWindow': 5000
                }
                
                query_string = '&'.join([f"{key}={params[key]}" for key in params])
                signature = hmac.new(
                    api_secret.encode('utf-8'),
                    query_string.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                url = f"{base_url}/fapi/v1/order?{query_string}&signature={signature}"
                
                response = requests.delete(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    print("\n✅ Order cancelled successfully!")
                    print(json.dumps(data, indent=2))
                else:
                    print(f"\n❌ Failed to cancel order: {response.status_code} - {response.text}")
            else:
                print(f"\n❌ Failed to get order status: {response.status_code} - {response.text}")
        else:
            print(f"\n❌ Failed to place order: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"\n❌ Error placing order: {str(e)}")
    
    print("\nTest complete!")

if __name__ == "__main__":
    main() 