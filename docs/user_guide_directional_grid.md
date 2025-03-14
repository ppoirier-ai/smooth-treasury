# Directional Grid Bot User Guide

The Directional Grid Bot is designed for traders who have a directional view on the market but want to optimize their returns using grid trading principles.

## Getting Started

### Prerequisites

- Exchange API keys with trading permissions
- Python 3.7+ environment with required dependencies

### Basic Usage

Run the directional grid bot with basic parameters:

```bash
python scripts/run_directional_grid_bot.py --symbol "BTCUSD" --capital 50000 --grid-count 50 --range-pct 0.5 --direction long
```

### Command Line Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--symbol` | Trading pair (e.g., "BTCUSD") | "BTC/USDT" |
| `--capital` | Total capital to allocate (in quote currency) | 100 |
| `--grid-count` | Number of grid levels | 5 |
| `--range-pct` | Price range percentage | 3.0 |
| `--duration` | Bot run duration in seconds | 3600 |
| `--testnet` | Use exchange testnet | False |
| `--direction` | Trading direction ("long" or "short") | "long" |
| `--leverage` | Leverage multiplier (1 = no leverage) | 2 |
| `--initial-position` | Percentage of capital for initial position | 50.0 |
| `--close-on-exit` | Close all positions when bot exits | False |

## How It Works

### Long-Biased Example

Let's say you run a long-biased grid bot with these parameters:
- Symbol: BTCUSD
- Capital: $50,000
- Grid Count: 10 (5 above, 5 below current price)
- Range: 1%
- Current BTC Price: $100,000

**Initial Setup:**
1. Bot places an initial long position of $50,000 (at 100% initial position)
2. Bot places 5 sell orders at these prices:
   - $100,200 (sell 10% of position)
   - $100,400 (sell 10% of position)
   - $100,600 (sell 10% of position)
   - $100,800 (sell 10% of position)
   - $101,000 (sell 10% of position)
3. Bot places 5 buy orders at these prices:
   - $99,800 (buy additional 10% of position)
   - $99,600 (buy additional 10% of position)
   - $99,400 (buy additional 10% of position)
   - $99,200 (buy additional 10% of position)
   - $99,000 (buy additional 10% of position)

**When orders fill:**
- When a sell order fills (profit taking), a new sell order is placed at that price level after a buy order fills
- When a buy order fills (accumulation), a new buy order is placed at that price level after a sell order fills
- The grid is continuously maintained with orders on both sides

### Short-Biased Example

For a short-biased grid bot, the process is reversed:
1. Initial short position is placed
2. Buy orders are placed below the entry price (to take profit)
3. When buy orders fill, new sell orders are placed at higher prices
4. The cycle continues, maintaining net short exposure

## Best Practices

1. **Start Small**: Begin with a small capital allocation to test the strategy
2. **Use Testnet First**: Always test on testnet before using real funds
3. **Appropriate Range**: Set a realistic price range (0.5-3% for most markets)
4. **Grid Count**: More grids mean smaller price movements trigger trades
5. **Monitor Regularly**: Check the bot's performance and adjust as needed

## Advanced Strategies

### Narrow Range in Sideways Markets
In rangebound markets, use a narrow price range (0.5-1%) with more grid levels to capture frequent small movements.

### Wider Range in Trending Markets
In strongly trending markets, use a wider range (2-5%) with fewer grid levels to avoid over-trading.

### Partial Position Strategy
Instead of starting with 100% of capital, use 50-75% for the initial position and allow the bot to scale in with remaining capital at lower prices (for long-biased bots).

## Size Considerations for Bybit

When using Bybit inverse contracts like BTCUSD:
- The order size is automatically adjusted to a reasonable contract size
- For BTCUSD, the bot will convert your USD capital to an appropriate number of contracts
- This adjustment helps ensure orders are within reasonable limits, especially at high BTC prices 