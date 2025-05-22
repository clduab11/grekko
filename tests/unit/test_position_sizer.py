"""
Unit tests for the PositionSizer class.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.strategy.position_sizer import PositionSizer, PositionSizingMethod
from src.risk_management.risk_manager import RiskManager


class TestPositionSizer:
    @pytest.fixture
    def mock_risk_manager(self):
        """Create a mock risk manager for testing"""
        risk_manager = MagicMock(spec=RiskManager)
        risk_manager.capital = 10000.0
        risk_manager.get_current_exposure.return_value = 2000.0
        return risk_manager

    @pytest.fixture
    def position_sizer(self, mock_risk_manager):
        """Create a PositionSizer instance for testing"""
        return PositionSizer(
            risk_manager=mock_risk_manager,
            default_method=PositionSizingMethod.RISK_BASED,
            max_position_size_pct=0.2,
            min_position_size_quote=10.0,
            optimal_positions_count=5
        )

    def test_initialization(self, position_sizer, mock_risk_manager):
        """Test proper initialization of PositionSizer"""
        assert position_sizer.risk_manager == mock_risk_manager
        assert position_sizer.default_method == PositionSizingMethod.RISK_BASED
        assert position_sizer.max_position_size_pct == 0.2
        assert position_sizer.min_position_size_quote == 10.0
        assert position_sizer.optimal_positions_count == 5

    def test_initialization_with_string_method(self, mock_risk_manager):
        """Test initialization with string method name"""
        position_sizer = PositionSizer(
            risk_manager=mock_risk_manager,
            default_method="percent_of_capital"
        )
        assert position_sizer.default_method == PositionSizingMethod.PERCENT_OF_CAPITAL

    def test_fixed_size_method(self, position_sizer):
        """Test fixed size position sizing method"""
        # Call calculate_position_size with FIXED method
        position_size, metadata = position_sizer.calculate_position_size(
            method=PositionSizingMethod.FIXED
        )
        
        # Verify position size and metadata
        assert position_size == 1000.0  # 10% of 10000
        assert metadata["method"] == PositionSizingMethod.FIXED.value
        assert metadata["capital"] == 10000.0
        assert metadata["percentage"] == 0.1

    def test_percent_of_capital_method(self, position_sizer):
        """Test percent of capital position sizing method"""
        # Call calculate_position_size with PERCENT_OF_CAPITAL method
        position_size, metadata = position_sizer.calculate_position_size(
            method=PositionSizingMethod.PERCENT_OF_CAPITAL
        )
        
        # Verify position size and metadata
        # Capital / optimal_positions_count = 10000 / 5 = 2000
        assert position_size == 2000.0
        assert metadata["method"] == PositionSizingMethod.PERCENT_OF_CAPITAL.value
        assert metadata["capital"] == 10000.0
        assert metadata["current_exposure"] == 2000.0
        assert metadata["optimal_positions"] == 5
        assert "percentage_used" in metadata

    def test_risk_based_method(self, position_sizer):
        """Test risk-based position sizing method"""
        # Prepare ticker data with price
        ticker_data = {"last": 100.0}
        
        # Call calculate_position_size with RISK_BASED method
        position_size, metadata = position_sizer.calculate_position_size(
            method=PositionSizingMethod.RISK_BASED,
            ticker_data=ticker_data,
            risk_per_trade_pct=0.01,
            stop_loss_pct=0.05
        )
        
        # Verify position size and metadata
        # risk_amount = 10000 * 0.01 = 100
        # position_size = 100 / 0.05 = 2000
        assert position_size == 2000.0
        assert metadata["method"] == PositionSizingMethod.RISK_BASED.value
        assert metadata["capital"] == 10000.0
        assert metadata["risk_percentage"] == 0.01
        assert metadata["risk_amount"] == 100.0
        assert metadata["stop_loss_percentage"] == 0.05
        assert metadata["position_size_base"] == 20.0  # 2000 / 100

    def test_risk_based_with_zero_stop_loss(self, position_sizer):
        """Test risk-based sizing with zero stop loss"""
        # Prepare ticker data with price
        ticker_data = {"last": 100.0}
        
        # Call calculate_position_size with RISK_BASED method but zero stop loss
        position_size, metadata = position_sizer.calculate_position_size(
            method=PositionSizingMethod.RISK_BASED,
            ticker_data=ticker_data,
            risk_per_trade_pct=0.01,
            stop_loss_pct=0.0  # Zero stop loss
        )
        
        # Should fall back to default 5% of capital
        assert position_size == 500.0  # 5% of 10000
        assert metadata["method"] == PositionSizingMethod.RISK_BASED.value

    def test_max_position_size_constraint(self, position_sizer):
        """Test max position size constraint"""
        # Prepare ticker data with low price to generate large position
        ticker_data = {"last": 10.0}
        
        # Call calculate_position_size with RISK_BASED method and tiny stop loss
        # to generate a very large position that should be constrained
        position_size, metadata = position_sizer.calculate_position_size(
            method=PositionSizingMethod.RISK_BASED,
            ticker_data=ticker_data,
            risk_per_trade_pct=0.05,
            stop_loss_pct=0.01  # Very small stop loss for large position
        )
        
        # Position should be capped at 20% of capital (2000)
        assert position_size == 2000.0  # max_position_size_pct * capital
        assert metadata["method"] == PositionSizingMethod.RISK_BASED.value

    def test_min_position_size_constraint(self, position_sizer):
        """Test min position size constraint"""
        # Prepare ticker data
        ticker_data = {"last": 100.0}
        
        # Call calculate_position_size with RISK_BASED method and large stop loss
        # to generate a very small position that should be constrained
        position_size, metadata = position_sizer.calculate_position_size(
            method=PositionSizingMethod.RISK_BASED,
            ticker_data=ticker_data,
            risk_per_trade_pct=0.001,  # Very small risk
            stop_loss_pct=0.2  # Large stop loss for small position
        )
        
        # Position should be at least the minimum (10)
        assert position_size == 10.0  # min_position_size_quote
        assert metadata["method"] == PositionSizingMethod.RISK_BASED.value

    def test_kelly_criterion_method(self, position_sizer):
        """Test Kelly Criterion position sizing method"""
        # Call calculate_position_size with KELLY method
        position_size, metadata = position_sizer.calculate_position_size(
            method=PositionSizingMethod.KELLY,
            win_rate=0.6,  # 60% win rate
            reward_risk_ratio=2.0  # 2:1 reward to risk
        )
        
        # Calculate expected Kelly percentage: (bp - q) / b
        # where b = 2.0, p = 0.6, q = 0.4
        # Kelly % = (2.0 * 0.6 - 0.4) / 2.0 = 0.4
        # Half Kelly = 0.2
        # Position size = 10000 * 0.2 = 2000
        assert position_size == 2000.0
        assert metadata["method"] == PositionSizingMethod.KELLY.value
        assert metadata["win_rate"] == 0.6
        assert metadata["reward_risk_ratio"] == 2.0
        assert abs(metadata["kelly_percentage"] - 0.4) < 0.0001
        assert abs(metadata["half_kelly_percentage"] - 0.2) < 0.0001

    def test_kelly_criterion_negative_expectancy(self, position_sizer):
        """Test Kelly Criterion with negative expectancy"""
        # Call calculate_position_size with KELLY method with bad parameters
        position_size, metadata = position_sizer.calculate_position_size(
            method=PositionSizingMethod.KELLY,
            win_rate=0.4,  # 40% win rate (low)
            reward_risk_ratio=1.0  # 1:1 reward to risk (poor)
        )
        
        # This has negative expectancy, so Kelly would be negative
        # Should return 0 position size
        assert position_size == 0.0
        assert metadata["method"] == PositionSizingMethod.KELLY.value
        assert "error" in metadata

    def test_volatility_adjusted_method(self, position_sizer):
        """Test volatility-adjusted position sizing method"""
        # Call calculate_position_size with VOLATILITY_ADJUSTED method
        position_size, metadata = position_sizer.calculate_position_size(
            method=PositionSizingMethod.VOLATILITY_ADJUSTED,
            risk_per_trade_pct=0.02,
            price_volatility=0.02  # 2% volatility
        )
        
        # Calculate expected position size
        # Base position = 10000 * 0.02 = 200
        # Volatility adjustment = 0.01 / 0.02 = 0.5
        # Final position = 200 * 0.5 = 100
        assert position_size == 100.0
        assert metadata["method"] == PositionSizingMethod.VOLATILITY_ADJUSTED.value
        assert metadata["volatility"] == 0.02
        assert abs(metadata["volatility_scalar"] - 0.5) < 0.0001

    def test_volatility_adjusted_zero_volatility(self, position_sizer):
        """Test volatility-adjusted with zero volatility"""
        # Call calculate_position_size with VOLATILITY_ADJUSTED method and zero volatility
        position_size, metadata = position_sizer.calculate_position_size(
            method=PositionSizingMethod.VOLATILITY_ADJUSTED,
            risk_per_trade_pct=0.02,
            price_volatility=0.0  # Zero volatility
        )
        
        # With zero volatility, scalar should be 1.0
        assert position_size == 200.0  # 10000 * 0.02 * 1.0
        assert metadata["method"] == PositionSizingMethod.VOLATILITY_ADJUSTED.value
        assert metadata["volatility_scalar"] == 1.0

    def test_ml_optimized_fallback(self, position_sizer):
        """Test ML_OPTIMIZED method falling back to risk-based"""
        # ML_OPTIMIZED is not implemented, so should fall back to risk-based
        ticker_data = {"last": 100.0}
        
        position_size, metadata = position_sizer.calculate_position_size(
            method=PositionSizingMethod.ML_OPTIMIZED,
            ticker_data=ticker_data,
            risk_per_trade_pct=0.01,
            stop_loss_pct=0.05
        )
        
        # Should use risk-based sizing as fallback
        assert position_size == 2000.0
        assert metadata["method"] == PositionSizingMethod.RISK_BASED.value

    def test_unknown_method(self, position_sizer):
        """Test with an invalid method"""
        # Create a method that doesn't exist in the enum
        # This is a bit of a hack for testing purposes
        invalid_method = "invalid_method"
        
        with pytest.raises(ValueError):
            position_size, metadata = position_sizer.calculate_position_size(
                method=invalid_method
            )

    def test_default_method(self, position_sizer):
        """Test using the default method"""
        # Don't specify a method, should use default (RISK_BASED)
        ticker_data = {"last": 100.0}
        
        position_size, metadata = position_sizer.calculate_position_size(
            ticker_data=ticker_data,
            risk_per_trade_pct=0.01,
            stop_loss_pct=0.05
        )
        
        # Should use RISK_BASED (the default)
        assert position_size == 2000.0
        assert metadata["method"] == PositionSizingMethod.RISK_BASED.value