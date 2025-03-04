#!/usr/bin/env python
import sys
import os
import hmac
import hashlib
import time
import json
import requests
from urllib.parse import urlencode

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.utils.logger import setup_logger

logger = setup_logger(__name__)

def debug_auth(api_key, api_secret):
    """Debug Bybit authentication with detailed output."""
    logger.info("==== Debugging Bybit Authentication ====")
    logger.info(f"API Key: {api_key}")
    
    # Get server time first
    base_url = "https://api-testnet.bybit.com"
    
    # 1. First get server time for synchronization
    logger.info("\n1. Checking server time...")
    try:
        time_url = f"{base_url}/v5/market/time"
        time_response = requests.get(time_url)
        time_data = time_response.json()
        
        if time_data and "result" in time_data and "timeSecond" in time_data["result"]:
            server_time = int(time_data["result"]["timeSecond"]) * 1000
            local_time = int(time.time() * 1000)
            time_diff = local_time - server_time
            
            logger.info(f"Server time: {server_time}")
            logger.info(f"Local time: {local_time}")
            logger.info(f"Time difference: {time_diff}ms")
            
            # Use server time directly
            timestamp = str(server_time)
        else:
            logger.error("Failed to get server time")
            timestamp = str(int(time.time() * 1000))
    except Exception as e:
        logger.error(f"Error getting server time: {str(e)}")
        timestamp = str(int(time.time() * 1000))
    
    # 2. Test GET request with proper server time
    logger.info("\n2. Testing GET request with server time...")
    recv_window = "20000"  # Use a large window to account for timing issues
    
    # Endpoint & params
    endpoint = "/v5/account/wallet-balance"
    params = {
        "accountType": "UNIFIED"
    }
    
    # Create param string
    param_str = f"accountType=UNIFIED&api_key={api_key}&recv_window={recv_window}&timestamp={timestamp}"
    
    logger.info(f"Param string: {param_str}")
    
    # Generate signature
    signature = hmac.new(
        bytes(api_secret, "utf-8"),
        bytes(param_str, "utf-8"),
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
    url = f"{base_url}{endpoint}?accountType=UNIFIED"
    
    logger.info(f"Making GET request to: {url}")
    logger.info(f"Headers: {json.dumps(headers, indent=2)}")
    
    try:
        response = requests.get(url, headers=headers)
        status_code = response.status_code
        response_text = response.text
        
        logger.info(f"Response status code: {status_code}")
        logger.info(f"Response content: {response_text}")
        
        # Try to parse response
        try:
            response_json = response.json()
            if "retCode" in response_json:
                logger.info(f"Return code: {response_json['retCode']}")
                logger.info(f"Return message: {response_json.get('retMsg', 'No message')}")
        except:
            pass
        
        if status_code == 200:
            logger.info("✅ GET Authentication successful!")
        else:
            logger.error("❌ GET Authentication failed.")
    except Exception as e:
        logger.error(f"Error making GET request: {str(e)}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Debug Bybit API Authentication')
    parser.add_argument('--api_key', type=str, required=True, help='API Key')
    parser.add_argument('--api_secret', type=str, required=True, help='API Secret')
    
    args = parser.parse_args()
    
    debug_auth(args.api_key, args.api_secret)

if __name__ == "__main__":
    main() 