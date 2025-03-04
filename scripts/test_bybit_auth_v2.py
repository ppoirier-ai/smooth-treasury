#!/usr/bin/env python
import sys
import os
import hmac
import hashlib
import time
import requests
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.utils.logger import setup_logger

logger = setup_logger(__name__)

def test_auth_get(api_key, api_secret):
    """Test Bybit authentication for GET request using headers."""
    logger.info("\n===== Testing Bybit GET Authentication =====")
    
    # Bybit testnet URL
    base_url = "https://api-testnet.bybit.com"
    endpoint = "/v5/account/wallet-balance"
    
    # Timestamp and parameters
    timestamp = str(int(time.time() * 1000))
    recv_window = "20000"  # Extended window for testing
    
    # Query parameters
    params = {
        "accountType": "UNIFIED"
    }
    
    # Create parameter string for signature
    param_str = ""
    
    # Add timestamp, key and window to param string
    param_str += f"accountType=UNIFIED&api_key={api_key}&recv_window={recv_window}&timestamp={timestamp}"
    
    logger.info(f"Param string for signature: {param_str}")
    
    # Generate HMAC signature
    signature = hmac.new(
        bytes(api_secret, "utf-8"),
        bytes(param_str, "utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    logger.info(f"Generated signature: {signature}")
    
    # Set up headers according to Bybit documentation
    headers = {
        "X-BAPI-API-KEY": api_key,
        "X-BAPI-SIGN": signature,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-RECV-WINDOW": recv_window
    }
    
    # Full URL with query parameters
    url = f"{base_url}{endpoint}?accountType=UNIFIED"
    
    logger.info(f"Making GET request to: {url}")
    logger.info(f"Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response content: {response.text}")
        
        if response.status_code == 200:
            logger.info("✅ GET Authentication successful!")
            return True
        else:
            logger.error("❌ GET Authentication failed.")
            return False
    except Exception as e:
        logger.error(f"Error making GET request: {str(e)}")
        return False

def test_auth_post(api_key, api_secret):
    """Test Bybit authentication for POST request using headers."""
    logger.info("\n===== Testing Bybit POST Authentication =====")
    
    # Bybit testnet URL
    base_url = "https://api-testnet.bybit.com"
    endpoint = "/v5/position/switch-isolated"  # Simple endpoint that requires auth
    
    # Timestamp and parameters
    timestamp = str(int(time.time() * 1000))
    recv_window = "20000"  # Extended window for testing
    
    # POST request body
    post_data = {
        "category": "inverse",
        "symbol": "BTCUSD",
        "tradeMode": 0  # 0 for cross margin
    }
    
    # Create parameter string for signature including body data
    param_str = timestamp + api_key + recv_window + json.dumps(post_data)
    
    logger.info(f"String for signature: {param_str}")
    
    # Generate HMAC signature
    signature = hmac.new(
        bytes(api_secret, "utf-8"),
        bytes(param_str, "utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    logger.info(f"Generated signature: {signature}")
    
    # Set up headers according to Bybit documentation
    headers = {
        "X-BAPI-API-KEY": api_key,
        "X-BAPI-SIGN": signature,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-RECV-WINDOW": recv_window,
        "Content-Type": "application/json"
    }
    
    url = f"{base_url}{endpoint}"
    
    logger.info(f"Making POST request to: {url}")
    logger.info(f"Headers: {headers}")
    logger.info(f"Body: {post_data}")
    
    try:
        response = requests.post(url, headers=headers, json=post_data)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response content: {response.text}")
        
        if response.status_code == 200:
            logger.info("✅ POST Authentication successful!")
            return True
        else:
            logger.error("❌ POST Authentication failed.")
            return False
    except Exception as e:
        logger.error(f"Error making POST request: {str(e)}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Bybit API Authentication v2')
    parser.add_argument('--api_key', type=str, required=True, help='API Key')
    parser.add_argument('--api_secret', type=str, required=True, help='API Secret')
    parser.add_argument('--method', type=str, choices=['get', 'post', 'both'], default='both', help='HTTP method to test')
    
    args = parser.parse_args()
    
    if args.method in ['get', 'both']:
        test_auth_get(args.api_key, args.api_secret)
    
    if args.method in ['post', 'both']:
        test_auth_post(args.api_key, args.api_secret)

if __name__ == "__main__":
    main() 