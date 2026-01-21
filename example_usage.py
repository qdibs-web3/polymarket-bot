"""
Example Usage Script
Demonstrates how to use the Polymarket bot components
"""

import os
from dotenv import load_dotenv
from src.polymarket_client import PolymarketClient
from src.market_analyzer import MarketAnalyzer
from src.strategy_manager import StrategyManager

# Load environment variables
load_dotenv()

def example_read_only_mode():
    """Example: Using the bot in read-only mode to explore markets"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Read-Only Mode - Exploring Markets")
    print("="*60 + "\n")
    
    # Initialize client without private key (read-only)
    config = {
        'host': 'https://clob.polymarket.com',
        'chain_id': 137
    }
    
    client = PolymarketClient(config)
    print("✓ Client initialized in read-only mode\n")
    
    # Fetch popular markets
    print("Fetching top 10 markets...")
    markets = client.get_all_markets(limit=10)
    
    print(f"\nFound {len(markets)} markets:\n")
    for i, market in enumerate(markets[:5], 1):
        question = market.get('question', 'N/A')
        volume = market.get('volume', 0)
        print(f"{i}. {question}")
        print(f"   Volume: ${volume:,.0f}\n")


def example_find_arbitrage():
    """Example: Finding arbitrage opportunities"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Finding Arbitrage Opportunities")
    print("="*60 + "\n")
    
    config = {
        'host': 'https://clob.polymarket.com',
        'chain_id': 137
    }
    
    client = PolymarketClient(config)
    analyzer = MarketAnalyzer(client)
    
    print("Scanning markets for arbitrage opportunities...")
    print("(This may take a minute...)\n")
    
    opportunities = analyzer.find_arbitrage_opportunities(min_profit_pct=0.5)
    
    if opportunities:
        print(f"Found {len(opportunities)} arbitrage opportunities!\n")
        
        for i, opp in enumerate(opportunities[:3], 1):
            print(f"Opportunity #{i}:")
            print(f"  Market: {opp['question'][:60]}...")
            print(f"  YES Price: ${opp['yes_price']:.4f}")
            print(f"  NO Price:  ${opp['no_price']:.4f}")
            print(f"  Combined:  ${opp['combined_cost']:.4f}")
            print(f"  Profit:    ${opp['profit']:.4f} ({opp['profit_pct']:.2f}%)")
            print(f"  Max Size:  {opp['max_position']:.0f} shares\n")
    else:
        print("No arbitrage opportunities found at this time.")
        print("This is normal - arbitrage opportunities are rare and fleeting.")


def example_analyze_market():
    """Example: Analyzing a specific market's quality"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Analyzing Market Quality")
    print("="*60 + "\n")
    
    config = {
        'host': 'https://clob.polymarket.com',
        'chain_id': 137
    }
    
    client = PolymarketClient(config)
    analyzer = MarketAnalyzer(client)
    
    # Get a high-volume market
    print("Finding a high-volume market to analyze...\n")
    markets = client.get_all_markets(limit=100)
    
    # Sort by volume and pick the top one
    markets_sorted = sorted(markets, key=lambda x: x.get('volume', 0), reverse=True)
    
    if markets_sorted:
        top_market = markets_sorted[0]
        market_id = top_market.get('condition_id')
        
        print(f"Analyzing: {top_market.get('question', 'N/A')}\n")
        
        quality = analyzer.analyze_market_quality(market_id)
        
        print("Quality Analysis:")
        print(f"  Quality Score: {quality.get('quality_score', 0)}/100")
        print(f"  Tradeable:     {'✓ Yes' if quality.get('tradeable') else '✗ No'}")
        print(f"  Volume:        ${quality.get('volume', 0):,.0f}")
        print(f"  Spread:        {quality.get('spread', 0):.4f}")
        print(f"  Liquidity:     {quality.get('liquidity', 0):,.0f} shares")
        print(f"  Current Price: ${quality.get('current_price', 0):.4f}")


def example_position_sizing():
    """Example: Calculating optimal position sizes"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Position Sizing with Kelly Criterion")
    print("="*60 + "\n")
    
    config = {
        'max_position_size': 100,
        'max_daily_loss': 50,
        'max_open_positions': 5,
        'min_edge': 0.05,
        'kelly_fraction': 0.25,
        'target_daily_return': 0.02
    }
    
    strategy_manager = StrategyManager(config)
    
    # Example arbitrage opportunity
    arb_opportunity = {
        'type': 'arbitrage',
        'profit_pct': 2.0,
        'max_position': 500,
        'question': 'Example Arbitrage Market'
    }
    
    bankroll = 1000
    position_size = strategy_manager.calculate_position_size(arb_opportunity, bankroll)
    
    print("Scenario: Arbitrage Opportunity")
    print(f"  Bankroll:      ${bankroll:.2f}")
    print(f"  Profit %:      {arb_opportunity['profit_pct']:.2f}%")
    print(f"  Max Liquidity: {arb_opportunity['max_position']:.0f} shares")
    print(f"  → Position Size: ${position_size:.2f}\n")
    
    # Example value bet
    value_opportunity = {
        'type': 'mispriced',
        'edge_pct': 8.0,
        'question': 'Example Value Bet Market'
    }
    
    position_size = strategy_manager.calculate_position_size(value_opportunity, bankroll)
    
    print("Scenario: Value Bet")
    print(f"  Bankroll:  ${bankroll:.2f}")
    print(f"  Edge:      {value_opportunity['edge_pct']:.2f}%")
    print(f"  → Position Size: ${position_size:.2f}")
    print(f"  (Using quarter-Kelly for safety)")


def example_risk_checks():
    """Example: Risk management checks"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Risk Management Checks")
    print("="*60 + "\n")
    
    config = {
        'max_position_size': 100,
        'max_daily_loss': 50,
        'max_open_positions': 5,
        'target_daily_return': 0.02
    }
    
    strategy_manager = StrategyManager(config)
    strategy_manager.start_of_day_balance = 1000
    
    # Simulate some trading activity
    print("Initial state:")
    can_trade, reason = strategy_manager.can_trade()
    print(f"  Can trade: {can_trade}")
    print(f"  Reason: {reason}\n")
    
    # Simulate reaching max positions
    print("After opening 5 positions:")
    for i in range(5):
        strategy_manager.open_positions[f"pos_{i}"] = {'size': 50}
    
    can_trade, reason = strategy_manager.can_trade()
    print(f"  Can trade: {can_trade}")
    print(f"  Reason: {reason}\n")
    
    # Simulate daily loss
    print("After hitting daily loss limit:")
    strategy_manager.open_positions.clear()
    strategy_manager.daily_pnl = -50
    
    can_trade, reason = strategy_manager.can_trade()
    print(f"  Can trade: {can_trade}")
    print(f"  Reason: {reason}\n")
    
    # Simulate reaching daily target
    print("After reaching daily profit target:")
    strategy_manager.daily_pnl = 20  # 2% of 1000
    
    can_trade, reason = strategy_manager.can_trade()
    print(f"  Can trade: {can_trade}")
    print(f"  Reason: {reason}")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("POLYMARKET BOT - EXAMPLE USAGE")
    print("="*60)
    print("\nThis script demonstrates the bot's capabilities.")
    print("No actual trades will be placed.\n")
    
    try:
        # Run examples
        example_read_only_mode()
        example_find_arbitrage()
        example_analyze_market()
        example_position_sizing()
        example_risk_checks()
        
        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("Make sure you have an internet connection and the required packages installed.")


if __name__ == "__main__":
    main()
