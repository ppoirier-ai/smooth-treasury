"""Utility functions for handling symbol information and precision."""
from typing import Dict, Any
from common.utils.logger import setup_logger

logger = setup_logger(__name__)

def get_symbol_info(client, symbol):
    """Get detailed symbol information to determine quantity precision."""
    try:
        # Extract base and quote currencies - handle both formats
        if "/" in symbol:
            base, quote = symbol.split('/')
        else:
            # For symbols like "BTCUSD"
            # Default assumption: first 3 chars are base, rest is quote
            # Better to have exchange-specific logic here
            if symbol.endswith('USD'):
                base = symbol[:-3]
                quote = 'USD'
            else:
                # Generic fallback
                base = symbol[:3]
                quote = symbol[3:]
        
        # Get instrument info from Bybit
        category = client._detect_symbol_category(symbol)
        normalized_symbol = client._normalize_symbol(symbol)
        
        params = {
            "category": category,
            "symbol": normalized_symbol
        }
        
        response = client._get_public("/v5/market/instruments-info", params)
        
        if response and "result" in response and "list" in response["result"]:
            symbol_info = response["result"]["list"][0]
            
            # Extract lot size filter and price filter
            filters = {}
            if "lotSizeFilter" in symbol_info:
                filters["lotSizeFilter"] = symbol_info["lotSizeFilter"]
            if "priceFilter" in symbol_info:
                filters["priceFilter"] = symbol_info["priceFilter"]
            
            # Extract relevant fields
            min_qty = float(filters.get("lotSizeFilter", {}).get("minOrderQty", "0.001"))
            qty_step = float(filters.get("lotSizeFilter", {}).get("qtyStep", "0.001"))
            min_price = float(filters.get("priceFilter", {}).get("minPrice", "0.01"))
            price_step = float(filters.get("priceFilter", {}).get("tickSize", "0.01"))
            
            return {
                "symbol": symbol,
                "min_qty": min_qty,
                "qty_step": qty_step,
                "min_price": min_price,
                "price_step": price_step,
                "info": symbol_info
            }
        
        # Fallback to default values
        logger.warning(f"Could not get precise symbol info for {symbol}, using defaults")
        return {
            "symbol": symbol,
            "min_qty": 0.001,  # Default min BTC quantity
            "qty_step": 0.001, # Default BTC step
            "min_price": 0.5,  # Default min price step
            "price_step": 0.5  # Default price step
        }
    
    except Exception as e:
        logger.error(f"Error getting symbol info: {str(e)}")
        return {
            "symbol": symbol,
            "min_qty": 0.001,  # Default min BTC quantity
            "qty_step": 0.001, # Default BTC step
            "min_price": 0.5,  # Default min price step
            "price_step": 0.5  # Default price step
        }

def adjust_quantity(amount, symbol_info):
    """Adjust quantity to match exchange requirements."""
    min_qty = symbol_info["min_qty"]
    qty_step = symbol_info["qty_step"]
    
    # Ensure minimum quantity
    amount = max(amount, min_qty)
    
    # Round to valid step size
    steps = round(amount / qty_step)
    amount = steps * qty_step
    
    # Format to appropriate precision
    precision = len(str(qty_step).split('.')[-1])
    formatted_amount = format(amount, f'.{precision}f')
    
    return formatted_amount

def adjust_price(price, symbol_info):
    """Adjust price to match exchange requirements."""
    price_step = symbol_info["price_step"]
    
    # Round to valid price step
    steps = round(price / price_step)
    price = steps * price_step
    
    # Format to appropriate precision
    precision = len(str(price_step).split('.')[-1])
    formatted_price = format(price, f'.{precision}f')
    
    return formatted_price 