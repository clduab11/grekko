"""
SpreadOptimizer: Dynamic spread optimization based on market volatility.
Implements logic as specified in docs/phase3_market_making_bot_pseudocode.md.
"""

from dataclasses import dataclass
from typing import Any

@dataclass
class SpreadOptimizerConfig:
    min_spread: float = 0.001
    max_spread: float = 0.01
    volatility_threshold: float = 0.05
    default_spread: float = 0.002

class SpreadOptimizer:
    """
    Optimizes bid/ask spreads dynamically based on volatility and market conditions.
    """

    def __init__(self, config: SpreadOptimizerConfig):
        # TEST: Spread optimizer initialization
        self.config = config

    def calculate_spread(self, volatility: float, liquidity: float, trend_strength: float) -> float:
        """
        Calculate optimal spread based on current market volatility, liquidity, and trend.
        """
        # TEST: Spread calculation based on volatility
        if volatility > self.config.volatility_threshold:
            spread = min(self.config.max_spread, self.config.default_spread * (1 + volatility * 5))
        else:
            spread = max(self.config.min_spread, self.config.default_spread * (1 - liquidity / 10000))
        # TEST: Spread adjustment for strong trends
        if trend_strength > 0.7:
            spread *= 1.1
        return round(spread, 6)

    def optimize_for_pair(self, market_analysis: Any) -> float:
        """
        Optimize spread for a specific trading pair using market analysis data.
        """
        # TEST: Integration with predictive models and sentiment analysis
        volatility = getattr(market_analysis, "volatility", 0.0)
        liquidity = getattr(market_analysis, "liquidity", 1000.0)
        trend_strength = getattr(market_analysis, "trend_strength", 0.0)
        return self.calculate_spread(volatility, liquidity, trend_strength)