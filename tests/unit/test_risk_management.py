"""
Unit tests for the risk management components.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from src.risk_management.risk_manager import RiskManager


class TestRiskManager:
    """Test suite for RiskManager"""
    
    @pytest.fixture
    def risk_manager(self):
        """Create a RiskManager instance for testing"""
        return RiskManager(capital=100000.0, max_trade_size_pct=0.15, max_drawdown_pct=0.10)
    
    def test_init(self, risk_manager):
        """Test initialization of RiskManager"""
        assert risk_manager.capital == 100000.0
        assert risk_manager.max_trade_size_pct == 0.15
        assert risk_manager.max_drawdown_pct == 0.10
    
    def test_calculate_position_size(self, risk_manager):
        """Test calculation of position size based on risk parameters"""
        # Test with 1.5% risk per trade and 5% stop loss
        position_size = risk_manager.calculate_position_size(
            risk_per_trade=0.015,
            stop_loss_distance=0.05
        )
        expected_size = (100000.0 * 0.015) / 0.05
        assert position_size == expected_size
        
        # Test with 2% risk per trade and 10% stop loss
        position_size = risk_manager.calculate_position_size(
            risk_per_trade=0.02,
            stop_loss_distance=0.10
        )
        expected_size = (100000.0 * 0.02) / 0.10
        assert position_size == expected_size
    
    def test_enforce_risk_limits(self, risk_manager):
        """Test enforcing risk limits on trade size"""
        # Test with trade within limits (10% of capital)
        trade_amount = 10000.0  # 10% of capital
        result = risk_manager.enforce_risk_limits(trade_amount)
        assert result == trade_amount
        
        # Test with trade exceeding limits (20% of capital)
        trade_amount = 20000.0  # 20% of capital
        result = risk_manager.enforce_risk_limits(trade_amount)
        assert result == 15000.0  # Should be capped at 15% of capital
    
    def test_time_weighted_order_slicing(self, risk_manager):
        """Test time-weighted order slicing"""
        total_amount = 10000.0
        slices = 5
        interval = 0.01  # Use small interval for testing
        
        # Mock the time.sleep function to avoid waiting
        with patch('time.sleep', return_value=None):
            # Mock the execution function
            mock_execute = MagicMock()
            
            # Execute the slicing
            results = risk_manager.time_weighted_order_slicing(
                total_amount, slices, interval, execute_slice_fn=mock_execute
            )
            
            # Check that execute_slice was called the correct number of times
            assert mock_execute.call_count == slices
            
            # Check that each slice was the correct size
            slice_size = total_amount / slices
            for call in mock_execute.call_args_list:
                args, kwargs = call
                assert args[0] == slice_size
    
    def test_calculate_var_with_empty_data(self, risk_manager):
        """Test VaR calculation with empty data"""
        returns = np.array([])
        var = risk_manager.calculate_var(returns)
        assert var == 0
    
    def test_calculate_var(self, risk_manager):
        """Test Value at Risk calculation"""
        # Create sample returns data
        returns = np.array([-0.01, 0.02, -0.03, 0.01, 0.02, -0.02, 0.03, -0.01])
        
        # Calculate 95% VaR
        var = risk_manager.calculate_var(returns, confidence_level=0.95)
        
        # VaR should be positive (represents a loss)
        assert var > 0
        
        # With this sample, roughly 5% of returns should be worse than VaR
        worse_than_var = np.sum(returns < -var) / len(returns)
        assert abs(worse_than_var - 0.05) < 0.1  # Allow some error due to small sample
    
    def test_calculate_cvar_with_empty_data(self, risk_manager):
        """Test CVaR calculation with empty data"""
        returns = np.array([])
        cvar = risk_manager.calculate_cvar(returns)
        assert cvar == 0
    
    def test_calculate_cvar(self, risk_manager):
        """Test Conditional Value at Risk calculation"""
        # Create sample returns data
        returns = np.array([-0.01, 0.02, -0.03, 0.01, 0.02, -0.02, 0.03, -0.01])
        
        # Calculate 95% CVaR
        cvar = risk_manager.calculate_cvar(returns, confidence_level=0.95)
        
        # CVaR should be positive (represents a loss)
        assert cvar > 0
        
        # Calculate 95% VaR for comparison
        var = risk_manager.calculate_var(returns, confidence_level=0.95)
        
        # CVaR should be greater than or equal to VaR
        assert cvar >= var
    
    def test_calculate_max_drawdown_with_empty_data(self, risk_manager):
        """Test max drawdown calculation with insufficient data"""
        prices = np.array([100])  # Need at least 2 points
        max_dd = risk_manager.calculate_max_drawdown(prices)
        assert max_dd == 0
    
    def test_calculate_max_drawdown(self, risk_manager):
        """Test maximum drawdown calculation"""
        # Create a price series with a known drawdown
        prices = np.array([100, 110, 105, 95, 90, 100, 110])
        
        # Calculate max drawdown
        max_dd = risk_manager.calculate_max_drawdown(prices)
        
        # The max drawdown should be (110-90)/110 = 18.18%
        expected_drawdown = (110 - 90) / 110
        assert abs(max_dd - expected_drawdown) < 0.0001
    
    def test_calculate_correlation_with_invalid_data(self, risk_manager):
        """Test correlation calculation with invalid data"""
        # Different length arrays
        returns_a = np.array([0.01, -0.02, 0.03])
        returns_b = np.array([0.02, -0.01])
        correlation = risk_manager.calculate_correlation(returns_a, returns_b)
        assert correlation == 0
        
        # Empty arrays
        returns_a = np.array([])
        returns_b = np.array([])
        correlation = risk_manager.calculate_correlation(returns_a, returns_b)
        assert correlation == 0
    
    def test_calculate_correlation(self, risk_manager):
        """Test correlation calculation"""
        # Create return series for two assets
        returns_a = np.array([0.01, -0.02, 0.03, -0.01, 0.02])
        returns_b = np.array([0.02, -0.01, 0.02, -0.02, 0.01])
        
        # Calculate correlation
        correlation = risk_manager.calculate_correlation(returns_a, returns_b)
        
        # Correlation should be between -1 and 1
        assert -1.0 <= correlation <= 1.0
        
        # For perfectly correlated series
        returns_a = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
        returns_b = np.array([0.02, 0.04, 0.06, 0.08, 0.10])  # 2 * returns_a
        correlation = risk_manager.calculate_correlation(returns_a, returns_b)
        assert abs(correlation - 1.0) < 0.0001
        
        # For perfectly anti-correlated series
        returns_a = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
        returns_b = np.array([-0.01, -0.02, -0.03, -0.04, -0.05])  # -1 * returns_a
        correlation = risk_manager.calculate_correlation(returns_a, returns_b)
        assert abs(correlation + 1.0) < 0.0001
    
    def test_check_circuit_breaker_with_zero_peak(self, risk_manager):
        """Test circuit breaker with zero peak value"""
        result = risk_manager.check_circuit_breaker(current_value=90000, peak_value=0)
        assert result is False
    
    def test_check_circuit_breaker_no_trigger(self, risk_manager):
        """Test circuit breaker when drawdown is below threshold"""
        # 5% drawdown, below 10% threshold
        result = risk_manager.check_circuit_breaker(current_value=95000, peak_value=100000)
        assert result is False
    
    def test_check_circuit_breaker_trigger(self, risk_manager):
        """Test circuit breaker when drawdown exceeds threshold"""
        # 15% drawdown, above 10% threshold
        result = risk_manager.check_circuit_breaker(current_value=85000, peak_value=100000)
        assert result is True