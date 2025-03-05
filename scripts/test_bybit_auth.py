#!/usr/bin/env python
import sys
import os
import hmac
import hashlib
import time
import requests
from urllib.parse import urlencode

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.utils.logger import setup_logger

logger = setup_logger(__name__)

def test_auth(api_key, api_secret):
    """Test Bybit authentication using raw request construction."""
    logger.info("Testing Bybit API authentication...")
    logger.info(f"API Key: {api_key}")
    
    # Bybit testnet URL
    base_url = "https://api-testnet.bybit.com"
    
    # Simple endpoint that requires authentication
    endpoint = "/v5/account/wallet-balance"
    
    # Current timestamp in milliseconds
    timestamp = str(int(time.time() * 1000))
    
    # Parameters
    params = {
        "accountType": "UNIFIED",  # For unified account
        "timestamp": timestamp,
        "api_key": api_key,
        "recv_window": "5000"
    }
    
    # Create signature string (param1=value1&param2=value2...)
    sorted_params = dict(sorted(params.items()))
    param_str = urlencode(sorted_params)
    
    # Log the param string being used for signature
    logger.info(f"Param string for signature: {param_str}")
    
    # Generate signature using HMAC-SHA256
    signature = hmac.new(
        bytes(api_secret, "utf-8"),
        bytes(param_str, "utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    # Add signature to parameters
    params["sign"] = signature
    
    # Construct full URL
    url = f"{base_url}{endpoint}"
    
    # Make request
    logger.info(f"Making request to: {url}")
    logger.info(f"With parameters: {params}")
    
    try:
        response = requests.get(url, params=params)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response content: {response.text}")
        
        if response.status_code == 200:
            logger.info("✅ Authentication successful!")
            return True
        else:
            logger.error("❌ Authentication failed.")
            return False
    except Exception as e:
        logger.error(f"Error making request: {str(e)}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Bybit API Authentication')
    parser.add_argument('--api_key', type=str, required=True, help='API Key')
    parser.add_argument('--api_secret', type=str, required=True, help='API Secret')
    
    args = parser.parse_args()
    
    test_auth(args.api_key, args.api_secret)

if __name__ == "__main__":
    main() 