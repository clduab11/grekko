"""
Wallet provider abstractions for decentralized execution.

Defines the WalletProvider interface and concrete implementations for MetaMask and Coinbase Wallet.
These providers enable integration of external wallet types with the Grekko platform.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class WalletProvider(ABC):
    """
    Abstract base class for all wallet providers.
    Defines the interface for wallet connection, signing, and transaction routing.
    """

    @abstractmethod
    def connect(self, connection_params: Dict[str, Any]) -> bool:
        """
        Establish a connection to the wallet.
        Args:
            connection_params (Dict[str, Any]): Parameters required for connection.
        Returns:
            bool: True if connection is successful, False otherwise.
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if the wallet is currently connected.
        Returns:
            bool: True if connected, False otherwise.
        """
        pass

    @abstractmethod
    def get_address(self) -> Optional[str]:
        """
        Retrieve the wallet's public address.
        Returns:
            Optional[str]: Wallet address if available, else None.
        """
        pass

    @abstractmethod
    def sign_transaction(self, transaction_data: Dict[str, Any]) -> Optional[str]:
        """
        Sign a transaction using the wallet.
        Args:
            transaction_data (Dict[str, Any]): Transaction details to sign.
        Returns:
            Optional[str]: Signed transaction data or None if signing fails.
        """
        pass

    @abstractmethod
    def send_transaction(self, transaction_data: Dict[str, Any]) -> Optional[str]:
        """
        Send a transaction through the wallet.
        Args:
            transaction_data (Dict[str, Any]): Transaction details to send.
        Returns:
            Optional[str]: Transaction hash or None if sending fails.
        """
        pass

class MetaMaskProvider(WalletProvider):
    """
    MetaMask wallet provider implementation.
    Handles connection and transaction signing for MetaMask browser extension.
    """

    def __init__(self):
        self._connected = False
        self._address = None

    def connect(self, connection_params: Dict[str, Any]) -> bool:
        # In a backend context, MetaMask is typically connected via frontend.
        # Here, we simulate connection for interface completeness.
        # Validate connection parameters
        if not connection_params.get("network") or not connection_params.get("chain_id"):
            self._connected = False
            self._address = None
            return False
        
        self._connected = True
        # Generate mock address if not provided
        self._address = connection_params.get("address", "0x1234567890123456789012345678901234567890")
        return self._connected

    def is_connected(self) -> bool:
        return self._connected

    def get_address(self) -> Optional[str]:
        return self._address

    def sign_transaction(self, transaction_data: Dict[str, Any]) -> Optional[str]:
        # MetaMask signing is handled client-side; backend may receive signed tx.
        # This method is a placeholder for interface compatibility.
        if not self._connected:
            return None
        return transaction_data.get("signed_tx", "0xmock_signature_hash")

    def send_transaction(self, transaction_data: Dict[str, Any]) -> Optional[str]:
        # In practice, the backend receives a signed tx and relays it to the network.
        # Here, we simulate sending and return a mock tx hash.
        if not self._connected or not self._address:
            return None
        return "0xmetamask_mock_tx_hash"

class CoinbaseWalletProvider(WalletProvider):
    """
    Coinbase Wallet provider implementation.
    Handles connection and transaction signing for Coinbase Wallet.
    """

    def __init__(self):
        self._connected = False
        self._address = None

    def connect(self, connection_params: Dict[str, Any]) -> bool:
        # Simulate connection for Coinbase Wallet.
        # Validate connection parameters
        if not connection_params.get("network") or not connection_params.get("chain_id"):
            self._connected = False
            self._address = None
            return False
        
        self._connected = True
        # Generate mock address if not provided
        self._address = connection_params.get("address", "0x9876543210987654321098765432109876543210")
        return self._connected

    def is_connected(self) -> bool:
        return self._connected

    def get_address(self) -> Optional[str]:
        return self._address

    def sign_transaction(self, transaction_data: Dict[str, Any]) -> Optional[str]:
        # Coinbase Wallet signing is typically client-side; backend may receive signed tx.
        if not self._connected:
            return None
        return transaction_data.get("signed_tx", "0xcoinbase_mock_signature_hash")

    def send_transaction(self, transaction_data: Dict[str, Any]) -> Optional[str]:
        if not self._connected or not self._address:
            return None
        return "0xcoinbase_mock_tx_hash"