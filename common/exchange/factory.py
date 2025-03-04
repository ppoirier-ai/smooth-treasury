from typing import Optional
from common.exchange.base_client import BaseExchangeClient
from common.exchange.binance_client import BinanceClient
from common.exchange.hyperliquid_client import HyperliquidClient

class ExchangeFactory:
    """Factory for creating exchange clients."""
    
    @staticmethod
    def create_exchange(
        exchange_name: str,
        api_key: str,
        api_secret: str,
        testnet: bool = True
    ) -> Optional[BaseExchangeClient]:
        """Create an exchange client instance."""
        exchange_name = exchange_name.lower()
        
        if exchange_name == "binance":
            return BinanceClient(api_key, api_secret, testnet)
        elif exchange_name == "hyperliquid":
            return HyperliquidClient(api_key, api_secret, testnet)
        else:
            raise ValueError(f"Unsupported exchange: {exchange_name}") 