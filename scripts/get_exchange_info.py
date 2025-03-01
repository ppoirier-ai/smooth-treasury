#!/usr/bin/env python
"""
Get Binance exchange information for proper precision handling
"""
import sys
import os
import requests
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_futures_exchange_info(testnet=True):
    """Get futures exchange information from Binance"""
    if testnet:
        url = "https://testnet.binancefuture.com/fapi/v1/exchangeInfo"
    else:
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to get exchange info: {response.text}")
        return None

def get_symbol_info(exchange_info, symbol):
    """Get specific symbol information"""
    if not exchange_info or 'symbols' not in exchange_info:
        return None
        
    # Convert to standard format (BTC/USDT -> BTCUSDT)
    if '/' in symbol:
        symbol = symbol.replace('/', '')
        
    for symbol_info in exchange_info['symbols']:
        if symbol_info['symbol'] == symbol:
            return symbol_info
    
    return None

def print_symbol_precision_info(symbol_info):
    """Print precision information for a symbol"""
    if not symbol_info:
        logger.error("Symbol information not found")
        return
        
    print(f"\nPrecision Information for {symbol_info['symbol']}:")
    print(f"  Status: {symbol_info['status']}")
    print(f"  Base Asset: {symbol_info['baseAsset']}")
    print(f"  Quote Asset: {symbol_info['quoteAsset']}")
    
    # Print price filter
    price_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER'), None)
    if price_filter:
        print(f"\nPrice Filter:")
        print(f"  Min Price: {price_filter['minPrice']}")
        print(f"  Max Price: {price_filter['maxPrice']}")
        print(f"  Tick Size: {price_filter['tickSize']} (price increment)")
    
    # Print lot size filter
    lot_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
    if lot_filter:
        print(f"\nLot Size Filter:")
        print(f"  Min Quantity: {lot_filter['minQty']}")
        print(f"  Max Quantity: {lot_filter['maxQty']}")
        print(f"  Step Size: {lot_filter['stepSize']} (quantity increment)")
    
    # Print market lot size filter
    market_lot_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'MARKET_LOT_SIZE'), None)
    if market_lot_filter:
        print(f"\nMarket Lot Size Filter:")
        print(f"  Min Quantity: {market_lot_filter['minQty']}")
        print(f"  Max Quantity: {market_lot_filter['maxQty']}")
        print(f"  Step Size: {market_lot_filter['stepSize']}")
    
    # Print min notional filter
    min_notional = next((f for f in symbol_info['filters'] if f['filterType'] == 'MIN_NOTIONAL'), None)
    if min_notional:
        print(f"\nMin Notional Filter:")
        print(f"  Min Notional: {min_notional['notional']} (minimum order value)")
    
    print("\nRecommended settings for running the bot:")
    if price_filter:
        price_precision = len(price_filter['tickSize'].rstrip('0').split('.')[1]) if '.' in price_filter['tickSize'] else 0
        print(f"  Price Precision: {price_precision} (--price-precision)")
    
    if lot_filter:
        qty_precision = len(lot_filter['stepSize'].rstrip('0').split('.')[1]) if '.' in lot_filter['stepSize'] else 0
        print(f"  Quantity Precision: {qty_precision} (--qty-precision)")
    
    if min_notional:
        print(f"  Minimum Capital: {float(min_notional['notional'])} (minimum capital to trade)")

def main():
    # Get exchange info
    exchange_info = get_futures_exchange_info(testnet=True)
    if not exchange_info:
        return
    
    # Ask for symbol
    symbol = input("Enter symbol (e.g., BTC/USDT or BTCUSDT): ").strip().upper()
    
    # Get and print symbol info
    symbol_info = get_symbol_info(exchange_info, symbol)
    if symbol_info:
        print_symbol_precision_info(symbol_info)
    else:
        print(f"Symbol {symbol} not found. Available symbols:")
        for symbol in exchange_info['symbols']:
            if symbol['status'] == 'TRADING':
                print(f"  {symbol['symbol']}")

if __name__ == "__main__":
    main() 