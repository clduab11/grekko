import logging
import pandas as pd

class PerformanceTracker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.performance_data = pd.DataFrame(columns=['strategy', 'metric', 'value'])

    def track_performance(self, strategy, metric, value):
        self.performance_data = self.performance_data.append({'strategy': strategy, 'metric': metric, 'value': value}, ignore_index=True)
        self.logger.info(f"Tracked performance: {strategy} - {metric}: {value}")

    def calculate_performance_metrics(self):
        metrics = self.performance_data.groupby(['strategy', 'metric']).mean().reset_index()
        self.logger.info("Calculated performance metrics")
        return metrics

    def store_performance_metrics(self, filepath):
        self.performance_data.to_csv(filepath, index=False)
        self.logger.info(f"Stored performance metrics to {filepath}")
