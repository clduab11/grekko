"""
CrossChainPriceDiscovery: Real-time price comparison across multiple blockchains.

Implements the PriceAggregator logic from the Phase 2 cross-chain arbitrage pseudocode.
Handles price aggregation, caching, and error resilience for DEX, oracle, and CEX sources.

TDD anchors and docstrings included for future test coverage.
"""

import statistics
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("CrossChainPriceDiscovery")

class PriceCache:
    """Simple in-memory cache with TTL for price data."""
    def __init__(self, ttl: int = 30):
        self.ttl = ttl
        self.cache: Dict[str, Any] = {}
        self.timestamps: Dict[str, int] = {}

    def get(self, key: str) -> Optional[float]:
        import time
        now = int(time.time())
        if key in self.cache and now - self.timestamps[key] < self.ttl:
            return self.cache[key]
        return None

    def set(self, key: str, value: float) -> None:
        import time
        self.cache[key] = value
        self.timestamps[key] = int(time.time())

class CrossChainPriceDiscovery:
    """
    Aggregates and normalizes asset prices across multiple chains and sources.
    Integrates with chain integrator for DEX/oracle access.
    """

    def __init__(self, price_sources: Dict[str, List[Dict[str, Any]]], chain_integrator: Any):
        """
        Initialize with price source configs and chain integrator.
        TDD: Price aggregator initializes with valid sources.
        """
        self.price_sources = price_sources
        self.chain_integrator = chain_integrator
        self.price_cache = PriceCache(ttl=30)

    def get_cross_chain_prices(self, asset_symbol: str) -> Dict[str, float]:
        """
        Returns a mapping of chain_id -> median price for the asset.
        TDD: Returns accurate cross-chain data, handles source failures gracefully.
        """
        chain_prices: Dict[str, float] = {}
        for chain_id in self.chain_integrator.get_active_chains():
            try:
                cache_key = f"price_{chain_id}_{asset_symbol}"
                cached_price = self.price_cache.get(cache_key)
                if cached_price is not None:
                    chain_prices[chain_id] = cached_price
                    continue

                chain_price_sources = self.price_sources.get(chain_id, [])
                prices = []
                for source_config in chain_price_sources:
                    try:
                        price = self.get_price_from_source(chain_id, asset_symbol, source_config)
                        if price and price > 0:
                            prices.append(price)
                    except Exception as e:
                        logger.warning(f"Failed to get price from {source_config.get('name', 'unknown')} on {chain_id}: {e}")
                        continue
                if prices:
                    median_price = statistics.median(prices)
                    chain_prices[chain_id] = median_price
                    self.price_cache.set(cache_key, median_price)
            except Exception as e:
                logger.error(f"Failed to get prices for {asset_symbol} on {chain_id}: {e}")
                continue
        return chain_prices

    def get_price_from_source(self, chain_id: str, asset_symbol: str, source_config: Dict[str, Any]) -> float:
        """
        Query a single price source (DEX, oracle, CEX).
        TDD: Handles various protocols and error cases.
        """
        source_type = source_config['type']
        if source_type == 'dex':
            return self.get_dex_price(chain_id, asset_symbol, source_config)
        elif source_type == 'oracle':
            return self.get_oracle_price(chain_id, asset_symbol, source_config)
        elif source_type == 'cex':
            return self.get_cex_price(asset_symbol, source_config)
        else:
            raise ValueError(f"Unsupported price source type: {source_type}")

    def get_dex_price(self, chain_id: str, asset_symbol: str, source_config: Dict[str, Any]) -> float:
        """
        Query price from a DEX protocol.
        TDD: Handles liquidity, slippage, and pair existence.
        """
        dex_client = self.chain_integrator.get_dex_client(chain_id, source_config['protocol'])
        base_token = source_config.get('base_token', 'USDC')
        pair_address = dex_client.get_pair_address(asset_symbol, base_token)
        if not pair_address:
            raise ValueError(f"No {asset_symbol}/{base_token} pair found")
        reserves = dex_client.get_pair_reserves(pair_address)
        if reserves.token0_symbol == asset_symbol:
            price = reserves.token1_reserve / reserves.token0_reserve
        else:
            price = reserves.token0_reserve / reserves.token1_reserve
        return price

    def get_oracle_price(self, chain_id: str, asset_symbol: str, source_config: Dict[str, Any]) -> float:
        """
        Query price from an on-chain oracle.
        TDD: Handles feed availability and staleness.
        """
        oracle_client = self.chain_integrator.get_oracle_client(chain_id, source_config['protocol'])
        price_feed_address = source_config.get('feed_address') or oracle_client.get_price_feed_address(asset_symbol)
        if not price_feed_address:
            raise ValueError(f"No price feed found for {asset_symbol}")
        price_data = oracle_client.get_latest_price(price_feed_address)
        if not getattr(price_data, "is_valid", False):
            raise ValueError("Oracle price data is stale")
        return price_data.price

    def get_cex_price(self, asset_symbol: str, source_config: Dict[str, Any]) -> float:
        """
        Query price from a centralized exchange API.
        TDD: Handles API errors and symbol mapping.
        """
        cex_client = source_config['client']
        return cex_client.get_price(asset_symbol)