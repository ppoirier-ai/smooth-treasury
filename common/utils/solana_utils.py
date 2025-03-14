"""
Utility functions for interacting with Solana blockchain.
"""

from solana.rpc.api import Client
from solana.publickey import PublicKey
from solana.transaction import Transaction
from solana.keypair import Keypair
import base58
import json
import time

def decode_private_key(private_key_string):
    """Decode a private key from various formats."""
    try:
        # Try base58 format first
        if len(private_key_string) == 88 or len(private_key_string) == 44:
            return base58.b58decode(private_key_string)
        
        # Try JSON format
        try:
            json_data = json.loads(private_key_string)
            if isinstance(json_data, list):
                return bytes(json_data)
        except:
            pass
            
        # Try hex format
        if private_key_string.startswith('0x'):
            return bytes.fromhex(private_key_string[2:])
        
        # Default to base58 with error handling
        return base58.b58decode(private_key_string)
    except Exception as e:
        raise ValueError(f"Failed to decode private key: {e}")

def get_current_slot(client):
    """Get the current slot on Solana blockchain."""
    return client.get_slot()['result']

def get_balance(client, public_key):
    """Get SOL balance for a wallet."""
    response = client.get_balance(public_key)
    if 'result' in response:
        # Convert lamports to SOL
        return response['result']['value'] / 1000000000
    return 0

def wait_for_confirmation(client, signature, timeout=60):
    """Wait for a transaction to be confirmed."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        resp = client.get_signature_statuses([signature])
        if resp['result']['value'][0] is not None:
            if resp['result']['value'][0]['confirmationStatus'] == 'confirmed':
                return True
        time.sleep(0.5)
    return False
