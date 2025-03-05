import logging
import yaml
import pandas as pd
from strategy.strategy_manager import StrategyManager

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def initialize_logging(log_level):
    logging.basicConfig(level=log_level)
    logger = logging.getLogger(__name__)
    return logger

def load_historical_data(filepath):
    data = pd.read_csv(filepath)
    return data

def backtest_strategy(strategy_manager, historical_data):
    results = []
    for index, row in historical_data.iterrows():
        market_data = row.to_dict()
        strategy_manager.execute_current_strategy(market_data)
        results.append(strategy_manager.current_strategy.performance_metrics)
    return results

def optimize_strategy_parameters(strategy_manager, historical_data):
    best_params = None
    best_performance = float('-inf')
    for params in strategy_manager.get_parameter_combinations():
        strategy_manager.update_strategy(strategy_manager.current_strategy_name, **params)
        performance = backtest_strategy(strategy_manager, historical_data)
        if performance > best_performance:
            best_performance = performance
            best_params = params
    return best_params, best_performance

def main():
    config = load_config('config/backtest.yaml')
    logger = initialize_logging(config['general']['log_level'])

    historical_data = load_historical_data(config['data']['historical_data_filepath'])
    strategy_manager = StrategyManager(api_key='your_api_key', api_secret='your_api_secret')

    best_params, best_performance = optimize_strategy_parameters(strategy_manager, historical_data)
    logger.info(f"Best parameters: {best_params}")
    logger.info(f"Best performance: {best_performance}")

if __name__ == "__main__":
    main()
