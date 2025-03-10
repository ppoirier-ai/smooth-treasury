# Directional Grid Bot: Visual Example

## Long-Biased Grid Bot Example

Using the following parameters:
- **Symbol:** BTCUSD
- **Capital:** $50,000
- **Grid Count:** 10 (5 above, 5 below current price)
- **Range:** 1%
- **Current Price:** $78,000
- **Initial Position:** 100%

### Initial Setup

```
Price: $78,000
                                  
$78,780  SELL 5,000 contracts  ↑
$78,682  SELL 5,000 contracts  |
$78,585  SELL 5,000 contracts  | Take-profit levels
$78,487  SELL 5,000 contracts  | (Sell orders)
$78,390  SELL 5,000 contracts  ↓

$78,000  INITIAL POSITION: BUY 50,000 contracts at market

$77,902  BUY 5,000 contracts  ↑
$77,805  BUY 5,000 contracts  |
$77,707  BUY 5,000 contracts  | Re-entry/accumulation levels
$77,610  BUY 5,000 contracts  | (Buy orders)
$77,512  BUY 5,000 contracts  ↓
```

### After One Sell Order Fills

```
Price: $78,390
                                  
$78,780  SELL 5,000 contracts  ↑
$78,682  SELL 5,000 contracts  | Remaining take-profit levels
$78,585  SELL 5,000 contracts  | (Sell orders)
$78,487  SELL 5,000 contracts  ↓

$78,390  ✓ FILLED: SELL 5,000 contracts (Profit taken)

$78,000  INITIAL POSITION (45,000 contracts remain)

$77,902  BUY 5,000 contracts  ↑
$77,805  BUY 5,000 contracts  |
$77,707  BUY 5,000 contracts  | Re-entry/accumulation levels
$77,610  BUY 5,000 contracts  | (Buy orders)
$77,512  BUY 5,000 contracts  ↓
```

### After One Buy Order Fills

```
Price: $77,902
                                  
$78,780  SELL 5,000 contracts  ↑
$78,682  SELL 5,000 contracts  | Take-profit levels
$78,585  SELL 5,000 contracts  | (Sell orders)
$78,487  SELL 5,000 contracts  ↓
$78,390  SELL 5,000 contracts ← New sell order placed after buy filled

$78,000  INITIAL POSITION (45,000 contracts remain)

$77,902  ✓ FILLED: BUY 5,000 contracts (Position replenished)

$77,805  BUY 5,000 contracts  ↑
$77,707  BUY 5,000 contracts  | Remaining re-entry levels
$77,610  BUY 5,000 contracts  | (Buy orders)
$77,512  BUY 5,000 contracts  ↓
```

### The Cycle Continues

As the price moves up and down within the range:
1. Sell orders fill when price rises, generating profit
2. Buy orders fill when price falls, accumulating at lower prices
3. New orders are constantly placed to maintain the grid structure
4. The bot maintains its directional bias with a net long position

### Key Points

1. **Dual-Sided Grid**: The bot places both buy and sell orders from the start
2. **Always Net Long**: Maintains directional exposure by always being net long
3. **Dynamic Grid Management**: Replaces filled orders to maintain the grid
4. **Profit From Volatility**: Makes money from price oscillations while maintaining directional exposure

## Comparison to Regular Grid Bot

A regular (non-directional) grid bot would:
- Have equal capital allocated to buys and sells across the range
- Not necessarily start with an initial position
- Potentially achieve a neutral position if all orders fill

The directional grid bot is different because:
- It starts with an initial position in the bias direction
- It maintains a net position in the bias direction throughout
- Order sizes may be asymmetric to preserve the directional bias 