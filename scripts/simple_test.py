#!/usr/bin/env python
"""
Simple script to test Binance Testnet connection directly.
"""
import ccxt
import sys

def main():
    if len(sys.argv) != 3:
        print("Usage: python simple_test.py <api_key> <api_secret>")
        return
    
    api_key = sys.argv[1]
    api_secret = sys.argv[2]
    
    print(f"Testing connection with provided API keys...")
    
    # Create exchange with testnet configuration
    exchange = ccxt.binance({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',
        },
        'urls': {
            'api': {
                'public': 'https://testnet.binance.vision/api/v3',
                'private': 'https://testnet.binance.vision/api/v3',
                'v3': 'https://testnet.binance.vision/api/v3',
                'fapiPublic': 'https://testnet.binancefuture.com/fapi/v1',
                'fapiPrivate': 'https://testnet.binancefuture.com/fapi/v1'
            },
            'test': True
        }
    })
    
    try:
        # Try a simple API call first
        print("Fetching testnet ticker...")
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"Current BTC/USDT price: {ticker['last']}")
        
        print("\nFetching account balance...")
        balance = exchange.fetch_balance()
        
        # Show only non-zero balances
        for currency, data in balance['total'].items():
            if data > 0:
                print(f"{currency}: Free={balance['free'][currency]}, Used={balance['used'][currency]}, Total={data}")
        
        print("\nConnection test successful!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 