"""
Latency optimization for the Grekko trading platform.

Optimizes order execution parameters and routing to minimize latency
and improve execution quality.
"""
import time
import asyncio
from typing import Dict, Any, List, Optional
from collections import deque
from datetime import datetime, timedelta

from ..utils.logger import get_logger


class LatencyOptimizer:
    """
    Optimizes trading latency through intelligent routing and parameter tuning.
    
    Tracks exchange performance, predicts optimal execution times, and
    adjusts parameters to minimize latency.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the latency optimizer.
        
        Args:
            config: Latency optimization configuration
        """
        self.config = config
        self.logger = get_logger('latency_optimizer')
        
        # Latency tracking per exchange
        self.latency_history = {}
        self.max_history_size = config.get('max_history_size', 1000)
        
        # Performance metrics
        self.exchange_metrics = {}
        
        # Optimization parameters
        self.optimization_enabled = config.get('enabled', True)
        self.target_latency_ms = config.get('target_latency_ms', 50)
        self.max_retry_latency_ms = config.get('max_retry_latency_ms', 200)
        
        # Network optimization
        self.connection_pools = {}
        self.max_connections = config.get('max_connections_per_exchange', 10)
        
        self.logger.info(f"LatencyOptimizer initialized with target latency: {self.target_latency_ms}ms")
    
    async def optimize_order_params(self,
                                  exchange: str,
                                  order_type: str,
                                  current_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize order parameters for minimal latency.
        
        Args:
            exchange: Exchange name
            order_type: Type of order
            current_params: Current order parameters
            
        Returns:
            Optimized parameters
        """
        if not self.optimization_enabled:
            return current_params
        
        optimized_params = current_params.copy()
        
        # Get current exchange metrics
        metrics = self.get_exchange_metrics(exchange)
        
        # Optimize based on current conditions
        if metrics['avg_latency'] > self.target_latency_ms:
            # High latency - adjust parameters
            optimized_params = self._adjust_for_high_latency(optimized_params, metrics)
        
        # Add timing optimization
        optimized_params['optimal_send_time'] = self._calculate_optimal_send_time(exchange)
        
        # Add connection pooling hint
        optimized_params['use_connection_pool'] = True
        optimized_params['pool_id'] = self._get_connection_pool_id(exchange)
        
        return optimized_params
    
    def record_latency(self, exchange: str, latency_ms: float, success: bool = True) -> None:
        """
        Record latency measurement for an exchange.
        
        Args:
            exchange: Exchange name
            latency_ms: Latency in milliseconds
            success: Whether the request was successful
        """
        if exchange not in self.latency_history:
            self.latency_history[exchange] = deque(maxlen=self.max_history_size)
        
        record = {
            'timestamp': time.time(),
            'latency_ms': latency_ms,
            'success': success
        }
        
        self.latency_history[exchange].append(record)
        
        # Update metrics
        self._update_exchange_metrics(exchange)
        
        # Log if latency is too high
        if latency_ms > self.max_retry_latency_ms:
            self.logger.warning(f"{exchange} latency {latency_ms:.1f}ms exceeds threshold")
    
    def get_exchange_latency(self, exchange: str) -> float:
        """
        Get current average latency for an exchange.
        
        Args:
            exchange: Exchange name
            
        Returns:
            Average latency in milliseconds
        """
        metrics = self.get_exchange_metrics(exchange)
        return metrics.get('avg_latency', 100)  # Default 100ms if no data
    
    def get_exchange_metrics(self, exchange: str) -> Dict[str, Any]:
        """
        Get comprehensive metrics for an exchange.
        
        Args:
            exchange: Exchange name
            
        Returns:
            Exchange metrics
        """
        if exchange not in self.exchange_metrics:
            self._update_exchange_metrics(exchange)
        
        return self.exchange_metrics.get(exchange, self._get_default_metrics())
    
    def get_fastest_exchange(self, exchanges: List[str]) -> str:
        """
        Get the exchange with lowest latency from a list.
        
        Args:
            exchanges: List of exchange names
            
        Returns:
            Exchange with lowest latency
        """
        if not exchanges:
            raise ValueError("No exchanges provided")
        
        # Get latencies
        latencies = {
            exchange: self.get_exchange_latency(exchange)
            for exchange in exchanges
        }
        
        # Return exchange with minimum latency
        return min(latencies.items(), key=lambda x: x[1])[0]
    
    def predict_execution_time(self, exchange: str, order_size: float) -> float:
        """
        Predict execution time for an order.
        
        Args:
            exchange: Exchange name
            order_size: Size of the order
            
        Returns:
            Predicted execution time in milliseconds
        """
        base_latency = self.get_exchange_latency(exchange)
        
        # Add size-based adjustment (larger orders may take longer)
        size_factor = 1.0 + (order_size / 10000) * 0.1  # 10% increase per 10k units
        
        # Add time-of-day adjustment
        hour = datetime.now().hour
        time_factor = 1.0
        if 14 <= hour <= 16:  # US market hours
            time_factor = 1.2  # 20% increase during peak hours
        
        return base_latency * size_factor * time_factor
    
    def should_retry_exchange(self, exchange: str) -> bool:
        """
        Determine if an exchange should be retried based on recent performance.
        
        Args:
            exchange: Exchange name
            
        Returns:
            True if exchange should be retried
        """
        metrics = self.get_exchange_metrics(exchange)
        
        # Don't retry if success rate is too low
        if metrics['success_rate'] < 0.5:  # Less than 50% success
            return False
        
        # Don't retry if latency is consistently high
        if metrics['avg_latency'] > self.max_retry_latency_ms:
            return False
        
        return True
    
    def _update_exchange_metrics(self, exchange: str) -> None:
        """
        Update metrics for an exchange based on recent history.
        
        Args:
            exchange: Exchange name
        """
        history = self.latency_history.get(exchange, [])
        
        if not history:
            self.exchange_metrics[exchange] = self._get_default_metrics()
            return
        
        # Calculate metrics from recent history
        recent_window = 300  # 5 minutes
        current_time = time.time()
        recent_records = [
            r for r in history 
            if current_time - r['timestamp'] < recent_window
        ]
        
        if not recent_records:
            recent_records = list(history)[-100:]  # Last 100 records
        
        # Calculate metrics
        latencies = [r['latency_ms'] for r in recent_records]
        successes = [r['success'] for r in recent_records]
        
        metrics = {
            'avg_latency': sum(latencies) / len(latencies),
            'min_latency': min(latencies),
            'max_latency': max(latencies),
            'success_rate': sum(successes) / len(successes),
            'sample_count': len(recent_records),
            'last_updated': current_time
        }
        
        # Calculate percentiles
        sorted_latencies = sorted(latencies)
        metrics['p50_latency'] = sorted_latencies[len(sorted_latencies) // 2]
        metrics['p95_latency'] = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        metrics['p99_latency'] = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        
        self.exchange_metrics[exchange] = metrics
    
    def _get_default_metrics(self) -> Dict[str, Any]:
        """Get default metrics for an exchange with no history."""
        return {
            'avg_latency': 100,
            'min_latency': 100,
            'max_latency': 100,
            'p50_latency': 100,
            'p95_latency': 150,
            'p99_latency': 200,
            'success_rate': 1.0,
            'sample_count': 0,
            'last_updated': time.time()
        }
    
    def _adjust_for_high_latency(self, 
                               params: Dict[str, Any], 
                               metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adjust parameters for high latency conditions.
        
        Args:
            params: Current parameters
            metrics: Exchange metrics
            
        Returns:
            Adjusted parameters
        """
        adjusted = params.copy()
        
        # Increase timeout for high latency
        if 'timeout' in adjusted:
            adjusted['timeout'] = max(
                adjusted['timeout'],
                metrics['p95_latency'] * 2 / 1000  # Convert to seconds
            )
        
        # Reduce request size if possible
        if 'batch_size' in adjusted and adjusted['batch_size'] > 1:
            adjusted['batch_size'] = max(1, adjusted['batch_size'] // 2)
        
        # Enable compression
        adjusted['enable_compression'] = True
        
        return adjusted
    
    def _calculate_optimal_send_time(self, exchange: str) -> float:
        """
        Calculate optimal time to send order based on patterns.
        
        Args:
            exchange: Exchange name
            
        Returns:
            Optimal send time (Unix timestamp)
        """
        # For now, return current time
        # In production, this would analyze patterns to find optimal times
        return time.time()
    
    def _get_connection_pool_id(self, exchange: str) -> str:
        """
        Get connection pool ID for an exchange.
        
        Args:
            exchange: Exchange name
            
        Returns:
            Connection pool ID
        """
        # Simple round-robin for now
        if exchange not in self.connection_pools:
            self.connection_pools[exchange] = 0
        
        pool_id = self.connection_pools[exchange] % self.max_connections
        self.connection_pools[exchange] += 1
        
        return f"{exchange}_pool_{pool_id}"
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive optimization report.
        
        Returns:
            Optimization metrics and recommendations
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'target_latency_ms': self.target_latency_ms,
            'exchanges': {}
        }
        
        for exchange, metrics in self.exchange_metrics.items():
            report['exchanges'][exchange] = {
                'avg_latency': metrics['avg_latency'],
                'success_rate': metrics['success_rate'],
                'status': self._get_exchange_status(metrics),
                'recommendation': self._get_exchange_recommendation(metrics)
            }
        
        return report
    
    def _get_exchange_status(self, metrics: Dict[str, Any]) -> str:
        """Get status string for exchange based on metrics."""
        if metrics['avg_latency'] <= self.target_latency_ms:
            return 'optimal'
        elif metrics['avg_latency'] <= self.target_latency_ms * 2:
            return 'acceptable'
        elif metrics['avg_latency'] <= self.max_retry_latency_ms:
            return 'degraded'
        else:
            return 'critical'
    
    def _get_exchange_recommendation(self, metrics: Dict[str, Any]) -> str:
        """Get recommendation for exchange based on metrics."""
        if metrics['avg_latency'] <= self.target_latency_ms:
            return 'No action needed'
        elif metrics['success_rate'] < 0.8:
            return 'Consider failover to alternative exchange'
        elif metrics['avg_latency'] > self.max_retry_latency_ms:
            return 'Avoid this exchange until performance improves'
        else:
            return 'Monitor closely, consider reducing order frequency'
    
    async def run_latency_test(self, exchange: str, test_func) -> Dict[str, Any]:
        """
        Run a latency test for an exchange.
        
        Args:
            exchange: Exchange name
            test_func: Async function to test
            
        Returns:
            Test results
        """
        results = []
        
        for i in range(5):  # Run 5 tests
            start_time = time.time()
            try:
                await test_func()
                latency_ms = (time.time() - start_time) * 1000
                results.append(latency_ms)
                self.record_latency(exchange, latency_ms, success=True)
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                self.record_latency(exchange, latency_ms, success=False)
                self.logger.error(f"Latency test failed: {str(e)}")
            
            await asyncio.sleep(0.1)  # Small delay between tests
        
        if results:
            return {
                'exchange': exchange,
                'avg_latency': sum(results) / len(results),
                'min_latency': min(results),
                'max_latency': max(results),
                'success_rate': len(results) / 5,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'exchange': exchange,
                'error': 'All tests failed',
                'timestamp': datetime.now().isoformat()
            }