"""
High-performance caching layer for the Grekko trading platform.

Implements multiple caching strategies to reduce latency and improve
performance for high-frequency trading operations.
"""
import time
import asyncio
import pickle
from typing import Dict, Any, Optional, Callable, Union
from collections import OrderedDict
from functools import wraps
import hashlib
import json

from .logger import get_logger


class CacheStrategy:
    """Base cache strategy interface."""
    
    def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        raise NotImplementedError
    
    def delete(self, key: str) -> None:
        raise NotImplementedError
    
    def clear(self) -> None:
        raise NotImplementedError
    
    def exists(self, key: str) -> bool:
        raise NotImplementedError


class LRUCache(CacheStrategy):
    """
    Least Recently Used (LRU) cache implementation.
    
    Optimized for frequently accessed data with automatic eviction
    of least recently used items.
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.timestamps = {}
        self.logger = get_logger('lru_cache')
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            # Check if expired
            if key in self.timestamps:
                expiry = self.timestamps[key]
                if expiry and time.time() > expiry:
                    self.delete(key)
                    return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest = next(iter(self.cache))
            self.delete(oldest)
        
        self.cache[key] = value
        self.cache.move_to_end(key)
        
        if ttl:
            self.timestamps[key] = time.time() + ttl
        elif key in self.timestamps:
            del self.timestamps[key]
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        if key in self.cache:
            del self.cache[key]
        if key in self.timestamps:
            del self.timestamps[key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.timestamps.clear()
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        if key in self.cache:
            if key in self.timestamps:
                if time.time() > self.timestamps[key]:
                    self.delete(key)
                    return False
            return True
        return False


class TTLCache(CacheStrategy):
    """
    Time-To-Live cache implementation.
    
    All entries have expiration times and are automatically cleaned up.
    """
    
    def __init__(self, default_ttl: int = 300, cleanup_interval: int = 60):
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        self.cache = {}
        self.timestamps = {}
        self.logger = get_logger('ttl_cache')
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_expired())
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key in self.cache:
            if time.time() <= self.timestamps[key]:
                return self.cache[key]
            else:
                self.delete(key)
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value with TTL."""
        ttl = ttl or self.default_ttl
        self.cache[key] = value
        self.timestamps[key] = time.time() + ttl
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.timestamps.clear()
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return key in self.cache and time.time() <= self.timestamps[key]
    
    async def _cleanup_expired(self) -> None:
        """Periodically clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                current_time = time.time()
                expired_keys = [
                    key for key, expiry in self.timestamps.items()
                    if current_time > expiry
                ]
                for key in expired_keys:
                    self.delete(key)
                
                if expired_keys:
                    self.logger.debug(f"Cleaned up {len(expired_keys)} expired entries")
            except Exception as e:
                self.logger.error(f"Error in cache cleanup: {str(e)}")


class LayeredCache:
    """
    Multi-layer cache system for optimal performance.
    
    Implements L1 (memory) and L2 (persistent) caching with
    automatic promotion/demotion of entries.
    """
    
    def __init__(self, 
                 l1_size: int = 100,
                 l2_size: int = 1000,
                 promotion_threshold: int = 3):
        self.l1_cache = LRUCache(max_size=l1_size)
        self.l2_cache = LRUCache(max_size=l2_size)
        self.promotion_threshold = promotion_threshold
        self.access_counts = {}
        self.logger = get_logger('layered_cache')
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from layered cache."""
        # Check L1 first
        value = self.l1_cache.get(key)
        if value is not None:
            return value
        
        # Check L2
        value = self.l2_cache.get(key)
        if value is not None:
            # Track access for promotion
            self.access_counts[key] = self.access_counts.get(key, 0) + 1
            
            # Promote to L1 if accessed frequently
            if self.access_counts[key] >= self.promotion_threshold:
                self.l1_cache.set(key, value)
                del self.access_counts[key]
            
            return value
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, tier: str = 'l2') -> None:
        """Set value in specified cache tier."""
        if tier == 'l1':
            self.l1_cache.set(key, value, ttl)
        else:
            self.l2_cache.set(key, value, ttl)
    
    def delete(self, key: str) -> None:
        """Delete from all cache layers."""
        self.l1_cache.delete(key)
        self.l2_cache.delete(key)
        if key in self.access_counts:
            del self.access_counts[key]
    
    def clear(self) -> None:
        """Clear all cache layers."""
        self.l1_cache.clear()
        self.l2_cache.clear()
        self.access_counts.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'l1_size': len(self.l1_cache.cache),
            'l2_size': len(self.l2_cache.cache),
            'pending_promotions': len(self.access_counts),
            'l1_capacity': self.l1_cache.max_size,
            'l2_capacity': self.l2_cache.max_size
        }


