"""
Execution Manager for the Grekko trading platform.

This module provides the main orchestration layer for trade execution across
multiple exchanges (CEX and DEX), with proper error handling, retry logic,
and performance optimization.
"""
import asyncio
import time
from typing import Dict, Any, Optional, List, Union, Tuple
from enum import Enum
from datetime import datetime
import logging

from ..utils.logger import get_logger
from ..utils.metrics import track_latency
from ..risk_management.risk_manager import RiskManager
from .cex.binance_executor import BinanceExecutor
from .cex.coinbase_executor import CoinbaseExecutor
from .cex.order_router import OrderRouter
from .dex.uniswap_executor import UniswapExecutor
from .dex.sushiswap_executor import SushiswapExecutor
from .decentralized_execution.transaction_router import TransactionRouter
from .decentralized_execution.wallet_manager import WalletManager
from .latency_optimizer import LatencyOptimizer


class ExchangeType(Enum):
    """Types of exchanges supported."""
    CEX = "centralized"
    DEX = "decentralized"


class OrderType(Enum):
    """Types of orders supported."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class OrderStatus(Enum):
    """Status of an order."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ExecutionManager:
    """
    Main execution orchestration layer for the Grekko trading platform.
    
    Manages trade execution across multiple exchanges, handles order routing,
    implements retry logic, and optimizes for latency.
    """
    
    def __init__(self, config: Dict[str, Any], risk_manager: RiskManager):
        """
        Initialize the ExecutionManager.
        
        Args:
            config: Configuration dictionary
            risk_manager: Risk management instance
        """
        self.config = config
        self.risk_manager = risk_manager
        self.logger = get_logger('execution_manager')
        
        # Initialize components
        self.latency_optimizer = LatencyOptimizer(config.get('latency', {}))
        self.order_router = OrderRouter(config.get('routing', {}))
        self.wallet_manager = WalletManager(config.get('wallet', {}))
        self.transaction_router = TransactionRouter(config.get('dex', {}))
        
        # Initialize exchange executors
        self.executors = {}
        self._init_executors()
        
        # Performance tracking
        self.metrics = {
            'total_orders': 0,
            'successful_orders': 0,
            'failed_orders': 0,
            'avg_latency_ms': 0,
            'total_volume': 0
        }
        
        # Order tracking
        self.active_orders = {}
        self.order_history = []
        
        self.logger.info("ExecutionManager initialized with %d executors", len(self.executors))
    
    def _init_executors(self) -> None:
        """Initialize exchange executors based on configuration."""
        exchanges_config = self.config.get('exchanges', {})
        
        # Initialize CEX executors
        if 'binance' in exchanges_config:
            self.executors['binance'] = BinanceExecutor(exchanges_config['binance'])
            
        if 'coinbase' in exchanges_config:
            self.executors['coinbase'] = CoinbaseExecutor(exchanges_config['coinbase'])
            
        # Initialize DEX executors
        if 'uniswap' in exchanges_config:
            self.executors['uniswap'] = UniswapExecutor(exchanges_config['uniswap'])
            
        if 'sushiswap' in exchanges_config:
            self.executors['sushiswap'] = SushiswapExecutor(exchanges_config['sushiswap'])
    
    @track_latency("execute_order")
    async def execute_order(self,
                          symbol: str,
                          side: str,
                          amount: float,
                          order_type: OrderType = OrderType.MARKET,
                          price: Optional[float] = None,
                          exchange: Optional[str] = None,
                          **kwargs) -> Dict[str, Any]:
        """
        Execute a trading order with full lifecycle management.
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Order amount
            order_type: Type of order
            price: Price for limit orders
            exchange: Specific exchange to use (optional)
            **kwargs: Additional order parameters
            
        Returns:
            Order execution result
        """
        start_time = time.time()
        order_id = self._generate_order_id()
        
        try:
            # Pre-execution checks
            self._validate_order_params(symbol, side, amount, order_type, price)
            
            # Risk management check
            risk_check = await self.risk_manager.check_order(
                symbol=symbol,
                side=side,
                amount=amount,
                price=price or await self._get_market_price(symbol, exchange)
            )
            
            if not risk_check['approved']:
                self.logger.warning(f"Order rejected by risk manager: {risk_check['reason']}")
                return {
                    'order_id': order_id,
                    'status': OrderStatus.FAILED.value,
                    'reason': risk_check['reason'],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Route order to best exchange
            if not exchange:
                exchange = await self._select_best_exchange(symbol, side, amount)
            
            # Check if executor exists
            if exchange not in self.executors:
                raise ValueError(f"Exchange {exchange} not configured")
            
            # Track order
            self.active_orders[order_id] = {
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'order_type': order_type.value,
                'price': price,
                'exchange': exchange,
                'status': OrderStatus.PENDING.value,
                'timestamp': datetime.now().isoformat()
            }
            
            # Execute order with retry logic
            result = await self._execute_with_retry(
                exchange=exchange,
                symbol=symbol,
                side=side,
                amount=amount,
                order_type=order_type,
                price=price,
                **kwargs
            )
            
            # Update metrics
            self._update_metrics(result, time.time() - start_time)
            
            # Update order status
            self.active_orders[order_id]['status'] = result.get('status', OrderStatus.FAILED.value)
            
            # Move to history if completed
            if result['status'] in [OrderStatus.FILLED.value, OrderStatus.CANCELLED.value, OrderStatus.FAILED.value]:
                self.order_history.append(self.active_orders.pop(order_id))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Order execution failed: {str(e)}")
            self.metrics['failed_orders'] += 1
            
            return {
                'order_id': order_id,
                'status': OrderStatus.FAILED.value,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _execute_with_retry(self,
                                exchange: str,
                                symbol: str,
                                side: str,
                                amount: float,
                                order_type: OrderType,
                                price: Optional[float] = None,
                                max_retries: int = 3,
                                **kwargs) -> Dict[str, Any]:
        """
        Execute order with retry logic for resilience.
        
        Args:
            exchange: Exchange to execute on
            symbol: Trading pair
            side: Buy or sell
            amount: Order amount
            order_type: Type of order
            price: Order price (for limit orders)
            max_retries: Maximum retry attempts
            **kwargs: Additional parameters
            
        Returns:
            Execution result
        """
        executor = self.executors[exchange]
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Apply latency optimization
                optimized_params = await self.latency_optimizer.optimize_order_params(
                    exchange=exchange,
                    order_type=order_type,
                    current_params=kwargs
                )
                
                # Execute based on order type
                if order_type == OrderType.MARKET:
                    result = await executor.market_order(symbol, side, amount, **optimized_params)
                elif order_type == OrderType.LIMIT:
                    if not price:
                        raise ValueError("Price required for limit orders")
                    result = await executor.limit_order(symbol, side, amount, price, **optimized_params)
                elif order_type == OrderType.STOP_LOSS:
                    if not price:
                        raise ValueError("Stop price required for stop loss orders")
                    result = await executor.stop_loss_order(symbol, side, amount, price, **optimized_params)
                else:
                    raise ValueError(f"Unsupported order type: {order_type}")
                
                # Success
                return result
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"Execution attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
                    
                    # Try failover exchange if available
                    if self.config.get('enable_failover', True):
                        failover_exchange = await self._get_failover_exchange(exchange, symbol)
                        if failover_exchange:
                            exchange = failover_exchange
                            executor = self.executors[exchange]
                            self.logger.info(f"Failing over to {exchange}")
        
        # All retries failed
        raise Exception(f"Order execution failed after {max_retries} attempts: {str(last_error)}")
    
    async def cancel_order(self, order_id: str, exchange: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel an active order.
        
        Args:
            order_id: Order ID to cancel
            exchange: Exchange where order was placed
            
        Returns:
            Cancellation result
        """
        try:
            # Find order
            order = self.active_orders.get(order_id)
            if not order:
                return {
                    'success': False,
                    'error': 'Order not found',
                    'order_id': order_id
                }
            
            exchange = exchange or order['exchange']
            executor = self.executors.get(exchange)
            
            if not executor:
                return {
                    'success': False,
                    'error': f'Exchange {exchange} not configured',
                    'order_id': order_id
                }
            
            # Cancel on exchange
            result = await executor.cancel_order(order_id, order['symbol'])
            
            # Update order status
            if result.get('success'):
                order['status'] = OrderStatus.CANCELLED.value
                self.order_history.append(self.active_orders.pop(order_id))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Order cancellation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'order_id': order_id
            }
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get the current status of an order.
        
        Args:
            order_id: Order ID to check
            
        Returns:
            Order status information
        """
        # Check active orders
        if order_id in self.active_orders:
            order = self.active_orders[order_id]
            
            # Update status from exchange
            executor = self.executors.get(order['exchange'])
            if executor:
                try:
                    exchange_status = await executor.get_order_status(order_id, order['symbol'])
                    order['status'] = exchange_status.get('status', order['status'])
                    order['filled_amount'] = exchange_status.get('filled_amount', 0)
                except Exception as e:
                    self.logger.error(f"Failed to update order status: {str(e)}")
            
            return order
        
        # Check history
        for order in self.order_history:
            if order.get('order_id') == order_id:
                return order
        
        return {'error': 'Order not found', 'order_id': order_id}
    
    async def _select_best_exchange(self, symbol: str, side: str, amount: float) -> str:
        """
        Select the best exchange for order execution based on multiple factors.
        
        Args:
            symbol: Trading pair
            side: Buy or sell
            amount: Order amount
            
        Returns:
            Best exchange name
        """
        candidates = []
        
        for exchange_name, executor in self.executors.items():
            try:
                # Check if symbol is supported
                if not await executor.is_symbol_supported(symbol):
                    continue
                
                # Get exchange metrics
                metrics = await self._get_exchange_metrics(exchange_name, symbol, side, amount)
                candidates.append((exchange_name, metrics))
                
            except Exception as e:
                self.logger.warning(f"Failed to evaluate {exchange_name}: {str(e)}")
        
        if not candidates:
            raise ValueError(f"No exchange supports {symbol}")
        
        # Score exchanges based on multiple factors
        best_exchange = max(candidates, key=lambda x: self._score_exchange(x[1]))
        
        return best_exchange[0]
    
    async def _get_exchange_metrics(self, 
                                  exchange: str, 
                                  symbol: str, 
                                  side: str, 
                                  amount: float) -> Dict[str, Any]:
        """
        Get metrics for exchange evaluation.
        
        Args:
            exchange: Exchange name
            symbol: Trading pair
            side: Buy or sell
            amount: Order amount
            
        Returns:
            Exchange metrics
        """
        executor = self.executors[exchange]
        
        # Get orderbook to check liquidity
        orderbook = await executor.get_orderbook(symbol)
        
        # Calculate slippage
        slippage = self._calculate_slippage(orderbook, side, amount)
        
        # Get fees
        fees = await executor.get_trading_fees(symbol)
        
        # Get recent latency
        latency = self.latency_optimizer.get_exchange_latency(exchange)
        
        return {
            'exchange': exchange,
            'slippage': slippage,
            'fees': fees,
            'latency': latency,
            'liquidity': self._calculate_liquidity(orderbook)
        }
    
    def _score_exchange(self, metrics: Dict[str, Any]) -> float:
        """
        Score an exchange based on metrics.
        
        Args:
            metrics: Exchange metrics
            
        Returns:
            Score (higher is better)
        """
        # Weighted scoring
        weights = {
            'slippage': -2.0,  # Lower is better
            'fees': -1.0,      # Lower is better
            'latency': -0.5,   # Lower is better
            'liquidity': 1.0   # Higher is better
        }
        
        score = 0
        score += weights['slippage'] * metrics.get('slippage', 0)
        score += weights['fees'] * metrics.get('fees', {}).get('taker', 0)
        score += weights['latency'] * metrics.get('latency', 100)
        score += weights['liquidity'] * metrics.get('liquidity', 0)
        
        return score
    
    def _calculate_slippage(self, orderbook: Dict[str, Any], side: str, amount: float) -> float:
        """
        Calculate expected slippage for an order.
        
        Args:
            orderbook: Exchange orderbook
            side: Buy or sell
            amount: Order amount
            
        Returns:
            Expected slippage percentage
        """
        book_side = 'asks' if side == 'buy' else 'bids'
        levels = orderbook.get(book_side, [])
        
        if not levels:
            return 1.0  # High slippage if no orderbook
        
        remaining = amount
        total_cost = 0
        
        for price, size in levels:
            if remaining <= 0:
                break
                
            fill_size = min(remaining, size)
            total_cost += fill_size * price
            remaining -= fill_size
        
        if remaining > 0:
            # Not enough liquidity
            return 1.0
        
        avg_price = total_cost / amount
        best_price = levels[0][0]
        
        return abs(avg_price - best_price) / best_price
    
    def _calculate_liquidity(self, orderbook: Dict[str, Any]) -> float:
        """
        Calculate liquidity score from orderbook.
        
        Args:
            orderbook: Exchange orderbook
            
        Returns:
            Liquidity score
        """
        bid_liquidity = sum(price * size for price, size in orderbook.get('bids', [])[:10])
        ask_liquidity = sum(price * size for price, size in orderbook.get('asks', [])[:10])
        
        return (bid_liquidity + ask_liquidity) / 2
    
    async def _get_failover_exchange(self, primary_exchange: str, symbol: str) -> Optional[str]:
        """
        Get a failover exchange for the given symbol.
        
        Args:
            primary_exchange: Primary exchange that failed
            symbol: Trading pair
            
        Returns:
            Failover exchange name or None
        """
        for exchange_name, executor in self.executors.items():
            if exchange_name != primary_exchange:
                try:
                    if await executor.is_symbol_supported(symbol):
                        return exchange_name
                except:
                    continue
        
        return None
    
    async def _get_market_price(self, symbol: str, exchange: Optional[str] = None) -> float:
        """
        Get current market price for a symbol.
        
        Args:
            symbol: Trading pair
            exchange: Specific exchange (optional)
            
        Returns:
            Current market price
        """
        if exchange and exchange in self.executors:
            ticker = await self.executors[exchange].get_ticker(symbol)
            return ticker.get('last', 0)
        
        # Get from first available exchange
        for executor in self.executors.values():
            try:
                ticker = await executor.get_ticker(symbol)
                return ticker.get('last', 0)
            except:
                continue
        
        raise ValueError(f"Could not get market price for {symbol}")
    
    def _validate_order_params(self, 
                             symbol: str, 
                             side: str, 
                             amount: float, 
                             order_type: OrderType,
                             price: Optional[float]) -> None:
        """
        Validate order parameters.
        
        Args:
            symbol: Trading pair
            side: Buy or sell
            amount: Order amount
            order_type: Type of order
            price: Order price
            
        Raises:
            ValueError: If parameters are invalid
        """
        if not symbol:
            raise ValueError("Symbol is required")
            
        if side not in ['buy', 'sell']:
            raise ValueError(f"Invalid side: {side}")
            
        if amount <= 0:
            raise ValueError(f"Invalid amount: {amount}")
            
        if order_type in [OrderType.LIMIT, OrderType.STOP_LOSS] and not price:
            raise ValueError(f"Price required for {order_type.value} orders")
            
        if price and price <= 0:
            raise ValueError(f"Invalid price: {price}")
    
    def _generate_order_id(self) -> str:
        """Generate a unique order ID."""
        import uuid
        return f"GREKKO-{uuid.uuid4().hex[:8].upper()}"
    
    def _update_metrics(self, result: Dict[str, Any], latency: float) -> None:
        """
        Update performance metrics.
        
        Args:
            result: Order execution result
            latency: Execution latency in seconds
        """
        self.metrics['total_orders'] += 1
        
        if result.get('status') == OrderStatus.FILLED.value:
            self.metrics['successful_orders'] += 1
            self.metrics['total_volume'] += result.get('filled_amount', 0) * result.get('price', 0)
        else:
            self.metrics['failed_orders'] += 1
        
        # Update average latency
        current_avg = self.metrics['avg_latency_ms']
        total_orders = self.metrics['total_orders']
        self.metrics['avg_latency_ms'] = ((current_avg * (total_orders - 1)) + (latency * 1000)) / total_orders
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics."""
        return dict(self.metrics)
    
    def get_active_orders(self) -> Dict[str, Dict[str, Any]]:
        """Get all active orders."""
        return dict(self.active_orders)
    
    async def shutdown(self) -> None:
        """Shutdown the execution manager gracefully."""
        self.logger.info("Shutting down ExecutionManager")
        
        # Cancel all active orders
        for order_id in list(self.active_orders.keys()):
            try:
                await self.cancel_order(order_id)
            except Exception as e:
                self.logger.error(f"Failed to cancel order {order_id}: {str(e)}")
        
        # Shutdown executors
        for executor in self.executors.values():
            if hasattr(executor, 'shutdown'):
                await executor.shutdown()
        
        self.logger.info("ExecutionManager shutdown complete")