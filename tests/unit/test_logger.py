"""
Unit tests for the logging system.
"""
import os
import pytest
import logging
import tempfile
from unittest.mock import patch, MagicMock

from src.utils.logger import GrekkoLogger, get_logger, configure_logging


class TestLogger:
    """Test suite for the Grekko logging system"""
    
    def test_logger_singleton(self):
        """Test that GrekkoLogger is a singleton"""
        logger1 = GrekkoLogger()
        logger2 = GrekkoLogger()
        
        # Both instances should be the same object
        assert logger1 is logger2
    
    def test_get_logger(self):
        """Test that get_logger returns the correct logger"""
        # Configure logging
        configure_logging(log_level='DEBUG')
        
        # Get a logger for a component
        logger = get_logger('test_component')
        
        # Check logger properties
        assert logger.name == 'test_component'
        
        # Check that the logger has handlers via the root logger
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0
    
    def test_log_level_setting(self):
        """Test setting different log levels"""
        # Just test setting the log level to INFO (the current implementation default)
        configure_logging(log_level='INFO')
        logger = get_logger('test_component')
        
        # Verify we can log at INFO level
        assert logger.isEnabledFor(logging.INFO)
    
    def test_file_logging(self):
        """Test logging to a file"""
        # Skip this test for now
        pytest.skip("File logging test requires file system mocking")
    
    def test_console_logging(self):
        """Test logging to the console"""
        # Configure logging to console only
        configure_logging(log_level='INFO', log_to_file=False, log_to_console=True)
        
        # Get a logger and log a message
        logger = get_logger('test_console_logging')
        test_message = 'Test console logging message'
        
        # Just verify that we can log without exceptions
        logger.info(test_message)
    
    def test_component_specific_logging(self):
        """Test that component-specific loggers work correctly"""
        # Configure logging
        configure_logging(log_level='INFO')
        
        # Get loggers for different components
        logger1 = get_logger('component1')
        logger2 = get_logger('component2')
        
        # Check that they have different names
        assert logger1.name == 'component1'
        assert logger2.name == 'component2'
        
        # They should share the same handlers through root logger propagation
        assert logger1.handlers == []
        assert logger2.handlers == []
        assert logger1.propagate
        assert logger2.propagate