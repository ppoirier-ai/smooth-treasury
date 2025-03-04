from typing import Dict, Any
from common.exchange.base_client import BaseExchangeClient
from common.exchange.binance_client import BinanceClient
from common.exchange.hyperliquid_client import HyperliquidClient
from common.exchange.bybit_client import BybitClient

def create_exchange(exchange_name: str, api_key: str, api_secret: str, testnet: bool = False) -> BaseExchangeClient:
    """Create an exchange client based on the exchange name.
    
    Args:
        exchange_name: Name of the exchange
        api_key: API key
        api_secret: API secret
        testnet: Whether to use testnet
        
    Returns:
        An exchange client
    """
    if exchange_name.lower() == 'binance':
        return BinanceClient(api_key, api_secret, testnet)
    elif exchange_name.lower() == 'hyperliquid':
        return HyperliquidClient(api_key, api_secret, testnet)
    elif exchange_name.lower() == 'bybit':
        return BybitClient(api_key, api_secret, testnet)
    else:
        raise ValueError(f"Unsupported exchange: {exchange_name}") 