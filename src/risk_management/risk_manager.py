import logging
import numpy as np
import time

class RiskManager:
    """
    Manages risk for trading operations.
    
    This class handles risk calculations, position sizing, and risk limits enforcement
    to ensure trading operations stay within defined risk parameters.
    
    Attributes:
        capital (float): Total capital available for trading
        max_trade_size_pct (float): Maximum trade size as percentage of capital
        max_drawdown_pct (float): Maximum allowed drawdown before triggering circuit breaker
        logger (logging.Logger): Logger for risk management events
    """
    
    def __init__(self, capital, max_trade_size_pct=0.15, max_drawdown_pct=0.10):
        """
        Initialize the risk manager.
        
        Args:
            capital (float): Total capital available for trading
            max_trade_size_pct (float): Maximum trade size as percentage of capital
            max_drawdown_pct (float): Maximum allowed drawdown percentage
        """
        self.capital = capital
        self.max_trade_size_pct = max_trade_size_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.logger = logging.getLogger(__name__)

    def calculate_position_size(self, risk_per_trade, stop_loss_distance):
        """
        Calculate position size based on risk per trade and stop loss distance.
        
        Args:
            risk_per_trade (float): Risk per trade as decimal (e.g., 0.01 for 1%)
            stop_loss_distance (float): Distance to stop loss as decimal (e.g., 0.05 for 5%)
            
        Returns:
            float: Position size based on risk parameters
        """
        position_size = (self.capital * risk_per_trade) / stop_loss_distance
        self.logger.debug(f"Calculated position size: {position_size} based on risk: {risk_per_trade}, stop loss: {stop_loss_distance}")
        return position_size

    def enforce_risk_limits(self, trade_amount):
        """
        Enforce risk limits on trade amount.
        
        Args:
            trade_amount (float): Proposed trade amount
            
        Returns:
            float: Adjusted trade amount within risk limits
        """
        max_trade_size = self.capital * self.max_trade_size_pct
        if trade_amount > max_trade_size:
            self.logger.warning(f"Trade amount {trade_amount} exceeds max trade size {max_trade_size}. Reducing trade amount.")
            trade_amount = max_trade_size
        return trade_amount

    def time_weighted_order_slicing(self, total_amount, slices, interval, execute_slice_fn=None):
        """
        Implement time-weighted average price strategy by slicing orders over time.
        
        Args:
            total_amount (float): Total amount to trade
            slices (int): Number of slices to divide the order into
            interval (float): Time interval between slices in seconds
            execute_slice_fn (callable, optional): Function to execute each slice
        
        Returns:
            list: Results of each slice execution
        """
        slice_amount = total_amount / slices
        results = []
        
        for i in range(slices):
            self.logger.info(f"Executing slice {i+1}/{slices} of amount {slice_amount}")
            # Execute the slice order if a function is provided
            if execute_slice_fn:
                result = execute_slice_fn(slice_amount)
                results.append(result)
            time.sleep(interval)
        
        return results

    def calculate_var(self, returns, confidence_level=0.95):
        """
        Calculate Value at Risk (VaR) using historical simulation method.
        
        Args:
            returns (numpy.ndarray): Array of historical returns
            confidence_level (float): Confidence level for VaR (e.g., 0.95 for 95%)
            
        Returns:
            float: Value at Risk (positive value representing potential loss)
        """
        if len(returns) == 0:
            return 0
            
        sorted_returns = np.sort(returns)
        index = int((1 - confidence_level) * len(sorted_returns))
        # Ensure index is within bounds
        index = max(0, min(index, len(sorted_returns) - 1))
        var = -sorted_returns[index]  # Convert to positive value representing loss
        return var if var > 0 else 0  # Ensure VaR is non-negative

    def calculate_cvar(self, returns, confidence_level=0.95):
        """
        Calculate Conditional Value at Risk (CVaR) using historical simulation method.
        
        Args:
            returns (numpy.ndarray): Array of historical returns
            confidence_level (float): Confidence level for CVaR (e.g., 0.95 for 95%)
            
        Returns:
            float: Conditional Value at Risk (positive value representing potential loss)
        """
        if len(returns) == 0:
            return 0
            
        sorted_returns = np.sort(returns)
        index = int((1 - confidence_level) * len(sorted_returns))
        # Ensure index is within bounds
        index = max(1, min(index, len(sorted_returns) - 1))
        cvar = -np.mean(sorted_returns[:index])  # Convert to positive value representing loss
        return cvar if cvar > 0 else 0  # Ensure CVaR is non-negative
        
    def calculate_max_drawdown(self, prices):
        """
        Calculate maximum drawdown from a series of prices.
        
        Args:
            prices (numpy.ndarray): Array of historical prices
            
        Returns:
            float: Maximum drawdown as a positive decimal (e.g., 0.20 for 20%)
        """
        if len(prices) < 2:
            return 0
            
        # Calculate running maximum
        running_max = np.maximum.accumulate(prices)
        # Calculate drawdown at each point
        drawdowns = (prices - running_max) / running_max
        # Get maximum drawdown (will be negative)
        max_drawdown = abs(np.min(drawdowns))
        
        return max_drawdown
        
    def calculate_correlation(self, returns_a, returns_b):
        """
        Calculate correlation between two return series.
        
        Args:
            returns_a (numpy.ndarray): First series of returns
            returns_b (numpy.ndarray): Second series of returns
            
        Returns:
            float: Correlation coefficient between the two series
        """
        if len(returns_a) != len(returns_b) or len(returns_a) < 2:
            return 0
            
        correlation = np.corrcoef(returns_a, returns_b)[0, 1]
        return correlation
        
    def check_circuit_breaker(self, current_value, peak_value):
        """
        Check if circuit breaker should be triggered based on drawdown.
        
        Args:
            current_value (float): Current portfolio value
            peak_value (float): Peak portfolio value
            
        Returns:
            bool: True if circuit breaker should be triggered, False otherwise
        """
        if peak_value == 0:
            return False
            
        drawdown = (peak_value - current_value) / peak_value
        should_trigger = drawdown >= self.max_drawdown_pct
        
        if should_trigger:
            self.logger.warning(f"Circuit breaker triggered: drawdown {drawdown:.2%} exceeds max {self.max_drawdown_pct:.2%}")
            
        return should_trigger