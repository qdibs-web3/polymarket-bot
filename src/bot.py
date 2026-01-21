
"""
Polymarket Trading Bot
Main entry point for the automated trading bot
"""

import logging
import time
import yaml
from dotenv import load_dotenv
import os
from datetime import datetime

from polymarket_client import PolymarketClient
from market_analyzer import MarketAnalyzer
from strategy_manager import StrategyManager
from performance_tracker import PerformanceTracker

def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load YAML configuration file"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Load environment variables for private key
    load_dotenv()
    private_key = os.getenv("POLYMARKET_PRIVATE_KEY")
    funder_address = os.getenv("POLYMARKET_FUNDER_ADDRESS")
    
    if private_key:
        config["private_key"] = private_key
    if funder_address:
        config["funder_address"] = funder_address
        
    return config

def setup_logging(log_level: str = "INFO"):
    """Set up logging configuration"""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/bot.log")
        ]
    )


def main():
    """Main trading bot loop"""
    # Load configuration
    config = load_config()
    
    # Setup logging
    setup_logging(config.get("log_level", "INFO"))
    logger = logging.getLogger(__name__)
    logger.info("Starting Polymarket Trading Bot")
    
    # Initialize components
    client = PolymarketClient(config)
    analyzer = MarketAnalyzer(client)
    strategy_manager = StrategyManager(config.get("risk_management", config))
    performance_tracker = PerformanceTracker(config.get("data_dir", "data"))
    
    # Initial balance (replace with actual balance fetching)
    current_balance = 1000.0
    strategy_manager.reset_daily_stats(current_balance)
    
    run_interval = config.get("run_interval_seconds", 60)
    
    while True:
        try:
            logger.info("Starting new trading cycle...")
            
            # Reset daily stats if new day
            strategy_manager.reset_daily_stats(current_balance)
            
            # Check if bot can trade
            can_trade, reason = strategy_manager.can_trade()
            if not can_trade:
                logger.warning(f"Trading paused: {reason}")
                time.sleep(run_interval)
                continue
            
            # Get best opportunities
            opportunities = analyzer.get_best_opportunities(bankroll=current_balance)
            
            if not opportunities:
                logger.info("No attractive opportunities found in this cycle.")
            else:
                logger.info(f"Found {len(opportunities)} potential opportunities.")
                
                # Execute trades based on opportunities
                for opp in opportunities:
                    can_trade, reason = strategy_manager.can_trade()
                    if not can_trade:
                        logger.warning(f"Stopping trades for this cycle: {reason}")
                        break
                    
                    opp_type = opp.get("type")
                    
                    if opp_type == "arbitrage" and config["strategies"]["arbitrage"]["enabled"]:
                        strategy_manager.execute_arbitrage_strategy(opp, client, current_balance)
                    
                    elif opp_type == "high_quality" and config["strategies"]["high_quality_markets"]["enabled"]:
                        # For high-quality markets, we can place limit orders
                        strategy_manager.execute_limit_order_strategy(opp, client, current_balance)
            
            # Manage open positions (profit-taking, stop-loss)
            strategy_manager.manage_positions(client)
            
            # Log portfolio summary
            summary = strategy_manager.get_portfolio_summary(client, current_balance)
            logger.info(f"Portfolio Summary: {summary}")
            
            # Record daily stats at end of day (or periodically)
            # This logic can be enhanced to be more precise
            if datetime.now().hour == 23 and datetime.now().minute >= 55:
                performance_tracker.record_daily_stats(summary)
                performance_tracker.save_report()

            logger.info(f"Trading cycle finished. Waiting for {run_interval} seconds.")
            time.sleep(run_interval)
            
        except KeyboardInterrupt:
            logger.info("Bot stopped manually.")
            break
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            time.sleep(run_interval)

if __name__ == "__main__":
    main()
