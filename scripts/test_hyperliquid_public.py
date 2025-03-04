import sys
import os
import json
import time
from hyperliquid.info import Info

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Hyperliquid Public API')
    parser.add_argument('--coin', type=str, default='BTC', help='Coin to test (default: BTC)')
    parser.add_argument('--testnet', action='store_true', help='Use testnet')
    
    args = parser.parse_args()
    
    try:
        # Initialize the Info client for public endpoints
        base_url = "https://dev.hyperliquid.xyz" if args.testnet else "https://api.hyperliquid.xyz"
        info = Info(base_url)
        
        logger.info(f"🔍 Testing Hyperliquid Public API at {base_url}")
        
        # Test metadata
        try:
            meta = info.meta()
            logger.info("✅ Successfully retrieved exchange metadata")
            
            # Get and display available coins
            available_coins = [asset['name'] for asset in meta['universe']]
            logger.info(f"Available assets count: {len(available_coins)}")
            logger.info(f"Sample assets: {json.dumps(available_coins[:10], indent=2)}")
            
            # Check if the requested coin is available
            coin = args.coin.upper().strip()
            if coin in available_coins:
                logger.info(f"✅ Requested coin {coin} is available on Hyperliquid")
            else:
                logger.warning(f"⚠️ Requested coin {coin} is not found in available assets")
                similar_coins = [c for c in available_coins if coin in c]
                if similar_coins:
                    logger.info(f"Similar coins: {similar_coins}")
        except Exception as e:
            logger.error(f"❌ Error getting metadata: {str(e)}")
        
        time.sleep(1)
        
        # Test market data
        try:
            prices = info.all_mids()
            logger.info("✅ Successfully retrieved all market prices")
            
            # Display specific coin price if available
            coin = args.coin.upper().strip()
            if coin in prices:
                logger.info(f"Current {coin} price: ${prices[coin]}")
            
            # Display sample of prices
            sample_prices = {k: prices[k] for k in list(prices.keys())[:5]}
            logger.info(f"Sample prices: {json.dumps(sample_prices, indent=2)}")
        except Exception as e:
            logger.error(f"❌ Error getting prices: {str(e)}")
        
        time.sleep(1)
        
        # Test orderbook using l2snapshot instead of l2_book
        try:
            coin = args.coin.upper().strip()
            # Use correct method name from SDK
            orderbook = info.l2snapshot(coin)
            logger.info(f"✅ Successfully retrieved orderbook for {coin}")
            
            # Format orderbook for better readability
            asks = orderbook.get('asks', [])[:5]  # First 5 asks
            bids = orderbook.get('bids', [])[:5]  # First 5 bids
            
            logger.info(f"Top 5 asks (sell orders):")
            for ask in asks:
                logger.info(f"  Price: ${ask[0]} - Size: {ask[1]}")
                
            logger.info(f"Top 5 bids (buy orders):")
            for bid in bids:
                logger.info(f"  Price: ${bid[0]} - Size: {bid[1]}")
        except Exception as e:
            logger.error(f"❌ Error getting orderbook: {str(e)}")
            logger.info("Trying alternative method...")
            
            # Try alternative method if the first one fails
            try:
                orderbook_data = {
                    "type": "l2Book",
                    "coin": coin,
                    "depth": 5
                }
                orderbook = info.post("/info", orderbook_data)
                logger.info(f"✅ Successfully retrieved orderbook using alternative method")
                logger.info(f"Orderbook data: {json.dumps(orderbook, indent=2)}")
            except Exception as e2:
                logger.error(f"❌ Alternative method also failed: {str(e2)}")
            
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    main() 