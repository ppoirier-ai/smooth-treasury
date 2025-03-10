# Directional Grid Bot Technical Documentation

## Implementation Overview

The Directional Grid Bot is implemented in `common/bot/directional_grid_bot.py` with these key components:

- **DirectionalGridBot class**: Main implementation with grid trading logic
- **run_directional_grid_bot.py**: CLI script to configure and run the bot

## Architecture

### Class Structure

```python
class DirectionalGridBot:
    """Grid trading bot with directional bias (long or short)."""
    
    def __init__(
        self,
        exchange: BaseExchangeClient,
        symbol: str,
        capital: float,
        grid_count: int = 5,
        range_percentage: float = 2.0,
        direction: Literal["long", "short"] = "long",
        leverage: int = 2,
        initial_position_pct: float = 100.0
    ):
        # Initialization logic
```

### Key Methods

- **_calculate_grid_levels()**: Determines price points for the grid
- **_calculate_order_size()**: Calculates position size for each grid level
- **place_initial_position()**: Creates the initial directional position
- **place_grid_orders()**: Places the grid of orders based on direction
- **monitor_and_update()**: Monitors order status and manages the grid
- **_handle_filled_order()**: Handles order fills and places new orders

## Example Execution Flow

### Initialization

1. Bot initializes with parameters and connects to exchange
2. Bot calculates grid levels and order sizes
3. Bot places initial position (if configured)
4. Bot places initial grid orders

### Runtime Execution

For a long-biased bot:

1. **Initial State**:
   - Initial long position placed at market
   - Sell orders placed at intervals above current price

2. **When sell order fills**:
   ```
   _handle_filled_order(): 
     - Record profit from sell
     - Find appropriate lower price level
     - Place new buy order at lower level
   ```

3. **When buy order fills**:
   ```
   _handle_filled_order():
     - Find appropriate higher price level
     - Place new sell order at higher level
   ```

4. **Continuous Monitoring**:
   ```
   monitor_and_update():
     - Check for filled orders
     - Maintain the grid structure
     - Update profit calculations
   ```

## Contract-Specific Logic

The bot handles different contract types:

### Linear Contracts (e.g., BTC/USDT)
- Order size calculated as: `capital_per_grid / avg_price`
- Applies leverage to the base currency amount

### Inverse Contracts (e.g., BTCUSD)
- Order size calculated directly as the USD contract amount
- For BTCUSD, each contract is worth $1 of Bitcoin

## Performance Considerations

1. **API Efficiency**
   - Batch operations where possible
   - Rate limiting awareness

2. **Error Handling**
   - Robust exception handling
   - Multiple retry attempts for critical operations

3. **Memory Management**
   - Efficient data structures for order tracking
   - Periodic cleanup of old order data

## Example Scenario in Detail

### Initial Setup
- Symbol: BTCUSD
- Capital: $50,000
- Grid Count: 50
- Range: 0.1%
- Current BTC Price: $78,000

### Bot Initialization
```
DirectionalGridBot.__init__:
  - calculate_grid_levels() => 50 levels from $77,922 to $78,078
  - calculate_order_size() => 2,000 contracts per grid level
```

### Order Placement
```
DirectionalGridBot.start():
  - place_initial_position() => Market buy 100,000 contracts
  - place_grid_orders() => 
    - For levels below current price: No orders (long bias)
    - For levels above current price: 50 sell orders at calculated levels
```

### Trading Scenario
1. Price moves up to $78,016 (first grid level above entry)
2. Sell order fills for 2,000 contracts, realizing profit
3. Bot places new buy order at $77,961 (first grid level below entry)
4. Price falls to $77,961
5. Buy order fills, replenishing position
6. Bot places new sell order at $78,016
7. Cycle continues...

## Implementation Details for Developers

```python
# Key parts of the implementation

def _handle_filled_order(self, order_id, order_data):
    """Handle a filled order - core logic of the directional grid trading."""
    # extract order details
    side = order_data.get("side")
    price = order_data.get("price")
    amount = order_data.get("amount")
    
    # record the filled order
    self.filled_orders.append({
        "id": order_id,
        "side": side,
        "price": price,
        "amount": amount,
        "time": datetime.now(),
        "type": order_data.get("type", "unknown")
    })
    self.filled_order_ids.add(order_id)
    
    # remove from active positions
    if order_id in self.active_positions:
        del self.active_positions[order_id]
    
    # get current price
    current_price = self._get_current_price()
    
    # place new orders based on direction and side
    if self.direction == "long":
        if side == "sell":  # sell order filled, place new buy order lower
            # Place buy order at a lower price
            # ... implementation details ...
        elif side == "buy":  # buy order filled, place new sell order higher
            # Place sell order at a higher price
            # ... implementation details ...
``` 