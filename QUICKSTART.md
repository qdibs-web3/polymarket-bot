# Polymarket Bot - Quick Start Guide

Get your bot running in 5 minutes!

## 1. Install Dependencies

```bash
cd polymarket_bot
pip install -r requirements.txt
```

## 2. Set Up Credentials

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```
POLYMARKET_PRIVATE_KEY="your-private-key"
POLYMARKET_FUNDER_ADDRESS="your-wallet-address"
```

## 3. Configure Risk Settings

Edit `config/config.yaml` to set your risk parameters:

```yaml
max_position_size: 25.0      # Start small!
max_daily_loss: 10.0         # Protect your capital
target_daily_return: 0.02    # 2% daily target
```

## 4. Test Without Trading

Run the example script to verify everything works:

```bash
python example_usage.py
```

## 5. Start Trading

When ready, start the bot:

```bash
python src/bot.py
```

## Monitor Performance

View logs in real-time:

```bash
tail -f logs/bot.log
```

Check performance reports:

```bash
cat data/performance_report_*.txt
```

## Important Safety Tips

- ✅ Start with small amounts ($100-$500)
- ✅ Monitor daily for the first week
- ✅ Use conservative risk settings initially
- ✅ Enable arbitrage strategy first (safest)
- ⚠️ Never risk more than you can afford to lose

## Need Help?

- Read the full [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions
- Check [DOCUMENTATION.md](DOCUMENTATION.md) for technical details
- Review [README.md](README.md) for an overview

## Disclaimer

Trading involves risk. This bot is for educational purposes. You are responsible for any losses.
