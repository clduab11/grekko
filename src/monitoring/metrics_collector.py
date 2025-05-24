"""
Metrics Collector - Real-time monitoring for Grekko Sniper Bot.

Collects and exposes metrics for Prometheus/Grafana monitoring.
"""
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from typing import Dict, Any
import asyncio

# Metrics definitions
TOKENS_DETECTED = Counter('grekko_tokens_detected_total', 'Total new tokens detected')
TOKENS_ANALYZED = Counter('grekko_tokens_analyzed_total', 'Total tokens analyzed for safety')
TRADES_EXECUTED = Counter('grekko_trades_executed_total', 'Total trades executed', ['status'])
DETECTION_TIME = Histogram('grekko_detection_time_seconds', 'Time to detect new tokens', buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 2.0])
EXECUTION_TIME = Histogram('grekko_execution_time_seconds', 'Time to execute trades', buckets=[0.1, 0.2, 0.5, 1.0, 2.0, 5.0])
SAFETY_SCORE = Histogram('grekko_safety_score', 'Distribution of safety scores', buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
PNL_GAUGE = Gauge('grekko_pnl_sol', 'Current P&L in SOL')
ACTIVE_POSITIONS = Gauge('grekko_active_positions', 'Number of active positions')
BOT_STATUS = Gauge('grekko_bot_status', 'Bot status (1=running, 0=stopped)')

# Alert thresholds
ALERT_THRESHOLDS = {
    'detection_time_ms': 500,  # Alert if detection takes >500ms
    'execution_time_ms': 1000,  # Alert if execution takes >1s
    'failed_trades_rate': 0.2,  # Alert if >20% trades fail
    'low_safety_rate': 0.3,     # Alert if >30% tokens have low safety
    'pnl_drawdown': -0.1,       # Alert if P&L drops >10%
}

class MetricsCollector:
    """Collects and exposes metrics for monitoring."""
    
    def __init__(self, port: int = 9090):
        self.port = port
        self.start_time = time.time()
        self.metrics_cache = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'peak_pnl': 0.0,
            'current_pnl': 0.0
        }
        
    def start(self):
        """Start the Prometheus metrics server."""
        start_http_server(self.port)
        print(f"Metrics server started on port {self.port}")
        
    def record_token_detected(self):
        """Record a new token detection."""
        TOKENS_DETECTED.inc()
        
    def record_token_analyzed(self, safety_score: float):
        """Record token analysis."""
        TOKENS_ANALYZED.inc()
        SAFETY_SCORE.observe(safety_score)
        
    def record_trade(self, success: bool, execution_time_ms: float):
        """Record trade execution."""
        status = 'success' if success else 'failed'
        TRADES_EXECUTED.labels(status=status).inc()
        EXECUTION_TIME.observe(execution_time_ms / 1000)
        
        # Update cache
        self.metrics_cache['total_trades'] += 1
        if success:
            self.metrics_cache['successful_trades'] += 1
        else:
            self.metrics_cache['failed_trades'] += 1
            
        # Check alert conditions
        self._check_alerts()
        
    def record_detection_time(self, detection_time_ms: float):
        """Record token detection time."""
        DETECTION_TIME.observe(detection_time_ms / 1000)
        
        if detection_time_ms > ALERT_THRESHOLDS['detection_time_ms']:
            print(f"⚠️  ALERT: Slow detection time: {detection_time_ms:.1f}ms")
            
    def update_pnl(self, pnl_sol: float):
        """Update P&L metrics."""
        PNL_GAUGE.set(pnl_sol)
        self.metrics_cache['current_pnl'] = pnl_sol
        
        # Track peak for drawdown calculation
        if pnl_sol > self.metrics_cache['peak_pnl']:
            self.metrics_cache['peak_pnl'] = pnl_sol
            
        # Check drawdown
        if self.metrics_cache['peak_pnl'] > 0:
            drawdown = (pnl_sol - self.metrics_cache['peak_pnl']) / self.metrics_cache['peak_pnl']
            if drawdown < ALERT_THRESHOLDS['pnl_drawdown']:
                print(f"⚠️  ALERT: Significant drawdown: {drawdown:.1%}")
                
    def update_positions(self, count: int):
        """Update active positions count."""
        ACTIVE_POSITIONS.set(count)
        
    def set_bot_status(self, is_running: bool):
        """Update bot status."""
        BOT_STATUS.set(1 if is_running else 0)
        
    def _check_alerts(self):
        """Check for alert conditions."""
        if self.metrics_cache['total_trades'] > 10:
            # Check failed trade rate
            fail_rate = self.metrics_cache['failed_trades'] / self.metrics_cache['total_trades']
            if fail_rate > ALERT_THRESHOLDS['failed_trades_rate']:
                print(f"⚠️  ALERT: High failure rate: {fail_rate:.1%}")
                
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        uptime = time.time() - self.start_time
        
        return {
            'status': 'healthy',
            'uptime_seconds': uptime,
            'metrics': {
                'total_trades': self.metrics_cache['total_trades'],
                'success_rate': (self.metrics_cache['successful_trades'] / self.metrics_cache['total_trades']) if self.metrics_cache['total_trades'] > 0 else 0,
                'current_pnl': self.metrics_cache['current_pnl'],
                'alerts': []  # Would populate with active alerts
            }
        }