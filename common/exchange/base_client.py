from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseExchangeClient(ABC):
    """Abstract base class for exchange clients."""
    
    @abstractmethod
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        pass
    
    @abstractmethod
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for a symbol."""
        pass
    
    @abstractmethod
    def get_account_balance(self, currency: str = None) -> Dict[str, Any]:
        """Get account balance."""
        pass
    
    @abstractmethod
    def create_order(self, symbol: str, side: str, amount: float, price: float) -> Optional[Dict]:
        """Create a new order."""
        pass
    
    @abstractmethod
    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all orders for a symbol."""
        pass
    
    @abstractmethod
    def get_open_orders(self, symbol: str) -> list:
        """Get all open orders for a symbol."""
        pass
    
    @abstractmethod
    def get_positions(self, symbol: str = None) -> list:
        """Get current positions."""
        pass 