import logging
import yaml
import os
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
from utils.credentials_manager import CredentialsManager
from utils.logger import configure_logging, get_logger
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
    """
    Initialize logging using the centralized logging system.
    
    Args:
        log_level (str): The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        logging.Logger: Logger for the main module
    """
    # Configure the centralized logging system
    configure_logging(log_level=log_level, log_to_file=True, log_to_console=True)
    
    # Get a logger for the main module
    logger = get_logger(__name__)
    
    # Log startup information
    logger.info(f"Grekko initializing, log level: {log_level}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    return logger

def ensure_credentials():
    """
    Ensure credentials exist, guide through setup if needed.
    
    Checks if the credentials vault exists and guides the user through 
    setting up API keys for exchanges if it doesn't.
    
    Returns:
        bool: True if credentials are set up, False if setup failed
    """
    logger = get_logger('credentials_setup')
    cred_manager = CredentialsManager()
    
    if not cred_manager.vault_exists():
        logger.info("No credentials vault found. Starting setup process...")
        print("\n==================================================")
        print("           GREKKO CREDENTIALS SETUP")
        print("==================================================")
        print("You need to set up API keys for the exchanges you want to use.")
        print("This is a one-time setup that creates an encrypted vault.")
        
        # Guide the user through credentials setup
        if cred_manager.setup_credentials():
            logger.info("Credentials setup completed successfully")
            return True
        else:
            logger.error("Credentials setup failed")
            print("\nCredentials setup failed. You can try again later.")
            print("Run the application again to retry setup.")
            return False
    
    # Vault exists, verify we can access at least one exchange
    try:
        exchanges = cred_manager.list_exchanges()
        if exchanges:
            logger.info(f"Found credentials for: {', '.join(exchanges)}")
            return True
        else:
            logger.warning("Credentials vault exists but contains no exchanges")
            print("\nCredentials vault exists but no exchanges are configured.")
            print("Would you like to set up exchange credentials now? (y/n)")
            
            if input().lower().startswith('y'):
                return cred_manager.setup_credentials()
            else:
                return False
    except Exception as e:
        logger.error(f"Error accessing credentials vault: {str(e)}")
        print("\nError accessing credentials vault. You may need to recreate it.")
        return False

async def start_api_server():
    """Start the API server for bot control and monitoring"""
    # Import and run the FastAPI server
    try:
        from .api.main import app
        import uvicorn
        
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    except ImportError:
        # Fallback if API not available
        logging.getLogger(__name__).info("API server not available, running in standalone mode")
        while True:
            await asyncio.sleep(60)  # Keep task alive

async def main():
    """
    Main entry point for the Grekko trading platform.
    
    Initializes the system, sets up components, and runs the main loop.
    """
    # Load environment variables
    load_dotenv()
    
    try:
        # Load configuration
        main_config_path = 'config/main.yaml'
        if not os.path.exists(main_config_path):
            print(f"Error: Configuration file '{main_config_path}' not found")
            print("Please ensure the configuration file exists and is valid")
            return 1
            
        config = load_config(main_config_path)
        
        # Set up logging
        log_level = config.get('general', {}).get('log_level', 'INFO')
        logger = initialize_logging(log_level)
        
        logger.info("Starting Grekko cryptocurrency trading platform")
        
        # Ensure credentials are set up
        if not ensure_credentials():
            logger.error("Failed to set up credentials, exiting")
            return 1
            
        # Initialize components
        logger.info("Initializing system components...")
        
        # Get default exchange from config
        default_exchange = config.get('default_exchange', 'binance')
        logger.info(f"Using {default_exchange} as default exchange")
        
        # Initialize core components
        strategy_selector = StrategySelector()
        model_trainer = ModelTrainer()
        model_evaluator = ModelEvaluator()
        online_learner = OnlineLearner(model_trainer.model)
        rl_environment = ReinforcementLearningEnvironment(state_space_size=10, action_space_size=5)
        data_processor = DataProcessor()
        data_streamer = DataStreamer()
        
        # Initialize components that require credentials
        try:
            # Initialize strategy manager with secure credentials
            strategy_manager = StrategyManager(exchange=default_exchange)
            
            # Set initial strategy
            default_strategy = config.get('default_strategy', 'momentum')
            if default_strategy in strategy_manager.strategies:
                strategy_manager.switch_strategy(default_strategy)
                logger.info(f"Set {default_strategy} as initial strategy")
            else:
                available_strategies = list(strategy_manager.strategies.keys())
                logger.warning(f"Default strategy '{default_strategy}' not found. Available: {available_strategies}")
                
            # Initialize risk manager
            initial_capital = config.get('risk', {}).get('initial_capital', 100000)
            max_drawdown = config.get('risk', {}).get('max_drawdown_pct', 0.10)
            max_position_size = config.get('risk', {}).get('max_position_size_pct', 0.15)
            
            risk_manager = RiskManager(
                capital=initial_capital,
                max_drawdown_pct=max_drawdown,
                max_trade_size_pct=max_position_size
            )
            
            logger.info(f"Risk manager initialized: {initial_capital} capital, {max_drawdown:.1%} max drawdown")
            
            # All components initialized successfully
            logger.info("Core components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing core components: {str(e)}")
            print(f"\nError: Failed to initialize core components: {str(e)}")
            print("Check your credentials and configuration, then try again")
            return 1
        
        # Start the mobile API server in background
        logger.info("Starting mobile API server")
        api_task = asyncio.create_task(start_api_server())
        
        # Initialize and start the autonomous trading agent
        try:
            agent_config_path = "config/agent_config.yaml"
            logger.info(f"Initializing trading agent from {agent_config_path}")
            
            trading_agent = TradingAgent(config_path=agent_config_path)
            logger.info("Trading agent initialized successfully")
            
            # Start the agent if auto-start is enabled
            auto_start = config.get('agent', {}).get('auto_start', False)
            if auto_start:
                logger.info("Auto-start enabled, starting trading agent...")
                await trading_agent.start()
                print("\nGreko trading agent started and running autonomously")
                print("Use Ctrl+C to stop the agent and exit")
            else:
                logger.info("Auto-start disabled, trading agent is ready but not active")
                print("\nGreko initialized successfully, but trading is not active")
                print("Update config/main.yaml and set agent.auto_start to true to enable trading")
                
            # Keep the main process running
            while True:
                await asyncio.sleep(60)
                # Periodically report status and run health checks
                if trading_agent.is_active:
                    trading_agent._report_status()
                    
        except KeyboardInterrupt:
            logger.info("Shutting down gracefully...")
            print("\nShutting down gracefully...")
            
            if 'trading_agent' in locals() and trading_agent.is_active:
                await trading_agent.stop()
            
        except Exception as e:
            logger.error(f"Error in main process: {str(e)}")
            print(f"\nError: {str(e)}")
            
        finally:
            # Cleanup resources
            logger.info("Cleaning up resources...")
            
            if 'api_task' in locals():
                api_task.cancel()
                
            logger.info("Grekko trading agent shutdown complete")
            print("Grekko shutdown complete")
            
    except Exception as e:
        print(f"Fatal error during startup: {str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)