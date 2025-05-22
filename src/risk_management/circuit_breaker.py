"""
Circuit breaker module for the Grekko trading system.

This module implements safety mechanisms to halt trading under extreme market conditions,
significant losses, or unusual price movements to prevent catastrophic losses.

The circuit breaker can be triggered by:
1. Excessive drawdown (percentage loss from peak value)
2. Unusual market volatility (compared to historical standard deviation)
3. Consecutive losing trades exceeding a threshold
4. Manual activation by risk management system
"""
import logging
import time
import traceback
import numpy as np
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple, Union
from ..utils.logger import get_logger

class TriggerReason(Enum):
    """Enumeration of circuit breaker trigger reasons."""
    DRAWDOWN = "excessive_drawdown"
    VOLATILITY = "unusual_volatility"
    CONSECUTIVE_LOSSES = "consecutive_losses"
    API_ERRORS = "api_errors"
    UNUSUAL_SPREAD = "unusual_spread"
    MANUAL = "manual_activation"
    SYSTEM_ERROR = "system_error"
    NETWORK_ISSUE = "network_issue"
    UNKNOWN = "unknown"

class CircuitBreaker:
    """
    Circuit breaker for trading operations.
    
    Monitors market conditions and portfolio performance to automatically
    halt trading when predefined risk thresholds are breached. This provides
    a critical safety mechanism to prevent catastrophic losses during extreme
    market conditions or system failures.
    
    Attributes:
        max_drawdown_pct (float): Maximum allowed drawdown as percentage
        volatility_threshold (float): Maximum allowed price volatility
        max_consecutive_losses (int): Maximum number of consecutive losing trades
        cooldown_minutes (int): Minutes to wait after a circuit breaker trigger
        is_active (bool): Current state of the circuit breaker
        triggered_at (datetime): When the circuit breaker was last triggered
        trigger_reason (TriggerReason): Reason why circuit breaker was triggered
        consecutive_losses (int): Current count of consecutive losing trades
        peak_portfolio_value (float): Highest portfolio value seen
        logger (logging.Logger): Logger for circuit breaker events
        trigger_history (List[Dict]): History of circuit breaker triggers
        error_count (Dict[str, int]): Count of different errors by category
    """
    
    def __init__(self, 
                 max_drawdown_pct: float = 0.10,
                 volatility_threshold: float = 3.0,
                 max_consecutive_losses: int = 5,
                 cooldown_minutes: int = 30,
                 max_api_errors: int = 3,
                 max_spread_multiple: float = 5.0,
                 enable_error_tracking: bool = True):
        """
        Initialize the circuit breaker with configurable safety thresholds.
        
        Args:
            max_drawdown_pct (float): Maximum allowed drawdown percentage (default: 10%)
            volatility_threshold (float): Maximum volatility in standard deviations (default: 3.0)
            max_consecutive_losses (int): Maximum consecutive losing trades (default: 5)
            cooldown_minutes (int): Minutes to wait after triggering (default: 30)
            max_api_errors (int): Maximum allowed API errors before triggering (default: 3)
            max_spread_multiple (float): Maximum allowed spread vs historical average (default: 5.0)
            enable_error_tracking (bool): Whether to track errors and API issues (default: True)
        """
        # Risk thresholds
        self.max_drawdown_pct = max_drawdown_pct
        self.volatility_threshold = volatility_threshold
        self.max_consecutive_losses = max_consecutive_losses
        self.cooldown_minutes = cooldown_minutes
        self.max_api_errors = max_api_errors
        self.max_spread_multiple = max_spread_multiple
        self.enable_error_tracking = enable_error_tracking
        
        # State tracking
        self.is_active = False
        self.triggered_at = None
        self.trigger_reason = None
        self.consecutive_losses = 0
        self.peak_portfolio_value = 0.0
        self.trigger_history = []
        self.error_count = {
            "api": 0,
            "network": 0,
            "system": 0,
            "timeout": 0,
            "unknown": 0
        }
        self.last_error_reset = datetime.now()
        
        # Setup logger
        self.logger = get_logger('circuit_breaker')
        self.logger.info("Circuit breaker initialized with the following parameters:")
        self.logger.info(f"- Max drawdown: {self.max_drawdown_pct:.1%}")
        self.logger.info(f"- Volatility threshold: {self.volatility_threshold:.1f}x")
        self.logger.info(f"- Max consecutive losses: {self.max_consecutive_losses}")
        self.logger.info(f"- Cooldown period: {self.cooldown_minutes} minutes")
        self.logger.info(f"- Error tracking enabled: {self.enable_error_tracking}")
        
    def update_portfolio_value(self, current_value):
        """
        Update the peak portfolio value.
        
        Args:
            current_value (float): Current portfolio value
        """
        if current_value > self.peak_portfolio_value:
            self.peak_portfolio_value = current_value
    
    def check_drawdown(self, current_value):
        """
        Check if drawdown exceeds maximum allowed.
        
        Args:
            current_value (float): Current portfolio value
            
        Returns:
            bool: True if drawdown threshold is breached, False otherwise
        """
        if self.peak_portfolio_value == 0:
            return False
            
        drawdown = (self.peak_portfolio_value - current_value) / self.peak_portfolio_value
        
        if drawdown >= self.max_drawdown_pct:
            self.logger.warning(
                f"Circuit breaker triggered: Drawdown {drawdown:.2%} exceeds maximum {self.max_drawdown_pct:.2%}"
            )
            return True
            
        return False
    
    def check_volatility(self, recent_returns, historical_std):
        """
        Check if recent volatility exceeds threshold.
        
        Args:
            recent_returns (list): List of recent returns
            historical_std (float): Historical standard deviation of returns
            
        Returns:
            bool: True if volatility threshold is breached, False otherwise
        """
        import numpy as np
        
        if len(recent_returns) < 2 or historical_std == 0:
            return False
            
        recent_std = np.std(recent_returns)
        volatility_ratio = recent_std / historical_std
        
        if volatility_ratio >= self.volatility_threshold:
            self.logger.warning(
                f"Circuit breaker triggered: Volatility ratio {volatility_ratio:.2f} exceeds threshold {self.volatility_threshold:.2f}"
            )
            return True
            
        return False
    
    def record_trade_result(self, is_profitable):
        """
        Record the result of a trade and check for consecutive losses.
        
        Args:
            is_profitable (bool): Whether the trade was profitable
            
        Returns:
            bool: True if consecutive loss threshold is breached, False otherwise
        """
        if is_profitable:
            self.consecutive_losses = 0
            return False
            
        self.consecutive_losses += 1
        
        if self.consecutive_losses >= self.max_consecutive_losses:
            self.logger.warning(
                f"Circuit breaker triggered: {self.consecutive_losses} consecutive losses exceeds maximum {self.max_consecutive_losses}"
            )
            return True
            
        return False
    
    def trigger(self, reason: Union[str, TriggerReason], details: Optional[Dict[str, Any]] = None):
        """
        Trigger the circuit breaker with detailed reason and metadata.
        
        Args:
            reason (Union[str, TriggerReason]): Reason for triggering
            details (Optional[Dict[str, Any]]): Additional details about the trigger
        
        Returns:
            bool: True if circuit breaker was activated, False if already active
        """
        # Already triggered
        if self.is_active:
            self.logger.info(f"Circuit breaker already active (triggered by {self.trigger_reason})")
            return False
            
        # Set circuit breaker state
        self.is_active = True
        self.triggered_at = datetime.now()
        
        # Convert string reason to enum if needed
        if isinstance(reason, str):
            try:
                self.trigger_reason = TriggerReason(reason)
            except ValueError:
                self.trigger_reason = TriggerReason.UNKNOWN
        else:
            self.trigger_reason = reason
            
        # Create trigger record
        trigger_record = {
            "timestamp": self.triggered_at.isoformat(),
            "reason": self.trigger_reason.value,
            "details": details or {},
            "cooldown_minutes": self.cooldown_minutes,
            "resume_at": (self.triggered_at + timedelta(minutes=self.cooldown_minutes)).isoformat()
        }
        
        # Add to history
        self.trigger_history.append(trigger_record)
        
        # Log the trigger event
        self.logger.warning(
            f"CIRCUIT BREAKER ACTIVATED: {self.trigger_reason.value}. "
            f"Trading halted for {self.cooldown_minutes} minutes until "
            f"{(self.triggered_at + timedelta(minutes=self.cooldown_minutes)).strftime('%H:%M:%S')}"
        )
        
        if details:
            self.logger.warning(f"Trigger details: {details}")
            
        return True
        
    def record_error(self, error_type: str, error: Exception = None):
        """
        Record an error and check if circuit breaker should be triggered.
        
        Args:
            error_type (str): Type of error (api, network, system, timeout, unknown)
            error (Exception, optional): The exception that occurred
            
        Returns:
            bool: True if circuit breaker was triggered due to errors, False otherwise
        """
        if not self.enable_error_tracking:
            return False
            
        # Reset error counts if it's been more than an hour
        if (datetime.now() - self.last_error_reset).total_seconds() > 3600:
            self.error_count = {k: 0 for k in self.error_count}
            self.last_error_reset = datetime.now()
            
        # Increment error count
        error_type = error_type.lower()
        if error_type in self.error_count:
            self.error_count[error_type] += 1
        else:
            self.error_count["unknown"] += 1
            
        # Log the error
        if error:
            self.logger.error(f"{error_type.upper()} ERROR: {str(error)}")
            # Log stack trace for system errors
            if error_type == "system":
                self.logger.error(f"Stack trace: {traceback.format_exc()}")
                
        # Check if we should trigger circuit breaker
        total_api_errors = self.error_count["api"] + self.error_count["network"] + self.error_count["timeout"]
        if total_api_errors >= self.max_api_errors:
            details = {
                "error_counts": self.error_count,
                "latest_error": str(error) if error else None,
                "error_type": error_type
            }
            return self.trigger(TriggerReason.API_ERRORS, details)
            
        # Immediately trigger on system errors
        if error_type == "system" and self.error_count["system"] > 0:
            details = {
                "error": str(error) if error else None,
                "stack_trace": traceback.format_exc() if error else None
            }
            return self.trigger(TriggerReason.SYSTEM_ERROR, details)
            
        return False
    
    def check_cooldown(self):
        """
        Check if cooldown period has elapsed.
        
        Returns:
            bool: True if cooldown period has elapsed, False otherwise
        """
        if not self.is_active:
            return True
            
        elapsed = datetime.now() - self.triggered_at
        
        if elapsed >= timedelta(minutes=self.cooldown_minutes):
            self.is_active = False
            self.logger.info("Circuit breaker cooldown period elapsed. Trading can resume.")
            return True
            
        return False
    
    def check_market_spread(self, current_spread: float, avg_spread: float) -> bool:
        """
        Check if current market spread is unusually wide.
        
        Args:
            current_spread (float): Current bid-ask spread
            avg_spread (float): Average bid-ask spread
            
        Returns:
            bool: True if spread threshold is breached, False otherwise
        """
        if avg_spread == 0 or current_spread < 0:
            return False
            
        spread_ratio = current_spread / avg_spread
        
        if spread_ratio >= self.max_spread_multiple:
            details = {
                "current_spread": current_spread,
                "avg_spread": avg_spread,
                "ratio": spread_ratio,
                "threshold": self.max_spread_multiple
            }
            self.logger.warning(
                f"Unusual spread detected: {spread_ratio:.2f}x normal "
                f"(current: {current_spread:.6f}, avg: {avg_spread:.6f})"
            )
            self.trigger(TriggerReason.UNUSUAL_SPREAD, details)
            return True
            
        return False
        
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the circuit breaker.
        
        Returns:
            Dict[str, Any]: Circuit breaker status information
        """
        status = {
            "is_active": self.is_active,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "trigger_reason": self.trigger_reason.value if self.trigger_reason else None,
            "consecutive_losses": self.consecutive_losses,
            "peak_portfolio_value": self.peak_portfolio_value,
            "error_counts": self.error_count,
            "triggers_count": len(self.trigger_history),
            "recent_triggers": self.trigger_history[-3:] if self.trigger_history else []
        }
        
        if self.is_active:
            cooldown_remaining = max(0, (self.triggered_at + timedelta(minutes=self.cooldown_minutes) - datetime.now()).total_seconds() / 60)
            status["cooldown_remaining_minutes"] = round(cooldown_remaining, 1)
            
        return status

    def can_trade(self, 
                 current_value: float, 
                 recent_returns: Optional[List[float]] = None, 
                 historical_std: Optional[float] = None,
                 current_spread: Optional[float] = None,
                 avg_spread: Optional[float] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if trading is allowed based on all circuit breaker conditions.
        
        Performs a comprehensive check of all safety conditions to determine
        if trading should be allowed or halted.
        
        Args:
            current_value (float): Current portfolio value
            recent_returns (Optional[List[float]]): List of recent returns
            historical_std (Optional[float]): Historical standard deviation of returns
            current_spread (Optional[float]): Current bid-ask spread
            avg_spread (Optional[float]): Average historical bid-ask spread
            
        Returns:
            Tuple[bool, Optional[str]]: (can_trade, reason_if_not)
        """
        try:
            # Update peak portfolio value
            self.update_portfolio_value(current_value)
            
            # If circuit breaker is active, check cooldown
            if self.is_active:
                if not self.check_cooldown():
                    cooldown_remaining = max(0, (self.triggered_at + timedelta(minutes=self.cooldown_minutes) - datetime.now()).total_seconds() / 60)
                    return False, f"Circuit breaker active ({self.trigger_reason.value if self.trigger_reason else 'unknown'}): {cooldown_remaining:.1f} minutes remaining"
                self.logger.info("Circuit breaker cooldown period elapsed, trading can resume")
            
            # Check drawdown threshold
            if self.check_drawdown(current_value):
                return False, "Maximum drawdown exceeded"
            
            # Check volatility threshold if data provided
            if recent_returns is not None and historical_std is not None:
                if self.check_volatility(recent_returns, historical_std):
                    return False, "Unusual market volatility"
            
            # Check spread threshold if data provided
            if current_spread is not None and avg_spread is not None:
                if self.check_market_spread(current_spread, avg_spread):
                    return False, "Unusual market spread"
            
            # All checks passed
            return True, None
            
        except Exception as e:
            # Record the error and possibly trigger circuit breaker
            self.record_error("system", e)
            self.logger.error(f"Error in circuit breaker can_trade check: {str(e)}")
            return False, f"System error in circuit breaker: {str(e)}"
    
    def reset(self, reset_history: bool = False, reset_peak_value: bool = False) -> Dict[str, Any]:
        """
        Reset the circuit breaker state.
        
        Args:
            reset_history (bool): Whether to reset trigger history
            reset_peak_value (bool): Whether to reset peak portfolio value
            
        Returns:
            Dict[str, Any]: Status of the circuit breaker after reset
        """
        previous_state = {
            "was_active": self.is_active,
            "trigger_reason": self.trigger_reason.value if self.trigger_reason else None,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "consecutive_losses": self.consecutive_losses,
            "error_counts": self.error_count.copy()
        }
        
        # Reset active state
        self.is_active = False
        self.triggered_at = None
        self.trigger_reason = None
        self.consecutive_losses = 0
        
        # Reset error counts
        self.error_count = {k: 0 for k in self.error_count}
        self.last_error_reset = datetime.now()
        
        # Optionally reset history
        if reset_history:
            self.trigger_history = []
            
        # Optionally reset peak value
        if reset_peak_value:
            self.peak_portfolio_value = 0.0
            
        self.logger.warning(
            "Circuit breaker has been reset manually. "
            f"Previous state: {previous_state}"
        )
        
        return self.get_status()