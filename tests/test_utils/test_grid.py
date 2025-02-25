import pytest
from common.utils.grid import calculate_grid_levels, calculate_grid_orders

def test_calculate_grid_levels():
    """Test grid level calculation."""
    levels = calculate_grid_levels(lower=20000, upper=25000, grids=5)
    assert len(levels) == 5
    assert levels[0] == 20000
    assert levels[-1] == 25000
    assert all(levels[i] < levels[i+1] for i in range(len(levels)-1))

def test_calculate_grid_orders():
    """Test grid order calculation."""
    levels = [20000, 21000, 22000, 23000]
    orders = calculate_grid_orders(capital=1.0, levels=levels)
    
    assert len(orders) == 6  # (n-1) * 2 orders for n levels
    
    # Check order structure
    for order in orders:
        assert 'side' in order
        assert 'price' in order
        assert 'amount' in order
        assert order['side'] in ['buy', 'sell']
        assert order['amount'] > 0

    # Check total capital usage
    total_buy_amount = sum(o['amount'] for o in orders if o['side'] == 'buy')
    assert abs(total_buy_amount - 1.0) < 0.0001 