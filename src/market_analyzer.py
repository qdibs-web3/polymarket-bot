"""
Market Analysis and Probability Assessment Engine
Analyzes markets for trading opportunities
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import time


class MarketAnalyzer:
    """Analyzes Polymarket markets to identify trading opportunities"""
    
    def __init__(self, client):
        """
        Initialize market analyzer
        
        Args:
            client: PolymarketClient instance
        """
        self.client = client
        self.logger = logging.getLogger(__name__)
        self.market_cache = {}
        self.cache_expiry = 60  # Cache for 60 seconds
    
    def find_arbitrage_opportunities(self, min_profit_pct: float = 1.0) -> List[Dict]:
        """
        Find intra-market arbitrage opportunities (YES + NO < $1.00)
        
        Args:
            min_profit_pct: Minimum profit percentage to consider
            
        Returns:
            List of arbitrage opportunities
        """
        opportunities = []
        
        try:
            markets = self.client.get_all_markets(limit=500)
            
            for market in markets:
                if not market.get('active', False):
                    continue
                
                tokens = market.get('tokens', [])
                if len(tokens) != 2:  # Binary markets only
                    continue
                
                yes_token = tokens[0].get('token_id')
                no_token = tokens[1].get('token_id')
                
                # Get best ask prices (what we'd pay to buy)
                yes_price = self.client.get_best_price(yes_token, 'BUY')
                no_price = self.client.get_best_price(no_token, 'BUY')
                
                if yes_price and no_price:
                    combined_cost = yes_price + no_price
                    
                    # Arbitrage exists if combined cost < 1.00
                    if combined_cost < 1.0:
                        profit = 1.0 - combined_cost
                        profit_pct = (profit / combined_cost) * 100
                        
                        if profit_pct >= min_profit_pct:
                            # Check liquidity
                            yes_depth = self.client.get_market_depth(yes_token)
                            no_depth = self.client.get_market_depth(no_token)
                            
                            min_liquidity = min(
                                yes_depth.get('total_ask_volume', 0),
                                no_depth.get('total_ask_volume', 0)
                            )
                            
                            opportunities.append({
                                'market_id': market.get('condition_id'),
                                'question': market.get('question'),
                                'yes_token': yes_token,
                                'no_token': no_token,
                                'yes_price': yes_price,
                                'no_price': no_price,
                                'combined_cost': combined_cost,
                                'profit': profit,
                                'profit_pct': profit_pct,
                                'max_position': min_liquidity,
                                'type': 'arbitrage'
                            })
            
            # Sort by profit percentage
            opportunities.sort(key=lambda x: x['profit_pct'], reverse=True)
            
            if opportunities:
                self.logger.info(f"Found {len(opportunities)} arbitrage opportunities")
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error finding arbitrage opportunities: {e}")
            return []
    
    def find_mispriced_markets(self, external_probabilities: Dict[str, float] = None) -> List[Dict]:
        """
        Find markets that are mispriced compared to external probability estimates
        
        Args:
            external_probabilities: Dict mapping market IDs to estimated probabilities
            
        Returns:
            List of potentially mispriced markets
        """
        opportunities = []
        
        if not external_probabilities:
            return opportunities
        
        try:
            for market_id, estimated_prob in external_probabilities.items():
                market = self.client.get_market_by_id(market_id)
                
                if not market or not market.get('active', False):
                    continue
                
                tokens = market.get('tokens', [])
                if len(tokens) < 1:
                    continue
                
                yes_token = tokens[0].get('token_id')
                market_price = self.client.get_midpoint_price(yes_token)
                
                if market_price:
                    # Calculate edge (difference between estimated and market probability)
                    edge = estimated_prob - market_price
                    edge_pct = (edge / market_price) * 100 if market_price > 0 else 0
                    
                    # Significant mispricing if edge > 5%
                    if abs(edge_pct) >= 5:
                        depth = self.client.get_market_depth(yes_token)
                        
                        opportunities.append({
                            'market_id': market_id,
                            'question': market.get('question'),
                            'token_id': yes_token,
                            'market_price': market_price,
                            'estimated_prob': estimated_prob,
                            'edge': edge,
                            'edge_pct': edge_pct,
                            'recommended_side': 'BUY' if edge > 0 else 'SELL',
                            'liquidity': depth.get('total_bid_volume' if edge < 0 else 'total_ask_volume', 0),
                            'type': 'mispriced'
                        })
            
            opportunities.sort(key=lambda x: abs(x['edge_pct']), reverse=True)
            
            if opportunities:
                self.logger.info(f"Found {len(opportunities)} potentially mispriced markets")
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error finding mispriced markets: {e}")
            return []
    
    def find_momentum_opportunities(self, price_change_threshold: float = 5.0) -> List[Dict]:
        """
        Find markets with strong price momentum
        
        Args:
            price_change_threshold: Minimum price change percentage to consider
            
        Returns:
            List of momentum opportunities
        """
        # Note: This requires historical price data which would need to be tracked
        # For now, this is a placeholder that could be enhanced with price tracking
        
        opportunities = []
        
        try:
            markets = self.client.get_all_markets(limit=200)
            
            for market in markets:
                if not market.get('active', False):
                    continue
                
                # Check if market has recent volume
                volume = market.get('volume', 0)
                if volume < 1000:  # Skip low-volume markets
                    continue
                
                tokens = market.get('tokens', [])
                if len(tokens) < 1:
                    continue
                
                yes_token = tokens[0].get('token_id')
                current_price = self.client.get_midpoint_price(yes_token)
                
                if current_price:
                    # Momentum indicators (would need historical data for full implementation)
                    # For now, identify markets with extreme prices that might reverse
                    
                    if current_price < 0.20:  # Oversold
                        opportunities.append({
                            'market_id': market.get('condition_id'),
                            'question': market.get('question'),
                            'token_id': yes_token,
                            'current_price': current_price,
                            'signal': 'OVERSOLD',
                            'recommended_side': 'BUY',
                            'volume': volume,
                            'type': 'momentum'
                        })
                    elif current_price > 0.80:  # Overbought
                        opportunities.append({
                            'market_id': market.get('condition_id'),
                            'question': market.get('question'),
                            'token_id': yes_token,
                            'current_price': current_price,
                            'signal': 'OVERBOUGHT',
                            'recommended_side': 'SELL',
                            'volume': volume,
                            'type': 'momentum'
                        })
            
            if opportunities:
                self.logger.info(f"Found {len(opportunities)} momentum opportunities")
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error finding momentum opportunities: {e}")
            return []
    
    def find_high_liquidity_markets(self, min_volume: float = 10000) -> List[Dict]:
        """
        Find markets with high liquidity for safer trading
        
        Args:
            min_volume: Minimum total volume
            
        Returns:
            List of high-liquidity markets
        """
        liquid_markets = []
        
        try:
            markets = self.client.get_all_markets(limit=500)
            
            for market in markets:
                if not market.get('active', False):
                    continue
                
                volume = market.get('volume', 0)
                
                if volume >= min_volume:
                    tokens = market.get('tokens', [])
                    if len(tokens) < 1:
                        continue
                    
                    yes_token = tokens[0].get('token_id')
                    depth = self.client.get_market_depth(yes_token)
                    current_price = self.client.get_midpoint_price(yes_token)
                    
                    liquid_markets.append({
                        'market_id': market.get('condition_id'),
                        'question': market.get('question'),
                        'token_id': yes_token,
                        'volume': volume,
                        'current_price': current_price,
                        'spread': depth.get('spread', 0),
                        'bid_volume': depth.get('total_bid_volume', 0),
                        'ask_volume': depth.get('total_ask_volume', 0),
                        'end_date': market.get('end_date_iso')
                    })
            
            # Sort by volume
            liquid_markets.sort(key=lambda x: x['volume'], reverse=True)
            
            return liquid_markets
            
        except Exception as e:
            self.logger.error(f"Error finding high-liquidity markets: {e}")
            return []
    
    def analyze_market_quality(self, market_id: str) -> Dict:
        """
        Comprehensive quality analysis of a specific market
        
        Args:
            market_id: Market condition ID
            
        Returns:
            Dictionary with quality metrics
        """
        try:
            market = self.client.get_market_by_id(market_id)
            
            if not market:
                return {'quality_score': 0, 'tradeable': False, 'reason': 'Market not found'}
            
            tokens = market.get('tokens', [])
            if len(tokens) < 1:
                return {'quality_score': 0, 'tradeable': False, 'reason': 'No tokens'}
            
            yes_token = tokens[0].get('token_id')
            
            # Gather metrics
            volume = market.get('volume', 0)
            depth = self.client.get_market_depth(yes_token)
            current_price = self.client.get_midpoint_price(yes_token)
            
            spread = depth.get('spread', 0)
            liquidity = min(depth.get('total_bid_volume', 0), depth.get('total_ask_volume', 0))
            
            # Calculate quality score (0-100)
            quality_score = 0
            
            # Volume score (0-30 points)
            if volume > 100000:
                quality_score += 30
            elif volume > 50000:
                quality_score += 25
            elif volume > 10000:
                quality_score += 20
            elif volume > 1000:
                quality_score += 10
            
            # Spread score (0-30 points)
            if spread < 0.01:
                quality_score += 30
            elif spread < 0.02:
                quality_score += 25
            elif spread < 0.05:
                quality_score += 15
            elif spread < 0.10:
                quality_score += 5
            
            # Liquidity score (0-40 points)
            if liquidity > 10000:
                quality_score += 40
            elif liquidity > 5000:
                quality_score += 30
            elif liquidity > 1000:
                quality_score += 20
            elif liquidity > 100:
                quality_score += 10
            
            # Determine if tradeable
            tradeable = quality_score >= 40 and market.get('active', False)
            
            return {
                'market_id': market_id,
                'question': market.get('question'),
                'quality_score': quality_score,
                'tradeable': tradeable,
                'volume': volume,
                'spread': spread,
                'liquidity': liquidity,
                'current_price': current_price,
                'active': market.get('active', False)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing market quality: {e}")
            return {'quality_score': 0, 'tradeable': False, 'reason': str(e)}
    
    def calculate_kelly_bet_size(self, probability: float, market_price: float, bankroll: float, 
                                 kelly_fraction: float = 0.25) -> float:
        """
        Calculate optimal bet size using Kelly Criterion
        
        Args:
            probability: Your estimated probability of YES outcome
            market_price: Current market price
            bankroll: Total available capital
            kelly_fraction: Fraction of Kelly to use (0.25 = quarter Kelly for safety)
            
        Returns:
            Recommended bet size in dollars
        """
        if market_price <= 0 or market_price >= 1:
            return 0
        
        # Kelly formula for binary outcomes
        # f = (p * (1 - market_price) - (1 - p) * market_price) / (1 - market_price)
        # where p is your estimated probability
        
        edge = probability - market_price
        
        if edge <= 0:
            return 0  # No edge, don't bet
        
        # Simplified Kelly for prediction markets
        kelly_pct = edge / (1 - market_price) if market_price < 1 else 0
        
        # Apply Kelly fraction for safety
        kelly_pct = kelly_pct * kelly_fraction
        
        # Calculate bet size
        bet_size = bankroll * kelly_pct
        
        # Cap at reasonable limits
        max_bet = bankroll * 0.10  # Never bet more than 10% on single market
        bet_size = min(bet_size, max_bet)
        
        return max(0, bet_size)
    
    def get_best_opportunities(self, bankroll: float, max_opportunities: int = 10) -> List[Dict]:
        """
        Get the best trading opportunities across all strategies
        
        Args:
            bankroll: Available capital
            max_opportunities: Maximum number of opportunities to return
            
        Returns:
            List of best opportunities sorted by expected value
        """
        all_opportunities = []
        
        # Find arbitrage opportunities (highest priority)
        arb_opps = self.find_arbitrage_opportunities(min_profit_pct=0.5)
        for opp in arb_opps:
            opp['priority'] = 1
            opp['expected_value'] = opp['profit_pct']
            all_opportunities.append(opp)
        
        # Find high-liquidity markets for safer trading
        liquid_markets = self.find_high_liquidity_markets(min_volume=5000)
        for market in liquid_markets[:20]:  # Top 20 liquid markets
            quality = self.analyze_market_quality(market['market_id'])
            if quality.get('tradeable', False) and quality.get('quality_score', 0) >= 60:
                market['priority'] = 2
                market['expected_value'] = quality['quality_score'] / 10
                market['type'] = 'high_quality'
                all_opportunities.append(market)
        
        # Sort by priority and expected value
        all_opportunities.sort(key=lambda x: (x.get('priority', 99), -x.get('expected_value', 0)))
        
        return all_opportunities[:max_opportunities]
