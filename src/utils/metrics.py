"""
Metrics utilities for the Grekko platform.

This module provides tools for tracking performance metrics throughout the system,
such as latency, API calls, success rates, and more.
"""
import time
import functools
import inspect
import logging
from typing import Dict, Any, Callable, Awaitable
from contextlib import contextmanager

from .logger import get_logger

# Global dictionary to store metrics
_metrics_store = {
    "latency": {},  # Method latency measurements
    "api_calls": {},  # External API call counts
    "success_rates": {},  # Success rates for operations
    "token_usage": {},  # LLM token usage
}

# Configure logger
logger = get_logger('metrics')

def track_latency(metric_name: str = None):
    """
    Decorator to track the latency of a function.
    
    Can be used with both synchronous and asynchronous functions.
    
    Args:
        metric_name (str, optional): Name of the metric. If None, uses function name.
    
    Returns:
        Function decorator
    """
    def decorator(func):
        nonlocal metric_name
        if metric_name is None:
            metric_name = func.__name__
            
        # Initialize metric if it doesn't exist
        if metric_name not in _metrics_store["latency"]:
            _metrics_store["latency"][metric_name] = {
                "count": 0,
                "total_time": 0,
                "avg_time": 0,
                "min_time": float('inf'),
                "max_time": 0,
            }
            
        # Check if the function is async
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    elapsed = time.time() - start_time
                    _update_latency_metric(metric_name, elapsed)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    elapsed = time.time() - start_time
                    _update_latency_metric(metric_name, elapsed)
            return sync_wrapper
            
    return decorator

@contextmanager
def measure_time(metric_name: str):
    """
    Context manager to measure the execution time of a code block.
    
    Args:
        metric_name (str): Name of the metric to update
    """
    start_time = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        _update_latency_metric(metric_name, elapsed)

def _update_latency_metric(metric_name: str, elapsed: float):
    """
    Update latency metrics for a given metric name.
    
    Args:
        metric_name (str): Name of the metric
        elapsed (float): Elapsed time in seconds
    """
    metric = _metrics_store["latency"][metric_name]
    metric["count"] += 1
    metric["total_time"] += elapsed
    metric["avg_time"] = metric["total_time"] / metric["count"]
    metric["min_time"] = min(metric["min_time"], elapsed)
    metric["max_time"] = max(metric["max_time"], elapsed)
    
    # Log slow operations
    if elapsed > 1.0:  # Log operations taking more than 1 second
        logger.debug(f"Slow operation: {metric_name} took {elapsed:.2f}s")

def track_api_call(api_name: str, success: bool = True):
    """
    Track an API call to an external service.
    
    Args:
        api_name (str): Name of the API
        success (bool): Whether the call was successful
    """
    if api_name not in _metrics_store["api_calls"]:
        _metrics_store["api_calls"][api_name] = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "success_rate": 1.0,
        }
        
    metric = _metrics_store["api_calls"][api_name]
    metric["total"] += 1
    
    if success:
        metric["successful"] += 1
    else:
        metric["failed"] += 1
        
    metric["success_rate"] = metric["successful"] / metric["total"]

