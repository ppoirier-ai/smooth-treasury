#!/usr/bin/env python
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    # Get API credentials from environment variables
    api_key = os.environ.get('BYBIT_API_KEY')
    api_secret = os.environ.get('BYBIT_API_SECRET')
    
    if not api_key or not api_secret:
        logger.error("API key and secret must be set as environment variables: BYBIT_API_KEY and BYBIT_API_SECRET")
        return
    
    # Dynamically check if pybit is installed
    try:
        from pybit.unified_trading import HTTP
    except ImportError:
        logger.error("pybit package not found. Installing...")
        os.system("pip install pybit")
        from pybit.unified_trading import HTTP
    
    logger.info("Initializing Bybit client using environment variables...")
    
    try:
        # Initialize client with environment variables
        session = HTTP(
            testnet=True,
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Simple test - get server time
        server_time = session.get_server_time()
        logger.info(f"Server time: {json.dumps(server_time, indent=2)}")
        
        # Test if key is valid
        user_api_info = session.get_api_key_information()
        logger.info(f"API key information: {json.dumps(user_api_info, indent=2)}")
        
        logger.info("✅ API key validation successful!")
        
    except Exception as e:
        logger.error(f"❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    main() 