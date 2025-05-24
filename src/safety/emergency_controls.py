"""
Emergency Controls - Safety mechanisms and circuit breakers for Grekko.

Implements multiple layers of protection to prevent catastrophic losses.
"""
import asyncio
from typing import Dict, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import os

from ..utils.logger import get_logger
from ..utils.database import get_db, Trade, Position

logger = get_logger('emergency_controls')


@dataclass
class RiskLimits:
    """Risk limits configuration."""
    max_daily_loss_sol: float = 1.0        # Maximum daily loss
    max_position_size_sol: float = 0.5     # Maximum single position
    max_total_exposure_sol: float = 5.0    # Maximum total exposure
    max_consecutive_losses: int = 5        # Consecutive losses before pause
    min_time_between_trades_ms: int = 1000 # Minimum time between trades
    max_slippage_percent: float = 5.0      # Maximum allowed slippage


class CircuitBreaker:
    """
    Multi-level circuit breaker for trade protection.
    
    Monitors various risk metrics and can halt trading when limits are exceeded.
    """
    
    def __init__(self, limits: RiskLimits):
        self.limits = limits
        self.is_active = True
        self.pause_until: Optional[datetime] = None
        self.daily_loss = 0.0
        self.consecutive_losses = 0
        self.last_trade_time: Optional[datetime] = None
        self.trip_history: List[Dict] = []
        
        # Callbacks for circuit breaker events
        self.on_trip_callbacks: List[Callable] = []
        self.on_reset_callbacks: List[Callable] = []
        
    def can_trade(self) -> tuple[bool, Optional[str]]:
        """
        Check if trading is allowed.
        
        Returns:
            Tuple of (can_trade, reason_if_blocked)
        """
        # Check if manually paused
        if not self.is_active:
            return False, "Circuit breaker manually deactivated"
            
        # Check if in cooldown period
        if self.pause_until and datetime.utcnow() < self.pause_until:
            remaining = (self.pause_until - datetime.utcnow()).total_seconds()
            return False, f"Circuit breaker tripped, cooldown for {remaining:.0f}s"
            
        # Check daily loss limit
        if abs(self.daily_loss) >= self.limits.max_daily_loss_sol:
            return False, f"Daily loss limit reached: {self.daily_loss:.2f} SOL"
            
        # Check consecutive losses
        if self.consecutive_losses >= self.limits.max_consecutive_losses:
            return False, f"Too many consecutive losses: {self.consecutive_losses}"
            
        # Check minimum time between trades
        if self.last_trade_time:
            time_since_last = (datetime.utcnow() - self.last_trade_time).total_seconds() * 1000
            if time_since_last < self.limits.min_time_between_trades_ms:
                return False, f"Too soon since last trade: {time_since_last:.0f}ms"
                
        return True, None
        
    def record_trade_result(self, pnl_sol: float, slippage_percent: float):
        """Record trade result and update circuit breaker state."""
        self.last_trade_time = datetime.utcnow()
        
        # Update daily loss
        self.daily_loss += pnl_sol
        
        # Update consecutive losses
        if pnl_sol < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
            
        # Check slippage
        if abs(slippage_percent) > self.limits.max_slippage_percent:
            logger.warning(f"High slippage detected: {slippage_percent:.1f}%")
            self.trip("high_slippage", f"Slippage {slippage_percent:.1f}% exceeded limit")
            
        # Auto-trip if limits exceeded
        if abs(self.daily_loss) >= self.limits.max_daily_loss_sol:
            self.trip("daily_loss", f"Daily loss {self.daily_loss:.2f} SOL exceeded limit")
        elif self.consecutive_losses >= self.limits.max_consecutive_losses:
            self.trip("consecutive_losses", f"{self.consecutive_losses} consecutive losses")
            
    def trip(self, reason: str, details: str, cooldown_minutes: int = 30):
        """
        Trip the circuit breaker.
        
        Args:
            reason: Why the breaker was tripped
            details: Additional details
            cooldown_minutes: How long to pause trading
        """
        self.pause_until = datetime.utcnow() + timedelta(minutes=cooldown_minutes)
        
        trip_event = {
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "details": details,
            "cooldown_minutes": cooldown_minutes,
            "daily_loss": self.daily_loss,
            "consecutive_losses": self.consecutive_losses
        }
        
        self.trip_history.append(trip_event)
        
        logger.error(f"🚨 CIRCUIT BREAKER TRIPPED: {reason} - {details}")
        logger.error(f"   Trading paused until: {self.pause_until}")
        
        # Execute callbacks
        for callback in self.on_trip_callbacks:
            try:
                callback(trip_event)
            except Exception as e:
                logger.error(f"Error in trip callback: {str(e)}")
                
    def reset(self):
        """Reset the circuit breaker (manual intervention)."""
        self.pause_until = None
        self.consecutive_losses = 0
        self.is_active = True
        
        logger.info("Circuit breaker manually reset")
        
        # Execute callbacks
        for callback in self.on_reset_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in reset callback: {str(e)}")
                
    def reset_daily_counters(self):
        """Reset daily counters (should be called at UTC midnight)."""
        self.daily_loss = 0.0
        logger.info("Daily loss counter reset")


