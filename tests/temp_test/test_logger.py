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
        assert logger.level <= logging.DEBUG
        
        # Check that the logger has handlers
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0
    
    def test_log_level_setting(self):
        """Test setting different log levels"""
        # Test each log level
        for level_name in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            # Configure with this level
            configure_logging(log_level=level_name)
            logger_instance = GrekkoLogger()
            
            # Check that the level was set correctly
            expected_level = getattr(logging, level_name)
            assert logger_instance.log_level == expected_level
            
            # Get a component logger and check its effective level
            logger = get_logger('test_component')
            assert logger.getEffectiveLevel() <= expected_level
    
    def test_file_logging(self):
        """Test logging to a file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Patch the log directory to use our temp directory
            with patch.object(GrekkoLogger, 'log_dir', temp_dir):
                # Configure logging
                configure_logging(log_level='INFO', log_to_file=True, log_to_console=False)
                
                # Get a logger and log a message
                logger = get_logger('test_file_logging')
                test_message = 'Test file logging message'
                logger.info(test_message)
                
                # Check that a log file was created
                log_files = [f for f in os.listdir(temp_dir) if f.startswith('grekko_')]
                assert len(log_files) > 0
                
                # Check that the message was written to the file
                log_file_path = os.path.join(temp_dir, log_files[0])
                with open(log_file_path, 'r') as f:
                    log_content = f.read()
                    assert test_message in log_content
    
    def test_console_logging(self):
        """Test logging to the console"""
        # Mock sys.stdout
        mock_stdout = MagicMock()
        
        with patch('sys.stdout', mock_stdout):
            # Configure logging to console only
            configure_logging(log_level='INFO', log_to_file=False, log_to_console=True)
            
            # Create a handler that will write to our mock
            mock_handler = MagicMock()
            root_logger = logging.getLogger()
            root_logger.addHandler(mock_handler)
            
            # Get a logger and log a message
            logger = get_logger('test_console_logging')
            test_message = 'Test console logging message'
            logger.info(test_message)
            
            # Check that the handler received the message
            mock_handler.handle.assert_called()
    
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
        
        # They should share the same handlers though (from root logger)
        root_handlers = logging.getLogger().handlers
        for handler in root_handlers:
            # Check that messages from both loggers go to this handler
            assert logger1.handlers == [] and logger2.handlers == []  # No specific handlers
            assert logger1.propagate and logger2.propagate  # Will propagate to root