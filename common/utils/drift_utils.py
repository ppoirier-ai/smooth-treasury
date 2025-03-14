"""
Utility functions specific to Drift Protocol operations.
"""

from typing import Dict, Any, List, Optional
from solana.publickey import PublicKey
import base64
import json

def derive_user_account(program_id: PublicKey, authority: PublicKey):
    """Derive the user account PDA for Drift protocol."""
    # In a real implementation, this would use the Drift SDK to derive the PDA
    seeds = [b"user", bytes(authority)]
    return PublicKey.find_program_address(seeds, program_id)[0]

def derive_market_account(program_id: PublicKey, market_index: int):
    """Derive the market account PDA for Drift protocol."""
    # In a real implementation, this would use the Drift SDK to derive the PDA
    seeds = [b"market", market_index.to_bytes(4, byteorder='little')]
    return PublicKey.find_program_address(seeds, program_id)[0]

def parse_perp_market_data(data: bytes) -> Dict[str, Any]:
    """Parse perp market account data into a structured format."""
    # This is a placeholder for the actual parsing logic
    # In a real implementation, this would use the Drift SDK to parse the data
    return {
        "market_index": 0,
        "base_asset_reserve": 1000000,
        "quote_asset_reserve": 50000000000,
        "base_asset_amount_long": 500000,
        "base_asset_amount_short": 500000,
        "open_interest": 1000000,
        "mark_price": 75000,
        "funding_rate": 0.0001
    }

def calculate_order_params(
    symbol: str,
    side: str,
    size: float,
    price: Optional[float] = None,
    order_type: str = "limit"
) -> Dict[str, Any]:
    """
    Calculate order parameters for Drift protocol.
    
    Args:
        symbol: Trading pair symbol (e.g., 'cbBTC-PERP')
        side: Order side ('buy' or 'sell')
        size: Order size in base asset
        price: Order price (required for limit orders)
        order_type: Order type ('limit' or 'market')
        
    Returns:
        Dictionary of order parameters for Drift
    """
    # This would be implemented based on Drift's order structure
    return {
        "symbol": symbol,
        "side": side.upper(),
        "size": size,
        "price": price,
        "type": order_type.upper(),
        "reduce_only": False,
        "post_only": False,
        "immediate_or_cancel": order_type.lower() == "market"
    }

def parse_position_data(position_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse position data from Drift into a standardized format."""
    # This would standardize Drift's position format to match our bot's expectations
    return {
        "symbol": position_data.get("symbol", ""),
        "side": "long" if position_data.get("base_asset_amount", 0) > 0 else "short",
        "size": abs(position_data.get("base_asset_amount", 0)),
        "entry_price": position_data.get("entry_price", 0),
        "mark_price": position_data.get("mark_price", 0),
        "liquidation_price": position_data.get("liquidation_price", 0),
        "unrealized_pnl": position_data.get("unrealized_pnl", 0),
        "leverage": position_data.get("leverage", 1)
    }

def format_order_for_tracking(order_response: Dict[str, Any]) -> Dict[str, Any]:
    """Format a Drift order response for tracking in the grid bot."""
    return {
        "order_id": order_response.get("order_id", ""),
        "client_id": order_response.get("client_id", ""),
        "symbol": order_response.get("symbol", ""),
        "side": order_response.get("side", "").lower(),
        "price": float(order_response.get("price", 0)),
        "amount": float(order_response.get("size", 0)),
        "filled": float(order_response.get("filled_size", 0)),
        "status": order_response.get("status", "open"),
        "created_at": order_response.get("created_at", 0)
    }
