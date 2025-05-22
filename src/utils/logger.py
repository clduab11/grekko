"""
Centralized logging configuration for the Grekko platform.
This module provides a consistent logging interface for all components.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path


class GrekkoLogger:
    """
    Centralized logger for the Grekko platform.
    
    Features:
    - Configurable log levels
    - File and console output
    - Rotation of log files
    - Consistent formatting
    - Component-specific logging
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern for logger"""
        if cls._instance is None:
            cls._instance = super(GrekkoLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, log_level='INFO', log_to_file=True, log_to_console=True):
        """
        Initialize the logger with the specified configuration.
        
        Args:
            log_level (str): The logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            log_to_file (bool): Whether to log to a file
            log_to_console (bool): Whether to log to the console
        """
        # Skip initialization if already initialized
        if self._initialized:
            return
        
        self._initialized = True
        self.log_level = self._get_log_level(log_level)
        self.log_to_file = log_to_file
        self.log_to_console = log_to_console
        self.log_dir = os.path.join(os.getcwd(), 'logs')
        
        # Ensure log directory exists
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # Create formatter
        self.formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Configure root logger
        self._configure_root_logger()
    
    def _get_log_level(self, level_name):
        """
        Convert log level name to logging module constant.
        
        Args:
            level_name (str): The name of the log level
            
        Returns:
            int: The logging level constant
        """
        levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return levels.get(level_name.upper(), logging.INFO)
    
    def _configure_root_logger(self):
        """Configure the root logger with file and console handlers."""
        # Get the root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add file handler if enabled
        if self.log_to_file:
            today = datetime.now().strftime('%Y-%m-%d')
            log_file = os.path.join(self.log_dir, f'grekko_{today}.log')
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(self.formatter)
            root_logger.addHandler(file_handler)
        
        # Add console handler if enabled
        if self.log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(self.formatter)
            root_logger.addHandler(console_handler)
    
    def get_logger(self, name):
        """
        Get a logger for a specific component.
        
        Args:
            name (str): The name of the component (e.g., 'trading_agent', 'risk_manager')
            
        Returns:
            logging.Logger: A logger configured for the component
        """
        return logging.getLogger(name)


# Global accessor function
def get_logger(name):
    """
    Get a logger for a specific component.
    
    Args:
        name (str): The name of the component
        
    Returns:
        logging.Logger: A logger configured for the component
    """
    logger = GrekkoLogger()
    return logger.get_logger(name)


def configure_logging(log_level='INFO', log_to_file=True, log_to_console=True):
    """
    Configure the global logging settings.
    
    Args:
        log_level (str): The logging level
        log_to_file (bool): Whether to log to a file
        log_to_console (bool): Whether to log to the console
    """
    GrekkoLogger(log_level, log_to_file, log_to_console)


# Configure default logging
configure_logging()