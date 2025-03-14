# Drift Protocol Integration Guide

This document describes the integration with Drift Protocol on Solana for the grid trading bot.

## Overview

Drift Protocol is a decentralized exchange on the Solana blockchain that offers spot and perpetual futures trading. Our integration allows the grid bot to operate on Drift using cbBTC (Coinbase's wrapped Bitcoin on Solana) and other assets.

## Requirements

To use the Drift integration, you need:

1. A Solana wallet with private key access
2. SOL tokens for transaction fees
3. USDC tokens for trading collateral
4. A Drift account (will be created automatically if not exists)

## Setup

### Generate a Solana Wallet

If you don't already have a Solana wallet, you can generate one:

```
solana-keygen new --outfile drift_wallet.json
```

This will create a new keypair file. **Keep this file secure!**

### Configure Solana RPC

By default, the bot uses public RPC endpoints, but for better reliability, consider using a dedicated RPC provider like:

- Helius
- Triton
- Alchemy

## Running the Bot on Drift

The command to run the grid bot on Drift is similar to Bybit, but with Drift-specific parameters:

```
python scripts/run_drift_grid_bot.py \
  --private-key $(cat drift_wallet.json) \
  --symbol "cbBTC-PERP" \
  --capital 1000 \
  --grid-count 5 \
  --lower 75000 \
  --upper 85000 \
  --direction long \
  --leverage 2 \
  --testnet
```

## Drift-Specific Considerations

### Fees

Drift has a different fee structure than centralized exchanges:

- Maker fee: -0.02% (rebate)
- Taker fee: 0.05%
- Settlement fee: 0.03%

### Solana Network Fees

Each transaction on Solana costs a small amount of SOL. Ensure your wallet has sufficient SOL to cover these fees.

### Transaction Finality

Unlike centralized exchanges with instant execution, Solana transactions typically take 300-600ms to confirm. The bot accounts for this latency.

### Account Funding

You need to deposit funds into your Drift margin account before trading.

## Supported Assets

The initial implementation supports:

- cbBTC-PERP (Coinbase BTC Perpetual)
- SOL-PERP (Solana Perpetual)
- ETH-PERP (Ethereum Perpetual)

## Technical Implementation

### Drift Protocol Integration

The integration uses the Drift Protocol's on-chain program to:

1. Place limit and market orders
2. Cancel orders
3. Track positions
4. Monitor account balances

### Account Structure

Drift uses a different account structure than centralized exchanges:

- User accounts are PDAs (Program Derived Addresses)
- Orders are stored on-chain
- Positions are updated atomically

### Error Handling

Transactions can fail for various reasons on Solana:

- Insufficient SOL for transaction fees
- Blockchain congestion
- Slippage protection triggering

The bot implements robust error handling and retry mechanisms to deal with these issues.

## Troubleshooting

### Common Issues

1. **Transaction Error: "Blockhash not found"**
   - The transaction took too long to process.
   - Solution: The bot will automatically retry with a fresh blockhash.

2. **Insufficient Funds**
   - Either insufficient SOL for transaction fees or insufficient USDC for margin.
   - Solution: Fund your wallet with more SOL or deposit more USDC to your Drift account.

3. **RPC Node Errors**
   - Public RPC nodes may have rate limits or be unreliable.
   - Solution: Use a dedicated RPC provider.

### Logs and Debugging

The bot writes detailed logs to help diagnose issues:

- Solana transaction logs
- Order placement attempts
- Account balance updates

Check these logs when troubleshooting problems.

## Implementation Notes

### SDK Integration

Our implementation uses AnchorPy to interact with the Drift Protocol's Solana program. We've created a dual-mode implementation that:

1. Uses the Drift Protocol SDK when available
2. Falls back to mock implementations for testing and development

This allows testing without needing to connect to the actual Solana blockchain during development.

### Transaction Flow

When placing an order on Drift:

1. The client creates a transaction with the appropriate Drift program instruction
2. The transaction is signed with the user's keypair
3. The transaction is sent to the Solana network
4. The client waits for confirmation
5. Once confirmed, the order is considered placed

### Error Handling

The implementation includes robust error handling for:

- Connection issues with Solana RPC
- Transaction failures
- Insufficient funds
- Account initialization errors

### Mock Mode

For testing without blockchain interaction, set the environment variable `DRIFT_MOCK_MODE=true`.
