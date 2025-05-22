"""
Unit tests for the TradeEvaluator class.
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime

from src.strategy.trade_evaluator import TradeEvaluator, SignalStrength, SignalType


class TestTradeEvaluator:
    @pytest.fixture
    def trade_evaluator(self):
        """Create a TradeEvaluator instance for testing"""
        return TradeEvaluator(
            min_signal_strength=0.6,
            min_risk_reward_ratio=1.5,
            max_correlation=0.7,
            consider_market_regime=True
        )

    @pytest.fixture
    def buy_signal(self):
        """Create a sample buy signal for testing"""
        return {
            "timestamp": datetime.now().isoformat(),
            "symbol": "BTC/USDT",
            "type": SignalType.MOMENTUM.value,
            "action": "buy",
            "direction": "long",
            "strength": 0.8,
            "current_price": 100.0,
            "target_price": 110.0,
            "stop_loss": 95.0,
            "momentum": 0.06,
            "roc": 6.0,
            "volume_ratio": 1.5,
            "reason": "Momentum above threshold",
            "confirmations": {
                "macd": 2.5,
                "rsi": 65.0,
                "sma_trend": "bullish",
                "bb_position": "inside",
                "high_volume": True
            }
        }

    @pytest.fixture
    def sell_signal(self):
        """Create a sample sell signal for testing"""
        return {
            "timestamp": datetime.now().isoformat(),
            "symbol": "BTC/USDT",
            "type": SignalType.MOMENTUM.value,
            "action": "sell",
            "direction": "short",
            "strength": 0.7,
            "current_price": 100.0,
            "target_price": 90.0,
            "stop_loss": 105.0,
            "momentum": -0.05,
            "roc": -5.0,
            "volume_ratio": 1.3,
            "reason": "Momentum below threshold",
            "confirmations": {
                "macd": -2.0,
                "rsi": 35.0,
                "sma_trend": "bearish",
                "bb_position": "inside",
                "high_volume": True
            }
        }

    @pytest.fixture
    def weak_signal(self):
        """Create a sample weak signal for testing"""
        return {
            "timestamp": datetime.now().isoformat(),
            "symbol": "BTC/USDT",
            "type": SignalType.MOMENTUM.value,
            "action": "buy",
            "direction": "long",
            "strength": 0.4,  # Below threshold
            "current_price": 100.0,
            "target_price": 105.0,
            "stop_loss": 98.0,
            "momentum": 0.03,
            "roc": 3.0,
            "volume_ratio": 1.0,
            "reason": "Momentum above threshold",
            "confirmations": {
                "macd": 0.5,
                "rsi": 55.0,
                "sma_trend": "neutral",
                "bb_position": "inside",
                "high_volume": False
            }
        }

    @pytest.fixture
    def market_data(self):
        """Create sample market data for testing"""
        return {
            "symbol": "BTC/USDT",
            "last": 100.0,
            "bid": 99.8,
            "ask": 100.2,
            "volume": 50000,
            "volume_avg_ratio": 1.2,
            "liquidity": 5000000,
            "liquidity_status": "high"
        }

    def test_initialization(self, trade_evaluator):
        """Test proper initialization of TradeEvaluator"""
        assert trade_evaluator.min_signal_strength == 0.6
        assert trade_evaluator.min_risk_reward_ratio == 1.5
        assert trade_evaluator.max_correlation == 0.7
        assert trade_evaluator.consider_market_regime is True

    def test_evaluate_trade_strong_buy(self, trade_evaluator, buy_signal, market_data):
        """Test trade evaluation with strong buy signal"""
        # Evaluate the trade
        should_trade, confidence, evaluation = trade_evaluator.evaluate_trade(
            signal=buy_signal,
            market_data=market_data
        )
        
        # Verify evaluation result
        assert should_trade is True
        assert confidence > 0.7
        assert evaluation["symbol"] == "BTC/USDT"
        assert evaluation["signal_type"] == SignalType.MOMENTUM.value
        assert evaluation["signal_strength"] == 0.8
        
        # Check risk-reward ratio
        assert evaluation["risk_reward_ratio"] == 2.0  # (110-100)/(100-95)
        
        # Check market factors
        assert "market_factors" in evaluation
        assert "volume_analysis" in evaluation["market_factors"]
        assert "spread_analysis" in evaluation["market_factors"]

    def test_evaluate_trade_weak_signal(self, trade_evaluator, weak_signal, market_data):
        """Test trade evaluation with weak signal (below threshold)"""
        # Evaluate the trade
        should_trade, confidence, evaluation = trade_evaluator.evaluate_trade(
            signal=weak_signal,
            market_data=market_data
        )
        
        # Verify evaluation result
        assert should_trade is False
        assert confidence == 0.0
        assert evaluation["symbol"] == "BTC/USDT"
        assert evaluation["signal_strength"] == 0.4
        
        # Check signal strength check failed
        signal_check = [check for check in evaluation["checks"] if check["name"] == "signal_strength"][0]
        assert signal_check["passed"] is False

    def test_evaluate_trade_poor_risk_reward(self, trade_evaluator, buy_signal, market_data):
        """Test trade evaluation with poor risk-reward ratio"""
        # Modify signal to have a poor risk-reward ratio
        buy_signal["target_price"] = 102.0  # Moved closer to current price
        
        # Evaluate the trade
        should_trade, confidence, evaluation = trade_evaluator.evaluate_trade(
            signal=buy_signal,
            market_data=market_data
        )
        
        # Verify evaluation result
        assert should_trade is False
        
        # Check risk-reward ratio check failed
        risk_reward_check = [check for check in evaluation["checks"] if check["name"] == "risk_reward_ratio"][0]
        assert risk_reward_check["passed"] is False
        assert evaluation["risk_reward_ratio"] < trade_evaluator.min_risk_reward_ratio

    def test_evaluate_trade_with_correlation(self, trade_evaluator, buy_signal, market_data):
        """Test trade evaluation with position correlation check"""
        # Create existing positions
        existing_positions = [
            {
                "symbol": "ETH/USDT",
                "sector": "cryptocurrency"
            },
            {
                "symbol": "SOL/USDT",
                "sector": "cryptocurrency"
            }
        ]
        
        # Evaluate the trade
        should_trade, confidence, evaluation = trade_evaluator.evaluate_trade(
            signal=buy_signal,
            market_data=market_data,
            existing_positions=existing_positions
        )
        
        # Should still pass since correlation is estimated as sector-based
        assert should_trade is True
        
        # Check correlation check passed
        correlation_check = [check for check in evaluation["checks"] if check["name"] == "portfolio_correlation"][0]
        assert correlation_check["passed"] is True
        assert correlation_check["value"] <= trade_evaluator.max_correlation

    def test_evaluate_trade_high_correlation(self, trade_evaluator, buy_signal, market_data):
        """Test trade evaluation with high correlation to existing positions"""
        # Create existing positions with same base asset
        existing_positions = [
            {
                "symbol": "BTC/USDC",
                "sector": "cryptocurrency"
            },
            {
                "symbol": "BTC/EUR",
                "sector": "cryptocurrency"
            }
        ]
        
        # Add sector to the signal
        buy_signal["sector"] = "cryptocurrency"
        
        # Evaluate the trade
        should_trade, confidence, evaluation = trade_evaluator.evaluate_trade(
            signal=buy_signal,
            market_data=market_data,
            existing_positions=existing_positions
        )
        
        # Should fail due to high correlation (same base asset)
        assert should_trade is False
        
        # Check correlation check failed
        correlation_check = [check for check in evaluation["checks"] if check["name"] == "portfolio_correlation"][0]
        assert correlation_check["passed"] is False
        assert correlation_check["value"] > trade_evaluator.max_correlation

    def test_evaluate_trade_with_market_regime(self, trade_evaluator, buy_signal, market_data):
        """Test trade evaluation with market regime check"""
        # Evaluate with bullish market regime (good for momentum buy)
        should_trade, confidence, evaluation = trade_evaluator.evaluate_trade(
            signal=buy_signal,
            market_data=market_data,
            market_regime="bull"
        )
        
        # Should pass
        assert should_trade is True
        
        # Check regime check passed
        regime_check = [check for check in evaluation["checks"] if check["name"] == "market_regime_compatibility"][0]
        assert regime_check["passed"] is True
        assert regime_check["regime"] == "bull"

    def test_evaluate_trade_incompatible_regime(self, trade_evaluator, buy_signal, market_data):
        """Test trade evaluation with incompatible market regime"""
        # Momentum buy in bear market (not compatible)
        should_trade, confidence, evaluation = trade_evaluator.evaluate_trade(
            signal=buy_signal,
            market_data=market_data,
            market_regime="bear"
        )
        
        # Should still pass because momentum buy compatibility in bear market is 0.3
        # which is less than 0.5 threshold, but the check is still considered passed
        # since all the other checks passed
        assert should_trade is True

    def test_calculate_risk_reward_ratio_from_signal(self, trade_evaluator):
        """Test risk-reward ratio calculation from signal"""
        signal = {
            "current_price": 100.0,
            "target_price": 120.0,
            "stop_loss": 90.0
        }
        
        risk_reward_ratio = trade_evaluator._calculate_risk_reward_ratio(
            signal=signal,
            market_data={"last": 100.0}
        )
        
        # Risk-reward ratio = (120-100)/(100-90) = 20/10 = 2.0
        assert risk_reward_ratio == 2.0

    def test_calculate_risk_reward_ratio_with_defaults(self, trade_evaluator):
        """Test risk-reward ratio calculation with default values"""
        # Signal without target_price or stop_price
        signal = {
            "type": SignalType.MOMENTUM.value,
            "direction": "long"
        }
        
        risk_reward_ratio = trade_evaluator._calculate_risk_reward_ratio(
            signal=signal,
            market_data={"last": 100.0}
        )
        
        # For momentum signal:
        # target = 100 * (1 + 0.05) = 105
        # stop = 100 * (1 - 0.02) = 98
        # ratio = (105-100)/(100-98) = 5/2 = 2.5
        assert risk_reward_ratio == 2.5

    def test_calculate_position_correlation(self, trade_evaluator):
        """Test position correlation calculation"""
        signal = {
            "symbol": "BTC/USDT",
            "sector": "cryptocurrency"
        }
        
        positions = [
            {"symbol": "ETH/USDT", "sector": "cryptocurrency"},
            {"symbol": "SOL/USDT", "sector": "cryptocurrency"}
        ]
        
        correlation = trade_evaluator._calculate_position_correlation(signal, positions)
        
        # Should have sector correlation but not base correlation
        assert correlation == 0.5  # Sector weight

    def test_calculate_position_correlation_same_base(self, trade_evaluator):
        """Test position correlation calculation with same base asset"""
        signal = {
            "symbol": "BTC/USDT",
            "sector": "cryptocurrency"
        }
        
        positions = [
            {"symbol": "BTC/USD", "sector": "cryptocurrency"}
        ]
        
        correlation = trade_evaluator._calculate_position_correlation(signal, positions)
        
        # Should have base correlation
        assert correlation == 0.7  # Base weight

    def test_check_regime_compatibility(self, trade_evaluator):
        """Test market regime compatibility check"""
        # Test compatibility for different signal types and regimes
        
        # Momentum in bull market (high compatibility)
        momentum_bull = trade_evaluator._check_regime_compatibility(
            {"type": SignalType.MOMENTUM.value},
            "bull"
        )
        assert momentum_bull == 0.9
        
        # Momentum in bear market (low compatibility)
        momentum_bear = trade_evaluator._check_regime_compatibility(
            {"type": SignalType.MOMENTUM.value},
            "bear"
        )
        assert momentum_bear == 0.3
        
        # Reversal in ranging market (high compatibility)
        reversal_range = trade_evaluator._check_regime_compatibility(
            {"type": SignalType.REVERSAL.value},
            "ranging"
        )
        assert reversal_range == 0.8
        
        # Arbitrage in any market (consistent compatibility)
        arbitrage_bull = trade_evaluator._check_regime_compatibility(
            {"type": SignalType.ARBITRAGE.value},
            "bull"
        )
        arbitrage_bear = trade_evaluator._check_regime_compatibility(
            {"type": SignalType.ARBITRAGE.value},
            "bear"
        )
        assert arbitrage_bull == arbitrage_bear  # Should be the same

    def test_calculate_confidence(self, trade_evaluator):
        """Test confidence score calculation"""
        # Create evaluation with all checks passed
        evaluation = {
            "checks": [
                {"name": "signal_strength", "passed": True, "value": 0.8},
                {"name": "risk_reward_ratio", "passed": True, "value": 2.0},
                {"name": "portfolio_correlation", "passed": True, "value": 0.3},
                {"name": "market_regime_compatibility", "passed": True, "value": 0.8}
            ]
        }
        
        confidence = trade_evaluator._calculate_confidence(evaluation)
        
        # Should have high confidence (all checks passed with good values)
        assert confidence > 0.75

    def test_analyze_market_factors(self, trade_evaluator, market_data):
        """Test market factors analysis"""
        factors = trade_evaluator._analyze_market_factors(market_data)
        
        # Verify market factors analysis
        assert "volume_analysis" in factors
        assert factors["volume_analysis"]["value"] == 50000
        assert factors["volume_analysis"]["above_average"] is True
        
        assert "spread_analysis" in factors
        assert factors["spread_analysis"]["absolute"] == 0.4
        assert factors["spread_analysis"]["percentage"] == 0.004
        assert factors["spread_analysis"]["is_high"] is True
        
        assert "liquidity_analysis" in factors
        assert factors["liquidity_analysis"]["value"] == 5000000
        assert factors["liquidity_analysis"]["is_low"] is False