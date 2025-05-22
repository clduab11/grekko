"""
Unit tests for the MomentumStrategy class.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from src.strategy.strategies.momentum_strategy import MomentumStrategy, TradingSignal
from src.strategy.position_sizer import PositionSizer, PositionSizingMethod
from src.strategy.trade_evaluator import TradeEvaluator, SignalStrength, SignalType
from src.risk_management.circuit_breaker import CircuitBreaker
from src.data_ingestion.connectors.exchange_connectors.binance_connector import BinanceConnector


class TestMomentumStrategy:
    @pytest.fixture
    def mock_risk_manager(self):
        """Create a mock risk manager for testing"""
        risk_manager = MagicMock()
        risk_manager.capital = 10000.0
        risk_manager.get_current_exposure.return_value = 2000.0
        return risk_manager

    @pytest.fixture
    def mock_connector(self):
        """Create a mock BinanceConnector for testing"""
        connector = MagicMock(spec=BinanceConnector)
        connector.create_order = AsyncMock(return_value={
            "id": "123456",
            "symbol": "BTC/USDT",
            "price": 100.0,
            "amount": 1.0,
            "side": "buy"
        })
        return connector

    @pytest.fixture
    def mock_circuit_breaker(self):
        """Create a mock CircuitBreaker for testing"""
        circuit_breaker = MagicMock(spec=CircuitBreaker)
        circuit_breaker.can_trade.return_value = (True, "")
        circuit_breaker.record_trade_result = MagicMock()
        return circuit_breaker

    @pytest.fixture
    def position_sizer(self, mock_risk_manager):
        """Create a PositionSizer instance for testing"""
        return PositionSizer(
            risk_manager=mock_risk_manager,
            default_method=PositionSizingMethod.RISK_BASED,
            max_position_size_pct=0.2,
            min_position_size_quote=10.0
        )

    @pytest.fixture
    def trade_evaluator(self):
        """Create a TradeEvaluator instance for testing"""
        return TradeEvaluator(
            min_signal_strength=0.6,
            min_risk_reward_ratio=1.5
        )

    @pytest.fixture
    def momentum_strategy(self, position_sizer, trade_evaluator, mock_connector, mock_circuit_breaker):
        """Create a MomentumStrategy instance for testing"""
        return MomentumStrategy(
            lookback_period=20,
            entry_threshold=0.05,
            exit_threshold=0.02,
            position_sizer=position_sizer,
            trade_evaluator=trade_evaluator,
            connector=mock_connector,
            circuit_breaker=mock_circuit_breaker
        )

    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data for testing"""
        # Generate sample data with a clear trend
        data = []
        base_price = 100.0
        for i in range(50):
            # Create trend: first 20 bars flat, next 30 bars upward trend
            price_trend = 0 if i < 20 else 0.01
            
            # Add some noise to the price
            noise = (np.random.random() - 0.5) * 2
            
            # Calculate price with trend and noise
            close_price = base_price * (1 + (i * price_trend) + (noise * 0.005))
            
            data.append({
                'timestamp': int((datetime.now() - timedelta(minutes=50-i)).timestamp()),
                'open': close_price * 0.99,
                'high': close_price * 1.02,
                'low': close_price * 0.98,
                'close': close_price,
                'volume': 100000 + (np.random.random() * 50000)
            })
        
        return pd.DataFrame(data)

    @pytest.fixture
    def downtrend_data(self):
        """Create sample OHLCV data with a downtrend for testing"""
        data = []
        base_price = 100.0
        for i in range(50):
            # Create trend: first 20 bars flat, next 30 bars downward trend
            price_trend = 0 if i < 20 else -0.01
            
            # Add some noise to the price
            noise = (np.random.random() - 0.5) * 2
            
            # Calculate price with trend and noise
            close_price = base_price * (1 + (i * price_trend) + (noise * 0.005))
            
            data.append({
                'timestamp': int((datetime.now() - timedelta(minutes=50-i)).timestamp()),
                'open': close_price * 0.99,
                'high': close_price * 1.02,
                'low': close_price * 0.98,
                'close': close_price,
                'volume': 100000 + (np.random.random() * 50000)
            })
        
        return pd.DataFrame(data)

    def test_initialization(self, momentum_strategy):
        """Test proper initialization of the MomentumStrategy class"""
        assert momentum_strategy.lookback_period == 20
        assert momentum_strategy.entry_threshold == 0.05
        assert momentum_strategy.exit_threshold == 0.02
        assert momentum_strategy.use_macd is True
        assert momentum_strategy.use_rsi is True
        assert momentum_strategy.data.empty
        assert momentum_strategy.indicators == {}
        assert momentum_strategy.active_trades == {}
        assert momentum_strategy.trade_history == []
        assert "trades_count" in momentum_strategy.performance_metrics

    def test_add_data_dict(self, momentum_strategy):
        """Test adding data as a dictionary"""
        data_dict = {
            'timestamp': int(datetime.now().timestamp()),
            'open': 100.0,
            'high': 101.0,
            'low': 99.0,
            'close': 100.5,
            'volume': 100000
        }
        
        momentum_strategy.add_data(data_dict)
        assert len(momentum_strategy.data) == 1
        assert momentum_strategy.data['close'].iloc[0] == 100.5

    def test_add_data_dataframe(self, momentum_strategy, sample_data):
        """Test adding data as a DataFrame"""
        momentum_strategy.add_data(sample_data)
        assert len(momentum_strategy.data) == len(sample_data)
        assert momentum_strategy.data['close'].iloc[-1] == sample_data['close'].iloc[-1]

    def test_add_data_missing_columns(self, momentum_strategy):
        """Test adding data with missing columns"""
        # Missing 'close' column but has 'price'
        data_dict = {
            'timestamp': int(datetime.now().timestamp()),
            'price': 100.5,
            'volume': 100000
        }
        
        momentum_strategy.add_data(data_dict)
        assert len(momentum_strategy.data) == 1
        assert momentum_strategy.data['close'].iloc[0] == 100.5

    def test_calculate_indicators(self, momentum_strategy, sample_data):
        """Test calculation of technical indicators"""
        momentum_strategy.add_data(sample_data)
        
        # Verify key indicators
        assert 'momentum' in momentum_strategy.indicators
        assert 'roc' in momentum_strategy.indicators
        assert 'sma_fast' in momentum_strategy.indicators
        assert 'sma_slow' in momentum_strategy.indicators
        assert 'rsi' in momentum_strategy.indicators
        assert 'macd_line' in momentum_strategy.indicators
        assert 'macd_signal' in momentum_strategy.indicators
        assert 'atr' in momentum_strategy.indicators

    def test_calculate_momentum(self, momentum_strategy, sample_data):
        """Test the calculate_momentum method"""
        momentum_strategy.add_data(sample_data)
        
        # Calculate expected momentum manually
        expected_momentum = sample_data['close'].iloc[-1] / sample_data['close'].iloc[-21] - 1
        actual_momentum = momentum_strategy.calculate_momentum()
        
        assert abs(actual_momentum - expected_momentum) < 0.0001

    def test_identify_trade_signal_uptrend(self, momentum_strategy, sample_data):
        """Test signal generation during an uptrend"""
        momentum_strategy.add_data(sample_data)
        
        signal = momentum_strategy.identify_trade_signal()
        
        # In the sample data (which has an uptrend), we should see a BUY signal
        assert signal['action'] == TradingSignal.BUY.value
        assert signal['direction'] == 'long'
        assert signal['strength'] > 0.5
        assert 'current_price' in signal
        assert 'target_price' in signal
        assert 'stop_loss' in signal
        
        # Check signal includes confirmations
        assert 'confirmations' in signal
        assert 'macd' in signal['confirmations']
        assert 'rsi' in signal['confirmations']

    def test_identify_trade_signal_downtrend(self, momentum_strategy, downtrend_data):
        """Test signal generation during a downtrend"""
        momentum_strategy.add_data(downtrend_data)
        
        signal = momentum_strategy.identify_trade_signal()
        
        # In a downtrend, we should see a SELL signal
        assert signal['action'] == TradingSignal.SELL.value
        assert signal['direction'] == 'short'
        assert signal['strength'] > 0.5
        assert 'current_price' in signal
        assert 'target_price' in signal
        assert 'stop_loss' in signal

    def test_identify_trade_signal_insufficient_data(self, momentum_strategy):
        """Test signal generation with insufficient data"""
        # Create insufficient data (less than lookback period)
        insufficient_data = pd.DataFrame([{
            'timestamp': datetime.now().timestamp(),
            'open': 100.0,
            'high': 101.0,
            'low': 99.0,
            'close': 100.5,
            'volume': 100000
        }])
        
        momentum_strategy.add_data(insufficient_data)
        signal = momentum_strategy.identify_trade_signal()
        
        # Should return HOLD due to insufficient data
        assert signal['action'] == TradingSignal.HOLD.value
        assert 'Insufficient data' in signal['reason']

    def test_identify_trade_signal_with_market_data(self, momentum_strategy, sample_data):
        """Test signal generation with additional market data"""
        momentum_strategy.add_data(sample_data)
        
        # Additional market data
        market_data = {
            'symbol': 'BTC/USDT',
            'last': 110.0,
            'volume': 200000
        }
        
        signal = momentum_strategy.identify_trade_signal(market_data)
        
        # Signal should include market data
        assert signal['symbol'] == 'BTC/USDT'
        assert signal['current_price'] == sample_data['close'].iloc[-1]  # Uses historical data close

    @pytest.mark.asyncio
    async def test_execute_trade_buy(self, momentum_strategy, sample_data, mock_connector):
        """Test executing a BUY trade"""
        momentum_strategy.add_data(sample_data)
        
        # Generate a buy signal
        signal = momentum_strategy.identify_trade_signal()
        assert signal['action'] == TradingSignal.BUY.value
        
        # Execute trade
        result = await momentum_strategy.execute_trade(signal)
        
        # Verify trade execution
        assert result['success'] is True
        assert 'order' in result
        assert result['order']['id'] == '123456'
        assert 'trade_id' in result
        assert result['trade_id'] in momentum_strategy.active_trades
        
        # Verify connector was called correctly
        mock_connector.create_order.assert_called_once()
        call_args = mock_connector.create_order.call_args[1]
        assert call_args['symbol'] == signal['symbol']
        assert call_args['side'] == 'buy'
        assert call_args['order_type'] == 'market'
        assert call_args['amount'] > 0

    @pytest.mark.asyncio
    async def test_execute_trade_no_connector(self, momentum_strategy, sample_data):
        """Test executing a trade without a connector"""
        momentum_strategy.connector = None
        momentum_strategy.add_data(sample_data)
        
        # Generate a buy signal
        signal = momentum_strategy.identify_trade_signal()
        
        # Try to execute trade
        result = await momentum_strategy.execute_trade(signal)
        
        # Should fail due to missing connector
        assert result['success'] is False
        assert 'No exchange connector available' in result['message']

    @pytest.mark.asyncio
    async def test_execute_trade_circuit_breaker_active(self, momentum_strategy, sample_data, mock_circuit_breaker):
        """Test executing a trade with active circuit breaker"""
        mock_circuit_breaker.can_trade.return_value = (False, "Max drawdown exceeded")
        momentum_strategy.add_data(sample_data)
        
        # Generate a buy signal
        signal = momentum_strategy.identify_trade_signal()
        
        # Try to execute trade
        result = await momentum_strategy.execute_trade(signal)
        
        # Should fail due to circuit breaker
        assert result['success'] is False
        assert 'Circuit breaker active' in result['message']

    @pytest.mark.asyncio
    async def test_close_trade(self, momentum_strategy, mock_connector):
        """Test closing a trade"""
        # Setup an active trade
        trade_id = "123456"
        momentum_strategy.active_trades[trade_id] = {
            "id": trade_id,
            "symbol": "BTC/USDT",
            "entry_time": datetime.now().isoformat(),
            "entry_price": 100.0,
            "amount": 1.0,
            "side": "buy",
            "target_price": 110.0,
            "stop_loss": 95.0
        }
        
        # Market data for the exit
        market_data = {
            "symbol": "BTC/USDT",
            "last": 110.0
        }
        
        # Close the trade
        result = await momentum_strategy.close_trade(trade_id, market_data)
        
        # Verify trade closing
        assert result['success'] is True
        assert result['trade_id'] == trade_id
        assert trade_id not in momentum_strategy.active_trades
        assert len(momentum_strategy.trade_history) == 1
        
        # Verify performance metrics were updated
        assert momentum_strategy.performance_metrics['trades_count'] > 0
        assert momentum_strategy.performance_metrics['winning_trades'] > 0
        
        # Verify connector was called correctly
        mock_connector.create_order.assert_called_once()
        call_args = mock_connector.create_order.call_args[1]
        assert call_args['symbol'] == "BTC/USDT"
        assert call_args['side'] == 'sell'  # Opposite of entry
        assert call_args['amount'] == 1.0

    @pytest.mark.asyncio
    async def test_close_trade_nonexistent(self, momentum_strategy):
        """Test closing a non-existent trade"""
        result = await momentum_strategy.close_trade("nonexistent")
        
        # Should fail because trade doesn't exist
        assert result['success'] is False
        assert 'not found' in result['message']

    @pytest.mark.asyncio
    async def test_monitor_trades_stop_loss(self, momentum_strategy, mock_connector):
        """Test monitoring trades with stop loss trigger"""
        # Setup an active trade
        trade_id = "123456"
        momentum_strategy.active_trades[trade_id] = {
            "id": trade_id,
            "symbol": "BTC/USDT",
            "entry_time": datetime.now().isoformat(),
            "entry_price": 100.0,
            "amount": 1.0,
            "side": "buy",
            "target_price": 110.0,
            "stop_loss": 95.0
        }
        
        # Market data with price at stop loss
        market_data = {
            "symbol": "BTC/USDT",
            "last": 94.0  # Below stop loss
        }
        
        # Monitor trades
        actions = await momentum_strategy.monitor_trades(market_data)
        
        # Verify stop loss was triggered
        assert len(actions) == 1
        assert actions[0]['action'] == 'stop_loss'
        assert actions[0]['trade_id'] == trade_id
        assert actions[0]['result']['success'] is True
        assert trade_id not in momentum_strategy.active_trades

    @pytest.mark.asyncio
    async def test_monitor_trades_take_profit(self, momentum_strategy, mock_connector):
        """Test monitoring trades with take profit trigger"""
        # Setup an active trade
        trade_id = "123456"
        momentum_strategy.active_trades[trade_id] = {
            "id": trade_id,
            "symbol": "BTC/USDT",
            "entry_time": datetime.now().isoformat(),
            "entry_price": 100.0,
            "amount": 1.0,
            "side": "buy",
            "target_price": 110.0,
            "stop_loss": 95.0
        }
        
        # Market data with price at target
        market_data = {
            "symbol": "BTC/USDT",
            "last": 111.0  # Above target
        }
        
        # Monitor trades
        actions = await momentum_strategy.monitor_trades(market_data)
        
        # Verify take profit was triggered
        assert len(actions) == 1
        assert actions[0]['action'] == 'take_profit'
        assert actions[0]['trade_id'] == trade_id
        assert actions[0]['result']['success'] is True
        assert trade_id not in momentum_strategy.active_trades

    @pytest.mark.asyncio
    async def test_monitor_trades_no_action(self, momentum_strategy):
        """Test monitoring trades with no trigger conditions"""
        # Setup an active trade
        trade_id = "123456"
        momentum_strategy.active_trades[trade_id] = {
            "id": trade_id,
            "symbol": "BTC/USDT",
            "entry_time": datetime.now().isoformat(),
            "entry_price": 100.0,
            "amount": 1.0,
            "side": "buy",
            "target_price": 110.0,
            "stop_loss": 95.0
        }
        
        # Market data with price in normal range (no trigger)
        market_data = {
            "symbol": "BTC/USDT",
            "last": 102.0  # Between stop loss and target
        }
        
        # Monitor trades
        actions = await momentum_strategy.monitor_trades(market_data)
        
        # Verify no actions were taken
        assert len(actions) == 0
        assert trade_id in momentum_strategy.active_trades

    def test_calculate_performance_metrics(self, momentum_strategy):
        """Test calculation of performance metrics"""
        # Setup trade history
        momentum_strategy.trade_history = [
            {
                "entry_price": 100.0,
                "exit_price": 110.0,
                "entry_time": (datetime.now() - timedelta(hours=1)).isoformat(),
                "exit_time": datetime.now().isoformat(),
                "amount": 1.0,
                "pnl_percentage": 0.1,
                "pnl_amount": 10.0
            },
            {
                "entry_price": 100.0,
                "exit_price": 95.0,
                "entry_time": (datetime.now() - timedelta(hours=2)).isoformat(),
                "exit_time": (datetime.now() - timedelta(hours=1)).isoformat(),
                "amount": 1.0,
                "pnl_percentage": -0.05,
                "pnl_amount": -5.0
            },
            {
                "entry_price": 100.0,
                "exit_price": 108.0,
                "entry_time": (datetime.now() - timedelta(hours=3)).isoformat(),
                "exit_time": (datetime.now() - timedelta(hours=2)).isoformat(),
                "amount": 1.0,
                "pnl_percentage": 0.08,
                "pnl_amount": 8.0
            }
        ]
        
        # Setup performance metrics
        momentum_strategy.performance_metrics = {
            "trades_count": 3,
            "winning_trades": 2,
            "losing_trades": 1,
            "win_rate": 2/3,
            "avg_profit_pct": 0.09,
            "avg_loss_pct": 0.05,
            "profit_factor": 0.0,
            "total_pnl": 0.13,
            "max_drawdown": 0.0
        }
        
        # Calculate performance metrics
        metrics = momentum_strategy.calculate_performance_metrics()
        
        # Verify key metrics
        assert metrics["trades_count"] == 3
        assert metrics["winning_trades"] == 2
        assert metrics["losing_trades"] == 1
        assert metrics["win_rate"] == 2/3
        assert abs(metrics["avg_profit_pct"] - 0.09) < 0.0001
        assert abs(metrics["avg_loss_pct"] - 0.05) < 0.0001
        assert metrics["profit_factor"] > 0
        assert abs(metrics["total_pnl"] - 0.13) < 0.0001
        assert metrics["max_drawdown"] >= 0.0

    def test_get_status(self, momentum_strategy, sample_data):
        """Test getting strategy status"""
        momentum_strategy.add_data(sample_data)
        
        # Add a trade to history
        momentum_strategy.trade_history = [{
            "entry_price": 100.0,
            "exit_price": 110.0,
            "entry_time": (datetime.now() - timedelta(hours=1)).isoformat(),
            "exit_time": datetime.now().isoformat(),
            "amount": 1.0,
            "pnl_percentage": 0.1,
            "pnl_amount": 10.0
        }]
        
        # Get status
        status = momentum_strategy.get_status()
        
        # Verify status content
        assert status["name"] == "Momentum Strategy"
        assert "config" in status
        assert status["config"]["lookback_period"] == 20
        assert status["config"]["entry_threshold"] == 0.05
        assert status["data_points"] == len(sample_data)
        assert status["completed_trades"] == 1
        assert "performance" in status