class EmergencyShutdown:
    """
    Emergency shutdown system for critical failures.
    
    Can be triggered manually or automatically based on severe conditions.
    """
    
    def __init__(self):
        self.shutdown_file = ".grekko_emergency_stop"
        self.shutdown_callbacks: List[Callable] = []
        self.is_checking = True
        
    async def start_monitoring(self):
        """Start monitoring for emergency shutdown signals."""
        while self.is_checking:
            # Check for shutdown file
            if os.path.exists(self.shutdown_file):
                await self.execute_shutdown("Shutdown file detected")
                break
                
            # Check system health
            if not self._check_system_health():
                await self.execute_shutdown("System health check failed")
                break
                
            await asyncio.sleep(1)  # Check every second
            
    def _check_system_health(self) -> bool:
        """
        Check overall system health.
        
        Returns:
            True if healthy, False if critical issue detected
        """
        try:
            # Check database connectivity
            with get_db() as db:
                db.execute("SELECT 1")
                
            # Check memory usage
            import psutil
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 90:
                logger.error(f"Critical memory usage: {memory_percent}%")
                return False
                
            # Add more health checks as needed
            
            return True
            
        except Exception as e:
            logger.error(f"System health check failed: {str(e)}")
            return False
            
    async def execute_shutdown(self, reason: str):
        """Execute emergency shutdown."""
        logger.critical(f"🚨🚨🚨 EMERGENCY SHUTDOWN: {reason}")
        
        # Create shutdown record
        shutdown_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "positions": await self._get_open_positions()
        }
        
        # Save shutdown state
        with open("emergency_shutdown.json", "w") as f:
            json.dump(shutdown_record, f, indent=2)
            
        # Execute callbacks
        for callback in self.shutdown_callbacks:
            try:
                await callback(reason)
            except Exception as e:
                logger.error(f"Error in shutdown callback: {str(e)}")
                
        # Stop monitoring
        self.is_checking = False
        
    async def _get_open_positions(self) -> List[Dict]:
        """Get all open positions for shutdown record."""
        positions = []
        
        with get_db() as db:
            open_positions = db.query(Position).filter(Position.is_active == True).all()
            
            for pos in open_positions:
                positions.append({
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "entry_price": pos.avg_entry_price,
                    "current_value": pos.position_value,
                    "unrealized_pnl": pos.unrealized_pnl
                })
                
        return positions
        
    def create_shutdown_file(self):
        """Create shutdown file to trigger emergency stop."""
        with open(self.shutdown_file, "w") as f:
            f.write(f"Emergency shutdown requested at {datetime.utcnow().isoformat()}")
            
    def register_shutdown_callback(self, callback: Callable):
        """Register a callback for emergency shutdown."""
        self.shutdown_callbacks.append(callback)


class PositionLimiter:
    """
    Enforces position size and exposure limits.
    
    Prevents overexposure to single tokens or total portfolio risk.
    """
    
    def __init__(self, limits: RiskLimits):
        self.limits = limits
        
    def check_position_allowed(self, 
                             token_address: str,
                             proposed_size_sol: float,
                             current_positions: Dict[str, float]) -> tuple[bool, Optional[str]]:
        """
        Check if a new position is allowed.
        
        Args:
            token_address: Token to buy
            proposed_size_sol: Size in SOL
            current_positions: Current positions {token: size_sol}
            
        Returns:
            Tuple of (allowed, reason_if_blocked)
        """
        # Check single position size
        if proposed_size_sol > self.limits.max_position_size_sol:
            return False, f"Position size {proposed_size_sol} SOL exceeds limit"
            
        # Check if already have position in this token
        if token_address in current_positions:
            total_size = current_positions[token_address] + proposed_size_sol
            if total_size > self.limits.max_position_size_sol:
                return False, f"Total position in {token_address[:8]} would exceed limit"
                
        # Check total exposure
        total_exposure = sum(current_positions.values()) + proposed_size_sol
        if total_exposure > self.limits.max_total_exposure_sol:
            return False, f"Total exposure would exceed {self.limits.max_total_exposure_sol} SOL"
            
        return True, None
        
    def suggest_position_size(self,
                            safety_score: float,
                            current_exposure: float) -> float:
        """
        Suggest position size based on safety score and current exposure.
        
        Uses Kelly Criterion-inspired sizing with safety adjustments.
        """
        # Base size from limits
        max_size = self.limits.max_position_size_sol
        
        # Adjust based on remaining exposure room
        remaining_exposure = self.limits.max_total_exposure_sol - current_exposure
        max_size = min(max_size, remaining_exposure)
        
        # Adjust based on safety score (Kelly-like)
        # Higher safety = larger position
        safety_multiplier = (safety_score / 100) ** 2  # Quadratic for conservatism
        
        suggested_size = max_size * safety_multiplier
        
        # Minimum position size (avoid dust)
        min_size = 0.01  # 0.01 SOL minimum
        
        return max(min_size, suggested_size)


# Example usage in main bot
async def setup_safety_systems(bot):
    """Set up all safety systems for the bot."""
    # Configure limits
    limits = RiskLimits(
        max_daily_loss_sol=2.0,
        max_position_size_sol=0.5,
        max_total_exposure_sol=5.0,
        max_consecutive_losses=5,
        min_time_between_trades_ms=1000,
        max_slippage_percent=5.0
    )
    
    # Initialize systems
    circuit_breaker = CircuitBreaker(limits)
    emergency_shutdown = EmergencyShutdown()
    position_limiter = PositionLimiter(limits)
    
    # Register callbacks
    circuit_breaker.on_trip_callbacks.append(
        lambda event: logger.critical(f"Circuit breaker tripped: {event}")
    )
    
    emergency_shutdown.register_shutdown_callback(
        lambda reason: bot.stop()
    )
    
    # Start emergency monitoring
    asyncio.create_task(emergency_shutdown.start_monitoring())
    
    # Reset daily counters at midnight
    async def daily_reset():
        while True:
            # Calculate seconds until midnight UTC
            now = datetime.utcnow()
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            seconds_until_midnight = (midnight - now).total_seconds()
            
            await asyncio.sleep(seconds_until_midnight)
            circuit_breaker.reset_daily_counters()
            
    asyncio.create_task(daily_reset())
    
    return circuit_breaker, emergency_shutdown, position_limiter