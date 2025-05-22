"""
Unit tests for the CircuitBreaker component.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from src.risk_management.circuit_breaker import CircuitBreaker


class TestCircuitBreaker:
    """Test suite for CircuitBreaker"""
    
    @pytest.fixture
    def circuit_breaker(self):
        """Create a CircuitBreaker instance for testing"""
        return CircuitBreaker(
            max_drawdown_pct=0.10,
            volatility_threshold=3.0,
            max_consecutive_losses=3,
            cooldown_minutes=5
        )
    
    def test_init(self, circuit_breaker):
        """Test initialization of CircuitBreaker"""
        assert circuit_breaker.max_drawdown_pct == 0.10
        assert circuit_breaker.volatility_threshold == 3.0
        assert circuit_breaker.max_consecutive_losses == 3
        assert circuit_breaker.cooldown_minutes == 5
        assert circuit_breaker.is_active is False
        assert circuit_breaker.triggered_at is None
        assert circuit_breaker.consecutive_losses == 0
        assert circuit_breaker.peak_portfolio_value == 0.0
    
    def test_update_portfolio_value(self, circuit_breaker):
        """Test updating peak portfolio value"""
        # Initial value
        circuit_breaker.update_portfolio_value(100000)
        assert circuit_breaker.peak_portfolio_value == 100000
        
        # Lower value should not update peak
        circuit_breaker.update_portfolio_value(90000)
        assert circuit_breaker.peak_portfolio_value == 100000
        
        # Higher value should update peak
        circuit_breaker.update_portfolio_value(110000)
        assert circuit_breaker.peak_portfolio_value == 110000
    
    def test_check_drawdown_with_zero_peak(self, circuit_breaker):
        """Test drawdown check with zero peak portfolio value"""
        assert circuit_breaker.check_drawdown(current_value=90000) is False
    
    def test_check_drawdown_below_threshold(self, circuit_breaker):
        """Test drawdown check below threshold"""
        # Set peak value
        circuit_breaker.peak_portfolio_value = 100000
        
        # 5% drawdown (below 10% threshold)
        assert circuit_breaker.check_drawdown(current_value=95000) is False
    
    def test_check_drawdown_above_threshold(self, circuit_breaker):
        """Test drawdown check above threshold"""
        # Set peak value
        circuit_breaker.peak_portfolio_value = 100000
        
        # 15% drawdown (above 10% threshold)
        assert circuit_breaker.check_drawdown(current_value=85000) is True
    
    def test_check_volatility_insufficient_data(self, circuit_breaker):
        """Test volatility check with insufficient data"""
        # Empty returns array
        assert circuit_breaker.check_volatility([], 0.01) is False
        
        # Single return (need at least 2)
        assert circuit_breaker.check_volatility([0.01], 0.01) is False
        
        # Zero historical std
        assert circuit_breaker.check_volatility([0.01, 0.02], 0) is False
    
    def test_check_volatility_below_threshold(self, circuit_breaker):
        """Test volatility check below threshold"""
        # Historical std: 0.01
        # Recent returns std: 0.02 (2x historical)
        recent_returns = [0.01, 0.03]  # std ~ 0.014
        historical_std = 0.007  # 2x less than recent
        
        # Volatility ratio: 2.0 (below 3.0 threshold)
        assert circuit_breaker.check_volatility(recent_returns, historical_std) is False
    
    def test_check_volatility_above_threshold(self, circuit_breaker):
        """Test volatility check above threshold"""
        # Historical std: 0.01
        # Recent returns with wide spread for high std
        recent_returns = [-0.05, 0.05]  # std = 0.07
        historical_std = 0.02
        
        # Volatility ratio: 3.5 (above 3.0 threshold)
        assert circuit_breaker.check_volatility(recent_returns, historical_std) is True
    
    def test_record_trade_result_profitable(self, circuit_breaker):
        """Test recording profitable trade"""
        # Set initial consecutive losses
        circuit_breaker.consecutive_losses = 2
        
        # Record profitable trade
        assert circuit_breaker.record_trade_result(is_profitable=True) is False
        
        # Consecutive losses should be reset
        assert circuit_breaker.consecutive_losses == 0
    
    def test_record_trade_result_losing_below_threshold(self, circuit_breaker):
        """Test recording losing trade below threshold"""
        # Set initial consecutive losses
        circuit_breaker.consecutive_losses = 1
        
        # Record losing trade
        assert circuit_breaker.record_trade_result(is_profitable=False) is False
        
        # Consecutive losses should be incremented
        assert circuit_breaker.consecutive_losses == 2
    
    def test_record_trade_result_losing_above_threshold(self, circuit_breaker):
        """Test recording losing trade above threshold"""
        # Set initial consecutive losses
        circuit_breaker.consecutive_losses = 2
        
        # Record losing trade (third consecutive)
        assert circuit_breaker.record_trade_result(is_profitable=False) is True
        
        # Consecutive losses should be incremented
        assert circuit_breaker.consecutive_losses == 3
    
    def test_trigger(self, circuit_breaker):
        """Test triggering the circuit breaker"""
        # Trigger the circuit breaker
        circuit_breaker.trigger(reason="Test trigger")
        
        # Check state
        assert circuit_breaker.is_active is True
        assert circuit_breaker.triggered_at is not None
    
    def test_check_cooldown_inactive(self, circuit_breaker):
        """Test cooldown check when circuit breaker is inactive"""
        assert circuit_breaker.check_cooldown() is True
    
    def test_check_cooldown_active_not_elapsed(self, circuit_breaker):
        """Test cooldown check when cooldown period has not elapsed"""
        # Trigger the circuit breaker
        circuit_breaker.trigger()
        
        # Check cooldown
        assert circuit_breaker.check_cooldown() is False
    
    def test_check_cooldown_active_elapsed(self, circuit_breaker):
        """Test cooldown check when cooldown period has elapsed"""
        # Trigger the circuit breaker with a time in the past
        circuit_breaker.is_active = True
        circuit_breaker.triggered_at = datetime.now() - timedelta(minutes=10)  # 10 minutes ago (beyond 5 min cooldown)
        
        # Check cooldown
        assert circuit_breaker.check_cooldown() is True
        assert circuit_breaker.is_active is False  # Should be reset
    
    def test_can_trade_while_active(self, circuit_breaker):
        """Test can_trade when circuit breaker is active"""
        # Trigger the circuit breaker
        circuit_breaker.trigger()
        
        # Check if can trade
        assert circuit_breaker.can_trade(current_value=100000) is False
    
    def test_can_trade_drawdown_trigger(self, circuit_breaker):
        """Test can_trade triggering due to drawdown"""
        # Set peak value
        circuit_breaker.peak_portfolio_value = 100000
        
        # Check with 15% drawdown (above 10% threshold)
        assert circuit_breaker.can_trade(current_value=85000) is False
        assert circuit_breaker.is_active is True
    
    def test_can_trade_volatility_trigger(self, circuit_breaker):
        """Test can_trade triggering due to volatility"""
        # Set up for volatility check
        recent_returns = [-0.05, 0.05]  # High volatility
        historical_std = 0.01
        
        # Check with high volatility
        assert circuit_breaker.can_trade(
            current_value=100000,
            recent_returns=recent_returns,
            historical_std=historical_std
        ) is False
        assert circuit_breaker.is_active is True
    
    def test_can_trade_all_clear(self, circuit_breaker):
        """Test can_trade with all conditions clear"""
        # Set peak value
        circuit_breaker.peak_portfolio_value = 100000
        
        # Normal volatility
        recent_returns = [0.01, 0.02]
        historical_std = 0.01
        
        # Check with normal conditions
        assert circuit_breaker.can_trade(
            current_value=95000,  # 5% drawdown (below threshold)
            recent_returns=recent_returns,
            historical_std=historical_std
        ) is True
        assert circuit_breaker.is_active is False
    
    def test_reset(self, circuit_breaker):
        """Test resetting the circuit breaker"""
        # Trigger the circuit breaker
        circuit_breaker.trigger()
        circuit_breaker.consecutive_losses = 2
        
        # Reset
        circuit_breaker.reset()
        
        # Check state
        assert circuit_breaker.is_active is False
        assert circuit_breaker.triggered_at is None
        assert circuit_breaker.consecutive_losses == 0