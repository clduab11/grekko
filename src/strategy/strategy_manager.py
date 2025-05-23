import logging
from .strategies.arbitrage_strategy import ArbitrageStrategy
from .strategies.mean_reversion_strategy import MeanReversionStrategy
from .strategies.momentum_strategy import MomentumStrategy
from .strategies.sentiment_strategy import SentimentStrategy
from ..ai_adaptation.ml_models.model_trainer import ModelTrainer
from ..utils.credentials_manager import CredentialsManager
from ..utils.logger import get_logger

class StrategyManager:
    def __init__(self, exchange='binance'):
        """
        Initialize the strategy manager with secure credential management.
        
        Args:
            exchange (str): The exchange to use for trading strategies
        """
        self.logger = get_logger('strategy_manager')
        self.exchange = exchange
        
        # Initialize credentials manager and get secure credentials
        try:
            cred_manager = CredentialsManager()
            credentials = cred_manager.get_credentials(exchange)
            self.api_key = credentials['api_key']
            self.api_secret = credentials['api_secret']
            
            # Initialize strategies with secure credentials
            self.strategies = {
                'arbitrage': ArbitrageStrategy(self.api_key, self.api_secret),
                'mean_reversion': MeanReversionStrategy(lookback_period=20, entry_threshold=0.05, exit_threshold=0.02),
                'momentum': MomentumStrategy(lookback_period=20, entry_threshold=0.05, exit_threshold=0.02),
                'sentiment': SentimentStrategy(sentiment_threshold=0.1)
            }
            self.logger.info(f"Initialized strategies with secure credentials for {exchange}")
        except Exception as e:
            self.logger.error(f"Failed to initialize strategies with secure credentials: {str(e)}")
            # Initialize with empty strategies as fallback
            self.strategies = {}
            
        self.current_strategy = None
        self.model_trainer = ModelTrainer()

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

    def add_ml_strategy(self, strategy_name, model_filepath, **params):
        self.model_trainer.load_training_data(model_filepath)
        self.model_trainer.set_training_parameters(**params)
        self.model_trainer.train_model()
        self.strategies[strategy_name] = self.model_trainer.model
        self.logger.info(f"Added machine learning-based strategy: {strategy_name}")
