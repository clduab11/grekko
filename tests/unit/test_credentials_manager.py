"""
Unit tests for the credentials manager component
"""
import os
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.credentials_manager import CredentialsManager


class TestCredentialsManager:
    """Test suite for CredentialsManager"""
    
    @pytest.fixture
    def temp_vault_path(self):
        """Create a temporary vault path for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir) / "test_credentials.grekko"
            yield str(vault_path)
    
    @pytest.fixture
    def cm_with_temp_vault(self, temp_vault_path):
        """Create a CredentialsManager instance with a temporary vault"""
        with patch.object(CredentialsManager, '_get_vault_path', return_value=temp_vault_path):
            cm = CredentialsManager()
            yield cm
            
    def test_vault_creation(self, cm_with_temp_vault, temp_vault_path):
        """Test that the vault is created when credentials are added"""
        with patch('getpass.getpass', return_value='test_password'):
            cm_with_temp_vault.add_credentials(
                exchange='binance',
                api_key='test_api_key',
                api_secret='test_api_secret'
            )
        
        assert os.path.exists(temp_vault_path), "Vault file should be created"
    
    def test_credential_retrieval(self, cm_with_temp_vault):
        """Test that credentials can be retrieved after adding them"""
        with patch('getpass.getpass', return_value='test_password'):
            # Add credentials
            cm_with_temp_vault.add_credentials(
                exchange='binance',
                api_key='test_api_key',
                api_secret='test_api_secret'
            )
            
            # Retrieve credentials
            credentials = cm_with_temp_vault.get_credentials('binance')
            
            assert credentials['api_key'] == 'test_api_key'
            assert credentials['api_secret'] == 'test_api_secret'
    
    def test_multiple_exchanges(self, cm_with_temp_vault):
        """Test adding credentials for multiple exchanges"""
        with patch('getpass.getpass', return_value='test_password'):
            # Add credentials for multiple exchanges
            cm_with_temp_vault.add_credentials(
                exchange='binance',
                api_key='binance_api_key',
                api_secret='binance_api_secret'
            )
            
            cm_with_temp_vault.add_credentials(
                exchange='coinbase',
                api_key='coinbase_api_key',
                api_secret='coinbase_api_secret'
            )
            
            # Retrieve credentials for both exchanges
            binance_creds = cm_with_temp_vault.get_credentials('binance')
            coinbase_creds = cm_with_temp_vault.get_credentials('coinbase')
            
            assert binance_creds['api_key'] == 'binance_api_key'
            assert coinbase_creds['api_key'] == 'coinbase_api_key'
    
    def test_credential_removal(self, cm_with_temp_vault):
        """Test removing credentials"""
        with patch('getpass.getpass', return_value='test_password'):
            # Add credentials
            cm_with_temp_vault.add_credentials(
                exchange='binance',
                api_key='test_api_key',
                api_secret='test_api_secret'
            )
            
            # Remove credentials
            cm_with_temp_vault.remove_credentials('binance')
            
            # Verify credentials are removed
            with pytest.raises(KeyError):
                cm_with_temp_vault.get_credentials('binance')
    
    def test_incorrect_password(self, cm_with_temp_vault):
        """Test handling of incorrect password"""
        # First setup with correct password
        with patch('getpass.getpass', return_value='correct_password'):
            cm_with_temp_vault.add_credentials(
                exchange='binance',
                api_key='test_api_key',
                api_secret='test_api_secret'
            )
        
        # Then try to access with incorrect password
        with patch('getpass.getpass', return_value='wrong_password'):
            with pytest.raises(ValueError, match="Invalid password"):
                cm_with_temp_vault.get_credentials('binance')
    
    def test_setup_credentials_interactive(self, cm_with_temp_vault):
        """Test interactive credential setup"""
        with patch('getpass.getpass', return_value='test_password'), \
             patch('builtins.input', side_effect=['binance', 'test_api_key', 'test_api_secret', 'n']):
            
            cm_with_temp_vault.setup_credentials()
            
            credentials = cm_with_temp_vault.get_credentials('binance')
            assert credentials['api_key'] == 'test_api_key'
            assert credentials['api_secret'] == 'test_api_secret'