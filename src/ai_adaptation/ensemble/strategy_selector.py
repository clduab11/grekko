"""
Strategy selection module for the Grekko trading platform.

This module implements the StrategySelector class that uses insights
from the LLM ensemble to select the optimal trading strategy for
current market conditions.
"""
import logging
import pandas as pd
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from ...utils.logger import get_logger
from ...utils.metrics import track_latency
from .performance_tracker import PerformanceTracker
from .llm_ensemble import LLMEnsemble

class StrategyType(Enum):
    """Types of trading strategies supported by the platform."""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    ARBITRAGE = "arbitrage"
    SENTIMENT = "sentiment"
    HOLD = "hold"  # No active strategy

class StrategyScore:
    """Container for strategy scores with market regime compatibility."""
    def __init__(self, strategy_type: StrategyType, base_score: float, 
                 market_regime_score: float, confidence: float):
        self.strategy_type = strategy_type
        self.base_score = base_score
        self.market_regime_score = market_regime_score
        self.confidence = confidence
        
    @property
    def combined_score(self) -> float:
        """Calculate the combined score with market regime weight."""
        # Weight base score more heavily but still consider market regime
        return (self.base_score * 0.7) + (self.market_regime_score * 0.3)

class StrategySelector:
    """
    Strategy selector that determines the optimal trading strategy.
    
    This class uses the LLM ensemble's analysis to select the most appropriate
    trading strategy for the current market conditions. It considers market
    regime, technical analysis, sentiment, and risk factors to make this
    determination.
    
    Attributes:
        llm_ensemble (LLMEnsemble): LLM ensemble for market analysis
        available_strategies (Dict[str, Any]): Available strategy instances
        current_strategy (str): Currently active strategy name
        market_regime (str): Current market regime classification
        logger (logging.Logger): Logger for strategy selection events
        performance_tracker (PerformanceTracker): Tracks strategy performance
    """
    
    def __init__(self, llm_ensemble: Optional[LLMEnsemble] = None):
        """
        Initialize the strategy selector.
        
        Args:
            llm_ensemble (Optional[LLMEnsemble]): LLM ensemble for market analysis
        """
        self.llm_ensemble = llm_ensemble
        self.available_strategies = {}
        self.current_strategy = None
        self.market_regime = "unknown"
        
        self.logger = get_logger('strategy_selector')
        self.performance_tracker = PerformanceTracker()
        self.logger.info("Strategy selector initialized")
        
        # Strategy performance tracking
        self.strategy_performance = {
            StrategyType.MOMENTUM.value: {"wins": 0, "losses": 0, "pnl": 0.0},
            StrategyType.MEAN_REVERSION.value: {"wins": 0, "losses": 0, "pnl": 0.0},
            StrategyType.ARBITRAGE.value: {"wins": 0, "losses": 0, "pnl": 0.0},
            StrategyType.SENTIMENT.value: {"wins": 0, "losses": 0, "pnl": 0.0},
        }
        
        # Market regime compatibility matrix
        self.regime_compatibility = {
            "bull": {
                StrategyType.MOMENTUM.value: 0.9,
                StrategyType.MEAN_REVERSION.value: 0.3,
                StrategyType.ARBITRAGE.value: 0.7,
                StrategyType.SENTIMENT.value: 0.6,
            },
            "bear": {
                StrategyType.MOMENTUM.value: 0.3,
                StrategyType.MEAN_REVERSION.value: 0.7,
                StrategyType.ARBITRAGE.value: 0.7,
                StrategyType.SENTIMENT.value: 0.6,
            },
            "ranging": {
                StrategyType.MOMENTUM.value: 0.2,
                StrategyType.MEAN_REVERSION.value: 0.9,
                StrategyType.ARBITRAGE.value: 0.8,
                StrategyType.SENTIMENT.value: 0.5,
            },
            "volatile": {
                StrategyType.MOMENTUM.value: 0.4,
                StrategyType.MEAN_REVERSION.value: 0.5,
                StrategyType.ARBITRAGE.value: 0.7,
                StrategyType.SENTIMENT.value: 0.7,
            },
            "unknown": {
                StrategyType.MOMENTUM.value: 0.5,
                StrategyType.MEAN_REVERSION.value: 0.5,
                StrategyType.ARBITRAGE.value: 0.5,
                StrategyType.SENTIMENT.value: 0.5,
            }
        }
    
    def register_strategy(self, strategy_type: StrategyType, strategy_instance: Any) -> None:
        """
        Register a strategy with the selector.
        
        Args:
            strategy_type (StrategyType): Type of the strategy
            strategy_instance (Any): Instance of the strategy class
        """
        self.available_strategies[strategy_type.value] = strategy_instance
        self.logger.info(f"Registered strategy: {strategy_type.value}")
    
    def select_best_strategy(self) -> str:
        """
        Select the best strategy based on historical performance.
        
        Returns:
            str: Name of the selected strategy
        """
        metrics = self.performance_tracker.calculate_performance_metrics()
        if metrics.empty:
            self.logger.warning("No performance metrics available to select the best strategy.")
            return None

        best_strategy = metrics.loc[metrics['value'].idxmax()]['strategy']
        self.logger.info(f"Selected best strategy based on historical performance: {best_strategy}")
        return best_strategy
    
    @track_latency("select_strategy")
    async def select_strategy(self, 
                           market_data: Dict[str, Any],
                           current_positions: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Select the optimal strategy for current market conditions using LLM ensemble.
        
        Args:
            market_data (Dict[str, Any]): Current market data
            current_positions (Optional[List[Dict[str, Any]]]): Current positions
            
        Returns:
            Tuple[str, Dict[str, Any]]: (selected strategy name, selection metadata)
        """
        # Check if we have LLM ensemble available
        if not self.llm_ensemble:
            # Fall back to performance-based selection
            selected_strategy = self.select_best_strategy()
            if not selected_strategy:
                selected_strategy = StrategyType.MOMENTUM.value  # Default

            metadata = {
                "selected_strategy": selected_strategy,
                "selection_method": "performance_based",
                "timestamp": datetime.now().isoformat()
            }
            
            return selected_strategy, metadata
            
        # Get market analysis from LLM ensemble
        analysis = await self.llm_ensemble.analyze(
            market_data=market_data,
            current_positions=current_positions
        )
        
        # Update market regime
        if "market_regime" in analysis:
            self.market_regime = analysis["market_regime"].lower()
            self.logger.info(f"Market regime identified as: {self.market_regime}")
        
        # Calculate strategy scores
        strategy_scores = self._calculate_strategy_scores(analysis)
        
        # Sort strategies by combined score
        sorted_strategies = sorted(
            strategy_scores,
            key=lambda s: s.combined_score,
            reverse=True
        )
        
        # Select top strategy if above threshold
        if sorted_strategies and sorted_strategies[0].combined_score >= 0.6:
            selected_strategy = sorted_strategies[0].strategy_type.value
        else:
            # Default to hold if no strategy has a good score
            selected_strategy = StrategyType.HOLD.value
            
        # Check if we need to switch strategies
        if selected_strategy != self.current_strategy:
            self.logger.info(f"Switching strategy from {self.current_strategy} to {selected_strategy}")
            self.current_strategy = selected_strategy
        
        # Prepare metadata about the selection
        metadata = {
            "selected_strategy": selected_strategy,
            "selection_method": "llm_ensemble",
            "market_regime": self.market_regime,
            "strategy_scores": [
                {
                    "strategy": s.strategy_type.value,
                    "base_score": s.base_score,
                    "market_regime_score": s.market_regime_score,
                    "combined_score": s.combined_score,
                    "confidence": s.confidence
                }
                for s in sorted_strategies
            ],
            "timestamp": datetime.now().isoformat(),
            "analysis_summary": {
                "technical": analysis.get("technical_summary"),
                "sentiment": analysis.get("sentiment_summary"),
                "risk": analysis.get("risk_summary")
            }
        }
        
        return selected_strategy, metadata
    
    def update_strategy_selection(self):
        """Update the current strategy selection based on performance."""
        best_strategy = self.select_best_strategy()
        if best_strategy and best_strategy != self.current_strategy:
            self.logger.info(f"Updating strategy from {self.current_strategy} to {best_strategy}")
            self.current_strategy = best_strategy
        else:
            self.logger.info("No update needed for strategy selection.")
    
    def _calculate_strategy_scores(self, analysis: Dict[str, Any]) -> List[StrategyScore]:
        """
        Calculate scores for each strategy based on market analysis.
        
        Args:
            analysis (Dict[str, Any]): Market analysis from LLM ensemble
            
        Returns:
            List[StrategyScore]: Scored strategies
        """
        scores = []
        
        # Extract strategy recommendations if available
        strategy_recommendations = analysis.get("strategy_recommendations", {})
        
        # Calculate scores for each strategy
        for strategy_type in StrategyType:
            if strategy_type == StrategyType.HOLD:
                continue  # Skip HOLD as it's not a real strategy
                
            # Get base score from ensemble recommendation if available
            base_score = strategy_recommendations.get(strategy_type.value, {}).get("score", 0.5)
            
            # Get confidence from ensemble
            confidence = strategy_recommendations.get(strategy_type.value, {}).get("confidence", 0.5)
            
            # Get market regime compatibility score
            market_regime_score = self.regime_compatibility.get(
                self.market_regime, {}
            ).get(strategy_type.value, 0.5)
            
            # Apply performance adjustment based on recent results
            performance_adjustment = self._calculate_performance_adjustment(strategy_type.value)
            
            # Adjust base score with performance
            adjusted_base_score = min(1.0, base_score * (1.0 + performance_adjustment))
            
            scores.append(StrategyScore(
                strategy_type=strategy_type,
                base_score=adjusted_base_score,
                market_regime_score=market_regime_score,
                confidence=confidence
            ))
            
        return scores
    
    def _calculate_performance_adjustment(self, strategy_name: str) -> float:
        """
        Calculate performance adjustment based on strategy history.
        
        Args:
            strategy_name (str): Name of the strategy
            
        Returns:
            float: Adjustment factor (-0.2 to +0.2)
        """
        if strategy_name not in self.strategy_performance:
            return 0.0
            
        perf = self.strategy_performance[strategy_name]
        total = perf["wins"] + perf["losses"]
        
        if total < 5:
            # Not enough data for adjustment
            return 0.0
            
        # Calculate win rate
        win_rate = perf["wins"] / total if total > 0 else 0.5
        
        # Calculate PnL per trade
        pnl_per_trade = perf["pnl"] / total if total > 0 else 0.0
        
        # Adjust based on win rate and PnL
        # Range from -0.2 to +0.2
        adjustment = ((win_rate - 0.5) * 0.2) + (pnl_per_trade * 0.1)
        
        return max(-0.2, min(0.2, adjustment))
    
    def update_strategy_performance(self, strategy_name: str, profit_loss: float) -> None:
        """
        Update performance metrics for a strategy after a trade.
        
        Args:
            strategy_name (str): Name of the strategy
            profit_loss (float): Profit/loss from the trade
        """
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = {"wins": 0, "losses": 0, "pnl": 0.0}
            
        perf = self.strategy_performance[strategy_name]
        
        # Update metrics
        if profit_loss > 0:
            perf["wins"] += 1
        else:
            perf["losses"] += 1
            
        perf["pnl"] += profit_loss
        
        self.logger.info(f"Updated {strategy_name} performance: {perf['wins']} wins, {perf['losses']} losses, PnL: {perf['pnl']:.2f}")
        
        # Also update the performance tracker
        self.performance_tracker.add_performance_data(strategy_name, profit_loss)
    
    def get_strategy_instance(self, strategy_name: str) -> Optional[Any]:
        """
        Get a strategy instance by name.
        
        Args:
            strategy_name (str): Name of the strategy
            
        Returns:
            Optional[Any]: Strategy instance or None if not found
        """
        return self.available_strategies.get(strategy_name)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for all strategies.
        
        Returns:
            Dict[str, Any]: Strategy performance metrics
        """
        metrics = {}
        
        for strategy_name, perf in self.strategy_performance.items():
            total = perf["wins"] + perf["losses"]
            win_rate = perf["wins"] / total if total > 0 else 0.0
            
            metrics[strategy_name] = {
                "total_trades": total,
                "win_rate": win_rate,
                "total_pnl": perf["pnl"],
                "average_pnl": perf["pnl"] / total if total > 0 else 0.0
            }
            
        return metrics