class CacheManager:
    """
    Central cache management system for Grekko.
    
    Provides unified interface for different caching strategies
    and cache decorators for functions.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger('cache_manager')
        
        # Initialize caches
        self.caches = {
            'market_data': LayeredCache(
                l1_size=config.get('market_data_l1_size', 50),
                l2_size=config.get('market_data_l2_size', 500)
            ),
            'orderbook': TTLCache(
                default_ttl=config.get('orderbook_ttl', 1),  # 1 second for orderbook
                cleanup_interval=5
            ),
            'api_responses': LRUCache(
                max_size=config.get('api_cache_size', 1000)
            ),
            'calculations': LRUCache(
                max_size=config.get('calc_cache_size', 500)
            )
        }
        
        # Performance metrics
        self.metrics = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
    
    def get(self, cache_name: str, key: str) -> Optional[Any]:
        """Get value from named cache."""
        if cache_name not in self.caches:
            self.logger.warning(f"Unknown cache: {cache_name}")
            return None
        
        value = self.caches[cache_name].get(key)
        
        if value is not None:
            self.metrics['hits'] += 1
        else:
            self.metrics['misses'] += 1
        
        return value
    
    def set(self, cache_name: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in named cache."""
        if cache_name not in self.caches:
            self.logger.warning(f"Unknown cache: {cache_name}")
            return
        
        self.caches[cache_name].set(key, value, ttl)
        self.metrics['sets'] += 1
    
    def delete(self, cache_name: str, key: str) -> None:
        """Delete key from named cache."""
        if cache_name not in self.caches:
            return
        
        self.caches[cache_name].delete(key)
        self.metrics['deletes'] += 1
    
    def clear(self, cache_name: Optional[str] = None) -> None:
        """Clear specified cache or all caches."""
        if cache_name:
            if cache_name in self.caches:
                self.caches[cache_name].clear()
        else:
            for cache in self.caches.values():
                cache.clear()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics."""
        total_operations = self.metrics['hits'] + self.metrics['misses']
        hit_rate = self.metrics['hits'] / total_operations if total_operations > 0 else 0
        
        return {
            **self.metrics,
            'hit_rate': hit_rate,
            'total_operations': total_operations,
            'cache_stats': {
                name: cache.get_stats() if hasattr(cache, 'get_stats') else {}
                for name, cache in self.caches.items()
            }
        }
    
    def cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()


def cached(cache_name: str, ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """
    Decorator for caching function results.
    
    Args:
        cache_name: Name of cache to use
        ttl: Time to live in seconds
        key_func: Custom function to generate cache key
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get cache manager (assumed to be available globally or via injection)
            cache_manager = kwargs.pop('_cache_manager', None)
            if not cache_manager:
                return await func(*args, **kwargs)
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager.cache_key(func.__name__, *args, **kwargs)
            
            # Check cache
            cached_value = cache_manager.get(cache_name, cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            cache_manager.set(cache_name, cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Get cache manager
            cache_manager = kwargs.pop('_cache_manager', None)
            if not cache_manager:
                return func(*args, **kwargs)
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager.cache_key(func.__name__, *args, **kwargs)
            
            # Check cache
            cached_value = cache_manager.get(cache_name, cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_name, cache_key, result, ttl)
            
            return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class OrderbookCache:
    """
    Specialized cache for orderbook data with microsecond precision.
    
    Optimized for HFT requirements with lock-free operations.
    """
    
    def __init__(self, max_depth: int = 20, ttl_ms: int = 100):
        self.max_depth = max_depth
        self.ttl_ms = ttl_ms
        self.cache = {}
        self.logger = get_logger('orderbook_cache')
    
    def update(self, exchange: str, symbol: str, orderbook: Dict[str, Any]) -> None:
        """Update orderbook with timestamp."""
        key = f"{exchange}:{symbol}"
        self.cache[key] = {
            'data': self._trim_orderbook(orderbook),
            'timestamp': time.time() * 1000  # Millisecond precision
        }
    
    def get(self, exchange: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get orderbook if not stale."""
        key = f"{exchange}:{symbol}"
        if key in self.cache:
            entry = self.cache[key]
            age_ms = (time.time() * 1000) - entry['timestamp']
            
            if age_ms <= self.ttl_ms:
                return entry['data']
            else:
                del self.cache[key]
        
        return None
    
    def _trim_orderbook(self, orderbook: Dict[str, Any]) -> Dict[str, Any]:
        """Trim orderbook to max depth for efficiency."""
        return {
            'bids': orderbook.get('bids', [])[:self.max_depth],
            'asks': orderbook.get('asks', [])[:self.max_depth],
            'timestamp': orderbook.get('timestamp')
        }
    
    def get_age_ms(self, exchange: str, symbol: str) -> Optional[float]:
        """Get age of cached orderbook in milliseconds."""
        key = f"{exchange}:{symbol}"
        if key in self.cache:
            return (time.time() * 1000) - self.cache[key]['timestamp']
        return None