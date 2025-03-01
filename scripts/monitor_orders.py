#!/usr/bin/env python
"""
Monitor existing orders on Binance Futures
"""
import sys
import os
import argparse
import logging
import time
from scripts.grid_trade_monitor import get_account_positions

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.exchange.futures_client import FuturesExchangeClient

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Monitor existing orders')
    parser.add_argument('api_key', help='Binance API key')
    parser.add_argument('api_secret', help='Binance API secret')
    parser.add_argument('pair', help='Trading pair, e.g. BTC/USDT')
    
    args = parser.parse_args()
    
    # Create exchange client
    exchange_client = FuturesExchangeClient(args.api_key, args.api_secret, testnet=True)
    
    # Monitoring loop
    logger.info(f"Monitoring orders for {args.pair}... Press Ctrl+C to exit.")
    
    try:
        while True:
            # Get current price
            current_price = exchange_client.get_ticker(args.pair)
            if current_price:
                logger.info(f"Current price: {current_price}")
            
            # Get open orders
            open_orders = exchange_client.get_open_orders(args.pair)
            logger.info(f"Open orders: {len(open_orders) if open_orders else 0}")
            
            for order in open_orders or []:
                logger.info(f"  Order {order['id']}: {order['side']} {order['amount']} @ {order['price']}")
            
            # Get account positions
            positions = get_account_positions(args.api_key, args.api_secret, testnet=True)
            active_positions = []
            
            if positions:
                for pos in positions:
                    if float(pos.get('positionAmt', 0)) != 0:
                        active_positions.append(pos)
                
                if active_positions:
                    logger.info("Active positions:")
                    for pos in active_positions:
                        symbol = pos.get('symbol', '')
                        amount = float(pos.get('positionAmt', 0))
                        entry_price = float(pos.get('entryPrice', 0))
                        pnl = float(pos.get('unRealizedProfit', 0))
                        
                        logger.info(f"  {symbol}: {amount} @ {entry_price} (PnL: {pnl:.2f} USDT)")
                else:
                    logger.info("No active positions")
            
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Exiting monitoring.")

if __name__ == "__main__":
    main() 