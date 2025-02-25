def calculate_grid_levels(lower: float, upper: float, grids: int) -> list[float]:
    """Calculate grid price levels."""
    step = (upper - lower) / (grids - 1)
    return [lower + i * step for i in range(grids)]

def calculate_grid_orders(capital: float, levels: list[float]) -> list[dict]:
    """Calculate grid orders."""
    order_amount = capital / (len(levels) - 1)
    orders = []
    
    for i in range(len(levels) - 1):
        # Buy order at lower level
        orders.append({
            'side': 'buy',
            'price': levels[i],
            'amount': order_amount
        })
        # Sell order at upper level
        orders.append({
            'side': 'sell',
            'price': levels[i + 1],
            'amount': order_amount
        })
    
    return orders 