# Bybit Grid Trading Bot

A grid trading bot implementation for Bybit exchange. This bot creates a grid of buy and sell orders within a specified price range to profit from price oscillations.

## Features

- Precision-aware order placement that respects Bybit's minimum quantity and price requirements
- Grid trading strategy with configurable parameters
- Automatic order replacement when orders are filled
- Profit tracking and performance metrics
- Can run on both testnet and mainnet

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/your-username/smooth-treasury.git
   cd smooth-treasury
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure your API keys by updating the runner script or creating a config file.

## Usage

### Basic Usage

Run the grid bot with default settings:

```
python scripts/run_precision_grid_bot.py
```

### Advanced Options

Customize the grid bot behavior:

```
python scripts/run_precision_grid_bot.py --symbol BTC/USDT --capital 100 --grid-count 5 --range-pct 2.0 --duration 3600
```

Parameters:
- `--symbol`: Trading pair to use (default: BTC/USDT)
- `--capital`: Amount to allocate in USDT (default: 100)
- `--grid-count`: Number of grid levels (default: 5)
- `--range-pct`: Price range percentage (default: 2.0)
- `--duration`: How long to run the bot in seconds (default: 300)
- `--testnet`: Use testnet instead of mainnet

## Grid Strategy Explanation

The grid strategy:

1. Divides a price range into equally-spaced levels
2. Places buy orders below current price and sell orders above current price
3. When a buy order is filled, places a sell order at the same price level (and vice versa)
4. Profits from price oscillations within the range

## Warning

Trading bots can lose money! Use at your own risk and start with small amounts on testnet first.