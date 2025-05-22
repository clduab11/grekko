"""
Position sizing module for the Grekko trading platform.

This module provides various position sizing algorithms to determine
the appropriate trade size based on risk parameters, market conditions,
and account balance.
"""
import logging
import math
from enum import Enum
from typing import Dict, Any, Optional, Union, Tuple, List
from ..utils.logger import get_logger
from ..risk_management.risk_manager import RiskManager

class PositionSizingMethod(Enum):
    """Position sizing methods supported by the platform."""
    FIXED = "fixed"
    PERCENT_OF_CAPITAL = "percent_of_capital"
    RISK_BASED = "risk_based"
    KELLY = "kelly_criterion"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    ML_OPTIMIZED = "ml_optimized"

class PositionSizer:
    """
    Handles position sizing for all trading strategies.
    
    This class calculates appropriate position sizes based on available capital,
    risk tolerance, and market conditions, ensuring that trades are sized
    according to the chosen risk management strategy.
    
    Attributes:
        risk_manager (RiskManager): Risk manager instance for risk calculations
        default_method (PositionSizingMethod): Default position sizing method
        max_position_size_pct (float): Maximum position size as percentage of capital
        min_position_size_quote (float): Minimum position size in quote currency
        optimal_positions_count (int): Target number of concurrent positions
        logger (logging.Logger): Logger for position sizing events
    """
    
    def __init__(self, 
                 risk_manager: RiskManager,
                 default_method: Union[str, PositionSizingMethod] = PositionSizingMethod.RISK_BASED,
                 max_position_size_pct: float = 0.2,
                 min_position_size_quote: float = 10.0,
                 optimal_positions_count: int = 5):
        """
        Initialize the position sizer.
        
        Args:
            risk_manager (RiskManager): Risk manager instance
            default_method (Union[str, PositionSizingMethod]): Default position sizing method
            max_position_size_pct (float): Maximum position size as percentage of capital
            min_position_size_quote (float): Minimum position size in quote currency
            optimal_positions_count (int): Target number of concurrent positions
        """
        self.risk_manager = risk_manager
        
        # Convert string to enum if needed
        if isinstance(default_method, str):
            self.default_method = PositionSizingMethod(default_method)
        else:
            self.default_method = default_method
            
        self.max_position_size_pct = max_position_size_pct
        self.min_position_size_quote = min_position_size_quote
        self.optimal_positions_count = optimal_positions_count
        
        self.logger = get_logger('position_sizer')
        self.logger.info(f"Position sizer initialized with {self.default_method.value} method")
        
    def calculate_position_size(self, 
                               method: Optional[Union[str, PositionSizingMethod]] = None,
                               ticker_data: Optional[Dict[str, Any]] = None,
                               risk_per_trade_pct: Optional[float] = None,
                               stop_loss_pct: Optional[float] = None,
                               win_rate: Optional[float] = None,
                               reward_risk_ratio: Optional[float] = None,
                               price_volatility: Optional[float] = None) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate position size based on the chosen method and parameters.
        
        Args:
            method (Optional[Union[str, PositionSizingMethod]]): Position sizing method
            ticker_data (Optional[Dict[str, Any]]): Current market data for the asset
            risk_per_trade_pct (Optional[float]): Risk per trade as percentage of capital
            stop_loss_pct (Optional[float]): Stop loss distance as percentage
            win_rate (Optional[float]): Historical win rate for this strategy/market
            reward_risk_ratio (Optional[float]): Expected reward to risk ratio
            price_volatility (Optional[float]): Current price volatility (std dev)
            
        Returns:
            Tuple[float, Dict[str, Any]]: (position_size, metadata)
        """
        # Use default method if none specified
        if method is None:
            method = self.default_method
        elif isinstance(method, str):
            method = PositionSizingMethod(method)
        
        # Get current capital from risk manager
        available_capital = self.risk_manager.capital
        current_exposure = self.risk_manager.get_current_exposure()
        
        # Default risk percentage if not specified
        if risk_per_trade_pct is None:
            risk_per_trade_pct = 0.01  # Default to 1% risk per trade
        
        # Default stop loss if not specified
        if stop_loss_pct is None:
            stop_loss_pct = 0.05  # Default to 5% stop loss
            
        # Get current price from ticker data
        current_price = ticker_data.get('last', 0) if ticker_data else 0
        
        # Log inputs for debugging
        self.logger.debug(
            f"Position size calculation - Method: {method.value}, "
            f"Capital: {available_capital}, Current exposure: {current_exposure}, "
            f"Risk: {risk_per_trade_pct:.1%}, Stop loss: {stop_loss_pct:.1%}"
        )
        
        # Calculate position size based on the chosen method
        if method == PositionSizingMethod.FIXED:
            return self._fixed_size(available_capital)
            
        elif method == PositionSizingMethod.PERCENT_OF_CAPITAL:
            return self._percent_of_capital(available_capital, current_exposure)
            
        elif method == PositionSizingMethod.RISK_BASED:
            return self._risk_based(available_capital, risk_per_trade_pct, stop_loss_pct, current_price)
            
        elif method == PositionSizingMethod.KELLY:
            if win_rate is None or reward_risk_ratio is None:
                self.logger.warning("Kelly criterion requires win_rate and reward_risk_ratio, falling back to risk-based")
                return self._risk_based(available_capital, risk_per_trade_pct, stop_loss_pct, current_price)
            return self._kelly_criterion(available_capital, win_rate, reward_risk_ratio)
            
        elif method == PositionSizingMethod.VOLATILITY_ADJUSTED:
            if price_volatility is None:
                self.logger.warning("Volatility-adjusted sizing requires price_volatility, falling back to risk-based")
                return self._risk_based(available_capital, risk_per_trade_pct, stop_loss_pct, current_price)
            return self._volatility_adjusted(available_capital, price_volatility, risk_per_trade_pct)
            
        elif method == PositionSizingMethod.ML_OPTIMIZED:
            self.logger.warning("ML-optimized sizing not implemented yet, falling back to risk-based")
            return self._risk_based(available_capital, risk_per_trade_pct, stop_loss_pct, current_price)
            
        else:
            self.logger.error(f"Unknown position sizing method: {method}")
            return 0.0, {"error": f"Unknown position sizing method: {method}"}
    
    def _fixed_size(self, capital: float) -> Tuple[float, Dict[str, Any]]:
        """Fixed position size implementation."""
        # Use a simple fixed percentage of capital
        position_quote_amount = capital * 0.1  # 10% of capital
        
        # Apply constraints
        position_quote_amount = min(position_quote_amount, capital * self.max_position_size_pct)
        position_quote_amount = max(position_quote_amount, self.min_position_size_quote)
        
        metadata = {
            "method": PositionSizingMethod.FIXED.value,
            "capital": capital,
            "percentage": 0.1
        }
        
        return position_quote_amount, metadata
    
    def _percent_of_capital(self, capital: float, current_exposure: float) -> Tuple[float, Dict[str, Any]]:
        """Percentage of capital implementation with optimal portfolio sizing."""
        # Calculate available capital for new positions
        available_for_new_positions = capital - current_exposure
        
        # Calculate position size based on optimal number of positions
        target_allocation = capital / self.optimal_positions_count
        position_quote_amount = min(target_allocation, available_for_new_positions)
        
        # Apply constraints
        position_quote_amount = min(position_quote_amount, capital * self.max_position_size_pct)
        position_quote_amount = max(position_quote_amount, self.min_position_size_quote)
        
        used_pct = position_quote_amount / capital
        
        metadata = {
            "method": PositionSizingMethod.PERCENT_OF_CAPITAL.value,
            "capital": capital,
            "current_exposure": current_exposure,
            "optimal_positions": self.optimal_positions_count,
            "percentage_used": used_pct
        }
        
        return position_quote_amount, metadata
    
    def _risk_based(self, capital: float, risk_pct: float, stop_loss_pct: float, 
                   current_price: float) -> Tuple[float, Dict[str, Any]]:
        """Risk-based position sizing implementation."""
        # Calculate risk amount in quote currency
        risk_amount = capital * risk_pct
        
        # Calculate position size based on stop loss
        if stop_loss_pct > 0 and current_price > 0:
            # Calculate position size as risk amount divided by potential loss percentage
            position_size_quote = risk_amount / stop_loss_pct
        else:
            # Fallback if stop loss or price is not valid
            position_size_quote = capital * 0.05  # Default to 5% of capital
        
        # Apply constraints
        position_size_quote = min(position_size_quote, capital * self.max_position_size_pct)
        position_size_quote = max(position_size_quote, self.min_position_size_quote)
        
        # Calculate position size in base currency if price is available
        position_size_base = position_size_quote / current_price if current_price > 0 else 0
        
        metadata = {
            "method": PositionSizingMethod.RISK_BASED.value,
            "capital": capital,
            "risk_percentage": risk_pct,
            "risk_amount": risk_amount,
            "stop_loss_percentage": stop_loss_pct,
            "position_size_base": position_size_base
        }
        
        return position_size_quote, metadata
    
    def _kelly_criterion(self, capital: float, win_rate: float, 
                        reward_risk_ratio: float) -> Tuple[float, Dict[str, Any]]:
        """Kelly Criterion position sizing implementation."""
        # Calculate Kelly percentage: f* = (bp - q) / b
        # Where: b = odds received on win, p = win rate, q = loss rate
        loss_rate = 1 - win_rate
        kelly_pct = (reward_risk_ratio * win_rate - loss_rate) / reward_risk_ratio
        
        # Apply half-Kelly for more conservative sizing
        half_kelly_pct = kelly_pct * 0.5
        
        # Handle negative Kelly (negative expectancy)
        if kelly_pct <= 0:
            self.logger.warning(f"Negative Kelly percentage: {kelly_pct:.2%} - trade has negative expectancy")
            return 0.0, {
                "method": PositionSizingMethod.KELLY.value,
                "capital": capital,
                "win_rate": win_rate,
                "reward_risk_ratio": reward_risk_ratio,
                "kelly_percentage": kelly_pct,
                "half_kelly_percentage": half_kelly_pct,
                "error": "Negative Kelly - trade has negative expectancy"
            }
        
        # Calculate position size based on Kelly
        position_quote_amount = capital * half_kelly_pct
        
        # Apply constraints
        position_quote_amount = min(position_quote_amount, capital * self.max_position_size_pct)
        position_quote_amount = max(position_quote_amount, self.min_position_size_quote)
        
        metadata = {
            "method": PositionSizingMethod.KELLY.value,
            "capital": capital,
            "win_rate": win_rate,
            "reward_risk_ratio": reward_risk_ratio,
            "kelly_percentage": kelly_pct,
            "half_kelly_percentage": half_kelly_pct
        }
        
        return position_quote_amount, metadata
    
    def _volatility_adjusted(self, capital: float, volatility: float, 
                            risk_pct: float) -> Tuple[float, Dict[str, Any]]:
        """Volatility-adjusted position sizing implementation."""
        # Calculate base position size
        base_position_size = capital * risk_pct
        
        # Adjust for volatility - reduce position size as volatility increases
        # Using a simple inverse relationship with volatility
        if volatility <= 0:
            volatility_scalar = 1.0
        else:
            # Scale the position size inversely to volatility
            # Higher volatility = smaller position size
            volatility_scalar = min(1.0, 0.01 / volatility)
        
        # Apply volatility adjustment
        position_quote_amount = base_position_size * volatility_scalar
        
        # Apply constraints
        position_quote_amount = min(position_quote_amount, capital * self.max_position_size_pct)
        position_quote_amount = max(position_quote_amount, self.min_position_size_quote)
        
        metadata = {
            "method": PositionSizingMethod.VOLATILITY_ADJUSTED.value,
            "capital": capital,
            "risk_percentage": risk_pct,
            "volatility": volatility,
            "volatility_scalar": volatility_scalar
        }
        
        return position_quote_amount, metadata