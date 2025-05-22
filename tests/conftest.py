"""
Unit test fixtures for Grekko unit tests.
"""
import pytest
import logging
from unittest.mock import MagicMock

# Mock the ccxt module
class MockCCXT:
    def __init__(self):
        self.has = {'fetchTicker': True}

# Create a patch for ccxt.pro as ccxt
ccxt = MagicMock()
ccxt.binance.return_value = MockCCXT()
ccxt.coinbasepro.return_value = MockCCXT()

# Override system import path
import sys
sys.modules['ccxt.pro'] = ccxt
sys.modules['ccxt'] = ccxt

@pytest.fixture
def test_logger():
    """Configure logging for tests"""
    logger = logging.getLogger('test')
    logger.setLevel(logging.DEBUG)
    
    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(ch)
    
    return logger