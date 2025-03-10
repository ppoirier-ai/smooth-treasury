# Directional Grid Bot: Visual Example

## Long-Biased Grid Bot Example

Using the following parameters:
- **Symbol:** BTCUSD
- **Capital:** $50,000
- **Grid Count:** 10
- **Range:** 1%
- **Current Price:** $78,000
- **Initial Position:** 100%

### Initial Setup

```
Price: $78,000
                                  
$78,780  SELL 5,000 contracts  ↑
$78,682  SELL 5,000 contracts  |
$78,585  SELL 5,000 contracts  |
$78,487  SELL 5,000 contracts  | Take-profit levels
$78,390  SELL 5,000 contracts  | (Sell orders)
$78,292  SELL 5,000 contracts  |
$78,195  SELL 5,000 contracts  |
$78,097  SELL 5,000 contracts  ↓

$78,000  INITIAL POSITION: BUY 50,000 contracts at market

(No buy orders initially - they get placed when sell orders are filled)
```

### After First Sell Order Fills

```
Price: $78,097
                                  
$78,780  SELL 5,000 contracts  ↑
$78,682  SELL 5,000 contracts  |
$78,585  SELL 5,000 contracts  |
$78,487  SELL 5,000 contracts  | Remaining take-profit levels
$78,390  SELL 5,000 contracts  | (Sell orders)
$78,292  SELL 5,000 contracts  |
$78,195  SELL 5,000 contracts  ↓

$78,097  ✓ FILLED: SELL 5,000 contracts (Profit taken)

$77,902  BUY 5,000 contracts ← New re-entry order placed after sell filled
```

### After Re-entry Order Fills

```
Price: $77,902
                                  
$78,780  SELL 5,000 contracts  ↑
$78,682  SELL 5,000 contracts  |
$78,585  SELL 5,000 contracts  |
$78,487  SELL 5,000 contracts  | Remaining take-profit levels
$78,390  SELL 5,000 contracts  | (Sell orders)
$78,292  SELL 5,000 contracts  |
$78,195  SELL 5,000 contracts  ↓

$78,097  SELL 5,000 contracts ← New sell order placed after buy filled

$77,902  ✓ FILLED: BUY 5,000 contracts (Position replenished)
```

### The Cycle Continues

As the price moves up and down within the range:
1. Sell orders fill when price rises, generating profit
2. Buy orders fill when price falls, replenishing the position
3. New orders are constantly placed to maintain the grid

### Key Points

1. **Always Net Long**: The bot maintains directional exposure by always being net long
2. **Strategic Order Placement**: Only places sell orders above current price initially
3. **Dynamic Grid Management**: Creates new orders as existing ones fill
4. **Profit From Volatility**: Makes money from price oscillations while maintaining directional exposure

## Comparison to Regular Grid Bot

A regular (non-directional) grid bot would:
- Place both buy and sell orders throughout the entire price range initially
- Not have an initial directional position
- Not maintain a consistent directional bias

The directional grid bot is more suitable when you have a longer-term directional view but want to optimize returns from shorter-term price movements. 