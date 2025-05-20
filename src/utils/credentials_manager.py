import os
import json
import getpass
from pathlib import Path
from .encryption import EncryptionManager, save_vault, load_vault
import logging

class CredentialsManager:
    """Manages secure storage and retrieval of API credentials"""
    
    def __init__(self, config_path=None):
        self.home_dir = str(Path.home())
        self.config_dir = os.path.join(self.home_dir, '.grekko')
        self.vault_path = os.path.join(self.config_dir, 'credentials.grekko')
        self.config_path = config_path or os.path.join(os.getcwd(), 'config', 'exchanges.yaml')
        self.logger = logging.getLogger(__name__)
        self._ensure_config_dir()
        
    def _ensure_config_dir(self):
        """Ensure the .grekko directory exists"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            self.logger.info(f"Created credentials directory at {self.config_dir}")
            
    def setup_credentials(self):
        """Interactive setup for new credentials"""
        credentials = {}
        
        print("Setting up API credentials...")
        # Get exchanges from config/exchanges.yaml
        exchanges = self._get_configured_exchanges()
        
        for exchange in exchanges:
            print(f"\nSetting up credentials for {exchange}:")
            api_key = input(f"{exchange} API Key: ")
            api_secret = getpass.getpass(f"{exchange} API Secret: ")
            
            credentials[exchange] = {
                'api_key': api_key,
                'api_secret': api_secret
            }
            
        # Get master password for the vault
        master_password = self._get_master_password(new=True)
        
        # Save credentials to encrypted vault
        save_vault(credentials, master_password, self.vault_path)
        print(f"Credentials saved securely to {self.vault_path}")
        
    def get_credentials(self, exchange):
        """Retrieve credentials for a specific exchange"""
        if not os.path.exists(self.vault_path):
            raise FileNotFoundError(f"Credentials vault not found at {self.vault_path}. Run setup_credentials() first.")
        
        master_password = self._get_master_password()
        
        try:
            vault = load_vault(master_password, self.vault_path)
            if exchange in vault:
                return vault[exchange]
            else:
                raise ValueError(f"No credentials found for {exchange}")
        except Exception as e:
            self.logger.error(f"Error loading credentials: {str(e)}")
            raise ValueError(f"Error loading credentials: {str(e)}")
            
    def _get_master_password(self, new=False):
        """Get master password, with confirmation if new"""
        if new:
            while True:
                password = getpass.getpass("Create master password for credential vault: ")
                confirm = getpass.getpass("Confirm master password: ")
                
                if password == confirm:
                    return password
                else:
                    print("Passwords do not match. Please try again.")
        else:
            return getpass.getpass("Enter master password for credential vault: ")
            
    def _get_configured_exchanges(self):
        """Parse exchanges.yaml to get list of configured exchanges"""
        import yaml
        
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                return list(config.keys()) if config else []
        except Exception as e:
            self.logger.warning(f"Could not load exchange config: {str(e)}")
            return ["binance", "coinbase", "uniswap"]  # Fallback defaults
            
    def add_credentials(self, exchange, api_key, api_secret):
        """Add or update credentials for a specific exchange"""
        if not os.path.exists(self.vault_path):
            credentials = {
                exchange: {
                    'api_key': api_key,
                    'api_secret': api_secret
                }
            }
            master_password = self._get_master_password(new=True)
        else:
            master_password = self._get_master_password()
            credentials = load_vault(master_password, self.vault_path)
            credentials[exchange] = {
                'api_key': api_key,
                'api_secret': api_secret
            }
            
        save_vault(credentials, master_password, self.vault_path)
        self.logger.info(f"Credentials for {exchange} added/updated.")
        
    def remove_credentials(self, exchange):
        """Remove credentials for a specific exchange"""
        if not os.path.exists(self.vault_path):
            raise FileNotFoundError(f"Credentials vault not found at {self.vault_path}")
            
        master_password = self._get_master_password()
        credentials = load_vault(master_password, self.vault_path)
        
        if exchange in credentials:
            del credentials[exchange]
            save_vault(credentials, master_password, self.vault_path)
            self.logger.info(f"Credentials for {exchange} removed.")
        else:
            self.logger.warning(f"No credentials found for {exchange}")
            
    def list_exchanges(self):
        """List exchanges with stored credentials"""
        if not os.path.exists(self.vault_path):
            return []
            
        try:
            master_password = self._get_master_password()
            credentials = load_vault(master_password, self.vault_path)
            return list(credentials.keys())
        except Exception as e:
            self.logger.error(f"Error listing exchanges: {str(e)}")
            return []