def track_token_usage(model: str, input_tokens: int, output_tokens: int):
    """
    Track token usage for language models.
    
    Args:
        model (str): Name of the model
        input_tokens (int): Number of input tokens
        output_tokens (int): Number of output tokens
    """
    if model not in _metrics_store["token_usage"]:
        _metrics_store["token_usage"][model] = {
            "calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }
        
    metric = _metrics_store["token_usage"][model]
    metric["calls"] += 1
    metric["input_tokens"] += input_tokens
    metric["output_tokens"] += output_tokens
    metric["total_tokens"] += input_tokens + output_tokens

def get_all_metrics() -> Dict[str, Any]:
    """
    Get all metrics data.
    
    Returns:
        Dict[str, Any]: Copy of all metrics
    """
    return {k: v.copy() for k, v in _metrics_store.items()}

def get_metric(category: str, name: str) -> Dict[str, Any]:
    """
    Get a specific metric.
    
    Args:
        category (str): Metric category (latency, api_calls, etc.)
        name (str): Metric name
        
    Returns:
        Dict[str, Any]: Metric data or empty dict if not found
    """
    if category in _metrics_store and name in _metrics_store[category]:
        return _metrics_store[category][name].copy()
    return {}

def reset_metrics(category: str = None, name: str = None):
    """
    Reset metrics data.
    
    Args:
        category (str, optional): Category to reset. If None, resets all categories.
        name (str, optional): Specific metric name to reset. If None, resets all in category.
    """
    if category is None:
        # Reset all metrics
        for cat in _metrics_store:
            _metrics_store[cat] = {}
    elif category in _metrics_store:
        if name is None:
            # Reset category
            _metrics_store[category] = {}
        elif name in _metrics_store[category]:
            # Reset specific metric
            if category == "latency":
                _metrics_store[category][name] = {
                    "count": 0,
                    "total_time": 0,
                    "avg_time": 0,
                    "min_time": float('inf'),
                    "max_time": 0,
                }
            elif category == "api_calls":
                _metrics_store[category][name] = {
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "success_rate": 1.0,
                }
            elif category == "token_usage":
                _metrics_store[category][name] = {
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                }
            else:
                _metrics_store[category][name] = {}

def log_metrics_summary():
    """Log a summary of all metrics to the logger."""
    logger.info("Metrics Summary:")
    
    # Log latency metrics
    if _metrics_store["latency"]:
        logger.info("Latency Metrics:")
        for name, data in _metrics_store["latency"].items():
            logger.info(f"  {name}: avg={data['avg_time']:.3f}s, min={data['min_time']:.3f}s, max={data['max_time']:.3f}s, count={data['count']}")
    
    # Log API call metrics
    if _metrics_store["api_calls"]:
        logger.info("API Call Metrics:")
        for name, data in _metrics_store["api_calls"].items():
            logger.info(f"  {name}: success_rate={data['success_rate']:.2%}, total={data['total']}, failed={data['failed']}")
    
    # Log token usage metrics
    if _metrics_store["token_usage"]:
        logger.info("Token Usage Metrics:")
        for name, data in _metrics_store["token_usage"].items():
            logger.info(f"  {name}: calls={data['calls']}, input={data['input_tokens']}, output={data['output_tokens']}, total={data['total_tokens']}")
            
    # Calculate cost estimates for token usage
    total_cost = 0.0
    if _metrics_store["token_usage"]:
        for model, data in _metrics_store["token_usage"].items():
            # Approximate costs
            if "gpt-4" in model:
                input_cost = data["input_tokens"] * 0.03 / 1000  # $0.03 per 1K tokens
                output_cost = data["output_tokens"] * 0.06 / 1000  # $0.06 per 1K tokens
            elif "gpt-3.5" in model:
                input_cost = data["input_tokens"] * 0.0015 / 1000  # $0.0015 per 1K tokens
                output_cost = data["output_tokens"] * 0.002 / 1000  # $0.002 per 1K tokens
            elif "claude-3-opus" in model:
                input_cost = data["input_tokens"] * 0.015 / 1000  # $0.015 per 1K tokens
                output_cost = data["output_tokens"] * 0.075 / 1000  # $0.075 per 1K tokens
            elif "claude-3-sonnet" in model or "claude-3-5-sonnet" in model:
                input_cost = data["input_tokens"] * 0.003 / 1000  # $0.003 per 1K tokens
                output_cost = data["output_tokens"] * 0.015 / 1000  # $0.015 per 1K tokens
            else:
                input_cost = data["input_tokens"] * 0.01 / 1000  # default
                output_cost = data["output_tokens"] * 0.03 / 1000  # default
                
            model_cost = input_cost + output_cost
            total_cost += model_cost
            logger.info(f"  {model} estimated cost: ${model_cost:.2f}")
            
        logger.info(f"Total estimated LLM cost: ${total_cost:.2f}")