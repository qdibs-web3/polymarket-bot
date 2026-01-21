"""
Performance Tracking and Reporting
Tracks bot performance and generates reports
"""

import logging
import json
from typing import Dict, List
from datetime import datetime, timedelta
import os


class PerformanceTracker:
    """Tracks and analyzes bot performance"""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize performance tracker
        
        Args:
            data_dir: Directory to store performance data
        """
        self.logger = logging.getLogger(__name__)
        self.data_dir = data_dir
        self.trades_file = os.path.join(data_dir, "trades.json")
        self.daily_stats_file = os.path.join(data_dir, "daily_stats.json")
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Load existing data
        self.trades = self._load_trades()
        self.daily_stats = self._load_daily_stats()
    
    def _load_trades(self) -> List[Dict]:
        """Load trade history from file"""
        if os.path.exists(self.trades_file):
            try:
                with open(self.trades_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading trades: {e}")
        return []
    
    def _save_trades(self):
        """Save trade history to file"""
        try:
            with open(self.trades_file, 'w') as f:
                json.dump(self.trades, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving trades: {e}")
    
    def _load_daily_stats(self) -> Dict:
        """Load daily statistics from file"""
        if os.path.exists(self.daily_stats_file):
            try:
                with open(self.daily_stats_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading daily stats: {e}")
        return {}
    
    def _save_daily_stats(self):
        """Save daily statistics to file"""
        try:
            with open(self.daily_stats_file, 'w') as f:
                json.dump(self.daily_stats, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving daily stats: {e}")
    
    def record_trade(self, trade: Dict):
        """
        Record a completed trade
        
        Args:
            trade: Trade dictionary with details
        """
        trade['timestamp'] = datetime.now().isoformat()
        self.trades.append(trade)
        self._save_trades()
        
        self.logger.info(f"Trade recorded: {trade.get('type', 'unknown')} - P&L: ${trade.get('pnl', 0):.2f}")
    
    def record_daily_stats(self, stats: Dict):
        """
        Record end-of-day statistics
        
        Args:
            stats: Daily statistics dictionary
        """
        date_str = datetime.now().strftime('%Y-%m-%d')
        stats['date'] = date_str
        self.daily_stats[date_str] = stats
        self._save_daily_stats()
        
        self.logger.info(f"Daily stats recorded for {date_str}")
    
    def get_performance_summary(self, days: int = 30) -> Dict:
        """
        Get performance summary for specified period
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Performance summary dictionary
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter recent trades
        recent_trades = [
            t for t in self.trades
            if datetime.fromisoformat(t['timestamp']) >= cutoff_date
        ]
        
        if not recent_trades:
            return {
                'total_trades': 0,
                'total_pnl': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0
            }
        
        # Calculate metrics
        total_trades = len(recent_trades)
        winning_trades = [t for t in recent_trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in recent_trades if t.get('pnl', 0) < 0]
        
        total_pnl = sum(t.get('pnl', 0) for t in recent_trades)
        total_wins = sum(t.get('pnl', 0) for t in winning_trades)
        total_losses = abs(sum(t.get('pnl', 0) for t in losing_trades))
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        avg_win = total_wins / len(winning_trades) if winning_trades else 0
        avg_loss = total_losses / len(losing_trades) if losing_trades else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Calculate by strategy type
        strategy_stats = {}
        for trade in recent_trades:
            strategy = trade.get('type', 'unknown')
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {'count': 0, 'pnl': 0}
            strategy_stats[strategy]['count'] += 1
            strategy_stats[strategy]['pnl'] += trade.get('pnl', 0)
        
        return {
            'period_days': days,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_wins': total_wins,
            'total_losses': total_losses,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'best_trade': max((t.get('pnl', 0) for t in recent_trades), default=0),
            'worst_trade': min((t.get('pnl', 0) for t in recent_trades), default=0),
            'strategy_breakdown': strategy_stats
        }
    
    def get_daily_returns(self, days: int = 30) -> List[Dict]:
        """
        Get daily returns for specified period
        
        Args:
            days: Number of days
            
        Returns:
            List of daily return dictionaries
        """
        daily_returns = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            if date_str in self.daily_stats:
                stats = self.daily_stats[date_str]
                daily_returns.append({
                    'date': date_str,
                    'pnl': stats.get('daily_pnl', 0),
                    'return_pct': stats.get('daily_return_pct', 0),
                    'trades': stats.get('daily_trades', 0)
                })
        
        return sorted(daily_returns, key=lambda x: x['date'])
    
    def generate_report(self, days: int = 30) -> str:
        """
        Generate performance report
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Formatted report string
        """
        summary = self.get_performance_summary(days)
        daily_returns = self.get_daily_returns(days)
        
        report = []
        report.append("=" * 60)
        report.append("POLYMARKET BOT PERFORMANCE REPORT")
        report.append("=" * 60)
        report.append(f"\nPeriod: Last {days} days")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("\n" + "-" * 60)
        report.append("OVERALL PERFORMANCE")
        report.append("-" * 60)
        report.append(f"Total Trades:        {summary['total_trades']}")
        report.append(f"Winning Trades:      {summary['winning_trades']}")
        report.append(f"Losing Trades:       {summary['losing_trades']}")
        report.append(f"Win Rate:            {summary['win_rate']:.2%}")
        report.append(f"\nTotal P&L:           ${summary['total_pnl']:.2f}")
        report.append(f"Total Wins:          ${summary['total_wins']:.2f}")
        report.append(f"Total Losses:        ${summary['total_losses']:.2f}")
        report.append(f"\nAverage Win:         ${summary['avg_win']:.2f}")
        report.append(f"Average Loss:        ${summary['avg_loss']:.2f}")
        report.append(f"Profit Factor:       {summary['profit_factor']:.2f}")
        report.append(f"\nBest Trade:          ${summary['best_trade']:.2f}")
        report.append(f"Worst Trade:         ${summary['worst_trade']:.2f}")
        
        # Strategy breakdown
        if summary['strategy_breakdown']:
            report.append("\n" + "-" * 60)
            report.append("STRATEGY BREAKDOWN")
            report.append("-" * 60)
            for strategy, stats in summary['strategy_breakdown'].items():
                report.append(f"\n{strategy.upper()}:")
                report.append(f"  Trades: {stats['count']}")
                report.append(f"  P&L:    ${stats['pnl']:.2f}")
                report.append(f"  Avg:    ${stats['pnl'] / stats['count']:.2f}")
        
        # Recent daily performance
        if daily_returns:
            report.append("\n" + "-" * 60)
            report.append("RECENT DAILY PERFORMANCE (Last 7 Days)")
            report.append("-" * 60)
            for day in daily_returns[-7:]:
                report.append(f"{day['date']}: ${day['pnl']:>8.2f} ({day['return_pct']:>6.2f}%) - {day['trades']} trades")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    def save_report(self, filename: str = None, days: int = 30):
        """
        Save performance report to file
        
        Args:
            filename: Output filename (default: performance_report_YYYYMMDD.txt)
            days: Number of days to analyze
        """
        if filename is None:
            filename = f"performance_report_{datetime.now().strftime('%Y%m%d')}.txt"
        
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            report = self.generate_report(days)
            with open(filepath, 'w') as f:
                f.write(report)
            
            self.logger.info(f"Performance report saved to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving report: {e}")
            return None
    
    def get_roi(self, initial_balance: float) -> float:
        """
        Calculate return on investment
        
        Args:
            initial_balance: Starting balance
            
        Returns:
            ROI as decimal (e.g., 0.25 = 25%)
        """
        total_pnl = sum(t.get('pnl', 0) for t in self.trades)
        return total_pnl / initial_balance if initial_balance > 0 else 0
    
    def get_sharpe_ratio(self, risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sharpe ratio from daily returns
        
        Args:
            risk_free_rate: Annual risk-free rate (default 0)
            
        Returns:
            Sharpe ratio
        """
        daily_returns = self.get_daily_returns(365)
        
        if len(daily_returns) < 2:
            return 0
        
        returns = [d['return_pct'] / 100 for d in daily_returns]
        
        # Calculate mean and std dev
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return 0
        
        # Annualize
        daily_risk_free = risk_free_rate / 365
        sharpe = (mean_return - daily_risk_free) / std_dev * (365 ** 0.5)
        
        return sharpe
    
    def get_max_drawdown(self) -> float:
        """
        Calculate maximum drawdown
        
        Returns:
            Max drawdown as decimal (e.g., 0.15 = 15%)
        """
        daily_returns = self.get_daily_returns(365)
        
        if not daily_returns:
            return 0
        
        # Calculate cumulative returns
        cumulative = 0
        peak = 0
        max_dd = 0
        
        for day in daily_returns:
            cumulative += day['pnl']
            if cumulative > peak:
                peak = cumulative
            
            drawdown = (peak - cumulative) / peak if peak > 0 else 0
            max_dd = max(max_dd, drawdown)
        
        return max_dd
