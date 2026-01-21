"""
Polymarket API Client
Wrapper for py-clob-client with additional functionality
"""

import logging
from typing import Dict, List, Optional
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, MarketOrderArgs, OrderType, BookParams, OpenOrderParams
from py_clob_client.order_builder.constants import BUY, SELL
import time


class PolymarketClient:
    """Enhanced Polymarket client with trading and market analysis capabilities"""
    
    def __init__(self, config: Dict):
        """
        Initialize Polymarket client
        
        Args:
            config: Configuration dictionary with API settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize CLOB client
        self.host = config.get('host', 'https://clob.polymarket.com')
        self.chain_id = config.get('chain_id', 137)
        
        # Check if trading mode (requires private key)
        self.trading_enabled = 'private_key' in config and config['private_key']
        
        if self.trading_enabled:
            self.client = ClobClient(
                self.host,
                key=config['private_key'],
                chain_id=self.chain_id,
                signature_type=config.get('signature_type', 1),
                funder=config.get('funder_address', '')
            )
            # Set API credentials
            self.client.set_api_creds(self.client.create_or_derive_api_creds())
            self.logger.info("Polymarket client initialized in TRADING mode")
        else:
            # Read-only mode
            self.client = ClobClient(self.host)
            self.logger.info("Polymarket client initialized in READ-ONLY mode")
    
    def get_all_markets(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Fetch all available markets
        
        Args:
            limit: Maximum number of markets to fetch
            offset: Offset for pagination
            
        Returns:
            List of market dictionaries
        """
        try:
            response = self.client.get_simplified_markets(limit=limit, offset=offset)
            return response.get('data', [])
        except Exception as e:
            self.logger.error(f"Error fetching markets: {e}")
            return []
    
    def get_market_by_id(self, condition_id: str) -> Optional[Dict]:
        """
        Get specific market by condition ID
        
        Args:
            condition_id: Market condition ID
            
        Returns:
            Market dictionary or None
        """
        try:
            markets = self.get_all_markets(limit=1000)
            for market in markets:
                if market.get('condition_id') == condition_id:
                    return market
            return None
        except Exception as e:
            self.logger.error(f"Error fetching market {condition_id}: {e}")
            return None
    
    def search_markets(self, keyword: str, active_only: bool = True) -> List[Dict]:
        """
        Search for markets containing keyword
        
        Args:
            keyword: Search term
            active_only: Only return active markets
            
        Returns:
            List of matching markets
        """
        try:
            markets = self.get_all_markets(limit=1000)
            keyword_lower = keyword.lower()
            
            results = []
            for market in markets:
                question = market.get('question', '').lower()
                description = market.get('description', '').lower()
                
                if keyword_lower in question or keyword_lower in description:
                    if active_only and not market.get('active', False):
                        continue
                    results.append(market)
            
            return results
        except Exception as e:
            self.logger.error(f"Error searching markets: {e}")
            return []
    
    def get_orderbook(self, token_id: str) -> Optional[Dict]:
        """
        Get orderbook for a specific token
        
        Args:
            token_id: Token ID
            
        Returns:
            Orderbook data or None
        """
        try:
            book = self.client.get_order_book(token_id)
            return {
                'bids': book.bids if hasattr(book, 'bids') else [],
                'asks': book.asks if hasattr(book, 'asks') else [],
                'market': book.market if hasattr(book, 'market') else token_id,
                'timestamp': time.time()
            }
        except Exception as e:
            self.logger.error(f"Error fetching orderbook for {token_id}: {e}")
            return None
    
    def get_midpoint_price(self, token_id: str) -> Optional[float]:
        """
        Get midpoint price for a token
        
        Args:
            token_id: Token ID
            
        Returns:
            Midpoint price or None
        """
        try:
            mid = self.client.get_midpoint(token_id)
            return float(mid) if mid else None
        except Exception as e:
            self.logger.error(f"Error fetching midpoint for {token_id}: {e}")
            return None
    
    def get_best_price(self, token_id: str, side: str) -> Optional[float]:
        """
        Get best bid or ask price
        
        Args:
            token_id: Token ID
            side: 'BUY' or 'SELL'
            
        Returns:
            Best price or None
        """
        try:
            price = self.client.get_price(token_id, side=side)
            return float(price) if price else None
        except Exception as e:
            self.logger.error(f"Error fetching {side} price for {token_id}: {e}")
            return None
    
    def get_last_trade_price(self, token_id: str) -> Optional[float]:
        """
        Get last traded price
        
        Args:
            token_id: Token ID
            
        Returns:
            Last trade price or None
        """
        try:
            price = self.client.get_last_trade_price(token_id)
            return float(price) if price else None
        except Exception as e:
            self.logger.error(f"Error fetching last trade price for {token_id}: {e}")
            return None
    
    def place_market_order(self, token_id: str, amount: float, side: str) -> Optional[Dict]:
        """
        Place a market order
        
        Args:
            token_id: Token ID
            amount: Dollar amount to trade
            side: BUY or SELL
            
        Returns:
            Order response or None
        """
        if not self.trading_enabled:
            self.logger.error("Trading not enabled - missing private key")
            return None
        
        try:
            order_side = BUY if side.upper() == 'BUY' else SELL
            
            market_order = MarketOrderArgs(
                token_id=token_id,
                amount=amount,
                side=order_side,
                order_type=OrderType.FOK  # Fill or Kill
            )
            
            signed_order = self.client.create_market_order(market_order)
            response = self.client.post_order(signed_order, OrderType.FOK)
            
            self.logger.info(f"Market order placed: {side} ${amount} on {token_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error placing market order: {e}")
            return None
    
    def place_limit_order(self, token_id: str, price: float, size: float, side: str) -> Optional[Dict]:
        """
        Place a limit order
        
        Args:
            token_id: Token ID
            price: Limit price (0.01 to 0.99)
            size: Number of shares
            side: BUY or SELL
            
        Returns:
            Order response or None
        """
        if not self.trading_enabled:
            self.logger.error("Trading not enabled - missing private key")
            return None
        
        try:
            order_side = BUY if side.upper() == 'BUY' else SELL
            
            limit_order = OrderArgs(
                token_id=token_id,
                price=price,
                size=size,
                side=order_side
            )
            
            signed_order = self.client.create_order(limit_order)
            response = self.client.post_order(signed_order, OrderType.GTC)  # Good Till Cancel
            
            self.logger.info(f"Limit order placed: {side} {size} shares @ ${price} on {token_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error placing limit order: {e}")
            return None
    
    def get_open_orders(self) -> List[Dict]:
        """
        Get all open orders
        
        Returns:
            List of open orders
        """
        if not self.trading_enabled:
            return []
        
        try:
            orders = self.client.get_orders(OpenOrderParams())
            return orders if orders else []
        except Exception as e:
            self.logger.error(f"Error fetching open orders: {e}")
            return []
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a specific order
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if successful, False otherwise
        """
        if not self.trading_enabled:
            return False
        
        try:
            self.client.cancel(order_id)
            self.logger.info(f"Order {order_id} cancelled")
            return True
        except Exception as e:
            self.logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    def cancel_all_orders(self) -> bool:
        """
        Cancel all open orders
        
        Returns:
            True if successful, False otherwise
        """
        if not self.trading_enabled:
            return False
        
        try:
            self.client.cancel_all()
            self.logger.info("All orders cancelled")
            return True
        except Exception as e:
            self.logger.error(f"Error cancelling all orders: {e}")
            return False
    
    def get_user_trades(self) -> List[Dict]:
        """
        Get user's trade history
        
        Returns:
            List of trades
        """
        if not self.trading_enabled:
            return []
        
        try:
            trades = self.client.get_trades()
            return trades if trades else []
        except Exception as e:
            self.logger.error(f"Error fetching trades: {e}")
            return []
    
    def calculate_implied_probability(self, token_id: str) -> Optional[float]:
        """
        Calculate implied probability from current price
        
        Args:
            token_id: Token ID
            
        Returns:
            Implied probability (0-1) or None
        """
        mid_price = self.get_midpoint_price(token_id)
        if mid_price is not None:
            return mid_price  # Polymarket prices are already probabilities (0-1)
        return None
    
    def get_market_depth(self, token_id: str) -> Dict:
        """
        Analyze market depth and liquidity
        
        Args:
            token_id: Token ID
            
        Returns:
            Dictionary with depth metrics
        """
        orderbook = self.get_orderbook(token_id)
        if not orderbook:
            return {'total_bid_volume': 0, 'total_ask_volume': 0, 'spread': 0}
        
        bids = orderbook.get('bids', [])
        asks = orderbook.get('asks', [])
        
        total_bid_volume = sum(float(bid.get('size', 0)) for bid in bids)
        total_ask_volume = sum(float(ask.get('size', 0)) for ask in asks)
        
        best_bid = float(bids[0].get('price', 0)) if bids else 0
        best_ask = float(asks[0].get('price', 1)) if asks else 1
        spread = best_ask - best_bid
        
        return {
            'total_bid_volume': total_bid_volume,
            'total_ask_volume': total_ask_volume,
            'best_bid': best_bid,
            'best_ask': best_ask,
            'spread': spread,
            'bid_levels': len(bids),
            'ask_levels': len(asks)
        }
