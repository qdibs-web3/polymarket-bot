"""
Strategy Manager and Risk Management
Implements betting strategies with comprehensive risk controls
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import time


class StrategyManager:
    """Manages betting strategies and risk controls"""
    
    def __init__(self, config: Dict):
        """
        Initialize strategy manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Risk parameters
        self.max_position_size = config.get('max_position_size', 100)  # Max $ per position
        self.max_daily_loss = config.get('max_daily_loss', 50)  # Max daily loss
        self.max_open_positions = config.get('max_open_positions', 5)
        self.min_edge = config.get('min_edge', 0.05)  # Minimum 5% edge
        self.kelly_fraction = config.get('kelly_fraction', 0.25)  # Quarter Kelly
        self.target_daily_return = config.get('target_daily_return', 0.02)  # 2% daily target
        
        # State tracking
        self.open_positions = {}
        self.daily_pnl = 0
        self.daily_trades = 0
        self.start_of_day_balance = 0
        self.last_reset_date = datetime.now().date()
        
    def reset_daily_stats(self, current_balance: float):
        """Reset daily statistics"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_pnl = 0
            self.daily_trades = 0
            self.start_of_day_balance = current_balance
            self.last_reset_date = today
            self.logger.info("Daily stats reset")
    
    def can_trade(self) -> tuple[bool, str]:
        """
        Check if bot can place new trades
        
        Returns:
            Tuple of (can_trade, reason)
        """
        # Check daily loss limit
        if self.daily_pnl <= -self.max_daily_loss:
            return False, f"Daily loss limit reached: ${self.daily_pnl:.2f}"
        
        # Check max open positions
        if len(self.open_positions) >= self.max_open_positions:
            return False, f"Max open positions reached: {len(self.open_positions)}"
        
        # Check if daily target reached (optional stop)
        if self.start_of_day_balance > 0:
            daily_return = self.daily_pnl / self.start_of_day_balance
            if daily_return >= self.target_daily_return:
                return False, f"Daily target reached: {daily_return:.2%}"
        
        return True, "OK"
    
    def calculate_position_size(self, opportunity: Dict, bankroll: float) -> float:
        """
        Calculate position size based on opportunity type and risk parameters
        
        Args:
            opportunity: Opportunity dictionary
            bankroll: Available capital
            
        Returns:
            Position size in dollars
        """
        opp_type = opportunity.get('type', 'unknown')
        
        if opp_type == 'arbitrage':
            # Arbitrage: Use larger position sizes (guaranteed profit)
            profit_pct = opportunity.get('profit_pct', 0)
            max_position = opportunity.get('max_position', 0)
            
            # Size based on profit and liquidity
            if profit_pct >= 2.0:
                size = min(self.max_position_size, max_position * 100, bankroll * 0.15)
            elif profit_pct >= 1.0:
                size = min(self.max_position_size * 0.7, max_position * 100, bankroll * 0.10)
            else:
                size = min(self.max_position_size * 0.5, max_position * 100, bankroll * 0.05)
            
            return size
        
        elif opp_type == 'mispriced':
            # Value betting: Use Kelly Criterion
            edge_pct = abs(opportunity.get('edge_pct', 0)) / 100
            
            if edge_pct < self.min_edge:
                return 0
            
            # Kelly sizing
            kelly_size = bankroll * edge_pct * self.kelly_fraction
            
            # Apply limits
            size = min(kelly_size, self.max_position_size, bankroll * 0.10)
            
            return size
        
        elif opp_type == 'high_quality':
            # High-quality markets: Conservative sizing
            quality_score = opportunity.get('quality_score', 0)
            
            if quality_score >= 80:
                size = min(self.max_position_size * 0.6, bankroll * 0.08)
            elif quality_score >= 60:
                size = min(self.max_position_size * 0.4, bankroll * 0.05)
            else:
                size = min(self.max_position_size * 0.2, bankroll * 0.03)
            
            return size
        
        else:
            # Default: Very conservative
            return min(self.max_position_size * 0.3, bankroll * 0.03)
    
    def execute_arbitrage_strategy(self, opportunity: Dict, client, bankroll: float) -> Optional[Dict]:
        """
        Execute arbitrage strategy (buy YES and NO when combined < $1)
        
        Args:
            opportunity: Arbitrage opportunity
            client: PolymarketClient instance
            bankroll: Available capital
            
        Returns:
            Execution result or None
        """
        try:
            position_size = self.calculate_position_size(opportunity, bankroll)
            
            if position_size < 10:  # Minimum $10 position
                self.logger.info("Position size too small for arbitrage")
                return None
            
            yes_token = opportunity['yes_token']
            no_token = opportunity['no_token']
            yes_price = opportunity['yes_price']
            no_price = opportunity['no_price']
            
            # Calculate shares to buy
            combined_cost = yes_price + no_price
            shares = position_size / combined_cost
            
            # Place market orders for both sides
            yes_order = client.place_market_order(yes_token, shares * yes_price, 'BUY')
            no_order = client.place_market_order(no_token, shares * no_price, 'BUY')
            
            if yes_order and no_order:
                position_id = f"arb_{yes_token}_{no_token}_{int(time.time())}"
                
                self.open_positions[position_id] = {
                    'type': 'arbitrage',
                    'yes_token': yes_token,
                    'no_token': no_token,
                    'shares': shares,
                    'cost': position_size,
                    'expected_profit': opportunity['profit'] * shares,
                    'entry_time': datetime.now(),
                    'market_id': opportunity['market_id']
                }
                
                self.daily_trades += 1
                
                self.logger.info(f"Arbitrage executed: {shares:.2f} shares for ${position_size:.2f}")
                
                return {
                    'success': True,
                    'position_id': position_id,
                    'size': position_size,
                    'expected_profit': opportunity['profit'] * shares
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error executing arbitrage: {e}")
            return None
    
    def execute_value_bet(self, opportunity: Dict, client, bankroll: float) -> Optional[Dict]:
        """
        Execute value bet on mispriced market
        
        Args:
            opportunity: Mispriced market opportunity
            client: PolymarketClient instance
            bankroll: Available capital
            
        Returns:
            Execution result or None
        """
        try:
            position_size = self.calculate_position_size(opportunity, bankroll)
            
            if position_size < 10:
                self.logger.info("Position size too small for value bet")
                return None
            
            token_id = opportunity['token_id']
            side = opportunity['recommended_side']
            market_price = opportunity['market_price']
            
            # Place market order
            order = client.place_market_order(token_id, position_size, side)
            
            if order:
                position_id = f"value_{token_id}_{int(time.time())}"
                
                self.open_positions[position_id] = {
                    'type': 'value_bet',
                    'token_id': token_id,
                    'side': side,
                    'size': position_size,
                    'entry_price': market_price,
                    'estimated_prob': opportunity['estimated_prob'],
                    'edge': opportunity['edge'],
                    'entry_time': datetime.now(),
                    'market_id': opportunity['market_id']
                }
                
                self.daily_trades += 1
                
                self.logger.info(f"Value bet executed: {side} ${position_size:.2f} on {token_id}")
                
                return {
                    'success': True,
                    'position_id': position_id,
                    'size': position_size,
                    'edge': opportunity['edge']
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error executing value bet: {e}")
            return None
    
    def execute_limit_order_strategy(self, opportunity: Dict, client, bankroll: float) -> Optional[Dict]:
        """
        Place limit orders for better prices
        
        Args:
            opportunity: Market opportunity
            client: PolymarketClient instance
            bankroll: Available capital
            
        Returns:
            Execution result or None
        """
        try:
            position_size = self.calculate_position_size(opportunity, bankroll)
            
            if position_size < 10:
                return None
            
            token_id = opportunity['token_id']
            current_price = opportunity.get('current_price', 0.5)
            
            # Place limit order slightly better than current price
            if current_price < 0.5:
                # Buying: Place bid below current ask
                limit_price = current_price * 0.98  # 2% better
                side = 'BUY'
            else:
                # Selling: Place ask above current bid
                limit_price = current_price * 1.02  # 2% better
                side = 'SELL'
            
            # Calculate shares
            shares = position_size / limit_price if limit_price > 0 else 0
            
            if shares < 1:
                return None
            
            # Place limit order
            order = client.place_limit_order(token_id, limit_price, shares, side)
            
            if order:
                position_id = f"limit_{token_id}_{int(time.time())}"
                
                self.open_positions[position_id] = {
                    'type': 'limit_order',
                    'token_id': token_id,
                    'side': side,
                    'size': position_size,
                    'limit_price': limit_price,
                    'shares': shares,
                    'order_id': order.get('id'),
                    'entry_time': datetime.now(),
                    'market_id': opportunity.get('market_id')
                }
                
                self.logger.info(f"Limit order placed: {side} {shares:.2f} @ ${limit_price:.3f}")
                
                return {
                    'success': True,
                    'position_id': position_id,
                    'order_id': order.get('id')
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error placing limit order: {e}")
            return None
    
    def manage_positions(self, client) -> List[Dict]:
        """
        Monitor and manage open positions
        
        Args:
            client: PolymarketClient instance
            
        Returns:
            List of actions taken
        """
        actions = []
        
        try:
            for position_id, position in list(self.open_positions.items()):
                position_type = position.get('type')
                
                if position_type == 'arbitrage':
                    # Arbitrage positions resolve automatically
                    # Check if market has resolved
                    # (Would need to implement market resolution checking)
                    pass
                
                elif position_type == 'value_bet':
                    # Check for profit-taking or stop-loss
                    token_id = position['token_id']
                    entry_price = position['entry_price']
                    current_price = client.get_midpoint_price(token_id)
                    
                    if current_price:
                        pnl_pct = (current_price - entry_price) / entry_price
                        
                        # Take profit at 50% gain
                        if pnl_pct >= 0.50:
                            self.logger.info(f"Taking profit on {position_id}: {pnl_pct:.2%}")
                            # Would execute close order here
                            actions.append({'action': 'close', 'position_id': position_id, 'reason': 'profit_target'})
                        
                        # Stop loss at 20% loss
                        elif pnl_pct <= -0.20:
                            self.logger.info(f"Stop loss on {position_id}: {pnl_pct:.2%}")
                            actions.append({'action': 'close', 'position_id': position_id, 'reason': 'stop_loss'})
                
                elif position_type == 'limit_order':
                    # Check if limit order filled
                    order_id = position.get('order_id')
                    if order_id:
                        # Would check order status here
                        pass
            
            return actions
            
        except Exception as e:
            self.logger.error(f"Error managing positions: {e}")
            return []
    
    def close_position(self, position_id: str, client) -> bool:
        """
        Close a specific position
        
        Args:
            position_id: Position ID to close
            client: PolymarketClient instance
            
        Returns:
            True if successful
        """
        if position_id not in self.open_positions:
            return False
        
        try:
            position = self.open_positions[position_id]
            position_type = position.get('type')
            
            if position_type == 'value_bet':
                token_id = position['token_id']
                size = position['size']
                side = 'SELL' if position['side'] == 'BUY' else 'BUY'
                
                # Close position with market order
                order = client.place_market_order(token_id, size, side)
                
                if order:
                    # Calculate P&L
                    entry_price = position['entry_price']
                    exit_price = client.get_midpoint_price(token_id)
                    
                    if exit_price:
                        pnl = (exit_price - entry_price) * size if position['side'] == 'BUY' else (entry_price - exit_price) * size
                        self.daily_pnl += pnl
                        
                        self.logger.info(f"Position closed: {position_id}, P&L: ${pnl:.2f}")
                    
                    del self.open_positions[position_id]
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return False
    
    def get_portfolio_summary(self, client, current_balance: float) -> Dict:
        """
        Get summary of portfolio and performance
        
        Args:
            client: PolymarketClient instance
            current_balance: Current account balance
            
        Returns:
            Portfolio summary dictionary
        """
        total_exposure = sum(pos.get('size', 0) for pos in self.open_positions.values())
        
        daily_return_pct = (self.daily_pnl / self.start_of_day_balance * 100) if self.start_of_day_balance > 0 else 0
        
        return {
            'current_balance': current_balance,
            'open_positions': len(self.open_positions),
            'total_exposure': total_exposure,
            'daily_pnl': self.daily_pnl,
            'daily_return_pct': daily_return_pct,
            'daily_trades': self.daily_trades,
            'max_daily_loss': self.max_daily_loss,
            'remaining_loss_buffer': self.max_daily_loss + self.daily_pnl,
            'target_reached': daily_return_pct >= (self.target_daily_return * 100)
        }
