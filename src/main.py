import logging
import yaml
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from utils.credentials_manager import CredentialsManager
from ai_adaptation.agent.trading_agent import TradingAgent
from ai_adaptation.ensemble.strategy_selector import StrategySelector
from ai_adaptation.ml_models.model_trainer import ModelTrainer
from ai_adaptation.ml_models.model_evaluator import ModelEvaluator
from ai_adaptation.ml_models.online_learner import OnlineLearner
from ai_adaptation.reinforcement.environment import ReinforcementLearningEnvironment
from data_ingestion.data_processor import DataProcessor
from data_ingestion.data_streamer import DataStreamer
from strategy.strategy_manager import StrategyManager
from risk_management.risk_manager import RiskManager

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def initialize_logging(log_level):
    log_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = os.path.join(log_dir, 'grekko.log')
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    return logger

def ensure_credentials():
    """Ensure credentials exist, guide through setup if needed"""
    cred_manager = CredentialsManager()
    home_dir = str(Path.home())
    vault_path = os.path.join(home_dir, '.grekko', 'credentials.grekko')
    
    if not os.path.exists(vault_path):
        print("No credentials vault found. Setting up credentials...")
        cred_manager.setup_credentials()
    
    return True

async def start_api_server():
    """Start the API server for mobile app integration"""
    # This would be implemented with FastAPI
    # For now, just log that it would start
    logging.getLogger(__name__).info("API server would start here (placeholder)")
    while True:
        await asyncio.sleep(60)  # Keep task alive

async def main():
    # Load environment variables
    load_dotenv()
    
    # Load configuration
    config = load_config('config/main.yaml')
    logger = initialize_logging(config['general']['log_level'])
    
    # Ensure credentials are set up
    ensure_credentials()
    
    # Initialize legacy components (for backward compatibility)
    strategy_selector = StrategySelector()
    model_trainer = ModelTrainer()
    model_evaluator = ModelEvaluator()
    online_learner = OnlineLearner(model_trainer.model)
    rl_environment = ReinforcementLearningEnvironment(state_space_size=10, action_space_size=5)
    data_processor = DataProcessor()
    data_streamer = DataStreamer()
    
    # Use secure credential manager instead of hardcoded credentials
    try:
        default_exchange = config.get('default_exchange', 'binance')
        strategy_manager = StrategyManager(exchange=default_exchange)
        risk_manager = RiskManager(capital=config.get('risk', {}).get('initial_capital', 100000))
        
        logger.info("Legacy components initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing legacy components: {str(e)}")
    
    # Start the mobile API server in background
    api_task = asyncio.create_task(start_api_server())
    
    # Initialize and start the autonomous trading agent
    try:
        trading_agent = TradingAgent(config_path="config/agent_config.yaml")
        logger.info("Trading agent initialized successfully")
        
        # Start the agent if auto-start is enabled
        if config.get('agent', {}).get('auto_start', False):
            await trading_agent.start()
        else:
            logger.info("Auto-start disabled, trading agent is ready but not active")
            
        # Keep the main process running
        while True:
            await asyncio.sleep(60)
            # Periodically report status
            if trading_agent.is_active:
                trading_agent._report_status()
                
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        if trading_agent.is_active:
            await trading_agent.stop()
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        
    finally:
        # Cleanup
        api_task.cancel()
        logger.info("Grekko trading agent shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())