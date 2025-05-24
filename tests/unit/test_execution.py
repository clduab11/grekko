"""
Unit tests for the execution layer components.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from src.execution.execution_manager import (
    ExecutionManager, ExchangeType, OrderType, OrderStatus
)
from src.execution.latency_optimizer import LatencyOptimizer
from src.execution.cex.order_router import OrderRouter, RoutingStrategy


class TestExecutionManager:
    """Test suite for ExecutionManager."""
    
    @pytest.fixture
    def mock_risk_manager(self):
        """Create a mock risk manager."""
        risk_manager = MagicMock()
        risk_manager.check_order = AsyncMock(return_value={
            'approved': True,
            'reason': None
        })
        return risk_manager
    
    @pytest.fixture
    def mock_config(self):
        """Create test configuration."""
        return {
            'exchanges': {
                'binance': {'enabled': True},
                'coinbase': {'enabled': True}
            },
            'latency': {'target_latency_ms': 50},
            'routing': {'default_strategy': 'smart_routing'}
        }
    
    @pytest.fixture
    async def execution_manager(self, mock_config, mock_risk_manager):
        """Create ExecutionManager instance for testing."""
        with patch('src.execution.execution_manager.BinanceExecutor'), \
             patch('src.execution.execution_manager.CoinbaseExecutor'):
            manager = ExecutionManager(mock_config, mock_risk_manager)
            yield manager
    
    @pytest.mark.asyncio
    async def test_execute_order_success(self, execution_manager, mock_risk_manager):
        """Test successful order execution."""
        # Mock executor
        mock_executor = AsyncMock()
        mock_executor.market_order.return_value = {
            'order_id': 'TEST123',
            'status': 'filled',
            'filled_amount': 0.1,
            'price': 50000
        }
        execution_manager.executors['binance'] = mock_executor
        
        # Execute order
        result = await execution_manager.execute_order(
            symbol='BTC/USDT',
            side='buy',
            amount=0.1,
            order_type=OrderType.MARKET,
            exchange='binance'
        )
        
        # Verify
        assert result['status'] == OrderStatus.FILLED.value
        assert 'order_id' in result
        mock_risk_manager.check_order.assert_called_once()
        mock_executor.market_order.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_order_risk_rejection(self, execution_manager, mock_risk_manager):
        """Test order rejected by risk manager."""
        # Configure risk rejection
        mock_risk_manager.check_order.return_value = {
            'approved': False,
            'reason': 'Exceeds position limit'
        }
        
        # Execute order
        result = await execution_manager.execute_order(
            symbol='BTC/USDT',
            side='buy',
            amount=10.0,
            exchange='binance'
        )
        
        # Verify rejection
        assert result['status'] == OrderStatus.FAILED.value
        assert result['reason'] == 'Exceeds position limit'
    
    @pytest.mark.asyncio
    async def test_execute_order_with_retry(self, execution_manager):
        """Test order execution with retry logic."""
        # Mock executor that fails then succeeds
        mock_executor = AsyncMock()
        mock_executor.market_order.side_effect = [
            Exception("Network error"),
            {'order_id': 'TEST456', 'status': 'filled', 'filled_amount': 0.1}
        ]
        execution_manager.executors['binance'] = mock_executor
        
        # Execute order
        result = await execution_manager.execute_order(
            symbol='BTC/USDT',
            side='buy',
            amount=0.1,
            exchange='binance'
        )
        
        # Verify retry worked
        assert result['status'] == OrderStatus.FILLED.value
        assert mock_executor.market_order.call_count == 2
    
    @pytest.mark.asyncio
    async def test_cancel_order(self, execution_manager):
        """Test order cancellation."""
        # Add active order
        order_id = 'TEST789'
        execution_manager.active_orders[order_id] = {
            'symbol': 'BTC/USDT',
            'exchange': 'binance',
            'status': OrderStatus.PENDING.value
        }
        
        # Mock executor
        mock_executor = AsyncMock()
        mock_executor.cancel_order.return_value = {'success': True}
        execution_manager.executors['binance'] = mock_executor
        
        # Cancel order
        result = await execution_manager.cancel_order(order_id)
        
        # Verify
        assert result['success'] is True
        assert order_id not in execution_manager.active_orders
        mock_executor.cancel_order.assert_called_once()
    
    def test_validate_order_params(self, execution_manager):
        """Test order parameter validation."""
        # Valid parameters
        execution_manager._validate_order_params(
            'BTC/USDT', 'buy', 0.1, OrderType.MARKET, None
        )
        
        # Invalid side
        with pytest.raises(ValueError, match="Invalid side"):
            execution_manager._validate_order_params(
                'BTC/USDT', 'invalid', 0.1, OrderType.MARKET, None
            )
        
        # Invalid amount
        with pytest.raises(ValueError, match="Invalid amount"):
            execution_manager._validate_order_params(
                'BTC/USDT', 'buy', -0.1, OrderType.MARKET, None
            )
        
        # Missing price for limit order
        with pytest.raises(ValueError, match="Price required"):
            execution_manager._validate_order_params(
                'BTC/USDT', 'buy', 0.1, OrderType.LIMIT, None
            )


class TestLatencyOptimizer:
    """Test suite for LatencyOptimizer."""
    
    @pytest.fixture
    def latency_optimizer(self):
        """Create LatencyOptimizer instance."""
        config = {
            'enabled': True,
            'target_latency_ms': 50,
            'max_history_size': 100
        }
        return LatencyOptimizer(config)
    
    def test_record_latency(self, latency_optimizer):
        """Test latency recording."""
        # Record some latencies
        latency_optimizer.record_latency('binance', 45.5, success=True)
        latency_optimizer.record_latency('binance', 55.2, success=True)
        latency_optimizer.record_latency('binance', 150.0, success=False)
        
        # Check metrics
        metrics = latency_optimizer.get_exchange_metrics('binance')
        assert metrics['sample_count'] == 3
        assert metrics['avg_latency'] > 0
        assert metrics['success_rate'] == 2/3
    
    def test_get_fastest_exchange(self, latency_optimizer):
        """Test finding fastest exchange."""
        # Record latencies for multiple exchanges
        latency_optimizer.record_latency('binance', 30.0)
        latency_optimizer.record_latency('coinbase', 50.0)
        latency_optimizer.record_latency('kraken', 40.0)
        
        # Find fastest
        fastest = latency_optimizer.get_fastest_exchange(['binance', 'coinbase', 'kraken'])
        assert fastest == 'binance'
    
    def test_should_retry_exchange(self, latency_optimizer):
        """Test retry decision logic."""
        # Good performance - should retry
        for _ in range(10):
            latency_optimizer.record_latency('binance', 30.0, success=True)
        assert latency_optimizer.should_retry_exchange('binance') is True
        
        # Poor success rate - should not retry
        for _ in range(10):
            latency_optimizer.record_latency('coinbase', 40.0, success=False)
        assert latency_optimizer.should_retry_exchange('coinbase') is False
    
    @pytest.mark.asyncio
    async def test_optimize_order_params(self, latency_optimizer):
        """Test order parameter optimization."""
        # Record high latency
        for _ in range(5):
            latency_optimizer.record_latency('binance', 150.0)
        
        # Optimize parameters
        params = {'timeout': 5, 'batch_size': 10}
        optimized = await latency_optimizer.optimize_order_params(
            'binance', 'market', params
        )
        
        # Check optimizations
        assert optimized['use_connection_pool'] is True
        assert optimized['enable_compression'] is True
        assert 'optimal_send_time' in optimized


class TestOrderRouter:
    """Test suite for OrderRouter."""
    
    @pytest.fixture
    def order_router(self):
        """Create OrderRouter instance."""
        config = {
            'default_strategy': 'smart_routing',
            'enable_split_routing': True,
            'max_route_splits': 3
        }
        return OrderRouter(config)
    
    @pytest.fixture
    def mock_exchanges(self):
        """Create mock exchange executors."""
        exchanges = {}
        
        for name in ['binance', 'coinbase', 'kraken']:
            executor = AsyncMock()
            executor.is_symbol_supported.return_value = True
            executor.get_ticker.return_value = {
                'bid': 49900, 'ask': 50100, 'last': 50000
            }
            executor.get_orderbook.return_value = {
                'bids': [[49900, 10], [49800, 20]],
                'asks': [[50100, 10], [50200, 20]]
            }
            executor.get_trading_fees.return_value = {
                'maker': 0.001, 'taker': 0.001
            }
            exchanges[name] = executor
        
        return exchanges
    
    @pytest.mark.asyncio
    async def test_route_best_price(self, order_router, mock_exchanges):
        """Test routing to best price."""
        # Set different prices
        mock_exchanges['binance'].get_ticker.return_value = {'ask': 50000}
        mock_exchanges['coinbase'].get_ticker.return_value = {'ask': 50100}
        
        # Route order
        routing = await order_router.route_order(
            symbol='BTC/USDT',
            side='buy',
            amount=0.1,
            order_type='market',
            exchanges=mock_exchanges,
            strategy=RoutingStrategy.BEST_PRICE
        )
        
        # Verify best price selection
        assert routing['strategy'] == RoutingStrategy.BEST_PRICE.value
        assert len(routing['routes']) == 1
        assert routing['routes'][0]['exchange'] == 'binance'
    
    @pytest.mark.asyncio
    async def test_route_lowest_fee(self, order_router, mock_exchanges):
        """Test routing to lowest fee exchange."""
        # Set different fees
        mock_exchanges['binance'].get_trading_fees.return_value = {
            'taker': 0.001
        }
        mock_exchanges['coinbase'].get_trading_fees.return_value = {
            'taker': 0.0025
        }
        
        # Route order
        routing = await order_router.route_order(
            symbol='BTC/USDT',
            side='buy',
            amount=0.1,
            order_type='market',
            exchanges=mock_exchanges,
            strategy=RoutingStrategy.LOWEST_FEE
        )
        
        # Verify lowest fee selection
        assert routing['routes'][0]['exchange'] == 'binance'
        assert routing['routes'][0]['expected_fee_rate'] == 0.001
    
    @pytest.mark.asyncio
    async def test_smart_routing_split(self, order_router, mock_exchanges):
        """Test smart routing with order splitting."""
        order_router.enable_split_routing = True
        
        # Route large order
        routing = await order_router.route_order(
            symbol='BTC/USDT',
            side='buy',
            amount=100000,  # Large order
            order_type='market',
            exchanges=mock_exchanges,
            strategy=RoutingStrategy.SMART_ROUTING
        )
        
        # Verify split routing
        assert routing.get('split_routing') is True
        assert len(routing['routes']) > 1
        
        # Verify total amount
        total_routed = sum(route['amount'] for route in routing['routes'])
        assert total_routed == pytest.approx(100000)
    
    def test_routing_statistics(self, order_router):
        """Test routing statistics tracking."""
        # Add some routing history
        order_router._record_routing_decision({
            'strategy': 'smart_routing',
            'routes': [{'exchange': 'binance', 'amount': 0.1}]
        })
        order_router._record_routing_decision({
            'strategy': 'best_price',
            'split_routing': True,
            'routes': [
                {'exchange': 'binance', 'amount': 0.05},
                {'exchange': 'coinbase', 'amount': 0.05}
            ]
        })
        
        # Get statistics
        stats = order_router.get_routing_statistics()
        
        # Verify
        assert stats['total_routes'] == 2
        assert stats['split_routes'] == 1
        assert stats['exchanges_used']['binance'] == 2
        assert stats['exchanges_used']['coinbase'] == 1
        assert stats['average_routes_per_order'] == 1.5