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
- Grid Count: 5
- Range: 1%
- Current BTC Price: $100,000

**Initial Setup:**
1. Bot places an initial long position of $50,000 (at 100% initial position)
2. Bot places 5 sell orders at these prices:
   - $100,200 (sell 20% of position)
   - $100,400 (sell 20% of position)
   - $100,600 (sell 20% of position)
   - $100,800 (sell 20% of position)
   - $101,000 (sell 20% of position)

**Scenario 1: Price rises to $100,200**
1. First sell order fills, capturing profit
2. Bot places a new buy order at $99,800 to replenish position

**Scenario 2: Price then falls to $99,800**
1. Buy order fills, replenishing the position
2. Bot places a new sell order at $100,200

**Ongoing Cycle:**
- As sell orders fill (profit taking), new buy orders are placed at lower levels
- As buy orders fill (position replenishment), new sell orders are placed at higher levels
- The bot maintains a net long position throughout, buying low and selling high

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