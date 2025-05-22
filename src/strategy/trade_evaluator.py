"""
Trade evaluation module for the Grekko trading platform.

This module provides tools to evaluate potential trades for profitability,
risk, and alignment with current market conditions and strategies before execution.
"""
import logging
import numpy as np
from typing import Dict, Any, Optional, Union, Tuple, List
from enum import Enum
from datetime import datetime
from ..utils.logger import get_logger

class SignalStrength(Enum):
    """Signal strength classifications for trade signals."""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    WEAK_BUY = "weak_buy"
    NEUTRAL = "neutral"
    WEAK_SELL = "weak_sell"
    SELL = "sell"
    STRONG_SELL = "strong_sell"

class SignalType(Enum):
    """Types of trading signals supported by the platform."""
    MOMENTUM = "momentum"
    TREND = "trend"
    REVERSAL = "reversal"
    BREAKOUT = "breakout"
    SUPPORT_RESISTANCE = "support_resistance"
    PATTERN = "pattern"
    SENTIMENT = "sentiment"
    FUNDAMENTAL = "fundamental"
    ARBITRAGE = "arbitrage"

class TradeEvaluator:
    """
    Evaluates potential trades based on multiple factors.
    
    This class analyzes trading signals and market conditions to determine
    whether a trade should be executed, and calculates expected profitability,
    risk, and other metrics to help make informed trading decisions.
    
    Attributes:
        min_signal_strength (float): Minimum signal strength to consider a trade (0-1)
        min_risk_reward_ratio (float): Minimum reward/risk ratio to consider a trade
        max_correlation (float): Maximum correlation with existing positions
        consider_market_regime (bool): Whether to consider overall market regime
        logger (logging.Logger): Logger for trade evaluation events
    """
    
    def __init__(self, 
                 min_signal_strength: float = 0.6,
                 min_risk_reward_ratio: float = 1.5,
                 max_correlation: float = 0.7,
                 consider_market_regime: bool = True):
        """
        Initialize the trade evaluator.
        
        Args:
            min_signal_strength (float): Minimum signal strength (0-1)
            min_risk_reward_ratio (float): Minimum reward/risk ratio
            max_correlation (float): Maximum correlation with existing positions
            consider_market_regime (bool): Whether to consider market regime
        """
        self.min_signal_strength = min_signal_strength
        self.min_risk_reward_ratio = min_risk_reward_ratio
        self.max_correlation = max_correlation
        self.consider_market_regime = consider_market_regime
        
        self.logger = get_logger('trade_evaluator')
        self.logger.info(f"Trade evaluator initialized with min signal strength: {min_signal_strength}")
    
    def evaluate_trade(self, 
                      signal: Dict[str, Any],
                      market_data: Dict[str, Any],
                      existing_positions: Optional[List[Dict[str, Any]]] = None,
                      market_regime: Optional[str] = None) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Evaluate a potential trade based on signal and market conditions.
        
        Args:
            signal (Dict[str, Any]): Trading signal including type, direction, strength
            market_data (Dict[str, Any]): Current market data for the asset
            existing_positions (Optional[List[Dict[str, Any]]]): Currently open positions
            market_regime (Optional[str]): Current market regime classification
            
        Returns:
            Tuple[bool, float, Dict[str, Any]]: (should_trade, confidence, metadata)
        """
        # Initialize evaluation metadata
        evaluation = {
            "timestamp": datetime.now().isoformat(),
            "symbol": signal.get("symbol"),
            "signal_type": signal.get("type"),
            "signal_direction": signal.get("direction"),
            "signal_strength": signal.get("strength", 0.0),
            "checks": [],
            "risk_reward_ratio": 0.0,
            "confidence": 0.0,
            "market_factors": {}
        }
        
        # 1. Check signal strength
        signal_strength = signal.get("strength", 0.0)
        signal_check_passed = signal_strength >= self.min_signal_strength
        evaluation["checks"].append({
            "name": "signal_strength",
            "passed": signal_check_passed,
            "threshold": self.min_signal_strength,
            "value": signal_strength
        })
        
        if not signal_check_passed:
            self.logger.info(f"Signal strength check failed: {signal_strength} < {self.min_signal_strength}")
            return False, 0.0, evaluation
        
        # 2. Calculate and check risk-reward ratio
        risk_reward_ratio = self._calculate_risk_reward_ratio(signal, market_data)
        evaluation["risk_reward_ratio"] = risk_reward_ratio
        
        risk_reward_check_passed = risk_reward_ratio >= self.min_risk_reward_ratio
        evaluation["checks"].append({
            "name": "risk_reward_ratio",
            "passed": risk_reward_check_passed,
            "threshold": self.min_risk_reward_ratio,
            "value": risk_reward_ratio
        })
        
        if not risk_reward_check_passed:
            self.logger.info(f"Risk-reward check failed: {risk_reward_ratio} < {self.min_risk_reward_ratio}")
            return False, 0.0, evaluation
        
        # 3. Check correlation with existing positions if provided
        correlation_check_passed = True
        if existing_positions:
            # Calculate position correlation
            correlation = self._calculate_position_correlation(signal, existing_positions)
            correlation_check_passed = correlation <= self.max_correlation
            
            evaluation["checks"].append({
                "name": "portfolio_correlation",
                "passed": correlation_check_passed,
                "threshold": self.max_correlation,
                "value": correlation
            })
            
            if not correlation_check_passed:
                self.logger.info(f"Correlation check failed: {correlation} > {self.max_correlation}")
                return False, 0.0, evaluation
        
        # 4. Check market regime compatibility if enabled and provided
        regime_check_passed = True
        if self.consider_market_regime and market_regime:
            # Check if signal is compatible with current market regime
            regime_compatibility = self._check_regime_compatibility(signal, market_regime)
            regime_check_passed = regime_compatibility >= 0.5
            
            evaluation["checks"].append({
                "name": "market_regime_compatibility",
                "passed": regime_check_passed,
                "value": regime_compatibility,
                "regime": market_regime
            })
            
            if not regime_check_passed:
                self.logger.info(f"Market regime check failed: {regime_compatibility} < 0.5 for {market_regime}")
                return False, 0.0, evaluation
        
        # 5. Calculate overall confidence score
        confidence = self._calculate_confidence(evaluation)
        evaluation["confidence"] = confidence
        
        # 6. Make final decision
        should_trade = all(check["passed"] for check in evaluation["checks"])
        
        # 7. Add market factors analysis
        evaluation["market_factors"] = self._analyze_market_factors(market_data)
        
        # Log evaluation result
        self.logger.info(
            f"Trade evaluation for {signal.get('symbol')}: "
            f"{'ACCEPTED' if should_trade else 'REJECTED'} with confidence {confidence:.2f}"
        )
        
        return should_trade, confidence, evaluation
    
    def _calculate_risk_reward_ratio(self, signal: Dict[str, Any], 
                                    market_data: Dict[str, Any]) -> float:
        """Calculate expected risk-reward ratio for the trade."""
        # Extract target and stop levels from signal if provided
        target_price = signal.get("target_price")
        stop_price = signal.get("stop_price")
        current_price = market_data.get("last", 0)
        
        # If target or stop not provided, use default percentages based on signal type
        if not target_price or not stop_price or not current_price:
            # Default values based on signal type
            if signal.get("type") == SignalType.MOMENTUM.value:
                reward_pct = 0.05  # 5% target for momentum
                risk_pct = 0.02    # 2% stop for momentum
            elif signal.get("type") == SignalType.REVERSAL.value:
                reward_pct = 0.03  # 3% target for reversal
                risk_pct = 0.015   # 1.5% stop for reversal
            else:
                reward_pct = 0.04  # 4% default target
                risk_pct = 0.02    # 2% default stop
            
            direction = 1 if signal.get("direction", "").lower() in ["buy", "long"] else -1
            
            # Calculate target and stop based on percentages
            target_price = current_price * (1 + direction * reward_pct)
            stop_price = current_price * (1 - direction * risk_pct)
        
        # Calculate potential reward and risk
        direction = 1 if signal.get("direction", "").lower() in ["buy", "long"] else -1
        potential_reward = abs(target_price - current_price)
        potential_risk = abs(current_price - stop_price)
        
        # Calculate ratio
        if potential_risk > 0:
            ratio = potential_reward / potential_risk
        else:
            ratio = 0.0
            
        return ratio
    
    def _calculate_position_correlation(self, signal: Dict[str, Any], 
                                       positions: List[Dict[str, Any]]) -> float:
        """Calculate correlation of new position with existing portfolio."""
        # Simple correlation estimation based on asset type/sector
        # This is a placeholder for a more sophisticated correlation analysis
        
        new_symbol = signal.get("symbol", "")
        new_base = new_symbol.split('/')[0] if '/' in new_symbol else new_symbol
        
        # Count positions with the same base asset
        same_base_count = sum(1 for pos in positions if pos.get("symbol", "").startswith(new_base))
        
        # Count positions in the same sector
        sector = signal.get("sector", "unknown")
        same_sector_count = sum(1 for pos in positions if pos.get("sector") == sector)
        
        # Simple correlation heuristic
        if len(positions) == 0:
            return 0.0
            
        base_weight = 0.7 if same_base_count > 0 else 0.0
        sector_weight = 0.5 if same_sector_count > 0 else 0.0
        
        correlation = max(base_weight, sector_weight)
        return correlation
    
    def _check_regime_compatibility(self, signal: Dict[str, Any], 
                                   market_regime: str) -> float:
        """Check if the signal is compatible with the current market regime."""
        # Define compatibility matrix for different signals and regimes
        compatibility_matrix = {
            SignalType.MOMENTUM.value: {
                "bull": 0.9,
                "bear": 0.3,
                "ranging": 0.5,
                "volatile": 0.4
            },
            SignalType.TREND.value: {
                "bull": 0.8,
                "bear": 0.8,
                "ranging": 0.2,
                "volatile": 0.4
            },
            SignalType.REVERSAL.value: {
                "bull": 0.3,
                "bear": 0.3,
                "ranging": 0.8,
                "volatile": 0.6
            },
            SignalType.BREAKOUT.value: {
                "bull": 0.7,
                "bear": 0.6,
                "ranging": 0.8,
                "volatile": 0.7
            },
            SignalType.ARBITRAGE.value: {
                "bull": 0.7,
                "bear": 0.7,
                "ranging": 0.7,
                "volatile": 0.7  # Arbitrage works in any regime
            }
        }
        
        # Get signal type and lower case market regime
        signal_type = signal.get("type", "unknown")
        market_regime = market_regime.lower()
        
        # Get compatibility from matrix or use default
        if signal_type in compatibility_matrix:
            return compatibility_matrix[signal_type].get(market_regime, 0.5)
        else:
            return 0.5  # Default compatibility
    
    def _calculate_confidence(self, evaluation: Dict[str, Any]) -> float:
        """Calculate overall confidence score for the trade."""
        # Define weights for different factors
        weights = {
            "signal_strength": 0.4,
            "risk_reward_ratio": 0.3,
            "portfolio_correlation": 0.15,
            "market_regime_compatibility": 0.15
        }
        
        confidence = 0.0
        weight_sum = 0.0
        
        # Calculate weighted average of factors
        for check in evaluation["checks"]:
            check_name = check["name"]
            if check_name in weights:
                value = check["value"]
                
                # Normalize value for confidence calculation
                if check_name == "signal_strength":
                    # Already in 0-1 range
                    normalized_value = value
                elif check_name == "risk_reward_ratio":
                    # Convert R:R ratio to 0-1 score (2.0 ’ 0.8, 3.0 ’ 0.9, etc.)
                    normalized_value = min(0.95, 0.5 + (value - 1) * 0.2)
                elif check_name == "portfolio_correlation":
                    # Invert correlation (lower is better)
                    normalized_value = 1.0 - value
                elif check_name == "market_regime_compatibility":
                    # Already in 0-1 range
                    normalized_value = value
                else:
                    normalized_value = 0.5  # Default
                
                # Add to weighted average
                confidence += weights[check_name] * normalized_value
                weight_sum += weights[check_name]
        
        # Normalize by actual weights used
        if weight_sum > 0:
            confidence /= weight_sum
        
        return confidence
    
    def _analyze_market_factors(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze additional market factors that may affect the trade."""
        factors = {}
        
        # Extract relevant market data if available
        if "volume" in market_data:
            factors["volume_analysis"] = {
                "value": market_data["volume"],
                "above_average": market_data.get("volume_avg_ratio", 1.0) > 1.2
            }
            
        if "bid" in market_data and "ask" in market_data:
            spread = market_data["ask"] - market_data["bid"]
            spread_pct = spread / market_data["bid"] if market_data["bid"] > 0 else 0
            
            factors["spread_analysis"] = {
                "absolute": spread,
                "percentage": spread_pct,
                "is_high": spread_pct > 0.002  # Flag high spreads (> 0.2%)
            }
            
        # Check for any liquidity warnings
        if "liquidity" in market_data:
            factors["liquidity_analysis"] = {
                "value": market_data["liquidity"],
                "is_low": market_data.get("liquidity_status") == "low"
            }
            
        return factors