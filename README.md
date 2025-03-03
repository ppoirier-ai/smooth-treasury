# Binance Futures Grid Trading Bot

A robust cryptocurrency grid trading bot for Binance Futures that implements an automated grid trading strategy with leverage support. The bot places a series of buy and sell orders at regular price intervals to profit from market volatility.

## Overview

Grid trading is a strategy that:
- Places multiple buy and sell orders at regular price intervals
- Profits from price oscillations in sideways markets
- Automatically maintains grid structure by replacing filled orders
- Uses leverage to increase potential returns (with increased risk)

## Project Structure

```
├── scripts
```

## Prerequisites

- Python 3.9+
- Binance Futures account
- Binance Futures API keys with trading permissions
- Basic understanding of futures trading and leverage

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd binance-futures-grid-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up configuration:
```bash
cp config/config.yaml.example config/config.yaml
# Edit config.yaml with your settings
```

## Quick Start

1. Test your API connection:
```bash
python scripts/test_futures.py YOUR_API_KEY YOUR_API_SECRET
```

2. Run the grid trading bot:
```bash
python scripts/advanced_grid_trader.py YOUR_API_KEY YOUR_API_SECRET BTC/USDT 300 --grids 5 --range-percentage 2.0
```

## Configuration Options

### Grid Trading Parameters

- `--grids`: Number of grid levels (default: 5)
- `--range-percentage`: Price range percentage (default: 2.0)
- `capital`: Trading capital in USDT
- `pair`: Trading pair (e.g., BTC/USDT)

### config.yaml Settings

```yaml
binance:
  testnet: true  # Set to false for live trading
  timeout: 10000

trading:
  default_leverage: 2
  max_active_bots_per_client: 2
  min_grid_spacing: 0.01
```

## Available Scripts

### Testing and Setup
- `test_futures.py`: Test Binance Futures connection
- `check_api_keys.py`: Verify API key configuration
- `exchange_connection_test.py`: Comprehensive exchange testing
- `update_keys_and_test.py`: Update and test API keys

### Trading
- `advanced_grid_trader.py`: Main grid trading bot
- `direct_trade_test.py`: Test direct trading functionality
- `run_bot_with_keys.py`: Run bot with API keys

### Debugging
- `check_grid_bot_params.py`: Verify grid parameters
- `fix_bot_with_keys.py`: Debug and fix bot issues

## Grid Trading Strategy

The bot implements a grid trading strategy with the following features:

1. **Grid Creation**
   - Creates evenly spaced buy/sell orders
   - Adapts to market conditions
   - Uses 2x leverage for increased potential returns

2. **Order Management**
   - Monitors order status
   - Replaces filled orders
   - Maintains grid structure

3. **Position Tracking**
   - Monitors open positions
   - Calculates realized/unrealized P&L
   - Tracks trading history

## Safety Features

- Testnet support for safe testing
- Automatic order size calculation
- Minimum notional value checks
- Clean shutdown process
- Comprehensive error handling

## Monitoring and Management

1. Check bot status:
```bash
python scripts/run_bot_with_keys.py YOUR_API_KEY YOUR_API_SECRET --status
```

2. Monitor active positions:
```bash
python scripts/run_bot_with_keys.py YOUR_API_KEY YOUR_API_SECRET --monitor
```

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Verify API keys are correct
   - Check network connection
   - Ensure Binance Futures is accessible

2. **Order Placement Failures**
   - Check account balance
   - Verify minimum order size
   - Confirm leverage settings

3. **Grid Issues**
   - Validate grid parameters
   - Check price range
   - Verify capital adequacy

## Warning ⚠️

- This bot uses 2x leverage which increases both potential profits and losses
- Always test on testnet before using real funds
- Grid trading may not be suitable for strongly trending markets
- Never trade with funds you cannot afford to lose
- Keep your API keys secure and never share them

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[MIT License](LICENSE)

## Disclaimer

This bot is provided for educational purposes only. Cryptocurrency futures trading with leverage involves substantial risk of loss. Use at your own risk and never trade with money you cannot afford to lose.