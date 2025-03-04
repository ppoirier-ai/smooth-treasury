import sys
import os
import json
from typing import Dict, Any
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.utils.logger import setup_logger

logger = setup_logger(__name__)

class HyperliquidTester:
    def __init__(self, wallet_address: str, signature: str, testnet: bool = False):
        self.wallet_address = wallet_address
        self.signature = signature
        
        # Initialize SDK clients
        # Hyperliquid URLs
        base_url = "https://dev.hyperliquid.xyz" if testnet else "https://api.hyperliquid.xyz"
        self.info = Info(base_url)
        self.exchange = Exchange(base_url, wallet_address, signature)
        
        logger.info(f"Using {'testnet' if testnet else 'mainnet'} at {base_url}")
    
    def test_connection(self) -> bool:
        """Test basic API connection."""
        try:
            # Get exchange metadata
            meta = self.info.meta()
            logger.info("✅ API connection successful")
            logger.info(f"Exchange metadata: {json.dumps(meta, indent=2)}")
            return True
        except Exception as e:
            logger.error(f"❌ Connection test failed: {str(e)}")
            return False
    
    def get_market_data(self) -> Dict[str, Any]:
        """Get current market data."""
        try:
            # Get all market prices
            prices = self.info.all_mids()
            logger.info("✅ Successfully retrieved market data")
            logger.info(f"Price data: {json.dumps(prices, indent=2)}")
            return prices
        except Exception as e:
            logger.error(f"❌ Error getting market data: {str(e)}")
            return {}
    
    def get_orderbook(self, coin: str = "BTC") -> Dict[str, Any]:
        """Get orderbook for a symbol."""
        try:
            coin = coin.upper().strip()
            
            # Get L2 orderbook
            orderbook = self.info.l2_book(coin)
            logger.info(f"✅ Successfully retrieved orderbook for {coin}")
            logger.info(f"Orderbook data: {json.dumps(orderbook, indent=2)}")
            return orderbook
        except Exception as e:
            logger.error(f"❌ Error getting orderbook: {str(e)}")
            return {}
    
    def get_user_state(self) -> Dict[str, Any]:
        """Get user's account state."""
        try:
            # Get user state
            user_state = self.info.user_state(self.wallet_address)
            logger.info("✅ Successfully retrieved user state")
            logger.info(f"User state: {json.dumps(user_state, indent=2)}")
            return user_state
        except Exception as e:
            logger.error(f"❌ Error getting user state: {str(e)}")
            return {}

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Hyperliquid API Connection')
    parser.add_argument('wallet_address', type=str, help='Wallet Address')
    parser.add_argument('signature', type=str, help='Signature')
    parser.add_argument('--coin', type=str, default='BTC', help='Coin to test (default: BTC)')
    parser.add_argument('--testnet', action='store_true', help='Use testnet')
    
    args = parser.parse_args()
    
    tester = HyperliquidTester(args.wallet_address, args.signature, args.testnet)
    
    logger.info("🔍 Testing Hyperliquid API Connection...")
    
    # Test basic connection
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