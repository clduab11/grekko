import logging
from .strategies.arbitrage_strategy import ArbitrageStrategy
from .strategies.mean_reversion_strategy import MeanReversionStrategy
from .strategies.momentum_strategy import MomentumStrategy
from .strategies.sentiment_strategy import SentimentStrategy

class StrategyManager:
    def __init__(self, api_key, api_secret):
        self.logger = logging.getLogger(__name__)
        self.strategies = {
            'arbitrage': ArbitrageStrategy(api_key, api_secret),
            'mean_reversion': MeanReversionStrategy(lookback_period=20, entry_threshold=0.05, exit_threshold=0.02),
            'momentum': MomentumStrategy(lookback_period=20, entry_threshold=0.05, exit_threshold=0.02),
            'sentiment': SentimentStrategy(sentiment_threshold=0.1)
        }
        self.current_strategy = None

    def switch_strategy(self, strategy_name):
        if strategy_name in self.strategies:
            self.current_strategy = self.strategies[strategy_name]
            self.logger.info(f"Switched to {strategy_name} strategy")
        else:
            self.logger.error(f"Strategy {strategy_name} not found")

    def execute_current_strategy(self, market_data):
        if self.current_strategy:
            signal = self.current_strategy.identify_trade_signal(market_data)
            self.current_strategy.execute_trade(signal, amount=100)
        else:
            self.logger.error("No strategy selected")

    def update_strategy(self, strategy_name, **params):
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
            for param, value in params.items():
                setattr(strategy, param, value)
            self.logger.info(f"Updated {strategy_name} strategy with parameters: {params}")
        else:
            self.logger.error(f"Strategy {strategy_name} not found")
