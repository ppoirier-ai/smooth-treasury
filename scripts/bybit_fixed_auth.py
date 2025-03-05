#!/usr/bin/env python
import sys
import os
import requests
import hmac
import hashlib
import time
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.utils.logger import setup_logger

logger = setup_logger(__name__)

def test_fixed_auth(api_key, api_secret):
    """Test Bybit auth with the format from the error message."""
    logger.info("=== Testing Bybit Authentication with Fixed Format ===")
    logger.info(f"API Key: {api_key}")
    
    # First get server time
    base_url = "https://api-testnet.bybit.com"
    
    try:
        time_url = f"{base_url}/v5/market/time"
        time_response = requests.get(time_url)
        time_data = time_response.json()
        
        if "result" in time_data and "timeSecond" in time_data["result"]:
            # Use server time
            timestamp = time_data["result"]["timeSecond"] + "000"  # Add milliseconds
            logger.info(f"Using server time: {timestamp}")
        else:
            logger.error("Failed to get server time")
            return False
            
        # Test GET request with new signature format
        endpoint = "/v5/user/query-api"
        recv_window = "20000"
        
        # Based on the error message, Bybit expects the signature to be calculated from:
        # timestamp + api_key + recv_window (without parameter names)
        origin_string = f"{timestamp}{api_key}{recv_window}"
        
        logger.info(f"Using origin string for signature: {origin_string}")
        
        signature = hmac.new(
            bytes(api_secret, "utf-8"),
            bytes(origin_string, "utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        logger.info(f"Generated signature: {signature}")
        
        # Set headers
        headers = {
            "X-BAPI-API-KEY": api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window
        }
        
        # Make request
        url = f"{base_url}{endpoint}"
        
        logger.info(f"Making request to: {url}")
        logger.info(f"With headers: {json.dumps(headers, indent=2)}")
        
        response = requests.get(url, headers=headers)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response content: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if "retCode" in result and result["retCode"] == 0:
                logger.info("✅ Authentication successful!")
                logger.info(f"API key info: {json.dumps(result.get('result', {}), indent=2)}")
                return True
            else:
                logger.error(f"⚠️ API request returned error: {result.get('retMsg', 'Unknown error')}")
                return False
        else:
            logger.error(f"❌ API request failed with status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
        return False
        
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Bybit Authentication with Fixed Format')
    parser.add_argument('--api_key', type=str, required=True, help='API Key')
    parser.add_argument('--api_secret', type=str, required=True, help='API Secret')
    
    args = parser.parse_args()
    
    test_fixed_auth(args.api_key, args.api_secret)

if __name__ == "__main__":
    main() 