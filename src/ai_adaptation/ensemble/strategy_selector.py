import logging
import pandas as pd
from .performance_tracker import PerformanceTracker

class StrategySelector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.performance_tracker = PerformanceTracker()
        self.current_strategy = None

    def select_best_strategy(self):
        metrics = self.performance_tracker.calculate_performance_metrics()
        if metrics.empty:
            self.logger.warning("No performance metrics available to select the best strategy.")
            return None

        best_strategy = metrics.loc[metrics['value'].idxmax()]['strategy']
        self.current_strategy = best_strategy
        self.logger.info(f"Selected best strategy: {best_strategy}")
        return best_strategy

    def update_strategy_selection(self):
        best_strategy = self.select_best_strategy()
        if best_strategy and best_strategy != self.current_strategy:
            self.logger.info(f"Updating strategy from {self.current_strategy} to {best_strategy}")
            self.current_strategy = best_strategy
        else:
            self.logger.info("No update needed for strategy selection.")
