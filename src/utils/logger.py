"""
Centralized logging configuration for the Grekko platform.
This module provides a consistent logging interface for all components.
"""
import logging
import os
import sys
import json # Added for JSON logging
from datetime import datetime
from pathlib import Path

# Custom JSON Formatter
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "service_name": record.name, # Logger name can represent service/component
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }
        # Add exception info if present
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)
        
        # Add extra fields if any (e.g., correlation_id)
        extra_fields = record.__dict__.get('extra_fields', {})
        log_record.update(extra_fields)
            
        return json.dumps(log_record)

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
    
    def __init__(self, log_level='INFO', log_to_file=True, log_to_console=True, log_format='json'):
        """
        Initialize the logger with the specified configuration.
        
        Args:
            log_level (str): The logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            log_to_file (bool): Whether to log to a file
            log_to_console (bool): Whether to log to the console
            log_format (str): 'json' or 'text'
        """
        # Skip initialization if already initialized
        if self._initialized:
            return
        
        self._initialized = True
        self.log_level = self._get_log_level(log_level)
        self.log_to_file = log_to_file
        self.log_to_console = log_to_console
        self.log_format = log_format.lower()
        self.log_dir = os.path.join(os.getcwd(), 'logs')
        
        # Ensure log directory exists
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # Create formatter based on log_format
        if self.log_format == 'json':
            self.formatter = JsonFormatter()
        else: # Default to text
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

    def get_logger_with_extra(self, name: str, **kwargs):
        """
        Get a logger and prepare to log with extra fields.
        Usage: logger.info("My message", extra={'extra_fields': {'correlation_id': '123'}})
        """
        logger = self.get_logger(name)
        # This method itself doesn't directly inject, but guides usage.
        # Actual injection happens if 'extra_fields' is passed in the logging call.
        return logger


# Global accessor function
def get_logger(name, **kwargs):
    """
    Get a logger for a specific component.
    
    Args:
        name (str): The name of the component
        
    Returns:
        logging.Logger: A logger configured for the component
    """
    grekko_logger_instance = GrekkoLogger() # Ensures singleton is initialized
    if kwargs:
        # This is a simplified way to hint at extra fields.
        # For true context injection, adapter or filter classes are more robust.
        # For now, we rely on the user passing `extra={'extra_fields': kwargs}`
        # to the actual log call e.g. logger.info("message", extra={'extra_fields': {'key': 'value'}})
        # This function primarily returns a standard logger instance.
        # The JsonFormatter will pick up 'extra_fields' if provided in the log call.
        pass
    return grekko_logger_instance.get_logger(name)


def configure_logging(log_level='INFO', log_to_file=True, log_to_console=True, log_format='json'):
    """
    Configure the global logging settings.
    
    Args:
        log_level (str): The logging level
        log_to_file (bool): Whether to log to a file
        log_to_console (bool): Whether to log to the console
        log_format (str): 'json' or 'text'
    """
    GrekkoLogger(log_level, log_to_file, log_to_console, log_format)


# Configure default logging (now defaults to JSON)
configure_logging(log_format='json')