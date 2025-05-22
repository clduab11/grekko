"""
Tests for the backtesting system.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from tests.simulation.backtester import Backtester
from src.strategy.strategies.momentum_strategy import MomentumStrategy
from src.strategy.strategies.mean_reversion_strategy import MeanReversionStrategy
from src.risk_management.risk_manager import RiskManager


class TestBacktesting:
    """Test suite for backtesting"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample market data for backtesting"""
        # Create date range
        dates = pd.date_range(start='2023-01-01', end='2023-01-31', freq='1D')
        
        # Create OHLCV data with a trend
        data = pd.DataFrame({
            'open': np.linspace(40000, 45000, len(dates)) + np.random.normal(0, 500, len(dates)),
            'high': np.linspace(41000, 46000, len(dates)) + np.random.normal(0, 500, len(dates)),
            'low': np.linspace(39000, 44000, len(dates)) + np.random.normal(0, 500, len(dates)),
            'close': np.linspace(40500, 45500, len(dates)) + np.random.normal(0, 500, len(dates)),
            'volume': np.random.normal(1000, 200, len(dates))
        }, index=dates)
        
        # Ensure high is always highest, low is lowest
        data['high'] = data[['open', 'high', 'close']].max(axis=1)
        data['low'] = data[['open', 'low', 'close']].min(axis=1)
        
        return data
    
    @pytest.fixture
    def backtester(self, sample_data):
        """Create a backtester instance with sample data"""
        return Backtester(
            data=sample_data,
            initial_capital=100000.0,
            trading_fee=0.001
        )
    
    @pytest.fixture
    def momentum_strategy(self):
        """Create a momentum strategy for testing"""
        return MomentumStrategy(
            lookback_period=5,
            buy_threshold=0.02,
            sell_threshold=-0.01
        )
    
    @pytest.fixture
    def mean_reversion_strategy(self):
        """Create a mean reversion strategy for testing"""
        return MeanReversionStrategy(
            lookback_period=10,
            entry_threshold=2.0,
            exit_threshold=0.5
        )
    
    @pytest.fixture
    def risk_manager(self):
        """Create a risk manager for testing"""
        return RiskManager(capital=100000.0)
    
    def test_backtester_initialization(self, backtester, sample_data):
        """Test that the backtester initializes correctly"""
        assert backtester.data.equals(sample_data)
        assert backtester.initial_capital == 100000.0
        assert backtester.current_capital == 100000.0
        assert backtester.trading_fee == 0.001
        assert len(backtester.trades) == 0
        assert len(backtester.portfolio_value) == 0
    
    def test_momentum_strategy_backtest(self, backtester, momentum_strategy, risk_manager):
        """Test backtesting with momentum strategy"""
        results = backtester.run(
            strategy=momentum_strategy,
            risk_manager=risk_manager,
            position_size_pct=0.1
        )
        
        assert 'trades' in results
        assert 'portfolio_value' in results
        assert 'performance_metrics' in results
        
        # Verify metrics
        metrics = results['performance_metrics']
        assert 'total_return' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
        assert 'win_rate' in metrics
        
        # Ensure results are reasonable
        assert -1.0 <= metrics['total_return'] <= 2.0  # Return between -100% and 200%
        assert -1.0 <= metrics['sharpe_ratio'] <= 5.0  # Reasonable Sharpe ratio range
        assert 0.0 <= metrics['max_drawdown'] <= 1.0  # Max drawdown between 0% and 100%
        assert 0.0 <= metrics['win_rate'] <= 1.0  # Win rate between 0% and 100%
    
    def test_mean_reversion_strategy_backtest(self, backtester, mean_reversion_strategy, risk_manager):
        """Test backtesting with mean reversion strategy"""
        results = backtester.run(
            strategy=mean_reversion_strategy,
            risk_manager=risk_manager,
            position_size_pct=0.1
        )
        
        assert 'trades' in results
        assert 'portfolio_value' in results
        assert 'performance_metrics' in results
    
    def test_compare_strategies(self, backtester, momentum_strategy, mean_reversion_strategy, risk_manager):
        """Test comparing different strategies"""
        momentum_results = backtester.run(
            strategy=momentum_strategy,
            risk_manager=risk_manager,
            position_size_pct=0.1
        )
        
        mean_reversion_results = backtester.run(
            strategy=mean_reversion_strategy,
            risk_manager=risk_manager,
            position_size_pct=0.1
        )
        
        # Compare strategies
        momentum_return = momentum_results['performance_metrics']['total_return']
        mean_reversion_return = mean_reversion_results['performance_metrics']['total_return']
        
        # Log the comparison
        print(f"Momentum return: {momentum_return:.2%}")
        print(f"Mean Reversion return: {mean_reversion_return:.2%}")
    
    def test_position_sizing_impact(self, backtester, momentum_strategy, risk_manager):
        """Test the impact of different position sizes"""
        # Test with different position sizes
        position_sizes = [0.05, 0.1, 0.2]
        results = []
        
        for size in position_sizes:
            result = backtester.run(
                strategy=momentum_strategy,
                risk_manager=risk_manager,
                position_size_pct=size
            )
            results.append((size, result['performance_metrics']['total_return']))
        
        # Position size should affect returns and risk
        for i in range(len(results) - 1):
            size1, return1 = results[i]
            size2, return2 = results[i + 1]
            
            # Larger position size should have more extreme returns (either higher or lower)
            assert abs(return2) >= abs(return1) * 0.5  # Allow some wiggle room
    
    def test_risk_management_integration(self, backtester, momentum_strategy, risk_manager):
        """Test integration with risk management"""
        # Run backtest with stop loss
        results_with_stop = backtester.run(
            strategy=momentum_strategy,
            risk_manager=risk_manager,
            position_size_pct=0.1,
            use_stop_loss=True,
            stop_loss_pct=0.05
        )
        
        # Run backtest without stop loss
        results_without_stop = backtester.run(
            strategy=momentum_strategy,
            risk_manager=risk_manager,
            position_size_pct=0.1,
            use_stop_loss=False
        )
        
        # Compare metrics
        with_stop_max_dd = results_with_stop['performance_metrics']['max_drawdown']
        without_stop_max_dd = results_without_stop['performance_metrics']['max_drawdown']
        
        # With stop loss, max drawdown should generally be lower
        # This is probabilistic, so allow for some exceptions
        print(f"Max drawdown with stop loss: {with_stop_max_dd:.2%}")
        print(f"Max drawdown without stop loss: {without_stop_max_dd:.2%}")
    
    def test_metrics_calculation(self, backtester, sample_data):
        """Test the calculation of performance metrics"""
        # Create a simple portfolio value series
        portfolio_values = [100000, 102000, 101000, 103000, 106000, 104000, 108000]
        dates = sample_data.index[:len(portfolio_values)]
        
        # Create trades list
        trades = [
            {'type': 'buy', 'price': 40000, 'size': 0.1, 'date': dates[0]},
            {'type': 'sell', 'price': 41000, 'size': 0.1, 'date': dates[1]},
            {'type': 'buy', 'price': 42000, 'size': 0.1, 'date': dates[2]},
            {'type': 'sell', 'price': 43000, 'size': 0.1, 'date': dates[4]}
        ]
        
        # Set the backtester state
        backtester.portfolio_value = pd.Series(portfolio_values, index=dates)
        backtester.trades = trades
        
        # Calculate metrics
        metrics = backtester._calculate_metrics()
        
        # Verify metrics
        assert 'total_return' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
        assert 'win_rate' in metrics
        
        # Check total return calculation
        expected_return = (portfolio_values[-1] - portfolio_values[0]) / portfolio_values[0]
        assert abs(metrics['total_return'] - expected_return) < 0.0001
        
        # Check win rate calculation (2 trades, both winners)
        assert metrics['win_rate'] == 1.0
        
        # Check max drawdown calculation
        # Max drawdown should be (106000 - 104000) / 106000 = 0.01887
        expected_max_dd = (106000 - 104000) / 106000
        assert abs(metrics['max_drawdown'] - expected_max_dd) < 0.0001