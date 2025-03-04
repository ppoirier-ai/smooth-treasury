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

def verify_key(api_key, api_secret):
    """Verify if a Bybit API key is valid using the simplest possible approach."""
    logger.info("=== Verifying Bybit API Key ===")
    logger.info(f"API Key: {api_key}")
    
    # 1. Get server time
    base_url = "https://api-testnet.bybit.com"
    
    try:
        # First, get server time
        time_url = f"{base_url}/v5/market/time"
        logger.info(f"Getting server time from: {time_url}")
        
        time_response = requests.get(time_url)
        time_data = time_response.json()
        
        if time_response.status_code != 200:
            logger.error(f"Failed to get server time. Status: {time_response.status_code}")
            logger.error(f"Response: {time_response.text}")
            return False
            
        logger.info(f"Server time response: {json.dumps(time_data, indent=2)}")
        
        if "result" in time_data and "timeSecond" in time_data["result"]:
            server_time = time_data["result"]["timeSecond"] + "000"  # Add milliseconds
            logger.info(f"Using server time: {server_time}")
        else:
            logger.error("Invalid server time response format")
            return False
            
        # 2. Make a simple authenticated request - get account type
        endpoint = "/v5/user/query-api"
        
        # Headers with timestamp from server
        timestamp = server_time
        recv_window = "20000"  # Large window for testing
        
        # Create signature
        param_str = f"api_key={api_key}&recv_window={recv_window}&timestamp={timestamp}"
        
        signature = hmac.new(
            bytes(api_secret, "utf-8"),
            bytes(param_str, "utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        # Set headers
        headers = {
            "X-BAPI-API-KEY": api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window
        }
        
        # Make request
        url = f"{base_url}{endpoint}"
        logger.info(f"Testing API key with request to: {url}")
        logger.info(f"Using headers: {json.dumps(headers, indent=2)}")
        
        response = requests.get(url, headers=headers)
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response content: {response.text}")
        
        # If successful, this should return information about the API key
        if response.status_code == 200:
            result = response.json()
            if "retCode" in result and result["retCode"] == 0:
                logger.info("✅ API key is valid and working correctly!")
                logger.info(f"API key details: {json.dumps(result.get('result', {}), indent=2)}")
                return True
            else:
                logger.error(f"⚠️ API request succeeded but returned error: {result.get('retMsg', 'Unknown error')}")
                return False
        else:
            logger.error(f"❌ API key verification failed with status {response.status_code}")
            logger.error(f"Error message: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during verification: {str(e)}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify Bybit API Key')
    parser.add_argument('--api_key', type=str, required=True, help='API Key')
    parser.add_argument('--api_secret', type=str, required=True, help='API Secret')
    
    args = parser.parse_args()
    
    verify_key(args.api_key, args.api_secret)

if __name__ == "__main__":
    main() 