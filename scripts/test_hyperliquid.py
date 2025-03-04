import sys
import os
import requests
import json
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.utils.logger import setup_logger

logger = setup_logger(__name__)

class HyperliquidTester:
    def __init__(self, wallet_address: str, signature: str):
        self.wallet_address = wallet_address
        self.signature = signature
        self.base_url = "https://api.hyperliquid.xyz/api/v1"
        
    def test_connection(self) -> bool:
        """Test basic API connection."""
        try:
            # Test public endpoint - get all markets
            url = f"{self.base_url}/info/meta"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Public API connection successful")
                logger.info(f"API Response: {json.dumps(data, indent=2)}")
                return True
            else:
                logger.error(f"❌ Public API connection failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Connection test failed: {str(e)}")
            return False
    
    def get_market_data(self, coin: str = "BTC") -> Dict[str, Any]:
        """Get current market data."""
        try:
            url = f"{self.base_url}/info/allMids"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Successfully retrieved market data")
                logger.info(f"Price data: {json.dumps(data, indent=2)}")
                return data
            else:
                logger.error(f"❌ Failed to get market data: {response.text}")
                return {}
        except Exception as e:
            logger.error(f"❌ Error getting market data: {str(e)}")
            return {}
    
    def get_orderbook(self, coin: str = "BTC") -> Dict[str, Any]:
        """Get orderbook for a symbol."""
        try:
            coin = coin.upper().strip()
            
            url = f"{self.base_url}/info/l2Book"
            data = {
                "coin": coin,
                "depth": 5  # Get top 5 levels
            }
            response = requests.post(url, json=data)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Successfully retrieved orderbook for {coin}")
                logger.info(f"Orderbook data: {json.dumps(data, indent=2)}")
                return data
            else:
                logger.error(f"❌ Failed to get orderbook: {response.text}")
                logger.info("Available coins: BTC, ETH, ARB, OP, etc.")
                return {}
        except Exception as e:
            logger.error(f"❌ Error getting orderbook: {str(e)}")
            return {}
    
    def get_user_state(self) -> Dict[str, Any]:
        """Get user's account state."""
        try:
            url = f"{self.base_url}/info/user"
            data = {
                "type": "userState",
                "user": self.wallet_address
            }
            response = requests.post(url, json=data)
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Successfully retrieved user state")
                logger.info(f"User state: {json.dumps(data, indent=2)}")
                return data
            else:
                logger.error(f"❌ Failed to get user state: {response.text}")
                return {}
        except Exception as e:
            logger.error(f"❌ Error getting user state: {str(e)}")
            return {}

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Hyperliquid API Connection')
    parser.add_argument('wallet_address', type=str, help='Wallet Address')
    parser.add_argument('signature', type=str, help='Signature')
    parser.add_argument('--coin', type=str, default='BTC', help='Coin to test (default: BTC)')
    
    args = parser.parse_args()
    
    tester = HyperliquidTester(args.wallet_address, args.signature)
    
    logger.info("🔍 Testing Hyperliquid API Connection...")
    
    # Test basic connection and get markets
    if not tester.test_connection():
        logger.error("❌ Basic connection test failed. Exiting...")
        return
    
    # Get market data
    logger.info("\n📊 Getting market data...")
    tester.get_market_data()
    
    # Get orderbook
    logger.info(f"\n📚 Getting orderbook for {args.coin}...")
    tester.get_orderbook(args.coin)
    
    # Get user state
    logger.info("\n👤 Getting user state...")
    tester.get_user_state()

if __name__ == "__main__":
    main() 