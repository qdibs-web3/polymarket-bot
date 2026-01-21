# Polymarket Trading Bot - Complete Setup Guide

This comprehensive guide will walk you through setting up and running your Polymarket trading bot. The bot is designed to automatically identify and execute profitable trading opportunities on the Polymarket prediction market platform.

## Table of Contents

1. [Understanding the Bot](#understanding-the-bot)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the Bot](#running-the-bot)
6. [Monitoring Performance](#monitoring-performance)
7. [Safety and Best Practices](#safety-and-best-practices)
8. [Troubleshooting](#troubleshooting)

## Understanding the Bot

The Polymarket trading bot implements several strategies to identify profitable opportunities:

### Trading Strategies

**Arbitrage Strategy**: This is the bot's primary strategy for risk-free profits. When the combined price of YES and NO tokens in a binary market is less than $1.00, the bot can buy both sides and guarantee a profit when the market resolves. For example, if YES costs $0.48 and NO costs $0.50, buying both costs $0.98 but will always pay out $1.00, netting a $0.02 profit per share.

**Value Betting Strategy**: The bot identifies markets where the current price differs significantly from the true probability of an outcome. This requires external probability estimates, which you can configure based on your own research or prediction models. When the bot detects a mispriced market with sufficient edge (default 5%), it places a bet sized according to the Kelly Criterion.

**High-Quality Market Strategy**: The bot focuses on liquid, high-volume markets with tight spreads to minimize execution risk. It places limit orders to capture favorable prices while maintaining safety through strict quality filters.

### Risk Management

The bot includes comprehensive risk management features designed to protect your capital:

- **Position Sizing**: Uses Kelly Criterion (with a conservative quarter-Kelly fraction) to determine optimal bet sizes based on edge and bankroll
- **Daily Loss Limits**: Automatically stops trading if daily losses exceed your configured threshold
- **Daily Profit Targets**: Can optionally stop trading after reaching your daily return goal
- **Maximum Positions**: Limits the number of concurrent open positions to prevent overexposure
- **Quality Filters**: Only trades on markets meeting minimum liquidity and spread requirements

## Prerequisites

Before setting up the bot, ensure you have the following:

### System Requirements

- **Operating System**: Linux, macOS, or Windows with WSL
- **Python**: Version 3.9 or higher
- **Internet Connection**: Stable connection for API access

### Polymarket Account

You need a Polymarket account with funds. The bot supports two types of wallets:

**Email/Magic Wallet** (Recommended for beginners): If you signed up with email, Polymarket uses a Magic wallet. This is the easiest option as allowances are set automatically. Your private key can be exported from your Polymarket account settings.

**MetaMask/Hardware Wallet**: If you use MetaMask or a hardware wallet, you'll need to set token allowances before trading. See the "Setting Token Allowances" section below.

### API Credentials

You need two pieces of information from your Polymarket wallet:

1. **Private Key**: Your wallet's private key for signing transactions
2. **Funder Address**: The address that holds your funds (usually your wallet address)

**Important**: Never share your private key with anyone. Store it securely in the `.env` file, which should never be committed to version control.

## Installation

Follow these steps to install the bot:

### Step 1: Install Python Dependencies

```bash
# Navigate to the bot directory
cd polymarket_bot

# Install required packages
pip install -r requirements.txt
```

This will install the following packages:

- `py-clob-client`: Official Polymarket Python client
- `requests`: HTTP library for API calls
- `pyyaml`: YAML configuration file parser
- `python-dotenv`: Environment variable management
- `web3`: Ethereum library for blockchain interactions

### Step 2: Create Environment File

Create a `.env` file in the root directory with your credentials:

```bash
# Create .env file
touch .env
```

Add your credentials to the `.env` file:

```
POLYMARKET_PRIVATE_KEY="your-private-key-here"
POLYMARKET_FUNDER_ADDRESS="your-wallet-address-here"
```

**Security Note**: The `.env` file contains sensitive information. Make sure it's included in your `.gitignore` file and never share it publicly.

### Step 3: Create Required Directories

```bash
# Create logs directory
mkdir -p logs

# Verify data directory exists
mkdir -p data
```

## Configuration

The bot's behavior is controlled by the `config/config.yaml` file. Here's a detailed explanation of each setting:

### API Settings

```yaml
host: "https://clob.polymarket.com"
chain_id: 137
signature_type: 1
```

- **host**: The Polymarket CLOB API endpoint (don't change unless using testnet)
- **chain_id**: Polygon network ID (137 for mainnet)
- **signature_type**: 
  - `0` for MetaMask/hardware wallets
  - `1` for Email/Magic wallets (default)
  - `2` for browser wallet proxies

### Risk Management Settings

```yaml
max_position_size: 50.0
max_open_positions: 5
max_daily_loss: 25.0
target_daily_return: 0.02
min_edge: 0.05
kelly_fraction: 0.25
```

**Recommended Settings for Beginners**:

- **max_position_size**: Start with $25-$50 per position
- **max_open_positions**: Keep at 3-5 positions
- **max_daily_loss**: Set to 2-5% of your total bankroll
- **target_daily_return**: 2% (0.02) is a reasonable daily goal
- **min_edge**: 5% (0.05) minimum edge for value bets
- **kelly_fraction**: 0.25 (quarter Kelly) is conservative and recommended

**For 2x Daily Target**: To aim for a 2x daily return (100% gain), you would need to set `target_daily_return: 1.0`. However, this is extremely aggressive and not recommended. A more realistic approach is to aim for 2-5% daily returns with consistent execution over time.

### Strategy Settings

```yaml
strategies:
  arbitrage:
    enabled: true
    min_profit_pct: 0.8
  value_betting:
    enabled: true
    external_sources: {}
  high_quality_markets:
    enabled: true
    min_volume: 5000
    min_quality_score: 60
```

- **arbitrage**: Enable this for risk-free profit opportunities
- **value_betting**: Requires external probability estimates (advanced)
- **high_quality_markets**: Focuses on liquid markets with tight spreads

### Bot Operation

```yaml
run_interval_seconds: 60
log_level: "INFO"
data_dir: "data"
```

- **run_interval_seconds**: Time between trading cycles (60 seconds recommended)
- **log_level**: Set to "DEBUG" for detailed logs, "INFO" for normal operation
- **data_dir**: Directory for storing trade history and reports

## Running the Bot

### Starting the Bot

To start the bot, run:

```bash
python src/bot.py
```

You should see output similar to:

```
2026-01-18 12:00:00 - __main__ - INFO - Starting Polymarket Trading Bot
2026-01-18 12:00:00 - polymarket_client - INFO - Polymarket client initialized in TRADING mode
2026-01-18 12:00:00 - __main__ - INFO - Starting new trading cycle...
```

### Running in the Background

To run the bot continuously in the background:

```bash
# Using nohup (Linux/macOS)
nohup python src/bot.py > logs/bot_output.log 2>&1 &

# Using screen (recommended)
screen -S polymarket_bot
python src/bot.py
# Press Ctrl+A, then D to detach
# Reattach with: screen -r polymarket_bot
```

### Stopping the Bot

To stop the bot gracefully:

- If running in foreground: Press `Ctrl+C`
- If running in background: Find the process ID and kill it:

```bash
ps aux | grep bot.py
kill <process_id>
```

## Monitoring Performance

### Real-Time Monitoring

The bot logs all activity to `logs/bot.log`. You can monitor it in real-time:

```bash
tail -f logs/bot.log
```

### Performance Reports

The bot automatically generates performance reports in the `data/` directory. To view your latest report:

```bash
cat data/performance_report_*.txt
```

### Key Metrics to Track

- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of total wins to total losses (aim for >1.5)
- **Daily P&L**: Your daily profit/loss
- **Max Drawdown**: Largest peak-to-trough decline

## Safety and Best Practices

### Start Small

Begin with a small bankroll ($100-$500) to test the bot and understand its behavior. Only increase your capital after you're comfortable with how it operates.

### Monitor Regularly

Check the bot's performance at least once per day. Review the logs and performance reports to ensure it's operating as expected.

### Set Conservative Limits

Use conservative risk settings initially. It's better to make smaller, consistent profits than to risk large losses.

### Understand the Strategies

Make sure you understand how each strategy works before enabling it. The arbitrage strategy is the safest and most straightforward.

### Keep Your Private Key Secure

Never share your private key or commit it to version control. Store it securely in the `.env` file with appropriate file permissions:

```bash
chmod 600 .env
```

### Test in Read-Only Mode First

You can test the bot in read-only mode by setting `trading_enabled: false` in the config. This allows you to see what opportunities the bot would find without actually placing trades.

### Don't Rely on Guarantees

While the bot implements proven strategies, no trading system can guarantee profits. Market conditions change, and there's always risk involved.

## Troubleshooting

### Bot Won't Start

**Issue**: `ModuleNotFoundError` when starting the bot

**Solution**: Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Authentication Errors

**Issue**: "Trading not enabled - missing private key"

**Solution**: Check that your `.env` file exists and contains valid credentials. Make sure you're loading it from the correct directory.

### No Opportunities Found

**Issue**: Bot runs but doesn't find any trading opportunities

**Solution**: This is normal during periods of low market activity. The bot is selective and only trades when it finds high-quality opportunities. Try:
- Lowering `min_profit_pct` for arbitrage (but not below 0.5%)
- Lowering `min_quality_score` for high-quality markets
- Checking that markets are active on Polymarket

### Orders Not Executing

**Issue**: Bot finds opportunities but orders fail

**Solution**: 
- Check that you have sufficient USDC balance
- For MetaMask/EOA wallets, ensure token allowances are set
- Verify your `funder_address` is correct
- Check Polygon network status

### Setting Token Allowances (MetaMask/EOA Users)

If you're using MetaMask or a hardware wallet, you need to approve token allowances before trading:

```python
from py_clob_client.client import ClobClient

client = ClobClient(
    "https://clob.polymarket.com",
    key="your-private-key",
    chain_id=137,
    signature_type=0  # EOA signature type
)

# Set allowances
client.set_api_creds(client.create_or_derive_api_creds())
client.approve_usdc()  # Approve USDC spending
client.approve_ctf()   # Approve conditional token spending
```

## Advanced Configuration

### Adding External Probability Sources

For value betting, you can add external probability sources:

```yaml
strategies:
  value_betting:
    enabled: true
    external_sources:
      market_id_1: 0.65  # Your estimated probability
      market_id_2: 0.42
```

### Customizing Position Sizing

You can modify the `calculate_position_size` method in `strategy_manager.py` to implement your own position sizing logic.

### Adding New Strategies

The modular architecture makes it easy to add new strategies. Create a new method in `strategy_manager.py` and add corresponding configuration in `config.yaml`.

## Support and Community

For questions, issues, or feature requests, please:

1. Check the logs in `logs/bot.log` for error messages
2. Review this guide and the README
3. Check the Polymarket documentation at https://docs.polymarket.com

## Disclaimer

This bot is provided for educational purposes only. Trading on prediction markets involves significant risk. You are solely responsible for any financial losses. The developers are not liable for any damages arising from the use of this software. Always trade responsibly and never risk more than you can afford to lose.
