"""
Order routing for CEX exchanges in the Grekko trading platform.

Routes orders to the optimal exchange based on various factors including
liquidity, fees, latency, and slippage.
"""
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from datetime import datetime

from ...utils.logger import get_logger


class RoutingStrategy(Enum):
    """Order routing strategies."""
    BEST_PRICE = "best_price"
    LOWEST_FEE = "lowest_fee"
    FASTEST_EXECUTION = "fastest_execution"
    SMART_ROUTING = "smart_routing"


class OrderRouter:
    """
    Intelligent order routing for centralized exchanges.
    
    Analyzes multiple factors to route orders to the optimal exchange
    for execution quality and cost.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the order router.
        
        Args:
            config: Router configuration
        """
        self.config = config
        self.logger = get_logger('order_router')
        
        # Routing configuration
        self.default_strategy = RoutingStrategy(
            config.get('default_strategy', RoutingStrategy.SMART_ROUTING.value)
        )
        self.enable_split_routing = config.get('enable_split_routing', True)
        self.max_route_splits = config.get('max_route_splits', 3)
        
        # Exchange preferences and weights
        self.exchange_weights = config.get('exchange_weights', {})
        self.blacklisted_exchanges = set(config.get('blacklisted_exchanges', []))
        
        # Routing metrics
        self.routing_history = []
        self.max_history = config.get('max_history', 1000)
        
        self.logger.info(f"OrderRouter initialized with strategy: {self.default_strategy.value}")
    
    async def route_order(self,
                        symbol: str,
                        side: str,
                        amount: float,
                        order_type: str,
                        exchanges: Dict[str, Any],
                        strategy: Optional[RoutingStrategy] = None,
                        **kwargs) -> Dict[str, Any]:
        """
        Route an order to the optimal exchange(s).
        
        Args:
            symbol: Trading pair
            side: Buy or sell
            amount: Order amount
            order_type: Market, limit, etc.
            exchanges: Available exchanges and their executors
            strategy: Routing strategy to use
            **kwargs: Additional routing parameters
            
        Returns:
            Routing decision with exchange(s) and amounts
        """
        strategy = strategy or self.default_strategy
        
        # Filter available exchanges
        available_exchanges = await self._filter_available_exchanges(
            symbol, exchanges, amount
        )
        
        if not available_exchanges:
            raise ValueError(f"No exchanges available for {symbol}")
        
        # Get routing based on strategy
        if strategy == RoutingStrategy.BEST_PRICE:
            routing = await self._route_best_price(
                symbol, side, amount, available_exchanges
            )
        elif strategy == RoutingStrategy.LOWEST_FEE:
            routing = await self._route_lowest_fee(
                symbol, side, amount, available_exchanges
            )
        elif strategy == RoutingStrategy.FASTEST_EXECUTION:
            routing = await self._route_fastest_execution(
                symbol, side, amount, available_exchanges
            )
        else:  # SMART_ROUTING
            routing = await self._route_smart(
                symbol, side, amount, order_type, available_exchanges, **kwargs
            )
        
        # Record routing decision
        self._record_routing_decision(routing)
        
        return routing
    
    async def _filter_available_exchanges(self,
                                        symbol: str,
                                        exchanges: Dict[str, Any],
                                        amount: float) -> Dict[str, Any]:
        """
        Filter exchanges based on availability and constraints.
        
        Args:
            symbol: Trading pair
            exchanges: All exchanges
            amount: Order amount
            
        Returns:
            Filtered exchanges
        """
        available = {}
        
        for exchange_name, executor in exchanges.items():
            # Skip blacklisted
            if exchange_name in self.blacklisted_exchanges:
                continue
            
            try:
                # Check if symbol is supported
                if await executor.is_symbol_supported(symbol):
                    # Check minimum order size
                    min_order = await self._get_min_order_size(
                        executor, symbol
                    )
                    if amount >= min_order:
                        available[exchange_name] = executor
                        
            except Exception as e:
                self.logger.warning(
                    f"Failed to check {exchange_name} availability: {str(e)}"
                )
        
        return available
    
    async def _route_best_price(self,
                              symbol: str,
                              side: str,
                              amount: float,
                              exchanges: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route to exchange with best price.
        
        Args:
            symbol: Trading pair
            side: Buy or sell
            amount: Order amount
            exchanges: Available exchanges
            
        Returns:
            Routing decision
        """
        # Get prices from all exchanges
        price_data = await self._get_prices_from_exchanges(
            symbol, side, amount, exchanges
        )
        
        # Find best price
        if side == 'buy':
            # For buy orders, we want the lowest ask price
            best_exchange = min(price_data.items(), key=lambda x: x[1]['price'])
        else:
            # For sell orders, we want the highest bid price
            best_exchange = max(price_data.items(), key=lambda x: x[1]['price'])
        
        return {
            'strategy': RoutingStrategy.BEST_PRICE.value,
            'routes': [{
                'exchange': best_exchange[0],
                'amount': amount,
                'expected_price': best_exchange[1]['price'],
                'expected_slippage': best_exchange[1]['slippage']
            }],
            'total_amount': amount,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _route_lowest_fee(self,
                              symbol: str,
                              side: str,
                              amount: float,
                              exchanges: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route to exchange with lowest fees.
        
        Args:
            symbol: Trading pair
            side: Buy or sell
            amount: Order amount
            exchanges: Available exchanges
            
        Returns:
            Routing decision
        """
        # Get fees from all exchanges
        fee_data = {}
        
        for exchange_name, executor in exchanges.items():
            try:
                fees = await executor.get_trading_fees(symbol)
                fee_data[exchange_name] = fees['taker']  # Use taker fee for market orders
            except Exception as e:
                self.logger.warning(f"Failed to get fees from {exchange_name}: {str(e)}")
        
        # Find lowest fee
        best_exchange = min(fee_data.items(), key=lambda x: x[1])
        
        return {
            'strategy': RoutingStrategy.LOWEST_FEE.value,
            'routes': [{
                'exchange': best_exchange[0],
                'amount': amount,
                'expected_fee_rate': best_exchange[1]
            }],
            'total_amount': amount,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _route_fastest_execution(self,
                                     symbol: str,
                                     side: str,
                                     amount: float,
                                     exchanges: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route to exchange with fastest execution.
        
        Args:
            symbol: Trading pair
            side: Buy or sell
            amount: Order amount
            exchanges: Available exchanges
            
        Returns:
            Routing decision
        """
        # This would typically use latency optimizer data
        # For now, use exchange weights as a proxy
        
        if self.exchange_weights:
            # Use configured weights
            best_exchange = max(
                exchanges.keys(),
                key=lambda x: self.exchange_weights.get(x, 1.0)
            )
        else:
            # Default to first available
            best_exchange = list(exchanges.keys())[0]
        
        return {
            'strategy': RoutingStrategy.FASTEST_EXECUTION.value,
            'routes': [{
                'exchange': best_exchange,
                'amount': amount
            }],
            'total_amount': amount,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _route_smart(self,
                         symbol: str,
                         side: str,
                         amount: float,
                         order_type: str,
                         exchanges: Dict[str, Any],
                         **kwargs) -> Dict[str, Any]:
        """
        Smart routing considering multiple factors.
        
        Args:
            symbol: Trading pair
            side: Buy or sell
            amount: Order amount
            order_type: Type of order
            exchanges: Available exchanges
            **kwargs: Additional parameters
            
        Returns:
            Routing decision
        """
        # Gather data from all exchanges
        exchange_scores = {}
        
        for exchange_name, executor in exchanges.items():
            try:
                score = await self._calculate_exchange_score(
                    exchange_name, executor, symbol, side, amount, order_type
                )
                exchange_scores[exchange_name] = score
            except Exception as e:
                self.logger.warning(
                    f"Failed to score {exchange_name}: {str(e)}"
                )
        
        if not exchange_scores:
            raise ValueError("Failed to score any exchanges")
        
        # Determine if we should split the order
        if self.enable_split_routing and amount > self._get_split_threshold(symbol):
            return await self._create_split_routing(
                symbol, side, amount, exchange_scores, exchanges
            )
        else:
            # Route to single best exchange
            best_exchange = max(exchange_scores.items(), key=lambda x: x[1]['total_score'])
            
            return {
                'strategy': RoutingStrategy.SMART_ROUTING.value,
                'routes': [{
                    'exchange': best_exchange[0],
                    'amount': amount,
                    'score': best_exchange[1]['total_score'],
                    'factors': best_exchange[1]
                }],
                'total_amount': amount,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _calculate_exchange_score(self,
                                      exchange_name: str,
                                      executor: Any,
                                      symbol: str,
                                      side: str,
                                      amount: float,
                                      order_type: str) -> Dict[str, float]:
        """
        Calculate comprehensive score for an exchange.
        
        Args:
            exchange_name: Name of exchange
            executor: Exchange executor
            symbol: Trading pair
            side: Buy or sell
            amount: Order amount
            order_type: Type of order
            
        Returns:
            Exchange score with breakdown
        """
        score_factors = {}
        
        # Price score (40% weight)
        try:
            ticker = await executor.get_ticker(symbol)
            if side == 'buy':
                price = ticker['ask']
                # Lower price is better for buying
                price_score = 100 / (1 + price)
            else:
                price = ticker['bid']
                # Higher price is better for selling
                price_score = price
            score_factors['price_score'] = price_score * 0.4
        except:
            score_factors['price_score'] = 0
        
        # Fee score (30% weight)
        try:
            fees = await executor.get_trading_fees(symbol)
            fee_rate = fees['taker' if order_type == 'market' else 'maker']
            # Lower fees are better
            fee_score = 100 / (1 + fee_rate * 100)
            score_factors['fee_score'] = fee_score * 0.3
        except:
            score_factors['fee_score'] = 0
        
        # Liquidity score (20% weight)
        try:
            orderbook = await executor.get_orderbook(symbol, limit=10)
            liquidity = self._calculate_liquidity_score(orderbook, side, amount)
            score_factors['liquidity_score'] = liquidity * 0.2
        except:
            score_factors['liquidity_score'] = 0
        
        # Exchange weight (10% weight)
        weight = self.exchange_weights.get(exchange_name, 1.0)
        score_factors['weight_score'] = weight * 10 * 0.1
        
        # Calculate total score
        score_factors['total_score'] = sum(
            v for k, v in score_factors.items() 
            if k != 'total_score'
        )
        
        return score_factors
    
    async def _create_split_routing(self,
                                  symbol: str,
                                  side: str,
                                  amount: float,
                                  exchange_scores: Dict[str, Dict[str, float]],
                                  exchanges: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a split routing across multiple exchanges.
        
        Args:
            symbol: Trading pair
            side: Buy or sell
            amount: Total order amount
            exchange_scores: Scores for each exchange
            exchanges: Exchange executors
            
        Returns:
            Split routing decision
        """
        # Sort exchanges by score
        sorted_exchanges = sorted(
            exchange_scores.items(),
            key=lambda x: x[1]['total_score'],
            reverse=True
        )
        
        # Determine split allocation
        routes = []
        remaining_amount = amount
        
        for i, (exchange_name, score) in enumerate(sorted_exchanges[:self.max_route_splits]):
            if remaining_amount <= 0:
                break
            
            # Allocate based on score weight
            if i < len(sorted_exchanges) - 1:
                # Allocate proportionally to score
                total_score = sum(s[1]['total_score'] for s in sorted_exchanges[:self.max_route_splits])
                allocation = (score['total_score'] / total_score) * amount
                allocation = min(allocation, remaining_amount)
            else:
                # Last exchange gets remaining
                allocation = remaining_amount
            
            routes.append({
                'exchange': exchange_name,
                'amount': allocation,
                'score': score['total_score'],
                'factors': score
            })
            
            remaining_amount -= allocation
        
        return {
            'strategy': RoutingStrategy.SMART_ROUTING.value,
            'split_routing': True,
            'routes': routes,
            'total_amount': amount,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _get_prices_from_exchanges(self,
                                       symbol: str,
                                       side: str,
                                       amount: float,
                                       exchanges: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Get prices and slippage estimates from all exchanges.
        
        Args:
            symbol: Trading pair
            side: Buy or sell
            amount: Order amount
            exchanges: Available exchanges
            
        Returns:
            Price data from each exchange
        """
        price_data = {}
        
        # Gather price data concurrently
        tasks = []
        for exchange_name, executor in exchanges.items():
            tasks.append(self._get_exchange_price(
                exchange_name, executor, symbol, side, amount
            ))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for exchange_name, result in zip(exchanges.keys(), results):
            if not isinstance(result, Exception):
                price_data[exchange_name] = result
            else:
                self.logger.warning(
                    f"Failed to get price from {exchange_name}: {str(result)}"
                )
        
        return price_data
    
    async def _get_exchange_price(self,
                                exchange_name: str,
                                executor: Any,
                                symbol: str,
                                side: str,
                                amount: float) -> Dict[str, float]:
        """
        Get price and slippage for a specific exchange.
        
        Args:
            exchange_name: Name of exchange
            executor: Exchange executor
            symbol: Trading pair
            side: Buy or sell
            amount: Order amount
            
        Returns:
            Price and slippage data
        """
        ticker = await executor.get_ticker(symbol)
        orderbook = await executor.get_orderbook(symbol)
        
        if side == 'buy':
            base_price = ticker['ask']
            book_side = 'asks'
        else:
            base_price = ticker['bid']
            book_side = 'bids'
        
        # Calculate slippage
        slippage = self._estimate_slippage(
            orderbook[book_side], amount, base_price
        )
        
        return {
            'price': base_price,
            'slippage': slippage,
            'effective_price': base_price * (1 + slippage)
        }
    
    def _calculate_liquidity_score(self,
                                 orderbook: Dict[str, Any],
                                 side: str,
                                 amount: float) -> float:
        """
        Calculate liquidity score for an orderbook.
        
        Args:
            orderbook: Exchange orderbook
            side: Buy or sell
            amount: Order amount
            
        Returns:
            Liquidity score (0-100)
        """
        book_side = 'asks' if side == 'buy' else 'bids'
        levels = orderbook.get(book_side, [])
        
        if not levels:
            return 0
        
        # Calculate total liquidity in top levels
        total_liquidity = sum(level[1] for level in levels[:10])
        
        # Score based on ratio of liquidity to order size
        if total_liquidity >= amount * 10:
            return 100  # Excellent liquidity
        elif total_liquidity >= amount * 5:
            return 80   # Good liquidity
        elif total_liquidity >= amount * 2:
            return 60   # Adequate liquidity
        elif total_liquidity >= amount:
            return 40   # Minimal liquidity
        else:
            return 20   # Poor liquidity
    
    def _estimate_slippage(self,
                         levels: List[List[float]],
                         amount: float,
                         base_price: float) -> float:
        """
        Estimate slippage for an order.
        
        Args:
            levels: Orderbook levels
            amount: Order amount
            base_price: Base price
            
        Returns:
            Estimated slippage as decimal
        """
        if not levels:
            return 0.1  # 10% default if no orderbook
        
        remaining = amount
        total_cost = 0
        
        for price, size in levels:
            if remaining <= 0:
                break
            
            fill_size = min(remaining, size)
            total_cost += fill_size * price
            remaining -= fill_size
        
        if remaining > 0:
            # Not enough liquidity, high slippage
            return 0.1
        
        avg_price = total_cost / amount
        slippage = (avg_price - base_price) / base_price
        
        return abs(slippage)
    
    async def _get_min_order_size(self,
                                executor: Any,
                                symbol: str) -> float:
        """
        Get minimum order size for a symbol.
        
        Args:
            executor: Exchange executor
            symbol: Trading pair
            
        Returns:
            Minimum order size
        """
        # This would typically query exchange rules
        # For now, return a default
        return 0.001
    
    def _get_split_threshold(self, symbol: str) -> float:
        """
        Get the threshold for splitting orders.
        
        Args:
            symbol: Trading pair
            
        Returns:
            Split threshold
        """
        # This would be configured per symbol
        # For now, return a default
        return 10000  # Split orders larger than 10k units
    
    def _record_routing_decision(self, routing: Dict[str, Any]) -> None:
        """
        Record a routing decision for analysis.
        
        Args:
            routing: Routing decision
        """
        self.routing_history.append(routing)
        
        # Trim history if needed
        if len(self.routing_history) > self.max_history:
            self.routing_history = self.routing_history[-self.max_history:]
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """
        Get routing statistics.
        
        Returns:
            Routing statistics
        """
        if not self.routing_history:
            return {'total_routes': 0}
        
        stats = {
            'total_routes': len(self.routing_history),
            'strategies_used': {},
            'exchanges_used': {},
            'split_routes': 0,
            'average_routes_per_order': 0
        }
        
        total_routes = 0
        
        for routing in self.routing_history:
            # Count strategies
            strategy = routing.get('strategy', 'unknown')
            stats['strategies_used'][strategy] = stats['strategies_used'].get(strategy, 0) + 1
            
            # Count exchanges
            for route in routing.get('routes', []):
                exchange = route['exchange']
                stats['exchanges_used'][exchange] = stats['exchanges_used'].get(exchange, 0) + 1
                total_routes += 1
            
            # Count split routes
            if routing.get('split_routing', False):
                stats['split_routes'] += 1
        
        stats['average_routes_per_order'] = total_routes / len(self.routing_history)
        
        return stats