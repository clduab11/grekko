"""
Secure credentials management for the Grekko trading platform.

This module provides a secure way to store and retrieve API keys, private keys,
and other sensitive credentials needed for exchange connectivity. It uses
strong encryption to protect credentials and a master password for the vault.
"""
import os
import json
import getpass
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from .encryption import EncryptionManager, save_vault, load_vault
from .logger import get_logger

class CredentialsManager:
    """
    Manages secure storage and retrieval of API credentials and private keys.
    
    Uses an encrypted vault to securely store all sensitive information,
    protected by a master password. Credentials are never stored in plain text
    anywhere in the code or configuration files.
    
    Attributes:
        config_dir (str): Path to the .grekko configuration directory
        vault_path (str): Path to the encrypted credentials vault
        logger (logging.Logger): Logger for credential operations
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the credentials manager.
        
        Args:
            config_path (Optional[str]): Path to exchanges configuration file
        """
        self.home_dir = str(Path.home())
        self.config_dir = os.path.join(self.home_dir, '.grekko')
        self.vault_path = os.path.join(self.config_dir, 'credentials.grekko')
        self.config_path = config_path or os.path.join(os.getcwd(), 'config', 'exchanges.yaml')
        self.logger = get_logger('credentials_manager')
        self._ensure_config_dir()
        
    def _ensure_config_dir(self) -> None:
        """Ensure the .grekko directory exists"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            self.logger.info(f"Created credentials directory: {self.config_dir}")
            
    def setup_credentials(self) -> bool:
        """
        Interactive setup for new credentials.
        
        Creates a new credentials vault and guides the user through setting up
        API keys for all configured exchanges. Requires user input for keys and
        a master password to encrypt the vault.
        
        Returns:
            bool: True if setup was successful, False otherwise
        """
        credentials = {}
        
        print("\n===== Grekko Credentials Setup =====")
        print("This will create a secure vault for your exchange API keys and private keys.")
        print("The vault will be encrypted with a master password that you need to remember.")
        print("None of your credentials will be stored in plain text.\n")
        
        # Get exchanges from config/exchanges.yaml
        exchanges = self._get_configured_exchanges()
        
        if not exchanges:
            self.logger.error("No exchanges configured. Check exchanges.yaml")
            print("No exchanges found in configuration. Setup cannot continue.")
            return False
        
        print(f"Found the following exchanges to configure: {', '.join(exchanges)}")
        print("\nYou'll need to provide API credentials for each exchange.")
        print("These can be obtained from your exchange account settings.")
        print("Leave empty to skip an exchange for now.\n")
        
        for exchange in exchanges:
            print(f"\nSetting up credentials for {exchange.upper()}:")
            api_key = input(f"{exchange} API Key: ").strip()
            
            if not api_key:
                print(f"Skipping {exchange}")
                continue
                
            api_secret = getpass.getpass(f"{exchange} API Secret: ").strip()
            
            # Optionally get passphrase for exchanges that need it
            passphrase = None
            if exchange.lower() in ['coinbase', 'coinbasepro', 'kraken']:
                passphrase = getpass.getpass(f"{exchange} API Passphrase (optional): ").strip()
            
            credentials[exchange] = {
                'api_key': api_key,
                'api_secret': api_secret
            }
            
            if passphrase:
                credentials[exchange]['passphrase'] = passphrase
                
            print(f"✓ {exchange} credentials added")
        
        if not credentials:
            self.logger.warning("No credentials were provided during setup")
            print("\nNo credentials were provided. Setup aborted.")
            return False
            
        # Get master password for the vault
        try:
            master_password = self._get_master_password(new=True)
            
            # Save credentials to encrypted vault
            save_vault(credentials, master_password, self.vault_path)
            self.logger.info(f"Credentials vault created: {self.vault_path}")
            
            print(f"\n✓ Credentials securely saved to {self.vault_path}")
            print("NOTE: Remember your master password - it cannot be recovered!")
            return True
            
        except KeyboardInterrupt:
            print("\nCredentials setup cancelled.")
            return False
        except Exception as e:
            self.logger.error(f"Error during credentials setup: {str(e)}")
            print(f"\nError setting up credentials: {str(e)}")
            return False
        
    def get_credentials(self, exchange: str) -> Dict[str, str]:
        """
        Retrieve credentials for a specific exchange.
        
        Args:
            exchange (str): Exchange name to get credentials for
            
        Returns:
            Dict[str, str]: Dictionary with api_key, api_secret, and possibly passphrase
            
        Raises:
            ValueError: If no credentials are found or vault cannot be opened
        """
        master_password = self._get_master_password()
        
        try:
            vault = load_vault(master_password, self.vault_path)
            
            if exchange in vault:
                self.logger.debug(f"Retrieved credentials for {exchange}")
                return vault[exchange]
            else:
                error_msg = f"No credentials found for {exchange}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
                
        except Exception as e:
            error_msg = f"Error loading credentials: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
    def add_credentials(self, exchange: str, api_key: str, api_secret: str, 
                       passphrase: Optional[str] = None) -> bool:
        """
        Add or update credentials for an exchange.
        
        Args:
            exchange (str): Exchange name
            api_key (str): API key for the exchange
            api_secret (str): API secret for the exchange
            passphrase (Optional[str]): Optional API passphrase for exchanges that need it
            
        Returns:
            bool: True if credentials were successfully added/updated
            
        Raises:
            ValueError: If vault cannot be opened or credentials cannot be saved
        """
        master_password = self._get_master_password()
        
        try:
            # Load existing vault or create new one
            try:
                vault = load_vault(master_password, self.vault_path)
            except FileNotFoundError:
                vault = {}
                
            # Update or add credentials
            vault[exchange] = {
                'api_key': api_key,
                'api_secret': api_secret
            }
            
            if passphrase:
                vault[exchange]['passphrase'] = passphrase
                
            # Save updated vault
            save_vault(vault, master_password, self.vault_path)
            self.logger.info(f"Added/updated credentials for {exchange}")
            return True
            
        except Exception as e:
            error_msg = f"Error adding credentials: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
    def remove_credentials(self, exchange: str) -> bool:
        """
        Remove credentials for an exchange from the vault.
        
        Args:
            exchange (str): Exchange name to remove credentials for
            
        Returns:
            bool: True if credentials were successfully removed
            
        Raises:
            ValueError: If vault cannot be opened or credentials cannot be saved
        """
        master_password = self._get_master_password()
        
        try:
            # Load existing vault
            vault = load_vault(master_password, self.vault_path)
            
            # Remove credentials if they exist
            if exchange in vault:
                del vault[exchange]
                
                # Save updated vault
                save_vault(vault, master_password, self.vault_path)
                self.logger.info(f"Removed credentials for {exchange}")
                return True
            else:
                self.logger.warning(f"No credentials found for {exchange} to remove")
                return False
                
        except Exception as e:
            error_msg = f"Error removing credentials: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
    def list_exchanges(self) -> list:
        """
        List all exchanges with stored credentials.
        
        Returns:
            list: List of exchange names with stored credentials
            
        Raises:
            ValueError: If vault cannot be opened
        """
        master_password = self._get_master_password()
        
        try:
            vault = load_vault(master_password, self.vault_path)
            return list(vault.keys())
            
        except Exception as e:
            error_msg = f"Error listing credentials: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
    def _get_master_password(self, new: bool = False) -> str:
        """
        Get master password, with confirmation if new.
        
        Args:
            new (bool): Whether this is a new password (requires confirmation)
            
        Returns:
            str: Master password for the vault
        """
        if new:
            while True:
                password = getpass.getpass("Create master password for credential vault: ")
                
                # Validate password strength
                validation = self._validate_password_strength(password)
                if not validation['valid']:
                    print(f"Password requirement: {validation['message']}")
                    continue
                    
                confirm = getpass.getpass("Confirm master password: ")
                
                if password == confirm:
                    return password
                else:
                    print("Passwords do not match. Please try again.")
        else:
            # Add retry limit for security
            max_attempts = 3
            for attempt in range(max_attempts):
                password = getpass.getpass(f"Enter master password for credential vault (attempt {attempt + 1}/{max_attempts}): ")
                if self.verify_master_password(password):
                    return password
                elif attempt < max_attempts - 1:
                    print("Incorrect password. Please try again.")
            
            raise ValueError("Maximum password attempts exceeded")
            
    def _get_configured_exchanges(self) -> list:
        """
        Parse exchanges.yaml to get list of configured exchanges.
        
        Returns:
            list: List of exchange names from configuration
        """
        import yaml
        
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                return list(config.keys()) if config else []
        except Exception as e:
            self.logger.warning(f"Could not read exchange config: {str(e)}")
            return ["binance", "coinbase", "uniswap"]  # Fallback defaults
            
    def verify_master_password(self, password: str) -> bool:
        """
        Verify if the master password is correct.
        
        Args:
            password (str): Master password to verify
            
        Returns:
            bool: True if password is correct, False otherwise
        """
        try:
            load_vault(password, self.vault_path)
            return True
        except Exception:
            return False
            
    def vault_exists(self) -> bool:
        """
        Check if credentials vault exists.
        
        Returns:
            bool: True if vault exists, False otherwise
        """
        return os.path.exists(self.vault_path)
    
    def _validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Validate password strength requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            Validation result with 'valid' and 'message' keys
        """
        if len(password) < 12:
            return {
                'valid': False,
                'message': 'Password must be at least 12 characters long'
            }
        
        if not any(c.isupper() for c in password):
            return {
                'valid': False,
                'message': 'Password must contain at least one uppercase letter'
            }
        
        if not any(c.islower() for c in password):
            return {
                'valid': False,
                'message': 'Password must contain at least one lowercase letter'
            }
        
        if not any(c.isdigit() for c in password):
            return {
                'valid': False,
                'message': 'Password must contain at least one number'
            }
        
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            return {
                'valid': False,
                'message': 'Password must contain at least one special character'
            }
        
        return {'valid': True, 'message': 'Password meets all requirements'}