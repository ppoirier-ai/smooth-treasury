# Directional Grid Bot

## Overview

The Directional Grid Bot is an advanced trading strategy that maintains a directional bias (long or short) while using grid trading principles to optimize returns. Unlike a traditional grid bot that places both buy and sell orders throughout the price range, the directional bot starts with an initial position and then uses grid levels to systematically take profits and re-enter positions.

## Key Features

- **Directional Bias**: Maintains net long or short exposure throughout the trading cycle
- **Initial Position**: Starts with a configurable percentage of capital deployed in the bias direction
- **Take-Profit Grid**: Places orders to systematically capture profits at predefined price levels
- **Automatic Re-entry**: When profit-taking orders are filled, automatically places new orders to re-enter at favorable prices
- **Customizable Parameters**: Adjust capital allocation, grid count, price range, leverage, and initial position sizing

## Requirements

### Functional Requirements

1. **Direction Setting**
   - Support both long and short bias trading
   - Maintain net position in the chosen direction

2. **Initial Position Management**
   - Place initial position using a configurable percentage of total capital
   - Support market orders for initial position entry

3. **Grid Management**
   - For long bias: Place sell orders above entry, buy orders below
   - For short bias: Place buy orders below entry, sell orders above
   - Maintain proper grid spacing based on price range and grid count

4. **Order Lifecycle**
   - Monitor order status (open, filled, canceled)
   - When take-profit orders fill, create new re-entry orders
   - When re-entry orders fill, create new take-profit orders

5. **Capital Allocation**
   - Distribute capital effectively across grid levels
   - Account for leverage in position sizing
   - Handle different contract types (linear vs inverse)

6. **Risk Management**
   - Allow for graceful stopping/starting
   - Properly cancel orders on exit
   - Provide real-time status and profit information

### Technical Requirements

1. **Performance**
   - Efficient order monitoring with minimal API usage
   - Responsive order placement after fills

2. **Error Handling**
   - Graceful handling of API errors and connectivity issues
   - Fail-safe mechanisms for critical operations

3. **Logging**
   - Comprehensive logging of all bot activities
   - Detailed profit tracking and position status

## Behavior

### Long-Biased Grid Bot

1. Places initial long position (e.g., 100% of allocated capital)
2. Places sell orders at intervals above the current price (take-profit orders)
3. When a sell order fills, places a new buy order at a lower price level
4. When that buy order fills, places a new sell order at a higher level
5. Continuously cycles, maintaining net long exposure while buying low and selling high

### Short-Biased Grid Bot

1. Places initial short position (e.g., 100% of allocated capital)
2. Places buy orders at intervals below the current price (take-profit orders)
3. When a buy order fills, places a new sell order at a higher price level
4. When that sell order fills, places a new buy order at a lower level
5. Continuously cycles, maintaining net short exposure while selling high and buying low

## Metrics and Monitoring

- **Active Orders**: Number and details of currently open orders
- **Filled Orders**: History of filled orders
- **Profit Calculation**: Running total of realized profit
- **Position Status**: Current net position and exposure 